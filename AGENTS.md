# OptiForge — Base44 dev environment

## What this is
A premium PC optimization product with license server. Three layers:
- `backend/` — Flask + SQLite, modular (blueprints). Serves the API (`/api/...`), the **client web UI** at `/app` (redirected from `/`), and the **admin panel** at `/admin`.
- `admin/` — admin console HTML (static), served by backend. Same-origin API calls.
- `client/web/` — premium client UI (HTML/CSS/JS) served at `/app`. Same files are used by the desktop client (pywebview) locally.
- `client/opticore_launcher.py` — legacy Tkinter desktop launcher (→ .exe via PyInstaller on Windows). NOT part of the web preview.

## Architecture
Backend is split into focused modules:
- `backend/app.py` — app factory (`create_app`), registers blueprints, calls `init_db`, serves static routes.
- `backend/config.py` — paths, admin password, secret key.
- `backend/db.py` — SQLite schema + migration (`init_db`). Creates `users`, `licenses`, `devices`, `optimization_history`; migrates old `licenses` table with `user_id`/`device_name`.
- `backend/security.py` — password hashing (werkzeug pbkdf2), stateless tokens (itsdangerous), `require_auth` decorator.
- `backend/plans.py` — 3 tiers (standard/pro/ultimate) + full optimization catalog (31 modules) with categories.
- `backend/blueprints/` — `auth` (register/login/me), `license` (activate/validate/info/devices), `optimization` (catalog/available/run/history), `admin` (keys CRUD, users, stats, devices).

## Running here
`docker compose -f docker-compose.base44.yml up -d` runs Flask from source (python:3.12-slim, repo bind-mounted at `/app`, working dir `/app/backend`) on host port **3000** → container 5000. Flask `--debug` hot-reloads edits to any backend file or static UI.

DB (`backend/licenses.db`) is initialized in `create_app()` (idempotent). Bind-mounted, persists across restarts.

## No external secrets
No external services. Admin password defaults to `schimba-parola-asta` (`OPTIFORGE_ADMIN_PASS`); token signing secret defaults to a dev value (`OPTIFORGE_SECRET_KEY`). `/run/base44/app.env` is wired as the last `env_file:` so dashboard values win.

## Verify it works
- `curl -sf http://localhost:3000/health` → `{"status":"ok"}`
- `curl -sf http://localhost:3000/app` → client UI HTML
- `curl -sf http://localhost:3000/admin` → admin HTML
- External-host check: `curl -sf -H "Host: external-preview.example.com" http://localhost:3000/app` returns the page.
- Full flow: register (`POST /api/auth/register`) → login → admin login (`/api/admin/login`) → generate key (`/api/admin/keys/generate` with tier) → activate (`/api/license/activate`) → catalog shows available modules.

## Preview flow
`/` redirects to `/app` — the premium client UI (login/register → dashboard with live CPU/RAM/GPU stats, optimization score, category modules, one-click optimize, history, license activation, account, settings). `/admin` is the management console (key generation for 3 tiers, user list, stats).
