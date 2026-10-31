#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import sys
from models import Grid
from compiler import compile_grid
from getMusescoreGrid import getGrid

def compare_lists(fl1, fl2):
    print(f"\n--- Comparaison détaillée ---", flush=True)
    print(f"flat_list ({len(fl1)} éléments) : {fl1}", flush=True)
    print(f"ref_list  ({len(fl2)} éléments) : {fl2}", flush=True)
    for x, item in enumerate(fl1):
        if x >= len(fl2):
            print(f"[{x}] liste trop petite (absent de ref_list)", flush=True)
            return
        a = fl1[x]
        b = fl2[x]
        if a != b:
            print("%4u X %-4u"%(a, b), flush=True)
        else:
            print("%4u . %-4u"%(a, b), flush=True)
    if len(fl1) > len(fl2):
        print(f"liste trop grande de {len(fl1) - len(fl2)} éléments", flush=True)
    for i, item in enumerate(fl1):
        sys.stdout.write("%-4u"%item)
        if i % 8 == 7:
            sys.stdout.write("\n")
    sys.stdout.write("\n")

def compare_dicts(d1, d2, name1="dict1", name2="dict2"):
    if hasattr(d1, "to_dict"):
        d1 = d1.to_dict()
    if hasattr(d2, "to_dict"):
        d2 = d2.to_dict()

    print(f"\n--- Comparaison détaillée : {name1} vs {name2} ---", flush=True)
    keys1 = set(d1.keys())
    keys2 = set(d2.keys())
    
    all_keys = sorted(list(keys1.union(keys2)))
    print(f"Total clés uniques : {len(all_keys)} ({name1}: {len(keys1)}, {name2}: {len(keys2)})", flush=True)
    
    mismatches = 0
    for key in all_keys:
        in1 = key in keys1
        in2 = key in keys2
        
        if not in1:
            print(f"[-] Clé '{key}' absente dans {name1}", flush=True)
            mismatches += 1
        elif not in2:
            print(f"[-] Clé '{key}' absente dans {name2}", flush=True)
            mismatches += 1
        else:
            v1 = d1[key]
            v2 = d2[key]
            if v1 != v2:
                print(f"[X] Différence sur la clé '{key}':", flush=True)
                print(f"    {name1}: {v1}", flush=True)
                print(f"    {name2}: {v2}", flush=True)
                mismatches += 1
            else:
                print(f"[.] Clé '{key}' identique", flush=True)
                
    if mismatches == 0:
        print("--- Dictionnaires strictement identiques ---", flush=True)
    else:
        print(f"--- Fin de comparaison : {mismatches} divergence(s) ---", flush=True)
    return mismatches == 0


def compare_grids_dict(grid1_dict, grid2_dict):
    print(f"\n========================================", flush=True)
    print(f"    COMPARAISON GLOBALE DES DEX GRILLES    ", flush=True)
    print(f"========================================", flush=True)
    
    compare_dicts(grid1_dict.get("header", {}), grid2_dict.get("header", {}), "Header_1", "Header_2")
    
    bars1 = grid1_dict.get("bars", [])
    bars2 = grid2_dict.get("bars", [])
    
    print(f"\n--- Comparaison des mesures (Total: {len(bars1)} vs {len(bars2)}) ---", flush=True)
    
    max_len = max(len(bars1), len(bars2))
    diff_count = 0
    
    for i in range(max_len):
        if i >= len(bars1):
            print(f"[{i+1:3d}] X [Absente dans Grille 1]", flush=True)
            diff_count += 1
            continue
        if i >= len(bars2):
            print(f"[{i+1:3d}] X [Absente dans Grille 2]", flush=True)
            diff_count += 1
            continue
            
        b1 = bars1[i]
        b2 = bars2[i]
        
        if b1 != b2:
            print(f"[{i+1:3d}] X DIFF", flush=True)
            keys_b1 = set(b1.keys())
            keys_b2 = set(b2.keys())
            for k in sorted(keys_b1.union(keys_b2)):
                if b1.get(k) != b2.get(k):
                    print(f"        -> clé '{k}': Grille1={b1.get(k)} | Grille2={b2.get(k)}", flush=True)
            diff_count += 1
        else:
            sys.stdout.write(f"[{i+1:3d}]. ")
            if i % 8 == 7:
                sys.stdout.write("\n")
                sys.stdout.flush()
                
    sys.stdout.write("\n")
    if diff_count == 0:
        print("=== TOUTES LES MESURES SONT IDENTIQUES ===", flush=True)
    else:
        print(f"=== {diff_count} mesure(s) différente(s) trouvée(s) ===", flush=True)

