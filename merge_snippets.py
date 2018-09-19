# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

"""
This file merge all json file from snippets to generation the out json file `data.json`
"""

import os
import json

snippets_dir = os.path.join(".", "snippets")
out_json = os.path.join(".", "data.json")

if __name__ == '__main__':
    temp_dict = {}
    for file in os.listdir(snippets_dir):
        snippet_file = os.path.join(snippets_dir, file)
        snippet_name = file[3:-5]
        with open(snippet_file, 'r', encoding='utf-8') as f:
            temp_snippet = json.load(f)
            temp_dict[snippet_name] = temp_snippet

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(temp_dict, f, indent=3, sort_keys=True, ensure_ascii=False)
