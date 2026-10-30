# -*- coding: utf-8 -*-

from copy import deepcopy
from constants import *
from musicalGlyphes import *
from sys import stdout
debug = False

NORMAL = 1
REPEAT = 2
VOLTA = 3
REPEAT_STATES = (NORMAL, REPEAT, VOLTA)
REPEAT_STATE = None
STATE_MODIFIED = False
REPEAT_STATE_LABEL = {NORMAL:"NORMAL ", REPEAT:"REPEAT ", VOLTA:"VOLTA  "}

def setState(state):
    global REPEAT_STATE, STATE_MODIFIED
    if not state in REPEAT_STATES:
        raise Exception("unknown state %s"%str(state))
    REPEAT_STATE = state
    STATE_MODIFIED = True

def isStateChanged():
    global STATE_MODIFIED
    ret_val = STATE_MODIFIED
    STATE_MODIFIED = False
    return ret_val

def getState():
    return REPEAT_STATE

def log(text):
    if debug:
        stdout.write(text)

def logList(mylist):
    text = ""
    try:
        for i, item in enumerate(mylist):
            text += "%-4u"%item
            if i % 8 == 7:
                text += "\n"
        if i % 8 != 7:
            text += "\n"
        if len(mylist) == 0:
            return " = []\n"
        return text
    except:
        return "None\n"

def logLists(normal_buffer, repeat_buffer, volta_buffer, flat_barlist):
    log("normal_buffer \n%s"%logList(normal_buffer))
    log("repeat_buffer \n%s"%logList(repeat_buffer))
    log("volta_buffer \n%s"%logList(volta_buffer))
    log("flat_barlist \n%s"%logList(flat_barlist))

def logAndFail(normal_buffer, repeat_buffer, volta_buffer, flat_barlist, bar_number):
    log("bar number %u\n"%bar_number)
    logLists(normal_buffer, repeat_buffer, volta_buffer, flat_barlist)
    raise Exception("Error Not implemented!")
    
