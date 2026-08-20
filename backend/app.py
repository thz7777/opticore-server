import sqlite3
import secrets
import string
import datetime
import os
import hashlib

from flask import Flask, request, jsonify, g, send_from_directory
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "licenses.db")
ADMIN_DIR = os.path.dirname(BASE_DIR)

ADMIN_PASSWORD = os.environ.get(
    "OPTIFORGE_ADMIN_PASS",
    "schimba-parola-asta"
)

# Generare token simplu (pentru sesiuni utilizatori)
def generate_token():
    return secrets.token_hex(32)

def hash_password(password):
    """Simple hashing for demo purposes. In prod use bcrypt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def check_password(password, stored_hash):
    parts = stored_hash.split(":")
    if len(parts) != 2:
        return False
    salt = parts[0]
    pwd_hash = parts[1]
    return hashlib.sha256((salt + password).encode()).hexdigest() == pwd_hash

TIERS = {
    "standard": {
        "label": "Standard",
        "optimizations": [
            "temp_cleaner",
            "network_boost"
        ]
    },
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
}

OPTIMIZATIONS_CATALOG = {
    "temp_cleaner": "Curatare fisiere temporare",
    "network_boost": "Optimizare retea si DNS",
    "startup_optimizer": "Optimizare pornire Windows",
    "performance_mode": "Mod performanta",
    "game_mode": "Windows Game Mode",
    "background_apps": "Reducere aplicatii Windows din fundal",
    "input_optimization": "Optimizare input si responsiveness",
    "game_dvr": "Game DVR si capturi",
    "xbox_game_bar": "Xbox Game Bar",
    "fullscreen_optimization": "Optimizare fullscreen",
    "advanced_cleanup": "Curatare avansata cache"
}

app = Flask(__name__)

_valid_admin_tokens = set()
# Stocarea token-urilor utilizatorilor: { token: user_id }
_valid_user_tokens = {}

app = Flask(__name__)

_valid_admin_tokens = set()
_valid_user_tokens = {}

# <-- INSEREAZĂ AICI BLOCUL LOGIN -->
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('email') == 'admin@test.com' and data.get('password') == 'parola_ta':
        token = str(uuid.uuid4())
        _valid_admin_tokens.add(token)
        return jsonify({'token': token, 'user': 'admin'})
    return jsonify({'error': 'Invalid credentials'}), 401
# -----------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

# ... restul funcțiilor tale (init_db, etc.) ...

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

    # --- NOUA TABLE: USERS ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            hwid TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            license_key TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (license_key) REFERENCES licenses (license_key)
        )
    """)
    
    conn.commit()
    conn.close()


def require_admin(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")

        if token not in _valid_admin_tokens:
            return jsonify({
                "error": "Neautorizat"
            }), 401

        return function(*args, **kwargs)

    return wrapper


def require_user(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not token or token not in _valid_user_tokens:
            return jsonify({"error": "Token invalid sau expirat"}), 401
            
        user_id = _valid_user_tokens[token]
        
        # Get user data to attach to g for convenience
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "Utilizator nu exista"}), 401
            
        g.user = dict(user)
        return function(*args, **kwargs)
    return wrapper


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(
        force=True,
        silent=True
    ) or {}

    password = data.get("password", "")

    if password != ADMIN_PASSWORD:
        return jsonify({
            "error": "Parola incorecta"
        }), 401

    token = secrets.token_hex(24)
    _valid_admin_tokens.add(token)

    return jsonify({
        "token": token
    })


@app.route("/api/admin/logout", methods=["POST"])
@require_admin
def admin_logout():
    token = request.headers.get("X-Admin-Token", "")
    _valid_admin_tokens.discard(token)

    return jsonify({
        "ok": True
    })


def generate_key_string():
    alphabet = string.ascii_uppercase + string.digits

    alphabet = (
        alphabet
        .replace("O", "")
        .replace("0", "")
        .replace("I", "")
        .replace("1", "")
    )

    groups = []

    for _ in range(4):
        groups.append(
            "".join(
                secrets.choice(alphabet)
                for _ in range(6)
            )
        )

    return "-".join(groups)


@app.route("/api/license/generate", methods=["POST"])
@require_admin
def generate_license():
    data = request.get_json() or {}
    tier = data.get("tier", "standard")
    note = data.get("note", "")
    
    if tier not in TIERS:
        return jsonify({"error": "Tier invalid"}), 400

    key = generate_key_string()
    now = datetime.datetime.now().isoformat()
    # Expirare 1 an (depinde de logica, aici e fix)
    expires = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()

    get_db().execute(
        "INSERT INTO licenses (license_key, tier, note, created_at, expires_at, status) VALUES (?, ?, ?, ?, ?, 'active')",
        (key, tier, note, now, expires)
    )
    get_db().commit()

    return jsonify({"license_key": key, "tier": tier, "note": note})


@app.route("/api/license/validate", methods=["POST"])
def validate_license():
    data = request.get_json() or {}
    key = data.get("license_key")
    
    if not key:
        return jsonify({"error": "Cheie lipsea"}), 400

    db = get_db()
    lic = db.execute("SELECT * FROM licenses WHERE license_key = ?", (key,)).fetchone()

    if not lic:
        return jsonify({"valid": False, "reason": "Cheie inexistenta"}), 404

    if lic['status'] != 'active':
        return jsonify({"valid": False, "reason": "Cheie inactivă"}), 403

    if lic['expires_at'] and lic['expires_at'] < datetime.datetime.now().isoformat():
        return jsonify({"valid": False, "reason": "Cheie expirată"}), 403

    return jsonify({
        "valid": True,
        "tier": lic['tier'],
        "optimizations": TIERS.get(lic['tier'], {}).get("optimizations", [])
    })


