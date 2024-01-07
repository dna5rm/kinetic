#!/bin/env bash

if [ -x "./manage.py" ]; then
    rm db.sqlite3
    rm -rf root/__pycache__
    rm -rf ./checklist/__pycache__ ./checklist/migrations
    rm -rf ./fping/__pycache__ ./fping/migrations

    ./manage.py migrate
    ./manage.py makemigrations checklist
    ./manage.py makemigrations fping
    ./manage.py migrate

#  if [ -e "fping.sql" ]; then
#    sqlite3 db.sqlite3 < fping/fping_example.sql
#  fi

    echo
    echo "Run: ./manage.py createsuperuser"
fi
