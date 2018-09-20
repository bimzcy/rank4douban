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
    time.sleep(5 + random.randint(1, 20))
    r = requests.get("https://api.douban.com/v2/movie/imdb/{}".format(imdbid))
    rj = r.json()
    id_link = rj.get("id") or rj.get("alt") or rj.get("mobile_link")
    dbid = re.search('/(?:movie|subject)/(\d+)/?', id_link).group(1)
    return int(dbid)


def get_dbid_from_name(name, year):
    time.sleep(5 + random.randint(1, 20))
    r = requests.get("https://api.douban.com/v2/movie/search?q={}".format(name))
    rj = r.json()
    all_subject = rj.get("subjects")
    chose_subject = list(filter(lambda x: x["year"] != "" and int(x["year"]) == int(year), all_subject))

    if len(chose_subject) > 0:
        return chose_subject[0].get("id")
    else:
        return all_subject[0].get("id")


def update_imdb_top_250():
    # Read our old data file
    rank_file = os.path.join('.', 'data', 'IMDbtop250.csv')
    f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
    old_rank_list = [(row['imdbid'], row['dbid']) for row in f_csv]

    # Get new top 250 rank list and update data file
    imdb_top_list = []
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

        item_dbid_search = list(filter(lambda x: x[0] == item_imdbid, old_rank_list))
        if len(item_dbid_search) > 0:  # Use old
            item_dbid = item_dbid_search[0][1]
        else:
            item_dbid = get_dbid_from_imdbid(item_imdbid)

        imdb_top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "imdbid": item_imdbid, "dbid": item_dbid})

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
            "list": {str(i["dbid"]): i['rank'] for i in imdb_top_list},
            "update": int(time.time())
        }, f, indent=3, sort_keys=True)


def update_afi_top_100():
    # Read our old data file
    rank_file = os.path.join('.', 'data', 'AFilist.csv')
    f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
    old_rank_list = [(row['afiid'], row['dbid']) for row in f_csv]

    # Get top 100 afilist and update data file
    afi_top_list = []
    afi_top_req = requests.get("http://www.afi.com/100years/movies10.aspx", headers=headers)
    afi_top_bs = BeautifulSoup(afi_top_req.text, 'lxml')
    afi_top_list_raw = afi_top_bs.select("#subcontent > div.pollListWrapper > div.pollList > div.listItemWrapper")

    for item in afi_top_list_raw:
        item_text = item.get_text(strip=True)
        item_search = re.search('(\d+)\.(.+?)\((\d+)\)', item_text)
        item_rank = item_search.group(1)
        item_title = item_search.group(2).strip()
        item_year = int(item_search.group(3))
        if item_title == "SUNRISE" and item_year == 1927:
            item_afiid = 12490
        else:
            item_afiid = re.search("Movie=(\d+)", item.find("a")["href"]).group(1)
        item_dbid_search = list(filter(lambda x: x[0] == item_afiid, old_rank_list))
        if len(item_dbid_search) > 0:  # Use old
            item_dbid = item_dbid_search[0][1]
        else:
            item_dbid = get_dbid_from_name(item_title, item_year)

        afi_top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "afiid": item_afiid, "dbid": item_dbid})

        # Save AFI top 100 rank list for next time used
    with open(rank_file, 'w', encoding='utf-8') as f:
        f_csv = csv.DictWriter(f, ['rank', 'title', 'year', 'afiid', 'dbid'], dialect=csv.unix_dialect)
        f_csv.writeheader()
        f_csv.writerows(afi_top_list)

    # Update snippets file
    snippets_json_file = os.path.join('.', 'snippets', '02_AFIlist.json')
    with open(snippets_json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "title": "美国电影学会（AFI）“百年百大”排行榜",
            "short_title": "AFI Top 100",
            "href": "http://www.afi.com/100years/movies10.aspx",
            "top": 2,
            "list": {str(i["dbid"]): i['rank'] for i in afi_top_list},
            "update": int(time.time())
        }, f, indent=3, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    update_imdb_top_250()
    update_afi_top_100()
