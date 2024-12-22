# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import re
import os
import csv
import time
import json
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
        self.csv = list(f_csv)
        self.old_list = [(row[rowname], row['dbid']) for row in self.csv]

    def get_dbid(self, iden_id, **kwargs):
        item_dbid_search = list(filter(lambda x: x[0] == iden_id, self.old_list))
        if len(item_dbid_search) > 0 and item_dbid_search[0][1] != '':  # Use old
            return item_dbid_search[0][1]
        else:
            q = kwargs.get("imdbid") or kwargs.get("title")
            return self.get_dbid_from_search(q, kwargs.get("year"))

    @staticmethod
    def get_dbid_from_search(q, year=None):
        time.sleep(random.randint(1, 5))
        r = requests.get("https://movie.douban.com/j/subject_suggest",
                         params={"q": q},
                         headers=headers)
        all_subject = r.json()

        if year:
            all_subject = list(filter(lambda x: x.get("year") == str(year), all_subject))

        if len(all_subject) > 0:
            return all_subject[0].get("id")

        return ''


def get_list_raw(link, selector) -> list:
    top_req = requests.get(link, headers=headers)
    top_req.encoding = "utf-8"
    top_bs = BeautifulSoup(top_req.text, 'lxml')
    return top_bs.select(selector)


def write_data_list(filename, header, data):
    rank_file = os.path.join('.', 'data', filename)
    with open(rank_file, 'w', encoding='utf-8') as f:
        f_csv = csv.DictWriter(f, header, dialect=csv.unix_dialect)
        f_csv.writeheader()
        f_csv.writerows(data)


def update_douban():
    top_list = []

    for start_ in range(0, 250, 25):
        time.sleep(random.randint(1, 5))
        subjects = get_list_raw('https://movie.douban.com/top250?start={}'.format(start_), 'ol.grid_view > li')
        for subject in subjects:
            try:
                all_title = ''.join(map(lambda x: x.get_text(), subject.find_all('span', class_='title')))
                all_title = all_title.replace('\xa0', ' ')

                if all_title.find('/') > -1:
                    titles = all_title.split('/')
                    title = titles[0].strip()
                    original_title = titles[1].strip()
                else:
                    title = original_title = all_title.strip()

                year = re.search(r'\d{4}', str(subject.find('p'))).group()
                dbid = re.search(r'https://movie.douban.com/subject/(\d+)', str(subject)).groups()[0]

                rating_num = subject.find('span', class_="rating_num").get_text(strip=True)
                rating_count = re.search(r'(\d+)人评价', str(subject)).groups()[0]

                top_list.append({
                    'rank': int(subject.find('em').get_text(strip=True)),
                    'title': title,
                    'original_title': original_title,
                    'year': year,
                    'rating_num': rating_num,
                    'rating_count': rating_count,
                    'dbid': dbid
                })
            except Exception:
                pass

    # Write Data list
    write_data_list("99_douban_top250.csv", ['rank', 'title', 'original_title', 'year', 'rating_num', 'rating_count', 'dbid'], top_list)


def update_imdb_top_250():
    # Read our old data file
    search = DBSearch("01_IMDbtop250.csv", "imdbid")

    # Get new top 250 rank list and update data file
    top_list = []
    top_list_req = get_list_raw('https://www.imdb.com/chart/top', 'script#__NEXT_DATA__')
    top_list_raw = json.loads(top_list_req[0].get_text(strip=True))['props']['pageProps']['pageData']['chartTitles']['edges']
    
    for item in top_list_raw:
        item_rank = item['currentRank']
        item_title = item['node']['titleText']['text']
        item_imdbid = item['node']['id']
        item_year = item['node']['releaseYear']['year']
        item_dbid = search.get_dbid(item_imdbid, imdbid=item_imdbid)

        top_list.append(
            {"rank": item_rank, "title": item_title, 'year': item_year, "imdbid": item_imdbid, "dbid": item_dbid})

    # Write Data list
    write_data_list("01_IMDbtop250.csv", ['rank', 'title', 'year', 'imdbid', 'dbid'], top_list)

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
        item_dbid = search.get_dbid(item_afiid, title=item_title, year=item_year)
        new = {"rank": item_rank, "title": item_title, 'year': item_year, "afiid": item_afiid, "dbid": item_dbid}
        top_list.append(new)

    # Write Data list
    write_data_list("02_AFilist.csv", ['rank', 'title', 'year', 'afiid', 'dbid'], top_list)


def update_cclist():
    search = DBSearch("03_CClist.csv", "ccid")

    top_list = search.csv  # Use old list for CC list only append item
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


def update_ss_(csvfile, reqlink, basedict):
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


def update_sscritics():
    update_ss_("04_SScritics.csv",
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics", {
                   "title": "《视与听》影史最佳影片-影评人Top100",
                   "short_title": "视与听影评人百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics",
                   "top": 4,
               })


def update_ssdirectors():
    update_ss_("05_SSdirectors.csv",
               "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors", {
                   "title": "《视与听》影史最佳影片-导演Top100",
                   "short_title": "视与听导演百佳",
                   "href": "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors",
                   "top": 5,
               })


def update_bgm_top_250():
    search = DBSearch("06_Bangumitop250.csv", "bgmid")

    top_list = []
    for p in range(1, 12):  # From page 1 - 11
        top_list_raw = get_list_raw('https://bgm.tv/anime/browser?sort=rank&page={}'.format(p),
                                    'ul#browserItemList > li')
        for item in top_list_raw:
            item_rank = re.search("\d+", item.find("span", class_="rank").get_text(strip=True)).group(0)
            if int(item_rank) > 250:
                break

            item_name_cn = item.find("a", class_="l").get_text(strip=True)
            item_name = item.find("small", class_="grey").get_text(strip=True) if item.find("small", class_="grey") else ""
            item_info = item.find("p", class_="info tip").get_text(strip=True)

            item_date_match = re.search("(\d{4})[年-](\d{1,2}[月-])?(\d{1,2}日?)?", item_info)
            item_date = item_date_match.group(0) if item_date_match else time.strftime("%Y")

            item_bgmid = re.search("\d+", item["id"]).group(0)
            item_dbid = search.get_dbid(item_bgmid, title=item_name_cn, year=re.search("(\d{4})", item_date).group(1))

            data = {"rank": item_rank, "name_cn": item_name_cn, 'name': item_name, 'date': item_date,
                    "bgmid": item_bgmid, "dbid": item_dbid}
            top_list.append(data)

    write_data_list("06_Bangumitop250.csv", ["rank", "name_cn", "name", "date", "bgmid", "dbid"], top_list)


if __name__ == '__main__':
    update_douban()
    update_imdb_top_250()
    update_bgm_top_250()
    update_cclist()

    # No need to update this rank list for may not update
    # update_afi_top_100()
    # update_sscritics()
    # update_ssdirectors()
