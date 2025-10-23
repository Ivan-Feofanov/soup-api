#!/usr/bin/env sh

# Run server
python -m gunicorn core.wsgi:application --bind 0.0.0.0:8000
