"""
Holland/RIASEC Karriere-Assessment Engine

6 Dimensionen:
R = Realistic (Realistisch/Praktisch)
I = Investigative (Forschend/Analytisch)
A = Artistic (Künstlerisch/Kreativ)
S = Social (Sozial/Helfend)
E = Enterprising (Unternehmerisch/Führend)
C = Conventional (Konventionell/Organisierend)

12 Forced-Choice Fragen — jede Antwort gibt Punkte auf 1-2 Dimensionen.
"""

from typing import List, Dict, Tuple

# ─── Fragen ──────────────────────────────────────────────────────────
# Jede Frage hat zwei Optionen (A/B).
# Jede Option vergibt Punkte auf eine oder mehrere RIASEC-Dimensionen.

QUESTIONS = [
    {
        "id": 1,
        "question": "Was machst du lieber?",
        "option_a": {
            "text": "Etwas Technisches bauen oder reparieren",
            "icon": "🔧",
            "scores": {"R": 2}
        },
        "option_b": {
            "text": "Etwas Kreatives gestalten oder designen",
            "icon": "🎨",
            "scores": {"A": 2}
        }
    },
    {
        "id": 2,
        "question": "Neues Projekt — was ist dein erster Impuls?",
        "option_a": {
            "text": "Daten sammeln und das Problem analysieren",
            "icon": "🔬",
            "scores": {"I": 2}
        },
        "option_b": {
            "text": "Menschen zusammenbringen und Aufgaben verteilen",
            "icon": "🤝",
            "scores": {"E": 1, "S": 1}
        }
    },
    {
        "id": 3,
        "question": "Welches Kompliment freut dich mehr?",
        "option_a": {
            "text": "\"Du kannst echt gut erklären!\"",
            "icon": "💬",
            "scores": {"S": 2}
        },
        "option_b": {
            "text": "\"Du hast echt den Durchblick bei Zahlen!\"",
            "icon": "📊",
            "scores": {"C": 1, "I": 1}
        }
    },
    {
        "id": 4,
        "question": "Samstagnachmittag — was machst du lieber?",
        "option_a": {
            "text": "An einem DIY-Projekt in der Werkstatt arbeiten",
            "icon": "🪚",
            "scores": {"R": 2}
        },
        "option_b": {
            "text": "Einen Business-Plan oder eine Strategie ausarbeiten",
            "icon": "📈",
            "scores": {"E": 2}
        }
    },
    {
        "id": 5,
        "question": "Was nervt dich weniger?",
        "option_a": {
            "text": "Stundenlang Excel-Tabellen organisieren",
            "icon": "📋",
            "scores": {"C": 2}
        },
        "option_b": {
            "text": "Stundenlang kreative Texte schreiben",
            "icon": "✍️",
            "scores": {"A": 2}
        }
    },
    {
        "id": 6,
        "question": "In einem Team — welche Rolle ziehst du an?",
        "option_a": {
            "text": "Die Person die Konflikte löst und alle zusammenhält",
            "icon": "🫂",
            "scores": {"S": 2}
        },
        "option_b": {
            "text": "Die Person die die Richtung vorgibt und Entscheidungen trifft",
            "icon": "🧭",
            "scores": {"E": 2}
        }
    },
    {
        "id": 7,
        "question": "Welches Buch greifst du eher?",
        "option_a": {
            "text": "Ein Sachbuch über Wissenschaft oder Technologie",
            "icon": "🧪",
            "scores": {"I": 2}
        },
        "option_b": {
            "text": "Eine Biografie über einen erfolgreichen Unternehmer",
            "icon": "📖",
            "scores": {"E": 1, "A": 1}
        }
    },
    {
        "id": 8,
        "question": "Was beschreibt dich besser?",
        "option_a": {
            "text": "Ich arbeite gerne mit meinen Händen — Ergebnisse anfassen können",
            "icon": "🖐️",
            "scores": {"R": 2}
        },
        "option_b": {
            "text": "Ich arbeite gerne mit Menschen — zuhören und unterstützen",
            "icon": "❤️",
            "scores": {"S": 2}
        }
    },
    {
        "id": 9,
        "question": "Dein Chef gibt dir die Wahl:",
        "option_a": {
            "text": "Ein komplexes Problem alleine lösen",
            "icon": "🧩",
            "scores": {"I": 1, "R": 1}
        },
        "option_b": {
            "text": "Ein neues Projekt vor dem Vorstand präsentieren",
            "icon": "🎤",
            "scores": {"E": 2}
        }
    },
    {
        "id": 10,
        "question": "Welcher Fehler stört dich mehr?",
        "option_a": {
            "text": "Eine Präsentation die langweilig und uninspiriert ist",
            "icon": "😴",
            "scores": {"A": 2}
        },
        "option_b": {
            "text": "Ein Bericht der ungenau und schlecht organisiert ist",
            "icon": "🚫",
            "scores": {"C": 2}
        }
    },
    {
        "id": 11,
        "question": "Was gibt dir mehr Energie?",
        "option_a": {
            "text": "Jemandem bei einem persönlichen Problem helfen",
            "icon": "🌱",
            "scores": {"S": 2}
        },
        "option_b": {
            "text": "Ein System optimieren das danach reibungslos läuft",
            "icon": "⚙️",
            "scores": {"C": 1, "R": 1}
        }
    },
    {
        "id": 12,
        "question": "Wenn Geld keine Rolle spielen würde:",
        "option_a": {
            "text": "Ein eigenes Startup gründen",
            "icon": "🚀",
            "scores": {"E": 1, "A": 1}
        },
        "option_b": {
            "text": "An einer Forschungseinrichtung arbeiten",
            "icon": "🏛️",
            "scores": {"I": 2}
        }
    }
]


