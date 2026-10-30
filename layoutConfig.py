#!/usr/bin/python
# -*- coding: utf-8 -*-

# --- Dimensions de la page (Standard A4 en points) ---
PAGE_WIDTH = 595.27
PAGE_HEIGHT = 841.89

# --- Marges et En-tête optimisés pour 10 lignes ---
MARGIN_LEFT = 30
MARGIN_RIGHT = 30
MARGIN_TOP = 25
MARGIN_BOTTOM = 25
HEADER_HEIGHT = 45  # Espace réservé en haut pour le titre et le compositeur

# --- Géométrie rigoureuse (Cible : Header + exactement 10 lignes sur la page 1) ---
# Hauteur utile = 841.89 - 25 (top) - 25 (bottom) - 45 (header) = ~746 points.
# Pour 10 lignes, chaque ligne (CELL_H + SPACING_Y) doit faire environ 72 points max.
CELL_W = 120
CELL_H = 50       # Hauteur idéale d'une mesure (plus équilibrée, ni trop haute, ni trop basse)
MAX_COLS = 4
SPACING_X = 15
SPACING_Y = 22    # Espacement vertical serré mais parfaitement lisible (50 + 22 = 72 * 10 = 720 < 746)