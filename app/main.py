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
import math

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

class JobsRequest(BaseModel):
    scores: dict          # normalisiert 0-100 pro Dimension (R,I,A,S,E,C)
    code: str
    custom_job: str = ""  # gesetzt = nur diesen einen Job bewerten


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
- superkraft: Nimm die Identitaet von "{d1}" und faerbe sie mit "{d2}" ein. Konkret und ueberraschend.
- kryptonit: Leite es aus der schwaechsten Richtung ("{d_low}") ab — das, was diese Person
  am ehesten nervt oder auslaugt. Lustig aber wahr.
- beschreibung: Was treibt die Person an, was nervt sie. Wie ein Kumpel, der sie gut kennt.
- job_teaser: Neugierig auf die Jobs machen, mit Bezug zum Profil.

STIL von superkraft & kryptonit (WICHTIG):
- Genau wie die Anker oben: eine kurze, knackige Phrase im Praesens.
- KEIN "Du koenntest ...", KEINE Weichmacher (kein "wahrscheinlich/vielleicht/duerfte").
  Es ist eine Archetyp-Zeile, kein Gutachten.
- superkraft = eine Faehigkeit als Infinitiv-Phrase. kryptonit = eine Situation, die auslaugt.
✅ superkraft: "Ideen vorantreiben, ohne den Bezug zur Realitaet zu verlieren."
❌ superkraft: "Du koenntest Projekte vorantreiben, ohne dabei den Bezug zur Realitaet zu verlieren." (zu weich, klingt schief)
✅ kryptonit: "Endlose Detailarbeit ohne den grossen Zusammenhang."
❌ kryptonit: "Detailarbeit raubt dir vermutlich die Motivation." (Weichmacher, kein Archetyp)

REGELN fuer beschreibung & job_teaser:
- Deutsch, Du-Form, einfache Sprache, Berufsschulniveau, keine Fachbegriffe.
- Vermutend: "koennte", "scheint", "wahrscheinlich" — KEINE absoluten Aussagen.
- KEINE Vorhersagen ueber ungetestete Faehigkeiten. Nichts erfinden, nur was aus dem Profil folgt.
✅ beschreibung: "Du ueberzeugst Leute wahrscheinlich eher durch Begeisterung als durch Druck."
❌ beschreibung: "Du wirst jeden Raum erobern." (zu absolut)

GILT IMMER: Niemals "als wie". Keine Emoji. Keine erfundenen Statistiken (nicht "nur 8% ...")."""

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


# RIASEC-Congruenz: deterministischer Match-Score aus Profil-Ähnlichkeit.
# Cosinus zwischen User-Profil und dem vom Job geforderten Profil, gemappt auf
# 60–96 % (Produkt-Philosophie: keine 0/100 %, Minimum 60). Gleicher User +
# gleicher Job ergibt IMMER denselben Wert — das ist der Glaubwürdigkeits-Kern.
def _match_score(user_scores: dict, job_riasec: dict) -> int:
    dims = ["R", "I", "A", "S", "E", "C"]
    u = [max(0.0, float(user_scores.get(d, 0) or 0)) for d in dims]
    j = [max(0.0, float(job_riasec.get(d, 0) or 0)) for d in dims]
    nu = math.sqrt(sum(a * a for a in u))
    nj = math.sqrt(sum(b * b for b in j))
    if nu == 0 or nj == 0:
        return 60
    cos = sum(a * b for a, b in zip(u, j)) / (nu * nj)  # ~0.5 .. 1.0
    score = 60 + (cos - 0.60) / (1.0 - 0.60) * 36         # 0.60->60, 1.0->96
    return int(max(60, min(96, round(score))))


@app.post("/api/jobs")
async def post_jobs(req: JobsRequest):
    """Generiere profilpassende Archetyp-Jobs (Claude) und berechne den
    Match-Score deterministisch aus der RIASEC-Congruenz."""
    dim_labels = {"R": "Realistisch", "I": "Forschend", "A": "Kreativ",
                  "S": "Sozial", "E": "Unternehmerisch", "C": "Organisierend"}
    profile = ", ".join([f"{dim_labels.get(k, k)}: {v}" for k, v in req.scores.items()])

    if req.custom_job:
        task = f'''Bewerte EINEN konkreten Beruf: "{req.custom_job}".
Gib genau ein Job-Objekt zurueck. Sei ehrlich — wenn der Job schlecht zum Profil passt,
schaetze sein RIASEC-Profil trotzdem realistisch (der Score wird separat berechnet).'''
        shape = '{ "jobs": [ {"title": "...", "riasec": {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}, "salary": "...", "desc": "..."} ] }'
        n_note = "- Genau 1 Job (der genannte). Titel ggf. sauber ausformuliert."
    else:
        task = "Schlage 7 konkrete Berufe (Archetypen, keine offenen Stellen) vor, die zu diesem Profil passen."
        shape = '{ "jobs": [ {"title": "...", "riasec": {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}, "salary": "...", "desc": "..."}, ... ] }'
        n_note = "- 7 Jobs. Mix: 4-5 starke Treffer + 2-3 die spannend, aber weniger offensichtlich sind (Range, nicht nur das Naheliegende)."

    prompt = f"""{task}

User-RIASEC-Profil (0-100, hoch = stark ausgepraegt): {profile}
Top-2: {req.code}

Antworte NUR mit diesem JSON, kein Text davor oder danach:
{shape}

Regeln:
- riasec = welches Profil DER JOB verlangt (NICHT das des Users). Schaetze realistisch
  aus deinem O*NET-/Berufskunde-Wissen, 0-100 pro Dimension.
- salary: realistische deutsche Brutto-Jahresspanne, grob (z.B. "45.000 - 72.000").
  Keine erfundene Praezision, kein Euro-Zeichen.
- desc: 1 kurzer Satz, Du-Form, was man da konkret tut. Kein HR-Jargon.
- Deutsche Berufsbezeichnungen. Keine erfundenen Statistiken.
{n_note}"""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if not m:
            return {"error": "parse_error", "raw": text[:200]}
        data = json.loads(m.group())
        jobs = []
        for j in data.get("jobs", []):
            score = _match_score(req.scores, j.get("riasec", {}))
            jobs.append({
                "title": j.get("title", ""),
                "match": score,
                "salary": j.get("salary", ""),
                "desc": j.get("desc", ""),
            })
        jobs.sort(key=lambda x: x["match"], reverse=True)
        return {"jobs": jobs}
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
