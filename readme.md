# OpenGrid 🎵

**OpenGrid** est une application Python / Tkinter conçue pour la création, l'édition et le pilotage temps réel de grilles musicales d'accords pour arrangeurs automatiques.

---

## 🚀 Fonctionnalités principales

* **Édition de grilles d'accords :** Saisie et modification faciles d'accords sur une grille visuelle ergonomique.
* **Import multi-formats intelligent :** 
  * Parse et convertit les partitions complexes issues de **MuseScore** (`.mscz`, MusicXML).
  * Importe également depuis **iReal Pro** et **Band-in-a-Box**.
* **Compilation & Aplatissement :** Le cœur du projet — un moteur interne qui analyse et aplatit les structures (mesures répétées, reprises, codas, etc.) pour générer une séquence linéaire exploitable.
* **Pilotage d'arrangeur externe :** Contrôle temps réel d'un processus d'arrangement automatique via MIDI et sous-processus.
* **Sauvegarde native :** Format de fichier dédié (`.grid`) et gestion de configuration locale.

---

## 🛠️ Stack technique & Prérequis système

### Prérequis externes
* **Python 3**
* **MuseScore** (doit être installé sur le système pour permettre l'import et le traitement des fichiers `.mscz` / MusicXML, avec le chemin configuré dans `config.json`).

### Dépendances Python
* `tkinterdnd2` *(Drag & Drop)*
* `rtmidi` *(Communication MIDI temps réel)*
* `reportlab` *(Moteur graphique et génération de PDF)*
* `pyRealParser` *(Parsing des grilles iReal Pro)*
* `fonttools` *(Manipulation des polices musicales)*

---

## 📦 Installation & Lancement

**Cloner le dépôt :**
   ```bash
   git clone [https://github.com/votre-compte/opengrid.git](https://github.com/votre-compte/opengrid.git)
   cd openGrid
   
pip install -r requirements.txt

python openGrid.py

📂 Structure du projet

    openGrid.py : Point d'entrée principal et interface GUI.

    config.json : Fichier de configuration utilisateur (chemins d'accès, exécutables dont MuseScore, ports MIDI).

📄 Licence

Projet sous licence MIT — Réutilisation et modifications libres.
