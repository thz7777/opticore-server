"""Panou administrare: admin auth, generare/gestionare chei, utilizatori, device-uri, stats."""
import secrets
import string
import datetime
from flask import Blueprint, request, jsonify
from db import get_db
from config import ADMIN_PASSWORD
from plans import TIERS

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# token-uri admin valide, în memorie
_valid_admin_tokens = set()


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token", "")
        if token not in _valid_admin_tokens:
            return jsonify({"error": "Neautorizat"}), 401
        return f(*args, **kwargs)
    return wrapper


@bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True, silent=True) or {}
    if data.get("password", "") != ADMIN_PASSWORD:
        return jsonify({"error": "Parolă incorectă"}), 401
    token = secrets.token_hex(24)
    _valid_admin_tokens.add(token)
    return jsonify({"token": token})


@bp.route("/logout", methods=["POST"])
@require_admin
def admin_logout():
    token = request.headers.get("X-Admin-Token", "")
    _valid_admin_tokens.discard(token)
    return jsonify({"ok": True})


def generate_key_string():
    alphabet = (string.ascii_uppercase + string.digits).replace("O", "").replace("0", "")
    alphabet = alphabet.replace("I", "").replace("1", "")
    groups = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "OF-" + "-".join(groups)


@bp.route("/keys/generate", methods=["POST"])
@require_admin
def generate_keys():
    data = request.get_json(force=True, silent=True) or {}
    tier = data.get("tier", "standard")
    quantity = max(1, min(int(data.get("quantity", 1)), 200))
    days_valid = data.get("days_valid")
    note = data.get("note", "")

    if tier not in TIERS:
        return jsonify({"error": "Nivel de licență invalid"}), 400

    db = get_db()
    created = []
    now = datetime.datetime.utcnow()
    expires_at = None
    if days_valid:
        expires_at = (now + datetime.timedelta(days=int(days_valid))).isoformat()

    for _ in range(quantity):
        key = generate_key_string()
        db.execute(
            "INSERT INTO licenses (license_key, tier, note, created_at, expires_at, status) VALUES (?, ?, ?, ?, ?, 'active')",
            (key, tier, note, now.isoformat(), expires_at),
        )
        created.append(key)
    db.commit()
    return jsonify({"created": created, "tier": tier, "expires_at": expires_at})


@bp.route("/keys", methods=["GET"])
@require_admin
def list_keys():
    db = get_db()
    query = "SELECT l.*, u.username AS owner FROM licenses l LEFT JOIN users u ON l.user_id = u.id WHERE 1=1"
    params = []
    if request.args.get("status"):
        query += " AND l.status = ?"
        params.append(request.args["status"])
    if request.args.get("tier"):
        query += " AND l.tier = ?"
        params.append(request.args["tier"])
    query += " ORDER BY l.id DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/keys/<license_key>/revoke", methods=["POST"])
@require_admin
def revoke_key(license_key):
    db = get_db()
    db.execute("UPDATE licenses SET status = 'revoked' WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/keys/<license_key>/reactivate", methods=["POST"])
@require_admin
def reactivate_key(license_key):
    db = get_db()
    db.execute("UPDATE licenses SET status = 'active' WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/keys/<license_key>/reset-device", methods=["POST"])
@require_admin
def reset_device(license_key):
    db = get_db()
    db.execute("UPDATE licenses SET hwid = NULL, activated_at = NULL WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/keys/<license_key>/rebind", methods=["POST"])
@require_admin
def rebind_key(license_key):
    """Eliberează complet licența (device + user) pentru reasignare."""
    db = get_db()
    db.execute("UPDATE licenses SET hwid = NULL, activated_at = NULL, user_id = NULL, device_name = NULL WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/keys/<license_key>", methods=["DELETE"])
@require_admin
def delete_key(license_key):
    db = get_db()
    db.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
    db.commit()
    return jsonify({"ok": True})


@bp.route("/stats", methods=["GET"])
@require_admin
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) c FROM licenses").fetchone()["c"]
    active = db.execute("SELECT COUNT(*) c FROM licenses WHERE status='active'").fetchone()["c"]
    revoked = db.execute("SELECT COUNT(*) c FROM licenses WHERE status='revoked'").fetchone()["c"]
    activated = db.execute("SELECT COUNT(*) c FROM licenses WHERE activated_at IS NOT NULL").fetchone()["c"]
    users = db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    by_tier = {r["tier"]: r["c"] for r in db.execute("SELECT tier, COUNT(*) c FROM licenses GROUP BY tier").fetchall()}
    return jsonify({
        "total": total, "active": active, "revoked": revoked,
        "activated": activated, "users": users, "by_tier": by_tier,
    })


@bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    db = get_db()
    rows = db.execute(
        """SELECT u.id, u.username, u.email, u.created_at, u.last_login,
                  (SELECT COUNT(*) FROM licenses l WHERE l.user_id = u.id AND l.status='active') AS active_licenses,
                  (SELECT GROUP_CONCAT(l.tier) FROM licenses l WHERE l.user_id = u.id AND l.status='active') AS tiers,
                  (SELECT COUNT(*) FROM devices d WHERE d.user_id = u.id) AS device_count
           FROM users u ORDER BY u.id DESC""",
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/users/<int:user_id>/devices", methods=["GET"])
@require_admin
def user_devices(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, hwid, device_name, registered_at, last_seen FROM devices WHERE user_id = ? ORDER BY registered_at DESC",
        (user_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])
