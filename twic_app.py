"""
TWIC Downloader v2.2
====================
Unofficial automated PGN downloader for The Week In Chess.
Multilingual (FR/EN/ES/DE/IT) + cross-platform (Windows/Mac/Linux).

Modes:
  - GUI (default)         : graphical wizard
  - --background <config> : silent download (scheduled task)
"""

import io
import json
import hashlib
import zipfile
import subprocess
import sys
import os
import threading
import logging
import base64
import platform
from pathlib import Path
from datetime import datetime, date, timedelta

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

try:
    import chess.pgn
    import requests
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


# =====================================================================
# CONSTANTES
# =====================================================================

APP_NAME = "TWIC Downloader"
APP_VERSION = "2.2"
TWIC_URL = "https://theweekinchess.com/zips/twic{num}g.zip"
USER_AGENT = "Mozilla/5.0 (TWIC-Downloader)"
ACCEPT_VARIANTS = {"", "standard", "chess", "from position"}
TWIC_REF_NUM = 920
TWIC_REF_DATE = date(2012, 6, 25)
SYSTEM = platform.system()

KNIGHT_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAxElEQVR4nO2WUQ6EIAxE62YP"
    "U+5/GHob9kvDIqbTQpescf4w0BkfFCV69K9i5jKjzjbDTESgOj29kEmawQgNOHltknM+nqeU"
    "vuZZaUAE6sK1eW9spQEHiNJbm+DZX2Yu6FZcEmDm0jNv97wdW3VKOau/ibADeSIw0tMeqYdQ"
    "RDZPqKEzsC/+BY1LAq15VJiQe8ASFg4wsztcASyyhIUCRL09FMBrjq5b/jEKDYBQuDcBIp3C"
    "/QloCv0f6Km9ppcTeAIs1wfcUkwjyYRrPQAAAABJRU5ErkJggg=="
)


# =====================================================================
# TRANSLATIONS
# =====================================================================

LANGS = {"fr": "Français", "en": "English", "es": "Español", "de": "Deutsch", "it": "Italiano"}

