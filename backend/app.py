"""
OptiForge License Server
=========================
Backend Flask + SQLite pentru generarea si validarea cheilor de licenta
pentru launcher-ul de optimizare OptiForge.

Rulare:
    pip install -r requirements.txt
    python app.py

Implicit porneste pe http://0.0.0.0:5000
Schimba ADMIN_PASSWORD inainte de a-l pune productie!
"""

import sqlite3
import secrets
import string
import hashlib
import datetime
import os
from flask import Flask, request, jsonify, g, send_from_directory
from functools import wraps

# ----------------------------------------------------------------------------
# CONFIGURARE
# ----------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "licenses.db")
ADMIN_DIR = os.path.join(os.path.dirname(BASE_DIR), "admin")

# SCHIMBA parola asta! Poate fi setata si din variabila de mediu OPTIFORGE_ADMIN_PASS
ADMIN_PASSWORD = os.environ.get("OPTIFORGE_ADMIN_PASS", "schimba-parola-asta")

# Niveluri de licenta -> ce optimizari deblocheaza fiecare
TIERS = {
    "standard": {
        "label": "Standard",
        "optimizations": ["temp_cleaner", "network_boost"],
    },
    "pro": {
        "label": "Pro",
        "optimizations": ["temp_cleaner", "network_boost", "startup_optimizer", "performance_mode"],
    },
}

OPTIMIZATIONS_CATALOG = {
    "temp_cleaner":      "Curatare fisiere temporare",
    "network_boost":     "Optimizare retea & DNS",
    "startup_optimizer": "Optimizare pornire Windows",
    "performance_mode":  "Mod performanta maxima",
}

app = Flask(__name__)

# token-uri admin valide, in memorie (se reseteaza la restart server)
_valid_admin_tokens = set()


# ----------------------------------------------------------------------------
# DB HELPERS
# ----------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            tier TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            activated_at TEXT,
            hwid TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------------