# ─── Typ-Mapping ─────────────────────────────────────────────────────
# Top-2 Holland-Code → Typ-Name + Beschreibung + Stärken

TYPE_MAP = {
    "RI": {
        "name": "Der Technische Analyst",
        "description": "Du kombinierst praktisches Geschick mit analytischem Denken. Du willst verstehen wie Dinge funktionieren — und sie dann besser machen. Komplexe Probleme mit konkreten Lösungen sind dein Ding.",
        "strengths": ["Problemlöser", "Technisch versiert", "Analytisch"]
    },
    "RA": {
        "name": "Der Handwerker-Künstler",
        "description": "Du erschaffst gerne Dinge mit deinen Händen — aber mit einem kreativen Twist. Qualität und Ästhetik sind dir wichtig. Du machst nicht einfach irgendwas, du machst es schön.",
        "strengths": ["Kreativ-praktisch", "Detailverliebt", "Handwerklich"]
    },
    "RS": {
        "name": "Der Praktische Helfer",
        "description": "Du packst gerne an und hilfst dabei anderen. Nicht mit Worten, sondern mit Taten. Du bist die Person die anruft wenn etwas kaputt ist — und die sich freut wenn sie helfen konnte.",
        "strengths": ["Hilfsbereit", "Zupackend", "Verlässlich"]
    },
    "RE": {
        "name": "Der Macher",
        "description": "Du willst Dinge nicht nur planen — du willst sie umsetzen. Schnell, pragmatisch, ergebnisorientiert. Du führst am liebsten indem du zeigst wie's geht.",
        "strengths": ["Umsetzungsstark", "Pragmatisch", "Führend"]
    },
    "RC": {
        "name": "Der Systematiker",
        "description": "Du liebst Ordnung und Struktur in der praktischen Welt. Prozesse optimieren, Systeme aufbauen, alles an seinem Platz. Du bist das Fundament auf dem andere aufbauen.",
        "strengths": ["Organisiert", "Zuverlässig", "Strukturiert"]
    },
    "IA": {
        "name": "Der Visionäre Denker",
        "description": "Du verbindest tiefes Nachdenken mit kreativen Ideen. Du siehst Muster wo andere Chaos sehen und entwickelst Lösungen die niemand erwartet hätte. Innovation ist dein Antrieb.",
        "strengths": ["Innovativ", "Tiefgründig", "Visionär"]
    },
    "IS": {
        "name": "Der Einfühlsame Forscher",
        "description": "Du willst Menschen verstehen — wirklich verstehen. Nicht oberflächlich, sondern was sie antreibt und bewegt. Du analysierst mit Kopf und Herz.",
        "strengths": ["Empathisch", "Analytisch", "Einfühlsam"]
    },
    "IE": {
        "name": "Der Strategische Kopf",
        "description": "Du denkst in Systemen und willst sie nutzen um etwas aufzubauen. Wissen ist für dich kein Selbstzweck — du willst es anwenden und damit führen.",
        "strengths": ["Strategisch", "Wissbegierig", "Durchsetzungsstark"]
    },
    "IC": {
        "name": "Der Präzise Denker",
        "description": "Genauigkeit und Tiefe sind deine Superkräfte. Du gräbst tiefer als andere und sorgst dafür dass alles stimmt. Fehler findest du — immer.",
        "strengths": ["Genau", "Gründlich", "Analytisch"]
    },
    "AS": {
        "name": "Der Kreative Helfer",
        "description": "Du nutzt deine Kreativität um anderen zu helfen. Ob durch Kunst, Worte oder Design — du inspirierst Menschen und gibst ihnen neue Perspektiven.",
        "strengths": ["Inspirierend", "Einfühlsam", "Kreativ"]
    },
    "AE": {
        "name": "Der Kreative Stratege",
        "description": "Du brauchst Gestaltungsfreiheit UND willst etwas bewegen. Routine killt dich — du willst Neues erschaffen und andere davon überzeugen. Du denkst groß und handelst schnell.",
        "strengths": ["Innovativ", "Überzeugend", "Ideenreich"]
    },
    "AC": {
        "name": "Der Ästhetische Perfektionist",
        "description": "Für dich muss es nicht nur funktionieren — es muss auch gut aussehen. Du bringst Kreativität und Ordnung zusammen und schaffst Dinge die schön UND durchdacht sind.",
        "strengths": ["Perfektionistisch", "Ästhetisch", "Organisiert"]
    },
    "SE": {
        "name": "Der People Leader",
        "description": "Du inspirierst Menschen und bringst sie dazu ihr Bestes zu geben. Du führst nicht durch Druck, sondern durch echtes Interesse an deinem Gegenüber. Beziehungen sind deine Währung.",
        "strengths": ["Charismatisch", "Empathisch", "Führungsstark"]
    },
    "SC": {
        "name": "Der Strukturierte Helfer",
        "description": "Du hilfst gerne — aber mit System. Nicht chaotisch, sondern organisiert und verlässlich. Du sorgst dafür dass Hilfe auch wirklich ankommt.",
        "strengths": ["Zuverlässig", "Hilfsbereit", "Organisiert"]
    },
    "EC": {
        "name": "Der Business-Macher",
        "description": "Du willst aufbauen, wachsen, optimieren. Du verbindest Unternehmergeist mit einem Sinn für Struktur. Du träumst nicht nur groß — du setzt es auch professionell um.",
        "strengths": ["Unternehmerisch", "Strukturiert", "Zielstrebig"]
    },
}


