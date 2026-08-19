"""Securitate: hashing parole + token-uri de sesiune."""
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from config import SECRET_KEY, TOKEN_MAX_AGE

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="optiforge-auth")


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def generate_token(user_id):
    return _serializer.dumps({"uid": user_id})


def verify_token(token):
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=TOKEN_MAX_AGE)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None


def require_auth(f):
    """Decorator pentru endpoint-uri care necesită un utilizator autentificat."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip() if auth.startswith("Bearer ") else auth.strip()
        uid = verify_token(token)
        if not uid:
            return jsonify({"error": "Neautorizat"}), 401
        g.user_id = uid
        return f(*args, **kwargs)
    return wrapper
