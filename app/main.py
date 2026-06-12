"""Work Mentor 2.0 — FastAPI Backend + Frontend"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os
import json
import re
import math
import urllib.request
import urllib.parse
import base64

from app.holland import ITEMS, assess, get_shuffled_items, _dim_label
from app.traits import DIMENSIONS, TRAIT_ITEMS, score_traits, get_trait_items, check_trait_quality
import anthropic

app = FastAPI(title="Work Mentor 3.0")

# Anthropic-Client robust initialisieren (kein Crash bei fehlendem Key)
try:
    claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY") or None)
except Exception:
    claude = None

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
    scores: dict
    code: str
    trait_scores: dict = {}  # {dim: Mittel 1-5} aus der Trait-Stufe (Stufe 2)
    variante: str = ""       # gewählte Job-Variante aus dem Berater-Schritt (optional)
    grounded: bool = True    # True = Anforderungen aus echten Stellenanzeigen erden
    typ_name: str = ""       # Interessen-Typ aus Test 1 (für die Interesse↔Können-Brücke)
    superkraft: str = ""     # Superkraft aus Test 1 (was die Person REIZT)
    insight: str = ""        # Krass-Zeile aus Test 2 — roter Faden, den der lever auflösen soll

class JobsRequest(BaseModel):
    scores: dict          # normalisiert 0-100 pro Dimension (R,I,A,S,E,C)
    code: str
    custom_job: str = ""  # gesetzt = nur diesen einen Job bewerten

class InsightRequest(BaseModel):
    answers: list         # [{"item_id": int, "value": 1..5}]
    code: str = ""        # RIASEC-Code (optional, zum Einfärben)
    type_name: str = ""   # Tier-/Typname (optional)

class JobContextRequest(BaseModel):
    job_name: str
    scores: dict = {}     # RIASEC-Scores (optional, für die "unsicher"-Empfehlung)
    grounded: bool = True # True = mit echten BA-Marktdaten erden; False = reines KI-Wissen

class JobCheckRequest(BaseModel):
    job_name: str         # Freitext-Eingabe des Users — wird auf Plausibilität geprüft
    scores: dict = {}     # RIASEC-Scores (optional) — für die Interessen-Passung


# Kanonische Tier-Sprüche — Ton-Anker im Prompt UND Fallback, falls der
# Claude-Call scheitert. Keyed nach Haupt-Dimension (+ Generalist "G").
TIER_ANCHORS = {
    "R": {"superkraft": "Aus dem Nichts etwas Funktionierendes bauen — bevor andere überhaupt verstanden haben, wie das Problem aussieht.",
          "kryptonit": "Endlose Meetings, in denen geredet wird statt gemacht."},
    "I": {"superkraft": "Muster erkennen, wo andere nur Chaos sehen — und das so erklären, dass es plötzlich offensichtlich wirkt.",
          "kryptonit": "Jemand sagt 'Glaub mir einfach' ohne Daten zu zeigen."},
    "A": {"superkraft": "Bestehende Ideen so neu kombinieren, dass alle denken: Klar, warum hat das nicht schon jemand gemacht?",
          "kryptonit": "Eine Vorlage in PowerPoint, die du nur noch ausfüllen sollst."},
    "S": {"superkraft": "Eine Gruppe so führen, dass sich jeder Einzelne gesehen fühlt — und am Ende mehr leistet als gedacht.",
          "kryptonit": "Allein in einem Co-Working zwischen 30 Headphones."},
    "E": {"superkraft": "Leute begeistern, bevor du selbst weißt, wovon du redest.",
          "kryptonit": "Jemand sagt: Das haben wir schon immer so gemacht."},
    "C": {"superkraft": "Aus Datenchaos eine saubere Struktur machen, die so logisch wirkt, als wäre sie schon immer da gewesen.",
          "kryptonit": "Lass uns das einfach spontan entscheiden."},
    "G": {"superkraft": "Zwischen Welten übersetzen, die sonst nicht miteinander reden.",
          "kryptonit": "Auf EINE Schiene festgelegt werden."},
}


@app.get("/api/items")
async def get_items():
    """Liefere Assessment-Items in zufälliger Reihenfolge."""
    return {"items": get_shuffled_items()}


@app.post("/api/assess")
async def post_assess(req: AssessmentRequest):
    """Berechne das Ergebnis + personalisierte KI-Texte (Beschreibung,
    Job-Teaser, Superkraft, Kryptonit) — gegründet auf dem vollen Profil."""
    answers = [{"item_id": a.item_id, "value": a.value} for a in req.answers]
    result = assess(answers)

    code = result["code"]
    is_gen = result.get("is_generalist", False)
    anchor_key = "G" if is_gen else code[0]
    anchor = TIER_ANCHORS.get(anchor_key, TIER_ANCHORS["E"])

    # Defaults — werden vom Claude-Call ueberschrieben (das Frontend hat einen eigenen Tier-Fallback)
    result["ai_superkraft"] = None
    result["ai_kryptonit"] = None

    try:
        norm = result.get("normalized_scores", result["scores"])
        sorted_dims = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        profile = ", ".join([f"{_dim_label(d)}: {v}" for d, v in sorted_dims])

        d1 = _dim_label(code[0])
        d2 = _dim_label(code[1])
        d_low = _dim_label(sorted_dims[-1][0])
        type_name = result.get("type_name", "")
        jobs_list = ", ".join([j["title"] for j in result.get("jobs", [])])

        prompt = f"""Du schreibst das Ergebnis fuer einen Karriere-Test. Antworte NUR mit diesem JSON, kein Text davor oder danach:

{{
  "beschreibung": "<2-3 kurze Saetze>",
  "job_teaser": "<1 Satz>",
  "superkraft": "<1 Satz>",
  "kryptonit": "<1 Satz>"
}}

DATEN DER PERSON:
Karriere-Typ: {type_name} ({d1}-{d2}){" (Generalist)" if is_gen else ""}
Profil (0-100, hoch = stark ausgepraegt): {profile}
Staerkste Richtung: {d1}
Zweitstaerkste: {d2}
Schwaechste Richtung: {d_low}
Passende Jobs: {jobs_list}

ANKER (Ton & Identitaet des Typs — als Vorlage fuer den Stil, NICHT 1:1 abschreiben):
Typische Superkraft: "{anchor['superkraft']}"
Typisches Kryptonit: "{anchor['kryptonit']}"

SO INDIVIDUALISIERST DU:
- superkraft: Nimm die Identitaet von "{d1}" und faerbe sie mit "{d2}" ein. Konkret und ueberraschend.
- kryptonit: Leite es aus der schwaechsten Richtung ("{d_low}") ab — das, was diese Person
  am ehesten nervt oder auslaugt. Lustig aber wahr.
- beschreibung: Was treibt die Person an, was nervt sie. Wie ein Kumpel, der sie gut kennt.
- job_teaser: Neugierig auf die Jobs machen, mit Bezug zum Profil.

STIL von superkraft & kryptonit (WICHTIG):
- Genau wie die Anker oben: eine kurze, knackige Phrase im Praesens.
- KEIN "Du koenntest ...", KEINE Weichmacher (kein "wahrscheinlich/vielleicht/duerfte").
  Es ist eine Archetyp-Zeile, kein Gutachten.