# ─── Job-Datenbank ───────────────────────────────────────────────────
# Top-3 Jobs pro Typ-Code mit Match-Score und Gehalt

JOB_DATABASE = {
    "RI": [
        {"title": "Ingenieur", "match": 91, "salary": "€52.000 – €78.000", "desc": "Entwickle und optimiere technische Systeme und Produkte."},
        {"title": "IT-Systemadministrator", "match": 85, "salary": "€42.000 – €65.000", "desc": "Halte komplexe IT-Systeme am Laufen und mach sie besser."},
        {"title": "Datenanalyst", "match": 79, "salary": "€45.000 – €68.000", "desc": "Finde Muster in Daten und leite konkrete Handlungen ab."},
    ],
    "RA": [
        {"title": "Industriedesigner", "match": 88, "salary": "€40.000 – €65.000", "desc": "Gestalte Produkte die funktional und schön sind."},
        {"title": "Architekt", "match": 84, "salary": "€45.000 – €72.000", "desc": "Entwirf Gebäude die Menschen inspirieren."},
        {"title": "Tischler / Möbeldesigner", "match": 78, "salary": "€32.000 – €52.000", "desc": "Erschaffe einzigartige Möbelstücke mit deinen Händen."},
    ],
    "RS": [
        {"title": "Physiotherapeut", "match": 87, "salary": "€35.000 – €52.000", "desc": "Hilf Menschen durch gezielte Bewegungstherapie."},
        {"title": "Rettungssanitäter", "match": 83, "salary": "€30.000 – €45.000", "desc": "Sei zur Stelle wenn es drauf ankommt."},
        {"title": "Ergotherapeut", "match": 79, "salary": "€33.000 – €48.000", "desc": "Unterstütze Menschen dabei ihren Alltag zu meistern."},
    ],
    "RE": [
        {"title": "Bauleiter", "match": 89, "salary": "€50.000 – €75.000", "desc": "Leite Bauprojekte von der Planung bis zur Fertigstellung."},
        {"title": "Produktionsleiter", "match": 85, "salary": "€55.000 – €80.000", "desc": "Steuere Teams und Prozesse in der Fertigung."},
        {"title": "Handwerksmeister", "match": 80, "salary": "€40.000 – €65.000", "desc": "Führe deinen eigenen Betrieb mit Hands-on-Mentalität."},
    ],
    "RC": [
        {"title": "Qualitätsmanager", "match": 86, "salary": "€48.000 – €72.000", "desc": "Stelle sicher dass Standards eingehalten werden."},
        {"title": "Logistikplaner", "match": 82, "salary": "€42.000 – €62.000", "desc": "Optimiere Lieferketten und Abläufe."},
        {"title": "Technischer Zeichner", "match": 77, "salary": "€35.000 – €50.000", "desc": "Erstelle präzise Pläne für technische Projekte."},
    ],
    "IA": [
        {"title": "UX Researcher", "match": 89, "salary": "€48.000 – €75.000", "desc": "Erforsche wie Menschen Produkte nutzen und verbessere sie."},
        {"title": "Wissenschaftsjournalist", "match": 83, "salary": "€38.000 – €58.000", "desc": "Mach komplexe Themen für alle verständlich."},
        {"title": "Innovationsmanager", "match": 80, "salary": "€55.000 – €85.000", "desc": "Entwickle neue Ideen und bring sie zur Marktreife."},
    ],
    "IS": [
        {"title": "Psychologe", "match": 90, "salary": "€42.000 – €68.000", "desc": "Verstehe menschliches Verhalten und hilf Menschen zu wachsen."},
        {"title": "Sozialforscher", "match": 84, "salary": "€40.000 – €60.000", "desc": "Erforsche gesellschaftliche Zusammenhänge und Trends."},
        {"title": "Pädagoge", "match": 79, "salary": "€38.000 – €55.000", "desc": "Begleite Menschen auf ihrem Bildungsweg."},
    ],
    "IE": [
        {"title": "Unternehmensberater", "match": 90, "salary": "€55.000 – €95.000", "desc": "Analysiere Unternehmen und entwickle Strategien."},
        {"title": "Data Scientist", "match": 86, "salary": "€52.000 – €82.000", "desc": "Nutze Daten um bessere Entscheidungen zu ermöglichen."},
        {"title": "Produktmanager", "match": 82, "salary": "€55.000 – €85.000", "desc": "Bringe Ideen vom Konzept zur Realität."},
    ],
    "IC": [
        {"title": "Wirtschaftsprüfer", "match": 88, "salary": "€52.000 – €85.000", "desc": "Prüfe Unternehmen auf Herz und Nieren."},
        {"title": "Forschungsingenieur", "match": 84, "salary": "€50.000 – €78.000", "desc": "Entwickle neue Technologien mit wissenschaftlicher Präzision."},
        {"title": "Pharmazeut", "match": 79, "salary": "€48.000 – €72.000", "desc": "Sorge für sichere und wirksame Medikamente."},
    ],
    "AS": [
        {"title": "Therapeut (Kunst/Musik)", "match": 87, "salary": "€35.000 – €55.000", "desc": "Nutze Kunst als Werkzeug um Menschen zu helfen."},
        {"title": "Lehrer (Kunst/Musik)", "match": 84, "salary": "€42.000 – €62.000", "desc": "Inspiriere junge Menschen durch kreative Fächer."},
        {"title": "Social Media Manager", "match": 78, "salary": "€35.000 – €55.000", "desc": "Erzähle Geschichten die Menschen berühren und verbinden."},
    ],
    "AE": [
        {"title": "UX Designer", "match": 87, "salary": "€45.000 – €72.000", "desc": "Gestalte digitale Produkte die Menschen lieben."},
        {"title": "Produktmanager", "match": 82, "salary": "€55.000 – €85.000", "desc": "Bringe Ideen vom Konzept zur Realität."},
        {"title": "Startup-Gründer", "match": 74, "salary": "Variabel", "desc": "Baue dein eigenes Ding von Null auf."},
    ],
    "AC": [
        {"title": "Grafikdesigner", "match": 88, "salary": "€35.000 – €58.000", "desc": "Gestalte visuelle Kommunikation die begeistert."},
        {"title": "Art Director", "match": 83, "salary": "€50.000 – €80.000", "desc": "Leite kreative Teams und definiere den visuellen Stil."},
        {"title": "Webdesigner", "match": 79, "salary": "€38.000 – €60.000", "desc": "Baue Websites die gut aussehen und perfekt funktionieren."},
    ],
    "SE": [
        {"title": "Personalmanager (HR)", "match": 89, "salary": "€48.000 – €75.000", "desc": "Finde und fördere die besten Talente."},
        {"title": "Teamleiter", "match": 85, "salary": "€50.000 – €78.000", "desc": "Führe dein Team zu Höchstleistungen."},
        {"title": "Trainer / Coach", "match": 80, "salary": "€40.000 – €70.000", "desc": "Entwickle Menschen und hilf ihnen zu wachsen."},
    ],
    "SC": [
        {"title": "Verwaltungsfachangestellter", "match": 85, "salary": "€35.000 – €52.000", "desc": "Sorge dafür dass alles seinen geregelten Gang geht."},
        {"title": "Sozialarbeiter", "match": 82, "salary": "€36.000 – €52.000", "desc": "Unterstütze Menschen in schwierigen Lebenslagen — systematisch."},
        {"title": "Medizinische Fachangestellte", "match": 78, "salary": "€30.000 – €42.000", "desc": "Organisiere den Praxisalltag und kümmere dich um Patienten."},
    ],
    "EC": [
        {"title": "Projektmanager", "match": 90, "salary": "€50.000 – €78.000", "desc": "Bringe komplexe Projekte strukturiert ins Ziel."},
        {"title": "Vertriebsleiter", "match": 85, "salary": "€55.000 – €90.000", "desc": "Baue Vertriebsteams auf und erreiche ambitionierte Ziele."},
        {"title": "Finanzberater", "match": 80, "salary": "€48.000 – €75.000", "desc": "Hilf Menschen und Unternehmen kluge finanzielle Entscheidungen zu treffen."},
    ],
}