T = {
    # ── General ──
    "app_title": {"fr": "TWIC Downloader", "en": "TWIC Downloader", "es": "TWIC Downloader", "de": "TWIC Downloader", "it": "TWIC Downloader"},
    "next": {"fr": "Suivant >", "en": "Next >", "es": "Siguiente >", "de": "Weiter >", "it": "Avanti >"},
    "back": {"fr": "< Retour", "en": "< Back", "es": "< Atrás", "de": "< Zurück", "it": "< Indietro"},
    "launch": {"fr": "▶  Lancer !", "en": "▶  Start!", "es": "▶  ¡Iniciar!", "de": "▶  Starten!", "it": "▶  Avvia!"},
    "finish": {"fr": "Terminer", "en": "Finish", "es": "Finalizar", "de": "Beenden", "it": "Fine"},

    # ── Page: Language ──
    "lang_title": {"fr": "Choisissez votre langue", "en": "Choose your language", "es": "Elige tu idioma", "de": "Sprache wählen", "it": "Scegli la lingua"},

    # ── Page: Welcome ──
    "welcome_title": {"fr": "Bienvenue dans TWIC Downloader", "en": "Welcome to TWIC Downloader", "es": "Bienvenido a TWIC Downloader", "de": "Willkommen bei TWIC Downloader", "it": "Benvenuto in TWIC Downloader"},
    "welcome_desc": {
        "fr": "Cet outil télécharge automatiquement les parties d'échecs\npubliées chaque semaine par The Week In Chess (TWIC),\nles dédoublonne et les organise par année.\n\nIl peut aussi créer une base filtrée par Elo pour\nconstruire une bibliothèque d'ouvertures de haut niveau.\n\nEnfin, il peut programmer un téléchargement automatique\nchaque semaine pour garder ta collection à jour.",
        "en": "This tool automatically downloads chess games\npublished weekly by The Week In Chess (TWIC),\nremoves duplicates and organizes them by year.\n\nIt can also create an Elo-filtered database\nto build a high-level opening book.\n\nFinally, it can schedule automatic weekly downloads\nto keep your collection up to date.",
        "es": "Esta herramienta descarga automáticamente partidas de ajedrez\npublicadas semanalmente por The Week In Chess (TWIC),\nelimina duplicados y las organiza por año.\n\nTambién puede crear una base filtrada por Elo\npara construir un libro de aperturas de alto nivel.\n\nFinalmente, puede programar descargas automáticas\nsemanales para mantener tu colección actualizada.",
        "de": "Dieses Tool lädt automatisch Schachpartien herunter,\ndie wöchentlich von The Week In Chess (TWIC)\nveröffentlicht werden, entfernt Duplikate\nund organisiert sie nach Jahr.\n\nEs kann auch eine Elo-gefilterte Datenbank erstellen,\num ein hochwertiges Eröffnungsbuch zu erstellen.\n\nSchließlich kann es automatische wöchentliche Downloads\nplanen, um Ihre Sammlung aktuell zu halten.",
        "it": "Questo strumento scarica automaticamente le partite di scacchi\npubblicate settimanalmente da The Week In Chess (TWIC),\nrimuove i duplicati e le organizza per anno.\n\nPuò anche creare un database filtrato per Elo\nper costruire un libro di aperture di alto livello.\n\nInfine, può programmare download settimanali automatici\nper mantenere la tua collezione aggiornata.",
    },
    "welcome_click": {"fr": "Clique sur Suivant pour commencer.", "en": "Click Next to begin.", "es": "Haz clic en Siguiente para comenzar.", "de": "Klicken Sie auf Weiter, um zu beginnen.", "it": "Clicca Avanti per iniziare."},
    "disclaimer": {"fr": "Outil non officiel, sans affiliation avec theweekinchess.com", "en": "Unofficial tool, not affiliated with theweekinchess.com", "es": "Herramienta no oficial, sin afiliación con theweekinchess.com", "de": "Inoffizielles Tool, nicht mit theweekinchess.com verbunden", "it": "Strumento non ufficiale, non affiliato a theweekinchess.com"},
    "personal_use": {"fr": "Usage personnel et éducatif", "en": "Personal and educational use", "es": "Uso personal y educativo", "de": "Persönlicher und pädagogischer Gebrauch", "it": "Uso personale e didattico"},

    # ── Page: Folder ──
    "folder_title": {"fr": "Dossier de destination", "en": "Destination folder", "es": "Carpeta de destino", "de": "Zielordner", "it": "Cartella di destinazione"},
    "folder_structure": {"fr": "Les fichiers seront organisés ainsi :", "en": "Files will be organized like this:", "es": "Los archivos se organizarán así:", "de": "Die Dateien werden so organisiert:", "it": "I file saranno organizzati così:"},
    "folder_label": {"fr": "Dossier :", "en": "Folder:", "es": "Carpeta:", "de": "Ordner:", "it": "Cartella:"},
    "folder_browse": {"fr": "Parcourir...", "en": "Browse...", "es": "Examinar...", "de": "Durchsuchen...", "it": "Sfoglia..."},
    "folder_auto_create": {"fr": "Le dossier sera créé automatiquement s'il n'existe pas.", "en": "The folder will be created automatically if it doesn't exist.", "es": "La carpeta se creará automáticamente si no existe.", "de": "Der Ordner wird automatisch erstellt, falls er nicht existiert.", "it": "La cartella verrà creata automaticamente se non esiste."},
    "folder_required": {"fr": "Choisis un dossier de destination.", "en": "Choose a destination folder.", "es": "Elige una carpeta de destino.", "de": "Wählen Sie einen Zielordner.", "it": "Scegli una cartella di destinazione."},

    # ── Page: Range ──
    "range_title": {"fr": "Période de téléchargement", "en": "Download period", "es": "Período de descarga", "de": "Download-Zeitraum", "it": "Periodo di download"},
    "range_from": {"fr": "À partir d'une date jusqu'au plus récent", "en": "From a date to the most recent", "es": "Desde una fecha hasta la más reciente", "de": "Ab einem Datum bis zum neuesten", "it": "Da una data alla più recente"},
    "range_between": {"fr": "Entre deux dates (plage personnalisée)", "en": "Between two dates (custom range)", "es": "Entre dos fechas (rango personalizado)", "de": "Zwischen zwei Daten (benutzerdefiniert)", "it": "Tra due date (intervallo personalizzato)"},
    "range_start": {"fr": "Début :", "en": "Start:", "es": "Inicio:", "de": "Start:", "it": "Inizio:"},
    "range_end": {"fr": "Fin :", "en": "End:", "es": "Fin:", "de": "Ende:", "it": "Fine:"},
    "range_shortcuts": {"fr": "Raccourcis :", "en": "Shortcuts:", "es": "Atajos:", "de": "Schnellauswahl:", "it": "Scorciatoie:"},
    "range_files": {"fr": "fichiers", "en": "files", "es": "archivos", "de": "Dateien", "it": "file"},
    "range_invalid": {"fr": "Le TWIC de début doit être inférieur ou égal au TWIC de fin.", "en": "Start TWIC must be less than or equal to end TWIC.", "es": "El TWIC de inicio debe ser menor o igual al TWIC de fin.", "de": "Start-TWIC muss kleiner oder gleich End-TWIC sein.", "it": "Il TWIC di inizio deve essere minore o uguale al TWIC di fine."},

    # ── Page: Elite ──
    "elite_title": {"fr": "Base filtrée par Elo (optionnel)", "en": "Elo-filtered database (optional)", "es": "Base filtrada por Elo (opcional)", "de": "Elo-gefilterte Datenbank (optional)", "it": "Database filtrato per Elo (opzionale)"},
    "elite_desc": {"fr": "Tu peux créer un fichier PGN ne contenant que les parties\nde joueurs forts. Idéal pour construire un livre d'ouvertures\ndans ChessBase.", "en": "You can create a PGN file containing only games\nfrom strong players. Ideal for building an opening book\nin ChessBase.", "es": "Puedes crear un archivo PGN que contenga solo partidas\nde jugadores fuertes. Ideal para construir un libro\nde aperturas en ChessBase.", "de": "Sie können eine PGN-Datei erstellen, die nur Partien\nstarker Spieler enthält. Ideal zum Erstellen eines\nEröffnungsbuchs in ChessBase.", "it": "Puoi creare un file PGN contenente solo le partite\ndi giocatori forti. Ideale per costruire un libro\ndi aperture in ChessBase."},
    "elite_enable": {"fr": "Créer une base filtrée par Elo", "en": "Create an Elo-filtered database", "es": "Crear una base filtrada por Elo", "de": "Elo-gefilterte Datenbank erstellen", "it": "Crea un database filtrato per Elo"},
    "elite_elo_label": {"fr": "Elo minimum :", "en": "Minimum Elo:", "es": "Elo mínimo:", "de": "Mindest-Elo:", "it": "Elo minimo:"},
    "elite_criteria": {"fr": "Critère :", "en": "Criteria:", "es": "Criterio:", "de": "Kriterium:", "it": "Criterio:"},
    "elite_at_least_one": {"fr": "Au moins un joueur", "en": "At least one player", "es": "Al menos un jugador", "de": "Mindestens ein Spieler", "it": "Almeno un giocatore"},
    "elite_both": {"fr": "Les deux joueurs", "en": "Both players", "es": "Ambos jugadores", "de": "Beide Spieler", "it": "Entrambi i giocatori"},
    "elo_invalid": {"fr": "L'Elo minimum doit être un nombre entier.", "en": "Minimum Elo must be an integer.", "es": "El Elo mínimo debe ser un número entero.", "de": "Mindest-Elo muss eine ganze Zahl sein.", "it": "L'Elo minimo deve essere un numero intero."},
    "elo_low_title": {"fr": "Elo très bas", "en": "Very low Elo", "es": "Elo muy bajo", "de": "Sehr niedriges Elo", "it": "Elo molto basso"},
    "elo_low_msg": {"fr": "Tu as saisi {elo} Elo.\n\nLe plus bas Elo FIDE est d'environ 1000.\nQuasiment toutes les parties seront retenues.\n\nContinuer quand même ?", "en": "You entered {elo} Elo.\n\nThe lowest FIDE Elo is about 1000.\nAlmost all games will be kept.\n\nContinue anyway?", "es": "Has ingresado {elo} Elo.\n\nEl Elo FIDE más bajo es aproximadamente 1000.\nCasi todas las partidas serán conservadas.\n\n¿Continuar de todos modos?", "de": "Sie haben {elo} Elo eingegeben.\n\nDas niedrigste FIDE-Elo liegt bei etwa 1000.\nFast alle Partien werden beibehalten.\n\nTrotzdem fortfahren?", "it": "Hai inserito {elo} Elo.\n\nL'Elo FIDE più basso è circa 1000.\nQuasi tutte le partite verranno conservate.\n\nContinuare comunque?"},
    "elo_high_title": {"fr": "Elo trop élevé", "en": "Elo too high", "es": "Elo demasiado alto", "de": "Elo zu hoch", "it": "Elo troppo alto"},
    "elo_high_msg": {"fr": "Tu as saisi {elo} Elo.\n\nLe record FIDE est d'environ 2882.\nAucun joueur n'atteint ce seuil.\n\nBaisse la valeur.", "en": "You entered {elo} Elo.\n\nThe FIDE record is about 2882.\nNo player reaches this threshold.\n\nLower the value.", "es": "Has ingresado {elo} Elo.\n\nEl récord FIDE es aproximadamente 2882.\nNingún jugador alcanza este umbral.\n\nReduce el valor.", "de": "Sie haben {elo} Elo eingegeben.\n\nDer FIDE-Rekord liegt bei etwa 2882.\nKein Spieler erreicht diese Schwelle.\n\nReduzieren Sie den Wert.", "it": "Hai inserito {elo} Elo.\n\nIl record FIDE è circa 2882.\nNessun giocatore raggiunge questa soglia.\n\nRiduci il valore."},

    # ── Page: Schedule ──
    "sched_title": {"fr": "Mise à jour automatique", "en": "Automatic updates", "es": "Actualizaciones automáticas", "de": "Automatische Updates", "it": "Aggiornamenti automatici"},
    "sched_desc": {"fr": "TWIC publie un nouveau fichier chaque lundi.\nLe programme peut planifier un téléchargement\nautomatique chaque semaine.", "en": "TWIC publishes a new file every Monday.\nThe program can schedule an automatic\ndownload every week.", "es": "TWIC publica un archivo nuevo cada lunes.\nEl programa puede programar una descarga\nautomática cada semana.", "de": "TWIC veröffentlicht jeden Montag eine neue Datei.\nDas Programm kann einen automatischen\nwöchentlichen Download planen.", "it": "TWIC pubblica un nuovo file ogni lunedì.\nIl programma può pianificare un download\nautomatico ogni settimana."},
    "sched_enable": {"fr": "Activer le téléchargement hebdomadaire", "en": "Enable weekly download", "es": "Activar descarga semanal", "de": "Wöchentlichen Download aktivieren", "it": "Attiva download settimanale"},
    "sched_day": {"fr": "Jour :", "en": "Day:", "es": "Día:", "de": "Tag:", "it": "Giorno:"},
    "sched_hour": {"fr": "Heure :", "en": "Hour:", "es": "Hora:", "de": "Uhrzeit:", "it": "Ora:"},
    "summary": {"fr": "Résumé", "en": "Summary", "es": "Resumen", "de": "Zusammenfassung", "it": "Riepilogo"},

    # ── Page: Progress ──
    "progress_title": {"fr": "Téléchargement en cours...", "en": "Downloading...", "es": "Descargando...", "de": "Wird heruntergeladen...", "it": "Download in corso..."},
    "progress_init": {"fr": "Initialisation...", "en": "Initializing...", "es": "Inicializando...", "de": "Initialisierung...", "it": "Inizializzazione..."},
    "progress_games": {"fr": "Parties traitées :", "en": "Games processed:", "es": "Partidas procesadas:", "de": "Bearbeitete Partien:", "it": "Partite elaborate:"},
    "progress_done": {"fr": "Téléchargement terminé — dernier :", "en": "Download complete — last:", "es": "Descarga completa — último:", "de": "Download abgeschlossen — letzter:", "it": "Download completato — ultimo:"},
    "all_done": {"fr": "✅ Tout est terminé !", "en": "✅ All done!", "es": "✅ ¡Todo terminado!", "de": "✅ Alles fertig!", "it": "✅ Tutto completato!"},
    "ctg_instructions": {"fr": "Pour le livre d'ouvertures .ctg :", "en": "For the .ctg opening book:", "es": "Para el libro de aperturas .ctg:", "de": "Für das Eröffnungsbuch .ctg:", "it": "Per il libro di aperture .ctg:"},

    # ── Days ──
    "monday": {"fr": "Lundi", "en": "Monday", "es": "Lunes", "de": "Montag", "it": "Lunedì"},
    "tuesday": {"fr": "Mardi", "en": "Tuesday", "es": "Martes", "de": "Dienstag", "it": "Martedì"},
    "wednesday": {"fr": "Mercredi", "en": "Wednesday", "es": "Miércoles", "de": "Mittwoch", "it": "Mercoledì"},
    "thursday": {"fr": "Jeudi", "en": "Thursday", "es": "Jueves", "de": "Donnerstag", "it": "Giovedì"},
    "friday": {"fr": "Vendredi", "en": "Friday", "es": "Viernes", "de": "Freitag", "it": "Venerdì"},
    "saturday": {"fr": "Samedi", "en": "Saturday", "es": "Sábado", "de": "Samstag", "it": "Sabato"},
    "sunday": {"fr": "Dimanche", "en": "Sunday", "es": "Domingo", "de": "Sonntag", "it": "Domenica"},
}

DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


# ── Current language (set by wizard) ──

_LANG = "fr"


def t(key, **kw):
    s = T.get(key, {}).get(_LANG, key)
    if kw:
        s = s.format(**kw)
    return s


def set_lang(lang):
    global _LANG
    _LANG = lang


def day_names():
    return [t(k) for k in DAY_KEYS]


def day_code_from_index(i):
    return DAY_CODES[i]


# =====================================================================
# HELPERS
# =====================================================================

def twic_date(num):
    return TWIC_REF_DATE + timedelta(days=(num - TWIC_REF_NUM) * 7)


def twic_year(num):
    return twic_date(num).year


def first_twic_of_year(year):
    n = TWIC_REF_NUM + int((date(year, 1, 1) - TWIC_REF_DATE).days / 7)
    while twic_date(n).year < year:
        n += 1
    return n


def latest_possible_twic():
    return TWIC_REF_NUM + (date.today() - TWIC_REF_DATE).days // 7


def estimate_duration(count):
    seconds = count * 15
    if seconds < 60:
        return "~<1 min"
    elif seconds < 3600:
        m = seconds // 60
        return f"~{m} min"
    else:
        h = seconds / 3600
        if h < 2:
            return f"~{int(h)}h{int((h % 1) * 60):02d}"
        else:
            return f"~{h:.0f}h"


