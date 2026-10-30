#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import filedialog
import webbrowser
from fontTools.ttLib import TTFont

# Initialisation de Tkinter (fenêtre cachée pour afficher uniquement le sélecteur de fichier)
root = tk.Tk()
root.withdraw()

# Ouverture de la boîte de dialogue pour choisir le fichier de police
font_path = filedialog.askopenfilename(
    title="Sélectionner une police de caractères",
    filetypes=[
        ("Fichiers de police ", "*.ttf"),
        ("Fichiers de police", "*.ttf *.otf"),
        ("Tous les fichiers", "*.*"),
    ],
)

# Si l'utilisateur annule la sélection, on arrête le script
if not font_path:
    print("Aucune police sélectionnée. Fin du script.")
    exit()

font_name = os.path.basename(font_path)
html_path = os.path.join("html", (os.path.splitext(font_name)[0] + ".html"))

# Extraction des caractères via fontTools
font = TTFont(font_path)
cmap = font["cmap"].getBestCmap()
code_points = sorted(list(cmap.keys()))

# Construction d'une page HTML stylisée avec la police embarquée
html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Visualiseur de Police - HTML</title>
    <style>
        @font-face {{
            font-family: 'CustomFont';
            src: url('file://{font_path}') format('truetype');
        }}
        body {{
            font-family: sans-serif;
            background: #f0f2f5;
            margin: 20px;
        }}
        h1 {{
            color: #333;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 10px;
        }}
        .cell {{
            background: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .glyph {{
            font-family: 'CustomFont', sans-serif;
            font-size: 28px;
            margin-bottom: 8px;
            display: block;
        }}
        .code {{
            font-size: 10px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>Visualiseur de Police : {font_name}</h1>
    <p>Total de glyphes trouvés : {len(code_points)}</p>
    <div class="grid">
"""

for cp in code_points:
    try:
        char = chr(cp)
    except ValueError:
        char = ""
    html_content += f"""
        <div class="cell">
            <span class="glyph">{char}</span>
            <span class="code">U+{cp:04X}</span>
        </div>"""

html_content += """
    </div>
</body>
</html>
"""

# Écriture et ouverture automatique dans le navigateur
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

webbrowser.open("file://" + os.path.abspath(html_path))