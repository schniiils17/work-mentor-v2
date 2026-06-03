"""Persönlichkeits-Stufe (Stufe 2) — Forced-Choice, ipsativ.

5 Arbeits-Pole, gemessen über 12 Entweder-oder-Paare (beide Optionen attraktiv).
Ergebnis ist relativ (Summe = Anzahl Items). Aus den Spannungen zwischen den
Polen baut die KI die zentrale "das bin so ich"-Erkenntnis.
"""

POLES = {
    "M": {"name": "Macher",    "desc": "schnell entscheiden, anpacken, vorangehen"},
    "V": {"name": "Verbinder", "desc": "Menschen, Konsens, Stimmung, Harmonie"},
    "S": {"name": "Vollender", "desc": "planen, ordnen, durchziehen, fertigmachen"},
    "E": {"name": "Entdecker", "desc": "Neues, Ideen, ausprobieren, Weite"},
    "F": {"name": "Freigeist", "desc": "unabhängig, eigener Weg, eigenes Tempo"},
}

TRAIT_ITEMS = [
    {"id": 1,  "a": {"text": "Schnell entscheiden und loslegen",            "pole": "M"}, "b": {"text": "Erst alle mit ins Boot holen",              "pole": "V"}},
    {"id": 2,  "a": {"text": "Neues ausprobieren und Ideen entwickeln",     "pole": "E"}, "b": {"text": "Dranbleiben, bis etwas fertig ist",          "pole": "S"}},
    {"id": 3,  "a": {"text": "Vollgas geben, um voranzukommen",             "pole": "M"}, "b": {"text": "Mein eigenes Tempo halten",                  "pole": "F"}},
    {"id": 4,  "a": {"text": "Im Team richtig aufgehen",                    "pole": "V"}, "b": {"text": "Lieber mein eigenes Ding machen",            "pole": "F"}},
    {"id": 5,  "a": {"text": "Mit einem klaren Plan starten",               "pole": "S"}, "b": {"text": "Spontan bleiben und schauen, was sich ergibt","pole": "E"}},
    {"id": 6,  "a": {"text": "Erst gründlich durchdenken",                  "pole": "S"}, "b": {"text": "Einfach anfangen und unterwegs anpassen",    "pole": "M"}},
    {"id": 7,  "a": {"text": "Dass sich alle wohlfühlen",                   "pole": "V"}, "b": {"text": "Dass die Sache vorankommt",                  "pole": "M"}},
    {"id": 8,  "a": {"text": "An einer kniffligen Idee tüfteln",            "pole": "E"}, "b": {"text": "Mit Leuten zusammen etwas bewegen",          "pole": "V"}},
    {"id": 9,  "a": {"text": "Frei und flexibel arbeiten",                  "pole": "F"}, "b": {"text": "Klare Abläufe und feste Strukturen",         "pole": "S"}},
    {"id": 10, "a": {"text": "Eine Entscheidung treffen und durchziehen",   "pole": "M"}, "b": {"text": "Erst alle Möglichkeiten ausloten",          "pole": "E"}},
    {"id": 11, "a": {"text": "Auf die Stimmung im Team achten",             "pole": "V"}, "b": {"text": "Auf saubere, fehlerfreie Ergebnisse achten", "pole": "S"}},
    {"id": 12, "a": {"text": "Selbst bestimmen, wie ich arbeite",           "pole": "F"}, "b": {"text": "Klare Ziele, die mich antreiben",            "pole": "M"}},
]

_ITEM_BY_ID = {it["id"]: it for it in TRAIT_ITEMS}


def score_traits(answers):
    """answers = [{"item_id": int, "choice": "a"|"b"}] -> {pole: count}"""
    scores = {k: 0 for k in POLES}
    for a in answers:
        it = _ITEM_BY_ID.get(a.get("item_id"))
        if not it:
            continue
        opt = it.get(a.get("choice"))
        if opt:
            scores[opt["pole"]] += 1
    return scores


def get_trait_items():
    """Items fürs Frontend (ohne Pol-Tags, damit nichts durchsickert)."""
    return [{"id": it["id"], "a": it["a"]["text"], "b": it["b"]["text"]} for it in TRAIT_ITEMS]
