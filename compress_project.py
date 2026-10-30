#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import zipfile
from datetime import datetime
from pathlib import Path

def compress_directory(target_path, output_filename=None):
    target_dir = Path(target_path).resolve()
    if not target_dir.is_dir():
        print(f"Erreur : '{target_dir}' n'est pas un dossier valide.")
        sys.exit(1)

    # Nom par défaut au format yymmddhhmmss.zip si non spécifié
    if not output_filename:
        output_filename = datetime.now().strftime('%y%m%d%H%M%S') + '.zip'

    output_path = Path(output_filename).resolve()

    print(f"Compression du dossier : {target_dir}")
    print(f"Archive de sortie : {output_path}")

    count = 0
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in target_dir.rglob('*'):
            # Exclusion de __pycache__
            if '__pycache__' in file_path.parts:
                continue
            
            # Exclusion des fichiers .zip
            if file_path.suffix.lower() == '.zip':
                continue
            
            # Exclusion de l'archive elle-même si elle est générée dans le dossier cible
            if file_path.resolve() == output_path:
                continue
            
            if file_path.is_file():
                arcname = file_path.relative_to(target_dir)
                zipf.write(file_path, arcname)
                count += 1

    print(f"Succès ! {count} fichiers compressés dans '{output_path.name}'.")

if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "."
    zip_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    compress_directory(path_arg, zip_name)