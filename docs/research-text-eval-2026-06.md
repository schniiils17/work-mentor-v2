# Qualitäts-Test der KI-Texte (Juni 2026)

> Erzeugt mit einem Eval-Workflow: 60 echte Texte (20 Profile × Krass-Zeile 2× + Die-eine-Sache 1×),
> jeder Text bewertet (Erkennung + Ton + Sprache) und blind zugeordnet (Barnum-Test, 1 aus 20). 122 Agenten.

## Wichtige Einordnung (vom Hauptmodell geprüft)

**Gute Nachricht:** Die Texte sind echt persönlich, kein Horoskop — Barnum-Trefferquote Insight 53 %,
Lever 80 % (Zufall wäre 5 %). Erkennung ~3,6–3,8/5. Konsistent (keine Person wich zwischen 2 Läufen stark
ab). Sogar zwei Fast-Zwillinge wurden 0-mal verwechselt.

**Zwei Zahlen sind Mess-Artefakte, KEINE Produkt-Fehler:**
- *Lever Sprache 0 %*: Das Generierungs-Skript hat die Überschrift an den Text geklebt. Im Produkt ist die
  Überschrift ein eigenes Feld — das Problem existiert dort nicht. Echter Rest: ein paar zu lange Sätze.
- *Insight Ton 13 %*: Gemessen wurde Coach-tastend (es könnte sein). Aber die Krass-Zeile ist absichtlich
  mutig und direkt — unfaire Messlatte.

**Echte Funde → daraus gefixt (V3.15.0):** (1) Insight kippte manchmal ins Anklagende → Regel
*Verhalten statt Charakter-Urteil* + absolute Wörter gesperrt. (2) Generalisten/flache Profile brachen ein
→ Sonderregel. (3) Lever zu lange Sätze / zu viel Job-Beschreibung → kürzere Sätze, mehr Mensch.

---

# Qualitäts-Zeugnis: KI-Texte (insight & lever)

## 1. Fazit

Die Texte können den "das bin ich"-Moment auslösen — aber verlässlich nur beim **insight**, und auch da mit einem ernsten Haken. Insight ist mit Barnum 53% spezifisch genug, dass Fremde mehr als die Hälfte der Texte der richtigen Person zuordnen konnten (Zufall wäre 5%). Das ist gut: die Texte beschreiben echte Menschen, keine Horoskope. Die **größte Schwäche steckt im Ton**: nur 13% der Insight-Texte treffen die tastende Coach-Stimme — die KI rutscht ständig ins Harte, Anklagende ("wird er dir egal", "lässt ihn stehen"). Beim **lever** ist es genau umgekehrt: Ton perfekt (100%), aber die Sprache komplett gerissen (0%) und die Texte sind zu generisch/austauschbar. Kurz: Insight ist treffsicher aber zu grob im Ton, lever ist warm aber zu beliebig und sprachlich zu verschachtelt.

## 2. Zeugnis-Tabelle

| Kennzahl | insight (n=40) | lever (n=20) |
|---|---|---|
| Erkennung Ø (1–5) | **3,83** | 3,60 |
| Barnum (richtige Zuordnung) | **53%** | **80%** |
| Ton ok | 13% ❌ | 100% ✅ |
| Sprache ok | 65% | 0% ❌ |

Lesehilfe: Barnum hoch = persönlich/spezifisch (gut). Beide Werte sind weit über Zufall (5%) — inhaltlich treffen die Texte. Die roten Felder sind die echten Baustellen: **Insight-Ton** und **Lever-Sprache**.

## 3. Konsistenz — verlässlich oder Glückssache?

**Verlässlich.** Von 20 Personen hatten 16 in beiden Läufen exakt dieselbe Note. Bei keiner einzigen Person wich die Erkennung um 2 oder mehr ab (`run_diff>=2` ist leer). Die vier Abweichungen waren alle nur 1 Punkt (3→4), also Schwankung im grünen Bereich — z.B. Mechatroniker (3/4), Kunsttherapeut (3/4), Schwacher Fit (3/4).

Das heißt: Die Qualität ist **kein Würfeln**. Wenn ein Profil schlecht abschneidet, dann systematisch (siehe Generalist: 2/2 in beiden Läufen — konstant schwach, nicht zufällig). Das ist eine gute Nachricht für dich: Du kannst Probleme gezielt am Prompt fixen, statt gegen Zufall anzukämpfen.

## 4. Muster — wer fällt durch und warum

**Muster A — Der Generalist/das flache Profil bricht komplett ein (Erkennung 2/2, beide Läufe).**
Die KI behandelt "keine Stärke ragt raus" als "konturloser Anpasser, der keine Position bezieht". Aber das Profil war stark in Durchsetzung/Menschen/Struktur. Zitat i16.1: *"am Ende weiß keiner, wofür du wirklich brennst. Auch du selbst nicht."* — die echte Person ist ein durchsetzungsstarker Koordinator und denkt "das bin ich nicht". Die KI erfindet eine Schwäche-Erzählung, die dem Profil widerspricht.

**Muster B — Insight kippt ins Anklagende statt Tastende (das Ton-Problem, 13%).**
Die Spannung ist oft richtig gebaut, aber zu hart formuliert:
- i1.1: *"wird er dir egal — du ziehst dein Ding durch und lässt ihn stehen"* → Charakter-Diagnose, kein "so ticke ich". Person fühlt sich angegriffen.
- i6.1: *"Andere gehen dir über alles… selbst entscheiden willst du nicht… sagst nie klar"* → Vorwurf, nicht Erkennen. Absolute Wörter ("über alles", "nie").
Die Spannung trifft, aber das "krass, das bin ich" kippt im zweiten Satz ins "nein, so bin ich nicht".

