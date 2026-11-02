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

    is_biab_song = extension in [".sgu", ".mgu"] or extension.startswith(".sg") or extension.startswith(".mg")

    if extension == ".mscz":
        _extract_mscz(file_path, TEMP_DIR)
        mscx_files = list(TEMP_DIR.glob("*.mscx"))
        if not mscx_files:
            raise FileNotFoundError(f"Aucun fichier .mscx trouvé dans {TEMP_DIR}")
        input_for_musescore = mscx_files[0]

    elif extension == ".zip":
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(TEMP_DIR)
        
        mscx_files = list(TEMP_DIR.glob("**/*.mscx"))
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
        input_for_musescore = file_path
    else:
        raise ValueError(f"Format de fichier non pris en charge ou extension non importable : {extension}")

    musicxml_path = TEMP_DIR / "partition.musicxml"
    success = False

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

    # 1. Recherche de la portée porteuse d'accords (pour les accords uniquement)
    chord_part = None
    for part in parts:
        if part.find(".//harmony") is not None:
            chord_part = part
            break
    if chord_part is None:
        chord_part = parts[0]

    # 2. Recherche de la portée porteuse de structure (sections, voltas, sauts, repères)
    structure_part = None
    for part in parts:
        has_structure = (
            part.find(".//rehearsal") is not None or
            part.find(".//segno") is not None or
            part.find(".//coda") is not None or
            part.find(".//ending") is not None
        )
        if not has_structure:
            for words in part.findall(".//words"):
                if words.text:
                    txt = words.text.strip().lower()
                    if any(k in txt for k in ["ds", "dc", "coda", "segno", "fine", "to coda"]):
                        has_structure = True
                        break
        if has_structure:
            structure_part = part
            break
    
    if structure_part is None:
        structure_part = parts[0]

    # --- En-tête : Récupération robuste du Titre et du Compositeur ---
    work_title = None
    for credit in root_elem.findall(".//credit"):
        c_type = credit.findtext("credit-type")
        if c_type == "title":
            words = credit.findtext("credit-words")
            if words:
                work_title = words.strip()
                break
    if not work_title:
        work_title = root_elem.findtext(".//work-title", file_path.stem)
    
    composer = root_elem.findtext(".//identification/creator[@type='composer']", "")
    if not composer:
        composer = root_elem.findtext(".//creator[@type='composer']", "")

    lyricist = root_elem.findtext(".//identification/creator[@type='lyricist']", "")
    arranger = root_elem.findtext(".//identification/creator[@type='arranger']", "")

    chord_measures = chord_part.findall("measure")
    struct_measures = structure_part.findall("measure")

    if not chord_measures:
        raise ValueError("Aucune mesure trouvée dans la partie d'accords.")

    initial_timesig = "4/4"
    initial_bpm = 120

    for measure in chord_measures:
        ts_elem = measure.find(".//time")
        if ts_elem is not None:
            beats = ts_elem.findtext("beats", "")
            beat_type = ts_elem.findtext("beat-type", "")
            if beats and beat_type:
                initial_timesig = f"{beats}/{beat_type}"
                break

    for measure in chord_measures:
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

    # Synchronisation des mesures entre chord_part et structure_part par index
    for i in range(1, len(chord_measures) + 1):
        chord_measure = chord_measures[i - 1]
        struct_measure = struct_measures[i - 1] if (i - 1) < len(struct_measures) else chord_measure

        measure_duration = 1920

        div_elem = chord_measure.find(".//divisions")
        if div_elem is not None and div_elem.text and div_elem.text.isdigit():
            current_divisions = int(div_elem.text.strip())

        ts_elem = chord_measure.find(".//time")
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

        keysig = chord_measure.findtext(".//key/fifths", "0")
        
        bpm = 0
        sound_elem = chord_measure.find(".//sound")
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

        # Extraction des barlines, reprises et voltas depuis la portée de structure
        for barline in struct_measure.findall("barline"):
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

            ending = barline.find("ending")
            if ending is not None:
                ending_type = ending.get("type")
                if ending_type in ("start", "discontinue"):
                    num = ending.get("number", "1")
                    bar.volta = num

        # Extraction des accords depuis la portée d'accords uniquement
        raw_chords = []
        cumulative_divisions = 0

        for elem in chord_measure:
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

        # Extraction des sections, repères et sauts depuis la portée de structure
        for elem in struct_measure:
            tag = elem.tag
            if tag == "direction":
                rehearsal = elem.find(".//rehearsal")
                if rehearsal is not None and rehearsal.text:
                    bar.add_section(rehearsal.text.strip())

                for words_elem in elem.findall(".//words"):
                    if words_elem.text:
                        w_text = words_elem.text.strip().lower()
                        w_clean = w_text.replace(".", "").replace(" ", "").replace("-", "")

                        if "dsalfin" in w_clean or "dselfin" in w_clean:
                            bar.add_jump("MG_DS_AL_FINE")
                        elif "dsalcoda" in w_clean or "dsalc" in w_clean:
                            bar.add_jump("MG_DS_AL_CODA")
                        elif "dcalfin" in w_clean:
                            bar.add_jump("MG_DC_AL_FINE")
                        elif "dcalcoda" in w_clean:
                            bar.add_jump("MG_DC_AL_CODA")
                        elif "tocoda" in w_clean or "toc" in w_clean:
                            bar.add_jump("MG_TO_CODA")
                        elif "dacapo" in w_clean or w_clean == "dc":
                            bar.add_jump("MG_DA_CAPO")
                        elif "dalsegno" in w_clean or w_clean == "ds":
                            bar.add_jump("MG_GOTO_SIGNO")
                        elif "fine" in w_clean:
                            bar.add_marker("MG_FINE")
                        elif "segno" in w_clean:
                            bar.add_marker("MG_SEGNO")
                        elif "coda" in w_clean and "to" not in w_clean and "al" not in w_clean:
                            bar.add_marker("MG_CODA")

                if elem.find(".//coda") is not None:
                    bar.add_marker("MG_CODA")
                if elem.find(".//segno") is not None:
                    bar.add_marker("MG_SEGNO")

                sound_dir = elem.find(".//sound")
                if sound_dir is not None:
                    if sound_dir.get("coda") or sound_dir.get("tocoda"):
                        if "MG_TO_CODA" not in bar.jumps:
                            bar.add_jump("MG_TO_CODA")
                    if sound_dir.get("dalsegno"):
                        if not any(j in bar.jumps for j in ["MG_DS_AL_CODA", "MG_DS_AL_FINE", "MG_GOTO_SIGNO"]):
                            bar.add_jump("MG_DS_AL_CODA")

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