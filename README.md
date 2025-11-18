### Soup API

Backend service for the Soup application: a Django 5.2 + Django Ninja Extra REST API with JWT authentication, Postgres, Docker support, and GitHub/Hobby deploy flows via Procfile.

#### Features
- Django Ninja Extra controllers under `/api/`
- JWT auth (access/refresh) with Google OAuth2 social login
- Users domain (profile read/update)
- Kitchen domain (recipes, drafts, ingredients, units, appliances)
- Postgres database, migrations, and static files pipeline
- CORS configured for a separate frontend
- Dockerfile (multi-stage, uv-managed venv), Procfile with release/web phases

---

### Tech stack
- Python 3.13
- Django 5.2
- django-ninja + ninja-extra, ninja-jwt
- social-auth-app-django
- Postgres (via `dj-database-url`)
- uv for dependency management (pyproject/uv.lock)
- gunicorn + gosu in container runtime
- pytest test suite

---

### Project layout
- `core/` — settings, URLs, api bootstrap
  - `core/api.py` — builds a `NinjaExtraAPI` instance, registers controllers/routers
  - `core/urls.py` — mounts admin at `/admin/` and the API at `/api/`
- `users/` — custom user model, auth endpoints, user APIs
  - `users/api/auth.py` — social login and token refresh endpoints
  - `users/api/users.py` — current-user endpoint and profile update
- `kitchen/` — domain modules for recipes, ingredients, appliances, etc.
- `_scripts/` — container entrypoint scripts
  - `run.sh` — gunicorn runner (web phase)
  - `release.sh` — `migrate` and `collectstatic` (release phase)
- `Dockerfile`, `Procfile` — container and deploy process
- `pyproject.toml`, `uv.lock` — dependencies with uv

---

### Local development

#### Prerequisites
- Python 3.13
- Postgres 14+ available locally, or a `DATABASE_URL`
- uv (recommended) or any PEP 517 compliant installer

#### 1) Clone and configure
```
git clone <your-fork-or-repo-url>
cd api
cp .env.example .env   # if you keep one, otherwise export env vars directly
```

Required environment variables (see also `core/settings.py`):
- `SECRET_KEY` — Django secret (any string in dev)
- `DEBUG` — `True` for local development
- `DATABASE_URL` — e.g. `postgres://postgres:postgres@localhost:5432/soup_db`
- `GOOGLE_CLIENT_ID` — Google OAuth2 client ID
- `GOOGLE_CLIENT_SECRET` — Google OAuth2 client secret
- `OPENAPI_GENERATOR_TOKEN` — optional token to access API docs when `DEBUG=False`
- `BE_HOSTNAME` — optional backend hostname to allow in `ALLOWED_HOSTS` (defaults to `localhost`)
- `FE_HOSTNAME` — optional frontend hostname to allow in `ALLOWED_HOSTS` (defaults to `localhost`)

Optional hosts/CORS notes:
- Allowed hosts include `127.0.0.1` plus values from `BE_HOSTNAME` and `FE_HOSTNAME` env vars
- CORS is enabled and default headers are extended for `x-email-verification-key` and `x-password-reset-key`
- If you need cross-origin requests, configure django-cors-headers origins in settings (no specific origins are hardcoded)

#### 2) Install dependencies

Using uv (fastest):
```
uv sync
```

Or with pip in a virtualenv:
```
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r <(uv export --no-dev)  # or use another exporter if uv not installed
```

#### 3) Prepare database
```
python manage.py migrate
python manage.py createsuperuser  # optional, for Django admin
```

#### 4) Run the server
```
python manage.py runserver 0.0.0.0:8000
```

Now available at:
- Admin: `http://localhost:8000/admin/`
- API root: `http://localhost:8000/api/`

---

### API and authentication

The API is built with Django Ninja Extra and mounted at `/api/`.

Auth flow:
- Social login (Google):
  - `POST /api/auth/login/{backend}/` with body `{ code, redirect_uri }`
  - The backend currently uses Google under the hood (`google-oauth2`)
  - On success returns `{ user, access_token, refresh_token }`
- Refresh token:
  - `POST /api/auth/token/refresh/` with body `{ refresh_token }`
  - Returns new `{ access_token, refresh_token }`

Protected endpoints require `Authorization: Bearer <access_token>` header.

Users API examples:
- `GET /api/users/me` — current user (JWT required)
- `PATCH /api/users/{uid}` — update own profile (username, handler, avatar)

Kitchen domain endpoints:
- Controllers are registered for recipes, drafts, ingredients, units, and appliances under `/api/`
- Inspect the OpenAPI docs for detailed routes and schemas

#### API docs

Interactive docs are available at `GET /api/docs` (served by Ninja/Ninja-Extra) with an access guard:
- In development (`DEBUG=True`): open access
- In production (`DEBUG=False`): one of the following is required:
  - Authenticated Django staff user, or
  - `X-Ninja-Token: <OPENAPI_GENERATOR_TOKEN>` request header

---

### Running with Docker

Build and run:
```
docker build -t soup-api .
docker run --rm -p 8000:8000 \
  -e SECRET_KEY=dev \
  -e DEBUG=True \
  -e DATABASE_URL=postgres://postgres:postgres@host.docker.internal:5432/soup_db \
  -e GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com \
  -e GOOGLE_CLIENT_SECRET=yyy \
  soup-api sh -c "_scripts/release.sh && _scripts/run.sh"
```

Notes:
- The image embeds a uv-managed virtual environment at `/app/.venv`
- `Procfile` defines two phases used by many PaaS providers:
  - `release: _scripts/release.sh` (migrations + collectstatic)
  - `web: _scripts/run.sh` (gunicorn)

---

### Testing

Run tests with pytest:
```
pytest
```

With coverage:
```
pytest --cov --cov-report=term-missing
```

Pytest is configured in `pyproject.toml` with `DJANGO_SETTINGS_MODULE=core.settings`.

---

### Environment variables reference

Required for most environments:
- `SECRET_KEY`
- `DATABASE_URL` (defaults to `postgres://postgres:postgres@localhost:5432/soup_db` if not set)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (for social login)

Useful/optional:
- `DEBUG` — enables dev mode behavior
- `OPENAPI_GENERATOR_TOKEN` — header token for `/api/docs` when `DEBUG=False`
- `BE_HOSTNAME`, `FE_HOSTNAME` — customize allowed back- and front-end hostnames

Static files:
- `STATIC_ROOT` default is `./staticfiles`; run `python manage.py collectstatic` in production.

Sessions/CSRF:
- Cookies are secure by default when `DEBUG=False` (see `core/settings.py`). JWT is used for API auth; sessions are kept for Django admin compatibility.

JWT tuning (see `NINJA_JWT` in `core/settings.py`):
- Access token lifetime: 1 hour
- Refresh token lifetime: 7 days; rotation enabled
- User identifier claim uses `uid`

---

### Troubleshooting
- 403 accessing `/api/docs` in production:
  - Add header `X-Ninja-Token: <OPENAPI_GENERATOR_TOKEN>`, or login as a Django staff user, or enable `DEBUG=True` (not recommended in prod)
- Social login fails locally:
  - Ensure Google OAuth2 credentials and allowed redirect URIs match your frontend
  - Check that `code` and `redirect_uri` values are forwarded as the body to `/api/auth/login/google-oauth2/`
- Database connection errors:
  - Verify `DATABASE_URL` and that Postgres is reachable from your environment/container

---

### License

MIT (or update accordingly).