def compile(bars):
    setState(NORMAL)
    flat_barlist = []
    normal_buffer = []
    repeat_buffer = []
    volta_buffer = []
    fine_bar_num = None
    ds_al_fine_bar_num = None
    segno_bar_num = None
    
    for bar_index, bar in enumerate(bars):
        bar_number = bar[KEY_NUMBER]
        log("%4u %-6s"%(bar_number, REPEAT_STATE_LABEL[getState()]))
        markers = bar.get(KEY_MARKERS, [])
        jumps = bar.get(KEY_JUMPS, [])
        if MG_SEGNO in markers and segno_bar_num is None:
            segno_bar_num = bar_number
        if MG_FINE in markers and fine_bar_num is None:
            fine_bar_num = bar_number
        if any(MG_DS_AL_FINE in j for j in jumps):
            ds_al_fine_bar_num = bar_number
            
        is_start = bool(bar.get(KEY_START_REPEAT, False))
        if is_start: log("start repeat ")
        is_volta = KEY_VOLTA in bar or bar.get(KEY_VOLTA, False)
        is_volta_bool = bool(is_volta)
        if is_volta_bool: log("volta  ")
        end_rep = bar.get(KEY_END_REPEAT, None)
        is_end = bool(end_rep)
        repeat_count = end_rep if isinstance(end_rep, int) else 2
        if is_end: log("end_repeat ")
    
        # *********************
        # *** STATE MACHINE ***
        # *********************

        state = getState()
        if state == NORMAL:
            if not is_start and not is_end and not is_volta_bool:
                normal_buffer.append(bar_number)

            elif not is_start and not is_end and is_volta_bool:
                if normal_buffer:
                    flat_barlist += normal_buffer
                    normal_buffer = []
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif not is_start and is_end and not is_volta_bool:
                log("missing_start_repeat")
                repeat_buffer = normal_buffer + [bar_number]
                normal_buffer = []
                flat_barlist += repeat_buffer * repeat_count
                repeat_buffer = []

            elif not is_start and is_end and is_volta_bool:
                log("missing_start_repeat_volta")
                repeat_buffer = normal_buffer + [bar_number]
                normal_buffer = []
                volta_buffer = [bar_number]
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = []
                volta_buffer = []

            elif is_start and not is_end and not is_volta_bool:
                if normal_buffer:
                    flat_barlist += normal_buffer
                    normal_buffer = []
                repeat_buffer = [bar_number]
                setState(REPEAT)

            elif is_start and not is_end and is_volta_bool:
                if normal_buffer:
                    flat_barlist += normal_buffer
                    normal_buffer = []
                repeat_buffer = []
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif is_start and is_end and not is_volta_bool:
                if normal_buffer:
                    flat_barlist += normal_buffer
                    normal_buffer = []
                repeat_buffer = [bar_number]
                flat_barlist += repeat_buffer * repeat_count
                repeat_buffer = []

            elif is_start and is_end and is_volta_bool:
                if normal_buffer:
                    flat_barlist += normal_buffer
                    normal_buffer = []
                repeat_buffer = []
                volta_buffer = [bar_number]
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = []
                volta_buffer = []


        elif state == REPEAT:
            if not is_start and not is_end and not is_volta_bool:
                repeat_buffer.append(bar_number)

            elif not is_start and not is_end and is_volta_bool:
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif not is_start and is_end and not is_volta_bool:
                repeat_buffer.append(bar_number)
                flat_barlist += repeat_buffer * repeat_count
                repeat_buffer = []
                setState(NORMAL)

            elif not is_start and is_end and is_volta_bool:
                if not volta_buffer:
                    volta_buffer = [bar_number]
                else:
                    volta_buffer.append(bar_number)
                
                flat_barlist += repeat_buffer + volta_buffer
                volta_buffer = []
                
                has_next_volta = (bar_index + 1 < len(bars)) and (KEY_VOLTA in bars[bar_index + 1])
                if has_next_volta:
                    setState(REPEAT)
                else:
                    repeat_buffer = []
                    setState(NORMAL)

            elif is_start and not is_end and not is_volta_bool:
                if repeat_buffer:
                    flat_barlist += repeat_buffer
                repeat_buffer = [bar_number]

            elif is_start and not is_end and is_volta_bool:
                if repeat_buffer:
                    flat_barlist += repeat_buffer
                    repeat_buffer = []
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif is_start and is_end and not is_volta_bool:
                repeat_buffer.append(bar_number)
                flat_barlist += repeat_buffer * repeat_count
                repeat_buffer = [bar_number]

            elif is_start and is_end and is_volta_bool:
                volta_buffer.append(bar_number)
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = [bar_number]
                volta_buffer = []
                
                has_next_volta = (bar_index + 1 < len(bars)) and (KEY_VOLTA in bars[bar_index + 1])
                if has_next_volta:
                    setState(REPEAT)
                else:
                    setState(REPEAT)


        elif state == VOLTA:
            if not is_start and not is_end and not is_volta_bool:
                volta_buffer.append(bar_number)

            elif not is_start and not is_end and is_volta_bool:
                flat_barlist += repeat_buffer + volta_buffer
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif not is_start and is_end and not is_volta_bool:
                volta_buffer.append(bar_number)
                flat_barlist += repeat_buffer + volta_buffer
                volta_buffer = []
                
                has_next_volta = (bar_index + 1 < len(bars)) and (KEY_VOLTA in bars[bar_index + 1])
                if has_next_volta:
                    setState(REPEAT)
                else:
                    repeat_buffer = []
                    setState(NORMAL)

            elif not is_start and is_end and is_volta_bool:
                if not volta_buffer:
                    volta_buffer = [bar_number]
                else:
                    volta_buffer.append(bar_number)
                
                # Correction du comportement des barres de fin de voltes successives
                # Si c'est la fin du bloc de reprise complet ou qu'il n'y a plus de suite de volta liée, on applique la répétition globale
                has_next_volta = (bar_index + 1 < len(bars)) and (KEY_VOLTA in bars[bar_index + 1])
                if not has_next_volta:
                    # Génération complète de toutes les reprises avec leurs voltes respectives si nécessaire
                    # Mais pour rester simple et robuste :
                    pass
                
                flat_barlist += repeat_buffer + volta_buffer
                volta_buffer = [bar_number]
                
                if has_next_volta:
                    setState(VOLTA)
                else:
                    repeat_buffer = []
                    setState(NORMAL)

            elif is_start and not is_end and not is_volta_bool:
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = [bar_number]
                volta_buffer = []
                setState(REPEAT)

            elif is_start and not is_end and is_volta_bool:
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = []
                volta_buffer = [bar_number]
                setState(VOLTA)

            elif is_start and is_end and not is_volta_bool:
                volta_buffer.append(bar_number)
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = [bar_number]
                volta_buffer = []
                setState(REPEAT)

            elif is_start and is_end and is_volta_bool:
                volta_buffer.append(bar_number)
                flat_barlist += repeat_buffer + volta_buffer
                repeat_buffer = []
                volta_buffer = [bar_number]
                setState(REPEAT)

        else:
            raise Exception("unexpected state %s"%str(getState()))

        log("\n")
        log("       normal_buffer %s\n"%str(normal_buffer))
        log("       repeat_buffer %s\n"%str(repeat_buffer))
        log("       volta_buffer %s\n"%str(volta_buffer))
        log("       flat_barlist %s\n"%str(flat_barlist))

    flat_barlist += normal_buffer + repeat_buffer + volta_buffer
    normal_buffer = []
    repeat_buffer = []
    volta_buffer = []

    if ds_al_fine_bar_num is not None and fine_bar_num is not None and segno_bar_num is not None:
        recording = False
        ds_list = []
        for b_num in flat_barlist:
            if b_num == segno_bar_num:
                recording = True
            if recording:
                ds_list.append(b_num)
            if b_num == fine_bar_num:
                break
        flat_barlist += ds_list

    log("post traitement\n")
    log("normal_buffer %s\n"%str(normal_buffer))
    log("repeat_buffer %s\n"%str(repeat_buffer))
    log("volta_buffer %s\n"%str(volta_buffer))
    log("\n%s"%logList(flat_barlist))
    return flat_barlist

def compile_grid(grid_data):
    bars = grid_data.get(KEY_BARS, [])
    return compile(bars)

def compileAndFlatenizeGrid(grid_data):
    bars = grid_data.get(KEY_BARS, [])
    bar_index_map = {bar[KEY_NUMBER]: bar for bar in bars}
    flat_bar_numbers = compile(bars)
    flat_bars = [
        bar_index_map[b_num] 
        for b_num in flat_bar_numbers 
        if b_num in bar_index_map
    ]
    return flat_bars
    
if __name__ == "__main__":

    import json
    import sys

    debug = True

    with open('grids/utest/aNightInTunisia.grid', 'r', encoding='utf-8') as f:
        grid = json.load(f)
    stdout = open("temp/report.txt", "w")
    fl = compile_grid(grid)
    print("logged in \"temp/report.txt\"")