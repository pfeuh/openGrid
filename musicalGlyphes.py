#!/usr/bin/python
# -*- coding: utf-8 -*-

# --- CONSTANTES DE MISE EN PAGE ---
MAX_COLS = 4  

# --- MARQUEURS (Cibles / Repères fixes) ---
MG_SEGNO = "MG_SEGNO"
MG_CODA = "MG_CODA"              # Symbole graphique Coda (𝄌)
MG_TEXT_CODA = "MG_TEXT_CODA"    # Texte "Coda"
MG_FINE = "MG_FINE"
MG_IDEM = "MG_IDEM"              # Simile / %
MG_GENERIC_MARKER = "MG_GENERIC_MARKER"

# --- SAUTS (Actions / Commandes de navigation) ---
MG_TO_CODA = "MG_TO_CODA"        # To Coda (Porte de sortie)
MG_GOTO_SIGNO = "MG_GOTO_SIGNO"  # D.S. simple
MG_DA_CAPO = "MG_DA_CAPO"        # Da Capo (D.C.)
MG_DS_AL_CODA = "MG_DS_AL_CODA"
MG_DS_AL_FINE = "MG_DS_AL_FINE"
MG_DC_AL_CODA = "MG_DC_AL_CODA"
MG_DC_AL_FINE = "MG_DC_AL_FINE"
MG_GENERIC_JUMP = "MG_GENERIC_JUMP"

# --- AUTRES ÉLÉMENTS STRUCTURELS ---
MG_REPEAT1 = "MG_REPEAT1"
MG_REPEAT2 = "MG_REPEAT2"
MG_START_REPEAT = "MG_START_REPEAT"
MG_END_REPEAT = "MG_END_REPEAT"
MG_LINE_BREAK = "MG_LINE_BREAK"
MG_VOLTA = "MG_VOLTA"

# Dictionnaire des signatures temporelles en police Bravura
TIME_SIGNATURE_GLYPHS = {
    "2/4": "\uf603",
    "2/2": "\uf604",
    "3/2": "\uf605",
    "3/4": "\uf606",
    "3/8": "\uf607",
    "4/4": "\uf608",
    "5/4": "\uf609",
    "5/8": "\uf60a",
    "6/4": "\uf60b",
    "6/8": "\uf60c",
    "7/8": "\uf60d",
    "9/8": "\uf60e",
    "12/8": "\uf60f"
}

# Configuration centralisée du rendu
GLYPH_CONFIGS = {
    MG_CODA: {
        "content": "\U0001D10C",  # Symbole Coda (𝄌) de Bravura
        "font": "Bravura",
        "size": 18,
        "row": "above",
        "align": "left"
    },
    MG_TEXT_CODA: {
        "content": "Coda",
        "font": "MuseJazzText",
        "size": 13,
        "row": "above",
        "align": "left"
    },
    MG_TO_CODA: {
        "content": "to \U0001D10C",
        "font": "MuseJazzText",
        "size": 13,
        "row": "above",
        "align": "right"
    },
    MG_IDEM: {
        "content": "\U0001D10E",
        "font": "Bravura",
        "size": 22,
        "row": "inside",
        "align": "center",
        "y_offset": 8
    },
    MG_SEGNO: {
        "content": "\ue047",
        "font": "Bravura",
        "size": 16,
        "row": "above",
        "align": "left"
    },
    MG_REPEAT1: {
        "content": "\ue04c",
        "font": "Bravura",
        "size": 15,
        "row": "inside",
        "align": "left"
    },
    MG_REPEAT2: {
        "content": "\ue04d",
        "font": "Bravura",
        "size": 15,
        "row": "inside",
        "align": "right"
    },
    MG_START_REPEAT: {
        "type": "repeat_bar",
        "side": "left",
        "content": "\ue040",
        "font": "Bravura",
        "size": 26,
        "row": "inside"
    },
    MG_END_REPEAT: {
        "type": "repeat_bar",
        "side": "right",
        "content": "\ue041",
        "font": "Bravura",
        "size": 26,
        "row": "inside"
    },
    MG_GOTO_SIGNO: {
        "content": "\U0001D109",
        "font": "Bravura",
        "size": 18,
        "row": "above",
        "align": "right"
    },
    MG_DA_CAPO: {
        "content": "D.C.",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_DS_AL_CODA: {
        "content": "D.S. al Coda",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_DS_AL_FINE: {
        "content": "D.S. al Fine",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_DC_AL_CODA: {
        "content": "D.C. al Coda",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_DC_AL_FINE: {
        "content": "D.C. al Fine",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_FINE: {
        "content": "Fine",
        "font": "MuseJazzText",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_VOLTA: {
        "type": "volta",
        "font": "MuseJazzText",
        "size": 13,
        "row": "above",
        "align": "left"
    }
}

# Dictionnaire dédié aux Marqueurs (Cibles)
MARKER_ITEMS = {
    "segno": MG_SEGNO,
    "ds1": MG_SEGNO,
    "coda": MG_CODA,      
    "coda2": MG_CODA,      
    "coda symbol": MG_CODA,
    "codab": MG_CODA,
    "fine": MG_FINE,
    "repeat1": MG_REPEAT1,
    "repeat2": MG_REPEAT2,
    "start_repeat": MG_START_REPEAT,
    "end_repeat": MG_END_REPEAT,
    "idem": MG_IDEM,
    "simile": MG_IDEM
}

# Dictionnaire dédié aux Sauts (Commandes)
JUMP_ITEMS = {
    "tocoda": MG_TO_CODA,
    "to coda": MG_TO_CODA,
    "ds2": MG_GOTO_SIGNO,
    "d.s.": MG_GOTO_SIGNO,
    "d.c.": MG_DA_CAPO,
    "da capo": MG_DA_CAPO,
    "d.s. al fine": MG_DS_AL_FINE,
    "d.s. al coda": MG_DS_AL_CODA,
    "d.c. al fine": MG_DC_AL_FINE,
    "d.c. al coda": MG_DC_AL_CODA
}

# Rétrocompatibilité globale pour les modules tiers qui importent ITEMS
ITEMS = {**MARKER_ITEMS, **JUMP_ITEMS}