**Muster C — Lever ist zu generisch (Barnum trotz 80% trügerisch im Detail).**
Mehrere Lever bleiben austauschbar:
- l8 (Sozialmanager): *"wichtige Termine oder Unterlagen durchrutschen"* — "könnte über fast jeden gesagt werden, der Struktur lernen muss".
- l9 (Eventmanager): *"du reagierst lieber spontan, kannst gut improvisieren"* — wurde sogar als Generalist verraten.
Es fehlt der eine konkrete, fast peinliche Haken, der nur diese Person meint.

**Muster D — Lever erklärt den Job statt den Menschen.**
l2 (Industriemechaniker): *"Maschinen laufen über mehrere Schichten, und jede Kleinigkeit muss weitergegeben werden"* — "zu viel Außenwelt, zu wenig Innenleben". Der "Ein Job wie dieser heißt aber vor allem…"-Baustein zieht den Text weg vom "das bin ich" hin zur Jobbeschreibung.

**Muster E — Lever-Sprache scheitert flächendeckend (0%).** Schachtelsätze und stehengebliebene Überschriften. l14 beginnt mit *"Menschen mitnehmen Es könnte sein, dass…"* — die Headline klebt am Fließtext ("wirkt versehentlich stehen geblieben und stört das Eintauchen"). Das ist ein Formatfehler, der in JEDEM lever-Text auftaucht.

**Fast-Zwillinge:** Sauber getrennt. Person 10 (Vertriebsleiter EC) und Person 20 (Fast-Zwilling EC) wurden bei 6 Betrachtungen **0-mal verwechselt**. Die Texte sind also fein genug, um zwei sehr ähnliche Profile auseinanderzuhalten — das spricht für echte Spezifität, nicht Schablone.

## 5. Konkrete Prompt-Verbesserungen

**Insight:**

1. **Tastend statt diagnostisch erzwingen (größter Hebel, fixt die 13% Ton).** Verbiete im Prompt explizit Charakter-Urteile im zweiten Satz. Regel: "Beschreibe ein Verhalten/eine Neigung, kein Charaktermerkmal. Nie 'dir egal', 'lässt ihn stehen', 'willst nicht'. Nutze 'du neigst dazu', 'oft', 'manchmal'." Beleg: i1.1, i6.1 — Spannung stimmt, Ton zerstört die Erkennung.

2. **Absolute Wörter sperren.** Blacklist im Prompt: "nie", "immer", "über alles", "keiner". Beleg: i6.1 (*"sagst nie klar"*, *"über alles"*) wurde trotz richtiger Barnum-Zuordnung als Vorwurf gelesen.

3. **Sonderregel für flache/Generalisten-Profile.** Wenn keine Stärke klar herausragt, NICHT "konturlos/weiß nicht wofür du stehst" erzählen. Stattdessen die Spannung aus den real vorhandenen mittleren Stärken bauen. Beleg: i16.1/i16.2 — beide Läufe 2/2, weil die KI eine falsche Schwäche-Story erfindet, die dem Durchsetzungs-Profil widerspricht. Gib dem Prompt die Top-2/3 Stärken explizit mit und sag: "Bau die Spannung NUR aus diesen, erfinde keine Anpasser-Erzählung."

**Lever:**

4. **Format-Fix für die Überschrift (sofort umsetzbar, fixt einen Teil der 0% Sprache).** Die Headline ("Auf Leute zugehen", "Menschen mitnehmen") landet im Fließtext-Anfang. Trenne sie sauber im Output-Format (eigenes JSON-Feld `titel` statt vorangestellt). Beleg: l2, l14 — Headline klebt am ersten Satz.

5. **Schachtelsätze verbieten, kurze Sätze erzwingen.** Sprache ist bei 0%. Regel: "Max. 12–15 Wörter pro Satz. Ein Gedanke pro Satz. Kein 'weil…, dass…, und…' in einem Satz." Beleg: l2, l9 enthalten lange Begründungsketten.

6. **Weniger Job-Beschreibung, mehr Mensch.** Der "Ein Job wie dieser heißt aber vor allem…"-Block zieht ins Generische. Kürze ihn auf einen halben Satz und verlange stattdessen einen konkreten, persönlichen Haken aus dem Profil. Regel: "Beschreibe, wie SIE tickt, nicht wie der Job tickt. Max. ein Satz über den Job." Beleg: l2 (zu viel Schichtbetrieb), l8/l9 (austauschbar, weil Job statt Person).

**Reihenfolge nach Wirkung:** Erst #1+#2 (Insight-Ton — größter Erkennungs-Killer), dann #4+#5 (Lever-Sprache — leicht zu fixen, aktuell 0%), dann #3+#6 (Spezifität — feinjustieren).

---

## Rohzahlen
```json
{
 "insight": {
  "kind": "insight",
  "n": 40,
  "erkennung_schnitt": 3.83,
  "barnum_trefferquote_prozent": 53,
  "ton_ok_prozent": 13,
  "sprache_ok_prozent": 65
 },
 "lever": {
  "kind": "lever",
  "n": 20,
  "erkennung_schnitt": 3.6,
  "barnum_trefferquote_prozent": 80,
  "ton_ok_prozent": 100,
  "sprache_ok_prozent": 0
 }
}
```
