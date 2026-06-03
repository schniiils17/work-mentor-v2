"""
Holland/RIASEC Karriere-Assessment Engine

6 Dimensionen:
R = Realistic (Realistisch/Praktisch)
I = Investigative (Forschend/Analytisch)
A = Artistic (Künstlerisch/Kreativ)
S = Social (Sozial/Helfend)
E = Enterprising (Unternehmerisch/Führend)
C = Conventional (Konventionell/Organisierend)

24 Aussagen (4 pro Dimension) auf 5-Punkte Likert-Skala.
Items sind an den O*NET Interest Profiler des US Department of Labor (Public Domain)
angelehnt, für den deutschen Sprachraum und eine berufstätige Zielgruppe (25–40)
adaptiert. R und I wurden bewusst entakademisiert/enthandwerklicht, damit Büro-/
Wissensarbeiter nicht systematisch bei allen R/I-Items "nein" sagen (flache Profile).

Methodik:
- User bewertet jede Aussage: "Wie sehr wuerde dir das Spass machen?"
- Skala: -2 (nein) bis +2 (sehr)
- Pro Dimension werden 4 Items addiert -> Rohwert -8 bis +8
- Top-2 Dimensionen ergeben den Holland-Code (z.B. "EA")
- Generalist-Erkennung: wenn Profil zu flach -> Chamäleon
"""

import random
from typing import List, Dict
from collections import Counter


# === Items (24 Aussagen, 4 pro Dimension) ===
# Quelle: O*NET Interest Profiler (Public Domain, US Department of Labor)

ITEMS = [
    # --- R (Realistic) --- Praktisch-handwerklich
    {"id": 1,  "dim": "R", "text": "Mit Werkzeug etwas selbst bauen oder zusammenbauen — Möbel, Regale oder Deko"},
    {"id": 2,  "dim": "R", "text": "Ein kaputtes Gerät selbst reparieren, statt es wegzugeben"},
    {"id": 3,  "dim": "R", "text": "Körperlich anpacken und etwas mit den eigenen Händen schaffen"},
    {"id": 5,  "dim": "R", "text": "Technische Geräte oder Maschinen bedienen und am Laufen halten"},

    # --- I (Investigative) --- Forschend-analytisch
    {"id": 7,  "dim": "I", "text": "Einem Problem auf den Grund gehen, bis du genau weißt woran es liegt"},
    {"id": 8,  "dim": "I", "text": "Herausfinden wie etwas funktioniert, indem du es genau unter die Lupe nimmst"},
    {"id": 9,  "dim": "I", "text": "Dich in ein neues Thema reinfuchsen, bis du es wirklich durchblickst"},
    {"id": 10, "dim": "I", "text": "Daten und Zahlen auswerten, um ein Muster oder eine Antwort zu finden"},

    # --- A (Artistic) --- Künstlerisch-kreativ
    {"id": 14, "dim": "A", "text": "Texte schreiben die Menschen berühren — Blogs, Songs oder Stories"},
    {"id": 15, "dim": "A", "text": "Visuelle Inhalte gestalten — Grafiken, Videos oder Animationen"},
    {"id": 16, "dim": "A", "text": "Neue Konzepte oder ungewöhnliche Lösungsansätze entwickeln"},
    {"id": 18, "dim": "A", "text": "Räume, Möbel oder Mode designen"},

    # --- S (Social) --- Helfend-sozial
    {"id": 19, "dim": "S", "text": "Menschen mit persönlichen oder emotionalen Problemen helfen"},
    {"id": 20, "dim": "S", "text": "Andere bei ihrer Berufswahl oder Karriere beraten"},
    {"id": 22, "dim": "S", "text": "Kindern oder Jugendlichen etwas beibringen"},
    {"id": 24, "dim": "S", "text": "In einem Team Konflikte lösen und vermitteln"},

    # --- E (Enterprising) --- Unternehmerisch-führend
    {"id": 25, "dim": "E", "text": "Ein eigenes Unternehmen oder Startup gründen"},
    {"id": 26, "dim": "E", "text": "Eine Abteilung oder ein Team in einer Firma leiten"},
    {"id": 28, "dim": "E", "text": "Geschäftsverträge oder größere Deals verhandeln"},
    {"id": 29, "dim": "E", "text": "Andere von einer Idee oder einem Produkt überzeugen"},

    # --- C (Conventional) --- Organisierend-strukturiert
    {"id": 31, "dim": "C", "text": "Eine Excel-Tabelle aufbauen und mit Formeln arbeiten"},
    {"id": 33, "dim": "C", "text": "Die Buchhaltung oder Finanzen einer Firma führen"},
    {"id": 34, "dim": "C", "text": "Ein Ablage- oder Ordnungssystem aufbauen, in dem alles seinen Platz hat"},
    {"id": 35, "dim": "C", "text": "Abläufe und Prozesse in einem Unternehmen optimieren"},
]


