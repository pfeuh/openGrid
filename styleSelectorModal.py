#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk


class StyleSelectorModal:
    """Petite fenêtre modale pour chercher et choisir un style depuis le catalogue de l'arrangeur."""

    def __init__(self, parent, catalog_path, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Sélection du Style")
        self.window.geometry("400x450")
        self.window.update_idletasks()
        self.window.grab_set()

        self.catalog_path = catalog_path
        self.callback = callback
        self.catalog = self.load_styles()
        self.filtered_data = list(self.catalog)

        # Recherche
        lbl = tk.Label(
            self.window,
            text="Rechercher un style ou une catégorie :",
            font=("Helvetica", 10),
        )
        lbl.pack(anchor="w", padx=10, pady=(10, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_styles)
        self.entry = tk.Entry(
            self.window, textvariable=self.search_var, font=("Helvetica", 12)
        )
        self.entry.pack(fill="x", padx=10, pady=5)
        self.entry.focus()

        # Liste
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(frame, font=("Helvetica", 11), selectmode=tk.SINGLE)
        scrollbar = tk.Scrollbar(
            frame, orient="vertical", command=self.listbox.yview
        )
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<Double-1>", lambda event: self.valider())

        # Bouton valider
        btn = tk.Button(
            self.window,
            text="Sélectionner ce Style",
            font=("Helvetica", 11, "bold"),
            bg="#28a745",
            fg="white",
            command=self.valider,
        )
        btn.pack(fill="x", padx=10, pady=10)

        self.update_listbox()

    def load_styles(self):
        if os.path.isfile(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur de lecture du catalogue : {e}")
        return []

    def filter_styles(self, *args):
        q = self.search_var.get().lower()
        if not q:
            self.filtered_data = list(self.catalog)
        else:
            self.filtered_data = [
                s
                for s in self.catalog
                if q in s.get("name", "").lower() or q in s.get("category", "").lower()
            ]
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.filtered_data:
            sig_str = s.get("sig", "4/4")
            tempo_val = s.get("tempo", 120)
            name_val = s.get("name", "Inconnu")
            cat_val = s.get("category", "Général")
            self.listbox.insert(
                tk.END,
                f"{name_val}  —  [{cat_val}]  ({tempo_val} BPM, {sig_str})",
            )
        if self.filtered_data:
            self.listbox.selection_set(0)

    def valider(self):
        sel = self.listbox.curselection()
        if sel:
            style_info = self.filtered_data[sel[0]]
            if self.callback:
                self.callback(style_info)
        self.window.destroy()