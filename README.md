# rank4douban
IMDb, CC, MOC, FIB, all kinds of billboard that connect the item title with douban ID.

# How to build rank list

1. upload rank data file like `01_IMDbtop250.csv` in `data` dir.

   - The file name MUST obey the regexr rule `\d{2}_.+?\.csv` and is a csv file.
   - The csv file MUST have headers and the first row must be `rank` or `spine`, and with a row named `dbid`.

2. Assign rank list data in `data\00_snippets.csv` with those information.

| Name       | Descr         | Sample           |
| -------------|:--------------:|:--------------:|
| file | The name of csv file | `03_CClist.csv` |
| title | The title of rank list | `The Criterion Collection 标准收藏` |
| short_title | The short title of rank list | `CC标准收藏编号` |
| href | The homepage url of rank list | `https://www.criterion.com/shop/browse/list?sort=spine_number` |
| other | The other key you want to assign in json file,the format like `{key1}:{value1}|{key2}:{value2}` | `prefix:#` |

3. If the rank list want to update automatically, you MUST write update function in `update_snippets.py`

4. Run those Python3 script.

```bash
python update_snippets.py
python build_data.py
```

