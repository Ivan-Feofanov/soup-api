#!/usr/bin/env sh

# Run server
exec gosu app uvicorn core.asgi:application --host 0.0.0.0 --port 8000

