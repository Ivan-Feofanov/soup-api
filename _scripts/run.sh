#!/usr/bin/env sh

# Run server
gunicorn core.wsgi:application

