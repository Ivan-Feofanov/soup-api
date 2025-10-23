#!/usr/bin/env sh

# Run server
gunicorn core.wsgi:application --bind 0.0.0.0:"$PORT"

