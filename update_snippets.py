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


def get_old_data_list(filename, rowname):
    rank_file = os.path.join('.', 'data', filename)
    f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
    return [(row[rowname], row['dbid']) for row in f_csv]


def get_list_raw(link, selector) -> list:
    top_req = requests.get(link, headers=headers)
    top_bs = BeautifulSoup(top_req.text, 'lxml')
    return top_bs.select(selector)


def write_data_list(filename, header, data):
    rank_file = os.path.join('.', 'data', filename)
    with open(rank_file, 'w', encoding='utf-8') as f:
        f_csv = csv.DictWriter(f, header, dialect=csv.unix_dialect)
        f_csv.writeheader()
        f_csv.writerows(data)


def write_snippets_json(filename, data):
    snippets_json_file = os.path.join('.', 'snippets', filename)
    data["update"] = int(time.time())
    with open(snippets_json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=3, sort_keys=True, ensure_ascii=False)


def update_imdb_top_250():
    # Read our old data file
    old_rank_list = get_old_data_list("IMDbtop250.csv", "imdbid")

    # Get new top 250 rank list and update data file
    top_list = []
    top_list_raw = get_list_raw('https://www.imdb.com/chart/top',
                                'table[data-caller-name="chart-top250movie"] > tbody > tr > td.titleColumn')
    for item in top_list_raw:
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

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "imdbid": item_imdbid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list("IMDbtop250.csv", ['rank', 'title', 'year', 'imdbid', 'dbid'], top_list)
    write_snippets_json('01_IMDbtop250.json', {
        "title": "IMDb Top 250",
        "short_title": "IMDb Top 250",
        "href": "https://www.imdb.com/chart/top",
        "top": 1,
        "list": {str(i["dbid"]): i['rank'] for i in top_list},
    })


def update_afi_top_100():
    # Read our old data file
    old_rank_list = get_old_data_list("AFilist.csv", "afiid")

    # Get top 100 afilist and update data file
    top_list = []
    top_list_raw = get_list_raw("http://www.afi.com/100years/movies10.aspx",
                                "#subcontent > div.pollListWrapper > div.pollList > div.listItemWrapper")
    for item in top_list_raw:
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

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "afiid": item_afiid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list("AFilist.csv", ['rank', 'title', 'year', 'afiid', 'dbid'], top_list)
    write_snippets_json('02_AFIlist.json', {
        "title": "美国电影学会（AFI）“百年百大”排行榜",
        "short_title": "AFI Top 100",
        "href": "http://www.afi.com/100years/movies10.aspx",
        "top": 2,
        "list": {str(i["dbid"]): i['rank'] for i in top_list},
    })


def update_cclist():
    pass


def update_ss_(csvfile, jsonfile, reqlink, basedict):
    # Read our old data file
    old_rank_list = get_old_data_list(csvfile, "bfid")

    # Get rank list and update data file
    top_list = []
    top_list_raw = get_list_raw(reqlink,
                                "#region-content-left-1 > div > div > div > div > div > div:nth-of-type(2) > div:nth-of-type(2) > h3")
    for item in top_list_raw:
        item_text = item.get_text(" ", strip=True)
        print(item_text)
        if re.search('Histoire', item_text):
            item_search = re.search('(\d+) (.+)', item_text)
            item_year = 1989
            item_bfid = "Histoire"
        else:
            item_search = re.search('(\d+) (.+?)\((\d{4})\)', item_text)
            item_year = int(item_search.group(3))
            item_bfid = re.search("films-tv-people/(.+)$", item.find("a")["href"]).group(1)
        item_rank = item_search.group(1)
        item_title = item_search.group(2).strip()

        item_dbid_search = list(filter(lambda x: x[0] == item_bfid, old_rank_list))
        if len(item_dbid_search) > 0:  # Use old
            item_dbid = item_dbid_search[0][1]
        else:
            item_dbid = get_dbid_from_name(item_title, item_year)

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "bfid": item_bfid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list(csvfile, ['rank', 'title', 'year', 'bfid', 'dbid'], top_list)
    basedict["list"] = {str(i["dbid"]): i['rank'] for i in top_list}
    write_snippets_json(jsonfile, basedict)


def update_sscritics():
    update_ss_("SScritics.csv", '04_SScritics.json',
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics", {
                   "title": "《视与听》影史最佳影片-影评人Top100",
                   "short_title": "视与听影评人百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics",
                   "top": 4,
               })


def update_ssdirectors():
    update_ss_("SSdirectors.csv", '05_SSdirectors.json',
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors", {
                   "title": "《视与听》影史最佳影片-导演Top100",
                   "short_title": "视与听导演百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors",
                   "top": 5,
               })


if __name__ == '__main__':
    update_imdb_top_250()
    update_afi_top_100()
    update_cclist()
    update_sscritics()
    update_ssdirectors()
