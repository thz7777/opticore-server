"""
OptiForge — Desktop Client (pywebview)
=======================================
Pornește serverul local Flask într-un thread, apoi deschide fereastra
pywebview care încarcă UI-ul premium (același HTML/CSS/JS ca în web).

Build .exe (PE WINDOWS, cu Python 3.11+):
    cd client/desktop
    pip install -r requirements.txt
    pyinstaller OptiForge.spec
    # → dist/OptiForge.exe
"""
import os
import sys
import threading
import webview

from local_api import app

PORT = 5959


def start_server():
    # debug=False ca să nu apară reloader-ul în_PROD în fereastra desktop
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # așteaptă scurt ca serverul să pornească
    import time
    time.sleep(1.0)

    webview.create_window(
        "OptiForge — Premium System Optimizer",
        f"http://127.0.0.1:{PORT}/",
        width=1180, height=760, min_size=(960, 640),
    )
    webview.start()


if __name__ == "__main__":
    main()
