#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

# Import de la structure orientée objets propre
from models import Grid, Header, Bar, ChordInternal
from musicalGlyphes import (
    MARKER_ITEMS, JUMP_ITEMS, 
    MG_TO_CODA, MG_CODA, MG_GOTO_SIGNO, 
    MG_GENERIC_MARKER, MG_GENERIC_JUMP
)
from chordGenerator import chordW3CtoGridChord

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
CONFIG_FILE_PATH = BASE_DIR / ".grid_editor_config.json"

TICKS_PER_QUARTER = 480  # Standard interne pour les ticks

def _extract_mscz(mscz_path, extract_to):
    if extract_to.exists(): 
        shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mscz_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def getGrid(file_path) -> Grid:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    extension = file_path.suffix.lower()
    input_for_musescore = None

    # Détection élargie des formats de chansons Band-in-a-Box (gère .sgu, .mgu, et toutes les variantes .sg* / .mg*)
    is_biab_song = extension in [".sgu", ".mgu"] or extension.startswith(".sg") or extension.startswith(".mg")

    # Aiguillage selon le type de fichier source
    if extension == ".mscz":
        _extract_mscz(file_path, TEMP_DIR)
        mscx_files = list(TEMP_DIR.glob("*.mscx"))
        if not mscx_files:
            raise FileNotFoundError(f"Aucun fichier .mscx trouvé dans {TEMP_DIR}")
        input_for_musescore = mscx_files[0]

    elif extension == ".zip":
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(TEMP_DIR)
        
        # Recherche d'un format compatible à l'intérieur du ZIP
        mscx_files = list(TEMP_DIR.glob("**/*.mscx"))
        
        # Recherche élargie de fichiers BIAB dans le ZIP
        biab_files = []
        for p in TEMP_DIR.glob("**/*"):
            if p.is_file():
                ext = p.suffix.lower()
                if ext in [".sgu", ".mgu"] or ext.startswith(".sg") or ext.startswith(".mg"):
                    biab_files.append(p)
        
        if mscx_files:
            input_for_musescore = mscx_files[0]
        elif biab_files:
            input_for_musescore = biab_files[0]
        else:
            raise FileNotFoundError("Aucun fichier compatible (.mscx ou grille Band-in-a-Box) trouvé dans l'archive ZIP.")

    elif is_biab_song:
        # Fichier binaire brut Band-in-a-Box (quelque soit sa variante de suffixe song)
        input_for_musescore = file_path
    else:
        raise ValueError(f"Format de fichier non pris en charge ou extension de style non importable : {extension}")

    musicxml_path = TEMP_DIR / "partition.musicxml"
    success = False

    # Chargement dynamique du chemin MuseScore depuis la configuration (.grid_editor_config.json)
    custom_musescore_path = None
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                custom_musescore_path = config.get("musescore_path")
        except Exception:
            pass

    musescore_commands = []
    if custom_musescore_path:
        musescore_commands.append(custom_musescore_path)

    musescore_commands.extend([
        "musescore4",
        "musescore",
        "mscore"
    ])

    for cmd in musescore_commands:
        try:
            # Si c'est un chemin absolu/relatif vers un fichier/AppImage, on vérifie son existence
            if ("/" in cmd or "\\" in cmd) and not Path(cmd).exists():
                continue

            subprocess.run(
                [cmd, "-o", str(musicxml_path), str(input_for_musescore)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            success = True
            break
        except (FileNotFoundError, subprocess.SubprocessError):
            continue

    if not success or not musicxml_path.exists():
        raise RuntimeError("Échec de la conversion du fichier en MusicXML via MuseScore.")

    tree = ET.parse(musicxml_path)
    root_elem = tree.getroot() # <score-partwise>

    parts = root_elem.findall("part")
    if not parts:
        raise ValueError("Aucune partie (part) trouvée dans le fichier MusicXML.")

    # Recherche de la première partie contenant des accords (<harmony>)
    target_part = None
    for part in parts:
        if part.find(".//harmony") is not None:
            target_part = part
            break
    
    if target_part is None:
        raise ValueError("Aucune partie contenant des accords (<harmony>) n'a été trouvée dans le fichier.")

    # Informations d'en-tête : priorité au titre textuel des crédits
    work_title = None
    for credit in root_elem.findall("credit"):
        c_type = credit.findtext("credit-type")
        if c_type == "title":
            words = credit.findtext("credit-words")
            if words:
                work_title = words.strip()
                break
    if not work_title:
        work_title = root_elem.findtext(".//work-title", file_path.stem)
    
    composer = root_elem.findtext(".//creator[@type='composer']", "")
    lyricist = root_elem.findtext(".//creator[@type='lyricist']", "")
    arranger = root_elem.findtext(".//creator[@type='arranger']", "")

    measures = target_part.findall("measure")
    if not measures:
        raise ValueError("Aucune mesure trouvée dans l'export MusicXML.")

    initial_timesig = "4/4"
    initial_bpm = 120

    for measure in measures:
        ts_elem = measure.find(".//time")
        if ts_elem is not None:
            beats = ts_elem.findtext("beats", "")
            beat_type = ts_elem.findtext("beat-type", "")
            if beats and beat_type:
                initial_timesig = f"{beats}/{beat_type}"
                break

    for measure in measures:
        sound_elem = measure.find(".//sound")
        if sound_elem is not None and sound_elem.get("tempo"):
            try:
                initial_bpm = int(float(sound_elem.get("tempo")))
                break
            except ValueError:
                pass

    grid = Grid(header=Header(
        title=work_title,
        composer=composer,
        lyricist=lyricist,
        arranger=arranger,
        timesig=initial_timesig,
        bpm=initial_bpm
    ))

    current_divisions = 1
    current_measure_tick = 0
    current_timesig = initial_timesig

    for i, measure in enumerate(measures, start=1):
        measure_duration = 1920

        div_elem = measure.find(".//divisions")
        if div_elem is not None and div_elem.text and div_elem.text.isdigit():
            current_divisions = int(div_elem.text.strip())

        ts_elem = measure.find(".//time")
        measure_timesig = ""
        
        if ts_elem is not None:
            beats = ts_elem.findtext("beats", "")
            beat_type = ts_elem.findtext("beat-type", "")
            if beats and beat_type:
                detected_ts = f"{beats}/{beat_type}"
                if i == 1 or detected_ts != current_timesig:
                    current_timesig = detected_ts
                    measure_timesig = detected_ts
                try:
                    measure_duration = int((int(beats) / int(beat_type)) * 4 * TICKS_PER_QUARTER)
                except ZeroDivisionError:
                    pass
        elif i == 1:
            measure_timesig = initial_timesig

        keysig = measure.findtext(".//key/fifths", "0")
        
        bpm = 0
        sound_elem = measure.find(".//sound")
        if sound_elem is not None and sound_elem.get("tempo"):
            try:
                bpm = int(float(sound_elem.get("tempo")))
            except ValueError:
                pass

        bar = Bar(
            number=i,
            timesig=measure_timesig,
            keysig=keysig,
            bpm=bpm
        )

        for barline in measure.findall("barline"):
            repeat = barline.find("repeat")
            if repeat is not None:
                direction = repeat.get("direction")
                if direction == "forward":
                    bar.start_repeat = True
                elif direction == "backward":
                    times = repeat.get("times", "1")
                    try:
                        bar.end_repeat = int(times)
                    except ValueError:
                        bar.end_repeat = 1

            # Extraction des voltas (endings MusicXML)
            ending = barline.find("ending")
            if ending is not None:
                ending_type = ending.get("type")
                if ending_type in ("start", "discontinue"):
                    num = ending.get("number", "1")
                    bar.volta = num

        raw_chords = []
        cumulative_divisions = 0

        for elem in measure:
            tag = elem.tag

            if tag == "harmony":
                chord_name = chordW3CtoGridChord(elem)
                
                offset_elem = elem.findtext("offset")
                if offset_elem and offset_elem.replace(".", "", 1).isdigit():
                    offset_val = float(offset_elem)
                else:
                    offset_val = float(cumulative_divisions)

                beat = round((offset_val / current_divisions) + 1, 1)
                rel_tick = int((offset_val / current_divisions) * TICKS_PER_QUARTER)
                abs_tick = current_measure_tick + rel_tick

                chord_obj = ChordInternal(chord=chord_name, tick=abs_tick, beat=beat)
                raw_chords.append(chord_obj)

            elif tag == "note":
                if elem.find("rest[@measure='yes']") is None:
                    dur_elem = elem.findtext("duration")
                    if dur_elem and dur_elem.isdigit():
                        cumulative_divisions += int(dur_elem)

            elif tag == "direction":
                rehearsal = elem.find(".//rehearsal")
                if rehearsal is not None and rehearsal.text:
                    bar.add_section(rehearsal.text.strip())

                words = elem.find(".//words")
                if words is not None and words.text:
                    w_text = words.text.strip().lower()
                    if "d.s. al fine" in w_text or "ds al fine" in w_text:
                        bar.add_jump("MG_DS_AL_FINE")
                    elif "d.s. al coda" in w_text or "ds al coda" in w_text:
                        bar.add_jump("MG_DS_AL_CODA")
                    elif "d.c. al fine" in w_text or "dc al fine" in w_text:
                        bar.add_jump("MG_DC_AL_FINE")
                    elif "d.c. al coda" in w_text or "dc al coda" in w_text:
                        bar.add_jump("MG_DC_AL_CODA")
                    elif "to" in w_text and "coda" in w_text:
                        bar.add_jump("MG_TO_CODA")
                    elif "d.c." in w_text or "da capo" in w_text:
                        bar.add_jump("MG_DA_CAPO")
                    elif "d.s." in w_text or "dal segno" in w_text:
                        bar.add_jump("MG_GOTO_SIGNO")
                    elif "fine" in w_text:
                        bar.add_marker("MG_FINE")
                    elif "segno" in w_text:
                        bar.add_marker("MG_SEGNO")
                    elif "coda" in w_text:
                        bar.add_marker("MG_CODA")

                if elem.find(".//segno") is not None:
                    bar.add_marker("MG_SEGNO")
                if elem.find(".//coda") is not None:
                    bar.add_marker("MG_CODA")

        if raw_chords:
            bar.set_chords_from_internal(raw_chords)

        grid.add_bar(bar)
        current_measure_tick += measure_duration

    return grid
    
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog
    from pdfGenerator import gridToPdf

    last_file_path = "lastFile.txt"
    initial_dir = "/"

    if os.path.exists(last_file_path):
        try:
            with open(last_file_path, "r", encoding="utf-8") as f:
                saved_path = f.read().strip()
                if saved_path:
                    initial_dir = os.path.dirname(saved_path) if os.path.isfile(saved_path) else saved_path
        except Exception:
            pass

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Sélectionner le fichier score",
        initialdir=initial_dir,
        filetypes=[("Fichiers MuseScore", "*.mscz"), ("Tous les fichiers", "*.*")]
    )

    if file_path:
        try:
            with open(last_file_path, "w", encoding="utf-8") as f:
                f.write(file_path)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du dernier fichier : {e}")

        grid = getGrid(file_path)
        gridToPdf(grid, "temp/test.pdf")
        print(type(grid))
        print(grid)
    else:
        print("Aucun fichier sélectionné.")