# === Typ-Mapping ===
# Top-2 Holland-Code -> Typ-Name + Beschreibung + Stärken

TYPE_MAP = {
    "RI": {
        "name": "Der Technische Analyst",
        "description": "Vermutlich willst du nicht nur wissen WAS funktioniert, sondern WARUM. Und dann machst du es besser.",
        "strengths": ["Problemlöser", "Technisch versiert", "Analytisch"]
    },
    "RA": {
        "name": "Der Handwerker-Künstler",
        "description": "Es könnte sein, dass du Dinge gerne mit deinen Händen erschaffst — aber mit einem kreativen Twist. Qualität und Ästhetik dürften dir wichtig sein.",
        "strengths": ["Kreativ-praktisch", "Detailverliebt", "Handwerklich"]
    },
    "RS": {
        "name": "Der Praktische Helfer",
        "description": "Wahrscheinlich bist du jemand, der lieber anpackt als redet — und dabei gerne anderen hilft.",
        "strengths": ["Hilfsbereit", "Zupackend", "Verlässlich"]
    },
    "RE": {
        "name": "Der Macher",
        "description": "Vermutlich reicht dir Planen allein nicht — du willst Ergebnisse sehen. Schnell, pragmatisch, hands-on.",
        "strengths": ["Umsetzungsstark", "Pragmatisch", "Führend"]
    },
    "RC": {
        "name": "Der Systematiker",
        "description": "Gut möglich, dass du Ordnung und Struktur schätzt — Prozesse optimieren, Systeme aufbauen, alles an seinem Platz.",
        "strengths": ["Organisiert", "Zuverlässig", "Strukturiert"]
    },
    "IA": {
        "name": "Der Visionäre Denker",
        "description": "Vermutlich verbindest du tiefes Nachdenken mit kreativen Ideen. Wo andere Chaos sehen, erkennst du wahrscheinlich Muster.",
        "strengths": ["Innovativ", "Tiefgründig", "Visionär"]
    },
    "IS": {
        "name": "Der Einfühlsame Forscher",
        "description": "Es könnte sein, dass du Menschen wirklich verstehen willst — nicht oberflächlich, sondern was sie antreibt und bewegt.",
        "strengths": ["Empathisch", "Analytisch", "Einfühlsam"]
    },
    "IE": {
        "name": "Der Strategische Kopf",
        "description": "Vermutlich denkst du in Systemen und willst Wissen nicht nur sammeln, sondern anwenden — um etwas aufzubauen.",
        "strengths": ["Strategisch", "Wissbegierig", "Durchsetzungsstark"]
    },
    "IC": {
        "name": "Der Präzise Denker",
        "description": "Genauigkeit und Tiefe könnten deine Superkräfte sein. Du gräbst vermutlich tiefer als andere — und merkst, wenn etwas nicht stimmt.",
        "strengths": ["Genau", "Gründlich", "Analytisch"]
    },
    "AS": {
        "name": "Der Kreative Helfer",
        "description": "Vielleicht nutzt du deine Kreativität, um anderen zu helfen — ob durch Kunst, Worte oder Design.",
        "strengths": ["Inspirierend", "Einfühlsam", "Kreativ"]
    },
    "AE": {
        "name": "Der Kreative Stratege",
        "description": "Vermutlich brauchst du Gestaltungsfreiheit UND willst etwas bewegen. Routine dürfte dich killen — du willst wahrscheinlich Neues erschaffen und andere davon überzeugen.",
        "strengths": ["Innovativ", "Überzeugend", "Ideenreich"]
    },
    "AC": {
        "name": "Der Ästhetische Perfektionist",
        "description": "Gut möglich, dass es dir nicht reicht wenn etwas nur funktioniert — es muss wahrscheinlich auch gut aussehen.",
        "strengths": ["Perfektionistisch", "Ästhetisch", "Organisiert"]
    },
    "SE": {
        "name": "Der People Leader",
        "description": "Vermutlich inspirierst du Menschen eher durch echtes Interesse als durch Druck. Wenn du führen würdest, dann wahrscheinlich über Beziehungen — nicht über Autorität.",
        "strengths": ["Charismatisch", "Empathisch", "Führungsstark"]
    },
    "SC": {
        "name": "Der Strukturierte Helfer",
        "description": "Wahrscheinlich hilfst du gerne — aber mit System. Nicht chaotisch, sondern organisiert und verlässlich.",
        "strengths": ["Zuverlässig", "Hilfsbereit", "Organisiert"]
    },
    "EC": {
        "name": "Der Business-Macher",
        "description": "Vermutlich willst du aufbauen, wachsen, optimieren. Unternehmergeist gepaart mit einem Sinn für Struktur könnte dein Ding sein.",
        "strengths": ["Unternehmerisch", "Strukturiert", "Zielstrebig"]
    },
}


