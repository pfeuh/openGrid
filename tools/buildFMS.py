# -*- coding: utf-8 -*-

states = ("NORMAL", "REPEAT", "VOLTA")
variables = ["is_start", "is_end", "is_volta"]

for state in states:
    print(f"        if state == {state}:")
    for i in range(8):
        # Le premier est un 'if', les 7 suivants sont des 'elif'
        keyword = "if" if i == 0 else "elif"
        
        # Extraction des bits pour chaque variable (i de 0 à 7 -> 000 à 111)
        conds = []
        for idx, var_name in enumerate(variables):
            shift = 2 - idx
            val = (i >> shift) & 1
            not_str = "not " if val == 0 else ""
            conds.append(f"{not_str}{var_name}")
            
        cond_str = " and ".join(conds)
        print(f"            {keyword} {cond_str}:")
        print(f"                raise Exception(\"Not implemented!\")\n")
    print()