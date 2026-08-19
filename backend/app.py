import sqlite3
import secrets
import string
import datetime
import os

from flask import Flask, request, jsonify, g, send_from_directory
from functools import wraps

# ============================================================

# CONFIG

# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(**file**))
DB_PATH = os.path.join(BASE_DIR, "licenses.db")

ADMIN_DIR = os.path.join(
os.path.dirname(BASE_DIR),
"admin"
)

ADMIN_PASSWORD = os.environ.get(
"OPTIFORGE_ADMIN_PASS",
"schimba-parola-asta"
)

# ============================================================

# LICENSE TIERS

# ============================================================

TIERS = {
"standard": {
"label": "Standard",
"optimizations": [
"temp_cleaner",
"network_boost"
]
},

```
"pro": {
    "label": "Pro",
    "optimizations": [
        "temp_cleaner",
        "network_boost",
        "startup_optimizer",
        "performance_mode"
    ]
},

"ultimate": {
    "label": "Ultimate",
    "optimizations": [
        "temp_cleaner",
        "network_boost",
        "startup_optimizer",
        "performance_mode",
        "game_mode",
        "background_apps",
        "input_optimization",
        "game_dvr",
        "xbox_game_bar",
        "fullscreen_optimization",
        "advanced_cleanup"
    ]
}
```

}

# ============================================================

# OPTIMIZATION CATALOG

# ============================================================

OPTIMIZATIONS_CATALOG = {
"temp_cleaner":
"Curatare fisiere temporare",

```
"network_boost":
    "Optimizare retea & DNS",

"startup_optimizer":
    "Optimizare pornire Windows",

"performance_mode":
    "Mod performanta",

"game_mode":
    "Optimizare Windows Game Mode",

"background_apps":
    "Reducere aplicatii Windows din fundal",

"input_optimization":
    "Optimizare input / responsiveness",

"game_dvr":
    "Dezactivare Game DVR / capturi",

"xbox_game_bar":
    "Optimizare Xbox Game Bar",

"fullscreen_optimization":
    "Optimizare fullscreen pentru jocuri",

"advanced_cleanup":
    "Curatare avansata cache"
```

}

app = Flask(**name**)

_valid_admin_tokens = set()

# ============================================================

# DATABASE

# ============================================================

def get_db():

```
if "db" not in g:

    g.db = sqlite3.connect(
        DB_PATH
    )

    g.db.row_factory = sqlite3.Row

return g.db
```

@app.teardown_appcontext
def close_db(exception=None):

```
db = g.pop("db", None)

if db is not None:
    db.close()
```

def init_db():

```
conn = sqlite3.connect(
    DB_PATH
)

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
```

# ============================================================

# ADMIN AUTH

# ============================================================

def require_admin(function):

```
@wraps(function)
def wrapper(*args, **kwargs):

    token = request.headers.get(
        "X-Admin-Token",
        ""
    )

    if token not in _valid_admin_tokens:

        return jsonify({
            "error": "Neautorizat"
        }), 401

    return function(
        *args,
        **kwargs
    )

return wrapper
```

@app.route(
"/api/admin/login",
methods=["POST"]
)
def admin_login():

```
data = request.get_json(
    force=True,
    silent=True
) or {}

password = data.get(
    "password",
    ""
)

if password != ADMIN_PASSWORD:

    return jsonify({
        "error": "Parola incorecta"
    }), 401

token = secrets.token_hex(24)

_valid_admin_tokens.add(
    token
)

return jsonify({
    "token": token
})
```

@app.route(
"/api/admin/logout",
methods=["POST"]
)
@require_admin
def admin_logout():

```
token = request.headers.get(
    "X-Admin-Token",
    ""
)

_valid_admin_tokens.discard(
    token
)

return jsonify({
    "ok": True
})
```

# ============================================================

# KEY GENERATION

# ============================================================

def generate_key_string():

```
alphabet = (
    string.ascii_uppercase
    + string.digits
)

alphabet = (
    alphabet
    .replace("O", "")
    .replace("0", "")
    .replace("I", "")
    .replace("1", "")
)

groups = []

for _ in range(4):

    group = "".join(
        secrets.choice(alphabet)
        for _ in range(4)
    )

    groups.append(group)

return "OF-" + "-".join(groups)
```

@app.route(
"/api/admin/keys/generate",
methods=["POST"]
)
@require_admin
def generate_keys():