# === Job-Datenbank ===

JOB_DATABASE = {
    "RI": [
        {"title": "Ingenieur", "match": 91, "salary": "52.000 - 78.000", "desc": "Entwickle und optimiere technische Systeme und Produkte."},
        {"title": "IT-Systemadministrator", "match": 85, "salary": "42.000 - 65.000", "desc": "Halte komplexe IT-Systeme am Laufen und mach sie besser."},
        {"title": "Datenanalyst", "match": 79, "salary": "45.000 - 68.000", "desc": "Finde Muster in Daten und leite konkrete Handlungen ab."},
    ],
    "RA": [
        {"title": "Industriedesigner", "match": 88, "salary": "40.000 - 65.000", "desc": "Gestalte Produkte die funktional und schoen sind."},
        {"title": "Architekt", "match": 84, "salary": "45.000 - 72.000", "desc": "Entwirf Gebäude die Menschen inspirieren."},
        {"title": "Tischler / Möbeldesigner", "match": 78, "salary": "32.000 - 52.000", "desc": "Erschaffe einzigartige Möbelstuecke mit deinen Händen."},
    ],
    "RS": [
        {"title": "Physiotherapeut", "match": 87, "salary": "35.000 - 52.000", "desc": "Hilf Menschen durch gezielte Bewegungstherapie."},
        {"title": "Rettungssanitäter", "match": 83, "salary": "30.000 - 45.000", "desc": "Sei zur Stelle wenn es drauf ankommt."},
        {"title": "Ergotherapeut", "match": 79, "salary": "33.000 - 48.000", "desc": "Unterstütze Menschen dabei ihren Alltag zu meistern."},
    ],
    "RE": [
        {"title": "Bauleiter", "match": 89, "salary": "50.000 - 75.000", "desc": "Leite Bauprojekte von der Planung bis zur Fertigstellung."},
        {"title": "Produktionsleiter", "match": 85, "salary": "55.000 - 80.000", "desc": "Steuere Teams und Prozesse in der Fertigung."},
        {"title": "Handwerksmeister", "match": 80, "salary": "40.000 - 65.000", "desc": "Führe deinen eigenen Betrieb mit Hands-on-Mentalität."},
    ],
    "RC": [
        {"title": "Qualitätsmanager", "match": 86, "salary": "48.000 - 72.000", "desc": "Stelle sicher dass Standards eingehalten werden."},
        {"title": "Logistikplaner", "match": 82, "salary": "42.000 - 62.000", "desc": "Optimiere Lieferketten und Abläufe."},
        {"title": "Technischer Zeichner", "match": 77, "salary": "35.000 - 50.000", "desc": "Erstelle präzise Pläne für technische Projekte."},
    ],
    "IA": [
        {"title": "UX Researcher", "match": 89, "salary": "48.000 - 75.000", "desc": "Erforsche wie Menschen Produkte nutzen und verbessere sie."},
        {"title": "Wissenschaftsjournalist", "match": 83, "salary": "38.000 - 58.000", "desc": "Mach komplexe Themen für alle verständlich."},
        {"title": "Innovationsmanager", "match": 80, "salary": "55.000 - 85.000", "desc": "Entwickle neue Ideen und bring sie zur Marktreife."},
    ],
    "IS": [
        {"title": "Psychologe", "match": 90, "salary": "42.000 - 68.000", "desc": "Verstehe menschliches Verhalten und hilf Menschen zu wachsen."},
        {"title": "Sozialforscher", "match": 84, "salary": "40.000 - 60.000", "desc": "Erforsche gesellschaftliche Zusammenhänge und Trends."},
        {"title": "Pädagoge", "match": 79, "salary": "38.000 - 55.000", "desc": "Begleite Menschen auf ihrem Bildungsweg."},
    ],
    "IE": [
        {"title": "Unternehmensberater", "match": 90, "salary": "55.000 - 95.000", "desc": "Analysiere Unternehmen und entwickle Strategien."},
        {"title": "Data Scientist", "match": 86, "salary": "52.000 - 82.000", "desc": "Nutze Daten um bessere Entscheidungen zu ermöglichen."},
        {"title": "Produktmanager", "match": 82, "salary": "55.000 - 85.000", "desc": "Bringe Ideen vom Konzept zur Realität."},
    ],
    "IC": [
        {"title": "Wirtschaftsprüfer", "match": 88, "salary": "52.000 - 85.000", "desc": "Prüfe Unternehmen auf Herz und Nieren."},
        {"title": "Forschungsingenieur", "match": 84, "salary": "50.000 - 78.000", "desc": "Entwickle neue Technologien mit wissenschaftlicher Präzision."},
        {"title": "Pharmazeut", "match": 79, "salary": "48.000 - 72.000", "desc": "Sorge für sichere und wirksame Medikamente."},
    ],
    "AS": [
        {"title": "Therapeut (Kunst/Musik)", "match": 87, "salary": "35.000 - 55.000", "desc": "Nutze Kunst als Werkzeug um Menschen zu helfen."},
        {"title": "Lehrer (Kunst/Musik)", "match": 84, "salary": "42.000 - 62.000", "desc": "Inspiriere junge Menschen durch kreative Fächer."},
        {"title": "Social Media Manager", "match": 78, "salary": "35.000 - 55.000", "desc": "Erzähle Geschichten die Menschen berühren und verbinden."},
    ],
    "AE": [
        {"title": "UX Designer", "match": 87, "salary": "45.000 - 72.000", "desc": "Gestalte digitale Produkte die Menschen lieben."},
        {"title": "Produktmanager", "match": 82, "salary": "55.000 - 85.000", "desc": "Bringe Ideen vom Konzept zur Realität."},
        {"title": "Startup-Gründer", "match": 74, "salary": "Variabel", "desc": "Baue dein eigenes Ding von Null auf."},
    ],
    "AC": [
        {"title": "Grafikdesigner", "match": 88, "salary": "35.000 - 58.000", "desc": "Gestalte visuelle Kommunikation die begeistert."},
        {"title": "Art Director", "match": 83, "salary": "50.000 - 80.000", "desc": "Leite kreative Teams und definiere den visuellen Stil."},
        {"title": "Webdesigner", "match": 79, "salary": "38.000 - 60.000", "desc": "Baue Websites die gut aussehen und perfekt funktionieren."},
    ],
    "SE": [
        {"title": "Personalmanager (HR)", "match": 89, "salary": "48.000 - 75.000", "desc": "Finde und fördere die besten Talente."},
        {"title": "Teamleiter", "match": 85, "salary": "50.000 - 78.000", "desc": "Führe dein Team zu Höchstleistungen."},
        {"title": "Trainer / Coach", "match": 80, "salary": "40.000 - 70.000", "desc": "Entwickle Menschen und hilf ihnen zu wachsen."},
    ],
    "SC": [
        {"title": "Verwaltungsfachangestellter", "match": 85, "salary": "35.000 - 52.000", "desc": "Sorge dafür dass alles seinen geregelten Gang geht."},
        {"title": "Sozialarbeiter", "match": 82, "salary": "36.000 - 52.000", "desc": "Unterstütze Menschen in schwierigen Lebenslagen — systematisch."},
        {"title": "Medizinische Fachangestellte", "match": 78, "salary": "30.000 - 42.000", "desc": "Organisiere den Praxisalltag und kümmere dich um Patienten."},
    ],
    "EC": [
        {"title": "Projektmanager", "match": 90, "salary": "50.000 - 78.000", "desc": "Bringe komplexe Projekte strukturiert ins Ziel."},
        {"title": "Vertriebsleiter", "match": 85, "salary": "55.000 - 90.000", "desc": "Baue Vertriebsteams auf und erreiche ambitionierte Ziele."},
        {"title": "Finanzberater", "match": 80, "salary": "48.000 - 75.000", "desc": "Hilf Menschen und Unternehmen kluge finanzielle Entscheidungen zu treffen."},
    ],
}


