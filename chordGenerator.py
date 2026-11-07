#!/usr/bin/python
# -*- coding: utf-8 -*-

# Dictionnaire des décalages de demi-tons par rapport à Do (C)
NOTE_OFFSETS = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

# Intervalles (en demi-tons par rapport à la fondamentale) et extensions enrichies
QUALITY_INTERVALS = {
    "": [0, 4, 7],       # Majeur
    "maj": [0, 4, 7],     # Majeur
    "^": [0, 4, 7, 11],   # Majeur 7 (Alias iReal Pro)
    "^7": [0, 4, 7, 11],  # Majeur 7 (Alias iReal Pro)
    "m": [0, 3, 7],       # Mineur
    "-": [0, 3, 7],       # Mineur
    "min": [0, 3, 7],     # Mineur
    "7": [0, 4, 7, 10],   # 7e dominante
    "maj7": [0, 4, 7, 11],# Majeur 7
    "7M": [0, 4, 7, 11],  # Alias Majeur 7
    "m7": [0, 3, 7, 10],  # Mineur 7
    "-7": [0, 3, 7, 10],  # Mineur 7
    "mM7": [0, 3, 7, 11], # Mineur 7
    "9": [0, 4, 7, 10, 14], # 9e
    "m9": [0, 3, 7, 10, 14], # Mineur 9
    "-9": [0, 3, 7, 10, 14], # Mineur 9
    "maj9": [0, 4, 7, 11, 14], # Majeur 9
    "9M": [0, 4, 7, 11, 14],   # Majeur 9
    "dim": [0, 3, 6],     # Diminué
    "o": [0, 3, 6],       # Diminué (Alias iReal Pro)
    "dim7": [0, 3, 6, 9], # Diminué 7
    "o7": [0, 3, 6, 9],   # Diminué 7 (Alias iReal Pro)
    "m7b5": [0, 3, 6, 10],# Semi-diminué
    "-7b5": [0, 3, 6, 10],# Semi-diminué
    "h": [0, 3, 6, 10],   # Semi-diminué (Alias iReal Pro)
    "h7": [0, 3, 6, 10],  # Semi-diminué (Alias iReal Pro)
    "aug": [0, 4, 8],     # Augmenté
    "+": [0, 4, 8],       # Augmenté (alias)
    "5+": [0, 4, 8],      # Augmenté (alias)
    "6": [0, 4, 7, 9],    # Sixte
    "m6": [0, 3, 7, 9],   # Mineur 6
    "-6": [0, 3, 7, 9],   # Mineur 6
    "sus4": [0, 5, 7],    # Sus4
    "sus2": [0, 2, 7],    # Sus2
    "7sus4": [0, 5, 7, 10], # 7Sus4
    "7sus2": [0, 2, 7, 10], # 7Sus2
    "9b5": [0, 4, 6, 10, 14], # 9b5
}


