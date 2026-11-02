#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../openGrid"))
)
import models
from fontLoader import register_project_fonts
from layoutConfig import MAX_COLS
from musicalGlyphes import GLYPH_CONFIGS, ITEMS


def gridToExcel(fname_input, fname_output):
  # 0. Enregistrement/Vérification des polices du projet
  register_project_fonts()

  # 1. Chargement de la grille via models.py
  grid = models.Grid.load(fname_input)
  header = grid.header
  bars = grid.bars

  # 2. Création du classeur Excel
  wb = openpyxl.Workbook()
  ws = wb.active
  ws.title = "Grille d'accords"
  ws.views.sheetView[0].showGridLines = True

  # --- Configuration de la zone d'impression (Portrait, 1 page en largeur x 1 page en hauteur) ---
  ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
  ws.page_setup.paperSize = ws.PAPERSIZE_A4
  ws.page_setup.fitToWidth = 1
  ws.page_setup.fitToHeight = 1
  ws.sheet_properties.pageSetUpPr.fitToPage = True

  # --- Styles Globaux (Strictement en Noir) ---
  font_title = Font(name="MuseJazzText", size=24, bold=True, color="000000")
  font_composer = Font(name="MuseJazzText", size=14, italic=True, color="000000")
  font_meta = Font(name="MuseJazzText", size=14, color="000000")

  # Police pour l'étage du haut (sections, repères, sauts, voltas) en noir
  font_top = Font(name="MuseJazzText", size=15, bold=True, color="000000")

  # --- InlineFonts pour le Rich Text de l'étage du bas (sz=26) ---
  inline_chord = InlineFont(rFont="MuseJazzText", sz=26, b=True, color="000000")

  # Pas d'encadrement par défaut pour la cellule du haut
  border_top_cell = Border(
      left=Side(style=None),
      right=Side(style=None),
      top=Side(style=None),
      bottom=Side(style=None),
  )

  # Bordure en forme de demi-carré (côté gauche et supérieur) pour les voltas
  border_volta_cell = Border(
      left=Side(style="medium", color="000000"),
      right=Side(style=None),
      top=Side(style="medium", color="000000"),
      bottom=Side(style=None),
  )

  # Encadrement noir, épais ("medium") et complet pour la cellule du bas
  border_bottom_cell = Border(
      left=Side(style="medium", color="000000"),
      right=Side(style="medium", color="000000"),
      top=Side(style="medium", color="000000"),
      bottom=Side(style="medium", color="000000"),
  )

  # --- En-tête du document ---
  if header and header.title:
    title_str = header.title
  else:
    title_str = os.path.splitext(os.path.basename(fname_input))[0]

  ws.merge_cells(
      start_row=1, start_column=1, end_row=1, end_column=MAX_COLS
  )
  title_cell = ws["A1"]
  title_cell.value = title_str
  title_cell.font = font_title
  title_cell.alignment = Alignment(horizontal="center", vertical="center")
  ws.row_dimensions[1].height = 40

  composer_str = header.composer if header and header.composer else ""
  if composer_str:
    ws.merge_cells(
        start_row=2, start_column=1, end_row=2, end_column=MAX_COLS
    )
    comp_cell = ws["A2"]
    comp_cell.value = composer_str
    comp_cell.font = font_composer
    comp_cell.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[2].height = 24
    meta_row_idx = 3
  else:
    meta_row_idx = 2

  meta_parts = []
  if header.style:
    meta_parts.append(f"Style: {header.style}")
  if header.bpm:
    meta_parts.append(f"BPM: {header.bpm}")
  if header.timesig:
    meta_parts.append(f"Mesure: {header.timesig}")

  if meta_parts:
    ws.merge_cells(
        start_row=meta_row_idx,
        start_column=1,
        end_row=meta_row_idx,
        end_column=MAX_COLS,
    )
    meta_cell = ws.cell(row=meta_row_idx, column=1, value="    ".join(meta_parts))
    meta_cell.font = font_meta
    meta_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[meta_row_idx].height = 24

  # --- Découpage des mesures en lignes (paquets de MAX_COLS) ---
  bar_lines = []
  current_line = []

  for bar in bars:
    current_line.append(bar)
    if bar.line_break or len(current_line) == MAX_COLS:
      bar_lines.append(current_line)
      current_line = []
  if current_line:
    bar_lines.append(current_line)

  global_prev_chords = None

  # --- Construction de la grille à deux étages ---
  for line_idx, line_bars in enumerate(bar_lines):
    row_top_data = []
    row_bottom_data = []

    for bar in line_bars:
      # --- 1. ÉTAGE SUPÉRIEUR (Sections, Markers, Jumps, Volta) ---
      top_extras = []
      if bar.sections:
        top_extras.append(f"[{', '.join(bar.sections)}]")
      if bar.volta:
        top_extras.append(bar.volta)

      for m in bar.markers:
        glyph_key = ITEMS.get(m.lower(), m)
        if glyph_key in GLYPH_CONFIGS:
          top_extras.append(GLYPH_CONFIGS[glyph_key].get("content", m))
        else:
          top_extras.append(m)

      for j in bar.jumps:
        glyph_key = ITEMS.get(j.lower(), j)
        if glyph_key in GLYPH_CONFIGS:
          top_extras.append(GLYPH_CONFIGS[glyph_key].get("content", j))
        else:
          top_extras.append(j)

      row_top_data.append("  ".join(top_extras) if top_extras else "")

      # --- 2. ÉTAGE INFÉRIEUR (Start repeat ||:, Chords, End repeat :||) ---
      chords = getattr(bar, "chords", [])
      cleaned_chords = [
          c.split("@")[0] if isinstance(c, str) and "@" in c else c
          for c in chords
      ]

      use_simile = False
      if (
          not cleaned_chords
          and global_prev_chords is not None
          and len(global_prev_chords) > 0
      ):
        cleaned_chords = global_prev_chords
        use_simile = True
      elif (
          cleaned_chords
          and global_prev_chords is not None
          and cleaned_chords == global_prev_chords
      ):
        use_simile = True

      if cleaned_chords:
        global_prev_chords = cleaned_chords

      if use_simile:
        chords_display = GLYPH_CONFIGS.get("MG_IDEM", {}).get(
            "content", "\U0001D10E"
        )
      else:
        chords_display = "   ".join(cleaned_chords) if cleaned_chords else "—"

      if bar.start_repeat and bar.end_repeat:
        end_str = ":||"
        if bar.end_repeat > 1:
          end_str += f" (x{bar.end_repeat})"
        full_cell_str = f"||:   {chords_display}   {end_str}"
      elif bar.start_repeat:
        full_cell_str = f"||:   {chords_display}"
      elif bar.end_repeat:
        end_str = ":||"
        if bar.end_repeat > 1:
          end_str += f" (x{bar.end_repeat})"
        full_cell_str = f"{chords_display}   {end_str}"
      else:
        full_cell_str = chords_display

      rich_bottom = CellRichText([TextBlock(inline_chord, full_cell_str)])
      row_bottom_data.append(rich_bottom)

    while len(row_top_data) < MAX_COLS:
      row_top_data.append("")
      row_bottom_data.append("")

    # Écriture de l'étage supérieur
    ws.append(row_top_data)
    top_row_idx = ws.max_row
    ws.row_dimensions[top_row_idx].height = 20

    for col_idx in range(1, MAX_COLS + 1):
      cell = ws.cell(row=top_row_idx, column=col_idx)
      cell.font = font_top

      bar = line_bars[col_idx - 1] if (col_idx - 1) < len(line_bars) else None

      # Si la mesure contient un saut (comme To Coda ou DS al Coda), on aligne à droite
      is_jump_bar = bar and (bar.jumps or any("coda" in j.lower() for j in bar.jumps))
      
      if is_jump_bar:
        cell.alignment = Alignment(horizontal="right", vertical="center", indent=1)
      else:
        cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)

      if bar and bar.volta:
        cell.border = border_volta_cell
      else:
        cell.border = border_top_cell

    # Écriture de l'étage inférieur avec des bordures noires et épaisses
    ws.append(row_bottom_data)
    bottom_row_idx = ws.max_row
    ws.row_dimensions[bottom_row_idx].height = 36

    for col_idx in range(1, MAX_COLS + 1):
      cell = ws.cell(row=bottom_row_idx, column=col_idx)
      cell.alignment = Alignment(horizontal="center", vertical="bottom")
      cell.border = border_bottom_cell

    # --- Insertion d'une ligne vide très fine entre chaque système de barres ---
    if line_idx < len(bar_lines) - 1:
      spacer_data = [""] * MAX_COLS
      ws.append(spacer_data)
      spacer_row_idx = ws.max_row
      ws.row_dimensions[spacer_row_idx].height = 6
      for col_idx in range(1, MAX_COLS + 1):
        ws.cell(row=spacer_row_idx, column=col_idx).border = Border(
            left=Side(style=None),
            right=Side(style=None),
            top=Side(style=None),
            bottom=Side(style=None),
        )

  # Largeur homogène des colonnes et définition de la zone d'impression
  for col_idx in range(1, MAX_COLS + 1):
    col_letter = get_column_letter(col_idx)
    ws.column_dimensions[col_letter].width = 24

  max_col_letter = get_column_letter(MAX_COLS)
  ws.print_area = f"A1:{max_col_letter}{ws.max_row}"

  wb.save(fname_output)
  print(f"Grille Excel générée avec succès : {fname_output}")


if __name__ == "__main__":
  gridToExcel(
      "suspense_sur_le_bateau-mouche.grid",
      "suspense_sur_le_bateau-mouche.xlsx",
  )