# Backwards-compat
QUESTIONS = ITEMS


def get_shuffled_items() -> List[Dict]:
    """Return items in randomized order for each assessment."""
    shuffled = ITEMS.copy()
    random.shuffle(shuffled)
    return shuffled


def check_answer_quality(answers: List[Dict]) -> Dict:
    """Check if answers have enough variance to be meaningful."""
    values = [a.get("value", 0) for a in answers]
    if not values:
        return {"valid": False, "reason": "no_answers"}
    
    # Check if all answers are the same
    unique = set(values)
    if len(unique) <= 1:
        return {"valid": False, "reason": "all_same"}
    
    # Check variance — if std deviation < 0.5, too flat
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = variance ** 0.5
    
    if std_dev < 0.5:
        return {"valid": False, "reason": "too_flat"}
    
    # Check if >80% are the same value
    most_common_count = Counter(values).most_common(1)[0][1]
    if most_common_count / len(values) > 0.8:
        return {"valid": False, "reason": "too_uniform"}
    
    return {"valid": True, "reason": None}


def calculate_scores(answers: List[Dict]) -> Dict[str, int]:
    """
    Berechne RIASEC-Scores aus den Likert-Antworten.
    answers = [{"item_id": 1, "value": 2}, ...]
    value: -2 bis +2 (5-Punkte-Skala)
    """
    scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
    
    item_map = {it["id"]: it for it in ITEMS}
    
    for answer in answers:
        item_id = answer.get("item_id") or answer.get("question_id")
        item = item_map.get(item_id)
        if not item:
            continue
        
        value = answer.get("value", 0)
        value = max(-2, min(2, int(value)))
        scores[item["dim"]] += value
    
    return scores


