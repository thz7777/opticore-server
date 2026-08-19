"""Autentificare utilizatori: register, login, logout, profil."""
import datetime
from flask import Blueprint, request, jsonify, g
from db import get_db
from security import hash_password, verify_password, generate_token, verify_token, require_auth
from plans import get_optimizations_for_tier

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _get_user_license(db, user_id):
    """Returnează licența activă a utilizatorului (sau None)."""
    row = db.execute(
        """SELECT * FROM licenses
           WHERE user_id = ? AND status = 'active'
           ORDER BY id DESC LIMIT 1""",
        (user_id,),
    ).fetchone()
    return row


def _license_payload(row):
    if not row:
        return None
    now = datetime.datetime.utcnow()
    expired = False
    if row["expires_at"]:
        expired = datetime.datetime.fromisoformat(row["expires_at"]) < now
    return {
        "license_key": row["license_key"],
        "tier": row["tier"],
        "expires_at": row["expires_at"],
        "activated_at": row["activated_at"],
        "expired": expired,
        "optimizations": get_optimizations_for_tier(row["tier"]),
    }


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    hwid = (data.get("hwid") or "").strip()
    device_name = (data.get("device_name") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "Username, email și parolă sunt obligatorii"}), 400
    if len(password) < 6:
        return jsonify({"error": "Parola trebuie să aibă minim 6 caractere"}), 400

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        return jsonify({"error": "Username-ul este deja folosit"}), 409
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify({"error": "Email-ul este deja folosit"}), 409

    now = datetime.datetime.utcnow().isoformat()
    cur = db.execute(
        "INSERT INTO users (username, email, password_hash, created_at, last_login) VALUES (?, ?, ?, ?, ?)",
        (username, email, hash_password(password), now, now),
    )
    user_id = cur.lastrowid

    # Înregistrează device-ul
    if hwid:
        db.execute(
            "INSERT OR IGNORE INTO devices (user_id, hwid, device_name, registered_at, last_seen) VALUES (?, ?, ?, ?, ?)",
            (user_id, hwid, device_name or None, now, now),
        )
    db.commit()

    token = generate_token(user_id)
    return jsonify({
        "token": token,
        "user": {"id": user_id, "username": username, "email": email},
        "license": _license_payload(_get_user_license(db, user_id)),
    })


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password", "")
    hwid = (data.get("hwid") or "").strip()
    device_name = (data.get("device_name") or "").strip()

    if not identifier or not password:
        return jsonify({"error": "Username/email și parolă sunt obligatorii"}), 400

    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier.lower()),
    ).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return jsonify({"error": "Credențiale incorecte"}), 401

    now = datetime.datetime.utcnow().isoformat()
    db.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
    if hwid:
        db.execute(
            "INSERT OR IGNORE INTO devices (user_id, hwid, device_name, registered_at, last_seen) VALUES (?, ?, ?, ?, ?)",
            (row["id"], hwid, device_name or None, now, now),
        )
        db.execute("UPDATE devices SET last_seen = ? WHERE user_id = ? AND hwid = ?", (now, row["id"], hwid))
    db.commit()

    token = generate_token(row["id"])
    return jsonify({
        "token": token,
        "user": {"id": row["id"], "username": row["username"], "email": row["email"], "last_login": now},
        "license": _license_payload(_get_user_license(db, row["id"])),
    })


@bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    # Token-urile sunt stateless (semnate) — clientul doar le uită.
    return jsonify({"ok": True})


@bp.route("/me", methods=["GET"])
@require_auth
def me():
    db = get_db()
    row = db.execute("SELECT id, username, email, created_at, last_login FROM users WHERE id = ?", (g.user_id,)).fetchone()
    if not row:
        return jsonify({"error": "Utilizator inexistent"}), 404
    devices = db.execute(
        "SELECT hwid, device_name, registered_at, last_seen FROM devices WHERE user_id = ? ORDER BY registered_at DESC",
        (g.user_id,),
    ).fetchall()
    return jsonify({
        "user": dict(row),
        "license": _license_payload(_get_user_license(db, g.user_id)),
        "devices": [dict(d) for d in devices],
    })
