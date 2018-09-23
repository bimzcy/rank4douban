# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

"""
This script do this things:
1. convert raw data csv to snippets json.
2. merge all json file from snippets to generation the out json file `data.json`
"""

import os
import csv
import json
import time

data_dir = os.path.join(".", "data")
snippets_descr_csv = os.path.join(data_dir, "00_snippets.csv")
snippets_dir = os.path.join(".", "snippets")
out_json = os.path.join(".", "data.json")


def convert():
    with open(snippets_descr_csv, encoding='utf-8') as f:
        data_csv_descr = list(csv.DictReader(f))
    for raw_data in data_csv_descr:
        data_csv_file = os.path.join(data_dir, raw_data["file"])
        data_csv = csv.DictReader(open(data_csv_file, encoding='utf-8'))
        rank_row = data_csv.fieldnames[0]
        data_list = {row["dbid"]: row[rank_row] for row in data_csv}

        json_data = {
            "title": raw_data["title"],
            "short_title": raw_data["short_title"],
            "href": raw_data["href"],
            "top": int(raw_data["file"][:2]),
            "list": data_list
        }

        if raw_data["other"]:
            other = (raw_data["other"] + "|").split("|")
            for i in [i for i in other if i != ""]:
                k, v = i.split(":")
                if k and v:
                    json_data[k] = v

        json_file = os.path.join(snippets_dir, raw_data["file"].replace(".csv", ".json"))
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=3, sort_keys=True, ensure_ascii=False)


def merge():
    temp_dict = {}
    for file in os.listdir(snippets_dir):
        snippet_file = os.path.join(snippets_dir, file)
        snippet_name = file[3:-5]
        with open(snippet_file, 'r', encoding='utf-8') as f:
            temp_snippet = json.load(f)
            temp_dict[snippet_name] = temp_snippet

    temp_dict["updated"] = int(time.time())
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(temp_dict, f, indent=3, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    convert()
    merge()
