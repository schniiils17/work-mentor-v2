"""Work Mentor 2.0 — FastAPI Backend + Frontend"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict
import os
import json
import re

from app.holland import ITEMS, assess, get_shuffled_items, _dim_label
import anthropic
import os

app = FastAPI(title="Work Mentor 3.0")

claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

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
    scores: Dict[str, int]
    code: str
    fit_answers: List[Dict] = []  # [{question, value}] from post-payment check


@app.get("/api/items")
async def get_items():
    """Liefere Assessment-Items in zufälliger Reihenfolge."""
    return {"items": get_shuffled_items()}


@app.post("/api/assess")
async def post_assess(req: AssessmentRequest):
    """Berechne das Ergebnis aus den Likert-Antworten + KI-Beschreibung."""
    answers = [{"item_id": a.item_id, "value": a.value} for a in req.answers]
    result = assess(answers)
    
    # KI-Beschreibung generieren
    try:
        scores = result["scores"]
        code = result["code"]
        d1 = _dim_label(code[0])
        d2 = _dim_label(code[1])
        is_gen = result.get("is_generalist", False)
        
        sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        profile = ", ".join([f"{_dim_label(d)}:{v}" for d, v in sorted_dims])
        
        jobs_list = ", ".join([j["title"] for j in result.get("jobs", [])])
        
        prompt = f"""Zwei Aufgaben. Antworte in genau diesem Format:

BESCHREIBUNG: [2-3 kurze Saetze]
JOB_TEASER: [1 Satz]

Profil-Scores: {profile}
Typ: {d1}-{d2}{" (Generalist)" if is_gen else ""}
Passende Jobs: {jobs_list}

Regeln fuer BESCHREIBUNG:
- Einfache Sprache. Kurze Saetze. Wie ein Kumpel der dich gut einschaetzt.
- Vermutend: wahrscheinlich, vermutlich, koennte sein
- Sag was die Person antreibt und was sie eher nervt
- Max 3 Saetze, keine Fachbegriffe
- Deutsch, Du-Form

Regeln fuer JOB_TEASER:
- 1 kurzer Satz der neugierig auf die Job-Matches macht
- Bezieh dich auf das konkrete Profil
- Kein gelogen-klingendes Zeug wie nur 8 Prozent haben dein Profil"""
        
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text
        
        if "BESCHREIBUNG:" in text and "JOB_TEASER:" in text:
            parts = text.split("JOB_TEASER:")
            result["ai_description"] = parts[0].replace("BESCHREIBUNG:", "").strip()
            result["ai_job_teaser"] = parts[1].strip()
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

    # Build fit-answers section if provided
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


@app.get("/fit-check-post", response_class=HTMLResponse)
async def fit_check_post(request: Request):
    return templates.TemplateResponse("fit-check-post.html", {"request": request})


@app.get("/fit-intro", response_class=HTMLResponse)
async def fit_intro(request: Request):
    return templates.TemplateResponse("fit-intro.html", {"request": request})


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
    return {"status": "ok", "version": "3.0.0"}
