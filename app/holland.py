"""
Holland/RIASEC Karriere-Assessment Engine

6 Dimensionen:
R = Realistic (Realistisch/Praktisch)
I = Investigative (Forschend/Analytisch)
A = Artistic (Kuenstlerisch/Kreativ)
S = Social (Sozial/Helfend)
E = Enterprising (Unternehmerisch/Fuehrend)
C = Conventional (Konventionell/Organisierend)

36 Aussagen (6 pro Dimension) auf 5-Punkte Likert-Skala.
Items basieren auf dem O*NET Interest Profiler des US Department of Labor (Public Domain),
uebersetzt und fuer den deutschen Sprachraum adaptiert.

Methodik:
- User bewertet jede Aussage: "Wie sehr wuerde dir das Spass machen?"
- Skala: -2 (nein) bis +2 (sehr)
- Pro Dimension werden 6 Items addiert -> Rohwert -12 bis +12
- Top-2 Dimensionen ergeben den Holland-Code (z.B. "EA")
- Generalist-Erkennung: wenn Profil zu flach -> Chamaeleon
"""

from typing import List, Dict


# === Items (36 Aussagen, 6 pro Dimension) ===
# Quelle: O*NET Interest Profiler (Public Domain, US Department of Labor)

ITEMS = [
    # --- R (Realistic) --- Praktisch-handwerklich
    {"id": 1,  "dim": "R", "text": "Mit Werkzeug etwas selbst bauen -- z.B. Moebel oder einen Schrank"},
    {"id": 2,  "dim": "R", "text": "Ein kaputtes Geraet selbst auseinandernehmen und reparieren"},
    {"id": 3,  "dim": "R", "text": "Einen PC aus Einzelteilen zusammenbauen"},
    {"id": 4,  "dim": "R", "text": "Eine Maschine oder Anlage bedienen die Produkte herstellt"},
    {"id": 5,  "dim": "R", "text": "Draussen arbeiten -- Garten, Baustelle oder Werkstatt"},
    {"id": 6,  "dim": "R", "text": "Ein Auto oder Fahrrad selbst warten und reparieren"},
    
    # --- I (Investigative) --- Forschend-analytisch
    {"id": 7,  "dim": "I", "text": "Ein neues Medikament oder eine Therapie entwickeln"},
    {"id": 8,  "dim": "I", "text": "Erforschen wie man Umweltverschmutzung reduzieren kann"},
    {"id": 9,  "dim": "I", "text": "Im Labor an Proben oder Experimenten arbeiten"},
    {"id": 10, "dim": "I", "text": "Daten auswerten um ein Muster oder eine Antwort zu finden"},
    {"id": 11, "dim": "I", "text": "Wissenschaftliche Artikel lesen um ein Problem zu verstehen"},
    {"id": 12, "dim": "I", "text": "Eine Studie planen und durchfuehren"},
    
    # --- A (Artistic) --- Kuenstlerisch-kreativ
    {"id": 13, "dim": "A", "text": "Ein Buch, eine Geschichte oder ein Drehbuch schreiben"},
    {"id": 14, "dim": "A", "text": "Ein Musikinstrument spielen oder Musik produzieren"},
    {"id": 15, "dim": "A", "text": "Visuelle Inhalte gestalten -- Grafiken, Videos oder Animationen"},
    {"id": 16, "dim": "A", "text": "Ein Buehenstueck, Konzert oder eine kreative Show entwickeln"},
    {"id": 17, "dim": "A", "text": "Fotos machen und kuenstlerisch bearbeiten"},
    {"id": 18, "dim": "A", "text": "Raeume, Moebel oder Mode designen"},
    
    # --- S (Social) --- Helfend-sozial
    {"id": 19, "dim": "S", "text": "Menschen mit persoenlichen oder emotionalen Problemen helfen"},
    {"id": 20, "dim": "S", "text": "Andere bei ihrer Berufswahl oder Karriere beraten"},
    {"id": 21, "dim": "S", "text": "Eine Schulklasse oder Gruppe unterrichten"},
    {"id": 22, "dim": "S", "text": "Kindern oder Jugendlichen etwas beibringen"},
    {"id": 23, "dim": "S", "text": "Aeltere Menschen oder Kranke betreuen und unterstuetzen"},
    {"id": 24, "dim": "S", "text": "In einem Team Konflikte loesen und vermitteln"},
    
    # --- E (Enterprising) --- Unternehmerisch-fuehrend
    {"id": 25, "dim": "E", "text": "Ein eigenes Unternehmen oder Startup gruenden"},
    {"id": 26, "dim": "E", "text": "Eine Abteilung oder ein Team in einer Firma leiten"},
    {"id": 27, "dim": "E", "text": "Mit Aktien, Investments oder Finanzmaerkten handeln"},
    {"id": 28, "dim": "E", "text": "Geschaeftsvertraege oder groessere Deals verhandeln"},
    {"id": 29, "dim": "E", "text": "Andere von einer Idee oder einem Produkt ueberzeugen"},
    {"id": 30, "dim": "E", "text": "Entscheidungen treffen die ein ganzes Projekt beeinflussen"},
    
    # --- C (Conventional) --- Organisierend-strukturiert
    {"id": 31, "dim": "C", "text": "Eine Excel-Tabelle aufbauen und mit Formeln arbeiten"},
    {"id": 32, "dim": "C", "text": "Dokumente Korrektur lesen und Fehler finden"},
    {"id": 33, "dim": "C", "text": "Die Buchhaltung oder Finanzen einer Firma fuehren"},
    {"id": 34, "dim": "C", "text": "Lagerbestaende erfassen und sauber dokumentieren"},
    {"id": 35, "dim": "C", "text": "Ablaeufe und Prozesse in einem Unternehmen optimieren"},
    {"id": 36, "dim": "C", "text": "Termine, Reisen oder Veranstaltungen planen und koordinieren"},
]


