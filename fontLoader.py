#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_project_fonts():
    """Vérifie, installe automatiquement les polices locales dans l'OS et les enregistre."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "font")
    if not os.path.isdir(fonts_dir):
        fonts_dir = os.path.join(base_dir, "fonts")
    
    if not os.path.isdir(fonts_dir):
        return

    # Dossier cible standard pour les polices utilisateur sous Linux/Unix
    user_fonts_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(user_fonts_dir, exist_ok=True)

    font_files = {
        "MuseJazzText": "MuseJazzText.ttf",
        "Bravura": "Bravura.ttf",
        "gjm_realbook-webfont": "gjm_realbook-webfont.ttf"
    }

    installed_new = False

    for font_name, filename in font_files.items():
        src_path = os.path.join(fonts_dir, filename)
        if os.path.isfile(src_path):
            # 1. Copie automatique dans le système utilisateur si absente
            dest_path = os.path.join(user_fonts_dir, filename)
            if not os.path.isfile(dest_path):
                try:
                    shutil.copy(src_path, dest_path)
                    installed_new = True
                except Exception as e:
                    print(f"Impossible de copier la police {filename}: {e}")

            # 2. Enregistrement pour ReportLab (PDF)
            try:
                pdfmetrics.getFont(font_name)
            except KeyError:
                try:
                    pdfmetrics.registerFont(TTFont(font_name, src_path))
                except Exception as e:
                    print(f"Erreur d'enregistrement ReportLab pour {font_name}: {e}")

    # Si de nouvelles polices ont été copiées, on rafraîchit le cache de l'OS en arrière-plan
    if installed_new:
        try:
            subprocess.run(["fc-cache", "-f", user_fonts_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass