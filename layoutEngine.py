#!/usr/bin/python
# -*- coding: utf-8 -*-

from layoutConfig import (
    PAGE_HEIGHT, MARGIN_LEFT, MARGIN_TOP, MARGIN_BOTTOM,
    HEADER_HEIGHT, CELL_W, CELL_H, MAX_COLS, SPACING_X, SPACING_Y
)

def get_pdf_rows_per_page():
    """Calcule le nombre de lignes tenant sur une page PDF A4."""
    usable_height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - HEADER_HEIGHT
    rows = int(usable_height // (CELL_H + SPACING_Y))
    return max(rows, 1)

def compute_pdf_layout(grid_obj):
    """
    Générateur pour le PDF : calcule les positions et détecte les sauts de page.
    Yields: (idx, bar, x, y, col, is_new_page, page_number)
    """
    bars = grid_obj.bars
    rows_per_page = get_pdf_rows_per_page()
    page_number = 1
    
    start_y = PAGE_HEIGHT - MARGIN_TOP - HEADER_HEIGHT

    for idx, bar in enumerate(bars):
        col = idx % MAX_COLS
        global_row = idx // MAX_COLS
        row_on_page = global_row % rows_per_page

        is_new_page = False
        if idx > 0 and row_on_page == 0 and col == 0:
            page_number += 1
            is_new_page = True

        y = start_y - (row_on_page + 1) * (CELL_H + SPACING_Y) + SPACING_Y
        x = MARGIN_LEFT + col * (CELL_W + SPACING_X)

        yield idx, bar, x, y, col, is_new_page, page_number

def compute_tkinter_layout(grid_obj):
    """
    Générateur pour Tkinter : calcule les positions en flux continu vertical.
    Yields: (idx, bar, x, y, col)
    """
    bars = grid_obj.bars
    start_y = MARGIN_TOP + HEADER_HEIGHT

    for idx, bar in enumerate(bars):
        col = idx % MAX_COLS
        row = idx // MAX_COLS

        x = MARGIN_LEFT + col * (CELL_W + SPACING_X)
        y = start_y + row * (CELL_H + SPACING_Y)

        yield idx, bar, x, y, col