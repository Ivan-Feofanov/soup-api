#!/usr/bin/env sh

# Run server
exec gosu app gunicorn core.wsgi:application