def callIntegration(fname):
    U1, U2 = "temp/utest1.grid", "temp/utest2.grid"
    print("testing integration %s"%fname, flush=True)
    grid1 = getGrid(fname)
    grid1.save(U1)
    grid2 = Grid.load(U1)
    #~ grid2.header.title = "valeur_corrompue"
    grid2.save(U2)
    with open(U1, "r", encoding="utf-8") as f1, open(U2, "r", encoding="utf-8") as f2:
        try:
            assert json.load(f1) == json.load(f2), "Perte de données détectée entre test1 et test2 !"
        except:
            compare_dicts(grid1, grid2 , "grid1", "grid2")
            raise

def callCompiler(fname, ref_list):
    print("testing compilation %s"%fname, flush=True)
    # Chargement strict via l'objet Grid
    grid_obj = Grid.load(fname)
    flat_list = compile_grid(grid_obj)
    try:
        assert flat_list == ref_list
    except AssertionError:
        compare_lists(flat_list, ref_list)
        raise
    except Exception as e:
        print(f"Autre exception attrapée : {e}", flush=True)
        raise

def callMusescoreGrid(fname, ref_list):
    print("testing musescore import %s" % fname, flush=True)
    grid = getGrid(fname)
    
    ref_bars = ref_list.get("bars", []) if isinstance(ref_list, dict) else ref_list
    assert len(grid.bars) == len(ref_bars), f"Échec nombre de mesures : obtenu {len(grid.bars)}, attendu {len(ref_bars)}"

    for i, ref_bar in enumerate(ref_bars):
        bar = grid.bars[i]
        actual_chords = [str(c) for c in bar.chords] if hasattr(bar, 'chords') else []
        expected_chords = ref_bar.get("chords", [])

        assert actual_chords == expected_chords, f"Échec à la mesure {i+1} : {actual_chords} != {expected_chords}"

def utestCompiler():
    ref_list = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 
                5, 6, 7, 8,
                9, 10, 11, 12,
                9, 10, 13, 14,
                9, 10, 15, 16,
                17, 18,
                17, 19, 20]
    callCompiler('grids/utest/utestScore.grid', ref_list)
    
    ref_list = [1, 2, 3, 4,
                5, 6, 7, 8, 9, 10, 11, 12,
                5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                5, 6, 7, 8, 9, 10, 11, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                5, 6, 7, 8, 9, 10, 11, 12,
                5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                5, 6, 7, 8, 9, 10, 11, 22]
    callCompiler('grids/utest/aNightInTunisia.grid', ref_list)

    ref_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
                34, 35, 36, 37, 38, 39, 40, 29, 30, 31, 32, 33, 34, 35,
                36, 37, 38, 39, 40, 41, 42, 43, 44]
    callCompiler('grids/utest/repetitionsSimples.grid', ref_list)

    ref_list = [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 
                6, 7, 8, 9, 10, 13, 14, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19, 20]
    callCompiler('grids/utest/repetitionsVolta.grid', ref_list)