def is_generalist(scores: Dict[str, int]) -> bool:
    """
    Prüfe ob das Profil zu flach ist für einen klaren Typ.
    Generalist = Chamäleon wenn:
    - Der hoechste Score unter 2 liegt (kaum positive Tendenz), ODER
    - Die Differenz zwischen Top-1 und Top-3 kleiner als 3 ist (alles aehnlich)
    (Schwellen auf 4 Items/Dimension skaliert, Rohwert-Range jetzt -8..+8.)
    """
    sorted_vals = sorted(scores.values(), reverse=True)
    top1 = sorted_vals[0]
    top3 = sorted_vals[2]

    # Schwellenwerte
    if top1 < 2:
        return True
    if (top1 - top3) < 3:
        return True

    return False


def get_top_two(scores: Dict[str, int]) -> str:
    """Ermittle den 2-Buchstaben Holland-Code (Top-2 Dimensionen)."""
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_dims[0][0] + sorted_dims[1][0]


def get_type_info(code: str, generalist: bool = False) -> Dict:
    """Hole Typ-Info für einen 2-Buchstaben Code."""
    
    if generalist:
        return {
            "name": "Das Chamäleon",
            "code": code,
            "description": "Wo andere ein klares Stärken-Profil haben, hast du vermutlich Range. Du wechselst möglicherweise Rollen, Branchen, Perspektiven — und nimmst aus jedem Kontext etwas mit.",
            "strengths": ["Vielseitig", "Anpassungsfähig", "Breit aufgestellt"]
        }
    
    if code in TYPE_MAP:
        return {**TYPE_MAP[code], "code": code}
    
    reversed_code = code[1] + code[0]
    if reversed_code in TYPE_MAP:
        return {**TYPE_MAP[reversed_code], "code": reversed_code}
    
    return {
        "name": "Der Entdecker",
        "code": code,
        "description": "Du hast vermutlich ein vielseitiges Profil — und das könnte eine echte Stärke sein.",
        "strengths": ["Vielseitig", "Anpassungsfähig", "Neugierig"]
    }


