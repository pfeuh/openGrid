# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import messagebox

import customFileDialog as fd
from irealPro2Json import irealproToGrid
from getMusescoreGrid import getGrid
from gridToExcell import gridToExcel

class GridIOHandler:
    """Gère l'ensemble des opérations d'E/S (Load, Import, Save, Export) pour l'application."""

    def __init__(self, app):
        self.app = app

    def import_ireal_pro_dialog(self):
        """Demande confirmation par une boîte askyesno, puis lit et importe le lien du presse-papier."""
        if messagebox.askyesno("Import iReal Pro", "Voulez-vous importer le lien iReal Pro depuis le presse-papier ?"):
            try:
                url = self.app.root.clipboard_get().strip()
            except Exception:
                url = ""

            if not url:
                messagebox.showwarning("Presse-papier vide", "Aucun texte n'a été trouvé dans le presse-papier.")
                return

            self.process_ireal_pro_url(url)

    def process_ireal_pro_url(self, url):
        """Appelle irealproToGrid et charge directement l'objet Grid retourné."""
        grid_obj = irealproToGrid(url)
         
        if not grid_obj:
            messagebox.showwarning("Attention", "La conversion n'a retourné aucune grille valide.")
            return

        self.app.current_filepath = None
        self.app.vectorial_editor.load_grid(grid_obj)
         
        if hasattr(grid_obj, 'header') and grid_obj.header:
            if hasattr(grid_obj.header, 'title') and grid_obj.header.title:
                self.app.title_entry.delete(0, tk.END)
                self.app.title_entry.insert(0, grid_obj.header.title)
            if hasattr(grid_obj.header, 'composer') and grid_obj.header.composer:
                self.app.composer_entry.delete(0, tk.END)
                self.app.composer_entry.insert(0, grid_obj.header.composer)
            if hasattr(grid_obj.header, 'bpm') and grid_obj.header.bpm:
                self.app.bpm_entry.delete(0, tk.END)
                self.app.bpm_entry.insert(0, str(grid_obj.header.bpm))
            if hasattr(grid_obj.header, 'timesig') and grid_obj.header.timesig:
                self.app.timesig_combo.set(grid_obj.header.timesig)

        self.app.set_modified(True)
        messagebox.showinfo("Succès", "Grille iReal Pro importée avec succès !")

    def load_json_fixed(self):
        """Ouvre le sélecteur de fichier Grid en pointant proprement sur le dossier et le nom du dernier fichier."""
        target_path = self.app.current_filepath or self.app.last_json_filepath
        initial_dir = os.path.dirname(target_path) if target_path and os.path.isfile(target_path) else "."
        initial_file = os.path.basename(target_path) if target_path and os.path.isfile(target_path) else ""

        file_path = fd.askopenfilename(
            title="Charger une grille",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=[("Fichiers Grille", "*.grid"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.app.last_json_filepath = file_path
            self.app.save_config()
            self.app.menu_handler._load_from_path(file_path, show_popup=True)

    def load_musescore_fixed(self):
        """Ouvre le sélecteur de fichier MuseScore en pointant proprement sur le dossier et le nom du dernier fichier."""
        initial_dir = os.path.dirname(self.app.last_musescore_filepath) if self.app.last_musescore_filepath and os.path.isfile(self.app.last_musescore_filepath) else "."
        initial_file = os.path.basename(self.app.last_musescore_filepath) if self.app.last_musescore_filepath and os.path.isfile(self.app.last_musescore_filepath) else ""

        file_path = fd.askopenfilename(
            title="Charger depuis MuseScore",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=[("Fichiers MuseScore", "*.mscz *.mscx"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.app.last_musescore_filepath = file_path
            self.app.save_config()
             
            # Application du sablier pendant le traitement MuseScore
            self.app.root.config(cursor="watch")
            self.app.root.update_idletasks()
            try:
                if hasattr(self.app.menu_handler, '_load_musescore_from_path'):
                    self.app.menu_handler._load_musescore_from_path(file_path)
                elif hasattr(self.app.menu_handler, 'load_musescore'):
                    self.app.menu_handler.load_musescore()
            finally:
                self.app.root.config(cursor="")

    def load_biab_fixed(self):
        """Ouvre le sélecteur de fichier Band-in-a-Box (.sgu, .mgu, .zip)."""
        initial_dir = os.path.dirname(self.app.last_biab_filepath) if self.app.last_biab_filepath and os.path.isfile(self.app.last_biab_filepath) else "."
        initial_file = os.path.basename(self.app.last_biab_filepath) if self.app.last_biab_filepath and os.path.isfile(self.app.last_biab_filepath) else ""

        file_path = fd.askopenfilename(
            title="Charger depuis Band-in-a-Box",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=[
                ("Band-in-a-Box & Archives", "*.sgu *.mgu *.zip"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if file_path:
            self.app.last_biab_filepath = file_path
            self.app.save_config()
            self._load_biab_from_path(file_path)

    def _load_biab_from_path(self, file_path):
        self.app.root.config(cursor="watch")
        self.app.root.update_idletasks()
        try:
            grid_obj = getGrid(file_path)
            if not grid_obj:
                messagebox.showwarning("Attention", "La conversion Band-in-a-Box n'a retourné aucune grille valide.")
                return

            self.app.current_filepath = None
            self.app.vectorial_editor.load_grid(grid_obj)

            if hasattr(grid_obj, 'header') and grid_obj.header:
                if hasattr(grid_obj.header, 'title') and grid_obj.header.title:
                    self.app.title_entry.delete(0, tk.END)
                    self.app.title_entry.insert(0, grid_obj.header.title)
                if hasattr(grid_obj.header, 'composer') and grid_obj.header.composer:
                    self.app.composer_entry.delete(0, tk.END)
                    self.app.composer_entry.insert(0, grid_obj.header.composer)
                if hasattr(grid_obj.header, 'bpm') and grid_obj.header.bpm:
                    self.app.bpm_entry.delete(0, tk.END)
                    self.app.bpm_entry.insert(0, str(grid_obj.header.bpm))
                if hasattr(grid_obj.header, 'timesig') and grid_obj.header.timesig:
                    self.app.timesig_combo.set(grid_obj.header.timesig)

            self.app.set_modified(True)
            messagebox.showinfo("Succès", f"Fichier Band-in-a-Box importé avec succès :\n{os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Erreur d'import", f"Impossible d'importer le fichier Band-in-a-Box :\n{e}")
        finally:
            self.app.root.config(cursor="")

    def export_excel_fixed(self):
        """Ouvre le sélecteur de fichier pour exporter la grille courante au format Excel (.xlsx)."""
        grid_obj = self.app.vectorial_editor.grid
        if not grid_obj or not grid_obj.bars:
            messagebox.showwarning("Attention", "Aucune grille active à exporter.")
            return

        target_path = self.app.current_filepath or self.app.last_json_filepath
        initial_dir = os.path.dirname(target_path) if target_path and os.path.isfile(target_path) else "."
        initial_file = (os.path.splitext(os.path.basename(target_path))[0] + ".xlsx") if target_path and os.path.isfile(target_path) else "grille.xlsx"

        file_path = fd.asksaveasfilename(
            title="Exporter la grille au format Excel",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel (*.xlsx)", "*.xlsx"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            try:
                gridToExcel(grid_obj, file_path)
                messagebox.showinfo("Succès", f"Grille exportée avec succès en Excel :\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erreur d'export Excel", f"Une erreur est survenue lors de l'export :\n{e}")

    def handle_file_drop(self, event):
        """Gère le dépôt d'un ou plusieurs fichiers par drag & drop sur la fenêtre."""
        files = self.app.root.tk.splitlist(event.data)
        if not files:
            return

        file_path = files[0]
        if not os.path.isfile(file_path):
            return

        if self.app.is_modified:
            if not self.app.menu_handler.check_save_before_action():
                return

        ext = os.path.splitext(file_path)[1].lower()
         
        try:
            if ext == '.grid':
                self.app.last_json_filepath = file_path
                self.app.save_config()
                self.app.menu_handler._load_from_path(file_path, show_popup=True)
            elif ext in ['.mscz', '.mscx']:
                self.app.last_musescore_filepath = file_path
                self.app.save_config()
                 
                self.app.root.config(cursor="watch")
                self.app.root.update_idletasks()
                try:
                    if hasattr(self.app.menu_handler, '_load_musescore_from_path'):
                        self.app.menu_handler._load_musescore_from_path(file_path)
                    elif hasattr(self.app.menu_handler, 'load_musescore'):
                        self.app.menu_handler.load_musescore()
                    else:
                        messagebox.showinfo("Info", f"Fichier MuseScore détecté : {os.path.basename(file_path)}")
                finally:
                    self.app.root.config(cursor="")
                     
            elif ext in ['.sgu', '.mgu', '.zip']:
                self.app.last_biab_filepath = file_path
                self.app.save_config()
                self._load_biab_from_path(file_path)
            else:
                messagebox.showwarning("Format non supporté", f"Le fichier '{os.path.basename(file_path)}' n'est pas un format reconnu (.grid, .mscz, .mscx, .sgu, .mgu, .zip).")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier déposé :\n{e}")