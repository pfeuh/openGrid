# -*- coding: utf-8 -*-

from copy import deepcopy
from constants import *
from musicalGlyphes import *
from models import Grid, Bar
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
    
def compile(bars: list[Bar]):
    setState(NORMAL)
    flat_barlist = []
    normal_buffer = []
    repeat_buffer = []
    volta_buffer = []
    fine_bar_num = None
    ds_al_fine_bar_num = None
    segno_bar_num = None
    
    for bar_index, bar in enumerate(bars):
        bar_number = bar.number
        log("%4u %-6s"%(bar_number, REPEAT_STATE_LABEL[getState()]))
        
        markers = bar.markers
        jumps = bar.jumps
        if MG_SEGNO in markers and segno_bar_num is None:
            segno_bar_num = bar_number
        if MG_FINE in markers and fine_bar_num is None:
            fine_bar_num = bar_number
        if any(MG_DS_AL_FINE in j for j in jumps):
            ds_al_fine_bar_num = bar_number
            
        is_start = bool(bar.start_repeat)
        if is_start: log("start repeat ")
        
        is_volta_bool = bool(bar.volta)
        if is_volta_bool: log("volta  ")
        
        end_rep = bar.end_repeat
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
                
                has_next_volta = (bar_index + 1 < len(bars)) and bool(bars[bar_index + 1].volta)
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
                
                has_next_volta = (bar_index + 1 < len(bars)) and bool(bars[bar_index + 1].volta)
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
                
                has_next_volta = (bar_index + 1 < len(bars)) and bool(bars[bar_index + 1].volta)
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
                
                flat_barlist += repeat_buffer + volta_buffer
                volta_buffer = [bar_number]
                
                has_next_volta = (bar_index + 1 < len(bars)) and bool(bars[bar_index + 1].volta)
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
        log("    normal_buffer %s\n"%str(normal_buffer))
        log("    repeat_buffer %s\n"%str(repeat_buffer))
        log("    volta_buffer %s\n"%str(volta_buffer))
        log("    flat_barlist %s\n"%str(flat_barlist))

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

    return flat_barlist

def compile_grid(grid: Grid) -> list[int]:
    """Compile la grille (objet Grid strict) et retourne les numéros de mesures."""
    return compile(grid.bars)

def compileAndFlatenizeGrid(grid: Grid) -> Grid:
    """Prend un objet Grid strict, le compile et retourne un NOUVEL objet Grid aplati."""
    bar_index_map = {bar.number: bar for bar in grid.bars}
    flat_bar_numbers = compile(grid.bars)
    
    flat_grid = Grid(header=deepcopy(grid.header))
    for new_num, b_num in enumerate(flat_bar_numbers, start=1):
        if b_num in bar_index_map:
            original_bar = bar_index_map[b_num]
            bar_data = original_bar.to_dict()
            bar_data[KEY_NUMBER] = new_num
            flat_grid.add_bar(Bar.from_dict(bar_data))
            
    return flat_grid

if __name__ == "__main__":
    import json
    import sys

    debug = True
    grid_obj = Grid.load('grids/utest/aNightInTunisia.grid')
    stdout = open("temp/report.txt", "w")
    fl = compile_grid(grid_obj)
    print("logged in \"temp/report.txt\"")