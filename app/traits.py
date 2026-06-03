"""Persönlichkeits-Stufe (Stufe 2) — 7 Dimensionen, Likert.

7 arbeitsbezogene Dimensionen (Big Five + O*NET Work Styles), gemessen über
18 Aussagen auf einer 5-Punkte-Skala (1 = stimmt gar nicht .. 5 = stimmt völlig).
Einige Items sind umgekehrt gepolt (sign = -1), um Ja-Sage-Tendenzen zu brechen.
Aus dem Profil (hohe/niedrige Dimensionen + Spannungen) baut die KI die zentrale
"das bin so ich"-Erkenntnis und den Job-Fit.

Wissenschaftliche Verankerung je Dimension:
- DU Durchsetzung     = Extraversion-Facette Assertiveness / O*NET Führung, Initiative
- ME Menschen         = Verträglichkeit / O*NET Empathie, Kooperation
- ST Struktur         = Gewissenhaftigkeit / O*NET Verlässlichkeit, Sorgfalt (stärkster Job-Prädiktor)
- NE Neugier          = Offenheit / O*NET Innovation, Wissensdurst
- KO Kontakt          = Extraversion-Facette Sociability / O*NET Soziale Orientierung
- RU Ruhe             = Emotionale Stabilität / O*NET Stresstoleranz (zweitstärkster Prädiktor)
- EI Eigenständigkeit = O*NET Independence / Autonomie (Selbstbestimmung)

Empirisch geprüft (Kipp-Test + Persona-Recovery, 28 balancierte Personas):
96 % Recovery, ~14 % Fragilität — gegenüber dem alten 5-Pol-Forced-Choice
(~55 % Recovery, 35 % Fragilität, Freigeist faktisch nicht messbar).
"""

DIMENSIONS = {
    "DU": {"name": "Durchsetzung",     "desc": "entscheiden, vorangehen, sich behaupten"},
    "ME": {"name": "Menschen",         "desc": "auf andere achten, Harmonie, Mitgefühl"},
    "ST": {"name": "Struktur",         "desc": "planen, ordnen, Angefangenes zu Ende ziehen"},
    "NE": {"name": "Neugier",          "desc": "Neues ausprobieren, tüfteln, um die Ecke denken"},
    "KO": {"name": "Kontakt",          "desc": "auf Menschen zugehen, in Gruppen aufblühen"},
    "RU": {"name": "Ruhe",             "desc": "unter Druck und Stress gelassen bleiben"},
    "EI": {"name": "Eigenständigkeit", "desc": "Freiraum brauchen, den eigenen Weg gehen"},
}

# (id, dim, sign, text) — sign -1 = umgekehrt gepolt (6 - Wert)
# Kontakt (KO) bewusst geschärft auf reine Geselligkeit/Sichtbarkeit, damit es
# nicht mit Menschen (ME, Fürsorge) verschwimmt.
TRAIT_ITEMS = [
    {"id": 1,  "dim": "DU", "sign": +1, "text": "Wenn etwas entschieden werden muss, übernehme ich das oft."},
    {"id": 2,  "dim": "DU", "sign": -1, "text": "Ich gehe Konflikten lieber aus dem Weg."},
    {"id": 3,  "dim": "DU", "sign": +1, "text": "Ich sage klar meine Meinung, auch wenn sie aneckt."},
    {"id": 4,  "dim": "ME", "sign": +1, "text": "Mir ist wichtig, dass es allen im Team gut geht."},
    {"id": 5,  "dim": "ME", "sign": +1, "text": "Wie es anderen gerade geht, merke ich oft als Erster."},
    {"id": 6,  "dim": "ME", "sign": -1, "text": "Ob mich jemand mag, ist mir ehrlich gesagt ziemlich egal."},
    {"id": 7,  "dim": "ST", "sign": +1, "text": "Ich plane meine Aufgaben gern durch, bevor ich anfange."},
    {"id": 8,  "dim": "ST", "sign": +1, "text": "Angefangene Sachen ziehe ich zu Ende, auch wenn's zäh wird."},
    {"id": 9,  "dim": "ST", "sign": -1, "text": "Ich lasse Dinge gern mal liegen und mache sie später."},
    {"id": 10, "dim": "NE", "sign": +1, "text": "Ich probiere lieber Neues aus, als beim Bewährten zu bleiben."},
    {"id": 11, "dim": "NE", "sign": +1, "text": "An kniffligen, neuen Fragen tüftle ich gern lange."},
    {"id": 12, "dim": "KO", "sign": +1, "text": "Ich rede gern und viel — auch mit fremden Menschen."},
    {"id": 13, "dim": "KO", "sign": -1, "text": "Nach vielen Gesprächen bin ich eher ausgelaugt als aufgedreht."},
    {"id": 14, "dim": "KO", "sign": +1, "text": "Im Mittelpunkt zu stehen macht mir nichts aus."},
    {"id": 15, "dim": "RU", "sign": +1, "text": "Wenn's stressig wird, bleibe ich meistens ruhig."},
    {"id": 16, "dim": "RU", "sign": -1, "text": "Druck und enge Deadlines bringen mich schnell aus dem Takt."},
    {"id": 17, "dim": "EI", "sign": +1, "text": "Ich arbeite am liebsten eigenständig, ohne dass mir jemand reinredet."},
    {"id": 18, "dim": "EI", "sign": -1, "text": "Klare Ansagen von oben sind mir lieber als völlige Freiheit."},
]

_ITEM_BY_ID = {it["id"]: it for it in TRAIT_ITEMS}


def score_traits(answers):
    """answers = [{"item_id": int, "value": 1..5}] -> {dim: Mittel 1.0-5.0}.

    Umgekehrt gepolte Items (sign -1) werden gespiegelt (6 - Wert), sodass ein
    hoher Dimensionswert immer "stark ausgeprägt" bedeutet.
    """
    sums = {k: 0 for k in DIMENSIONS}
    counts = {k: 0 for k in DIMENSIONS}
    for a in answers:
        it = _ITEM_BY_ID.get(a.get("item_id"))
        if not it:
            continue
        v = a.get("value")
        if v is None:
            continue
        v = max(1, min(5, int(v)))
        contrib = v if it["sign"] > 0 else 6 - v
        sums[it["dim"]] += contrib
        counts[it["dim"]] += 1
    return {k: round(sums[k] / counts[k], 1) if counts[k] else 3.0 for k in DIMENSIONS}


def get_trait_items():
    """Items fürs Frontend (ohne Dimension/Pol-Tag, damit nichts durchsickert)."""
    return [{"id": it["id"], "text": it["text"]} for it in TRAIT_ITEMS]