# --- UTILIZATOR (ACCOUNTS) SYSTEM ROUTES ---

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    if not email or not username or not password:
        return jsonify({"error": "Date incomplete"}), 400

    db = get_db()
    
    # Verificam daca exista deja
    if db.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username)).fetchone():
        return jsonify({"error": "Email sau username deja exista"}), 409

    now = datetime.datetime.now().isoformat()
    pwd_hash = hash_password(password)

    cursor = db.execute(
        "INSERT INTO users (email, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (email, username, pwd_hash, now)
    )
    db.commit()
    
    user_id = cursor.lastrowid

    # Generam un token pentru sesiune
    token = generate_token()
    _valid_user_tokens[token] = user_id

    return jsonify({
        "message": "Cont creat cu succes",
        "token": token,
        "user": {"id": user_id, "email": email, "username": username}
    }), 201

    db = get_db()
    # Cautam dupa email SAU username
    user = db.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?", 
        (identifier, identifier)
    ).fetchone()

    if not user:
        return jsonify({"error": "Utilizator nu a fost gasit"}), 404

    if not check_password(password, user['password_hash']):
        return jsonify({"error": "Parola incorecta"}), 401

    # Generare token
    token = generate_token()
    _valid_user_tokens[token] = user['id']

    return jsonify({
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "username": user['username']
        }
    })

@app.route("/api/auth/logout", methods=["POST"])
@require_user
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token in _valid_user_tokens:
        del _valid_user_tokens[token]
    return jsonify({"ok": True})

@app.route("/api/account/me", methods=["GET"])
@require_user
def get_account():
    user = g.user
    db = get_db()
    
    # Preluam licentele asociate
    user_licenses = db.execute(
        "SELECT l.*, ul.is_active FROM user_licenses ul JOIN licenses l ON l.license_key = ul.license_key WHERE ul.user_id = ?",
        (user['id'],)
    ).fetchall()
    
    # Formatare response
    licenses_info = []
    for lic in user_licenses:
        licenses_info.append({
            "key": lic['license_key'],
            "tier": lic['tier'],
            "status": lic['status'],
            "is_active": bool(lic['is_active']),
            "expires_at": lic['expires_at']
        })

    return jsonify({
        "user": {
            "id": user['id'],
            "email": user['email'],
            "username": user['username'],
            "created_at": user['created_at']
        },
        "licenses": licenses_info
    })

@app.route("/api/license/redeem", methods=["POST"])
@require_user
def redeem_license():
    data = request.get_json() or {}
    license_key = data.get("license_key")
    
    if not license_key:
        return jsonify({"error": "Cheie de licenta lipseste"}), 400
        
    db = get_db()
    lic = db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
    
    if not lic:
        return jsonify({"error": "Cheie invalida"}), 404
        
    if lic['status'] != 'active':
        return jsonify({"error": "Cheie deja utilizata sau inactiva"}), 400
        
    # Verificam daca e deja atasata cuiva (optional, dar recomandat)
    existing = db.execute("SELECT id FROM user_licenses WHERE license_key = ?", (license_key,)).fetchone()
    if existing:
        return jsonify({"error": "Aceasta cheie este deja asociata unui cont"}), 409

    user_id = g.user['id']
    
    db.execute(
        "INSERT INTO user_licenses (user_id, license_key) VALUES (?, ?)",
        (user_id, license_key)
    )
    
    # Marcam licenta ca "activata" sau "redeemed" in sensul ca nu mai e disponibila pentru altcineva (opional, aici pastram status active dar e atasata)
    # Putem adauga un flag sau doar lasam in user_licenses
    
    db.commit()
    
    return jsonify({
        "message": "Licenta atasata cu succes",
        "tier": lic['tier']
    })

@app.route("/api/license/activate-device", methods=["POST"])
@require_user
def activate_device():
    data = request.get_json() or {}
    hwid = data.get("hwid")
    license_key = data.get("license_key")
    
    if not hwid or not license_key:
        return jsonify({"error": "Hwid si Cheie necesare"}), 400
        
    db = get_db()
    user_id = g.user['id']
    
    # Verificam daca userul are licenta asta
    user_lic = db.execute(
        "SELECT * FROM user_licenses WHERE user_id = ? AND license_key = ?",
        (user_id, license_key)
    ).fetchone()
    
    if not user_lic:
        return jsonify({"error": "Nu detii aceasta licenta"}), 403
        
    # Actualizam HWID in tabela de licente (sau cream o tabela device, dar aici actualizam direct pt simplitate)
    db.execute("UPDATE licenses SET hwid = ?, activated_at = ? WHERE license_key = ?", 
               (hwid, datetime.datetime.now().isoformat(), license_key))
    db.commit()
    
    return jsonify({"ok": True, "message": "Dispozitiv activat"})

@app.route("/api/optimization/log", methods=["POST"])
def log_optimization():
    # Aceasta ruta e publica sau protejata? Presupunem ca e log general sau atasat userului prin token
    # Pentru a fi consistent cu "account", sa o facem opțional protejata sau nu. 
    # Clientul o cheama probabil dupa optimizare.
    
    data = request.get_json() or {}
    # Salvam log in DB sau doar return ok?
    # Salvam pt istoric
    db = get_db()
    db.execute("INSERT INTO logs (message, timestamp) VALUES (?, ?)", 
               (data.get("message", "Optimizare"), datetime.datetime.now().isoformat()))
    db.commit()
    
    return jsonify({"ok": True})

# Tabel logs pentru a nu da eroare la insert
# Adaugam un hook pentru a crea tabelul logs daca nu exista
def ensure_logs_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# Apelam la start
ensure_logs_table()

# ... (păstrează restul codului așa cum e) ...

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)

@app.route('/')
def root():
    return jsonify({"status": "ok", "message": "Server is running"})