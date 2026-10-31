#!/usr/bin/python
# -*- coding: utf-8 -*-

import tkinter as tk
from graphicsDriver import TkinterDriver
from barDrawing import BarDrawing
from layoutConfig import (
    PAGE_WIDTH, MARGIN_LEFT, MARGIN_TOP, HEADER_HEIGHT,
    CELL_W, CELL_H, MAX_COLS, SPACING_Y
)
from layoutEngine import compute_tkinter_layout

class VectorialGridCanvas:
    """Éditeur graphique vectoriel interactif basé sur un Canvas Tkinter."""

    def __init__(self, parent, on_measure_edit_callback=None):
        self.parent = parent
        self.on_measure_edit_callback = on_measure_edit_callback or self.edit_measure
        self.grid = None
        self.edited_bar = None  # Mémorisation de la mesure active pour le redessin persistant

        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.frame, width=PAGE_WIDTH, bg="#f5f5f5", highlightthickness=0)
        self.v_scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        
        self.canvas.config(yscrollcommand=self.v_scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=False)
        self.v_scrollbar.pack(side="right", fill="y")

        self.driver = TkinterDriver(self.canvas)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel_linux)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel_linux)

        self.measure_rects = {}

    def load_grid(self, grid_obj):
        self.grid = grid_obj
        self.edited_bar = None
        self.redraw()

    def set_bar_background(self, bar_obj, color):
        """Modifie la couleur de fond du rectangle associé à une mesure (Bar) sur le canvas et mémorise l'état."""
        self.edited_bar = bar_obj if color else None
        for rect_id, bar in self.measure_rects.items():
            if bar is bar_obj:
                try:
                    fill_val = color if color else ""
                    self.canvas.itemconfigure(rect_id, fill=fill_val)
                except Exception:
                    pass
                break

    def redraw(self):
        self.canvas.delete("all")
        self.measure_rects.clear()

        if not self.grid:
            return

        header = getattr(self.grid, 'header', None)
        title = header.title if header and header.title else "Grille sans titre"
        composer = header.composer if header and header.composer else ""

        self.driver.draw_text(MARGIN_LEFT, MARGIN_TOP + 15, title, "default_fnt", 16, anchor="sw")
        if composer:
            right_x = PAGE_WIDTH - MARGIN_LEFT - 9
            comp_width = self.driver.string_width(composer, "default_fnt", 10)
            self.driver.draw_text(right_x - comp_width, MARGIN_TOP + 15, composer, "default_fnt", 10, anchor="sw")

        bars = self.grid.bars
        global_prev_chords = None

        total_rows = (len(bars) + MAX_COLS - 1) // MAX_COLS
        start_y = MARGIN_TOP + HEADER_HEIGHT

        for idx, bar, x, y, col in compute_tkinter_layout(self.grid):
            bar_drawer = BarDrawing(x, y, CELL_W, CELL_H, self.driver, bar_data=bar)

            rect_id = bar_drawer.rect_id
            if rect_id:
                self.measure_rects[rect_id] = bar
                # Restauration automatique du fond jaune si c'est la mesure active lors d'un redraw
                if bar is self.edited_bar:
                    try:
                        self.canvas.itemconfigure(rect_id, fill="#FFF2CC")
                    except Exception:
                        pass

            if col == 0:
                num_y = y + CELL_H - 4
                self.driver.draw_text(x + 4, num_y, str(bar.number), "default_fnt", 8, anchor="sw")

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

        total_height = start_y + total_rows * (CELL_H + SPACING_Y) + 50
        self.canvas.config(scrollregion=(0, 0, PAGE_WIDTH, total_height))

    def edit_measure(self, bar_obj):
        """Méthode par défaut si aucun callback externe n'est fourni."""
        if self.on_measure_edit_callback and self.on_measure_edit_callback != self.edit_measure:
            self.on_measure_edit_callback(bar_obj)

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mouse_wheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def on_canvas_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        clicked_items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
        
        for item in clicked_items:
            if item in self.measure_rects:
                bar_obj = self.measure_rects[item]
                if self.on_measure_edit_callback:
                    self.on_measure_edit_callback(bar_obj)
                break