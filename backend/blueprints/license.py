"""Activare și validare licențe + device binding."""
import datetime
from flask import Blueprint, request, jsonify, g
from db import get_db
from security import require_auth
from plans import TIERS, get_optimizations_for_tier

bp = Blueprint("license", __name__, url_prefix="/api/license")


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
        "tier_label": TIERS.get(row["tier"], {}).get("label", row["tier"]),
        "expires_at": row["expires_at"],
        "activated_at": row["activated_at"],
        "expired": expired,
        "optimizations": get_optimizations_for_tier(row["tier"]),
    }


@bp.route("/activate", methods=["POST"])
@require_auth
def activate():
    """Leagă o cheie de licență de contul utilizatorului + device-ul curent."""
    data = request.get_json(force=True, silent=True) or {}
    license_key = (data.get("key") or data.get("license_key") or "").strip().upper()
    hwid = (data.get("hwid") or "").strip()
    device_name = (data.get("device_name") or "").strip()

    if not license_key:
        return jsonify({"error": "Cheie lipsă"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
    if not row:
        return jsonify({"error": "Cheie inexistentă"}), 404
    if row["status"] != "active":
        return jsonify({"error": "Cheie revocată"}), 403

    # Verifică expirarea
    if row["expires_at"]:
        if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(row["expires_at"]):
            return jsonify({"error": "Cheie expirată"}), 403

    # Dacă licența e deja legată de alt utilizator
    if row["user_id"] and row["user_id"] != g.user_id:
        return jsonify({"error": "Această licență aparține altui cont"}), 403

    # Device binding: dacă HWID-ul e setat și diferă, refuză
    if row["hwid"] and hwid and row["hwid"] != hwid:
        return jsonify({"error": "Licența este activă pe alt dispozitiv. Contactează suport pentru rebind."}), 403

    now = datetime.datetime.utcnow().isoformat()
    db.execute(
        "UPDATE licenses SET user_id = ?, hwid = ?, device_name = ?, activated_at = COALESCE(activated_at, ?) WHERE license_key = ?",
        (g.user_id, hwid or row["hwid"], device_name or row["device_name"], now, license_key),
    )
    # Înregistrează/actualizează device-ul
    if hwid:
        db.execute(
            "INSERT OR IGNORE INTO devices (user_id, hwid, device_name, registered_at, last_seen) VALUES (?, ?, ?, ?, ?)",
            (g.user_id, hwid, device_name or None, now, now),
        )
        db.execute("UPDATE devices SET last_seen = ? WHERE user_id = ? AND hwid = ?", (now, g.user_id, hwid))
    db.commit()

    row = db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
    return jsonify({"valid": True, "license": _license_payload(row)})


@bp.route("/validate", methods=["POST"])
def validate():
    """Validare simplă cheie+HWID (folosită de client la pornire, fără cont)."""
    data = request.get_json(force=True, silent=True) or {}
    license_key = (data.get("key") or "").strip().upper()
    hwid = (data.get("hwid") or "").strip()

    if not license_key:
        return jsonify({"valid": False, "reason": "Cheie lipsă"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
    if not row:
        return jsonify({"valid": False, "reason": "Cheie inexistentă"}), 404
    if row["status"] != "active":
        return jsonify({"valid": False, "reason": "Cheie revocată"}), 403
    if row["expires_at"] and datetime.datetime.utcnow() > datetime.datetime.fromisoformat(row["expires_at"]):
        return jsonify({"valid": False, "reason": "Cheie expirată"}), 403

    if row["hwid"] is None:
        now = datetime.datetime.utcnow().isoformat()
        db.execute("UPDATE licenses SET hwid = ?, activated_at = ? WHERE license_key = ?", (hwid, now, license_key))
        db.commit()
    elif row["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "Licența este activă pe alt dispozitiv"}), 403

    return jsonify({"valid": True, "license": _license_payload(row)})


@bp.route("/info", methods=["GET"])
@require_auth
def info():
    """Returnează licența curentă a utilizatorului autentificat."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM licenses WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
        (g.user_id,),
    ).fetchone()
    if not row:
        return jsonify({"license": None})
    return jsonify({"license": _license_payload(row)})


@bp.route("/devices", methods=["GET"])
@require_auth
def list_devices():
    db = get_db()
    devices = db.execute(
        "SELECT id, hwid, device_name, registered_at, last_seen FROM devices WHERE user_id = ? ORDER BY registered_at DESC",
        (g.user_id,),
    ).fetchall()
    return jsonify([dict(d) for d in devices])
