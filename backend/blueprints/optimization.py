"""Optimizări: catalog, rulare (înregistrare istoric), istoric, restore."""
import datetime
from flask import Blueprint, request, jsonify, g
from db import get_db
from security import require_auth
from plans import get_catalog, get_optimizations_for_tier, tier_includes, OPTIMIZATIONS

bp = Blueprint("optimization", __name__, url_prefix="/api/optimization")


def _user_tier(db, user_id):
    row = db.execute(
        "SELECT tier FROM licenses WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row["tier"] if row else None


@bp.route("/catalog", methods=["GET"])
@require_auth
def catalog():
    db = get_db()
    tier = _user_tier(db, g.user_id)
    return jsonify({"tier": tier, "optimizations": get_catalog(tier)})


@bp.route("/available", methods=["GET"])
@require_auth
def available():
    """Lista modulelor disponibile pentru planul curent."""
    db = get_db()
    tier = _user_tier(db, g.user_id)
    if not tier:
        return jsonify({"tier": None, "optimizations": []})
    return jsonify({"tier": tier, "optimizations": get_optimizations_for_tier(tier)})


@bp.route("/run", methods=["POST"])
@require_auth
def run():
    """Înregistrează o optimizare rulată (clientul execută efectiv acțiunea local).
    Serverul verifică planul și stochează istoricul + before/after."""
    data = request.get_json(force=True, silent=True) or {}
    optimization_key = (data.get("optimization") or "").strip()
    before_state = data.get("before_state")
    after_state = data.get("after_state")

    if optimization_key not in OPTIMIZATIONS:
        return jsonify({"error": "Modul de optimizare invalid"}), 400

    db = get_db()
    tier = _user_tier(db, g.user_id)
    if not tier:
        return jsonify({"error": "Nu ai o licență activă"}), 403
    if not tier_includes(tier, optimization_key):
        return jsonify({"error": "Acest modul nu este inclus în planul tău"}), 403

    license_row = db.execute(
        "SELECT license_key FROM licenses WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
        (g.user_id,),
    ).fetchone()

    now = datetime.datetime.utcnow().isoformat()
    db.execute(
        """INSERT INTO optimization_history (user_id, license_key, optimization, tier, ran_at, before_state, after_state)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (g.user_id, license_row["license_key"] if license_row else None,
         optimization_key, tier, now,
         _json(before_state), _json(after_state)),
    )
    db.commit()
    return jsonify({"ok": True, "optimization": optimization_key, "tier": tier, "ran_at": now})


@bp.route("/history", methods=["GET"])
@require_auth
def history():
    db = get_db()
    limit = min(int(request.args.get("limit", 100)), 500)
    rows = db.execute(
        """SELECT id, optimization, tier, ran_at, before_state, after_state
           FROM optimization_history WHERE user_id = ?
           ORDER BY id DESC LIMIT ?""",
        (g.user_id, limit),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


def _json(val):
    import json
    if val is None:
        return None
    if isinstance(val, str):
        return val
    return json.dumps(val)
