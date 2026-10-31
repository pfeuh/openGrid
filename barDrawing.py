#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from constants import (
    KEY_SECTIONS, KEY_VOLTA, KEY_START_REPEAT, KEY_END_REPEAT,
    TAG_SECTION, TAG_VOLTA, TAG_REPEAT_BAR
)
from musicalGlyphes import *

CHAR_SHARP = "\ue10c"
CHAR_FLAT = "\ue10d"
CHORD_FONT_SIZE = 18
CHORD_COMPACT_SIZE = 12

GLYPH_DIM = "\ue18e"
GLYPH_M7B5_MODIFIER = "\ue18f"
GLYPH_MAJ7 = "\ue18a"

COLOR_GLYPH_MAP = {
    "dim": GLYPH_DIM,
    "m7b5": GLYPH_M7B5_MODIFIER,
    "maj7": GLYPH_MAJ7,
    "M7": GLYPH_MAJ7,
    "7M": GLYPH_MAJ7,
    "7maj": GLYPH_MAJ7
}

class BarDrawing:
    def __init__(self, x, y, w, h, driver, no_rect=False, bar_data=None, bg_color=None):
        self.__x = x
        self.__y = y
        self.__w = w
        self.__h = h
        self.__driver = driver
        self.rect_id = None
        
        self.__cursors = {
            'nw': 0, 'n': 0, 'ne': 0,
            'w': 0,  'center': 0, 'c': 0, 'e': 0,
            'sw': 0, 's': 0, 'se': 0,
            'above_left': 0, 'above_center': 0, 'above_right': 0
        }
        
        if self.__driver is not None and not no_rect:
            # On passe fill=bg_color si fourni, sinon style par défaut
            fill_val = bg_color if bg_color is not None else 1
            self.rect_id = self.__driver.draw_rect(x, y, w, h, stroke=1, fill=fill_val, line_width=1.0)

        if bar_data:
            self.render_bar_data(bar_data)

    def set_background_color(self, color):
        """Modifie la couleur de fond du rectangle de la mesure."""
        if self.__driver is not None and self.rect_id is not None:
            if hasattr(self.__driver, 'set_rect_color'):
                self.__driver.set_rect_color(self.rect_id, fill=color)
            elif hasattr(self.__driver, 'itemconfigure'): # Compatibilité directe Canvas Tkinter si besoin
                self.__driver.itemconfigure(self.rect_id, fill=color)

    def render_bar_data(self, bar):
        if not bar:
            return
        
        # 1. Sections (ex: "A", "B", "Interlude")
        sections = getattr(bar, KEY_SECTIONS, [])
        if sections:
            self.render_glyph_tag(TAG_SECTION, " / ".join(sections))

        # 2. Voltas (ex: "1.", "2.", "3.")
        volta = getattr(bar, KEY_VOLTA, '')
        if volta:
            self.render_glyph_tag(TAG_VOLTA, volta)

        # 3. Barres de répétition début/fin
        if getattr(bar, KEY_START_REPEAT, False):
            self.render_glyph_tag(KEY_START_REPEAT)
            
        end_repeat = getattr(bar, KEY_END_REPEAT, None)
        if end_repeat and (end_repeat is True or (isinstance(end_repeat, int) and end_repeat > 0)):
            self.render_glyph_tag(KEY_END_REPEAT)

        # 4. Marqueurs (ex: MG_SEGNO, MG_FINE, MG_CODA)
        for marker in getattr(bar, 'markers', []):
            self.render_glyph_tag(marker)

        # 5. Sauts (ex: MG_GOTO_SIGNO)
        for jump in getattr(bar, 'jumps', []):
            self.render_glyph_tag(jump)

        # 6. Signature rythmique (ex: 4/4, 3/4...)
        timesig = getattr(bar, 'timesig', '')
        if timesig:
            self.draw_timesig(timesig)

    def write(self, text, font, size, anchor="center", y_offset=0):
        if self.__driver is None or not text:
            return

        text_width = self.__driver.string_width(text, font, size)
        text_height = size * 0.7  

        anchor = anchor.lower()
        if anchor == 'c':
            anchor = 'center'

        offset = self.__cursors.get(anchor, 0)

        if anchor in ('center', 'above_center', 'c'):
            tx = self.__x + (self.__w - text_width) / 2.0 + offset
        elif anchor in ('e', 'ne', 'se', 'above_right'): 
            tx = self.__x + self.__w - text_width - offset - 4
        elif anchor == 'sw':
            tx = self.__x + 2 + offset
        else:  
            tx = self.__x + offset + 4

        is_tkinter = getattr(self.__driver, 'is_top_origin', False)

        if anchor.startswith('above_') or anchor == 'above':
            ty = (self.__y - 2 + y_offset) if is_tkinter else (self.__y + self.__h + 6 + y_offset)
        elif anchor == 'center':
            drop = (size * 0.4) if (is_tkinter and text == "\U0001D10E") else 0
            ty = self.__y + (self.__h - text_height) / 2.0 + y_offset + drop
        elif anchor == 'sw':
            ty = (self.__y + self.__h - 4 + y_offset) if is_tkinter else (self.__y + 2 + y_offset)
        elif 'n' in anchor and 's' not in anchor: 
            ty = (self.__y + 4 + y_offset) if is_tkinter else (self.__y + self.__h - text_height - 4 + y_offset)
        elif 's' in anchor and 'n' not in anchor: 
            ty = (self.__y + self.__h - text_height - 4 + y_offset) if is_tkinter else (self.__y + 4 + y_offset)
        else:
            ty = self.__y + (self.__h - text_height) / 2.0 + y_offset

        self.__driver.draw_text(tx, ty, text, font, size, anchor="sw")
        if anchor in self.__cursors:
            self.__cursors[anchor] += text_width + 4

    def draw_cartouche_label(self, text):
        if self.__driver is None or not text:
            return

        size = 14
        text_width = self.__driver.string_width(text, "text_fnt", size)
        text_height = size * 0.7

        offset = self.__cursors.get('above_left', 0)
        tx = self.__x + offset + 2
        
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)
        ty = (self.__y - 4) if is_tkinter else (self.__y + self.__h + 4)

        padding_x = 5
        padding_y = 3
        box_w = text_width + (padding_x * 2)
        box_h = text_height + (padding_y * 2)
        box_y = (ty - box_h) if is_tkinter else (ty - 2)

        self.__driver.draw_rect(tx, box_y, box_w, box_h, stroke=1, fill=0, line_width=0.8)
        self.__driver.draw_text(tx + padding_x, ty + 1, text, "text_fnt", size, anchor="sw")
        self.__cursors['above_left'] += box_w + 4

    def draw_jump(self, text):
        if self.__driver is None or not text:
            return
        self.write(text, "text_fnt", 11, "above_right")

    def draw_to_coda(self):
        if self.__driver is None:
            return
        
        coda_config = GLYPH_CONFIGS.get("MG_CODA", {"content": "\U0001D10C", "font": "Bravura", "size": 13})
        coda_char = coda_config["content"]
        coda_font = coda_config["font"]
        
        text_font = "text_fnt"
        text_size = 11
        coda_size = int(13 * 0.8)

        w_to = self.__driver.string_width("To ", text_font, text_size)
        w_coda = self.__driver.string_width(coda_char, coda_font, coda_size)
        total_width = w_to + w_coda

        offset = self.__cursors.get('above_right', 0)
        tx = self.__x + self.__w - total_width - offset - 4
        
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)
        ty = (self.__y - 2) if is_tkinter else (self.__y + self.__h + 6)

        self.__driver.draw_text(tx, ty, "To ", text_font, text_size, anchor="sw")
        self.__driver.draw_text(tx + w_to, ty, coda_char, coda_font, coda_size, anchor="sw")
        
        self.__cursors['above_right'] += total_width + 4

    def draw_timesig(self, timesig):
        base_x = self.__x + 2
        offset = self.__cursors.get('w', 0)
        tx = base_x + offset
        
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)

        if timesig in TIME_SIGNATURE_GLYPHS:
            glyph = TIME_SIGNATURE_GLYPHS[timesig]
            size = 20  
            if is_tkinter:
                size_rep = int(self.__h * 0.45)
                text_height = size_rep * 0.7
                ty = self.__y + (self.__h / 2.0) + (text_height / 2.0)
            else:
                ty = self.__y + (self.__h - (size * 0.7)) / 2.0 - 2
            self.__driver.draw_text(tx, ty, glyph, "Bravura", size, anchor="sw")
            glyph_width = self.__driver.string_width(glyph, "Bravura", size)
            self.__cursors['w'] = offset + glyph_width + 4
        else:
            parts = timesig.split('/')
            if len(parts) == 2:
                num, den = parts[0], parts[1]
                sub_size = 11
                
                if is_tkinter:
                    size_rep = int(self.__h * 0.45)
                    text_height = size_rep * 0.7
                    base_ty = self.__y + (self.__h / 2.0) + (text_height / 2.0) - sub_size
                    self.__driver.draw_text(tx, base_ty, num, "text_fnt", sub_size, anchor="sw")
                    self.__driver.draw_text(tx, base_ty + sub_size, den, "text_fnt", sub_size, anchor="sw")
                else:
                    center_y = self.__y + self.__h / 2.0
                    self.__driver.draw_text(tx, center_y - 2, num, "text_fnt", sub_size, anchor="sw")
                    self.__driver.draw_text(tx, center_y + sub_size - 2, den, "text_fnt", sub_size, anchor="sw")
                
                num_w = self.__driver.string_width(num, "text_fnt", sub_size)
                den_w = self.__driver.string_width(den, "text_fnt", sub_size)
                max_w = max(num_w, den_w)
                self.__cursors['w'] = offset + max_w + 4
            else:
                self.write(timesig, "text_fnt", 11, "w")

    def draw_volta(self, volta_text, config):
        if self.__driver is None or not volta_text:
            return

        size = config.get("size", 13)
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)

        text = str(volta_text).strip()
        if not text.endswith("."):
            text += "."

        if is_tkinter:
            line_start_y = self.__y
            text_y = self.__y - 3            
            bracket_y = text_y - size - 2    
        else:
            line_start_y = self.__y + self.__h
            text_y = self.__y + self.__h + 5   
            bracket_y = text_y + size + 2    

        self.__driver.draw_line(self.__x, line_start_y, self.__x, bracket_y, line_width=1.2)         
        self.__driver.draw_line(self.__x, bracket_y, self.__x + self.__w, bracket_y, line_width=1.2) 
        
        self.__driver.draw_text(self.__x + 6, text_y, text, config.get("font", "text_fnt"), size, anchor="sw")

    def draw_repeat_bar(self, config):
        if self.__driver is None:
            return

        font = config.get("font", "Bravura")
        content = config.get("content", "")
        side = config.get("side", "left")
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)

        if is_tkinter:
            size = int(self.__h * 0.45)
            text_height = size * 0.7
            ty = self.__y + (self.__h / 2.0) + (text_height / 2.0)
        else:
            size = config.get("size", 26)
            text_height = size * 0.7
            ty = self.__y + (self.__h - text_height) / 2.0 - 4

        if side == "left":
            base_x = self.__x + 2
            offset = self.__cursors.get('w', 0)
            tx = base_x + offset
            text_width = self.__driver.string_width(content, font, size)
            self.__cursors['w'] = offset + text_width + 4
        else:
            text_width = self.__driver.string_width(content, font, size)
            tx = self.__x + self.__w - text_width + 1  

        self.__driver.draw_text(tx, ty, content, font, size, anchor="sw")

    def parse_chord(self, chord_str):
        if not chord_str:
            return None, None, None

        pattern = r"^([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?$"
        match = re.match(pattern, chord_str.strip())
        if match:
            return match.group(1), match.group(2), match.group(3)
        
        return chord_str, "", None

    def _format_part(self, part_str):
        if not part_str:
            return ""
        return part_str.replace("#", CHAR_SHARP).replace("b", CHAR_FLAT)

    def _format_color(self, color_str):
        if not color_str:
            return ""
        if color_str in COLOR_GLYPH_MAP:
            return COLOR_GLYPH_MAP[color_str]
        return self._format_part(color_str)

    def render_glyph_tag(self, tag, custom_text=None):
        if tag == TAG_SECTION and custom_text:
            self.draw_cartouche_label(custom_text)
            return

        if tag == "MG_TO_CODA" or str(tag).upper() == "MG_TO_CODA":
            self.draw_to_coda()
            return

        if (tag and tag.startswith(TAG_VOLTA)) or (custom_text and str(custom_text).strip().endswith(".")):
            config = GLYPH_CONFIGS.get(MG_VOLTA, {"type": TAG_VOLTA, "size": 13, "font": "text_fnt"})
            self.draw_volta(custom_text or tag, config)
            return

        if tag in ITEMS:
            tag = ITEMS[tag]

        if not tag:
            return
        
        config = GLYPH_CONFIGS.get(tag)
        if not config:
            print(f"[ERREUR BAR_DRAWING] Aucune configuration graphique trouvée pour le tag/glyphe : '{tag}' (custom_text: {custom_text})")
            return
        
        if config.get("type") == TAG_VOLTA:
            self.draw_volta(custom_text, config)
            return

        if config.get("type") == TAG_REPEAT_BAR:
            self.draw_repeat_bar(config)
            return

        content = config["content"]
        font = config["font"]
        size = config["size"]
        row = config["row"]
        align = config["align"]
        y_offset = config.get("y_offset", 0)

        if tag == "coda" or tag == "MG_CODA":
            size = int(size * 0.8)

        if row == "above":
            anchor = "above_left" if align == "left" else ("above_right" if align == "right" else "above_center")
        elif row == "inside":
            anchor = "w" if align == "left" else ("e" if align == "right" else "center")
        else:
            anchor = "center"

        self.write(content, font, size, anchor, y_offset=y_offset)

    def _draw_single_chord(self, chord_str, center_x, center_y, font_size):
        resolved_font = "text_fnt"
        sup_size = int(font_size * 0.75)
        
        root, color, bass = self.parse_chord(chord_str)
        f_root = self._format_part(root)
        f_color = self._format_color(color)
        f_bass = self._format_part(bass)
        
        r_w = self.__driver.string_width(f_root, resolved_font, font_size)
        if f_color in ("69", "6/9"):
            c_w = self.__driver.string_width("6", resolved_font, int(sup_size * 0.85))
        else:
            c_w = self.__driver.string_width(f_color, resolved_font, sup_size) if f_color else 0
        b_w = self.__driver.string_width(f"/{f_bass}", resolved_font, font_size) if f_bass else 0
        total_w = r_w + c_w + b_w
        
        start_x = center_x - (total_w / 2.0)
        text_height = font_size * 0.7
        
        base_y = center_y - (text_height / 2.0)
        
        is_tkinter = getattr(self.__driver, 'is_top_origin', False)
        if is_tkinter:
            ascent, _ = self.__driver.get_font_metrics(resolved_font, font_size)
            base_y = center_y + (ascent / 2.0)

        sup_y = base_y - (font_size * 0.28) if is_tkinter else base_y + (font_size * 0.28)
        
        current_x = start_x
        self.__driver.draw_text(current_x, base_y, f_root, resolved_font, font_size, anchor="sw")
        current_x += r_w
        
        if f_color:
            if f_color in ("69", "6/9"):
                half_sup = sup_size * 0.52
                if is_tkinter:
                    top_y = sup_y - half_sup * 0.3
                    bot_y = sup_y + half_sup * 0.7
                else:
                    top_y = sup_y + half_sup * 0.3
                    bot_y = sup_y - half_sup * 0.7
                self.__driver.draw_text(current_x, top_y, "6", resolved_font, int(sup_size * 0.85), anchor="sw")
                self.__driver.draw_text(current_x, bot_y, "9", resolved_font, int(sup_size * 0.85), anchor="sw")
                current_x += self.__driver.string_width("6", resolved_font, int(sup_size * 0.85))
            else:
                self.__driver.draw_text(current_x, sup_y, f_color, resolved_font, sup_size, anchor="sw")
                current_x += c_w
                
        if f_bass:
            bass_str = f"/{f_bass}"
            self.__driver.draw_text(current_x, base_y, bass_str, resolved_font, font_size, anchor="sw")

    def write_chords(self, chords):
        if self.__driver is None or not chords:
            return

        cleaned_chords = []
        for chord_str in chords:
            if isinstance(chord_str, str) and '@' in chord_str:
                chord_str = chord_str.split('@')[0]
            cleaned_chords.append(chord_str)

        num_chords = len(cleaned_chords)
        center_y = self.__y + (self.__h / 2.0)

        if num_chords == 1:
            self._draw_single_chord(cleaned_chords[0], self.__x + (self.__w / 2.0), center_y, CHORD_FONT_SIZE)
        elif num_chords == 2:
            self._draw_single_chord(cleaned_chords[0], self.__x + (self.__w * 0.30), center_y, CHORD_FONT_SIZE)
            self._draw_single_chord(cleaned_chords[1], self.__x + (self.__w * 0.70), center_y, CHORD_FONT_SIZE)
        else:
            font_size = CHORD_COMPACT_SIZE
            resolved_font = "text_fnt"
            sup_size = int(font_size * 0.75)
            
            parsed_list = []
            for chord_str in cleaned_chords:
                root, color, bass = self.parse_chord(chord_str)
                f_root = self._format_part(root)
                f_color = self._format_color(color)
                f_bass = self._format_part(bass)
                parsed_list.append((f_root, f_color, f_bass))

            chord_widths = []
            for f_root, f_color, f_bass in parsed_list:
                r_w = self.__driver.string_width(f_root, resolved_font, font_size)
                if f_color in ("69", "6/9"):
                    c_w = self.__driver.string_width("6", resolved_font, int(sup_size * 0.85))
                else:
                    c_w = self.__driver.string_width(f_color, resolved_font, sup_size) if f_color else 0
                b_w = self.__driver.string_width(f"/{f_bass}", resolved_font, font_size) if f_bass else 0
                chord_widths.append(r_w + c_w + b_w)

            spacing = self.__driver.string_width("  ", resolved_font, font_size)
            total_width = sum(chord_widths) + spacing * (num_chords - 1)
            start_x = self.__x + (self.__w - total_width) / 2.0
            
            text_height = font_size * 0.7
            base_y = center_y - (text_height / 2.0)
            
            is_tkinter = getattr(self.__driver, 'is_top_origin', False)
            if is_tkinter:
                ascent, _ = self.__driver.get_font_metrics(resolved_font, font_size)
                base_y = center_y + (ascent / 2.0)
            
            sup_y = base_y - (font_size * 0.28) if is_tkinter else base_y + (font_size * 0.28)

            current_x = start_x
            for idx, (f_root, f_color, f_bass) in enumerate(parsed_list):
                r_w = self.__driver.string_width(f_root, resolved_font, font_size)
                self.__driver.draw_text(current_x, base_y, f_root, resolved_font, font_size, anchor="sw")
                current_x += r_w

                if f_color:
                    if f_color in ("69", "6/9"):
                        half_sup = sup_size * 0.52
                        if is_tkinter:
                            top_y = sup_y - half_sup * 0.3
                            bot_y = sup_y + half_sup * 0.7
                        else:
                            top_y = sup_y + half_sup * 0.3
                            bot_y = sup_y - half_sup * 0.7
                        self.__driver.draw_text(current_x, top_y, "6", resolved_font, int(sup_size * 0.85), anchor="sw")
                        self.__driver.draw_text(current_x, bot_y, "9", resolved_font, int(sup_size * 0.85), anchor="sw")
                        current_x += self.__driver.string_width("6", resolved_font, int(sup_size * 0.85))
                    else:
                        self.__driver.draw_text(current_x, sup_y, f_color, resolved_font, sup_size, anchor="sw")
                        current_x += self.__driver.string_width(f_color, resolved_font, sup_size)

                if f_bass:
                    bass_str = f"/{f_bass}"
                    self.__driver.draw_text(current_x, base_y, bass_str, resolved_font, font_size, anchor="sw")
                    current_x += self.__driver.string_width(bass_str, resolved_font, font_size)

                if idx < num_chords - 1:
                    current_x += spacing