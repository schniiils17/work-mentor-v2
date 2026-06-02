"""Work Mentor 2.0 — FastAPI Backend + Frontend"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os
import json
import re

from app.holland import ITEMS, assess, get_shuffled_items, _dim_label
import anthropic

app = FastAPI(title="Work Mentor 3.0")

# Anthropic-Client robust initialisieren (kein Crash bei fehlendem Key)
try:
    claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY") or None)
except Exception:
    claude = None

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ─── API ─────────────────────────────────────────────────────────────

class Answer(BaseModel):
    item_id: int
    value: int  # -2 to +2 (Likert scale)

class AssessmentRequest(BaseModel):
    answers: List[Answer]

class FitRequest(BaseModel):
    job_name: str
    scores: dict
    code: str
    fit_answers: list = []  # [{question, value}] aus dem Post-Payment-Check


# Kanonische Tier-Sprüche — Ton-Anker im Prompt UND Fallback, falls der
# Claude-Call scheitert. Keyed nach Haupt-Dimension (+ Generalist "G").
TIER_ANCHORS = {
    "R": {"superkraft": "Aus dem Nichts etwas Funktionierendes bauen — bevor andere überhaupt verstanden haben, wie das Problem aussieht.",
          "kryptonit": "Endlose Meetings, in denen geredet wird statt gemacht."},
    "I": {"superkraft": "Muster erkennen, wo andere nur Chaos sehen — und das so erklären, dass es plötzlich offensichtlich wirkt.",
          "kryptonit": "Jemand sagt 'Glaub mir einfach' ohne Daten zu zeigen."},
    "A": {"superkraft": "Bestehende Ideen so neu kombinieren, dass alle denken: Klar, warum hat das nicht schon jemand gemacht?",
          "kryptonit": "Eine Vorlage in PowerPoint, die du nur noch ausfüllen sollst."},
    "S": {"superkraft": "Eine Gruppe so führen, dass sich jeder Einzelne gesehen fühlt — und am Ende mehr leistet als gedacht.",
          "kryptonit": "Allein in einem Co-Working zwischen 30 Headphones."},
    "E": {"superkraft": "Leute begeistern, bevor du selbst weißt, wovon du redest.",
          "kryptonit": "Jemand sagt: Das haben wir schon immer so gemacht."},
    "C": {"superkraft": "Aus Datenchaos eine saubere Struktur machen, die so logisch wirkt, als wäre sie schon immer da gewesen.",
          "kryptonit": "Lass uns das einfach spontan entscheiden."},
    "G": {"superkraft": "Zwischen Welten übersetzen, die sonst nicht miteinander reden.",
          "kryptonit": "Auf EINE Schiene festgelegt werden."},
}


@app.get("/api/items")
async def get_items():
    """Liefere Assessment-Items in zufälliger Reihenfolge."""
    return {"items": get_shuffled_items()}


@app.post("/api/assess")
async def post_assess(req: AssessmentRequest):
    """Berechne das Ergebnis + personalisierte KI-Texte (Beschreibung,
    Job-Teaser, Superkraft, Kryptonit) — gegründet auf dem vollen Profil."""
    answers = [{"item_id": a.item_id, "value": a.value} for a in req.answers]
    result = assess(answers)

    code = result["code"]
    is_gen = result.get("is_generalist", False)
    anchor_key = "G" if is_gen else code[0]
    anchor = TIER_ANCHORS.get(anchor_key, TIER_ANCHORS["E"])

    # Statischer Fallback — nie schlechter als vorher
    result["ai_superkraft"] = None
    result["ai_kryptonit"] = None
    result["fallback_superkraft"] = anchor["superkraft"]
    result["fallback_kryptonit"] = anchor["kryptonit"]

    try:
        norm = result.get("normalized_scores", result["scores"])
        sorted_dims = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        profile = ", ".join([f"{_dim_label(d)}: {v}" for d, v in sorted_dims])

        d1 = _dim_label(code[0])
        d2 = _dim_label(code[1])
        d_low = _dim_label(sorted_dims[-1][0])
        type_name = result.get("type_name", "")
        jobs_list = ", ".join([j["title"] for j in result.get("jobs", [])])

        prompt = f"""Du schreibst das Ergebnis fuer einen Karriere-Test. Antworte NUR mit diesem JSON, kein Text davor oder danach:

{{
  "beschreibung": "<2-3 kurze Saetze>",
  "job_teaser": "<1 Satz>",
  "superkraft": "<1 Satz>",
  "kryptonit": "<1 Satz>"
}}

DATEN DER PERSON:
Karriere-Typ: {type_name} ({d1}-{d2}){" (Generalist)" if is_gen else ""}
Profil (0-100, hoch = stark ausgepraegt): {profile}
Staerkste Richtung: {d1}
Zweitstaerkste: {d2}
Schwaechste Richtung: {d_low}
Passende Jobs: {jobs_list}

ANKER (Ton & Identitaet des Typs — als Vorlage fuer den Stil, NICHT 1:1 abschreiben):
Typische Superkraft: "{anchor['superkraft']}"
Typisches Kryptonit: "{anchor['kryptonit']}"

SO INDIVIDUALISIERST DU:
- superkraft: Nimm die Identitaet von "{d1}" und faerbe sie mit "{d2}" ein. Konkret und
  ueberraschend — der Satz soll sich anfuehlen wie "woher wissen die das?".
- kryptonit: Leite es aus der schwaechsten Richtung ("{d_low}") ab — das, was diese Person
  am ehesten nervt oder auslaugt. Lustig aber wahr.
- beschreibung: Was treibt die Person an, was nervt sie. Wie ein Kumpel, der sie gut kennt.
- job_teaser: Neugierig auf die Jobs machen, mit Bezug zum Profil.