def calculate_scores(answers: List[Dict]) -> Dict[str, int]:
    """
    Berechne RIASEC-Scores aus den Antworten.
    answers = [{"question_id": 1, "choice": "a"}, ...]
    """
    scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    
    question_map = {q["id"]: q for q in QUESTIONS}
    
    for answer in answers:
        q = question_map.get(answer["question_id"])
        if not q:
            continue
        
        choice = answer["choice"]
        if choice == "a":
            option_scores = q["option_a"]["scores"]
        elif choice == "b":
            option_scores = q["option_b"]["scores"]
        else:
            continue
        
        for dim, pts in option_scores.items():
            scores[dim] += pts
    
    return scores


def get_top_two(scores: Dict[str, int]) -> str:
    """Ermittle den 2-Buchstaben Holland-Code (Top-2 Dimensionen)."""
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_dims[0][0] + sorted_dims[1][0]


def get_type_info(code: str) -> Dict:
    """Hole Typ-Info für einen 2-Buchstaben Code. Probiert beide Reihenfolgen."""
    if code in TYPE_MAP:
        return {**TYPE_MAP[code], "code": code}
    
    reversed_code = code[1] + code[0]
    if reversed_code in TYPE_MAP:
        return {**TYPE_MAP[reversed_code], "code": reversed_code}
    
    # Fallback
    return {
        "name": "Der Entdecker",
        "code": code,
        "description": "Du hast ein vielseitiges Profil — das ist eine Stärke! Du passt dich an und findest in vielen Bereichen deinen Weg.",
        "strengths": ["Vielseitig", "Anpassungsfähig", "Neugierig"]
    }