- superkraft = eine Faehigkeit als Infinitiv-Phrase MIT einem konkreten, ueberraschenden Bild oder
  einer pointierten Wendung (genau wie die Anker oben). NIEMALS nur zwei aneinandergereihte
  Allerwelts-Verben — das klingt duenn und beliebig.
✅ superkraft: "Ideen vorantreiben, ohne den Bezug zur Realitaet zu verlieren."
✅ superkraft (E+C): "Eine vage Idee in einen Plan verwandeln, der wirklich läuft — bevor andere noch diskutieren."
❌ superkraft: "Geschäfte abschließen und dabei den Überblick behalten." (zwei Allerwelts-Verben, kein Bild, klingt dünn)
❌ superkraft: "Du koenntest Projekte vorantreiben, ohne dabei den Bezug zur Realitaet zu verlieren." (zu weich, klingt schief)
✅ kryptonit: "Endlose Detailarbeit ohne den großen Zusammenhang."
❌ kryptonit: "Detailarbeit raubt dir vermutlich die Motivation." (Weichmacher, kein Archetyp)

REGELN fuer beschreibung & job_teaser:
- Deutsch, Du-Form, einfache Sprache, Berufsschulniveau, keine Fachbegriffe.
- Vermutend: "koennte", "scheint", "wahrscheinlich" — KEINE absoluten Aussagen.
- KEINE Vorhersagen ueber ungetestete Faehigkeiten. Nichts erfinden, nur was aus dem Profil folgt.
✅ beschreibung: "Du ueberzeugst Leute wahrscheinlich eher durch Begeisterung als durch Druck."
❌ beschreibung: "Du wirst jeden Raum erobern." (zu absolut)

GILT IMMER: Niemals "als wie". Keine Emoji. Keine erfundenen Statistiken (nicht "nur 8% ...").
Verwende AUSSCHLIESSLICH echte Umlaute (ä, ö, ü) und ß — niemals ae/oe/ue/ss als Ersatz."""

        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            result["ai_description"] = data.get("beschreibung")
            result["ai_job_teaser"] = data.get("job_teaser")
            result["ai_superkraft"] = data.get("superkraft")
            result["ai_kryptonit"] = data.get("kryptonit")
        else:
            result["ai_description"] = text
            result["ai_job_teaser"] = None
    except Exception as e:
        result["ai_description"] = None
        result["ai_error"] = str(e)

    return result


# (_fetch_ba_listings entfernt — das langsame Einzel-Anzeigen-Lesen brachte gegenueber
# Claudes Berufswissen kaum mehr, kostete aber ~14s. Stattdessen erden wir leicht ueber
# die schnellen Markt-Facetten in _fetch_ba_market.)


@app.post("/api/fit")
async def post_fit(req: FitRequest):
    """Generiere job-spezifische Fit-Analyse via Claude — Anforderungen aus echten
    Stellenanzeigen geerdet (mit Fallback auf KI-Wissen)."""
    dim_labels = {"R": "Realistisch", "I": "Forschend", "A": "Kreativ",
                  "S": "Sozial", "E": "Unternehmerisch", "C": "Organisierend"}
    scores_str = ", ".join([f"{dim_labels.get(k, k)}: {v}" for k, v in req.scores.items()])

    traits_section = ""
    if req.trait_scores:
        ranked = sorted(req.trait_scores.items(), key=lambda x: x[1], reverse=True)
        lines = [f"- {DIMENSIONS[k]['name']} ({DIMENSIONS[k]['desc']}): {v} von 5" for k, v in ranked if k in DIMENSIONS]
        traits_section = "\n\nPersoenlichkeits-Profil (7 Eigenschaften, je 1-5, hoeher = staerker ausgepraegt):\n" + "\n".join(lines)
        answers_note = "- Nutze das Persoenlichkeits-Profil als Hauptquelle fuer Staerken und Gaps — wie die Person tickt vs. was der Job verlangt"
    else:
        answers_note = "- Leite Staerken und Gaps aus den RIASEC-Scores ab"

    # Schnelle echte Marktdaten (BA, ~0.3s) — leichter Anker + "Echter Markt"-Panel
    markt = {}
    markt_anchor = ""
    if req.grounded:
        m = _fetch_ba_market(req.job_name)
        # Nur verlässliche Marktdaten nutzen. Bei sehr wenigen Treffern hat die
        # BA-Suche meist einen unpassenden Beruf erwischt (z.B. "Startup-Gründer"
        # -> 2 Karosseriebau-Meister-Stellen). Dann KEIN Panel + KEINE Erdung,
        # sonst sickert der Müll in den Report.
        if m.get("count") is not None and m.get("count") >= 15:
            qe = m.get("quereinstieg", {})
            markt = {
                "offene_stellen": m.get("count"),
                "berufsfelder": m.get("berufsfelder", [])[:3],
                "regionen": m.get("regionen", []),
                "quereinstieg_moeglich": qe.get("true", 0) > 0,
                "homeoffice_stellen": m.get("homeoffice", 0),
                "arbeitszeit": m.get("arbeitszeit", {}),
                "quelle": "Bundesagentur für Arbeit",
            }
            anchor = []
            if m.get("berufsfelder"):
                anchor.append("Berufsfelder: " + ", ".join(m["berufsfelder"][:4]))
            if m.get("titel"):
                anchor.append("echte Stellentitel: " + "; ".join(m["titel"][:5]))
            if anchor:
                markt_anchor = ("\n\nMARKT-KONTEXT (echte BA-Daten, nur als leichter Anker fuer die richtige "
                                "Variante — ergaenze KEINE erfundenen Details):\n- " + "\n- ".join(anchor))

    variant_section = ""
    if req.variante:
        variant_section = (f"\n\nWICHTIG — GEWAEHLTE VARIANTE (so und NUR so fuehrt die Person den Job aus): "
                           f"{req.variante}\nDURCHGAENGIG fuer ALLE Texte (fit_headline, requirements, strength, lever): "
                           "Illustriere alles mit den KONKRETEN Alltags-Situationen DIESER Variante. Fuehrt die Person "
                           "z.B. ein Team, kommen ihre Staerken/Anforderungen in FUEHRUNGS-Situationen vor (Team steuern, "
                           "Ziele setzen, Leute coachen, Zahlen pruefen). Sagt die Variante, dass die Person NICHT selbst "
                           "am Kunden ist, dann darf KEINE einzige der 4 Anforderungen eigenen Kundenkontakt verlangen — "
                           "das schließt AUSDRUECKLICH auch 'Kundenbeziehungen pflegen', 'Großkunden/Key Accounts "
                           "betreuen', 'Netzwerken mit Kunden' und 'Kundengespraeche/Akquise/Verkauf' ein. Diese gehoeren "
                           "dann GAR NICHT in die Liste (auch nicht als Hebel). Schliesse variant-fremde Aufgaben komplett "
                           "AUS. Greife NIE auf das Klischee des Jobtitels zurueck, wenn die Variante etwas anderes sagt.")

    interest_section = ""
    if req.typ_name or req.superkraft:
        interest_section = (
            "\n\nINTERESSEN-PROFIL (aus dem ERSTEN Test — was die Person REIZT, NICHT was ihr leichtfaellt):"
            f"\n- Interessen-Typ: {req.typ_name}"
            f"\n- Ihre 'Superkraft' (= ihr Interesse): {req.superkraft}"
            "\nDas Persoenlichkeits-Profil oben zeigt dagegen, was ihr LEICHT faellt. Diese zwei koennen "
            "auseinandergehen — siehe Regel 'INTERESSE vs. KOENNEN'."
        )

    insight_section = ""
    if req.insight and req.insight.strip():
        insight_section = (
            "\n\nROTER FADEN (die Krass-Zeile aus Test 2, die die Person ueber sich gelesen und WIEDERERKANNT hat):"
            f"\n\"{req.insight.strip()}\""
            "\nDer 'lever' MUSS GENAU diese Spannung aufgreifen und einen Ausweg zeigen — KEIN neues Thema. "
            "Greif ein Wort/Bild der Zeile auf (nicht 1:1 zitieren), dann zeig den Hebel. Die Zeile ist hart "
            "formuliert; im lever machst du daraus eine TENDENZ (Weichmacher vorne, der scharfe Inhalt bleibt)."
        )

    prompt = f"""Du bist ein erfahrener Karriere-Coach. Stell dir vor, du hast diese eine Person ein
