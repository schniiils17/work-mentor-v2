# Scoring-Analyse — Work Mentor V3 (Juni 2026)

> Read-only Tiefen-Analyse des Produktkerns: Scoring von Test 1 (RIASEC/Holland)
> und Test 2 (Traits). Reine Diagnose — **nichts wurde geändert.** Jede
> Code-Aussage ist mit Datei:Zeile belegt; die drei load-bearing Behauptungen
> wurden zusätzlich von Hand am Code gegengeprüft (✓ verifiziert).

## Kurzfazit

Das Scoring funktioniert und produziert nutzbare Profile. Es ist handwerklich
solide, hat aber **drei belegte Schwachstellen** — und Test 1 hat ein
semantisches Problem bei der Skalen-Mitte. Nichts davon ist „kaputt", aber zwei
Punkte sind echte Bugs/Falschaussagen, die vor einem ernsthaften Launch raus
sollten.

---

## Frage 1 — Was misst die Mitte der Skala?

**Test 2 „Teils teils" (Wert 3) — sauber.** ✓
Zustimmungs-Skala („wie sehr trifft das zu?"). Die Mitte heißt eindeutig „mal so,
mal so / kommt drauf an" — echte Ambivalenz. Wird korrekt in den Dimensions-
Mittelwert eingerechnet (traits.py:78-81). **Reines Signal, kein Handlungsbedarf.**

**Test 1 „Unsicher" (Wert 0) — mehrdeutig.** ⚠️
Genuss-Skala („wie sehr würde dir das Spaß machen?", holland.py:19). „Unsicher"
vermischt zwei verschiedene Zustände:
- (a) echte Indifferenz: „ist mir egal"
- (b) Unwissenheit: „kenn ich nicht / weiß nicht"

Der Code trennt das nicht — jede 0 wird gleich addiert (holland.py:290-292).
Beide ziehen das Profil flach, und ein flaches Profil → „Generalist/Chamäleon"
(holland.py:379). Wer „Unsicher" als „kenn ich nicht" meinte, wird also evtl.
falsch als Chamäleon getypt. **Das ist die eine schwache Stelle bei der Mitte.**

---

## Frage 2 — Einzeln gemessen oder Gesamtbild? Wird ein Muster genutzt?

**Beides — erst einzeln, dann Gesamtbild.** Jede Antwort wird einzeln pro
Dimension verrechnet (Test 1: Summe -8..+8, holland.py:284-292; Test 2:
Mittelwert 1.0-5.0, traits.py:70-81). Daraus entsteht ein Gesamtbild: Test 1 →
Top-2-Code + Generalist-Flag; Test 2 → 7 Dimensions-Werte + Ranking. Am Ende
steht also ein Profil, nicht 24 Einzelurteile.

**Aber: „oft teils teils" wird NICHT als eigenes Signal genutzt.** ⚠️
- Test 1 prüft wenigstens grob die Varianz (`check_answer_quality`,
  holland.py:247-271): flaggt „immer dasselbe" / „zu uniform". ABER es flaggt
  nicht „zu viele Mittenwerte", und das Flag **blockiert nichts** — das Ergebnis
  wird trotzdem ausgeliefert (main.py liest `answer_quality` nicht aus).
- **Test 2 prüft GAR NICHTS** (traits.py:62-81). Wer 18× dasselbe klickt, kriegt
  trotzdem ein Insight. ✓ verifiziert — **das ist ein echter Bug.**

Ein Muster wie „die Person antwortet auf die Hälfte mit der Mitte" könnte etwas
aussagen (Satisficing, echte Ambivalenz, oder Unwissenheit) — wird aber nirgends
erfasst.

---

## Frage 3 — Welches Mittel-Label ist je Test besser? + alle Chips

| Test | aktuelle Mitte | Urteil | Empfehlung |
|------|----------------|--------|------------|
| Test 1 (Genuss) | „Unsicher" | ⚠️ mehrdeutig | **→ „Neutral"** (oder „Egal" / „Weder noch") — macht die Mitte klar zu „mir egal", nicht „kenn ich nicht" |
| Test 2 (Zustimmung) | „Teils teils" | ✅ ideal | **nichts ändern** |

**Dein Instinkt stimmt: pro Test ist das beste Label unterschiedlich**, weil die
Skalen verschiedene Dinge messen (Genuss vs. Zustimmung). Auf einer Zustimmungs-
Skala ist „Teils teils" der Standard-Mittenwert; auf einer Genuss-Skala ist
„Unsicher" mehrdeutig.

Die übrigen Labels (Gar nicht / Eher nicht / Gerne-Eher schon / Sehr gerne-Voll &
ganz) sind semantisch klar. Ein kleiner Sauberkeits-Punkt: in trait-check.html
existieren die Labels doppelt (Buttons Z. 86-90 + `VAL_LABELS` Z. 108) — müssen
synchron bleiben, sonst zeigt der Chat ein anderes Wort als der Button.

---

## Drei Schwachstellen (nicht gefragt, aber wichtig — alle ✓ am Code geprüft)

1. **Test 2 hat keinen Quality-Filter (Bug).** Stumpfes Durchklicken → trotzdem
   ein „Ergebnis". Test 1 hat wenigstens einen groben Check.
2. **„Bayesian Smoothing" ist falsch benannt.** Im Code (main.py:459-460) ist es
   simples Kappen auf 60-96 % (`max(60, min(96, …))`) — kein Bayesian-Verfahren.
   Steht falsch in CLAUDE.md (Punkt 7). Kann peinlich werden, wenn's jemand
   nachschlägt. Ehrliche Formulierung: „Match-Score-Untergrenze 60 %, Obergrenze
   96 % — verhindert demoralisierende 0 %- und scheinsichere 100 %-Werte."
3. **„96 % Recovery / wissenschaftlich geprüft" ist unbelegt.** Steht nur als
   Kommentar (traits.py:18-20). Kein Test, keine 28 Personas im Repo. Solange du
   nicht damit wirbst: egal. Sobald „wissenschaftlich validiert" Verkaufsargument
   wird: Problem.

**Item-Qualität (kleiner):** ME und NE haben kein einziges Umkehr-Item (alle
positiv gepolt) → anfällig für Ja-Sage-Tendenz. NE und RU/EI haben nur 2 Items
pro Dimension — unter dem üblichen Standard für stabile Messung.

---

## Frage 4 — Abhängigkeits-Karte (was hängt am Scoring?)

Dein Instinkt stimmt: Scoring-Änderungen kaskadieren. Die Kette:

```
Antwort → Dimensions-Score (holland.calculate_scores / traits.score_traits)
  ├─ Generalist-Schwelle (holland.py:312-314: top1<1, Differenz<3)
  │     └─ Typ vs. „Chamäleon"-Texte (main.py:113, TIER_ANCHORS)
  ├─ Top-2-Code → Job-Matches
  │     └─ _match_score (main.py:450-460: Kappen 60-96)
  └─ Normalisierung 0-100 (holland.py:388-390)
        └─ Report-Prompts /api/fit, /api/insight (Roh-Ranges hardcodiert im Prompt)
```

**Wenn du X änderst, muss Y mit:**
- **Skala/Aggregation ändern** → Generalist-Schwelle neu kalibrieren + die
  hardcodierten Roh-Ranges in den Prompts („Rohwerte -8 bis +8") anpassen, sonst
  rechnet die KI auf falscher Basis.
- **Mitte-Behandlung ändern** → Normalisierung + Match-Score-Mapping prüfen
  (wenn die durchschnittliche Ähnlichkeit kippt, landen viele Jobs auf dem
  Minimum 60 → keine Differenzierung mehr).
- **Likert-Skala 1-5 ändern (z.B. 1-6)** → die Konstante `6` in traits.py:78
  (Umkehr-Items) + alle Prompts.
- **Chip-Label Test 1 ändern** → nur HTML, aber die Roh-Range-Texte in den
  Prompts beachten.

**Risiko:** Es gibt **keine Tests**. Jede Scoring-Änderung müsste man an ~20-30
Test-Personas durchspielen, um zu sehen, wer vom Typ zum Generalist kippt.

---

## Priorisierung (Vorschlag — nichts davon ist umgesetzt)

**Billig + risikoarm (zuerst):**
1. Quality-Check für Test 2 (analog zu Test 1).
2. Test 1 „Unsicher" → „Neutral".
3. Die zwei Doku-Falschaussagen geradeziehen (Bayesian, 96 %).

**Größer / braucht echte Daten (später):**
4. Reverse-Keying für ME + NE ergänzen.
5. Generalist-Schwelle an echten Usern validieren.
6. Mittenwert-Muster als eigenes Signal erfassen (falls überhaupt gewollt).
