# OptiForge — Base44 dev environment

## What this is
A license-server app with three parts:
- `backend/` — Flask + SQLite server (`app.py`) on port 5000. Serves the API (`/api/...`) AND the static admin panel.
- `admin/` — single `index.html` (static), served by the backend at `/` and `/admin`. All API calls are relative (same origin).
- `client/` — Python desktop launcher (compiled to `.exe` on Windows via PyInstaller). NOT part of the web preview.

## Running here
`docker compose -f docker-compose.base44.yml up -d` runs the Flask backend from source (python:3.12-slim, repo bind-mounted at `/app`, working dir `/app/backend`) on host port **3000** → container 5000. Flask runs in `--debug` mode so edits to `backend/app.py` and `admin/index.html` hot-reload.

The DB (`backend/licenses.db`) is initialized on startup via `init_db()` (CREATE TABLE IF NOT EXISTS — idempotent). It's committed in the repo and bind-mounted, so data persists across container restarts but is reset if the file is removed.

## No external secrets
No external services. The admin password defaults to `schimba-parola-asta` (set via `OPTIFORGE_ADMIN_PASS`); override it through the platform secrets if needed. `/run/base44/app.env` is wired as the last `env_file:` so a dashboard value wins over the default.

## Verify it works
- `curl -sf http://localhost:3000/health` → `{"status":"ok"}`
- `curl -sf http://localhost:3000/` → the admin HTML page
- External-host preview check: `curl -sf -H "Host: external-preview.example.com" http://localhost:3000/` returns the page (Flask accepts any host).

## Admin login
POST `/api/admin/login` with `{"password": "..."}` returns `{"token": "..."}`; use it as `X-Admin-Token` header for the admin endpoints.
