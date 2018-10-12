#!/usr/bin/env bash

SHELL_FOLDER=$(cd "$(dirname "$0")";pwd)

cd $SHELL_FOLDER
python3 update_snippets.py
python3 build_data.py

DATE=`date +%Y-%m-%d`
git commit -a -m "Daily update $DATE"
git pull

