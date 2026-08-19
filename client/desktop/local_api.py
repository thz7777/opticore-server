"""
OptiForge — Server local (desktop)
===================================
Servește UI-ul web premium + oferă un bridge local pentru:
  - /api/local/stats          → statistici sistem reale (psutil)
  - /api/local/run-optimization → execută optimizarea reală pe Windows

Toate celelalte /api/* sunt proxy-uite către serverul remote OptiForge
(auth, licențe, istoric) — astfel secretele rămân server-side.
"""
import os
import time
import threading
from flask import Flask, request, jsonify, send_from_directory, Response
import requests

# Directorul cu UI-ul web (dev: ../web  |  bundled: _MEIPASS/web)
BASE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE, "..", "web")
if not os.path.isdir(WEB_DIR):
    WEB_DIR = os.path.join(getattr(os.sys, "_MEIPASS", BASE), "web")

SERVER_URL = os.environ.get("OPTIFORGE_SERVER_URL", "https://opticore-server.onrender.com")

app = Flask(__name__)

# ---- stats cache ----
_last_net = None
_last_net_t = 0


def get_system_stats():
    global _last_net, _last_net_t
    import psutil
    cpu = psutil.cpu_percent(interval=0.4)
    ram = psutil.virtual_memory().percent
    disk_path = "C:\\" if os.name == "nt" else "/"
    try:
        disk = psutil.disk_usage(disk_path).percent
    except Exception:
        disk = 50
    # rețea (Mb/s aproximat)
    now = time.time()
    net = psutil.net_io_counters()
    net_speed = 12
    if _last_net is not None and now - _last_net_t > 0:
        delta = (net.bytes_sent + net.bytes_recv) - (_last_net.bytes_sent + _last_net.bytes_recv)
        net_speed = round((delta * 8 / 1e6) / max(now - _last_net_t, 0.1), 1)
    _last_net = net
    _last_net_t = now
    # GPU & temp: estimate (psutil nu oferă GPU cross-platform)
    gpu = max(5, min(80, cpu * 0.6 + 10))
    try:
        temps = psutil.sensors_temperatures()
        temp = 52
        if temps:
            for name, entries in temps.items():
                if entries:
                    temp = entries[0].current
                    break
    except Exception:
        temp = 52
    return {"cpu": round(cpu), "ram": round(ram), "gpu": round(gpu),
            "disk": round(disk), "net": round(net_speed), "temp": round(temp)}


@app.route("/api/local/stats", methods=["GET"])
def local_stats():
    return jsonify(get_system_stats())


@app.route("/api/local/run-optimization", methods=["POST"])
def local_run():
    from optimizations import run_optimization, OPTIMIZATIONS
    data = request.get_json(force=True, silent=True) or {}
    key = data.get("optimization", "")
    if key not in OPTIMIZATIONS:
        return jsonify({"error": "Modul invalid"}), 400
    logs = []

    def log(msg):
        logs.append(msg)

    ok = run_optimization(key, log)
    return jsonify({"ok": ok, "optimization": key, "logs": logs})


# ---- Proxy către serverul remote pentru toate celelalte /api/* ----
@app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_api(subpath):
    url = f"{SERVER_URL.rstrip('/')}/api/{subpath}"
    headers = {k: v for k, v in request.headers if k.lower() != "host"}
    body = request.get_data()
    try:
        resp = requests.request(
            method=request.method, url=url, headers=headers,
            params=request.args, data=body, timeout=15,
        )
        return Response(resp.content, status=resp.status_code,
                        headers={"Content-Type": resp.headers.get("Content-Type", "application/json")})
    except requests.RequestException as e:
        return jsonify({"error": f"Server indisponibil: {e}"}), 502


# ---- Servire UI web ----
@app.route("/")
def root():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/<path:filename>")
def serve_asset(filename):
    return send_from_directory(WEB_DIR, filename)