# =====================================================================
# ENGINE
# =====================================================================

class TWICEngine:

    def __init__(self, root_dir, start_twic=1313, end_twic=None,
                 elo_min=0, require_both=False, callback=None):
        self.root_dir = Path(root_dir)
        self.start_twic = start_twic
        self.end_twic = end_twic
        self.elo_min = elo_min
        self.require_both = require_both
        self.cb = callback or (lambda *a: None)
        self.cancelled = False
        self.actual_last = start_twic - 1

    def cancel(self):
        self.cancelled = True

    # ── Paths ──

    def year_dir(self, y):
        d = self.root_dir / f"TWIC {y}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "weekly_clean").mkdir(exist_ok=True)
        (d / "raw_downloads").mkdir(exist_ok=True)
        return d

    def state_file(self):
        return self.root_dir / "twic_state.json"

    def hashes_file(self, y):
        return self.year_dir(y) / "seen_hashes.txt"

    def annual_pgn(self, y):
        return self.year_dir(y) / f"TWIC_{y}_cumulative.pgn"

    def weekly_pgn(self, y, n):
        return self.year_dir(y) / "weekly_clean" / f"twic{n}_clean.pgn"

    def raw_zip(self, y, n):
        return self.year_dir(y) / "raw_downloads" / f"twic{n}g.zip"

    def config_file(self):
        return self.root_dir / "twic_config.json"

    # ── State management ──

    def load_state(self):
        sf = self.state_file()
        if sf.exists():
            return json.loads(sf.read_text(encoding="utf-8"))
        return {"last_twic": self.start_twic - 1}

    def save_state(self, state):
        tmp = self.state_file().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self.state_file())

    def load_hashes(self, y):
        f = self.hashes_file(y)
        if f.exists():
            return set(f.read_text(encoding="utf-8").splitlines())
        return set()

    def save_hashes(self, y, h):
        f = self.hashes_file(y)
        tmp = f.with_suffix(".txt.tmp")
        tmp.write_text("\n".join(sorted(h)), encoding="utf-8")
        tmp.replace(f)

    def save_config(self):
        cfg = {
            "root_dir": str(self.root_dir),
            "start_twic": self.start_twic,
            "elo_min": self.elo_min,
            "require_both": self.require_both,
            "lang": _LANG,
        }
        cf = self.config_file()
        tmp = cf.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        tmp.replace(cf)

    # ── PGN processing ──

    def extract_pgn(self, zip_bytes):
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            name = next((x for x in z.namelist() if x.lower().endswith(".pgn")), None)
            if not name:
                raise ValueError("No PGN")
            return z.read(name).decode("utf-8", errors="replace")

    def detect_year(self, pgn_text):
        pgn_io = io.StringIO(pgn_text)
        counts = {}
        for _ in range(100):
            g = chess.pgn.read_game(pgn_io)
            if g is None:
                break
            d = g.headers.get("Date", "")
            if len(d) >= 4:
                try:
                    y = int(d[:4])
                    if 1990 <= y <= 2100:
                        counts[y] = counts.get(y, 0) + 1
                except ValueError:
                    pass
        if counts:
            return max(counts, key=counts.get)
        return datetime.now().year

    def game_hash(self, game):
        h = game.headers
        parts = [
            h.get("White", ""), h.get("Black", ""), h.get("Date", ""),
            h.get("Event", ""), h.get("Round", ""),
            " ".join(m.uci() for m in game.mainline_moves()),
        ]
        return hashlib.sha1("|".join(parts).encode()).hexdigest()

    def dedupe(self, pgn_text, seen):
        pgn_io = io.StringIO(pgn_text)
        clean = []
        new_hashes = set()
        n_new = 0
        n_dup = 0

        while True:
            try:
                g = chess.pgn.read_game(pgn_io)
            except Exception:
                continue
            if g is None:
                break

            variant = g.headers.get("Variant", "").strip().lower()
            if variant not in ACCEPT_VARIANTS:
                continue

            gh = self.game_hash(g)
            if gh in seen or gh in new_hashes:
                n_dup += 1
                continue

            new_hashes.add(gh)
            n_new += 1
            try:
                clean.append(str(g))
            except (ValueError, KeyError):
                pass

        return "\n\n".join(clean) + "\n", n_new, n_dup, new_hashes

    def write_atomic(self, path, content):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)

    def append_atomic(self, path, content):
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        self.write_atomic(path, existing + content)

    # ── Download one TWIC ──

    def process_one(self, num):
        self.cb("log", f"TWIC {num}...")

        try:
            r = requests.get(
                TWIC_URL.format(num=num),
                headers={"User-Agent": USER_AGENT},
                timeout=60,
            )
        except requests.RequestException as e:
            self.cb("log", f"  Network: {e}")
            return False

        if r.status_code == 404:
            self.cb("log", f"  404")
            return False
        if r.status_code != 200:
            self.cb("log", f"  HTTP {r.status_code}")
            return False

        try:
            pgn_text = self.extract_pgn(r.content)
        except Exception as e:
            self.cb("log", f"  Error: {e}")
            return False

        year = self.detect_year(pgn_text)
        self.cb("log", f"  → {year}")

        self.year_dir(year)
        self.raw_zip(year, num).write_bytes(r.content)

        seen = self.load_hashes(year)
        clean_pgn, n_new, n_dup, new_hashes = self.dedupe(pgn_text, seen)
        self.cb("log", f"  +{n_new} new, -{n_dup} dup")
        self.cb("games", n_new)

        if n_new > 0:
            self.write_atomic(self.weekly_pgn(year, num), clean_pgn)
            self.append_atomic(self.annual_pgn(year), clean_pgn)

        seen |= new_hashes
        self.save_hashes(year, seen)
        return True

    # ── Download loop ──

    def run_download(self):
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.save_config()

        state = self.load_state()
        num = max(state["last_twic"] + 1, self.start_twic)
        misses = 0

        while not self.cancelled:
            if self.end_twic is not None and num > self.end_twic:
                break
            if self.end_twic is None and misses >= 3:
                break

            ok = self.process_one(num)
            if ok:
                self.actual_last = num
                state["last_twic"] = num
                self.save_state(state)
                misses = 0
            else:
                misses += 1

            self.cb("progress", num)
            num += 1

        self.cb("done", self.actual_last)

    # ── Elo filter ──

    def run_filter(self):
        if self.elo_min <= 0:
            self.cb("filter_done", None)
            return

        self.cb("log", f"\nElo >= {self.elo_min}...")
        output = self.root_dir / f"TWIC_elite_{self.elo_min}+.pgn"
        pgns = sorted(self.root_dir.glob("TWIC */TWIC_*_cumulative.pgn"))

        if not pgns:
            self.cb("filter_done", None)
            return

        total_kept = 0

        with open(output, "w", encoding="utf-8") as out:
            for p in pgns:
                if self.cancelled:
                    break

                self.cb("log", f"  {p.parent.name}")
                n_kept = 0

                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    while True:
                        try:
                            g = chess.pgn.read_game(f)
                        except Exception:
                            continue
                        if g is None:
                            break

                        variant = g.headers.get("Variant", "").strip().lower()
                        if variant not in ACCEPT_VARIANTS:
                            continue

                        try:
                            white_elo = int(g.headers.get("WhiteElo", "0"))
                            black_elo = int(g.headers.get("BlackElo", "0"))
                        except ValueError:
                            continue

                        if self.require_both:
                            ok = white_elo >= self.elo_min and black_elo >= self.elo_min
                        else:
                            ok = white_elo >= self.elo_min or black_elo >= self.elo_min

                        if not ok:
                            continue

                        try:
                            out.write(str(g))
                            out.write("\n\n")
                            n_kept += 1
                        except (ValueError, KeyError):
                            pass

                out.flush()
                self.cb("log", f"    → {n_kept}")
                total_kept += n_kept

        size_mb = output.stat().st_size / 1024 / 1024
        self.cb("log", f"\n{output.name} ({size_mb:.1f} Mo, {total_kept})")
        self.cb("filter_done", str(output))

    # ── Scheduled task (cross-platform) ──

    def create_schedule(self, day="WED", hour="12:00"):
        exe = sys.executable
        cfg = str(self.config_file())
        self.cb("log", f"\nScheduled task...")

        if SYSTEM == "Windows":
            cmds = [
                f'schtasks /Delete /TN "TWIC Auto Downloader" /F 2>nul',
                f'schtasks /Create /TN "TWIC Auto Downloader" '
                f'/TR "\"{exe}\" --background \"{cfg}\"" '
                f'/SC WEEKLY /D {day} /ST {hour} /RL LIMITED /F',
            ]
            for c in cmds:
                subprocess.run(c, shell=True, capture_output=True)

        elif SYSTEM == "Darwin":
            h, m = hour.split(":")
            day_map = {"MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6, "SUN": 7}
            plist = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0"><dict>\n'
                '<key>Label</key><string>com.twic.downloader</string>\n'
                '<key>ProgramArguments</key><array>\n'
                f'<string>{exe}</string><string>--background</string><string>{cfg}</string>\n'
                '</array>\n'
                '<key>StartCalendarInterval</key><dict>\n'
                f'<key>Weekday</key><integer>{day_map.get(day, 3)}</integer>\n'
                f'<key>Hour</key><integer>{int(h)}</integer>\n'
                f'<key>Minute</key><integer>{int(m)}</integer>\n'
                '</dict></dict></plist>'
            )
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.twic.downloader.plist"
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(plist, encoding="utf-8")
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
            subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)

        else:
            h, m = hour.split(":")
            day_map = {"MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6, "SUN": 0}
            cron_line = f'{m} {h} * * {day_map.get(day, 3)} "{exe}" --background "{cfg}"'
            marker = "# TWIC-AUTO-DOWNLOADER"
            try:
                existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            except Exception:
                existing = ""
            lines = [l for l in existing.splitlines() if marker not in l]
            lines.append(f"{cron_line}  {marker}")
            subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, capture_output=True)

        self.cb("log", f"  OK ({SYSTEM}: {day} {hour})")


