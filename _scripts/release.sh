#!/usr/bin/env sh
# Migrate database
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
