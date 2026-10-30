#!/usr/init/python
# -*- coding: utf-8 -*-

import json
import sys
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

def callCompiler(fname, ref_list):
    print("testing compilation %s"%fname, flush=True)
    with open(fname, 'r', encoding='utf-8') as f:
        grid = json.load(f)
    flat_list = compile_grid(grid)
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

if __name__ == "__main__":
    utestCompiler()
    utestGetMusescoreGrid()
    print ("\nA L L    T E S T S    P A S S E D !")
    
    