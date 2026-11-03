# -*- coding: utf-8 -*-

import tkinter.filedialog as std_fd

# Tentative d'importation de tkfilebrowser pour un rendu amélioré sous Linux/Ubuntu
try:
    from tkfilebrowser import askopenfilename as tk_askopenfilename, asksaveasfilename as tk_asksaveasfilename, askopendirname as tk_askopendirname
    import tkinter.filedialog as fd

    def _adapt_args(kwargs):
        if 'filetypes' in kwargs:
            new_filetypes = []
            for name, pattern in kwargs['filetypes']:
                if isinstance(pattern, (list, tuple)):
                    pattern_str = "|".join(pattern)
                else:
                    pattern_str = pattern.replace(' ', '|')
                new_filetypes.append((name, pattern_str))
            kwargs['filetypes'] = new_filetypes
         
        # Désactive l'affichage des fichiers récents pour éviter le bug des index numériques sous Linux
        if 'show_recent' in tk_askopenfilename.__code__.co_varnames:
            kwargs['show_recent'] = False
             
        return kwargs

    def custom_askopenfilename(**kwargs):
        try:
            if 'parent' in kwargs and kwargs['parent']:
                kwargs['parent'].update_idletasks()
            return tk_askopenfilename(**_adapt_args(kwargs))
        except Exception:
            # Repli automatique sur le sélecteur natif standard en cas d'échec de tkfilebrowser
            return std_fd.askopenfilename(**kwargs)

    def custom_asksaveasfilename(**kwargs):
        try:
            if 'parent' in kwargs and kwargs['parent']:
                kwargs['parent'].update_idletasks()
            return tk_asksaveasfilename(**_adapt_args(kwargs))
        except Exception:
            # Repli automatique sur le sélecteur natif standard en cas d'échec de tkfilebrowser
            return std_fd.asksaveasfilename(**kwargs)

    # Exposition sous les noms standard pour que fd.askopenfilename fonctionne directement
    askopenfilename = custom_askopenfilename
    asksaveasfilename = custom_asksaveasfilename
    askopendirname = tk_askopendirname
    HAS_TKFILEBROWSER = True
except ImportError:
    HAS_TKFILEBROWSER = False
    # Si tkfilebrowser n'est pas disponible, on expose les standards directement
    askopenfilename = std_fd.askopenfilename
    asksaveasfilename = std_fd.asksaveasfilename
    askopendirname = std_fd.askopendirname