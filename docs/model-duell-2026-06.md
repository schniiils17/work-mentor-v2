# Modellwahl — Blind-Duell Sonnet 4.6 vs Opus 4.8 (Juni 2026)

> 6 Profile × 2 Textsorten × 2 Modelle, gleiche Prompts, blinde A/B-Richter (2 Stimmen, Position alterniert). 49 Agenten.

**Auszählung:** Krass-Zeile Sonnet 8:4 · Die-eine-Sache Opus 8:4. Kein Modell generell besser.

---

# Modellwahl: Sonnet 4.6 vs Opus 4.8 — Blind-Duell

## 1. Das Urteil

**Insight (Krass-Zeile): Sonnet gewinnt deutlich.** 8:4 für Sonnet, davon 8 deutliche Siege. Bei kurzen, pointierten Zeilen liefert Sonnet die besseren Treffer. Opus wirkt hier abstrakt/coachig ("eigenen Spielraum", "den Weg, den jemand anderes dir aufzeichnet") — zu kopflastig für eine knackige Zeile.

**Lever (Report): Opus gewinnt deutlich.** 8:4 für Opus, 7 deutliche Siege. Bei längeren, strukturierten Texten mit konkretem Hebel spielt Opus seine Stärke aus — Sonnet kippt hier in Coach-Imperative ("Üb mal, auch loszulassen") und absolute Aussagen ("kannst nicht jeden retten").

Kein Modell ist generell besser. Es kehrt sich pro Textsorte exakt um.

## 2. Macht Opus die "unsauberen Formulierungen" weg?

**Nein, nicht zuverlässig.** Opus produziert eigene Fehlerklasse:

- Beim Buchhalter-Lever (Opus gewinnt) hatte die unterlegene Sonnet-Version trotzdem den grammatisch gebrochenen Schachtelsatz "...anziehend findest – aber noch nicht richtig greifbar für dich ist" — aber das war Sonnet. **Wenn Opus verliert** (Vertriebsleiter-Insight), liefert es selbst Schachtelsätze mit Doppelpunkt-Konstruktion, schiefe Bilder ("aufzeichnet" statt "vorzeichnet") und Klischees ("Dinge durchziehen").
- Opus' typische Schwäche ist **Abstraktion/Coach-Jargon ohne konkreten ersten Schritt** ("mehr Einfluss als durch Durchsetzen allein", "kurz innezuhalten" ohne Mini-Aktion).

Heißt: Opus eliminiert nicht die Regelverstöße — es verschiebt sie von "anklagend/absolut" (Sonnets Hauptproblem) zu "abstrakt/kopflastig". Beide brauchen Prompt-Härtung. Das saubere Schreiben kommt nicht automatisch durchs teurere Modell.

## 3. Empfehlung pro Endpoint

**Krass-Zeile (insight): Sonnet 4.6.**
Doppelt begründet: Sonnet gewinnt die Qualität deutlich (8:4) UND ist relevant — Achtung: Latenz spielt hier kaum eine Rolle (Opus ~7s ist schnell genug). Aber Qualität schlägt klar zu Sonnet aus. Heute läuft das auf Opus — **das würde ich umstellen auf Sonnet 4.6.** Quick Win.

**Report (lever/fit): Bei Sonnet bleiben bzw. Sonnet 4.6 testen — NICHT auf Opus.**
Hier ist die Latenz der Killer: Opus 4.8 schwankt 40–120s und reißt den Teaser-Timeout. Das ist ein hartes Produkt-Problem, kein Schönheitsfehler. Opus' Qualitätsvorsprung beim Lever (8:4) ist real, aber **nicht 120s und kaputte Teaser wert.**
Reihenfolge:
1. Sonnet 4.6 als Report-Modell nehmen (vs. altem Snapshot ~31s → 4.6 ~40s, akzeptabel).
2. Prompt für den Lever härten gegen Sonnets Schwächen (Coach-Imperative, absolute Aussagen, halluzinierte Zahlen wie "25 Kinder").
3. Async/Teaser-Architektur nur bauen, wenn du Opus zwingend willst — aber das löst die Schwankung nicht, nur das Timeout-Symptom.

## 4. Fazit

Der Modell-Wechsel lohnt den Aufwand nicht — die Qualität steckt im Prompt: Opus' Lever-Vorsprung frisst die Latenz auf, und beide Modelle brechen dieselben Regeln (nur unterschiedlich), also bringt dich eine Prompt-Härtung weiter als jeder Modell-Tausch.