def get_matching_jobs(code: str) -> List[Dict]:
    """Hole passende Jobs für einen Holland-Code."""
    if code in JOB_DATABASE:
        return JOB_DATABASE[code]
    
    reversed_code = code[1] + code[0]
    if reversed_code in JOB_DATABASE:
        return JOB_DATABASE[reversed_code]
    
    # Fallback: Jobs der ersten Dimension
    first = code[0]
    for key, jobs in JOB_DATABASE.items():
        if key.startswith(first):
            return jobs
    
    return JOB_DATABASE.get("AE", [])


def assess(answers: List[Dict]) -> Dict:
    """
    Hauptfunktion: Nimmt Antworten entgegen und liefert das komplette Ergebnis.
    """
    scores = calculate_scores(answers)
    code = get_top_two(scores)
    type_info = get_type_info(code)
    jobs = get_matching_jobs(code)
    
    # Normalisiere Scores auf 0-100 für das Hexagon
    max_possible = 8  # Theoretisches Maximum pro Dimension
    normalized_scores = {}
    for dim, val in scores.items():
        normalized_scores[dim] = min(round((val / max_possible) * 100), 100)
    
    return {
        "code": type_info["code"],
        "dimensions": {
            "first": code[0],
            "second": code[1],
            "first_label": _dim_label(code[0]),
            "second_label": _dim_label(code[1]),
        },
        "type_name": type_info["name"],
        "description": type_info["description"],
        "strengths": type_info["strengths"],
        "scores": scores,
        "normalized_scores": normalized_scores,
        "jobs": jobs,
    }


def _dim_label(dim: str) -> str:
    """Menschenlesbarer Name für eine RIASEC-Dimension."""
    labels = {
        "R": "Realistisch",
        "I": "Forschend",
        "A": "Kreativ",
        "S": "Sozial",
        "E": "Unternehmerisch",
        "C": "Organisierend",
    }
    return labels.get(dim, dim)