# =====================================================================
# GUI WIZARD
# =====================================================================

class WizardApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("650x540")
        self.root.resizable(False, False)

        try:
            icon_data = base64.b64decode(KNIGHT_ICON_B64)
            self.icon_img = tk.PhotoImage(data=base64.b64encode(icon_data))
            self.root.iconphoto(True, self.icon_img)
        except Exception:
            pass

        # Variables
        self.target_dir = tk.StringVar(value=self._guess_dir())
        self.start_twic = tk.IntVar(value=first_twic_of_year(2020))
        self.end_twic = tk.IntVar(value=latest_possible_twic())
        self.range_mode = tk.StringVar(value="from")
        self.enable_elite = tk.BooleanVar(value=False)
        self.elo_min = tk.StringVar(value="2250")
        self.require_both = tk.BooleanVar(value=False)
        self.enable_schedule = tk.BooleanVar(value=True)
        self.schedule_day_idx = tk.IntVar(value=2)
        self.schedule_hour = tk.StringVar(value="12:00")

        # Layout
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=30, pady=10)

        sep = ttk.Separator(self.root, orient="horizontal")
        sep.pack(fill="x", padx=20)

        self.nav = tk.Frame(self.root)
        self.nav.pack(fill="x", padx=30, pady=10)

        self.btn_back = tk.Button(self.nav, text="", width=10, command=self.prev_page)
        self.btn_back.pack(side="left")

        self.btn_next = tk.Button(self.nav, text="", width=10, command=self.next_page)
        self.btn_next.pack(side="right")

        # Pages
        self.pages = [
            self._page_lang, self._page_welcome, self._page_folder,
            self._page_range, self._page_elite, self._page_schedule,
            self._page_progress,
        ]
        self.page_idx = 0
        self.engine = None
        self.total_games = 0
        self._show_page(0)

    def _guess_dir(self):
        for base in [Path.home() / "Documents", Path.home() / "OneDrive" / "Documents"]:
            d = base / "ChessBase" / "Bases"
            if d.exists():
                return str(d / "The Week In Chess (TWIC)")
        return str(Path.home() / "Documents" / "TWIC")

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _update_nav(self):
        idx = self.page_idx
        self.btn_back.config(text=t("back"), state="normal" if 1 < idx < 6 else "disabled")

        if idx == 0:
            self.btn_back.config(state="disabled")
            self.btn_next.config(text=t("next"), state="normal")
        elif idx < 5:
            self.btn_next.config(text=t("next"), state="normal", command=self.next_page)
        elif idx == 5:
            self.btn_next.config(text=t("launch"), state="normal", command=self.next_page)
        else:
            self.btn_next.config(state="disabled")
            self.btn_back.config(state="disabled")

    def _show_page(self, idx):
        self.page_idx = idx
        self._clear()
        self.pages[idx]()
        self._update_nav()

    # ── Navigation ──

    def next_page(self):
        if self.page_idx == 2:
            if not self.target_dir.get().strip():
                messagebox.showwarning("", t("folder_required"))
                return

        if self.page_idx == 3 and self.range_mode.get() == "between":
            if self.start_twic.get() > self.end_twic.get():
                messagebox.showwarning("", t("range_invalid"))
                return

        if self.page_idx == 4 and self.enable_elite.get():
            try:
                elo = int(self.elo_min.get())
            except ValueError:
                messagebox.showwarning("", t("elo_invalid"))
                return
            if elo < 1000:
                if not messagebox.askyesno(t("elo_low_title"), t("elo_low_msg", elo=elo)):
                    return
            elif elo > 2900:
                messagebox.showwarning(t("elo_high_title"), t("elo_high_msg", elo=elo))
                return

        if self.page_idx == 5:
            self._show_page(6)
            self.root.update()
            self._start_engine()
            return

        if self.page_idx < len(self.pages) - 1:
            self._show_page(self.page_idx + 1)

    def prev_page(self):
        if self.page_idx > 1:
            self._show_page(self.page_idx - 1)

    # ── PAGE 0: Language ──

    def _page_lang(self):
        f = self.container
        tk.Label(f, text="🌐", font=("Segoe UI", 32)).pack(pady=(30, 10), anchor="center")
        tk.Label(f, text="Choose your language / Choisissez votre langue",
                 font=("Segoe UI", 12)).pack(anchor="center", pady=(0, 20))
        for code, name in LANGS.items():
            tk.Button(f, text=name, width=20, font=("Segoe UI", 11),
                      command=lambda c=code: self._select_lang(c)).pack(pady=3, anchor="center")

    def _select_lang(self, code):
        set_lang(code)
        self._show_page(1)

    # ── PAGE 1: Welcome ──

    def _page_welcome(self):
        f = self.container
        tk.Label(f, text=t("welcome_title"), font=("Segoe UI", 16, "bold")).pack(pady=(20, 15), anchor="center")
        tk.Label(f, text=t("welcome_desc"), font=("Segoe UI", 11), justify="center").pack(pady=10, anchor="center")
        tk.Label(f, text=t("welcome_click"), font=("Segoe UI", 10, "italic")).pack(pady=(15, 5), anchor="center")
        tk.Label(f, text="─" * 55, font=("Segoe UI", 8), fg="gray").pack(pady=(15, 0))
        tk.Label(f, text=t("disclaimer"), font=("Segoe UI", 8, "italic"), fg="gray").pack(anchor="center")
        tk.Label(f, text=f"v{APP_VERSION} — {t('personal_use')}", font=("Segoe UI", 8, "italic"), fg="gray").pack(anchor="center")

    # ── PAGE 2: Folder ──

    def _page_folder(self):
        f = self.container
        tk.Label(f, text=t("folder_title"), font=("Segoe UI", 14, "bold")).pack(pady=(20, 15), anchor="center")
        tk.Label(f, text=t("folder_structure"), font=("Segoe UI", 10)).pack(anchor="center")

        tree = "  📁 TWIC\\\n  ├── 📁 TWIC 2020\\\n  ├── ...\n  ├── 📁 TWIC 2026\\\n  └── 📄 TWIC_elite_XXXX+.pgn"
        tk.Label(f, text=tree, font=("Consolas", 9), justify="left").pack(pady=10, anchor="center")

        row = tk.Frame(f)
        row.pack(pady=15, anchor="center")
        tk.Label(row, text=t("folder_label"), font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(row, textvariable=self.target_dir, font=("Segoe UI", 9), width=42).pack(side="left", padx=5)
        tk.Button(row, text=t("folder_browse"), command=self._browse).pack(side="left")

        tk.Label(f, text=t("folder_auto_create"), font=("Segoe UI", 9, "italic"), fg="gray").pack(pady=5, anchor="center")

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.target_dir.set(d)

    # ── PAGE 3: Range ──

    def _page_range(self):
        f = self.container
        tk.Label(f, text=t("range_title"), font=("Segoe UI", 14, "bold")).pack(pady=(10, 8), anchor="center")

        mode_frame = tk.Frame(f)
        mode_frame.pack(anchor="center", pady=5)
        tk.Radiobutton(mode_frame, text=t("range_from"), variable=self.range_mode, value="from",
                       font=("Segoe UI", 10), command=self._update_range_ui).pack(anchor="w")
        tk.Radiobutton(mode_frame, text=t("range_between"), variable=self.range_mode, value="between",
                       font=("Segoe UI", 10), command=self._update_range_ui).pack(anchor="w")

        tk.Label(f, text=t("range_start"), font=("Segoe UI", 9, "bold")).pack(pady=(8, 0), anchor="center")
        self.lbl_start = tk.Label(f, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_start.pack(anchor="center")

        max_twic = latest_possible_twic()
        self.slider_start = tk.Scale(f, from_=920, to=max_twic, orient="horizontal",
                                     variable=self.start_twic, length=550, showvalue=False,
                                     command=self._update_range_labels)
        self.slider_start.pack(anchor="center")

        self.lbl_end_title = tk.Label(f, text=t("range_end"), font=("Segoe UI", 9, "bold"))
        self.lbl_end_title.pack(pady=(5, 0), anchor="center")
        self.lbl_end = tk.Label(f, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_end.pack(anchor="center")
        self.slider_end = tk.Scale(f, from_=920, to=max_twic, orient="horizontal",
                                   variable=self.end_twic, length=550, showvalue=False,
                                   command=self._update_range_labels)
        self.slider_end.pack(anchor="center")

        tk.Label(f, text=t("range_shortcuts"), font=("Segoe UI", 9)).pack(pady=(5, 2), anchor="center")

        current_year = date.today().year
        years = list(range(2012, current_year + 1))
        mid = (len(years) + 1) // 2

        for row_years in [years[:mid], years[mid:]]:
            row = tk.Frame(f)
            row.pack(anchor="center", pady=1)
            for y in row_years:
                n = first_twic_of_year(y)
                tk.Button(row, text=str(y), width=5, font=("Segoe UI", 8),
                          command=lambda v=n: self.start_twic.set(v)).pack(side="left", padx=2)

        self.lbl_estimate = tk.Label(f, text="", font=("Segoe UI", 9, "italic"), fg="gray")
        self.lbl_estimate.pack(pady=(5, 0), anchor="center")

        self._update_range_ui()

    def _update_range_ui(self):
        if self.range_mode.get() == "between":
            self.slider_start.pack_forget()
            self.lbl_end_title.pack_forget()
            self.lbl_end.pack_forget()
            self.slider_end.pack_forget()
            self.lbl_estimate.pack_forget()
            self.slider_start.pack(anchor="center")
            self.lbl_end_title.pack(pady=(5, 0), anchor="center")
            self.lbl_end.pack(anchor="center")
            self.slider_end.pack(anchor="center")
            self.lbl_estimate.pack(pady=(5, 0), anchor="center")
        else:
            self.lbl_end_title.pack_forget()
            self.lbl_end.pack_forget()
            self.slider_end.pack_forget()
            self.end_twic.set(latest_possible_twic())

        self._update_range_labels(None)

    def _update_range_labels(self, _):
        s = self.start_twic.get()
        ds = twic_date(s)
        self.lbl_start.config(text=f"TWIC n°{s}  —  {ds.strftime('%d/%m/%Y')}")

        if self.range_mode.get() == "between":
            e = self.end_twic.get()
            de = twic_date(e)
            self.lbl_end.config(text=f"TWIC n°{e}  —  {de.strftime('%d/%m/%Y')}")
            count = max(0, e - s + 1)
        else:
            count = latest_possible_twic() - s + 1

        dur = estimate_duration(count)
        self.lbl_estimate.config(text=f"≈ {count} {t('range_files')} — {dur}")

    # ── PAGE 4: Elite ──

    def _page_elite(self):
        f = self.container
        tk.Label(f, text=t("elite_title"), font=("Segoe UI", 14, "bold")).pack(pady=(20, 10), anchor="center")
        tk.Label(f, text=t("elite_desc"), font=("Segoe UI", 10), justify="center").pack(anchor="center")

        tk.Checkbutton(f, text=t("elite_enable"), variable=self.enable_elite,
                       font=("Segoe UI", 11), command=self._toggle_elite).pack(pady=(15, 10), anchor="center")

        self.elite_frame = tk.Frame(f)
        self.elite_frame.pack(anchor="center")

        row1 = tk.Frame(self.elite_frame)
        row1.pack(pady=5, anchor="center")
        tk.Label(row1, text=t("elite_elo_label"), font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(row1, textvariable=self.elo_min, width=6, font=("Segoe UI", 10), justify="center").pack(side="left", padx=5)
        tk.Label(row1, text="(FIDE: 1000–2882)", font=("Segoe UI", 8, "italic"), fg="gray").pack(side="left", padx=5)

        row2 = tk.Frame(self.elite_frame)
        row2.pack(pady=5, anchor="center")
        tk.Label(row2, text=t("elite_criteria"), font=("Segoe UI", 10)).pack(side="left")
        tk.Radiobutton(row2, text=t("elite_at_least_one"), variable=self.require_both,
                       value=False, font=("Segoe UI", 10)).pack(side="left", padx=8)
        tk.Radiobutton(row2, text=t("elite_both"), variable=self.require_both,
                       value=True, font=("Segoe UI", 10)).pack(side="left", padx=8)

        self._toggle_elite()

    def _toggle_elite(self):
        state = "normal" if self.enable_elite.get() else "disabled"
        for w in self.elite_frame.winfo_children():
            for child in w.winfo_children():
                try:
                    child.config(state=state)
                except tk.TclError:
                    pass

    # ── PAGE 5: Schedule ──

    def _page_schedule(self):
        f = self.container
        tk.Label(f, text=t("sched_title"), font=("Segoe UI", 14, "bold")).pack(pady=(20, 10), anchor="center")
        tk.Label(f, text=t("sched_desc"), font=("Segoe UI", 10), justify="center").pack(anchor="center")

        tk.Checkbutton(f, text=t("sched_enable"), variable=self.enable_schedule,
                       font=("Segoe UI", 11), command=self._toggle_sched).pack(pady=(15, 10), anchor="center")

        self.sched_frame = tk.Frame(f)
        self.sched_frame.pack(anchor="center")

        row = tk.Frame(self.sched_frame)
        row.pack(anchor="center", pady=5)
        tk.Label(row, text=t("sched_day"), font=("Segoe UI", 10)).pack(side="left")
        self.day_combo = ttk.Combobox(row, width=12, values=day_names(), state="readonly")
        self.day_combo.current(self.schedule_day_idx.get())
        self.day_combo.pack(side="left", padx=5)
        tk.Label(row, text=t("sched_hour"), font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))
        ttk.Combobox(row, textvariable=self.schedule_hour, width=6,
                     values=["06:00", "08:00", "10:00", "12:00", "14:00", "18:00", "20:00"],
                     state="readonly").pack(side="left", padx=5)

        self._toggle_sched()

        tk.Label(f, text="─" * 55, font=("Segoe UI", 8), fg="gray").pack(pady=(25, 5))
        tk.Label(f, text=t("summary"), font=("Segoe UI", 12, "bold")).pack(anchor="center")

        self.lbl_summary = tk.Label(f, text="", font=("Segoe UI", 9), justify="center")
        self.lbl_summary.pack(anchor="center", pady=5)

        self._update_summary()

    def _toggle_sched(self):
        state = "normal" if self.enable_schedule.get() else "disabled"
        for w in self.sched_frame.winfo_children():
            for child in w.winfo_children():
                try:
                    child.config(state=state)
                except tk.TclError:
                    pass
        self._update_summary()

    def _update_summary(self):
        s = self.start_twic.get()
        ds = twic_date(s)
        lines = [f"📁  {self.target_dir.get()}"]

        if self.range_mode.get() == "between":
            e = self.end_twic.get()
            de = twic_date(e)
            lines.append(f"📥  TWIC {s} ({ds.strftime('%d/%m/%Y')}) → {e} ({de.strftime('%d/%m/%Y')})")
        else:
            lines.append(f"📥  TWIC {s} ({ds.strftime('%d/%m/%Y')}) → latest")

        if self.enable_elite.get():
            mode = t("elite_both") if self.require_both.get() else t("elite_at_least_one")
            lines.append(f"⭐  Elo ≥ {self.elo_min.get()} ({mode})")

        if self.enable_schedule.get():
            di = self.day_combo.current()
            day_name = day_names()[di] if di >= 0 else "?"
            lines.append(f"🔄  {day_name} {self.schedule_hour.get()}")

        self.lbl_summary.config(text="\n".join(lines))

    # ── PAGE 6: Progress ──

    def _page_progress(self):
        f = self.container
        tk.Label(f, text=t("progress_title"), font=("Segoe UI", 14, "bold")).pack(pady=(10, 5), anchor="center")

        self.progress = ttk.Progressbar(f, length=570, mode="determinate")
        self.progress.pack(pady=5, anchor="center")

        self.lbl_status = tk.Label(f, text=t("progress_init"), font=("Segoe UI", 10))
        self.lbl_status.pack(anchor="center")

        self.lbl_games = tk.Label(f, text=f"{t('progress_games')} 0", font=("Segoe UI", 9))
        self.lbl_games.pack(anchor="center")

        self.log_text = tk.Text(f, height=12, font=("Consolas", 9), state="disabled",
                                bg="#1e1e1e", fg="#d4d4d4", wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=5)

    def _log(self, msg):
        if not hasattr(self, "log_text"):
            return
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ── Engine ──

    def _start_engine(self):
        start = self.start_twic.get()
        end = self.end_twic.get() if self.range_mode.get() == "between" else None
        target_end = end if end else latest_possible_twic()

        self.progress["maximum"] = max(1, target_end - start + 1)
        self.progress["value"] = 0
        self.total_games = 0

        elo = 0
        if self.enable_elite.get():
            try:
                elo = int(self.elo_min.get())
            except ValueError:
                elo = 0

        self.engine = TWICEngine(
            root_dir=self.target_dir.get(),
            start_twic=start,
            end_twic=end,
            elo_min=elo,
            require_both=self.require_both.get(),
            callback=lambda e, d: self.root.after(0, self._on_event, e, d),
        )

        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def _run_pipeline(self):
        self.engine.run_download()

        if self.engine.elo_min > 0 and not self.engine.cancelled:
            self.engine.run_filter()

        if self.enable_schedule.get() and not self.engine.cancelled:
            di = self.day_combo.current()
            dc = day_code_from_index(di) if di >= 0 else "WED"
            self.engine.create_schedule(day=dc, hour=self.schedule_hour.get())

        if not self.engine.cancelled:
            self.engine.cb("all_done", None)

    def _on_event(self, evt, data):
        if evt == "log":
            self._log(str(data))

        elif evt == "progress":
            val = data - self.engine.start_twic + 1
            self.progress["value"] = min(val, self.progress["maximum"])
            self.lbl_status.config(text=f"TWIC n°{data}")

        elif evt == "games":
            self.total_games += data
            self.lbl_games.config(text=f"{t('progress_games')} {self.total_games:,}")

        elif evt == "done":
            self.progress["value"] = self.progress["maximum"]
            self.lbl_status.config(text=f"{t('progress_done')} TWIC {data}")
            if self.engine.elo_min <= 0 and not self.enable_schedule.get():
                self._finish()

        elif evt == "filter_done":
            if not self.enable_schedule.get():
                self._finish()

        elif evt == "all_done":
            self._finish()

    def _finish(self):
        self.progress["value"] = self.progress["maximum"]
        self.btn_next.config(text=t("finish"), state="normal", command=self.root.destroy)

        self._log(f"\n{t('all_done')}")
        self._log(f"📁 {self.target_dir.get()}")

        if self.engine.elo_min > 0:
            self._log(f"⭐ TWIC_elite_{self.engine.elo_min}+.pgn")

        if self.enable_schedule.get():
            di = self.day_combo.current()
            day_name = day_names()[di] if di >= 0 else "?"
            self._log(f"🔄 {day_name} {self.schedule_hour.get()}")

        self._log(f"\n{t('ctg_instructions')}")
        self._log("1. ChessBase → .cbh")
        self._log("2. Ctrl+A → .ctg")

    def run(self):
        self.root.mainloop()


# =====================================================================
# BACKGROUND MODE
# =====================================================================

def run_background(config_path):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))

    if "lang" in cfg:
        set_lang(cfg["lang"])

    engine = TWICEngine(
        root_dir=cfg["root_dir"],
        start_twic=cfg.get("start_twic", 920),
        elo_min=cfg.get("elo_min", 0),
        require_both=cfg.get("require_both", False),
        callback=lambda ev, d: logging.info(f"{d}") if ev == "log" else None,
    )

    engine.run_download()

    if cfg.get("elo_min", 0) > 0:
        engine.run_filter()


# =====================================================================
# MAIN
# =====================================================================

def main():
    if "--background" in sys.argv:
        idx = sys.argv.index("--background")
        if idx + 1 < len(sys.argv):
            run_background(sys.argv[idx + 1])
        return

    if not HAS_TK:
        print("tkinter unavailable")
        sys.exit(1)

    if not HAS_DEPS:
        if HAS_TK:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("", "pip install requests python-chess")
            root.destroy()
        sys.exit(1)

    WizardApp().run()


if __name__ == "__main__":
    main()
