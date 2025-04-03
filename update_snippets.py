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
import cloudscraper
from bs4 import BeautifulSoup

headers = {
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
}


scraper = cloudscraper.create_scraper()

remote_map = {
    'imdbid': {  # IMDb
        'url': 'https://ourbits.github.io/PtGen/internal_map/douban_imdb_map.json',
        'douban_key': 'dbid'
    },
    'bgm_id': {  # Bangumi
        'url': 'https://rhilip.github.io/BangumiExtLinker/data/anime_map.json',
        'douban_key': 'douban_id'
    }
}

for key in remote_map.keys():
    r = requests.get(remote_map[key]['url'])
    remote_map[key]['data'] = r.json()

class DBSearch(object):
    def __init__(self, filename, pk):
        rank_file = os.path.join('.', 'data', filename)
        f_csv = csv.DictReader(open(rank_file, encoding='utf-8'))
        self.csv = list(f_csv)
        self.pk = pk

    def get_old_row(self, value):
        row_search = [i for i in self.csv if i[self.pk] == value]
        if len(row_search) > 0:
            return row_search[0]

    def get_dbid(self, iden_id, **kwargs):
        old_row = self.get_old_row(iden_id)
        if old_row is not None and old_row.get('dbid') != '':  # Use old
            return old_row.get('dbid')
        else:
            # 首先从公开的map中搜索
            for (key, map_value) in remote_map.items():
                if kwargs.get(key):
                    t = [i for i in map_value['data'] if i[key] == kwargs[key]]
                    if len(t) > 0:
                        return t[0][map_value['douban_key']]

            # 如果公开的map中没有对应的信息，则尝试使用title从豆瓣搜索
            q = kwargs.get("imdbid") or kwargs.get("title")
            return self.get_dbid_from_search(q, kwargs.get("year"))

    @staticmethod
    def get_dbid_from_search(q, year=None):
        time.sleep(random.randint(1, 5))

        """ subject_suggest 目前不返回任何数据，弃用
        r = scraper.get("https://movie.douban.com/j/subject_suggest",
                         params={"q": q})
        all_subject = r.json()
        """

        r = scraper.get("https://www.douban.com/search", params={"q": q, 'cat': 1002})
        rb = BeautifulSoup(r.text, 'lxml')
        all_subject = []
        for subject in rb.select('div.result-list div.result'):
            another = subject.select_one('div.title a[onclick]')
            title = another.get_text(strip=True)
            sid = re.search(r'sid: (\d+)', another.attrs['onclick']).group(1)
            year = subject.select_one('span.subject-cast').get_text(strip=True).split(' / ')[-1]
            all_subject.append({'id': sid, 'title': title, 'year': year})

        if year:
            all_subject = list(filter(lambda x: x.get("year") == str(year), all_subject))

        if len(all_subject) > 0:
            return all_subject[0].get("id")

        return ""

def request_with_bs4(link, pass_cf = True, **kwargs):
    if pass_cf:
        top_req = scraper.get(link)
    else:
        top_req = requests.get(link, headers=headers, **kwargs)
    top_req.encoding = "utf-8"
    return BeautifulSoup(top_req.text, 'lxml')

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
        subjects_req = request_with_bs4(f'https://movie.douban.com/top250?start={start_}')
        for subject in subjects_req.select('ol.grid_view > li'):
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
    top_list_req = request_with_bs4('https://www.imdb.com/chart/top', pass_cf=False)
    next_data_json = top_list_req.select_one('script#__NEXT_DATA__').get_text(strip=True)
    top_list_raw = json.loads(next_data_json)['props']['pageProps']['pageData']['chartTitles']['edges']
    
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
    top_list_req = request_with_bs4('http://www.afi.com/100years/movies10.aspx')
    for item in top_list_req.select('#subcontent > div.pollListWrapper > div.pollList > div.listItemWrapper'):
        item_text = item.get_text(strip=True)
        item_search = re.search(r'(\d+)\.(.+?)\((\d+)\)', item_text)
        item_rank = item_search.group(1)
        item_title = item_search.group(2).strip()
        item_year = int(item_search.group(3))
        if item_title == "SUNRISE" and item_year == 1927:
            item_afiid = 12490
        else:
            item_afiid = re.search(r"Movie=(\d+)", item.find("a")["href"]).group(1)
        item_dbid = search.get_dbid(item_afiid, title=item_title, year=item_year)
        new = {"rank": item_rank, "title": item_title, 'year': item_year, "afiid": item_afiid, "dbid": item_dbid}
        top_list.append(new)

    # Write Data list
    write_data_list("02_AFilist.csv", ['rank', 'title', 'year', 'afiid', 'dbid'], top_list)