```
data = request.get_json(
    force=True,
    silent=True
) or {}

tier = data.get(
    "tier",
    "standard"
)

try:

    quantity = int(
        data.get(
            "quantity",
            1
        )
    )

except Exception:

    quantity = 1

days_valid = data.get(
    "days_valid"
)

note = data.get(
    "note",
    ""
)

if tier not in TIERS:

    return jsonify({
        "error": "Nivel de licenta invalid"
    }), 400

quantity = max(
    1,
    min(quantity, 200)
)

expires_at = None

now = datetime.datetime.utcnow()

if days_valid:

    try:

        expires_at = (
            now
            + datetime.timedelta(
                days=int(days_valid)
            )
        ).isoformat()

    except Exception:

        return jsonify({
            "error":
                "days_valid invalid"
        }), 400

db = get_db()

created = []

for _ in range(quantity):

    while True:

        key = generate_key_string()

        try:

            db.execute(
                """
                INSERT INTO licenses
                (
                    license_key,
                    tier,
                    note,
                    created_at,
                    expires_at,
                    status
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'active'
                )
                """,
                (
                    key,
                    tier,
                    note,
                    now.isoformat(),
                    expires_at
                )
            )

            created.append(key)

            break

        except sqlite3.IntegrityError:

            continue

db.commit()

return jsonify({
    "created": created,
    "tier": tier,
    "tier_label":
        TIERS[tier]["label"],
    "expires_at": expires_at,
    "optimizations":
        TIERS[tier]["optimizations"]
})
```

# ============================================================

# LIST KEYS

# ============================================================

@app.route(
"/api/admin/keys",
methods=["GET"]
)
@require_admin
def list_keys():

```
db = get_db()

status_filter = request.args.get(
    "status"
)

tier_filter = request.args.get(
    "tier"
)

query = """
    SELECT *
    FROM licenses
    WHERE 1=1
"""

params = []

if status_filter:

    query += """
        AND status = ?
    """

    params.append(
        status_filter
    )

if tier_filter:

    query += """
        AND tier = ?
    """

    params.append(
        tier_filter
    )

query += """
    ORDER BY id DESC
"""

rows = db.execute(
    query,
    params
).fetchall()

return jsonify([
    dict(row)
    for row in rows
])
```

# ============================================================

# REVOKE KEY

# ============================================================

@app.route(
"/api/admin/keys/<license_key>/revoke",
methods=["POST"]
)
@require_admin
def revoke_key(license_key):

```
db = get_db()

db.execute(
    """
    UPDATE licenses
    SET status = 'revoked'
    WHERE license_key = ?
    """,
    (license_key,)
)

db.commit()

return jsonify({
    "ok": True
})
```

# ============================================================

# REACTIVATE KEY

# ============================================================

@app.route(
"/api/admin/keys/<license_key>/reactivate",
methods=["POST"]
)
@require_admin
def reactivate_key(license_key):

```
db = get_db()

db.execute(
    """
    UPDATE licenses
    SET status = 'active'
    WHERE license_key = ?
    """,
    (license_key,)
)

db.commit()

return jsonify({
    "ok": True
})
```

# ============================================================

# RESET DEVICE

# ============================================================

@app.route(
"/api/admin/keys/<license_key>/reset-device",
methods=["POST"]
)
@require_admin
def reset_device(license_key):

```
db = get_db()

db.execute(
    """
    UPDATE licenses
    SET
        hwid = NULL,
        activated_at = NULL
    WHERE license_key = ?
    """,
    (license_key,)
)

db.commit()

return jsonify({
    "ok": True
})
```

# ============================================================

# DELETE KEY

# ============================================================

@app.route(
"/api/admin/keys/<license_key>",
methods=["DELETE"]
)
@require_admin
def delete_key(license_key):

```
db = get_db()

db.execute(
    """
    DELETE FROM licenses
    WHERE license_key = ?
    """,
    (license_key,)
)

db.commit()

return jsonify({
    "ok": True
})
```

# ============================================================

# ADMIN STATS

# ============================================================

@app.route(
"/api/admin/stats",
methods=["GET"]
)
@require_admin
def stats():