Gespraech lang erlebt — ihre Art, ihr Tempo, wo sie aufblueht und wo sie sich selbst im Weg steht.
Jetzt schreibst du ihr eine persoenliche Rueckmeldung zum Job "{req.job_name}". Kein Gutachten —
eine Rueckmeldung, bei der sie denkt: "krass, der hat mich gesehen, und jetzt weiss ich, woran ich arbeiten muss."

Was du ueber die Person weißt:
RIASEC-Profil: {req.code}
Dimension-Scores (Rohwerte -8 bis +8): {scores_str}{traits_section}{interest_section}{insight_section}{variant_section}{markt_anchor}

Was du NICHT weißt — und worueber du deshalb KEINE Annahme triffst:
- Ob die Person aktuell in diesem Job, einem anderen Job oder gerade gar nicht arbeitet.
- Ob sie ein Team hat, wie viel Berufserfahrung sie hat, ob sie Schuelerin, Studentin oder Wechslerin ist.
Du kennst NUR: ihre Veranlagung (oben) und den Job, den sie gerade pruefen will. Beziehe NICHTS auf eine
angenommene aktuelle Situation ("in deiner naechsten Teamsitzung", "in deinem jetzigen Job"). Den ZIELJOB
darfst du konditional nennen ("ein Job wie dieser heißt vor allem...").

Antworte in GENAU diesem JSON, kein Fliesstext davor oder danach:

{{
  "fit_score": <Zahl 50-88, realistisch auf Basis aller vorliegenden Daten>,
  "fit_headline": "<1 ermutigender, persoenlicher Satz, Du-Form. Er darf NICHT behaupten, was eine Anforderung oder die bruecke unten verneint — leite ihn aus den tatsaechlichen Badge-Ergebnissen ab.>",
  "bruecke": "<1-2 KURZE Saetze ODER leerer String. NUR fuellen, wenn das Interesse (Typ/Superkraft aus Test 1) auf eine NIEDRIGE passende Eigenschaft trifft. Dann benenne die Spannung als HEBEL, Du-Form, einfach: 'X reizt dich — deshalb dieser Job. Leicht faellt dir X aber noch nicht. Das ist kein Widerspruch, sondern dein Hebel.' Wenn Interesse und Veranlagung zusammenpassen: leerer String.>",
  "requirements": [
    {{"name": "<Kern-Anforderung des Jobs, 2-5 Woerter>", "badge": "passt_gut|solide_basis|dein_hebel", "body": "<1 Satz: deine Auspraegung dazu, ehrlich, Du-Form>"}}
  ],
  "strengths": [
    {{"name": "<staerkste Eigenschaft, 1-2 Woerter>", "body": "<1 Satz, was sie fuer DIESE Variante bringt>"}}
  ],
  "lever": {{
    "name": "<die eine Sache, an der es sich zu arbeiten lohnt — 1-3 einfache Alltagswoerter, KEIN Fachbegriff>",
    "observation": "<2 KURZE Saetze (je max ~15 Woerter) Coach-Stimme: 'Es koennte sein, dass du...' — benenne ein Muster ihrer Veranlagung UND seinen Preis. Tastend, nie belehrend.>",
    "edge": "<2 KURZE Saetze (je max ~15 Woerter), KONKRET und fassbar. Beschreibe, was sich fuer DICH aendert, wenn du hier waechst — ein greifbarer GEWINN, NICHT wie der Job/die Branche funktioniert. VERBOTEN: 'Ein Job wie dieser heisst...', 'Die besten X tun Y', 'Teams/Firmen laufen nur, wenn...' (Job-Lehrbuch statt Person). VERBOTEN das Wort 'Wachstumskante' und abstrakte Coach-Saetze. 'name' und 'edge' nicht redundant. KEINE Imperative, KEINE Vorhersage ueber andere ('X vertraut/respektiert dich mehr'), KEINE absoluten Woerter ('nur', 'immer', 'jeder', 'alle', 'jede'), KEINE erfundenen Zahlen.>"
  }},
  "resource": {{"kind": "book", "title": "...", "author": "...", "price": "<grobe Preisangabe, z.B. 'ca. 20 €'>", "body": "<1 Satz warum genau das>", "cta": "Auf Amazon ansehen"}},
  "schritte": [
    {{"title": "<kurzer Titel>", "body": "<1 konkreter Satz: eine kleine Uebung, die AB HEUTE in jedem Alltag machbar ist — Arbeit, Freunde, Familie, egal. Bezogen auf Veranlagung + Hebel, NIE auf eine angenommene Situation.>"}}
  ],
  "positionierung": "<2 kurze Saetze: EIN neuer, konkreter Tipp fuers Bewerbungsgespraech — wie die Person ihren EINEN Hebel selbst anspricht, bevor andere fragen. NICHT die Staerken wiederholen.>",
  "einstiegswege": [
    {{"name": "<Einstiegsweg in diesen Beruf, kurz>", "detail": "<1 knapper Satz>"}}
  ],
  "fachlich": "<1 kurzer Hinweis auf rein fachliche Voraussetzungen (Ausbildung, Software, Jahre Erfahrung, Fuehrerschein), ohne Bewertung — oder leerer String>"
}}

Regeln:
- INTERESSE vs. KOENNEN (roter Faden — am allerwichtigsten): Test 1 zeigt die INTERESSEN (Typ/Superkraft = was die
  Person REIZT). Das Persoenlichkeits-Profil zeigt, was ihr LEICHT faellt. Diese zwei koennen AUSEINANDERGEHEN —
  z.B. starkes Interesse am Organisieren, aber niedrige Eigenschaft Struktur. Das ist KEIN Widerspruch, und du
  darfst es NIEMALS unkommentiert als Widerspruch stehen lassen (toedlich fuer das Vertrauen!):
  * Geht Interessen-Typ/Superkraft gegen eine niedrige passende Eigenschaft: FUELLE "bruecke" und mach GENAU diese
    Spannung zum Hebel — "Das reizt dich, faellt dir aber noch nicht leicht — genau das ist dein Hebel."
  * fit_headline, requirements und lever duerfen das Interesse NIE einfach abtun ("Struktur ist nicht deine Staerke")
    OHNE es einzuordnen. Reihenfolge immer: Interesse anerkennen -> ehrlich die Veranlagung -> als Hebel rahmen.
  * Passen Interesse und Veranlagung zusammen: "bruecke" leer lassen.