# === Typ-Mapping ===
# Top-2 Holland-Code -> Typ-Name + Beschreibung + Staerken

TYPE_MAP = {
    "RI": {
        "name": "Der Technische Analyst",
        "description": "Du kombinierst praktisches Geschick mit analytischem Denken. Du willst verstehen wie Dinge funktionieren -- und sie dann besser machen.",
        "strengths": ["Problemloeser", "Technisch versiert", "Analytisch"]
    },
    "RA": {
        "name": "Der Handwerker-Kuenstler",
        "description": "Du erschaffst gerne Dinge mit deinen Haenden -- aber mit einem kreativen Twist. Qualitaet und Aesthetik sind dir wichtig.",
        "strengths": ["Kreativ-praktisch", "Detailverliebt", "Handwerklich"]
    },
    "RS": {
        "name": "Der Praktische Helfer",
        "description": "Du packst gerne an und hilfst dabei anderen. Nicht mit Worten, sondern mit Taten.",
        "strengths": ["Hilfsbereit", "Zupackend", "Verlaesslich"]
    },
    "RE": {
        "name": "Der Macher",
        "description": "Du willst Dinge nicht nur planen -- du willst sie umsetzen. Schnell, pragmatisch, ergebnisorientiert.",
        "strengths": ["Umsetzungsstark", "Pragmatisch", "Fuehrend"]
    },
    "RC": {
        "name": "Der Systematiker",
        "description": "Du liebst Ordnung und Struktur in der praktischen Welt. Prozesse optimieren, Systeme aufbauen, alles an seinem Platz.",
        "strengths": ["Organisiert", "Zuverlaessig", "Strukturiert"]
    },
    "IA": {
        "name": "Der Visionaere Denker",
        "description": "Du verbindest tiefes Nachdenken mit kreativen Ideen. Du siehst Muster wo andere Chaos sehen.",
        "strengths": ["Innovativ", "Tiefgruendig", "Visionaer"]
    },
    "IS": {
        "name": "Der Einfuehlsame Forscher",
        "description": "Du willst Menschen verstehen -- wirklich verstehen. Nicht oberflaechlich, sondern was sie antreibt und bewegt.",
        "strengths": ["Empathisch", "Analytisch", "Einfuehlsam"]
    },
    "IE": {
        "name": "Der Strategische Kopf",
        "description": "Du denkst in Systemen und willst sie nutzen um etwas aufzubauen. Wissen ist fuer dich kein Selbstzweck -- du willst es anwenden.",
        "strengths": ["Strategisch", "Wissbegierig", "Durchsetzungsstark"]
    },
    "IC": {
        "name": "Der Praezise Denker",
        "description": "Genauigkeit und Tiefe sind deine Superkraefte. Du graebst tiefer als andere und sorgst dafuer dass alles stimmt.",
        "strengths": ["Genau", "Gruendlich", "Analytisch"]
    },
    "AS": {
        "name": "Der Kreative Helfer",
        "description": "Du nutzt deine Kreativitaet um anderen zu helfen. Ob durch Kunst, Worte oder Design -- du inspirierst Menschen.",
        "strengths": ["Inspirierend", "Einfuehlsam", "Kreativ"]
    },
    "AE": {
        "name": "Der Kreative Stratege",
        "description": "Du brauchst Gestaltungsfreiheit UND willst etwas bewegen. Routine killt dich -- du willst Neues erschaffen und andere davon ueberzeugen. Du denkst gross und handelst schnell.",
        "strengths": ["Innovativ", "Ueberzeugend", "Ideenreich"]
    },
    "AC": {
        "name": "Der Aesthetische Perfektionist",
        "description": "Fuer dich muss es nicht nur funktionieren -- es muss auch gut aussehen. Du bringst Kreativitaet und Ordnung zusammen.",
        "strengths": ["Perfektionistisch", "Aesthetisch", "Organisiert"]
    },
    "SE": {
        "name": "Der People Leader",
        "description": "Du inspirierst Menschen und bringst sie dazu ihr Bestes zu geben. Du fuehrst nicht durch Druck, sondern durch echtes Interesse an deinem Gegenueber. Beziehungen sind deine Waehrung.",
        "strengths": ["Charismatisch", "Empathisch", "Fuehrungsstark"]
    },
    "SC": {
        "name": "Der Strukturierte Helfer",
        "description": "Du hilfst gerne -- aber mit System. Nicht chaotisch, sondern organisiert und verlaesslich.",
        "strengths": ["Zuverlaessig", "Hilfsbereit", "Organisiert"]
    },
    "EC": {
        "name": "Der Business-Macher",
        "description": "Du willst aufbauen, wachsen, optimieren. Du verbindest Unternehmergeist mit einem Sinn fuer Struktur.",
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
        {"title": "Architekt", "match": 84, "salary": "45.000 - 72.000", "desc": "Entwirf Gebaeude die Menschen inspirieren."},
        {"title": "Tischler / Moebeldesigner", "match": 78, "salary": "32.000 - 52.000", "desc": "Erschaffe einzigartige Moebelstuecke mit deinen Haenden."},
    ],
    "RS": [
        {"title": "Physiotherapeut", "match": 87, "salary": "35.000 - 52.000", "desc": "Hilf Menschen durch gezielte Bewegungstherapie."},
        {"title": "Rettungssanitaeter", "match": 83, "salary": "30.000 - 45.000", "desc": "Sei zur Stelle wenn es drauf ankommt."},
        {"title": "Ergotherapeut", "match": 79, "salary": "33.000 - 48.000", "desc": "Unterstuetze Menschen dabei ihren Alltag zu meistern."},
    ],
    "RE": [
        {"title": "Bauleiter", "match": 89, "salary": "50.000 - 75.000", "desc": "Leite Bauprojekte von der Planung bis zur Fertigstellung."},
        {"title": "Produktionsleiter", "match": 85, "salary": "55.000 - 80.000", "desc": "Steuere Teams und Prozesse in der Fertigung."},
        {"title": "Handwerksmeister", "match": 80, "salary": "40.000 - 65.000", "desc": "Fuehre deinen eigenen Betrieb mit Hands-on-Mentalitaet."},
    ],
    "RC": [
        {"title": "Qualitaetsmanager", "match": 86, "salary": "48.000 - 72.000", "desc": "Stelle sicher dass Standards eingehalten werden."},
        {"title": "Logistikplaner", "match": 82, "salary": "42.000 - 62.000", "desc": "Optimiere Lieferketten und Ablaeufe."},
        {"title": "Technischer Zeichner", "match": 77, "salary": "35.000 - 50.000", "desc": "Erstelle praezise Plaene fuer technische Projekte."},
    ],
    "IA": [
        {"title": "UX Researcher", "match": 89, "salary": "48.000 - 75.000", "desc": "Erforsche wie Menschen Produkte nutzen und verbessere sie."},
        {"title": "Wissenschaftsjournalist", "match": 83, "salary": "38.000 - 58.000", "desc": "Mach komplexe Themen fuer alle verstaendlich."},
        {"title": "Innovationsmanager", "match": 80, "salary": "55.000 - 85.000", "desc": "Entwickle neue Ideen und bring sie zur Marktreife."},
    ],
    "IS": [
        {"title": "Psychologe", "match": 90, "salary": "42.000 - 68.000", "desc": "Verstehe menschliches Verhalten und hilf Menschen zu wachsen."},
        {"title": "Sozialforscher", "match": 84, "salary": "40.000 - 60.000", "desc": "Erforsche gesellschaftliche Zusammenhaenge und Trends."},
        {"title": "Paedagoge", "match": 79, "salary": "38.000 - 55.000", "desc": "Begleite Menschen auf ihrem Bildungsweg."},
    ],
    "IE": [
        {"title": "Unternehmensberater", "match": 90, "salary": "55.000 - 95.000", "desc": "Analysiere Unternehmen und entwickle Strategien."},
        {"title": "Data Scientist", "match": 86, "salary": "52.000 - 82.000", "desc": "Nutze Daten um bessere Entscheidungen zu ermoeglichen."},
        {"title": "Produktmanager", "match": 82, "salary": "55.000 - 85.000", "desc": "Bringe Ideen vom Konzept zur Realitaet."},
    ],
    "IC": [
        {"title": "Wirtschaftspruefer", "match": 88, "salary": "52.000 - 85.000", "desc": "Pruefe Unternehmen auf Herz und Nieren."},
        {"title": "Forschungsingenieur", "match": 84, "salary": "50.000 - 78.000", "desc": "Entwickle neue Technologien mit wissenschaftlicher Praezision."},
        {"title": "Pharmazeut", "match": 79, "salary": "48.000 - 72.000", "desc": "Sorge fuer sichere und wirksame Medikamente."},
    ],
    "AS": [
        {"title": "Therapeut (Kunst/Musik)", "match": 87, "salary": "35.000 - 55.000", "desc": "Nutze Kunst als Werkzeug um Menschen zu helfen."},
        {"title": "Lehrer (Kunst/Musik)", "match": 84, "salary": "42.000 - 62.000", "desc": "Inspiriere junge Menschen durch kreative Faecher."},
        {"title": "Social Media Manager", "match": 78, "salary": "35.000 - 55.000", "desc": "Erzaehle Geschichten die Menschen beruehren und verbinden."},
    ],
    "AE": [
        {"title": "UX Designer", "match": 87, "salary": "45.000 - 72.000", "desc": "Gestalte digitale Produkte die Menschen lieben."},
        {"title": "Produktmanager", "match": 82, "salary": "55.000 - 85.000", "desc": "Bringe Ideen vom Konzept zur Realitaet."},
        {"title": "Startup-Gruender", "match": 74, "salary": "Variabel", "desc": "Baue dein eigenes Ding von Null auf."},
    ],
    "AC": [
        {"title": "Grafikdesigner", "match": 88, "salary": "35.000 - 58.000", "desc": "Gestalte visuelle Kommunikation die begeistert."},
        {"title": "Art Director", "match": 83, "salary": "50.000 - 80.000", "desc": "Leite kreative Teams und definiere den visuellen Stil."},
        {"title": "Webdesigner", "match": 79, "salary": "38.000 - 60.000", "desc": "Baue Websites die gut aussehen und perfekt funktionieren."},
    ],
    "SE": [
        {"title": "Personalmanager (HR)", "match": 89, "salary": "48.000 - 75.000", "desc": "Finde und foerdere die besten Talente."},
        {"title": "Teamleiter", "match": 85, "salary": "50.000 - 78.000", "desc": "Fuehre dein Team zu Hoechstleistungen."},
        {"title": "Trainer / Coach", "match": 80, "salary": "40.000 - 70.000", "desc": "Entwickle Menschen und hilf ihnen zu wachsen."},
    ],
    "SC": [
        {"title": "Verwaltungsfachangestellter", "match": 85, "salary": "35.000 - 52.000", "desc": "Sorge dafuer dass alles seinen geregelten Gang geht."},
        {"title": "Sozialarbeiter", "match": 82, "salary": "36.000 - 52.000", "desc": "Unterstuetze Menschen in schwierigen Lebenslagen -- systematisch."},
        {"title": "Medizinische Fachangestellte", "match": 78, "salary": "30.000 - 42.000", "desc": "Organisiere den Praxisalltag und kuemmere dich um Patienten."},
    ],
    "EC": [
        {"title": "Projektmanager", "match": 90, "salary": "50.000 - 78.000", "desc": "Bringe komplexe Projekte strukturiert ins Ziel."},
        {"title": "Vertriebsleiter", "match": 85, "salary": "55.000 - 90.000", "desc": "Baue Vertriebsteams auf und erreiche ambitionierte Ziele."},
        {"title": "Finanzberater", "match": 80, "salary": "48.000 - 75.000", "desc": "Hilf Menschen und Unternehmen kluge finanzielle Entscheidungen zu treffen."},
    ],
}


