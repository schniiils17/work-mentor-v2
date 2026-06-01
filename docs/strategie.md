# Work Mentor — Strategie & Roadmap

> Wird nur bei Strategie-Themen geladen, nicht bei jeder Coding-Session.
> Stand: Mai 2026.

## Übergeordnete Strategie

**Trichter-Modell:**
- Screen 1–3 = gratis, viral, bringt Leute (vorgefertigt, skalierbar)
- Screen 4–5 = gratis, baut Tiefe (halb-individuell)
- Screen 6–7 = Premium, verdient Geld (voll individuell, KI-generiert)

**Monetarisierung:**
- 80 % Premium-Reports (€19–29)
- 15 % Affiliate in Reports (Amazon-Bücher ~4,5 %, Udemy-Kurse 10–15 %,
  Coaches 20–25 %). Amazon-Affiliate-Tag: `workmentor21-21`
- 5 % Coach-Vermittlung (langfristig)

**Vision:**
- Kurzfristig: viral durch teilbare Tier-Ergebnisse (Modell 16Personalities)
- Mittelfristig: Benchmark-Daten nach 1000+ Usern
  ("durchsetzungsstärker als 73 % aller Vertriebsleiter-Aspiranten")
- Langfristig: B2A API (Business-to-Agent) — KI-Agents nutzen Work Mentor
  als Assessment-Engine

---

## Roadmap bis Launch

### Launch-kritisch (MUSS vor Launch)
- [ ] **Screen 5 — Fit-Check** (5 Persönlichkeits- + 3 Skill-Fragen, ~3 Min,
      job-spezifisch)
- [ ] **Screen 6 — Teaser mit Blur** (Stärken sichtbar, Gaps geblurrt →
      Neugier-Lücke)
- [ ] **Screen 7 — Premium-Report + Stripe** (komplette Gap-Analyse,
      KI-generiert, PDF)
- [ ] Übergangstexte zwischen Screens (ausgetextet in Journey-V3-Doku)
- [ ] Conversion-Events für GA4 + Meta Pixel einrichten

### Nach Launch (kann warten)
- Landing-Page-SEO pro Job (CMS Collections)
- Benchmark-Daten
- B2A API
- Desktop-Version
- Adaptives Assessment (Fragen nachladen basierend auf Scores)

### Status der Screens (V3)
| Screen | Status |
|--------|--------|
| 1 Landing | ✅ Live |
| 2 Assessment (Likert-im-Chat, 36 Fragen) | ✅ Live |
| 3 Karriere-Tier Dashboard (Hexagon, Superkraft/Kryptonit) | ✅ Live |
| 3b Story-Karte (9:16, /story) | ✅ Live |
| 4 Job-Matches | 🔲 konzipiert |
| 5 Fit-Check | 🔲 offen |
| 6 Teaser mit Blur | 🔲 offen |
| 7 Premium-Report + Stripe | 🔲 offen |

### Weitere offene TODOs
- [ ] Tier-Illustrationen (Flat Editorial, NICHT 3D/Cartoon — wurde abgelehnt).
      7 Artworks: 6 Tiere + Chamäleon.
- [ ] Sticky Fortschrittsbalken-Bug (verschwindet beim Scrollen)
- [ ] Feedback-Buttons statt Warteliste
- [ ] Logo final
- [ ] CookieYes verifizieren
- [ ] Instagram Ads schalten (erst wenn Tracking steht)
- [ ] Synchronen Claude-Call in `app/main.py` auf async umstellen (`AsyncAnthropic` +
      `await`) — synchrone Calls waren laut Projekt-Historie Ursache für Timeout-Probleme.
- [ ] Klären ob Bayesian Smoothing für Score-Berechnung gewollt ist — war als
      Design-Entscheidung dokumentiert, ist aber aktuell nicht implementiert.

---

## Go-to-Market

**Bisher:**
- Soft Launch über privates Instagram (~900 Follower) am 18.05.2026 — wenig
  Traffic, kaum Assessments gestartet.
- Grundidee: Freundeskreis + LinkedIn zuerst, dann SEO, Instagram Ads später.

**Erkenntnisse:**
- Instagram Story allein bringt kaum Traffic. Privates Insta ist nicht der
  richtige Kanal für ein Produkt.
- Nils will authentisch bleiben — "E-Mails sammeln fühlt sich eklig an",
  kein Funnel-Marketing. Wunsch: "TikTok-Vibes", Leute kommen von selbst.

**Offene GTM-Fragen:**
- Wann Instagram Ads schalten? (Tracking muss erst stehen)
- Wie den viralen Loop der Share-Karten triggern?
- SEO-Strategie für Landing Pages pro Job-Kategorie?

---

## Offene strategische Entscheidungen
1. Wie soll der Premium-Report konkret aussehen? (€19–39 PDF fühlt sich für
   Nils noch "dünn" an)
2. Welche Paid-Modelle testen? (Report, Abo, Coaching-Vermittlung, B2B)
3. Wann und wie Ads schalten?
4. Soll der Chat-Mentor einen Namen bekommen?
5. Free vs. Paid: Was genau wird geblurrt?

## Risiken & Annahmen
- **Annahme** (ungetestet): Karriere-Typ als Tier ist viral genug zum Teilen.
- **Annahme** (nicht validiert): 2–5 % Freemium-zu-Paid-Conversion.
- **Risiko**: Railway Cold Start — UptimeRobot-Ping ist Workaround, nicht Lösung.
- **Risiko**: 24 Fragen evtl. zu lang (Länge hat aber nur ~2,3 % Einfluss auf
  Completion Rate).
- **Unsicherheit**: Welches Paid-Produkt User wirklich wollen.
  Nils' Haltung: "Erst launchen, dann User fragen."
- **Budget**: ~100 € Invest, danach Kosten optimieren.
