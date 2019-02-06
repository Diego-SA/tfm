#!/usr/bin/env bash
python3 manage.py rqworker
python3 manage.py runserver 0.0.0.0:8000