def update_cclist():
    search = DBSearch("03_CClist.csv", "ccid")

    top_list = search.csv  # Use old list for CC list only append item
    last_check_spine = max(map(lambda x: int(x["spine"]), search.csv))

    top_list_req = request_with_bs4('https://www.criterion.com/shop/browse/list?sort=spine_number')
    for item in top_list_req.select("#gridview > tbody > tr"):
        item_spine = item.find("td", class_="g-spine").get_text(strip=True).zfill(4)
        if item_spine and int(item_spine) > last_check_spine:  # We only record those item which has spine number
            item_search = re.search(r"/(?P<type>films|boxsets)/(?P<num>\d+)", item["data-href"])
            item_type = item_search.group("type")
            if item_type == "films":  # This item is films type
                item_num = item_search.group("num")
                item_title = item.find("td", class_="g-title").get_text(strip=True)
                item_year = item.find("td", class_="g-year").get_text(strip=True)
                item_dbid = search.get_dbid(item_num, title=item_title, year=item_year)

                new = {"spine": item_spine, "title": item_title, 'year': item_year, "ccid": item_num, "dbid": item_dbid}
                top_list.append(new)
            elif item_type == "boxsets":
                boxset_list_req = request_with_bs4(item["data-href"])
                for item1 in boxset_list_req.select("div.left > div > div > section.film-sets-list > div > ul > a"):
                    item1_search = re.search(r"/(?P<type>films|boxsets)/(?P<num>\d+)", item1["href"])
                    item1_num = item1_search.group("num")
                    item1_title = item1.find("p", class_="film-set-title").get_text(strip=True)
                    item1_year = item1.find("p", class_="film-set-year").get_text(strip=True)
                    item1_dbid = search.get_dbid(item1_num, title=item1_title, year=item1_year)
                    new = {"spine": item_spine, "title": item1_title, 'year': item1_year, "ccid": item1_num,
                           "dbid": item1_dbid}
                    top_list.append(new)
    write_data_list("03_CClist.csv", ['spine', 'title', 'year', 'ccid', 'dbid'], top_list)


def update_ss_(csvfile, reqlink):
    # Read our old data file
    search = DBSearch(csvfile, "bfid")

    # Get rank list and update data file
    top_list = []
    top_list_req = request_with_bs4(reqlink)
    for item in top_list_req.select("#region-content-left-1 > div > div > div > div > div > div:nth-of-type(2) > div:nth-of-type(2) > h3"):
        item_text = item.get_text(" ", strip=True)
        if re.search('Histoire', item_text):
            item_search = re.search(r'(\d+) (.+)', item_text)
            item_year = 1989
            item_bfid = "Histoire"
        else:
            item_search = re.search(r'(\d+) (.+?)\((\d{4})\)', item_text)
            item_year = int(item_search.group(3))
            item_bfid = re.search("films-tv-people/(.+)$", item.find("a")["href"]).group(1)
        item_rank = item_search.group(1)
        item_title = item_search.group(2).strip()
        item_dbid = search.get_dbid(item_bfid, title=item_title, year=item_year)

        top_list.append({"rank": item_rank, "title": item_title, 'year': item_year, "bfid": item_bfid, "dbid": item_dbid})

    # Write Data list and snippets file
    write_data_list(csvfile, ['rank', 'title', 'year', 'bfid', 'dbid'], top_list)


