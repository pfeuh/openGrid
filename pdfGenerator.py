#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from graphicsDriver import PdfDriver
from barDrawing import BarDrawing
from layoutConfig import (
    PAGE_WIDTH, PAGE_HEIGHT, MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, CELL_W, CELL_H
)
from layoutEngine import compute_pdf_layout

def register_custom_fonts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "font")
    if not os.path.isdir(fonts_dir):
        fonts_dir = os.path.join(base_dir, "fonts")
    
    for font_name, filename in [
        ("MuseJazzText", "MuseJazzText.ttf"),
        ("Bravura", "Bravura.ttf"),
        ("gjm_realbook-webfont", "gjm_realbook-webfont.ttf")
    ]:
        font_path = os.path.join(fonts_dir, filename)
        if os.path.isfile(font_path):
            try:
                pdfmetrics.getFont(font_name)
            except KeyError:
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception:
                    pass

def gridToPdf(grid_obj, output_pdf_path):
    register_custom_fonts()

    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    driver = PdfDriver(c)

    header = getattr(grid_obj, 'header', None)
    title = header.title if header and header.title else "Grille sans titre"
    composer = header.composer if header and header.composer else ""

    page_number = 1

    def draw_page_decorations(is_first_page):
        nonlocal page_number
        if is_first_page:
            header_y = PAGE_HEIGHT - MARGIN_TOP - 15
            driver.draw_text(MARGIN_LEFT, header_y, title, "default_fnt", 16, anchor="sw")
            if composer:
                right_x = PAGE_WIDTH - MARGIN_RIGHT - 15
                comp_width = driver.string_width(composer, "default_fnt", 10)
                driver.draw_text(right_x - comp_width, header_y, composer, "default_fnt", 10, anchor="sw")
        
        driver.draw_text(MARGIN_LEFT, 20, title, "default_fnt", 8, anchor="sw")
        driver.draw_text(PAGE_WIDTH / 2, 20, f"- {page_number} -", "default_fnt", 8, anchor="center")

    draw_page_decorations(is_first_page=True)
    global_prev_chords = None

    for idx, bar, x, y, col, is_new_page, current_page_num in compute_pdf_layout(grid_obj):
        if is_new_page:
            c.showPage()
            page_number = current_page_num
            draw_page_decorations(is_first_page=False)

        bar_drawer = BarDrawing(x, y, CELL_W, CELL_H, driver, bar_data=bar)

        if col == 0:
            driver.draw_text(x + 4, y + 4, str(bar.number), "default_fnt", 8, anchor="sw")

        chords = getattr(bar, 'chords', [])
        cleaned_chords = [c.split('@')[0] if isinstance(c, str) and '@' in c else c for c in chords]

        use_simile = False
        if not cleaned_chords and global_prev_chords is not None and len(global_prev_chords) > 0:
            cleaned_chords = global_prev_chords
            use_simile = True
        elif cleaned_chords and global_prev_chords is not None and cleaned_chords == global_prev_chords:
            use_simile = True

        if use_simile:
            bar_drawer.write("\U0001D10E", "Bravura", 18, anchor="center")
        elif chords:
            bar_drawer.write_chords(chords)

        if cleaned_chords:
            global_prev_chords = cleaned_chords

    c.showPage()
    c.save()