#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from tkinter.font import Font

STRICT_FONT_MAP = {
    "default_fnt": "MuseJazzText",
    "music_fnt": "Bravura",
    "section_fnt": "gjm_realbook-webfont",
    "text_fnt": "MuseJazzText",
    "GjmRealbook": "gjm_realbook-webfont",
    "Bravura": "Bravura",
    "MuseJazzText": "MuseJazzText"
}

class BaseDriver(ABC):
    """Interface unifiée pour le rendu graphique (ReportLab & Tkinter Canvas)."""

    is_top_origin = False

    def resolve_font(self, font_name):
        return STRICT_FONT_MAP.get(font_name, font_name)

    @abstractmethod
    def draw_rect(self, x, y, w, h, stroke=1, fill=0, line_width=1.0):
        pass

    @abstractmethod
    def draw_text(self, x, y, text, font, size, anchor="sw"):
        pass

    @abstractmethod
    def draw_line(self, x1, y1, x2, y2, line_width=1.0):
        pass

    @abstractmethod
    def string_width(self, text, font, size):
        pass

    @abstractmethod
    def get_font_metrics(self, font, size):
        pass


class PdfDriver(BaseDriver):
    """Driver pour la génération PDF via ReportLab."""

    is_top_origin = False

    def __init__(self, reportlab_canvas):
        self.sheet = reportlab_canvas

    def draw_rect(self, x, y, w, h, stroke=1, fill=0, line_width=1.0):
        self.sheet.setLineWidth(line_width)
        if fill:
            self.sheet.setFillColor(colors.white)
            self.sheet.rect(x, y, w, h, stroke=stroke, fill=1)
        else:
            self.sheet.rect(x, y, w, h, stroke=stroke, fill=0)

    def draw_text(self, x, y, text, font, size, anchor="sw"):
        resolved_font = self.resolve_font(font)
        self.sheet.setFont(resolved_font, size)
        self.sheet.setFillColor(colors.black)
        self.sheet.drawString(x, y, text)

    def draw_line(self, x1, y1, x2, y2, line_width=1.0):
        self.sheet.setLineWidth(line_width)
        self.sheet.line(x1, y1, x2, y2)

    def string_width(self, text, font, size):
        resolved_font = self.resolve_font(font)
        return pdfmetrics.stringWidth(text, resolved_font, size)

    def get_font_metrics(self, font, size):
        # Approximation proportionnelle standard pour ReportLab
        return size * 0.75, size * 0.25


class TkinterDriver(BaseDriver):
    """Driver pour l'affichage interactif via Canvas Tkinter."""

    is_top_origin = True

    def __init__(self, tk_canvas):
        self.canvas = tk_canvas

    def draw_rect(self, x, y, w, h, stroke=1, fill=0, line_width=1.0):
        outline = "#333333" if stroke else ""
        fill_color = "#ffffff" if fill else ""
        return self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline=outline, width=line_width, fill=fill_color
        )

    def draw_text(self, x, y, text, font, size, anchor="sw"):
        tk_anchor_map = {
            "sw": "sw", "nw": "nw", "center": "center",
            "c": "center", "w": "w", "e": "e", "se": "se", "ne": "ne"
        }
        resolved_font = self.resolve_font(font)
        
        y_adjusted = y
        # Correction mathématique de la baseline pour l'ancre "sw" sous Tkinter
        if anchor == "sw":
            _, descent = self.get_font_metrics(font, size)
            y_adjusted = y + descent

        tk_anchor = tk_anchor_map.get(anchor, "sw")
        return self.canvas.create_text(
            x, y_adjusted, text=text, font=(resolved_font, int(size)),
            anchor=tk_anchor, fill="#000000"
        )

    def draw_line(self, x1, y1, x2, y2, line_width=1.0):
        return self.canvas.create_line(x1, y1, x2, y2, width=line_width, fill="#333333")

    def string_width(self, text, font, size):
        resolved_font = self.resolve_font(font)
        try:
            f = Font(family=resolved_font, size=int(size))
            return f.measure(text)
        except Exception:
            return len(text) * (size * 0.6)

    def get_font_metrics(self, font, size):
        resolved_font = self.resolve_font(font)
        try:
            f = Font(family=resolved_font, size=int(size))
            return f.metrics("ascent"), f.metrics("descent")
        except Exception:
            return size * 0.75, size * 0.25