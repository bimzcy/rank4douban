# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import re
import os
import csv
import json
import time
import random
import requests

from bs4 import BeautifulSoup

headers = {
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
}


def get_dbid_from_imdbid(imdbid):
    time.sleep(5)
    r = requests.get("https://api.douban.com/v2/movie/imdb/{}".format(imdbid))
    rj = r.json()
    id_link = rj.get("id") or rj.get("alt") or rj.get("mobile_link")
    dbid = re.search('/(?:movie|subject)/(\d+)/?', id_link).group(1)
    return int(dbid)


def get_dbid_from_name(name):
    pass


def update_imdb_top_250():
    # Read our old data file
    rank_file = os.path.join('.', 'data', 'IMDbtop250.csv')
    f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
    old_rank_list = [(row['rank'], row['imdbid'], row['dbid']) for row in f_csv]
    imdb_top_list = []

    # Get new top 250 rank list and update data file
    imdb_top_req = requests.get('https://www.imdb.com/chart/top', headers=headers)
    imdb_top_bs = BeautifulSoup(imdb_top_req.text, 'lxml')
    imdb_top_list_raw = imdb_top_bs.select('table[data-caller-name="chart-top250movie"] > tbody > tr > td.titleColumn')

    for item in imdb_top_list_raw:
        item_text = item.get_text(strip=True)
        item_search = re.search('(\d+)\.(.+?)\((\d+)\)', item_text)
        item_rank = item_search.group(1)
        item_title = item_search.group(2)
        item_year = item_search.group(3)
        item_imdbid = re.search("(tt\d+)", item.find("a")["href"]).group(1)

        item_dbid_search = list(filter(lambda x: x[1] == item_imdbid, old_rank_list))
        if len(item_dbid_search) > 0:  # Use old
            item_dbid = item_dbid_search[0][2]
        else:
            item_dbid = get_dbid_from_imdbid(item_imdbid)

        imdb_top_list.append({"rank": item_rank, "title": item_title, 'year': item_year, "imdbid": item_imdbid, "dbid": item_dbid})

    # Save IMDb top 250 rank list for next time used
    with open(rank_file, 'w', encoding='utf-8') as f:
        f_csv = csv.DictWriter(f, ['rank', 'title', 'year', 'imdbid', 'dbid'], dialect=csv.unix_dialect)
        f_csv.writeheader()
        f_csv.writerows(imdb_top_list)

    # Update snippets file
    snippets_json_file = os.path.join('.', 'snippets', '01_IMDbtop250.json')
    with open(snippets_json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "title": "IMDb Top 250",
            "short_title": "IMDb Top 250",
            "href": "https://www.imdb.com/chart/top",
            "top": 1,
            "list": {i["dbid"]: i['rank'] for i in imdb_top_list},
            "update": int(time.time())
        }, f, indent=3, sort_keys=True)


if __name__ == '__main__':
    update_imdb_top_250()
