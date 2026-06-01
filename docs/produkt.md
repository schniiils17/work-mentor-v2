# Work Mentor — Produkt im Detail

> Wird bei Produkt-/Feature-Arbeit geladen. Stand: V3 (Mai 2026).

## Kernproblem & Zielgruppe

**Problem:** Menschen treffen die Job-Entscheidung nach Bauchgefühl statt nach
Daten. Zwischen "gratis Google/ChatGPT" und "teurer Coach (€200/h)" gibt es
nichts, das "Wer bin ich?" mit "Was braucht DIESER Job?" verbindet — schnell,
günstig, ehrlich.

**Zielgruppe:** 25–40 Jahre, mitten im Berufsleben, ahnt dass mehr geht.
Mix aus Neugier und leichter Unsicherheit. Will Klarheit, keine 200-Fragen-Tests.

## Produktphilosophie

- **"Holland ist die Tür, KI ist der Raum"** — die 15 Karriere-Typen
  (Tier-Avatare) sind der virale Marketing-Hook; echte Individualität kommt
  durch KI-Interpretation der vollen 6 RIASEC-Dimensionen.
- **Ehrlichkeit bei Gaps**, 3 Arten:
  - Skill-Gaps → lernbar
  - Persönlichkeits-Awareness → bewusst steuerbar
  - Interessens-Mismatch → NICHT änderbar → ehrlich benennen, keine falschen
    Versprechen
- **Tendenzen, keine Diagnosen** — mit ~21 Items zeigt man Richtungen.
- **Respektvoll, nie belehrend.**
- **Kein Karriere-Coach** — Spiegel + Vorhersage, kein "90-Tage-Plan"
  (klingt nach Upsell).
- **Kompass, nicht Spiegel**: "Passt DU zu DIESEM Job?" — nicht "Wer bist du?"
  (Abgrenzung zu 16Personalities).
- Auf der Landing Page **"Arbeitstyp"** statt "Karriere-Typ" (universeller).

---

## Die Journey (7 Screens)

1. **Landing** — "Finde raus, welcher Arbeitstyp du wirklich bist." Ein Button,
   keine Anmeldung.
2. **Holland-Assessment** — 36 Fragen, ~5 Min, Likert-Skala im Chat-Look
   (5-Punkt-Skala als Quick-Reply-Chips).
3. **Karriere-Typ** ← Viral-Moment — Tier-Name + Superkraft + Kryptonit +
   Share-Karte. (Kryptonit ist der virale Teile-Trigger.)
4. **Job-Matches** — Top 5 Jobs mit Match-% ODER "Ich hab einen Job im Kopf".
5. **Fit-Check** — 5 Persönlichkeits- + 3 Skill-Fragen (~3 Min, job-spezifisch).
6. **Gratis-Ergebnis (Teaser)** — Stärken sichtbar, Gaps geblurrt.
7. **Premium-Report (€19–29)** — komplette Gap-Analyse, KI-generiert, PDF.

---

## RIASEC-System (V3)

6 Dimensionen, je ein Tier-Maskottchen + Farbe:

| Code | Dimension | Tier | Farbe |
|------|-----------|------|-------|
| R | Realistic | Wolf | Stahlblau `#475569` |
| I | Investigative | Eule | Indigo `#4338CA` |
| A | Artistic | Fuchs | Amber `#F59E0B` |
| S | Social | Delphin | Teal `#0D9488` |
| E | Enterprising | Adler | Orange `#EA580C` |
| C | Conventional | Oktopus | Violett `#7C3AED` |
| — | Generalist | Chamäleon | Multi-Gradient |

**Dynamisches Farbsystem:** `--primary` = Haupttier-Farbe,
`--accent` = Zweittyp-Farbe. 30 Kombinationen automatisch.
Grenzfälle: >15 % Abstand = klarer Haupttyp, <5 % = Chamäleon.

**15 Karriere-Typen:** jeder mit Name, Beschreibung, Stärken, Superkraft,
Kryptonit und 3 passenden Jobs (Match-Score + Gehalt).

---

## Design-System

- **Farben**: Deep Navy `#1a3a5c` (primary), Warm White `#FAF9F6` (BG),
  Grün (Stärken), Amber (Hebel), Indigo (Insights), Lila (Motive).
- **Schrift**: Fraunces/Instrument Serif (Headlines) + Geist (Body).
  ⚠️ Offener Punkt: Nils findet Serif + Fachsprache "zu akademisch" — schüchtert
  Nicht-Akademiker ein. Bei Design-Arbeit darauf achten.
- **Radii**: 10 / 14 / 18 / 24 / 9999 px
- **Animation**: `cubic-bezier(0.22, 1, 0.36, 1)`, Score count-up 1400ms,
  Spider-Chart 1100ms.

---

## Evaluator (V3, aktiv)

Kern der Ergebnis-Generierung. Regeln:

1. Tendenzen, keine Diagnosen.
2. Respektvoll, nie belehrend — "könnte" statt "wird".
3. Keine Job-Vorhersagen über die gemessenen Dimensionen hinaus.
4. Kurze Insights — 1–2 Sätze pro Dimension.
5. Keine Job-Skills erfinden.
6. Du-Form, einfach, Berufsschulniveau, NUR Deutsch.
7. NIEMALS "als wie".
8. Keine Halluzinationen — nur was aus den Antworten folgt.
9. Labels: "Sehr stark", "Stark", "Ausgeglichen", "Entwicklungsbedarf".
10. Match-Score-Minimum 60 % (60–69 Solide, 70–79 Gut, 80–89 Sehr stark,
    90+ Perfekt).
11. Skill-Fit-Sprache: User HAT den Job noch nicht → als Potenzial formulieren.

**JSON-Output-Schema:**
```json
{
  "match_score": 72,
  "match_label": "Kurzer ermutigender Satz",
  "skill_fits": [{"skill": "...", "beschreibung": "...", "fit": "passt_gut/solide_basis/dein_hebel", "fit_grund": "..."}],
  "dimensions": [{"dimension": "...", "label": "...", "user_score": 35, "job_relevanz": "hoch", "bewertung": "...", "insight": "..."}],
  "staerken": [{"dimension": "...", "begruendung": "..."}],
  "hauptgap": {"dimension": "...", "label": "...", "beschreibung": "...", "intensity": "low/medium/high"},
  "bright_vs_dark": {"beschreibung": "..."},
  "motive": {"profil": "...", "job_fit": "..."},
  "main_potential": "...",
  "main_risk": "...",
  "buchempfehlung": {"titel": "...", "autor": "...", "begruendung": "...", "amazon_suchbegriff": "..."},
  "naechster_schritt": "..."
}
```

---

## Legacy (nur Referenz — NICHT mehr aktiv)

- **V1** (April): Make + Google Sheets + OpenAI/Claude/Perplexity, Framer-Frontend,
  spezifischer Zieljob-Check, statischer Flow.
- **V2** (Mai): Python/FastAPI, adaptiver Diagnostik-Agent, **7-Dimensionen-Modell**
  (Durchsetzung, Empathie, Gewissenhaftigkeit, Offenheit, Extraversion,
  Stressresistenz, Autonomie). Adaptive Diagnostik geparkt für später.
- Bei Widersprüchen im alten Code gilt: **V3 (RIASEC) ist die Wahrheit.**
- Mentor-Charakter (System Prompt v5): ruhig, aufmerksam, warmherzig, hört mehr
  zu als er redet, wertet nie, Du-Form, Berufsschulniveau, kein HR-Jargon.
