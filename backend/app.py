"""
OptiForge License Server — aplicație principală
=================================================
Server Flask + SQLite cu:
  - Sistem de conturi (register/login, hashing parole, sesiuni)
  - Licențe pe 3 planuri (Standard / Pro / Ultimate) cu device binding
  - Istoric de optimizări
  - Panou admin (generare/gestionare chei, utilizatori, device-uri)
  - UI client premium (servit la /app)

Rulare:
    pip install -r requirements.txt
    python app.py
"""
import os
from flask import Flask, send_from_directory, redirect

from config import DB_PATH, ADMIN_DIR, CLIENT_WEB_DIR, SECRET_KEY
from db import init_db, close_db
from blueprints.auth import bp as auth_bp
from blueprints.license import bp as license_bp
from blueprints.optimization import bp as optimization_bp
from blueprints.admin import bp as admin_bp


def create_app():
    app = Flask(__name__)
    app.config["DB_PATH"] = DB_PATH
    app.config["SECRET_KEY"] = SECRET_KEY

    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(license_bp)
    app.register_blueprint(optimization_bp)
    app.register_blueprint(admin_bp)

    init_db(DB_PATH)

    # ---- Rute statice ----
    @app.route("/")
    def root():
        return redirect("/app")

    @app.route("/app")
    @app.route("/app/")
    def serve_client():
        return send_from_directory(CLIENT_WEB_DIR, "index.html")

    @app.route("/app/<path:filename>")
    def serve_client_assets(filename):
        return send_from_directory(CLIENT_WEB_DIR, filename)

    @app.route("/admin")
    def serve_admin():
        return send_from_directory(ADMIN_DIR, "index.html")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    init_db(DB_PATH)
    print(f"[OptiForge] DB: {DB_PATH}")
    print(f"[OptiForge] UI client:  http://localhost:5000/app")
    print(f"[OptiForge] Admin:      http://localhost:5000/admin")
    app.run(host="0.0.0.0", port=5000, debug=True)