- KOHAERENZ (am wichtigsten!): Der ganze Report erzaehlt EINE Geschichte — ohne Wiederholung, ohne Widerspruch.
  * Es gibt GENAU EINEN "dein_hebel" unter den requirements. Dieser eine Hebel IST "die eine Sache" (lever) —
    gleiches Thema, gleicher Punkt. NIEMALS zwei Baustellen.
  * Alle 3 schritte gehoeren zu DIESEM einen Hebel. Kein Schritt zu einem anderen Thema.
  * Jede Sektion bringt etwas NEUES. Wiederhole NICHT dieselbe Eigenschaft in mehreren Sektionen. Wenn
    "ruhig/gelassen" eine Staerke ist, steht das EINMAL (in strengths) — nicht nochmal in headline oder positionierung.
  * KEIN Widerspruch: Sagt der lever "mehr auf Leute zugehen", darf positionierung NICHT sagen "sag, dass du das meidest".
  * Schreib durchgaengig ueber die Person (Du-Form). KEIN "ich" ("das verstehe ich gut" ist verboten).
- EHRLICHKEIT beim Fit: Bestimme den fit_score ehrlich aus den Badges. Danach richtet sich der ganze Ton.
  * Hoher Fit (>=75): Der Job passt. Die eine Sache ist eine echte Chance, auf die man sich freuen kann.
  * Mittlerer/niedriger Fit (<70): Das ist ein STRECK-JOB. Er fordert die Person an genau den Stellen, wo sie am
    wenigsten andockt. Sag das EHRLICH und warm — tu NICHT so, als waere es nur eine kleine Baustelle. Die
    fit_headline benennt den Stretch offen (z.B. "Dieser Job wuerde dich an einer Stelle fordern, die dir nicht
    liegt — ob sich das lohnt, entscheidest du"). Kein falscher Optimismus, kein Schoenreden. Ziel: eine ehrliche
    Entscheidungsgrundlage, keine Ermutigung um jeden Preis.
- requirements: GENAU 4 Kern-Anforderungen DIESES Jobs.
  Schreib sie aus deinem fundierten Berufswissen, KORREKT zur gewaehlten Variante und am
  Markt-Kontext orientiert (falls vorhanden) — kein Stereotyp, kein generisches Bla.
  Decke die bekannte, etablierte Form des Jobs ab — aber erfinde NICHTS Konkretes
  (keine ausgedachten Aufgaben, Zahlen, Werkzeuge).
  Waehle nur Anforderungen, die mit PERSOENLICHKEIT/Arbeitsweise zu tun haben (nur die koennen wir
  gegen das Profil spiegeln). Reine Fach-/Formal-Voraussetzungen (Software, Jahre Erfahrung,
  Fuehrerschein, Abschluss) gehoeren NICHT in die 4 — die nennst du knapp im Feld "fachlich".
  badge: "passt_gut" = klare Staerke | "solide_basis" = okay, ausbaufaehig | "dein_hebel" = hier hakt es am meisten.
  GENAU EIN "dein_hebel" (= die eine Sache). Der Rest passt_gut oder solide_basis, ehrlich verteilt.
  body je Anforderung: 1 kurzer Satz, der deine Auspraegung ehrlich spiegelt. Du-Form. Jeder body ein NEUER
  Aspekt — nicht 4x dieselbe Eigenschaft.
- fit_score spiegelt die Summe der Badges ehrlich (viele passt_gut = hoch, mehrere Hebel = niedriger).
- strengths: GENAU 2 staerkste Eigenschaften (Trait-Ebene). lever: die EINE wichtigste Sache, an der es sich
  zu arbeiten lohnt.
  METHODISCH: Illustriere strengths mit einer KONKRETEN Situation aus dem ECHTEN Alltag DIESER Variante
  (bzw. des Jobs) — niemals mit einem Job-Klischee oder einer Taetigkeit, die die Person in ihrer Variante
  gar nicht macht. Lieber allgemein-treffend als falsch-konkret.
  Der "krass das bin ich"-Effekt im lever kommt daher, dass du den PREIS einer Veranlagung benennst —
  NICHT aus Schmeichelei und NICHT aus einem erfundenen Requisit. Werde praezise im MUSTER und im GEFUEHL,
  nicht in ausgedachten Szenen.
  LEVER-SPRACHE (die haeufigsten Fehler, unbedingt vermeiden):
  ❌ "Vertriebsteams laufen nur, wenn jeder Bock hat." (Job-Lehrbuch + absolut "nur"/"jeder")
  ❌ "Die besten Produktmanager verbringen mehr Zeit mit Nutzern als mit Spreadsheets." (generische Predigt, kein persoenlicher Haken)
  ❌ "Da liegt deine Wachstumskante." (eingebrannte Floskel — das Wort ist GANZ verboten)
  ❌ "Die Schueler respektieren dich mehr, wenn du klare Grenzen ziehst." (WIRKUNGSVERSPRECHEN ueber andere — verboten)
  ❌ "Die Teams vertrauen dir mehr, weil du souveraen wirkst." (Vorhersage, wie andere reagieren — verboten)
  ✅ "Dir faellt vieles leichter, sobald du frueh ansagst, was geht." (ich-bezogen, kein Versprechen ueber andere)
  REGEL: Schreib ueber DICH (was DIR leichter wird), NIE darueber, wie ANDERE reagieren ("die anderen werden...",
  "X respektiert/vertraut dir mehr"). KEINE absoluten Woerter ("alle", "jede", "jeder", "immer", "nur").
- resource: EIN echtes Buch, das genau an diesem Hebel ansetzt.
- schritte: GENAU 3. Jede eine kleine Uebung, die AB HEUTE in JEDEM Alltag machbar ist, egal wo die Person
  gerade steht. KEINE Zeithorizonte, KEINE angenommene Situation, KEIN "in deinem Job/Team". Nur Veranlagung + Hebel.
- positionierung: 2 kurze Saetze, EIN neuer Tipp fuers Gespraech (siehe JSON). Nicht die Staerken wiederholen.
- einstiegswege: GENAU 3 realistische Wege in DIESEN Beruf (z.B. Ausbildung, Quereinstieg, Weiterbildung,
  Studium — je nach Beruf). Etabliertes Berufswissen, erfinde nichts Konkretes.
- {answers_note}
- Coach-Stimme: warm, direkt, tastend wo es um Wachstum geht ("es koennte sein, dass..."), nie belehrend,
  nie absolut. Deutsch, Du-Form, NIEMALS als-wie.
- SPRACHE — verstaendlich UND wuchtig (das Wichtigste!): Schreib, wie du es einem 16-jaehrigen Azubi
  sagen wuerdest. Jedes Wort muss er SOFORT verstehen. Die Wucht kommt aus der WAHRHEIT, nicht aus großen
  Woertern. VERBOTEN sind abstrakte Hauptwoerter und Coach-Sprech wie "Stressstabilitaet", "Anspannung
  regulieren", "den Automatismus unterbrechen", "in einen Modus wechseln", "Selbstregulation", "Resilienz".
  Stattdessen: einfache Verben, konkrete Bilder, kurze Saetze, EIN Gedanke pro Satz.
  ✅ "Wenn's brennt, machst du einfach schneller — statt kurz Luft zu holen."
  ❌ "In Phasen hoher Belastung wechselst du in einen Modus erhoehter Handlungsgeschwindigkeit."
  ✅ "Bleib ruhig, wenn's stressig wird — dann ziehen die Leute mit. Das kann man üben."
  ❌ "Wer die eigene Anspannung bewusst reguliert, führt in Krisensituationen souveräner."
- SATZBAU — der haeufigste Fehler, unbedingt vermeiden: KEINE Schachtelsaetze. Kurze Hauptsaetze, EIN
  Gedanke pro Satz, hoechstens EIN Komma pro Satz. Keine eingeschobenen Nebensaetze ("du, wenn ..., eher ...").
  Keine Ketten aus "bis ... und ... wenn ...". Lieber drei kurze Saetze als einen langen. Lies laut — wo du
  Luft holst, mach einen Punkt.
  ✅ "Du machst Tempo, bis dir die Luft wegbleibt. Dass du zu weit gehst, merkst du erst hinterher."
  ❌ "Statt still zu stehen, machst du Tempo, bis dir die Luft wegbleibt, und merkst erst, dass du am Limit bist, wenn du schon drüber bist."
  ✅ "Wenn der Druck steigt, schaltest du einen Gang hoeher. Es koennte sein, dass du dir damit selbst mehr Stress machst."
  ❌ "Es koennte sein, dass du, wenn der Druck steigt und schnelle Ergebnisse gefragt sind, einen Gang hoeher schaltest."
- Verwende AUSSCHLIESSLICH echte Umlaute (ä, ö, ü) und ß — niemals ae/oe/ue/ss als Ersatz.

Beispiel fuer die Coach-Stimme im "lever"-Block (NUR der Ton, nicht der Inhalt):
- observation: "Es koennte sein, dass du, wenn's schnell gehen soll, Entscheidungen lieber allein triffst,
  als sie lange auszudiskutieren — weil Diskutieren dauert und du das Ergebnis eh schon vor Augen hast.
  Kurzfristig bist du damit schneller."
- edge: "Wenn du Leute frueh fragst, ziehen sie staerker mit. Du verlierst nichts dabei — du gewinnst
  Rueckhalt, den du jetzt manchmal liegen laesst."
"""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1850,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            # Rückwärtskompat: altes Single-"strength" aus strengths[0] ableiten
            if isinstance(result.get("strengths"), list) and result["strengths"] and "strength" not in result:
                result["strength"] = result["strengths"][0]
            if markt:
                result["markt"] = markt
            return result
        return {"error": "parse_error", "raw": text[:200]}
    except Exception as e:
        return {"error": str(e)}


# RIASEC-Congruenz: deterministischer Match-Score aus Profil-Ähnlichkeit.
# Cosinus zwischen User-Profil und dem vom Job geforderten Profil, gemappt auf
# 60–96 % (Produkt-Philosophie: keine 0/100 %, Minimum 60). Gleicher User +
# gleicher Job ergibt IMMER denselben Wert — das ist der Glaubwürdigkeits-Kern.
def _match_score(user_scores: dict, job_riasec: dict) -> int:
    dims = ["R", "I", "A", "S", "E", "C"]
    u = [max(0.0, float(user_scores.get(d, 0) or 0)) for d in dims]
    j = [max(0.0, float(job_riasec.get(d, 0) or 0)) for d in dims]
    nu = math.sqrt(sum(a * a for a in u))
    nj = math.sqrt(sum(b * b for b in j))
    if nu == 0 or nj == 0:
        return 60
    cos = sum(a * b for a, b in zip(u, j)) / (nu * nj)  # RIASEC-Vektoren: ~0.70 .. 1.0
    score = 60 + (cos - 0.70) / (1.0 - 0.70) * 36         # 0.70->60, 1.0->96
    return int(max(60, min(96, round(score))))


@app.post("/api/jobs")
async def post_jobs(req: JobsRequest):
    """Generiere profilpassende Archetyp-Jobs (Claude) und berechne den
    Match-Score deterministisch aus der RIASEC-Congruenz."""
    dim_labels = {"R": "Realistisch", "I": "Forschend", "A": "Kreativ",
                  "S": "Sozial", "E": "Unternehmerisch", "C": "Organisierend"}
    profile = ", ".join([f"{dim_labels.get(k, k)}: {v}" for k, v in req.scores.items()])

    if req.custom_job:
        task = f'''Bewerte EINEN konkreten Beruf: "{req.custom_job}".
Gib genau ein Job-Objekt zurueck. Sei ehrlich — wenn der Job schlecht zum Profil passt,
schaetze sein RIASEC-Profil trotzdem realistisch (der Score wird separat berechnet).'''
        shape = '{ "jobs": [ {"title": "...", "riasec": {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}, "salary": "...", "desc": "..."} ] }'
        n_note = "- Genau 1 Job (der genannte). Titel ggf. sauber ausformuliert."
    else:
        task = "Schlage 5 konkrete Berufe (Archetypen, keine offenen Stellen) vor."
        shape = '{ "jobs": [ {"title": "...", "riasec": {"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}, "salary": "...", "desc": "..."}, ... ] }'
        n_note = """- Genau 5 Jobs, nach Passung absteigend:
  * 3-4 klare Treffer + 1-2 weniger offensichtliche, inspirierende Berufe (Range, nicht nur
    das Naheliegende). Vermeide Berufe, deren Profil dem User komplett entgegengesetzt ist.
  * Schaetze die riasec jedes Jobs ehrlich; der Score wird daraus berechnet."""

    prompt = f"""{task}

User-RIASEC-Profil (0-100, hoch = stark ausgepraegt): {profile}
Top-2: {req.code}

Antworte NUR mit diesem JSON, kein Text davor oder danach:
{shape}

Regeln:
- riasec = welches Profil DER JOB verlangt (NICHT das des Users). Schaetze realistisch
  aus deinem O*NET-/Berufskunde-Wissen, 0-100 pro Dimension.
- salary: realistische deutsche Brutto-Jahresspanne, grob (z.B. "45.000 - 72.000").
  Keine erfundene Praezision, kein Euro-Zeichen.
- desc: 1 kurzer Satz, Du-Form, was man da konkret tut. Kein HR-Jargon.
- Deutsche Berufsbezeichnungen. Keine erfundenen Statistiken.
{n_note}"""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if not m:
            return {"error": "parse_error", "raw": text[:200]}
        data = json.loads(m.group())
        jobs = []
        for j in data.get("jobs", []):
            score = _match_score(req.scores, j.get("riasec", {}))
            jobs.append({
                "title": j.get("title", ""),
                "match": score,
                "salary": j.get("salary", ""),
                "desc": j.get("desc", ""),
            })
        jobs.sort(key=lambda x: x["match"], reverse=True)
        return {"jobs": jobs}
    except Exception as e:
        return {"error": str(e)}


def _fetch_ba_market(job_name: str) -> dict:
    """Echte Marktdaten der Bundesagentur fuer Arbeit (Jobboerse + BERUFENET).
    Schnell (~0.3s/Call), kostenlos, keine Anmeldung. Bei Fehler bleibt das Feld
    leer -> der Berater faellt sauber auf reines KI-Wissen zurueck."""
    out = {"count": None, "berufsfelder": [], "arbeitszeit": {}, "titel": [], "amtliche_varianten": [],
           "quereinstieg": {}, "regionen": [], "homeoffice": 0}
    q = urllib.parse.quote(job_name)
    try:
        req = urllib.request.Request(
            f"https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?was={q}&size=20",
            headers={"X-API-Key": "jobboerse-jobsuche"})
        with urllib.request.urlopen(req, timeout=4) as r:
            d = json.loads(r.read().decode())
        out["count"] = d.get("maxErgebnisse")
        f = d.get("facetten", {})
        bf = f.get("berufsfeld", {}).get("counts", {})
        out["berufsfelder"] = [k for k, _ in sorted(bf.items(), key=lambda x: -x[1])[:6]]
        az = f.get("arbeitszeit", {}).get("counts", {})
        labels = {"vz": "Vollzeit", "tz": "Teilzeit", "mj": "Minijob", "ho": "Homeoffice", "snw": "Schicht/Nacht/Wochenende"}
        out["arbeitszeit"] = {labels.get(k, k): v for k, v in az.items()}
        out["titel"] = list(dict.fromkeys(
            s.get("stellenangebotsTitel", "") for s in d.get("ergebnisliste", []) if s.get("stellenangebotsTitel")))[:8]
        qe = f.get("quereinstieg", {}).get("counts", {})
        out["quereinstieg"] = {"true": qe.get("true", 0), "false": qe.get("false", 0)}
        ao = f.get("arbeitsort", {}).get("counts", {})
        out["regionen"] = [k for k, _ in sorted(ao.items(), key=lambda x: -x[1])[:3]]
        out["homeoffice"] = f.get("homeoffice", {}).get("counts", {}).get("nv_true", 0)
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            f"https://rest.arbeitsagentur.de/infosysbub/bnet/pc/v1/berufe?suchwoerter={q}&page=0&size=8",
            headers={"X-API-Key": "infosysbub-berufenet"})
        with urllib.request.urlopen(req, timeout=4) as r:
            b = json.loads(r.read().decode())
        out["amtliche_varianten"] = [x.get("kurzBezeichnungNeutral") for x in
            b.get("_embedded", {}).get("berufSucheList", [])[:8] if x.get("kurzBezeichnungNeutral")]
    except Exception:
        pass
    return out


@app.post("/api/job-context")
async def post_job_context(req: JobContextRequest):
    """Karriereberater-Schritt: erkennt den Job und liefert die 2-3 Achsen, die
    ihn am staerksten unterscheiden — in Alltagssprache, als Chip-Fragen. Damit
    schaerfen wir gemeinsam mit dem User, welche Variante des Jobs gemeint ist,
    bevor der Fit berechnet wird."""
    market = {}
    real_block = ""
    if req.grounded:
        market = _fetch_ba_market(req.job_name)
        parts = []
        if market.get("amtliche_varianten"):
            parts.append("Amtliche Berufs-Varianten (BERUFENET): " + "; ".join(market["amtliche_varianten"]))
        if market.get("berufsfelder"):
            parts.append("Reale Berufsfelder, in denen dieser Job ausgeschrieben ist: " + "; ".join(market["berufsfelder"]))
        if market.get("titel"):
            parts.append("Echte aktuelle Stellentitel: " + "; ".join(market["titel"]))
        if market.get("arbeitszeit"):
            parts.append("Arbeitszeit-Verteilung der echten Stellen: " + ", ".join(f"{k}: {v}" for k, v in market["arbeitszeit"].items()))
        if market.get("count"):
            parts.append(f"Aktuell {market['count']} offene Stellen in Deutschland.")
        if parts:
            real_block = ("\n\nECHTE MARKTDATEN (Bundesagentur fuer Arbeit, heute abgefragt) — nutze diese "
                          "als Anker fuer deine Optionen:\n- " + "\n- ".join(parts) +
                          "\n\nWICHTIG zur Vollstaendigkeit: Decke ZUSAETZLICH die bekannten gaengigen Varianten "
                          "des Berufs ab, auch wenn sie hier gerade nicht ausgeschrieben sind — solange es "
                          "etablierte, reale Formen des Berufs sind (nur weil eine Variante heute nicht "
                          "ausgeschrieben ist, gibt es sie trotzdem). Aber erfinde KEINE exotischen Varianten "
                          "und keine konkreten Fakten.")

    scores_block = ""
    if req.scores:
        dl = {"R": "Praktisch", "I": "Forschend", "A": "Kreativ", "S": "Sozial", "E": "Unternehmerisch", "C": "Organisierend"}
        ranked = sorted(req.scores.items(), key=lambda x: x[1], reverse=True)
        sc = ", ".join(f"{dl.get(k, k)}: {v}" for k, v in ranked)
        scores_block = (f"\n\nINTERESSEN-PROFIL der Person (0-100): {sc}\n"
                        "Fuege pro Achse zusaetzlich eine 'empfehlung' hinzu: welche EINE Option am besten "
                        "zu diesem Interessen-Profil passt, mit 1 kurzem Grund in Alltagssprache (Du-Form). "
                        "Das zeigen wir, wenn die Person unsicher ist.")

    prompt = f"""Du bist ein erfahrener, lockerer Karriereberater. Du sprichst mit einer normalen
berufstaetigen Person ohne Studium (Berufsschulniveau).

Die Person interessiert sich fuer den Beruf: "{req.job_name}".{real_block}{scores_block}

Denselben Beruf gibt es in sehr verschiedenen Varianten — der Alltag UND die noetigen Eigenschaften
gehen je nach Variante weit auseinander. Finde die 2-3 Achsen, die DIESEN Beruf am staerksten
unterscheiden, und stell sie als kurze Gespraechsfragen.

Antworte NUR mit diesem JSON, kein Text davor oder danach:
{{
  "erkannt": "<wie du den Beruf verstehst, 1 kurzer lockerer Satz, Du-Form>",
  "achsen": [
    {{
      "frage": "<kurze, lockere Berater-Frage, Du-Form>",
      "optionen": [
        {{"label": "<Antwort in Alltagssprache, 1-5 Woerter>", "hinweis": "<intern, 2-4 Woerter: welche Richtung das zeigt>"}}
      ],
      "empfehlung": {{"label": "<die zum Interessen-Profil passende Option, oder leer wenn keine Interessen vorliegen>", "grund": "<1 kurzer Satz, Du-Form, warum>"}}
    }}
  ]
}}

SPRACHE — das Allerwichtigste:
- Deutsch, Du-Form, Berufsschulniveau. Kurze, klare Saetze.
- NULL Fachbegriffe, NULL englische Woerter. Faellt dir eins ein, uebersetze es in Alltagssprache.
  ❌ verboten: "Stakeholder", "B2B", "Corporate", "Reporting", "Pipeline", "Lead", "skalieren",
     "Akquise", "Agentur", "Kennzahlen", "agil"
  ✅ stattdessen: "die vielen Leute, mit denen du dich absprichst", "große Firma",
     "kleine Firma oder selbststaendig", "Zahlen im Blick behalten", "neue Kunden ansprechen"
- Keine Emoji.
- Verwende AUSSCHLIESSLICH echte Umlaute (ä, ö, ü) und ß — niemals ae/oe/ue/ss als Ersatz.

INHALT:
- 2-3 Achsen, die WIRKLICH unterscheiden — wo Alltag und noetige Eigenschaften am meisten kippen.
  Frag NICHT "magst du den Job?".
- METHODISCH: Formuliere die Fragen ueber das UMFELD und die ROLLE (Branche, Setting, fuehren vs.
  selbst machen) — NICHT darueber, was die Person PERSOENLICH an der Front tut. Bei einer Fuehrungs-
  Variante verkauft/schraubt/pflegt die Person evtl. gar nicht selbst. Also "In welcher Branche soll
  dein Team arbeiten?" statt "Was wuerdest DU verkaufen?". Die Frage muss zu JEDER Rollen-Variante passen.
- Gute Achsen sind oft: Machst du es eher selbst (am Menschen, am Werk) oder leitest du andere an?
  Allein oder viel mit Leuten? Grosse Firma oder klein/selbststaendig? In welchem Bereich?
- Pro Achse 2-3 ECHTE Optionen (die Auswahl "Bin mir unsicher" fuegen wir selbst hinzu — gib sie NICHT).
- Ist der Beruf sehr vage (z.B. "irgendwas mit Medien"), mach die erste Achse zur Eingrenzung.

✅ gute Frage: "Wenn du an Projektmanager denkst — willst du eher selbst mittendrin sein und
   Aufgaben verteilen, oder lieber im Hintergrund alles in Ruhe planen?"
❌ schlechte Frage: "Bevorzugst du agiles oder klassisches Stakeholder-Management?" (Fachjargon)"""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            result = json.loads(m.group())
            return result
        return {"error": "parse_error", "raw": text[:200]}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/job-check")
async def post_job_check(req: JobCheckRequest):
    """Input-Guard fuer die Freitext-Job-Eingabe. Ordnet ein:
    ok | traum (echt, aber extrem selten) | kein_beruf (Quatsch) | heikel (Erwachsenenbereich).
    Bei Fehler -> 'ok' (fail open, niemand wird faelschlich blockiert)."""
    market = _fetch_ba_market(req.job_name)
    ba_hint = ""
    if market.get("count") is not None:
        treffer = market.get("count") or 0
        amt = len(market.get("amtliche_varianten") or [])
        ba_hint = (f"\n(Marktdaten zur Eingabe: {treffer} offene Stellen, {amt} amtliche Berufstreffer. "
                   "0 Stellen UND 0 Berufstreffer ist ein starkes Signal fuer 'kein echter Beruf'.)")

    prompt = f"""Klassifiziere diese Eingabe als moeglichen Zieljob fuer einen Karriere-Test: "{req.job_name}".{ba_hint}

Antworte NUR mit diesem JSON, kein Text davor oder danach:
{{"status": "ok|traum|kein_beruf|heikel", "name": "<sauber formulierter Jobname>", "hinweis": "<kurze freundliche Nachricht, Du-Form — oder leer bei ok>", "riasec": {{"R":0,"I":0,"A":0,"S":0,"E":0,"C":0}}}}

- riasec: schaetze das von DIESEM Beruf geforderte Interessen-Profil (RIASEC, 0-100 je Dimension) aus deinem Berufswissen. Bei kein_beruf/heikel egal (0).
- ok: ein normaler, realistisch erreichbarer Beruf. hinweis: leer.
- traum: ein ECHTER, aber extrem seltener/schwer erreichbarer Beruf (z.B. Astronaut, Popstar, Profifussballer,
  Bundeskanzler) — den schaffen nur ganz wenige Menschen. hinweis: WARM und anerkennend, KEIN Traumkiller,
  KEINE harten Realitaets-Saetze. Wuerdige den Traum und frag SANFT, ob wirklich damit weitergetestet werden soll.
- kein_beruf: kein echter Beruf, Quatsch, Tippmuell oder Unmoegliches ("asdfgh", "Chef von allem"). hinweis:
  freundlich, bitte um einen echten Job.
- heikel: Erwachsenen-/Sexbereich oder Illegales. hinweis: hoeflich ablehnen — "Dafuer ist Work Mentor nicht gedacht."

Sprache: Deutsch, Du-Form, Berufsschulniveau, kurze Saetze. Keine Emoji. Niemals "als wie".
Verwende AUSSCHLIESSLICH echte Umlaute (ä, ö, ü) und ß — niemals ae/oe/ue/ss als Ersatz.
Beispiel traum-hinweis: "Astronaut — was fuer ein Traum. Das schaffen nur eine Handvoll Menschen weltweit. Wollen wir trotzdem schauen, ob du als Typ dahin passt?\""""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            d = json.loads(m.group())
            if d.get("status") not in ("ok", "traum", "kein_beruf", "heikel"):
                d["status"] = "ok"
            # Ground-Truth-Schutz: Wenn der Job am echten Arbeitsmarkt EXISTIERT
            # (offene Stellen ODER amtlicher BERUFENET-Eintrag), darf er NIE als
            # "kein_beruf" durchfallen — egal was das Modell meint. So kann kein
            # echter Beruf faelschlich abgewiesen werden. (Heikel bleibt heikel.)
            real_job = (market.get("count") or 0) > 0 or len(market.get("amtliche_varianten") or []) > 0
            if real_job and d.get("status") == "kein_beruf":
                d["status"] = "ok"
                d["hinweis"] = ""
            # Interessen-Passung: Match aus User-Scores vs. geschaetztem Job-RIASEC
            ri = d.get("riasec") or {}
            if req.scores and isinstance(ri, dict) and any(ri.values()):
                d["match"] = _match_score(req.scores, ri)
            d.pop("riasec", None)
            d.setdefault("name", req.job_name)
            return d
    except Exception:
        pass
    return {"status": "ok", "name": req.job_name, "hinweis": ""}


@app.get("/api/trait-items")
async def trait_items():
    """Forced-Choice-Items für Stufe 2 (ohne Pol-Tags)."""
    return {"items": get_trait_items()}


@app.post("/api/insight")
async def post_insight(req: InsightRequest):
    """Stufe-2-Engine (Prototyp): Forced-Choice → ipsative Pol-Scores →
    EINE benannte Charakter-Wahrheit aus der schärfsten Spannung."""
    scores = score_traits(req.answers)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    profile = "\n".join([f"- {DIMENSIONS[k]['name']} ({DIMENSIONS[k]['desc']}): {v} von 5" for k, v in ranked])

    typ = f"\nKarriere-Typ (Interessen): {req.type_name} ({req.code})" if req.type_name else ""

    # Plausibilitaets-Check: stures Durchklicken -> KI soll nicht so tun, als haette
    # sie eine scharfe Wahrheit gefunden.
    quality = check_trait_quality(req.answers)
    quality_note = ""
    if not quality["valid"]:
        quality_note = (
            "\n\nACHTUNG — DUENNE DATENLAGE: Die Antworten wirken sehr einfoermig "
            "(viel dasselbe angeklickt oder kaum Variation). Das Profil ist wenig belastbar. "
            "Tu NICHT so, als haettest du einen scharfen Treffer. Formuliere zurueckhaltend und "
            "ehrlich aus den zwei staerksten der vorhandenen Eigenschaften — lieber eine vorsichtige, "
            "wahre Beobachtung als ein selbstsicherer Schuss ins Blaue."
        )

    prompt = f"""Du formulierst die zentrale "das bin so ich"-Erkenntnis fuer einen Karriere-Selbsttest.

Die Person hat 18 Aussagen auf einer Skala von 1-5 bewertet. Daraus ergeben sich 7 Eigenschaften
(1 = schwach, 5 = stark ausgepraegt):
{profile}{typ}{quality_note}

Die schaerfste Erkenntnis liegt in einer SPANNUNG. Zwei moegliche Muster — nimm das, das die
treffendste Zeile ergibt:
1. Zwei hohe Eigenschaften (4-5), die sich reiben.
2. Eine hohe Eigenschaft und das, was du dafuer opferst (eine klar niedrige, 1-2).

SONDERFALL flaches Profil (keine Eigenschaft ragt klar heraus, alle aehnlich): ERFINDE KEINE
"du-bist-konturlos / weisst-nicht-wofuer-du-stehst / passt-dich-ueberall-an"-Geschichte. Die widerspricht
fast immer dem echten Profil und trifft daneben. Nimm stattdessen die zwei staerksten der vorhandenen
Eigenschaften (oben zuerst gelistet) und bau die Spannung NUR aus denen.

AUFBAU der Erkenntnis (1-2 kurze Saetze):
- Erst die Spannung benennen.
- Dann eine leicht unbequeme, selbst-entlarvende KONSEQUENZ — die Stelle, wo man sich ertappt.

ENTSCHEIDEND — konkret, aber NICHT erfunden:
- Die Schaerfe kommt aus der unbequemen Konsequenz, NICHT aus einem ausgedachten Requisit.
- ERFINDE KEINE konkreten Gegenstaende oder Szenen, die nicht jeder hat: keine "Browser-Tabs",
  "E-Mails", "Kalender", "Post-its", "To-do-Listen", "Meetings". Die treffen nur manche — und wer
  sie nicht hat, fuehlt sich NICHT erkannt, sondern falsch eingeschaetzt. Das zerstoert den Moment.
- Werde praezise im MUSTER und im GEFUEHL — formuliere das, was fuer JEDEN mit diesem Muster wahr
  ist, scharf und unbequem. Praezise, nicht bebildert.

VERBOTEN als Schluss: vage Floskeln wie "kostet Zeit und Nerven", "bremst dich aus", "raubt
Energie", "faellt dir schwer", "zieht dich in zwei Richtungen". Zu allgemein.

Regeln:
- Mutige Beobachtung im Praesens. KEINE Weichmacher (kein "vielleicht/koennte/vermutlich") —
  Spiegel, keine Vorhersage.
- VERHALTEN statt CHARAKTER-URTEIL (wichtigster Hebel fuer "das bin ich"): Beschreibe, WAS die Person tut
  oder wozu sie neigt — niemals, WIE sie als Mensch IST. Ein Verhalten erkennt man wieder; ein Urteil wehrt
  man ab. GESPERRT sind absolute/urteilende Woerter: "nie", "immer", "ueber alles", "egal", "lässt ihn stehen",
  "willst nicht", "kannst nicht", "interessiert dich nicht", "musst nicht", "jeden/alle retten", "kannst nicht jeden".
  Die Konsequenz muss sich anfuehlen wie "ja, ertappt" — nicht wie "nein, so bin ich nicht".
  ✅ "Du merkst gar nicht, wie sehr du dann in deinem Tunnel bist."
  ❌ "Andere werden dir egal — du ziehst dein Ding durch und lässt sie stehen." (Urteil -> Abwehr)
  ✅ "Du sagst lieber ja, als jemanden zu enttaeuschen — und schluckst, was du eigentlich willst."
  ❌ "Selbst entscheiden willst du nicht, und sagst nie klar, was du brauchst." (absolut -> Vorwurf)
- Leicht unbequem, aber nie verletzend oder herablassend.
- KEINE Ratschlaege/Imperative ("üb mal", "lern", "versuch", "du musst", "du solltest", "lass los"). Die Zeile ist ein
  SPIEGEL, kein Tipp — beschreibe was IST, gib keinen Rat.
- Erfinde KEINE Zahlen/Mengen ("25 Kinder", "drei Projekte", "zehn Mails"). Die folgen nicht aus den Antworten und
  treffen nur manche — das zerstoert den Moment.
- Du-Form, kein Fachjargon. Nenne KEINE der Eigenschafts-Namen (Durchsetzung, Menschen, Struktur, Neugier, Kontakt, Ruhe, Eigenständigkeit) im Text.
- SPRACHE — verstaendlich UND wuchtig (das Wichtigste!): Schreib, wie du es einem 16-jaehrigen Azubi sagen
  wuerdest. Jedes Wort muss er SOFORT verstehen. Die Wucht kommt aus der WAHRHEIT, nicht aus großen Woertern.
  VERBOTEN sind abstrakte Hauptwoerter / Coach-Sprech ("Stressstabilitaet", "Anspannung regulieren",
  "in einen Modus wechseln", "Selbstregulation", "Resilienz") und verschachtelte Saetze. Einfache Verben,
  konkrete Bilder, kurze Saetze.
  ✅ "Wenn's brennt, machst du einfach schneller — statt kurz Luft zu holen."
  ❌ "Sobald der Druck steigt, wird genau das eng, wo du eigentlich stark sein willst."
- SATZBAU — der haeufigste Fehler: KEINE Schachtelsaetze. Kurze Hauptsaetze, EIN Gedanke pro Satz, hoechstens
  EIN Komma pro Satz. Keine eingeschobenen Nebensaetze ("du, wenn ..., eher ..."). Keine Ketten aus
  "bis ... und ... wenn ...". Zwei kurze Saetze schlagen einen langen. Der Stakkato-Rhythmus knallt mehr.
  ✅ "Du machst Tempo, bis dir die Luft wegbleibt. Dass du zu weit gehst, merkst du erst hinterher."
  ❌ "Statt still zu stehen, machst du Tempo, bis dir die Luft wegbleibt, und merkst erst, dass du am Limit bist, wenn du schon drüber bist."
- Niemals "als wie". Keine Emoji. Keine erfundenen Statistiken.
- Verwende AUSSCHLIESSLICH echte Umlaute (ä, ö, ü) und ß — niemals ae/oe/ue/ss als Ersatz.

✅ "Du willst schnell vorankommen — aber niemanden zuruecklassen. Also wartest du auf Leute, die du
   laengst ueberholt hast, und machst es am Ende doch selbst."
✅ "Du bist schon bei der naechsten Idee, bevor die letzte fertig ist — und die Haelfte deiner
   Anfaenge sieht nie das Tageslicht."
✅ "Du sagst ja, obwohl du innerlich laengst nein denkst — und keiner merkt, wie oft du dich dabei
   selbst uebergehst."
❌ "Dein Browser hat zwanzig Tabs mit halbfertigen Ideen offen." (erfundenes Requisit — trifft nur manche)
❌ "Du willst alles richtig machen und alle mitnehmen — das kostet dich Zeit und Nerven." (vage Floskel)
❌ "Du wirst als Fuehrungskraft erfolgreich sein." (Vorhersage)

Antworte NUR mit der Erkenntnis, kein Vorspann."""

    try:
        msg = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"insight": msg.content[0].text.strip(), "scores": scores, "ranked": [k for k, _ in ranked], "quality": quality}
    except Exception as e:
        return {"error": str(e), "scores": scores}


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


@app.get("/fit-intro", response_class=HTMLResponse)
async def fit_intro(request: Request):
    return templates.TemplateResponse("fit-intro.html", {"request": request})


@app.get("/trait-check", response_class=HTMLResponse)
async def trait_check(request: Request):
    return templates.TemplateResponse("trait-check.html", {"request": request})


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
    return {"status": "ok", "version": "3.23.0"}
