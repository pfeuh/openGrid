#!/usr/bin/python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

def open_measure_editor(root, bar_obj, on_save_callback):
    """Ouvre une fenêtre modale Tkinter dédiée pour éditer en détail une mesure (Bar)."""
    popup = tk.Toplevel(root)
    popup.title(f"Édition avancée - Mesure {bar_obj.number}")
    popup.geometry("380x310")
    
    # Correction pour s'assurer que la fenêtre est affichée avant d'appliquer le grab modal
    popup.update_idletasks()
    popup.grab_set()

    # 1. Accords
    ttk.Label(popup, text="Accords (séparés par des espaces) :", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
    chords_var = tk.StringVar(value=" ".join(bar_obj.chords) if hasattr(bar_obj, 'chords') else "")
    entry_chords = ttk.Entry(popup, textvariable=chords_var, font=("Courier", 11), width=38)
    entry_chords.pack(padx=15, pady=2)
    entry_chords.focus()

    # 2. Voltas (ex: 1., 2.)
    ttk.Label(popup, text="Volta (ex: 1., 2.) :", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
    volta_var = tk.StringVar(value=str(getattr(bar_obj, 'volta', '')))
    entry_volta = ttk.Entry(popup, textvariable=volta_var, width=15)
    entry_volta.pack(anchor="w", padx=15, pady=2)

    # 3. Répétitions (Cases à cocher et spinbox)
    repeat_frame = ttk.Frame(popup)
    repeat_frame.pack(fill="x", padx=15, pady=10)

    start_repeat_var = tk.BooleanVar(value=bool(getattr(bar_obj, 'start_repeat', False)))
    chk_start = ttk.Checkbutton(repeat_frame, text="Début de répétition (𝄆)", variable=start_repeat_var)
    chk_start.pack(anchor="w", pady=2)

    end_repeat_val = getattr(bar_obj, 'end_repeat', 0)
    initial_end_val = int(end_repeat_val) if isinstance(end_repeat_val, int) and end_repeat_val > 0 else (2 if end_repeat_val else 0)
    
    end_repeat_var = tk.IntVar(value=initial_end_val)
    end_repeat_frame = ttk.Frame(repeat_frame)
    end_repeat_frame.pack(anchor="w", fill="x", pady=2)
    
    chk_end_box = ttk.Checkbutton(
        end_repeat_frame, 
        text="Fin de répétition (fois) :", 
        variable=tk.BooleanVar(value=end_repeat_var.get() > 0),
        command=lambda: end_repeat_var.set(2 if end_repeat_var.get() == 0 else 0)
    )
    chk_end_box.pack(side="left")
    
    spin_end_repeat = ttk.Spinbox(end_repeat_frame, from_=1, to=9, width=3, textvariable=end_repeat_var)
    spin_end_repeat.pack(side="left", padx=5)

    # Boutons d'action
    btn_frame = ttk.Frame(popup)
    btn_frame.pack(fill="x", padx=15, pady=15)

    def save_changes():
        new_text = chords_var.get().strip()
        bar_obj.chords = new_text.split() if new_text else []
        bar_obj.volta = volta_var.get().strip()
        bar_obj.start_repeat = start_repeat_var.get()
        bar_obj.end_repeat = end_repeat_var.get() if end_repeat_var.get() > 0 else 0
        
        if on_save_callback:
            on_save_callback()
        popup.destroy()

    ttk.Button(btn_frame, text="Annuler", command=popup.destroy).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Valider", command=save_changes).pack(side="right", padx=5)