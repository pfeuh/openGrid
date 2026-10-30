SYNTHÈSE DU PARSING XML ET LISTE DES ÉLÉMENTS RÉCUPÉRÉS DANS ms2grid.py

1. Décompression du fichier .mscz
- Le fichier .mscz (archive ZIP) est extrait dans le dossier temporaire `temp/`.
- Recherche dynamique du fichier XML natif .mscx extrait.

2. Chargement du document XML
- Utilisation de xml.etree.ElementTree pour analyser l'arbre XML du fichier .mscx (`root_elem`).

3. Liste détaillée des éléments extraits :

A. En-tête (Header) :
- Titre (`title`) : Récupéré via l'élément Text de style "title", ou par défaut le nom du fichier.
- Sous-titre (`subtitle`) : Élément Text de style "subtitle".
- Compositeur (`composer`) : Élément Text de style "composer".
- Parolier (`lyricist`) : Élément Text de style "poet".
- Arrangeur (`arranger`) : Élément Text de style "arranger".
- Signature rythmique globale (`timesig` / `global_timesig`) : Issue du premier élément `TimeSig` trouvé (`sigN` / `sigD`).

B. Par mesure (Measure) :
Chaque mesure est parcourue séquentiellement et extrait les informations suivantes :
- Accords (`Harmony`) : 
  * Note fondamentale (`root`), nom/suffixe (`name`), basse inversée (`bass`).
  * Conversion des chiffres TPC (Tone Pitch Class) en noms de notes textuels.
  * Propagation automatique des accords sur les mesures vides à partir de la mesure précédente.
- Textes de portée (`StaffText`) : Indications textuelles attachées à la portée.
- Repères et marques de répétition (`Marker` et `RehearsalMark`) : 
  * Extraits, normalisés et mappés via le dictionnaire externe `musicalGlyphes` (ex: Coda, Fine, Segno, repères A, B, C...).
- Sauts (`Jump`) : 
  * Types de sauts et cibles normalisées (ex: conversion de `jumpTo="start"` en `D.C.`, `jumpTo="segno"` en `D.S.`, etc.).
- Barres de mesure (`BarLine`) : Types de barres (double, répétition, fin, etc.).
- Signature rythmique locale (`TimeSig` spécifique à une mesure).
- Voltas (`volta`) : Fins de reprises textuelles.
- Sauts de ligne et Départs de reprise (`LayoutBreak` / `repeatStart`) : Indicateurs de saut de ligne ou de début de reprise (`line_break`).

4. Assemblage et export
- Création d'un objet structuré `Bar` pour chaque mesure.
- Génération d'un dictionnaire global structuré contenant l'en-tête (avec style, catégorie et BPM par défaut) et la liste complète des mesures (`bars`) pour alimenter l'éditeur de grilles (`gridEditor`).