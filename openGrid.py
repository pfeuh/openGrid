#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import signal
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import rtmidi

# Import de TkinterDnD pour le support du Drag & Drop
from tkinterdnd2 import DND_FILES, TkinterDnD

# Import des constantes centralisées
from constants import (
    KEY_HEADER, KEY_BARS, KEY_TITLE, KEY_COMPOSER, 
    KEY_BPM, KEY_TIMESIG, KEY_STYLE, KEY_NUMBER, KEY_CHORDS
)

from measureEditor import open_measure_editor

# Import des modules personnalisés
from models import Grid, Header, Bar
from vectorialEditor import VectorialGridCanvas
from fontLoader import register_project_fonts
from menuHandler import MenuHandler
from compiler import compileAndFlatenizeGrid

# Chemin de configuration par défaut
CONFIG_FILE_PATH = ".grid_editor_config.json"
DEFAULT_CATALOG_PATH = os.path.join("styles", "dgx670.json")

class HybridGridEditorApp:

    def __init__(self, root):
        self.root = root
        self.root.geometry("850x730")

        # Enregistrement des polices du projet au démarrage
        register_project_fonts()

        self.current_filepath = None
        self.last_json_filepath = None
        self.last_musescore_filepath = None
        self.last_biab_filepath = None
        self.last_pdf_filepath = None
        self.last_excel_filepath = None  # Suivi du dernier fichier Excel exporté
        self.style_catalog_path = DEFAULT_CATALOG_PATH
        self.midi_port_idx = 0
        self.musescore_path = None
        self.arranger_process = None
        self.is_modified = False
        self.edited_bar = None  # Suivi de la mesure en cours d'édition

        self.load_config()

        # Instanciation du gestionnaire de menus
        self.menu_handler = MenuHandler(self)

        # Interception de la fermeture de la fenêtre (croix rouge)
        self.root.protocol("WM_DELETE_WINDOW", self.menu_handler.file_close)

        # --- CONFIGURATION DU DRAG & DROP ---
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_file_drop)

        # Création de la barre de menu déléguée au gestionnaire
        self.menubar = self.menu_handler.setup_menus(root)

        # CORRECTION ROBUSTE : Fermeture immédiate de tous les menus au moindre clic ou perte de focus
        def close_all_menus(event=None):
            try:
                for i in range(self.menubar.index("end") + 1):
                    try:
                        sub = self.menubar.entrycget(i, "menu")
                        if sub:
                            self.root.nametowidget(sub).unpost()
                    except Exception:
                        pass
            except Exception:
                pass

        self.root.bind("<Button-1>", close_all_menus, add="+")
        self.root.bind("<FocusOut>", close_all_menus, add="+")
        self.root.bind("<Unmap>", close_all_menus, add="+")

        # Cadre En-tête global (Informations + Paramètres Style / Tempo / Signature)
        header_frame = ttk.LabelFrame(root, text="Informations de la Grille & Style")
        header_frame.pack(fill="x", padx=10, pady=5)

        # Ligne 1 : Titre et Compositeur
        ttk.Label(header_frame, text="Titre :").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.title_entry = ttk.Entry(header_frame, width=22)
        self.title_entry.insert(0, "noname")
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)
        self.title_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        ttk.Label(header_frame, text="Compositeur :").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.composer_entry = ttk.Entry(header_frame, width=18)
        self.composer_entry.grid(row=0, column=3, padx=5, pady=5)
        self.composer_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        # Ligne 2 : Style, Catégorie, Arrangeur et Paramètres (Tempo / Signature)
        ttk.Label(header_frame, text="Style :").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
         
        style_display_frame = ttk.Frame(header_frame)
        style_display_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.style_name_var = tk.StringVar(value="StandardRock")
        self.lbl_style_display = ttk.Label(
            style_display_frame,
            textvariable=self.style_name_var,
            font=("Arial", 9, "bold"),
            foreground="#0056b3",
        )
        self.lbl_style_display.pack(side="left", padx=(0, 4))

        self.style_category_var = tk.StringVar(value="")
        self.lbl_category_display = ttk.Label(
            style_display_frame,
            textvariable=self.style_category_var,
            font=("Arial", 9, "italic"),
            foreground="#666",
        )
        self.lbl_category_display.pack(side="left")

        arranger_frame = ttk.Frame(header_frame)
        arranger_frame.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(arranger_frame, text="Arr. :", font=("Arial", 9)).pack(side="left", padx=2)
        self.arranger_name_var = tk.StringVar(value=os.path.basename(self.style_catalog_path))
        self.lbl_arranger_display = ttk.Label(
            arranger_frame,
            textvariable=self.arranger_name_var,
            font=("Arial", 9, "bold"),
            foreground="#444",
        )
        self.lbl_arranger_display.pack(side="left", padx=2)

        param_frame = ttk.Frame(header_frame)
        param_frame.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(param_frame, text="Tempo :").pack(side="left", padx=2)
        self.bpm_entry = ttk.Entry(param_frame, width=6)
        self.bpm_entry.insert(0, "110.0")
        self.bpm_entry.pack(side="left", padx=2)
        self.bpm_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        # Activation de l'écouteur de changement de style après l'initialisation des widgets d'en-tête
        self.style_name_var.trace_add("write", self._on_style_name_changed)

        ttk.Label(param_frame, text="Sig :").pack(side="left", padx=(10, 2))
        self.timesig_combo = ttk.Combobox(
            param_frame,
            values=["4/4", "3/4", "6/8", "9/8", "12/8", "2/4", "5/4"],
            width=5,
        )
        self.timesig_combo.set("4/4")
        self.timesig_combo.pack(side="left", padx=2)
        self.timesig_combo.bind("<<ComboboxSelected>>", lambda e: self.mark_as_modified())

        # Ligne 3 : Contrôles MIDI, Compilation et Bouton unique Play / Stop intelligent
        control_frame = ttk.LabelFrame(root, text="Contrôle MIDI, Compilation & Lecture")
        control_frame.pack(fill="x", padx=10, pady=5)

        midi_sub_frame = ttk.Frame(control_frame)
        midi_sub_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        ttk.Label(midi_sub_frame, text="Port MIDI :").pack(side="left", padx=2)
         
        self.midi_ports_list = self.get_available_midi_ports()
        self.midi_port_combo = ttk.Combobox(
            midi_sub_frame,
            values=self.midi_ports_list,
            width=22,
            state="readonly"
        )
        self.midi_port_combo.pack(side="left", padx=5)
        if self.midi_ports_list:
            if 0 <= self.midi_port_idx < len(self.midi_ports_list):
                self.midi_port_combo.current(self.midi_port_idx)
            else:
                self.midi_port_combo.current(0)
        self.midi_port_combo.bind("<<ComboboxSelected>>", self.on_midi_port_changed)

        btn_refresh_midi = ttk.Button(midi_sub_frame, text="🔄", width=3, command=self.refresh_midi_ports)
        btn_refresh_midi.pack(side="left", padx=2)

        # Bouton Compiler ajouté à côté du Play
        self.btn_compile = tk.Button(
            control_frame,
            text="⚡ Compiler",
            font=("Helvetica", 10, "bold"),
            bg="#d0e8f2",
            padx=10,
            command=self.compile_grid_action
        )
        self.btn_compile.pack(side="right", padx=5, pady=5)

        # Bouton unique Play / Stop
        self.btn_toggle_play = tk.Button(
            control_frame,
            text="▶ Play",
            font=("Helvetica", 10, "bold"),
            padx=15,
            command=self.toggle_playback
        )
        self.btn_toggle_play.pack(side="right", padx=5, pady=5)
         
        self.default_btn_bg = self.btn_toggle_play.cget("bg")

        # --- CONTENEUR ÉDITEUR VECTORIEL ---
        grid_container = ttk.Frame(root)
        grid_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.vectorial_editor = VectorialGridCanvas(grid_container, on_measure_edit_callback=self.edit_measure_popup)

        # Chargement initial du style par défaut pour positionner le tempo et la catégorie
        self._on_style_name_changed()

        # Démarrage forcé sur une feuille vierge "noname" de 32 mesures
        self.current_filepath = None
        self.update_title()
        default_grid = Grid(Header(title="noname"))
        for i in range(1, 33):
            default_grid.add_bar(Bar(number=i))
        self.vectorial_editor.load_grid(default_grid)
        self.set_modified(False)

        self.check_arranger_status()

    def handle_file_drop(self, event):
        """Gère le dépôt de fichiers par drag & drop."""
        files = self.root.tk.splitlist(event.data)
        if files and os.path.isfile(files[0]):
            self.menu_handler._load_from_path(files[0])

    def get_style_info_from_catalog(self, style_name):
        """Recherche dans le catalogue de styles le tempo (bpm) et la catégorie associés au style."""
        if not self.style_catalog_path or not os.path.isfile(self.style_catalog_path):
            return None, None
        try:
            with open(self.style_catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
               
            if isinstance(catalog, dict):
                for cat, styles in catalog.items():
                    if isinstance(styles, dict):
                        if style_name in styles:
                            style_data = styles[style_name]
                            tempo = style_data.get("tempo") or style_data.get("bpm")
                            return cat, tempo
                    elif isinstance(styles, list):
                        for s in styles:
                            if isinstance(s, dict) and s.get("name") == style_name:
                                tempo = s.get("tempo") or s.get("bpm")
                                return cat, tempo
            elif isinstance(catalog, list):
                for s in catalog:
                    if isinstance(s, dict) and s.get("name") == style_name:
                        cat = s.get("category", "")
                        tempo = s.get("tempo") or s.get("bpm")
                        return cat, tempo
        except Exception as e:
            print(f"Erreur lors de la lecture du catalogue de styles : {e}")
        return None, None

    def _on_style_name_changed(self, *args):
        style_name = self.style_name_var.get()
        cat, bpm = self.get_style_info_from_catalog(style_name)
        if cat:
            self.style_category_var.set(f"[{cat}]")
        else:
            default_cat = self.menu_handler.find_category_for_style(style_name)
            if default_cat:
                self.style_category_var.set(f"[{default_cat}]")
            else:
                self.style_category_var.set("[Pop & Rock]")

        if bpm is not None:
            if hasattr(self, 'bpm_entry') and self.bpm_entry:
                self.bpm_entry.delete(0, tk.END)
                self.bpm_entry.insert(0, str(bpm))
         
        self.mark_as_modified()

    def _generate_flatenized_json(self):
        """Méthode interne pour générer et sauvegarder temp/flatenized.json via un objet Grid strict."""
        if self.current_filepath and not self.is_modified and os.path.isfile(self.current_filepath) and self.current_filepath.endswith(".grid"):
            grid_obj = Grid.load(self.current_filepath)
        else:
            grid_obj = self.vectorial_editor.grid
            if not grid_obj:
                grid_obj = Grid(header=Header())

        try:
            current_bpm = float(self.bpm_entry.get())
        except ValueError:
            current_bpm = 110.0

        grid_obj.header.title = self.title_entry.get()
        grid_obj.header.composer = self.composer_entry.get()
        grid_obj.header.bpm = current_bpm
        grid_obj.header.timesig = self.timesig_combo.get()
        grid_obj.header.style = self.style_name_var.get()

        flat_grid_obj = compileAndFlatenizeGrid(grid_obj)
         
        os.makedirs("temp", exist_ok=True)
        output_path = os.path.join("temp", "flatenized.json")
        flat_grid_obj.save(output_path)
         
        return output_path

    def compile_grid_action(self):
        """Action déclenchée par le bouton Compiler : génère temp/flatenized.json et affiche le résultat."""
        try:
            output_path = self._generate_flatenized_json()
            if not output_path:
                messagebox.showwarning("Attention", "Aucune grille chargée à compiler.")
                return

            flat_grid_obj = Grid.load(output_path)
            sequence = [bar.number for bar in flat_grid_obj.bars]
             
            print(f"\n--- COMPILATION & APLATISSEMENT RÉUSSIS ({len(sequence)} mesures) ---")
            print(f"Fichier sauvegardé : {output_path}")

        except Exception as e:
            messagebox.showerror("Erreur de compilation", f"Une erreur est survenue :\n{e}")
            print(f"Erreur de compilation : {e}")

    def get_available_midi_ports(self):
        try:
            midi_out = rtmidi.MidiOut()
            ports = midi_out.get_ports()
            del midi_out
            if ports:
                return [f"[{i}] {p}" for i, p in enumerate(ports)]
        except Exception:
            pass
        return ["Aucun port MIDI disponible"]

    def refresh_midi_ports(self):
        self.midi_ports_list = self.get_available_midi_ports()
        self.midi_port_combo['values'] = self.midi_ports_list
        if self.midi_ports_list and "Aucun" not in self.midi_ports_list[0]:
            self.midi_port_combo.current(0)
            self.midi_port_idx = 0

    def on_midi_port_changed(self, event):
        sel = self.midi_port_combo.current()
        if sel >= 0:
            self.midi_port_idx = sel
            self.save_config()

    def toggle_playback(self):
        if self.arranger_process and self.arranger_process.poll() is None:
            self.stop_arranger_process()
        else:
            self.start_arranger_process()

    def start_arranger_process(self):
        self.stop_arranger_process()

        port_idx = self.midi_port_combo.current()
        if port_idx < 0:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un port MIDI valide.")
            return

        try:
            flat_json_path = self._generate_flatenized_json()
            if not flat_json_path:
                messagebox.showerror("Erreur", "Impossible de générer la grille aplatie pour la lecture.")
                return
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la compilation pour la lecture :\n{e}")
            return

        script_path = "remotedArranger.py"
        if not os.path.isfile(script_path):
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remotedArranger.py")

        if not os.path.isfile(script_path):
            messagebox.showerror("Erreur", "Le fichier 'remotedArranger.py' est introuvable.")
            return

        try:
            cmd = [sys.executable, script_path, str(port_idx), flat_json_path]
            self.arranger_process = subprocess.Popen(cmd)
            self.btn_toggle_play.config(text="⏹ En cours...", bg="#28a745", fg="white")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'arrangeur :\n{e}")

    def stop_arranger_process(self):
        if self.arranger_process:
            try:
                if self.arranger_process.poll() is None:
                    self.arranger_process.send_signal(signal.SIGINT)
                    self.arranger_process.wait(timeout=1.5)
            except Exception:
                try:
                    self.arranger_process.terminate()
                except Exception:
                    pass
            self.arranger_process = None

        self.btn_toggle_play.config(text="▶ Play", bg=self.default_btn_bg, fg="black")

    def check_arranger_status(self):
        if self.arranger_process is not None:
            if self.arranger_process.poll() is not None:
                self.arranger_process = None
                self.btn_toggle_play.config(text="▶ Play", bg=self.default_btn_bg, fg="black")
         
        self.root.after(500, self.check_arranger_status)

    def mark_as_modified(self):
        if not self.is_modified:
            self.set_modified(True)

    def set_modified(self, status):
        self.is_modified = status
        self.update_title()

    def edit_measure_popup(self, bar_obj):
        """Délègue l'affichage du dialogue d'édition au module measureEditor avec support de la navigation par index."""
        if not self.vectorial_editor.grid or not self.vectorial_editor.grid.bars:
            return

        bars_list = self.vectorial_editor.grid.bars
        try:
            current_index = bars_list.index(bar_obj)
        except ValueError:
            return

        if self.edited_bar and self.edited_bar != bar_obj:
            self.vectorial_editor.set_bar_background(self.edited_bar, "")

        self.edited_bar = bar_obj
        self.vectorial_editor.set_bar_background(bar_obj, "#FFF2CC")

        def on_save():
            self._on_measure_saved()

        def on_close():
            if self.edited_bar:
                self.vectorial_editor.set_bar_background(self.edited_bar, "")
                self.edited_bar = None
            self._on_measure_saved()

        def on_navigate(current_bar, direction):
            nonlocal current_index
            if not bars_list:
                return None
             
            self.vectorial_editor.set_bar_background(bars_list[current_index], "")
            current_index = (current_index + direction) % len(bars_list)
            next_bar = bars_list[current_index]

            self.edited_bar = next_bar
            self.vectorial_editor.set_bar_background(next_bar, "#FFF2CC")
            self._on_measure_saved()

            return next_bar

        open_measure_editor(
            self.root, 
            bar_obj, 
            on_save_callback=on_save, 
            on_close_callback=on_close,
            on_navigate_callback=on_navigate
        )

    def _on_measure_saved(self):
        self.vectorial_editor.redraw()
        self.mark_as_modified()

    def update_title(self):
        if self.current_filepath:
            filename = os.path.basename(self.current_filepath)
            base_title = f"Remoted Arranger - {filename}"
        else:
            base_title = f"Remoted Arranger - {self.title_entry.get() if hasattr(self, 'title_entry') else 'Sans titre'}"

        if self.is_modified:
            self.root.title(base_title + " *")
        else:
            self.root.title(base_title)

    def load_config(self):
        if os.path.isfile(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if json_path := config.get("last_json_filepath"):
                        self.last_json_filepath = json_path
                    if ms_path := config.get("last_musescore_filepath"):
                        self.last_musescore_filepath = ms_path
                    if musescore_exe := config.get("musescore_path"):
                        self.musescore_path = musescore_exe
                    if biab_path := config.get("last_biab_filepath"):
                        self.last_biab_filepath = biab_path
                    if pdf_path := config.get("last_pdf_filepath"):
                        self.last_pdf_filepath = pdf_path
                    if excel_path := config.get("last_excel_filepath"):
                        self.last_excel_filepath = excel_path
                    if midi_idx := config.get("midi_port_idx"):
                        self.midi_port_idx = int(midi_idx)
            except Exception:
                pass

    def save_config(self):
        config = {}
        if os.path.isfile(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        if self.last_json_filepath:
            config["last_json_filepath"] = self.last_json_filepath
        if self.last_musescore_filepath:
            config["last_musescore_filepath"] = self.last_musescore_filepath
        if self.last_biab_filepath:
            config["last_biab_filepath"] = self.last_biab_filepath
        if self.last_pdf_filepath:
            config["last_pdf_filepath"] = self.last_pdf_filepath
        if self.last_excel_filepath:
            config["last_excel_filepath"] = self.last_excel_filepath
        if self.musescore_path:
            config["musescore_path"] = self.musescore_path
        if hasattr(self, 'midi_port_idx'):
            config["midi_port_idx"] = self.midi_port_idx

        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = HybridGridEditorApp(root)
    root.mainloop()