def get_matching_jobs(code: str) -> List[Dict]:
    """Hole passende Jobs für einen Holland-Code."""
    if code in JOB_DATABASE:
        return JOB_DATABASE[code]
    
    reversed_code = code[1] + code[0]
    if reversed_code in JOB_DATABASE:
        return JOB_DATABASE[reversed_code]
    
    first = code[0]
    for key, jobs in JOB_DATABASE.items():
        if key.startswith(first):
            return jobs
    
    return JOB_DATABASE.get("AE", [])


def assess(answers: List[Dict]) -> Dict:
    """
    Hauptfunktion: Nimmt Antworten entgegen und liefert das komplette Ergebnis.
    """
    quality = check_answer_quality(answers)
    scores = calculate_scores(answers)
    code = get_top_two(scores)
    generalist = is_generalist(scores)
    type_info = get_type_info(code, generalist)
    jobs = get_matching_jobs(code)
    
    # Normalisiere Scores auf 0-100 für das Hexagon
    # Maximum pro Dimension: 4 Items x 2 Punkte = 8
    max_possible = 8
    min_possible = -8
    normalized_scores = {}
    for dim, val in scores.items():
        normalized = ((val - min_possible) / (max_possible - min_possible)) * 100
        normalized_scores[dim] = max(0, min(100, round(normalized)))
    
    return {
        "code": type_info.get("code", code),
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
        "is_generalist": generalist,
        "answer_quality": quality,
    }


def _dim_label(dim: str) -> str:
    labels = {
        "R": "Realistisch",
        "I": "Forschend",
        "A": "Kreativ",
        "S": "Sozial",
        "E": "Unternehmerisch",
        "C": "Organisierend",
    }
    return labels.get(dim, dim)