def chordW3CtoGridChord(harmony_elem) -> str:
    """Extrait et convertit un élément <harmony> MusicXML (standard W3C) 
    en nom d'accord propre pour la grille."""
    
    # 1. Fondamentale (Root)
    root_step = harmony_elem.findtext("root/root-step", "")
    root_alter = harmony_elem.findtext("root/root-alter", "0")
    
    alter_str = ""
    try:
        alter = int(root_alter)
        if alter == 1:
            alter_str = "#"
        elif alter == -1:
            alter_str = "b"
        elif alter == 2:
            alter_str = "##"
        elif alter == -2:
            alter_str = "bb"
    except ValueError:
        pass

    root = f"{root_step}{alter_str}"

    # 2. Qualité de base (<kind>)
    kind_elem = harmony_elem.find("kind")
    suffix = ""
    val = ""
    if kind_elem is not None:
        text_attr = kind_elem.get("text", "").strip()
        if text_attr:
            suffix = text_attr
        else:
            val = (kind_elem.text or "").strip().lower()
            
            official_kind_map = {
                "major": "",
                "minor": "m",
                "augmented": "aug",
                "diminished": "dim",
                "dominant": "7",
                "major-seventh": "7M",
                "minor-seventh": "m7",
                "diminished-seventh": "dim7",
                "augmented-seventh": "7aug",
                "half-diminished": "m7b5",
                "major-minor": "m7M",
                "power": "5",
                "suspended-second": "sus2",
                "suspended-fourth": "sus4",
                "major-sixth": "6",
                "minor-sixth": "m6",
                "dominant-ninth": "9",
                "major-ninth": "9M",
                "minor-ninth": "m9",
                "dominant-11th": "11",
                "major-11th": "11M",
                "minor-11th": "m11",
                "dominant-13th": "13",
                "major-13th": "13M",
                "minor-13th": "m13",
                "none": ""
            }
            suffix = official_kind_map.get(val, val if val and val != "none" else "")

    # Détection spécifique si le kind est "dominant" mais qu'il porte en réalité une 7e majeure
    is_dominant_maj7 = (val == "dominant")

    # 3. Degrés et altérations (<degree>)
    degrees_suffix = ""
    for degree in harmony_elem.findall("degree"):
        deg_value = degree.findtext("degree-value", "")
        deg_alter = degree.findtext("degree-alter", "0")
        
        if deg_value:
            d_alt = 0
            d_alter_str = ""
            try:
                d_alt = int(deg_alter)
                if d_alt == 1:
                    d_alter_str = "#"
                elif d_alt == -1:
                    d_alter_str = "b"
                elif d_alt == 2:
                    d_alter_str = "##"
                elif d_alt == -2:
                    d_alter_str = "bb"
            except ValueError:
                pass
            
            # Si c'est un accord dominant avec un degré 7 neutre/altéré à 0, c'est un 7M
            if is_dominant_maj7 and deg_value == "7" and d_alt == 0:
                suffix = "7M"
                continue

            deg_str = f"{d_alter_str}{deg_value}"
            if deg_str not in suffix:
                degrees_suffix += deg_str

    # 4. Basse de l'accord (<bass>)
    bass_step = harmony_elem.findtext("bass/bass-step", "")
    bass_alter = harmony_elem.findtext("bass/bass-alter", "0")
    bass_str = ""
    if bass_step:
        b_alter_str = ""
        try:
            b_alter = int(bass_alter)
            if b_alter == 1:
                b_alter_str = "#"
            elif b_alter == -1:
                b_alter_str = "b"
        except ValueError:
            pass
        bass_str = f"/{bass_step}{b_alter_str}"

    return f"{root}{suffix}{degrees_suffix}{bass_str}"


def chord_to_midi(chord_str, base_octave=1):
    """Convertit dynamiquement n'importe quel accord (avec slash chords type C/D)
    en notes MIDI dans la zone basse/main gauche. La première lettre de la
    fondamentale (et de la basse) est tolérée en minuscule ou majuscule.
    """
    clean_chord = chord_str.strip()
    if "@" in clean_chord:
        clean_chord = clean_chord.split("@")[0].strip()
        
    bass_note_midi = None

    if "/" in clean_chord:
        chord_part, bass_part = clean_chord.split("/", 1)
        chord_part = chord_part.strip()
        bass_part = bass_part.strip()

        b_root_letter = bass_part[0].upper()
        if len(bass_part) > 1 and bass_part[1] in ["#", "b"]:
            b_root = b_root_letter + bass_part[1]
        else:
            b_root = b_root_letter

        if b_root in NOTE_OFFSETS:
            base_midi = base_octave * 12 + 12
            bass_note_midi = base_midi + NOTE_OFFSETS[b_root]
    else:
        chord_part = clean_chord

    root_letter = chord_part[0].upper()
    if len(chord_part) > 1 and chord_part[1] in ["#", "b"]:
        root = root_letter + chord_part[1]
        quality = chord_part[2:]
    else:
        root = root_letter
        quality = chord_part[1:]

    if root not in NOTE_OFFSETS:
        root = "C"
        print("<<< root %s not found! >>>"%str(root))

    if quality not in QUALITY_INTERVALS:
        print("<<< chord %s not found! >>>"%str(quality))
        quality = ""

    base_midi = base_octave * 12 + 12
    semitone_base = NOTE_OFFSETS[root]
    intervals = QUALITY_INTERVALS[quality]

    notes = [base_midi + semitone_base + interval for interval in intervals]

    if bass_note_midi is not None:
        if bass_note_midi not in notes:
            notes.append(bass_note_midi)
        notes.sort()

    while any(n > 43 for n in notes):
        notes = [n - 12 for n in notes]

    return notes