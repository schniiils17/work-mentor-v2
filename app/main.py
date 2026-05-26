"""Work Mentor 2.0 — FastAPI Backend + Frontend"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os

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
    value: int  # -3 to +3 (Likert scale)

class AssessmentRequest(BaseModel):
    answers: List[Answer]


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
        
        prompt = f"""Schreib 2-3 kurze Saetze ueber jemanden mit diesem Profil.

Scores: {profile}
Typ: {d1}-{d2}{" (Generalist)" if is_gen else ""}

Regeln:
- Einfache Sprache. Kurze Saetze. Wie ein Kumpel der dich gut einschaetzt.
- Vermutend: wahrscheinlich, vermutlich, koennte sein
- Sag was die Person antreibt und was sie eher nervt
- Max 3 Saetze, keine Fachbegriffe, kein Berater-Deutsch
- Deutsch, Du-Form"""
        
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        result["ai_description"] = msg.content[0].text
    except Exception as e:
        result["ai_description"] = None
        result["ai_error"] = str(e)
    
    return result


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
