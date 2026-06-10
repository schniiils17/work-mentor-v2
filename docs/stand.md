# Stand & nächste Schritte

> Die *kurze* Übersicht zum Abhaken. Details: `journey-audit-2026-06.md` (Teardown),
> `research-2026-06.md` (Strategie), `research-text-eval-2026-06.md` (Text-Qualität).
> **Stand: 10. Juni 2026 · live V3.15.0**

---

## Was die vier großen Analyse-Läufe ergaben

1. **Bug-Hunt** (Code/UX) → 17 Bugs gefunden & gefixt (V3.14.0). *Hygiene erledigt.*
2. **Strategie-Recherche** (Preis, Kauf-Psychologie, erste Nutzer, Wettbewerb) → `research-2026-06.md`.
   Kern: 19 € ok / kein Abo als USP; Report = **Diagnose, kein Katalog**; jeden Satz an die echten
   Antworten koppeln; Wachstum über **SEO/Typ-Seiten**, nicht Viralität.
3. **Text-Qualitäts-Test** (Barnum-Eval, 2×) → die Einzeltexte sind **spezifisch & konsistent** (kein
   Horoskop). Härten/Generalist/Sprache gefixt (V3.15.0). Rest: Insight rutscht noch zu oft ins Negative.
4. **Journey-Audit** (jede Kachel + Kauf-Test) → **DER Befund:** die zwei Tests widersprechen sich, der
   User würde nicht zahlen und fühlt sich verarscht. `journey-audit-2026-06.md`.

## Die Kern-Erkenntnis (alles zusammen)

**Die Einzelteile sind gut — das System cohäriert nicht.** Test 1 (Interessen) und Test 2 (Persönlichkeit)
laufen getrennt und widersprechen sich (Typ „Systematiker" ↔ Report „Struktur ist nicht deine Stärke").
Genau diese Inkohärenz macht, dass es sich **nicht nach 19 € anfühlt** — nicht fehlendes Handwerk.

---

## Roadmap — Schritt für Schritt

### Phase 0 — Vertrauens-Killer sofort (Minuten, reine Copy)
- [ ] Preis konsistent **19 €** (Bezahl-Button zeigt fälschlich 20 €)
- [ ] „100 % kostenlos" → ehrliches Versprechen (Test gratis, Report 19 €)
- [ ] Tote Impressum/Datenschutz-Links (Pflicht vor Bezahlung)

### Phase 1 — Der rote Faden (DER Qualitätssprung)
- [ ] **Backend-Reconciliation:** beide Prompts kriegen Interessen-Typ + Superkraft als gleichwertigen
      Input + Regel „benenne die Spannung Interesse↔Können explizit"
- [ ] **Brücken-Kachel** im Report + **Setup-Satz** auf der Ergebnis-Seite
      (*„Struktur reizt dich — leicht fällt sie dir noch nicht — genau das ist dein Hebel."*)
- [ ] **fit_headline-Widerspruch** fixen (Headline aus den Badge-Ergebnissen ableiten)

### Phase 2 — Glaubwürdigkeit
- [ ] Fit-Score muss Reibung einrechnen (aktuell beide Fälle 78 %)
- [ ] Match-Badges spreizen (aktuell alles „Starke Passung")
- [ ] Teaser reicher (strengths[0] + geblurrte Vorschau), Report weniger gestreckt (2. Hebel, job-konkrete Schritte)
- [ ] Text-Reste: Insight = Selbstbild zuerst, Schwäche nur als Schluss-Pointe, kein Fremd-Gefühl

### Phase 3 — Wachstum (später, eigene Projekte)
- [ ] 15 deutsche SEO-Typ-Seiten (`/typen/…`)
- [ ] Teilbares Marken-Ergebnisbild + verspielte Typnamen
- [ ] Payment + Impressum/Datenschutz (zum Launch)
- [ ] A/B-Test 19 € vs. 24 €

---

*Pflege: erledigte Schritte abhaken; neue Erkenntnisse oben unter „Kern-Erkenntnis".*
