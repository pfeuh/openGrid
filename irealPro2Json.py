#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import re
import unicodedata
from pyRealParser import Tune
from models import Grid, Header, Bar

def to_camel_case(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    words = re.findall(r'[a-zA-Z0-9]+', s)
    if not words: return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])

def normalize_ireal_chord(chord_str):
    """Traduit les symboles natifs iReal Pro (^, o, h, etc.) en notations standard."""
    if not chord_str:
        return ""
    if "/" in chord_str:
        left, right = chord_str.split("/", 1)
        return normalize_ireal_chord(left) + "/" + right
    
    s = chord_str.strip()
    # Remplacements iReal Pro vers les standards de l'application
    s = s.replace("^7", "maj7")
    s = s.replace("^", "maj7")   # Le triangle ^ seul signifie major 7
    s = s.replace("o7", "dim7")
    s = s.replace("o", "dim")
    s = s.replace("h7", "m7b5")
    s = s.replace("h", "m7b5")
    return s

def saveGrid(grid_obj):
    os.makedirs("grids", exist_ok=True)
    tune_name = grid_obj.header.title if grid_obj.header else "morceau"
    fname = to_camel_case(tune_name) or "morceau"
    filepath = os.path.join("grids", f"{fname}.grid")
    
    data = grid_obj.to_dict() if hasattr(grid_obj, "to_dict") else {}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Grille sauvegardée avec succès : {filepath}")

def irealproToGrid(url):
    tunes = Tune.parse_ireal_url(url)
    if not tunes:
        return None
    
    tune = tunes[0]
    
    title = getattr(tune, 'title', "Inconnu")
    composer = getattr(tune, 'composer', "Inconnu")
    style = getattr(tune, 'style', "Standard")
    bpm_val = float(tune.bpm) if getattr(tune, 'bpm', None) and str(tune.bpm).replace('.', '', 1).isdigit() else 120.0
    timesig_val = f"{tune.time_signature[0]}/{tune.time_signature[1]}" if getattr(tune, 'time_signature', None) else "4/4"

    header = Header(
        title=title,
        composer=composer,
        style=style,
        category="Jazz / Pop",
        bpm=bpm_val,
        timesig=timesig_val
    )

    grid_obj = Grid(header=header)
    
    measures = getattr(tune, 'measures_as_strings', [])
    for i, measure in enumerate(measures, start=1):
        cleaned_measure = measure.strip() if measure else ""
        chords_list = []
        if cleaned_measure:
            # On normalise chaque accord extrait pour éliminer les symboles iReal Pro bruts (^, o, h)
            chords_list = [normalize_ireal_chord(c.strip()) for c in cleaned_measure.split() if c.strip()]
        
        line_break = (i % 4 == 0 and i < len(measures))
        
        bar_obj = Bar(number=i)
        bar_obj.chords = chords_list
        if hasattr(bar_obj, 'line_break'):
            bar_obj.line_break = line_break
            
        grid_obj.add_bar(bar_obj)
        
    return grid_obj

if __name__ == "__main__":
    url_test = "irealb://A%20Night%20In%20Tunisia=Gillespie%20Dizzy==Latin=D%2D==1r34LbKcu7hE%7CQy4Eb7XQyX7bE%7CQyX6%2DD%7CyQX7bE%7CQyX6%2DD%7CQy%7CD%2D6X4TA%2A%7BQyX7h9LZD%2DcKQyX7%2DG%7CQyX9bD7%7CQyX7hAB%2A%5B%7DQyXl%20LZGb7A%207%7CQyX7XyQ%7CFX6%2DD%7CQyX7bEA%2A%5B%20%5D9b7A%207hE%7CQyX7%5EyQ%7CEb9b7C%7ClcKQyQ%7CEb7%5BYZ%20Q%20%20%2DDZL9b7%20A7hE%7CQyX6%2DD%7CQyXQEh7XyX6%2DDyX7%5E%2D7%2311XcKQyX11%237GZL%20lKcQyX7%2DDZL%20lcKQyl%20LZGbEZL%20Q%7CG%2D7XyQ%7CGb7%239XyQKcl%20LZF%5E7XyQKcl%20LZEh7XyQ%7CA7b9XyQZ%20==0=0==="
    
    resultat_grid = irealproToGrid(url_test)
    if resultat_grid:
        saveGrid(resultat_grid)
    else:
        print("URL invalide ou aucun morceau trouvé.")