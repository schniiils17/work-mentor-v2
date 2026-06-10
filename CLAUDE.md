# Work Mentor — Claude Code Kontext

> Mobile-First Karriere-Webapp unter **work-mentor.com**. Hilft Menschen
> herauszufinden, welcher Arbeitstyp sie sind und welche Jobs zu ihnen passen.
> Aktueller Stand: **V3** (RIASEC/Holland-basiert). Alles Ältere ist Legacy.

## Weiterführende Docs

Diese Datei ist bewusst schlank. Für Details bei Bedarf nachschlagen:
- **Strategie, Roadmap, Monetarisierung, GTM** → `docs/strategie.md`
- **Produkt im Detail** (7 Screens, RIASEC, 15 Typen, Philosophie) → `docs/produkt.md`
- **Markt & Wettbewerber** (reine Referenz) → `docs/markt.md`

---

## Wer ist Nils (und wie mit ihm arbeiten)

- **Vibecoder**: kennt Make, Framer, Cursor gut. Schreibt selbst keinen Code,
  ist Anfänger bei Backend/API. Versteht aber Prompts und LLM-Logik sehr gut.
- **Technische Erklärungen einfach halten, mit Analogien.** Keine Fachbegriffe
  ohne Erklärung.
- **Kosteneffizient arbeiten**: bei einfachen Aufgaben kurz und knapp, volle
  Tiefe nur bei schweren. Keine Platzhalter, keine Füllsätze.
- **Direkt sein, Meinung haben.** Kein "Great question!", kein Geschwurbel.
- Motiviert sich durch Diskussion, nicht durch Planung. Kritischer Tester —
  erkennt sofort, wenn etwas zu wertend, zu absolut oder zu oberflächlich ist.
- Sprache: **Deutsch, Du-Form.**

---

## Tech-Stack (V3 — verbindlich)

```
User (Mobile Browser)
  → work-mentor.com (IONOS DNS)
    → Railway (FastAPI: Backend + Frontend zusammen)
      → Claude API (Anthropic) für Auswertung & Skill-Research
```

- **Backend**: Python 3, FastAPI, async wo nötig
- **Frontend**: Jinja-Templates + statische HTML/JS. **Framer und Make werden NICHT mehr genutzt.**
- **KI**: `anthropic` Python SDK. Modell `claude-sonnet-4-20250514` für die langen/Volumen-Calls
  (assess, fit, jobs, job-context, job-check). `/api/insight` (kurze „Das bist du"-Krass-Zeile)
  läuft auf `claude-sonnet-4-6`. Ein Blind-Duell (`docs/model-duell-2026-06.md`) zeigte: Sonnet
  schreibt die kurze Zeile **besser** als Opus; Opus gewinnt nur bei längeren Texten, ist dort
  aber zu langsam (Report-Timeout). **Saubere Texte kommen vom Prompt, nicht vom teureren Modell.**
  (Läuft über API-Key, NICHT über dieses Abo.)
- **Hosting**: Railway Hobby Plan, Auto-Deploy von GitHub `main`
- **Repo (aktiv)**: `schniiils17/work-mentor-v2` (enthält V3-Code)
- **Keine persistente DB** in V3 — Ergebnisse client-seitig gehalten

### Wichtige Backend-Dateien
| Datei | Zweck |
|-------|-------|
| `app/main.py` | FastAPI App, API-Endpoints, Pydantic-Models, Claude-Prompt (inline) |
| `app/holland.py` | RIASEC-Items (36), Typ-Mapping (15 Typen), Job-Datenbank, Scoring-Logik |

---

## Code-Konventionen

- **Naming**: `snake_case` (Python), `camelCase` (JS/TS)
- **API-Format**: JSON. Evaluator-Output ist **strikt JSON, kein Fließtext.**
- **Claude-Prompts**: detaillierte Instruktionen mit ✅/❌-Beispielen im Prompt.
- **Async statt sync** bei API-Calls (synchrone Calls verursachten Timeouts).

### Vermeiden
- Keine synchronen API-Calls, wo async möglich ist.
- Keine hardcodierten Webhook-URLs (Legacy aus der Make-Zeit).
- **Keine deutschen typografischen Anführungszeichen (`„…"`) in JavaScript** —
  das schließende `"` ist ASCII U+0022 und bricht JS-String-Delimiter.
- Bei DSGVO-kritischen Scripts `type="text/plain"` + `data-cookieyes` nicht
  vergessen (GA4 + Meta Pixel laden erst nach Cookie-Consent).

---

## Copy & Ton (im Produkt)

- **Deutsch, Du-Form, Berufsschulniveau.** Kurze Sätze. Klare Sprache.
- **Kein HR-Jargon**: "Kundenbeziehungen" statt "CRM", "Menschen führen" statt
  "Leadership".
- **Tendenzen, keine Diagnosen.** "könnte" statt "wird". Nie belehrend.
- Keine absoluten Aussagen ("Du vergisst keine Termine").
- Keine Vorhersagen über ungetestete Fähigkeiten ("Kaltakquise wird dir nicht
  liegen").
- Keine Halluzinationen — nur was aus den Antworten folgt.
- Grammatik: **niemals "als wie"** — nur "als" ODER "wie".
- **Keine Emoji im Produkt** — Lucide Icons statt Emoji.
- Bewertungs-Labels: NUR diese vier — **"Sehr stark", "Stark", "Ausgeglichen",
  "Entwicklungsbedarf"**. (Kein "Ausreichend" — klingt nach Schulnote.)

✅ "Du neigst dazu, erstmal zuzuhören bevor du dich einbringst"
✅ "Struktur und Planung scheinen dir zu liegen"
❌ "Du vergisst keine Termine" (zu absolut)
❌ "Kaltakquise wird dir nicht liegen" (Urteil über ungetestete Fähigkeit)

---

## Deploy-Workflow

```
Code ändern → git push (main) → Railway deployt automatisch
```
- Kein Staging/Preview — direkt auf Production.
- Aktuell keine Tests, keine CI/CD. Manuelles Testen durch Nils.
- **Secrets gehören NIE ins Repo.** Alle Keys (Anthropic, GitHub, Railway etc.)
  in `.env`, die via `.gitignore` ausgeschlossen ist. Nie in dieser Datei,
  nie in den Docs.

---

## Zentrale Architektur-Entscheidungen (Kurzform)

1. **Make → FastAPI**: Make war zu teuer und unflexibel.
2. **Framer → FastAPI-Frontend**: Framer war nur Code-Container, jetzt
   Backend + Frontend zusammen.
3. **Fester Statement-Pool statt Claude-generierter Fragen**: Claude
   interpretiert nur, generiert keine Fragen. 1 Claude-Call statt 15.
4. **Likert-im-Chat statt Chat-Situationsfragen**: Situationsfragen waren zu
   durchschaubar.
5. **Jooble deaktiviert**: zu langsam. Skill-Research nur über Claude (15–20s).
6. **Match-Score-Minimum 60%**: darunter demotiviert es User.
7. **Bayesian Smoothing**: zieht Extremwerte zur Mitte (keine 0%/100%).