```
db = get_db()

total = db.execute(
    "SELECT COUNT(*) c FROM licenses"
).fetchone()["c"]

active = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE status = 'active'
    """
).fetchone()["c"]

revoked = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE status = 'revoked'
    """
).fetchone()["c"]

activated = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE activated_at IS NOT NULL
    """
).fetchone()["c"]

standard = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE tier = 'standard'
    """
).fetchone()["c"]

pro = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE tier = 'pro'
    """
).fetchone()["c"]

ultimate = db.execute(
    """
    SELECT COUNT(*) c
    FROM licenses
    WHERE tier = 'ultimate'
    """
).fetchone()["c"]

return jsonify({
    "total": total,
    "active": active,
    "revoked": revoked,
    "activated": activated,
    "standard": standard,
    "pro": pro,
    "ultimate": ultimate
})
```

# ============================================================

# LICENSE VALIDATION

# ============================================================

@app.route(
"/api/license/validate",
methods=["POST"]
)
def validate_license():

```
data = request.get_json(
    force=True,
    silent=True
) or {}

license_key = (
    data.get("key") or ""
).strip().upper()

hwid = (
    data.get("hwid") or ""
).strip()

if not license_key:

    return jsonify({
        "valid": False,
        "reason": "Cheie lipsa"
    }), 400

if not hwid:

    return jsonify({
        "valid": False,
        "reason": "HWID lipsa"
    }), 400

db = get_db()

row = db.execute(
    """
    SELECT *
    FROM licenses
    WHERE license_key = ?
    """,
    (license_key,)
).fetchone()

if row is None:

    return jsonify({
        "valid": False,
        "reason": "Cheie inexistenta"
    }), 404

if row["status"] != "active":

    return jsonify({
        "valid": False,
        "reason": "Cheie revocata"
    }), 403

if row["expires_at"]:

    try:

        expires = (
            datetime.datetime
            .fromisoformat(
                row["expires_at"]
            )
        )

        if datetime.datetime.utcnow() > expires:

            return jsonify({
                "valid": False,
                "reason": "Cheie expirata"
            }), 403

    except Exception:

        return jsonify({
            "valid": False,
            "reason":
                "Data de expirare invalida"
        }), 500

# ========================================================
# DEVICE LOCK
# ========================================================

if row["hwid"] is None:

    db.execute(
        """
        UPDATE licenses
        SET
            hwid = ?,
            activated_at = ?
        WHERE license_key = ?
        """,
        (
            hwid,
            datetime.datetime.utcnow().isoformat(),
            license_key
        )
    )

    db.commit()

elif row["hwid"] != hwid:

    return jsonify({
        "valid": False,
        "reason":
            "Cheia este deja activa pe alt dispozitiv"
    }), 403

# ========================================================
# TIER
# ========================================================

tier = row["tier"]

tier_info = TIERS.get(
    tier
)

if tier_info is None:

    return jsonify({
        "valid": False,
        "reason":
            "Nivel de licenta invalid"
    }), 500

return jsonify({
    "valid": True,
    "tier": tier,
    "tier_label":
        tier_info["label"],
    "expires_at":
        row["expires_at"],
    "optimizations":
        tier_info["optimizations"]
})
```

# ============================================================

# PUBLIC TIER INFORMATION

# ============================================================

@app.route(
"/api/license/tiers",
methods=["GET"]
)
def license_tiers():

```
result = {}

for tier_name, tier in TIERS.items():

    result[tier_name] = {
        "label":
            tier["label"],

        "optimizations": [
            {
                "id": optimization,
                "name":
                    OPTIMIZATIONS_CATALOG.get(
                        optimization,
                        optimization
                    )
            }
            for optimization
            in tier["optimizations"]
        ]
    }

return jsonify(
    result
)
```

# ============================================================

# ADMIN PANEL

# ============================================================

@app.route("/")
@app.route("/admin")
def serve_admin():

```
return send_from_directory(
    ADMIN_DIR,
    "index.html"
)
```

# ============================================================

# HEALTH CHECK

# ============================================================

@app.route("/health")
def health():

```
return jsonify({
    "status": "ok"
})
```

# ============================================================

# START SERVER

# ============================================================

if **name** == "**main**":

```
init_db()

print(
    "[OptiForge] Database:",
    DB_PATH
)

print(
    "[OptiForge] Admin panel:",
    "http://localhost:5000/admin"
)

app.run(
    host="0.0.0.0",
    port=int(
        os.environ.get(
            "PORT",
            5000
        )
    ),
    debug=False
)
```

```
```
