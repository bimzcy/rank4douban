#!/usr/bin/env bash

SHELL_FOLDER=$(cd "$(dirname "$0")";pwd)

cd $SHELL_FOLDER
git pull
python3 update_snippets.py
python3 build_data.py

DATE=`date +%Y-%m-%d`
git commit -a -m ":arrow_up: Daily update at $DATE"
git push

