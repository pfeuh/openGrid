#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path

import pdfGenerator
import getMusescoreGrid
from toCamelCase import to_camel_case
from models import Grid, Header, Bar
from styleSelectorModal import StyleSelectorModal


class MenuHandler:
    def __init__(self, app):
        self.app = app  # Référence vers l'instance de HybridGridEditorApp

    def find_category_for_style(self, style_name):
        if os.path.isfile(self.app.style_catalog_path):
            try:
                with open(self.app.style_catalog_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
                    for s in catalog:
                        if s.get("name", "").lower() == style_name.lower():
                            return s.get("category", "")
            except Exception:
                pass
        return ""

    def select_arranger(self):
        initial_dir = os.path.dirname(self.app.style_catalog_path) if os.path.exists(self.app.style_catalog_path) else "styles"
        if not os.path.exists(initial_dir):
            initial_dir = "."

        filepath = filedialog.askopenfilename(
            title="Sélectionner le catalogue de l'arrangeur",
            initialdir=initial_dir,
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.app.style_catalog_path = filepath
            self.app.arranger_name_var.set(os.path.basename(filepath))
            self.app.save_config()
            cat = self.find_category_for_style(self.app.style_name_var.get())
            self.app.style_category_var.set(f"[{cat}]" if cat else "")

    def open_style_selector(self):
        StyleSelectorModal(self.app.root, self.app.style_catalog_path, self.on_style_selected)

    def on_style_selected(self, style_info):
        name = style_info.get("name", "StandardRock")
        cat = style_info.get("category", "Pop & Rock")
        tempo = style_info.get("tempo", 110.0)
        sig = style_info.get("sig", "4/4")

        self.app.style_name_var.set(name)
        self.app.style_category_var.set(f"[{cat}]" if cat else "")
        self.app.bpm_entry.delete(0, tk.END)
        self.app.bpm_entry.insert(0, str(tempo))
        self.app.timesig_combo.set(sig)
        self.app.mark_as_modified()

    def get_default_filename(self):
        title_val = self.app.title_entry.get().strip()
        if not title_val:
            return "grille.grid"
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else "_" for c in title_val)
        safe_title = safe_title.strip().replace(" ", "_").lower()
        return f"{safe_title}.grid" if safe_title else "grille.grid"

    def get_default_pdf_filename(self):
        title_val = self.app.title_entry.get().strip()
        if self.app.current_filepath:
            base_name = os.path.splitext(os.path.basename(self.app.current_filepath))[0]
            return to_camel_case(base_name) + ".pdf"
        elif title_val:
            return to_camel_case(title_val) + ".pdf"
        elif self.app.last_pdf_filepath:
            return os.path.basename(self.app.last_pdf_filepath)
        return "score.pdf"

    def get_initial_dir(self, target_filepath=None):
        if target_filepath and os.path.exists(target_filepath):
            parent_dir = os.path.dirname(target_filepath)
            if os.path.isdir(parent_dir):
                return parent_dir
        if self.app.current_filepath:
            parent_dir = os.path.dirname(self.app.current_filepath)
            if os.path.isdir(parent_dir):
                return parent_dir
        return os.getcwd()

    def check_save_before_action(self):
        if not self.app.is_modified:
            return True

        filename = os.path.basename(self.app.current_filepath) if self.app.current_filepath else "Sans titre"
        response = messagebox.askyesnocancel(
            "Modifications non enregistrées",
            f"Le fichier '{filename}' a été modifié.\nVoulez-vous enregistrer les modifications ?"
        )
        
        if response is True:
            return self.file_save()
        elif response is False:
            return True
        else:
            return False

    def file_new(self):
        if not self.check_save_before_action():
            return

        nb_measures = simpledialog.askinteger(
            "Nouvelle Grille", 
            "Nombre de mesures pour cette grille :", 
            initialvalue=32, 
            minvalue=1, 
            maxvalue=200,
            parent=self.app.root
        )
        
        if nb_measures is None:
            return

        self.app.stop_arranger_process()
        self.app.current_filepath = None
        self.app.save_config()
        
        self.app.title_entry.delete(0, tk.END)
        self.app.title_entry.insert(0, "Ma Grille")
        self.app.composer_entry.delete(0, tk.END)
        self.app.composer_entry.insert(0, "Pierre Faller")
        self.app.style_name_var.set("StandardRock")
        
        cat = self.find_category_for_style("StandardRock")
        self.app.style_category_var.set(f"[{cat}]" if cat else "[Pop & Rock]")

        self.app.bpm_entry.delete(0, tk.END)
        self.app.bpm_entry.insert(0, "110.0")
        self.app.timesig_combo.set("4/4")
        
        default_grid = Grid(Header(title="Ma Grille"))
        for i in range(1, nb_measures + 1):
            default_grid.add_bar(Bar(number=i))
            
        self.app.vectorial_editor.load_grid(default_grid)
        self.app.set_modified(False)

    def file_save(self):
        if self.app.current_filepath:
            return self._save_to_path(self.app.current_filepath)
        else:
            return self.file_save_as()

    def file_save_as(self):
        initial_dir = self.get_initial_dir(self.app.last_json_filepath)
        initial_file = os.path.basename(self.app.current_filepath) if self.app.current_filepath else self.get_default_filename()

        filepath = filedialog.asksaveasfilename(
            title="Enregistrer la grille sous",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".grid",
            filetypes=[("Fichiers Grille", "*.grid"), ("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self.app.current_filepath = filepath
            self.app.last_json_filepath = filepath
            self.app.save_config()
            return self._save_to_path(filepath)
        return False

    def file_save_copy(self):
        initial_dir = self.get_initial_dir(self.app.last_json_filepath)
        initial_file = os.path.basename(self.app.current_filepath) if self.app.current_filepath else self.get_default_filename()

        filepath = filedialog.asksaveasfilename(
            title="Enregistrer une copie",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".grid",
            filetypes=[("Fichiers Grille", "*.grid"), ("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self.app.last_json_filepath = filepath
            self.app.save_config()
            self._save_to_path(filepath)

    def file_close(self):
        if self.check_save_before_action():
            self.app.stop_arranger_process()
            self.app.root.destroy()

    def load_json(self):
        if not self.check_save_before_action():
            return

        initial_dir = self.get_initial_dir(self.app.last_json_filepath)

        filepath = filedialog.askopenfilename(
            title="Charger une grille",
            initialdir=initial_dir,
            filetypes=[("Fichiers Grille", "*.grid"), ("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self._load_from_path(filepath)

    def _load_from_path(self, filepath, show_popup=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            header = data.get("header", {})
            self.app.title_entry.delete(0, tk.END)
            self.app.title_entry.insert(0, header.get("title", "Ma Grille"))
            self.app.composer_entry.delete(0, tk.END)
            self.app.composer_entry.insert(0, header.get("composer", ""))
            
            style = header.get("style", "StandardRock")
            self.app.style_name_var.set(style)
            cat = header.get("category", self.find_category_for_style(style))
            self.app.style_category_var.set(f"[{cat}]" if cat else "")

            self.app.bpm_entry.delete(0, tk.END)
            self.app.bpm_entry.insert(0, str(header.get("bpm", 110.0)))
            self.app.timesig_combo.set(header.get("timesig", "4/4"))

            bars = data.get("bars", [])
            grid_obj = Grid(header=Header(**header))
            
            for b_data in bars:
                bar = Bar(number=b_data.get("number", 1))
                bar.chords = b_data.get("chords", [])
                bar.start_repeat = b_data.get("start_repeat", False)
                bar.end_repeat = b_data.get("end_repeat", 0)
                bar.volta = b_data.get("volta", "")
                bar.markers = b_data.get("markers", [])
                bar.sections = b_data.get("sections", [])
                bar.jumps = b_data.get("jumps", [])
                grid_obj.add_bar(bar)

            self.app.vectorial_editor.load_grid(grid_obj)

            self.app.current_filepath = filepath
            self.app.last_json_filepath = filepath
            self.app.save_config()
            self.app.set_modified(False)

            if show_popup:
                messagebox.showinfo("Succès", f"Grille chargée avec succès !\nTotal : {len(bars)} mesures.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier :\n{e}")

    def _save_to_path(self, filepath):
        try:
            bpm_val = float(self.app.bpm_entry.get().strip())
        except ValueError:
            bpm_val = 120.0

        cat_raw = self.app.style_category_var.get().strip()
        cat_clean = cat_raw.strip("[]")

        header = Header(
            title=self.app.title_entry.get().strip(),
            composer=self.app.composer_entry.get().strip(),
            style=self.app.style_name_var.get().strip(),
            category=cat_clean,
            bpm=bpm_val,
            timesig=self.app.timesig_combo.get().strip()
        )
        
        grid_data = self.app.vectorial_editor.grid.to_dict()
        grid_data["header"] = header.to_dict()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(grid_data, f, ensure_ascii=False, indent=4)
            self.app.current_filepath = filepath
            self.app.last_json_filepath = filepath
            self.app.save_config()
            self.app.set_modified(False)
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement :\n{e}")
            return False

    def load_musescore(self):
        """Méthode unifiée de chargement d'un fichier MuseScore."""
        if not self.check_save_before_action():
            return

        initial_dir = "scores" if os.path.exists("scores") else "."
        if self.app.last_musescore_filepath:
            parent_dir = os.path.dirname(self.app.last_musescore_filepath)
            if os.path.exists(parent_dir):
                initial_dir = parent_dir

        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier MuseScore",
            initialdir=initial_dir,
            filetypes=[("Fichiers MuseScore", "*.mscz *.mscx"), ("Tous les fichiers", "*.*")]
        )
        if not filepath:
            return

        self._load_musescore_from_path(filepath)

    def _load_musescore_from_path(self, filepath):
        """Traite et charge un fichier MuseScore depuis un chemin donné."""
        self.app.last_musescore_filepath = filepath
        self.app.save_config()

        try:
            grid_obj_from_ms = getMusescoreGrid.getGrid(filepath)
            
            header = grid_obj_from_ms.header
            if header:
                if header.title:
                    self.app.title_entry.delete(0, tk.END)
                    self.app.title_entry.insert(0, header.title)
                if header.composer:
                    self.app.composer_entry.delete(0, tk.END)
                    self.app.composer_entry.insert(0, header.composer)
                if header.bpm:
                    self.app.bpm_entry.delete(0, tk.END)
                    self.app.bpm_entry.insert(0, str(header.bpm))
                if header.timesig:
                    self.app.timesig_combo.set(header.timesig)

            self.app.vectorial_editor.load_grid(grid_obj_from_ms)
            
            self.app.current_filepath = None
            self.app.set_modified(True)
            messagebox.showinfo("Succès", f"Grille MuseScore importée !\nTotal de mesures : {len(grid_obj_from_ms.bars)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'import MuseScore :\n{e}")

    def generate_pdf(self):
        initial_dir = self.get_initial_dir(self.app.last_pdf_filepath)

        pdf_filename = self.get_default_pdf_filename()
        filepath = filedialog.asksaveasfilename(
            title="Exporter en PDF",
            initialdir=initial_dir,
            initialfile=pdf_filename,
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            try:
                pdfGenerator.gridToPdf(self.app.vectorial_editor.grid, filepath)
                self.app.last_pdf_filepath = filepath
                self.app.save_config()
                messagebox.showinfo("Succès", f"PDF généré avec succès :\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF :\n{e}")