def utestGetMusescoreGrid():
    ref_list = {
        "header": {
            "title": "Partition sans titre",
            "composer": "Compositeur / Arrangeur",
            "style": "StandardRock",
            "category": "Pop & Rock",
            "bpm": 120.0,
            "timesig": "4/4"
        },
        "bars": [
            {
                "number": 1,
                "chords": ["C", "G/B@2.0", "Am@3.0", "C/G@4.0"],
                "timesig": "4/4",
                "keysig": "0"
            },
            {
                "number": 2,
                "chords": ["C", "G/B@2.0", "Am@3.0", "F/G@4.0"],
                "timesig": "4/4",
                "keysig": "0"
            },
            {
                "number": 3,
                "chords": ["G", "Bb@2.5", "C@4.0"],
                "timesig": "4/4",
                "keysig": "0"
            }
        ]
    }
    
    callMusescoreGrid("musescore/utest/chords.mscz", ref_list)
    
    ref_list = {
        "header": {
            "title": "A night in Tunisia",
            "composer": "un gars",
            "style": "StandardRock",
            "category": "Pop & Rock",
            "bpm": 120.0,
            "timesig": "4/4"
        },
        "bars": [
            {
                "number": 1,
                "timesig": "4/4",
                "keysig": "-1"
            },
            {
                "number": 2
            },
            {
                "number": 3
            },
            {
                "number": 4,
                "line_break": True
            },
            {
                "number": 5,
                "chords": [
                    "Eb7"
                ],
                "markers": [
                    "MG_SEGNO"
                ],
                "sections": [
                    "A"
                ],
                "start_repeat": True
            },
            {
                "number": 6,
                "chords": [
                    "Dm6"
                ]
            },
            {
                "number": 7,
                "chords": [
                    "Eb7"
                ]
            },
            {
                "number": 8,
                "chords": [
                    "Dm6"
                ],
                "line_break": True
            },
            {
                "number": 9,
                "chords": [
                    "Eb7"
                ]
            },
            {
                "number": 10,
                "chords": [
                    "Dm6"
                ]
            },
            {
                "number": 11,
                "chords": [
                    "Em7b5",
                    "A7b5@3.0"
                ]
            },
            {
                "number": 12,
                "chords": [
                    "Dm6"
                ],
                "volta": "1.",
                "end_repeat": 2
            },
            {
                "number": 13,
                "chords": [
                    "Dm6"
                ],
                "volta": "2.",
                "line_break": True
            },
            {
                "number": 14,
                "chords": [
                    "Am7b5"
                ],
                "sections": [
                    "B"
                ]
            },
            {
                "number": 15,
                "chords": [
                    "D7b9"
                ]
            },
            {
                "number": 16,
                "chords": [
                    "Gm6"
                ]
            },
            {
                "number": 17,
                "chords": [
                    "C7@3.0"
                ],
                "line_break": True
            },
            {
                "number": 18,
                "chords": [
                    "Gm7b5"
                ]
            },
            {
                "number": 19,
                "chords": [
                    "C7b9"
                ]
            },
            {
                "number": 20,
                "chords": [
                    "F6"
                ]
            },
            {
                "number": 21,
                "chords": [
                    "Em7b5",
                    "A7b5@3.0"
                ],
                "end_repeat": 2
            },
            {
                "number": 22,
                "chords": [
                    "Dm6"
                ],
                "markers": [
                    "MG_FINE"
                ],
                "volta": "3.",
                "line_break": True
            },
            {
                "number": 23,
                "chords": [
                    "Em7b5"
                ],
                "sections": [
                    "Interlude"
                ]
            },
            {
                "number": 24
            },
            {
                "number": 25,
                "chords": [
                    "Eb7#11",
                ]
            },
            {
                "number": 26,
                "line_break": True
            },
            {
                "number": 27,
                "chords": [
                    "Dm"
                ]
            },
            {
                "number": 28
            },
            {
                "number": 29,
                "chords": [
                    "G7#11"
                ]
            },
            {
                "number": 30,
                "line_break": True
            },
            {
                "number": 31,
                "chords": [
                    "GmM7"
                ]
            },
            {
                "number": 32,
                "chords": [
                    "Gm7"
                ]
            },
            {
                "number": 33,
                "chords": [
                    "Gb7#9",
                    "A"
                ]
            },
            {
                "number": 34,
                "chords": [
                    "FM7@4.5"
                ],
                "line_break": True
            },
            {
                "number": 35
            },
            {
                "number": 36
            },
            {
                "number": 37,
                "chords": [
                    "Em7b5"
                ]
            },
            {
                "number": 38,
                "chords": [
                    "A7b9"
                ],
                "jumps": [
                    "MG_DS_AL_FINE"
                ]
            }
        ]
    }

    callMusescoreGrid("musescore/utest/aNightInTunisia.mscz", ref_list)

def utestIntegration():
    callIntegration("musescore/utest/aNightInTunisia.mscz")

if __name__ == "__main__":
    utestIntegration()
    utestCompiler()
    utestGetMusescoreGrid()
    print ("\nA L L    T E S T S    P A S S E D !")