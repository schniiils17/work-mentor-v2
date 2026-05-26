"""Work Mentor 2.0 — FastAPI Backend + Frontend"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os

from app.holland import ITEMS, assess

app = FastAPI(title="Work Mentor 2.0")

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
    """Liefere alle Assessment-Items."""
    return {"items": ITEMS}


@app.post("/api/assess")
async def post_assess(req: AssessmentRequest):
    """Berechne das Ergebnis aus den Likert-Antworten."""
    answers = [{"item_id": a.item_id, "value": a.value} for a in req.answers]
    result = assess(answers)
    return result


# ─── Frontend Routes ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/assessment", response_class=HTMLResponse)
async def assessment(request: Request):
    return templates.TemplateResponse("assessment.html", {
        "request": request,
        "items": ITEMS
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