# AUTH ADMIN
# ----------------------------------------------------------------------------

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if token not in _valid_admin_tokens:
            return jsonify({"error": "Neautorizat"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True, silent=True) or {}
    password = data.get("password", "")
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Parola incorecta"}), 401
    token = secrets.token_hex(24)
    _valid_admin_tokens.add(token)
    return jsonify({"token": token})


@app.route("/api/admin/logout", methods=["POST"])
@require_admin
def admin_logout():
    token = request.headers.get("X-Admin-Token", "")
    _valid_admin_tokens.discard(token)
    return jsonify({"ok": True})


# ----------------------------------------------------------------------------
# GENERARE CHEI
# ----------------------------------------------------------------------------

def generate_key_string():
    alphabet = string.ascii_uppercase + string.digits
    # elimina caractere ambigue
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    groups = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "OF-" + "-".join(groups)


@app.route("/api/admin/keys/generate", methods=["POST"])
@require_admin
def generate_keys():
    data = request.get_json(force=True, silent=True) or {}
    tier = data.get("tier", "standard")
    quantity = int(data.get("quantity", 1))
    days_valid = data.get("days_valid")  # None = fara expirare
    note = data.get("note", "")

    if tier not in TIERS:
        return jsonify({"error": "Nivel de licenta invalid"}), 400
    quantity = max(1, min(quantity, 200))

    db = get_db()
    created = []
    now = datetime.datetime.utcnow()
    expires_at = None
    if days_valid:
        expires_at = (now + datetime.timedelta(days=int(days_valid))).isoformat()

    for _ in range(quantity):
        key = generate_key_string()
        db.execute(
            "INSERT INTO licenses (license_key, tier, note, created_at, expires_at, status) "
            "VALUES (?, ?, ?, ?, ?, 'active')",
            (key, tier, note, now.isoformat(), expires_at),
        )
        created.append(key)
    db.commit()
    return jsonify({"created": created, "tier": tier, "expires_at": expires_at})


@app.route("/api/admin/keys", methods=["GET"])
@require_admin
def list_keys():
    db = get_db()
    status_filter = request.args.get("status")
    tier_filter = request.args.get("tier")

    query = "SELECT * FROM licenses WHERE 1=1"
    params = []
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if tier_filter:
        query += " AND tier = ?"
        params.append(tier_filter)
    query += " ORDER BY id DESC"

    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/admin/keys/<license_key>/revoke", methods=["POST"])
@require_admin
def revoke_key(license_key):
    db = get_db()
    db.execute("UPDATE licenses SET status = 'revoked' WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/keys/<license_key>/reactivate", methods=["POST"])
@require_admin
def reactivate_key(license_key):
    db = get_db()
    db.execute("UPDATE licenses SET status = 'active' WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/keys/<license_key>/reset-device", methods=["POST"])
@require_admin
def reset_device(license_key):
    """Deblocheaza cheia de pe device-ul curent (util cand clientul isi schimba PC-ul)."""
    db = get_db()
    db.execute(
        "UPDATE licenses SET hwid = NULL, activated_at = NULL WHERE license_key = ?",
        (license_key,),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/keys/<license_key>", methods=["DELETE"])
@require_admin
def delete_key(license_key):
    db = get_db()
    db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) c FROM licenses").fetchone()["c"]
    active = db.execute("SELECT COUNT(*) c FROM licenses WHERE status='active'").fetchone()["c"]
    revoked = db.execute("SELECT COUNT(*) c FROM licenses WHERE status='revoked'").fetchone()["c"]
    activated = db.execute("SELECT COUNT(*) c FROM licenses WHERE activated_at IS NOT NULL").fetchone()["c"]
    return jsonify({"total": total, "active": active, "revoked": revoked, "activated": activated})


# ----------------------------------------------------------------------------
# VALIDARE LICENTA (folosit de launcher-ul client)
# ----------------------------------------------------------------------------

@app.route("/api/license/validate", methods=["POST"])
def validate_license():
    data = request.get_json(force=True, silent=True) or {}
    license_key = (data.get("key") or "").strip().upper()
    hwid = data.get("hwid", "")

    if not license_key:
        return jsonify({"valid": False, "reason": "Cheie lipsa"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()

    if row is None:
        return jsonify({"valid": False, "reason": "Cheie inexistenta"}), 404

    if row["status"] != "active":
        return jsonify({"valid": False, "reason": "Cheie revocata"}), 403

    if row["expires_at"]:
        expires = datetime.datetime.fromisoformat(row["expires_at"])
        if datetime.datetime.utcnow() > expires:
            return jsonify({"valid": False, "reason": "Cheie expirata"}), 403

    # blocare pe un singur device
    if row["hwid"] is None:
        db.execute(
            "UPDATE licenses SET hwid = ?, activated_at = ? WHERE license_key = ?",
            (hwid, datetime.datetime.utcnow().isoformat(), license_key),
        )
        db.commit()
    elif row["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "Cheia este deja activa pe alt dispozitiv"}), 403

    tier_info = TIERS.get(row["tier"], TIERS["standard"])
    return jsonify({
        "valid": True,
        "tier": row["tier"],
        "tier_label": tier_info["label"],
        "expires_at": row["expires_at"],
        "optimizations": tier_info["optimizations"],
    })


# ----------------------------------------------------------------------------
# SERVIRE PANOU ADMIN (fisier static)
# ----------------------------------------------------------------------------

@app.route("/")
@app.route("/admin")
def serve_admin():
    return send_from_directory(ADMIN_DIR, "index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ----------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print(f"[OptiForge] Baza de date: {DB_PATH}")
    print(f"[OptiForge] Panou admin:  http://localhost:5000/admin")
    print(f"[OptiForge] Parola admin implicita: {ADMIN_PASSWORD}  (SCHIMB-O!)")
    app.run(host="0.0.0.0", port=5000, debug=False)
