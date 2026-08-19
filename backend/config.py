"""Configurare OptiForge."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DB_PATH = os.environ.get("OPTIFORGE_DB_PATH", os.path.join(BACKEND_DIR, "licenses.db"))
ADMIN_DIR = os.path.join(BASE_DIR, "admin")
CLIENT_WEB_DIR = os.path.join(BASE_DIR, "client", "web")

# Parola admin (panoul web de administrare)
ADMIN_PASSWORD = os.environ.get("OPTIFORGE_ADMIN_PASS", "schimba-parola-asta")

# Secret pentru semnarea token-urilor de sesiune (client).
# În producție setează OPTIFORGE_SECRET_KEY cu o valoare stabilă & secretă.
SECRET_KEY = os.environ.get("OPTIFORGE_SECRET_KEY", "optiforge-dev-secret-change-me")

# Durata de viață a token-ului client (secunde) — 30 zile
TOKEN_MAX_AGE = 60 * 60 * 24 * 30
