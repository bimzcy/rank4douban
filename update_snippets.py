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


class DBSearch(object):
    def __init__(self, filename, rowname):
        rank_file = os.path.join('.', 'data', filename)
        f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
        self.csv = [row for row in f_csv]
        self.old_list = [(row[rowname], row['dbid']) for row in self.csv]

    def get_dbid(self, iden_id, **kwargs):
        item_dbid_search = list(filter(lambda x: x[0] == iden_id, self.old_list))
        if len(item_dbid_search) > 0:  # Use old
            return item_dbid_search[0][1]
        elif kwargs.get("imdbid"):
            return self.get_dbid_from_imdbid(kwargs.get("imdbid"))
        else:
            return self.get_dbid_from_name(kwargs.get("title"), kwargs.get("year"))

    @staticmethod
    def get_dbid_from_imdbid(imdbid):
        time.sleep(5 + random.randint(1, 20))
        r = requests.get("https://api.douban.com/v2/movie/imdb/{}".format(imdbid))
        rj = r.json()
        id_link = rj.get("id") or rj.get("alt") or rj.get("mobile_link")
        dbid = re.search('/(?:movie|subject)/(\d+)/?', id_link).group(1)
        return int(dbid)

    @staticmethod
    def get_dbid_from_name(name, year):
        time.sleep(5 + random.randint(1, 20))
        r = requests.get("https://api.douban.com/v2/movie/search?q={}".format(name))
        rj = r.json()
        all_subject = rj.get("subjects")
        try:
            chose_subject = list(filter(lambda x: x["year"] == str(year), all_subject))

            if len(chose_subject) > 0:
                return chose_subject[0].get("id")
        except Exception:
            print(name, year)
            print(rj)
            if rj.get("msg"):
                time.sleep(random.randint(5,20) * 60)


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
    search = DBSearch("01_IMDbtop250.csv", "imdbid")

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
        item_dbid = search.get_dbid(item_imdbid, imdbid=item_imdbid)

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "imdbid": item_imdbid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list("01_IMDbtop250.csv", ['rank', 'title', 'year', 'imdbid', 'dbid'], top_list)
    write_snippets_json('01_IMDbtop250.json', {
        "title": "IMDb Top 250",
        "short_title": "IMDb Top 250",
        "href": "https://www.imdb.com/chart/top",
        "top": 1,
        "list": {str(i["dbid"]): i['rank'] for i in top_list},
    })


def update_afi_top_100():
    search = DBSearch("02_AFilist.csv", "afiid")

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
        item_dbid = search.get_dbid(item_afiid, titme=item_title, year=item_year)
        new = {"rank": item_rank, "title": item_title, 'year': item_year, "afiid": item_afiid, "dbid": item_dbid}
        top_list.append(new)

    # Write Data list and snippets file
    write_data_list("02_AFilist.csv", ['rank', 'title', 'year', 'afiid', 'dbid'], top_list)
    write_snippets_json('02_AFIlist.json', {
        "title": "美国电影学会（AFI）“百年百大”排行榜",
        "short_title": "AFI Top 100",
        "href": "http://www.afi.com/100years/movies10.aspx",
        "top": 2,
        "list": {str(i["dbid"]): i['rank'] for i in top_list},
    })


def update_cclist():
    search = DBSearch("03_CClist.csv", "ccid")

    top_list = search.csv   # Use old list for CC list only append item
    last_check_spine = max(map(lambda x: int(x["spine"]), search.csv))

    top_list_raw = get_list_raw("https://www.criterion.com/shop/browse/list?sort=spine_number",
                                "#gridview > tbody > tr")
    for item in top_list_raw:
        item_spine = item.find("td", class_="g-spine").get_text(strip=True).zfill(4)
        if item_spine and int(item_spine) > last_check_spine:  # We only record those item which has spine number
            item_search = re.search("/(?P<type>films|boxsets)/(?P<num>\d+)", item["data-href"])
            item_type = item_search.group("type")
            if item_type == "films":  # This item is films type
                item_num = item_search.group("num")
                item_title = item.find("td", class_="g-title").get_text(strip=True)
                item_year = item.find("td", class_="g-year").get_text(strip=True)
                item_dbid = search.get_dbid(item_num, title=item_title, year=item_year)

                new = {"spine": item_spine, "title": item_title, 'year': item_year, "ccid": item_num, "dbid": item_dbid}
                top_list.append(new)
                print(new)
            elif item_type == "boxsets":
                boxset_list_raw = get_list_raw(item["data-href"],
                                               "div.left > div > div > section.film-sets-list > div > ul > a")
                for item1 in boxset_list_raw:
                    item1_search = re.search("/(?P<type>films|boxsets)/(?P<num>\d+)", item1["href"])
                    item1_num = item1_search.group("num")
                    item1_title = item1.find("p", class_="film-set-title").get_text(strip=True)
                    item1_year = item1.find("p", class_="film-set-year").get_text(strip=True)
                    item1_dbid = search.get_dbid(item1_num, title=item1_title, year=item1_year)
                    new = {"spine": item_spine, "title": item1_title, 'year': item1_year, "ccid": item1_num,
                           "dbid": item1_dbid}
                    top_list.append(new)
    write_data_list("03_CClist.csv", ['spine', 'title', 'year', 'ccid', 'dbid'], top_list)
    write_snippets_json('03_CClist.json', {
        "title": "The Criterion Collection 标准收藏",
        "short_title": "CC标准收藏编号",
        "href": "https://www.criterion.com/shop/browse/list?sort=spine_number",
        "top": 3,
        "list": {str(i["dbid"]): i['spine'] for i in top_list},
        "prefix": "#",
    })


def update_ss_(csvfile, jsonfile, reqlink, basedict):
    # Read our old data file
    search = DBSearch(csvfile, "bfid")

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
        item_dbid = search.get_dbid(item_bfid, title=item_title, year=item_year)

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "bfid": item_bfid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list(csvfile, ['rank', 'title', 'year', 'bfid', 'dbid'], top_list)
    basedict["list"] = {str(i["dbid"]): i['rank'] for i in top_list}
    write_snippets_json(jsonfile, basedict)


def update_sscritics():
    update_ss_("04_SScritics.csv", '04_SScritics.json',
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics", {
                   "title": "《视与听》影史最佳影片-影评人Top100",
                   "short_title": "视与听影评人百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics",
                   "top": 4,
               })


def update_ssdirectors():
    update_ss_("05_SSdirectors.csv", '05_SSdirectors.json',
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors", {
                   "title": "《视与听》影史最佳影片-导演Top100",
                   "short_title": "视与听导演百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors",
                   "top": 5,
               })


if __name__ == '__main__':
    update_imdb_top_250()
    #update_afi_top_100()
    update_cclist()
    #update_sscritics()
    #update_ssdirectors()