REGELN (streng):
- Deutsch, Du-Form, einfache Sprache, Berufsschulniveau, keine Fachbegriffe.
- Vermutend: "koennte", "scheint", "wahrscheinlich" — KEINE absoluten Aussagen.
- KEINE Vorhersagen ueber ungetestete Faehigkeiten. Nichts erfinden, nur was aus dem Profil folgt.
- Niemals "als wie". Keine Emoji. Keine erfundenen Statistiken (nicht "nur 8% ...").

✅ "Du ueberzeugst Leute wahrscheinlich eher durch Begeisterung als durch Druck."
✅ "Routine und starre Vorgaben duerften dir schnell die Energie rauben."
❌ "Du wirst jeden Raum erobern." (zu absolut)
❌ "Kaltakquise liegt dir nicht." (Urteil ueber ungetestete Faehigkeit)"""

        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            result["ai_description"] = data.get("beschreibung")
            result["ai_job_teaser"] = data.get("job_teaser")
            result["ai_superkraft"] = data.get("superkraft")
            result["ai_kryptonit"] = data.get("kryptonit")
        else:
            result["ai_description"] = text
            result["ai_job_teaser"] = None
    except Exception as e:
        result["ai_description"] = None
        result["ai_error"] = str(e)

    return result


@app.post("/api/fit")
async def post_fit(req: FitRequest):
    """Generiere job-spezifische Fit-Analyse via Claude."""
    dim_labels = {"R": "Realistisch", "I": "Forschend", "A": "Kreativ",
                  "S": "Sozial", "E": "Unternehmerisch", "C": "Organisierend"}
    scores_str = ", ".join([f"{dim_labels.get(k, k)}: {v}" for k, v in req.scores.items()])

    answers_section = ""
    if req.fit_answers:
        scale = {-2: "Stimmt gar nicht", -1: "Eher nicht", 0: "Teils-teils", 1: "Eher ja", 2: "Stimmt voll"}
        lines = [f'- "{a["question"]}": {scale.get(a["value"], str(a["value"]))}' for a in req.fit_answers]
        answers_section = "\n\nSelbsteinschätzung des Users (8 Fragen zum Job-Fit):\n" + "\n".join(lines)
        answers_note = "- Nutze die Selbsteinschätzung als Hauptquelle fuer Staerken und Gaps — sie ist direktes Signal"
    else:
        answers_note = "- Leite Staerken und Gaps aus den RIASEC-Scores ab"

    prompt = f"""Analysiere den Job-Fit fuer den Job "{req.job_name}".

RIASEC-Profil: {req.code}
Dimension-Scores (Rohwerte -12 bis +12): {scores_str}{answers_section}

Antworte in GENAU diesem JSON, kein Fliesstext davor oder danach:

{{
  "fit_score": <Zahl 50-88, realistisch auf Basis aller vorliegenden Daten>,
  "fit_headline": "<1 Satz, stärkste Verbindung zwischen Profil und Job, Du-Form>",
  "strengths": [
    {{"name": "...", "body": "..."}},
    {{"name": "...", "body": "..."}},
    {{"name": "...", "body": "..."}}
  ],
  "gaps": [
    {{"name": "...", "body": "...", "tag": "lernbar"}},
    {{"name": "...", "body": "...", "tag": "steuerbar"}}
  ],
  "lever": {{
    "skill": "...",
    "text": "... koennte deinen Fit um ~X% heben."
  }},
  "resources": [
    {{"kind": "book", "title": "...", "author": "...", "price": "ca. €X", "cta": "Auf Amazon ansehen", "for": "..."}},
    {{"kind": "coach", "title": "...", "author": "1:1 Coaching", "price": "ab €120/Session", "cta": "Coach finden", "for": "..."}}
  ]
}}

Regeln:
- fit_score: ehrlich, 60-80 ist realistisch
- strengths: 3 Staerken, je 2 Saetze body, konkret auf den Job bezogen
- gaps: 2 ehrliche Luecken. tag: "lernbar" = Skill, "steuerbar" = Persoenlichkeit, "mismatch" = Interessens-Mismatch
- lever: wichtigster Hebel, mit geschaetzter Fit-Verbesserung in Prozent
- resources: echte Buecher/Kurse, maximal 2
- {answers_note}
- Deutsch, Du-Form, kein HR-Jargon, kurze Saetze, NIEMALS als-wie"""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "parse_error", "raw": text[:200]}
    except Exception as e:
        return {"error": str(e)}


# ─── Frontend Routes ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/assessment", response_class=HTMLResponse)
async def assessment(request: Request):
    return templates.TemplateResponse("assessment.html", {
        "request": request,
        "items": get_shuffled_items()
    })


@app.get("/ergebnis", response_class=HTMLResponse)
async def ergebnis(request: Request):
    return templates.TemplateResponse("ergebnis.html", {"request": request})


@app.get("/story", response_class=HTMLResponse)
async def story(request: Request):
    return templates.TemplateResponse("story.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse)
async def jobs(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/fit-intro", response_class=HTMLResponse)
async def fit_intro(request: Request):
    return templates.TemplateResponse("fit-intro.html", {"request": request})


@app.get("/fit-check-post", response_class=HTMLResponse)
async def fit_check_post(request: Request):
    return templates.TemplateResponse("fit-check-post.html", {"request": request})


@app.get("/teaser", response_class=HTMLResponse)
async def teaser(request: Request):
    return templates.TemplateResponse("teaser.html", {"request": request})


@app.get("/premium", response_class=HTMLResponse)
async def premium(request: Request):
    return templates.TemplateResponse("premium.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(path):
        return FileResponse(path)
    return HTMLResponse(status_code=204)


# ─── Health Check ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.1.0"}