# Backwards-compat
QUESTIONS = ITEMS


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
    Pruefe ob das Profil zu flach ist fuer einen klaren Typ.
    Generalist = Chamaeleon wenn:
    - Der hoechste Score unter 3 liegt (kaum positive Tendenz), ODER
    - Die Differenz zwischen Top-1 und Top-3 kleiner als 4 ist (alles aehnlich)
    """
    sorted_vals = sorted(scores.values(), reverse=True)
    top1 = sorted_vals[0]
    top3 = sorted_vals[2]
    
    # Schwellenwerte
    if top1 < 3:
        return True
    if (top1 - top3) < 4:
        return True
    
    return False


def get_top_two(scores: Dict[str, int]) -> str:
    """Ermittle den 2-Buchstaben Holland-Code (Top-2 Dimensionen)."""
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_dims[0][0] + sorted_dims[1][0]


def get_type_info(code: str, generalist: bool = False) -> Dict:
    """Hole Typ-Info fuer einen 2-Buchstaben Code."""
    
    if generalist:
        return {
            "name": "Das Chamaeleon",
            "code": code,
            "description": "Wo andere ein klares Staerken-Profil haben, hast du Range. Du wechselst Rollen, Branchen, Perspektiven -- und nimmst aus jedem Kontext etwas mit. Selten, gefragt, schwer zu fassen.",
            "strengths": ["Vielseitig", "Anpassungsfaehig", "Breit aufgestellt"]
        }
    
    if code in TYPE_MAP:
        return {**TYPE_MAP[code], "code": code}
    
    reversed_code = code[1] + code[0]
    if reversed_code in TYPE_MAP:
        return {**TYPE_MAP[reversed_code], "code": reversed_code}
    
    return {
        "name": "Der Entdecker",
        "code": code,
        "description": "Du hast ein vielseitiges Profil -- das ist eine Staerke! Du passt dich an und findest in vielen Bereichen deinen Weg.",
        "strengths": ["Vielseitig", "Anpassungsfaehig", "Neugierig"]
    }


def get_matching_jobs(code: str) -> List[Dict]:
    """Hole passende Jobs fuer einen Holland-Code."""
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
    scores = calculate_scores(answers)
    code = get_top_two(scores)
    generalist = is_generalist(scores)
    type_info = get_type_info(code, generalist)
    jobs = get_matching_jobs(code)
    
    # Normalisiere Scores auf 0-100 fuer das Hexagon
    # Maximum pro Dimension: 6 Items x 2 Punkte = 12
    max_possible = 12
    min_possible = -12
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
