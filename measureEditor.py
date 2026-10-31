#!/usr/bin/python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

def open_measure_editor(root, bar_obj, on_save_callback=None, on_close_callback=None, on_navigate_callback=None):
    """Ouvre une fenêtre modale Tkinter dédiée pour éditer en détail une mesure (Bar),
    avec gestion fluide de la navigation Précédent / Suivant sans fermer le popup."""
    popup = tk.Toplevel(root)
    popup.title(f"Édition avancée - Mesure {bar_obj.number}")
    popup.geometry("400x390")
    
    popup.update_idletasks()
    popup.grab_set()

    def close_popup():
        if on_close_callback:
            on_close_callback()
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", close_popup)

    # 1. Accords
    ttk.Label(popup, text="Accords (séparés par des espaces) :", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
    chords_var = tk.StringVar()
    entry_chords = ttk.Entry(popup, textvariable=chords_var, font=("Courier", 11), width=38)
    entry_chords.pack(padx=15, pady=2)
    entry_chords.focus()

    # 2. Interprétation Rythmique (Binaire / Ternaire)
    ttk.Label(popup, text="Interprétation des croches :", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
    ternary_var = tk.BooleanVar()
    chk_ternary = ttk.Checkbutton(popup, text="Mode Ternaire (Swing / Triplet)", variable=ternary_var)
    chk_ternary.pack(anchor="w", padx=15, pady=2)

    # 3. Voltas (ex: 1., 2.)
    ttk.Label(popup, text="Volta (ex: 1., 2.) :", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
    volta_var = tk.StringVar()
    entry_volta = ttk.Entry(popup, textvariable=volta_var, width=15)
    entry_volta.pack(anchor="w", padx=15, pady=2)

    # 4. Répétitions
    repeat_frame = ttk.Frame(popup)
    repeat_frame.pack(fill="x", padx=15, pady=10)

    start_repeat_var = tk.BooleanVar()
    chk_start = ttk.Checkbutton(repeat_frame, text="Début de répétition (𝄆)", variable=start_repeat_var)
    chk_start.pack(anchor="w", pady=2)

    end_repeat_var = tk.IntVar()
    end_repeat_checked_var = tk.BooleanVar()

    end_repeat_frame = ttk.Frame(repeat_frame)
    end_repeat_frame.pack(anchor="w", fill="x", pady=2)
    
    def on_checkbox_toggle():
        if end_repeat_checked_var.get():
            if end_repeat_var.get() == 0:
                end_repeat_var.set(2)
        else:
            end_repeat_var.set(0)

    def on_spinbox_change(*args):
        try:
            val = end_repeat_var.get()
            if val > 0:
                end_repeat_checked_var.set(True)
            else:
                end_repeat_checked_var.set(False)
        except tk.TclError:
            pass

    end_repeat_var.trace_add("write", on_spinbox_change)

    chk_end_box = ttk.Checkbutton(
        end_repeat_frame, 
        text="Fin de répétition (fois) :", 
        variable=end_repeat_checked_var,
        command=on_checkbox_toggle
    )
    chk_end_box.pack(side="left")
    
    spin_end_repeat = ttk.Spinbox(end_repeat_frame, from_=1, to=9, width=3, textvariable=end_repeat_var)
    spin_end_repeat.pack(side="left", padx=5)

    active_bar = {"obj": bar_obj}

    def load_bar_data(b):
        active_bar["obj"] = b
        popup.title(f"Édition avancée - Mesure {b.number}")
        
        chords_var.set(" ".join(b.chords) if hasattr(b, 'chords') and b.chords else "")
        
        current_ternary = getattr(b, 'ternary', False)
        ternary_var.set(False if current_ternary is None else current_ternary)
        
        volta_var.set(str(getattr(b, 'volta', '')))
        start_repeat_var.set(bool(getattr(b, 'start_repeat', False)))
        
        end_val = getattr(b, 'end_repeat', 0)
        init_end = int(end_val) if isinstance(end_val, int) and end_val > 0 else 0
        end_repeat_var.set(init_end)
        end_repeat_checked_var.set(init_end > 0)
        
        entry_chords.focus()
        entry_chords.select_range(0, tk.END)

    load_bar_data(bar_obj)

    def apply_changes_to_current_object():
        b = active_bar["obj"]
        new_text = chords_var.get().strip()
        raw_chords = new_text.split() if new_text else []
        
        total_beats = 4
        timesig_str = getattr(b, 'timesig', '')
        if timesig_str and '/' in timesig_str:
            try:
                total_beats = int(timesig_str.split('/')[0])
            except ValueError:
                pass

        num_chords = len(raw_chords)
        parsed_chords = []

        for idx, token in enumerate(raw_chords):
            if not token:
                continue
            
            if '@' in token:
                chd_part, beat_part = token.split('@', 1)
                chd_cap = chd_part[0].upper() + chd_part[1:] if chd_part else ""
                try:
                    bt = float(beat_part)
                except ValueError:
                    bt = 1.0 + idx * (total_beats / num_chords) if num_chords > 0 else 1.0
                parsed_chords.append((chd_cap, bt))
            else:
                chd_cap = token[0].upper() + token[1:] if token else ""
                if num_chords > 0:
                    bt = 1.0 + idx * (total_beats / num_chords)
                else:
                    bt = 1.0
                parsed_chords.append((chd_cap, bt))

        compressed_chords = []
        last_chord = None
        for chd, bt in parsed_chords:
            if chd != last_chord:
                compressed_chords.append((chd, bt))
                last_chord = chd

        formatted_chords = []
        for chd, bt in compressed_chords:
            if abs(bt - round(bt)) < 1e-4:
                bt_clean = int(round(bt))
                if bt_clean == 1:
                    formatted_chords.append(chd)
                else:
                    formatted_chords.append(f"{chd}@{bt_clean}")
            else:
                bt_rounded = round(bt, 3)
                formatted_chords.append(f"{chd}@{bt_rounded}")

        b.chords = formatted_chords
        b.ternary = ternary_var.get()
        b.volta = volta_var.get().strip()
        b.start_repeat = start_repeat_var.get()
        b.end_repeat = end_repeat_var.get() if end_repeat_var.get() > 0 else 0

    btn_frame = ttk.Frame(popup)
    btn_frame.pack(fill="x", padx=15, pady=15)

    nav_subframe = ttk.Frame(btn_frame)
    nav_subframe.pack(side="left")

    action_subframe = ttk.Frame(btn_frame)
    action_subframe.pack(side="right")

    def save_and_close():
        apply_changes_to_current_object()
        if on_save_callback:
            on_save_callback()
        close_popup()

    def navigate(direction):
        # 1. Sauvegarde les modifications de la mesure en cours dans l'objet
        apply_changes_to_current_object()
        if on_save_callback:
            on_save_callback()
        
        # 2. Demande au parent (openGrid.py) de basculer sur la mesure adjacente
        if on_navigate_callback:
            next_bar = on_navigate_callback(active_bar["obj"], direction)
            if next_bar:
                load_bar_data(next_bar)

    # Boutons Précédent / Suivant branchés
    btn_prev = ttk.Button(nav_subframe, text="< Précédent", command=lambda: navigate(-1))
    btn_prev.pack(side="left", padx=2)

    btn_next = ttk.Button(nav_subframe, text="Suivant >", command=lambda: navigate(1))
    btn_next.pack(side="left", padx=2)

    # Boutons Annuler / Valider
    ttk.Button(action_subframe, text="Annuler", command=close_popup).pack(side="right", padx=2)
    ttk.Button(action_subframe, text="Valider", command=save_and_close).pack(side="right", padx=2)