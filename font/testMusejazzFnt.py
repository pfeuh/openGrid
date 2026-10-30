#!/usr/init/python
# -*- coding: utf-8 -*-

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# 1. Enregistrer les polices avec des noms personnalisés
# (Assurez-vous que les chemins vers vos fichiers .otf sont corrects)
pdfmetrics.registerFont(TTFont('MuseJazz', 'MuseJazz.ttf'))
pdfmetrics.registerFont(TTFont('MuseJazzText', 'MuseJazzText.ttf'))

# 2. Créer votre document PDF (exemple avec un Canvas)
c = canvas.Canvas("lead_sheet.pdf", pagesize=(600, 400))

# 3. Utiliser la police pour le texte ou les symboles
c.setFont('MuseJazzText', 16)
c.drawString(50, 300, "Cmaj7    Am7    Dm7    G7")

c.setFont('MuseJazz', 24)
c.drawString(50, 250, "\ue047\ue048\ue049\ue04a")  # Affichera les symboles musicaux/accords du style

c.save()