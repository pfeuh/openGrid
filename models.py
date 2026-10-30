#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import List
from constants import (
    KEY_TITLE, KEY_SUBTITLE, KEY_COMPOSER, KEY_LYRICIST, KEY_ARRANGER,
    KEY_NUMBER, KEY_CHORDS, KEY_MARKERS, KEY_SECTIONS, KEY_JUMPS,
    KEY_BARLINES, KEY_SYSTEM_TEXTS, KEY_VOLTA, KEY_LINE_BREAK, KEY_TIMESIG,
    KEY_HEADER, KEY_BARS, KEY_KEYSIG, KEY_START_REPEAT, KEY_END_REPEAT,
    KEY_STYLE, KEY_CATEGORY, KEY_BPM, DEFAULT_STYLE, DEFAULT_CATEGORY, DEFAULT_BPM, DEFAULT_TIMESIG
)

class ChordInternal:
    """Classe utilitaire interne pour trier les accords par tick avant stockage en chaîne."""
    def __init__(self, chord: str, tick: int, beat: float):
        self.chord = self._clean_chord(chord)
        self.tick = tick
        self.beat = beat

    def _clean_chord(self, chord: str) -> str:
        if not chord or chord.strip() in ("", "None", "NoneNone", "NoneN.C."):
            return "N.C."
        if chord.startswith("None"):
            chord = chord[4:]
        if not chord or chord == "None":
            return "N.C."
        return chord

    def to_string(self) -> str:
        # Si le beat est 1.0 (défaut), on omet la référence temporelle
        if self.beat == 1.0:
            return self.chord
        return f"{self.chord}@{self.beat}"


class Bar:
    def __init__(self, number: int, timesig: str = "", keysig: str = "", bpm: int = 0,  
                 volta: str = "", line_break: bool = False, start_repeat: bool = False, end_repeat: int = 0):
        self.number = number
        self.chords: List[str] = []
        self.markers: List[str] = []
        self.sections: List[str] = []
        self.jumps: List[str] = []
        self.barlines: List[str] = []
        self.system_texts: List[str] = []
        self.volta = volta
        self.line_break = line_break
        self.timesig = timesig
        self.keysig = keysig
        self.bpm = bpm
        self.start_repeat = start_repeat
        self.end_repeat = end_repeat

    def set_chords_from_internal(self, internal_chords: List[ChordInternal]) -> None:
        """Trie par tick et convertit les objets internes en chaînes uniques."""
        internal_chords.sort(key=lambda c: c.tick)
        self.chords = [c.to_string() for c in internal_chords]

    def add_marker(self, marker: str) -> None:
        if marker not in self.markers:
            self.markers.append(marker)

    def add_section(self, section: str) -> None:
        if section not in self.sections:
            self.sections.append(section)

    def add_jump(self, jump: str) -> None:
        if jump not in self.jumps:
            self.jumps.append(jump)

    def add_barline(self, barline: str) -> None:
        self.barlines.append(barline)

    def add_system_text(self, text: str) -> None:
        self.system_texts.append(text)

    def to_dict(self) -> dict:
        d = {KEY_NUMBER: self.number}
        if self.chords: d[KEY_CHORDS] = self.chords
        if self.markers: d[KEY_MARKERS] = self.markers
        if self.sections: d[KEY_SECTIONS] = self.sections
        if self.jumps: d[KEY_JUMPS] = self.jumps
        if self.barlines: d[KEY_BARLINES] = self.barlines
        if self.system_texts: d[KEY_SYSTEM_TEXTS] = self.system_texts
        if self.volta: d[KEY_VOLTA] = self.volta
        if self.line_break: d[KEY_LINE_BREAK] = True
        if self.start_repeat: d[KEY_START_REPEAT] = True
        if self.end_repeat: d[KEY_END_REPEAT] = self.end_repeat
        if self.timesig: d[KEY_TIMESIG] = self.timesig
        if self.keysig: d[KEY_KEYSIG] = self.keysig
        if self.bpm: d[KEY_BPM] = self.bpm
        return d

    def __str__(self) -> str:
        chords_part = f"[{', '.join(self.chords)}]" if self.chords else "[]"
        extras = []
        if self.line_break: extras.append("line_break")
        if self.start_repeat: extras.append("start_repeat")
        if self.end_repeat: extras.append(f"end_repeat: {self.end_repeat}")
        if self.timesig: extras.append(f"timesig: {self.timesig}")
        if self.keysig: extras.append(f"keysig: {self.keysig}")
        if self.bpm: extras.append(f"bpm: {self.bpm}")
        if self.volta: extras.append(f"volta: {self.volta}")
        if self.sections: extras.append(f"sections: {self.sections}")
        if self.markers: extras.append(f"markers: {self.markers}")
        if self.jumps: extras.append(f"jumps: {self.jumps}")
        if self.system_texts: extras.append(f"texts: {self.system_texts}")
        
        extra_str = f" | {' | '.join(extras)}" if extras else ""
        return f"Bar {self.number:3d} | {chords_part}{extra_str}"

    def __repr__(self) -> str:
        return f"Bar(number={self.number}, chords={self.chords})"


class Header:
    def __init__(self, title: str = "", subtitle: str = "", composer: str = "",  
                    lyricist: str = "", arranger: str = "", style: str = DEFAULT_STYLE,  
                    category: str = DEFAULT_CATEGORY, bpm: int = 120, timesig: str = DEFAULT_TIMESIG):
        self.title = title
        self.subtitle = subtitle
        self.composer = composer
        self.lyricist = lyricist
        self.arranger = arranger
        self.style = style
        self.category = category
        self.bpm = bpm
        self.timesig = timesig

    def to_dict(self) -> dict:
        d = {KEY_TITLE: self.title}
        if self.subtitle: d[KEY_SUBTITLE] = self.subtitle
        if self.composer: d[KEY_COMPOSER] = self.composer
        if self.lyricist: d[KEY_LYRICIST] = self.lyricist
        if self.arranger: d[KEY_ARRANGER] = self.arranger
        d[KEY_STYLE] = self.style
        d[KEY_CATEGORY] = self.category
        d[KEY_BPM] = self.bpm
        d[KEY_TIMESIG] = self.timesig
        return d

    def __str__(self) -> str:
        parts = []
        if self.composer:
            parts.append(f"Comp: {self.composer}")
        if self.timesig:
            parts.append(self.timesig)
        if self.bpm:
            parts.append(f"{self.bpm} BPM")
        
        details = " | ".join(parts)
        details_str = f" ({details})" if details else ""
        return f"'{self.title}'{details_str}"

    def __repr__(self) -> str:
        return f"Header(title='{self.title}', composer='{self.composer}', bpm={self.bpm}, timesig='{self.timesig}')"


class Grid:
    def __init__(self, header: Header):
        self.header = header
        self.bars: List[Bar] = []

    def add_bar(self, bar: Bar) -> None:
        self.bars.append(bar)

    def get_bar(self, number: int) -> Bar:
        for bar in self.bars:
            if bar.number == number:
                return bar
        return None

    def to_dict(self) -> dict:
        return {
            KEY_HEADER: self.header.to_dict(),
            KEY_BARS: [b.to_dict() for b in self.bars]
        }

    def __str__(self) -> str:
        bars_summary = f"\n".join(str(bar) for bar in self.bars)
        return f"Grid Header: {self.header}\nTotal bars: {len(self.bars)}\n---\n{bars_summary}"

    def __repr__(self) -> str:
        return f"Grid(header={self.header!r}, bars_count={len(self.bars)})"