# 《视与听》影史最佳影片-影评人Top100
def update_sscritics():
    update_ss_("04_SScritics.csv", "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/critics")

# 《视与听》影史最佳影片-导演Top100
def update_ssdirectors():
    update_ss_("05_SSdirectors.csv", "https://www.bfi.org.uk/films-tv-people/sightandsoundpoll2012/directors")

def update_bgm_top_250():
    search = DBSearch("06_Bangumitop250.csv", "bgmid")

    top_list = []
    for p in range(1, 12):  # From page 1 - 11
        top_list_req = request_with_bs4(f'https://bgm.tv/anime/browser?sort=rank&page={p}')
        for item in top_list_req.select("ul#browserItemList > li"):
            item_rank = re.search(r"\d+", item.find("span", class_="rank").get_text(strip=True)).group(0)
            if int(item_rank) > 250:
                break

            item_name_cn = item.find("a", class_="l").get_text(strip=True)
            item_name = item.find("small", class_="grey").get_text(strip=True) if item.find("small", class_="grey") else ""
            item_info = item.find("p", class_="info tip").get_text(strip=True)

            item_date_match = re.search(r"(\d{4})[年-](\d{1,2}[月-])?(\d{1,2}日?)?", item_info)
            item_date = item_date_match.group(0) if item_date_match else time.strftime("%Y")

            item_bgmid = re.search(r"\d+", item["id"]).group(0)
            item_dbid = search.get_dbid(item_bgmid, title=item_name_cn, year=re.search(r"(\d{4})", item_date).group(1), bgm_id=item_bgmid)

            data = {"rank": item_rank, "name_cn": item_name_cn, 'name': item_name, 'date': item_date,
                    "bgmid": item_bgmid, "dbid": item_dbid}
            top_list.append(data)

    write_data_list("06_Bangumitop250.csv", ["rank", "name_cn", "name", "date", "bgmid", "dbid"], top_list)

def update_letterboxed_top_250():
    search = DBSearch("08_letterboxed_top_250.csv", "film_id")
    top_list = []
    for p in range(1, 4): # From page 1-3
        top_list_req = request_with_bs4(f'https://letterboxd.com/dave/list/official-top-250-narrative-feature-films/page/{p}/')
        for item in top_list_req.select("ul.film-list li.numbered-list-item"):
            rank = item.select_one('p.list-number').get_text(strip=True)
            div_another = item.select_one('div.film-poster')
            film_id = div_another.attrs['data-film-id']
            old_data = search.get_old_row(film_id)
            if old_data:
                data = old_data
                data['rank'] = rank
            else:
                target_link = f'https://letterboxd.com{div_another.attrs["data-target-link"]}'
                link_req = request_with_bs4(target_link)
                title = link_req.select_one('h1.primaryname').get_text(strip=True)
                year = link_req.select_one('div.releaseyear a').get_text(strip=True)

                imdb_id = ''
                imdb_another = link_req.select_one('a[data-track-action="IMDb"]')
                if imdb_another:
                    imdb_id = re.search(r'(tt\d+)', imdb_another.attrs['href']).group(1)

                dbid = search.get_dbid(film_id, title=title, imdbid=imdb_id, year=year)

                data = {
                    "rank": rank,
                    "title": title,
                    "year": year,
                    "film_id": film_id,
                    "imdbid": imdb_id,
                    "dbid": dbid,
                }

            top_list.append(data)

    write_data_list("08_letterboxed_top_250.csv", ["rank", "title", "year", "film_id", "imdbid", "dbid"], top_list)


if __name__ == '__main__':
    update_douban()
    update_imdb_top_250()
    update_bgm_top_250()
    update_cclist()
    update_letterboxed_top_250()

    # No need to update this rank list for may not update
    # update_afi_top_100()
    # update_sscritics()
    # update_ssdirectors()
