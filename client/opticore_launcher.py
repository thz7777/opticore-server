"""
OptiForge Launcher
===================
Aplicatie client (Tkinter) care cere o cheie de licenta, o valideaza fata de
serverul OptiForge, apoi deblocheaza panoul de optimizari in functie de
nivelul licentei (standard / pro).

Compilare in .exe (pe Windows, cu Python instalat):
    pip install -r requirements.txt
    pyinstaller --noconsole --onefile --name OptiForge opticore_launcher.py

Config:
    Modifica SERVER_URL mai jos cu adresa reala a serverului tau OptiForge.
"""

import json
import os
import platform
import subprocess
import threading
import uuid
import hashlib
import tkinter as tk
from tkinter import messagebox
import urllib.request
import urllib.error

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------

SERVER_URL = "https://opticore-server.onrender.com"
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "OptiForge")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

COLORS = {
    "bg": "#15130F",
    "panel": "#201D17",
    "panel2": "#26221A",
    "steel": "#39352A",
    "text": "#EDE6D6",
    "muted": "#8C8573",
    "forge": "#FF5A1F",
    "spark": "#4FC3F7",
    "danger": "#E5484D",
}

OPTIMIZATION_LABELS = {
    "temp_cleaner": ("Curatare fisiere temporare", "Sterge fisierele temporare din Windows si browsere pentru a elibera spatiu."),
    "network_boost": ("Optimizare retea & DNS", "Reseteaza stack-ul de retea si goleste cache-ul DNS pentru conexiuni mai stabile."),
    "startup_optimizer": ("Optimizare pornire Windows", "Analizeaza programele de la pornire si le poti dezactiva pe cele inutile."),
    "performance_mode": ("Mod performanta maxima", "Activeaza planul de alimentare 'Performanta ridicata' si reduce efectele vizuale."),
}


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------

def get_hwid():
    """Genereaza un identificator relativ stabil al masinii, fara date sensibile."""
    raw = f"{platform.node()}-{uuid.getnode()}-{platform.system()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def call_api(path, payload):
    url = SERVER_URL.rstrip("/") + path
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
        except Exception:
            data = {"reason": "Eroare server"}
        return data, e.code
    except Exception as e:
        return {"reason": f"Nu ma pot conecta la server ({e})"}, 0


def run_cmd(cmd, log_fn):
    """Ruleaza o comanda de sistem si trimite output-ul catre log_fn."""
    log_fn(f"$ {cmd}")
    if platform.system() != "Windows":
        log_fn("  (simulare - aceasta comanda ruleaza doar pe Windows)")
        return
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.stdout.strip():
            log_fn(result.stdout.strip())
        if result.returncode != 0 and result.stderr.strip():
            log_fn(f"  [!] {result.stderr.strip()}")
    except Exception as e:
        log_fn(f"  [!] Eroare: {e}")


# ----------------------------------------------------------------------------
# OPTIMIZARI
# ----------------------------------------------------------------------------

def opt_temp_cleaner(log_fn):
    log_fn("=== Curatare fisiere temporare ===")
    temp_dirs = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""),
                 os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp")]
    for d in set(t for t in temp_dirs if t):
        run_cmd(f'del /q /f /s "{d}\\*" 2>nul', log_fn)
        run_cmd(f'for /d %i in ("{d}\\*") do rd /s /q "%i" 2>nul', log_fn)

    # cache Windows Update descarcat (sigur de sters, se re-descarca la nevoie)
    run_cmd('net stop wuauserv', log_fn)
    run_cmd(f'del /q /f /s "{os.environ.get("WINDIR","C:\\Windows")}\\SoftwareDistribution\\Download\\*" 2>nul', log_fn)
    run_cmd('net start wuauserv', log_fn)

    # cosul de gunoi
    run_cmd('powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"', log_fn)

    # cache thumbnail-uri
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        run_cmd(f'del /q /f "{local_appdata}\\Microsoft\\Windows\\Explorer\\thumbcache_*.db" 2>nul', log_fn)
        # cache-uri browsere (Chrome / Edge)
        run_cmd(f'del /q /f /s "{local_appdata}\\Google\\Chrome\\User Data\\Default\\Cache\\*" 2>nul', log_fn)
        run_cmd(f'del /q /f /s "{local_appdata}\\Microsoft\\Edge\\User Data\\Default\\Cache\\*" 2>nul', log_fn)

    # rapoarte de erori Windows vechi
    run_cmd(f'del /q /f /s "%ProgramData%\\Microsoft\\Windows\\WER\\ReportQueue\\*" 2>nul', log_fn)

    run_cmd("ipconfig /flushdns", log_fn)
    log_fn("Curatare finalizata.\n")


def opt_network_boost(log_fn):
    log_fn("=== Optimizare retea & DNS ===")
    run_cmd("ipconfig /flushdns", log_fn)
    run_cmd("ipconfig /registerdns", log_fn)
    run_cmd("ipconfig /release", log_fn)
    run_cmd("ipconfig /renew", log_fn)
    run_cmd("netsh int tcp set global autotuninglevel=normal", log_fn)
    run_cmd("netsh int tcp set global rss=enabled", log_fn)
    run_cmd("netsh int tcp set global ecncapability=enabled", log_fn)
    run_cmd("netsh winsock reset", log_fn)
    run_cmd("netsh interface ip reset", log_fn)
    # elimina limitarea de latime de banda impusa de Windows pentru trafic non-critic
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" '
        '/v NetworkThrottlingIndex /t REG_DWORD /d ffffffff /f',
        log_fn,
    )
    run_cmd("arp -d *", log_fn)
    log_fn("Optimizare retea finalizata. Poate fi necesar un restart.\n")


def opt_startup_optimizer(log_fn):
    log_fn("=== Optimizare pornire Windows ===")
    # sarcini de telemetrie/diagnostic cunoscute ca fiind sigure de dezactivat
    safe_tasks_to_disable = [
        r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
        r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
        r"\Microsoft\Windows\Autochk\Proxy",
        r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
        r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
        r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
    ]
    for task in safe_tasks_to_disable:
        run_cmd(f'schtasks /Change /TN "{task}" /Disable', log_fn)

    # dezactiveaza intarzierea artificiala de pornire a aplicatiilor
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize" '
        '/v StartupDelayInMSec /t REG_DWORD /d 0 /f',
        log_fn,
    )

    log_fn("Sarcini de fundal neesentiale dezactivate.")
    log_fn("Se deschide Task Manager (tab Startup) pentru aplicatiile ramase, alege manual ce mai opresti...")
    run_cmd("start taskmgr /7", log_fn)
    log_fn("Optimizare pornire finalizata.\n")


def opt_performance_mode(log_fn):
    log_fn("=== Mod performanta maxima ===")
    high_perf_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    run_cmd(f"powercfg /setactive {high_perf_guid}", log_fn)
    run_cmd("powercfg /change monitor-timeout-ac 15", log_fn)
    run_cmd("powercfg /change standby-timeout-ac 0", log_fn)

    # efecte vizuale reduse la minim (ajustate pentru performanta)
    run_cmd(
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" '
        '/v VisualFXSetting /t REG_DWORD /d 2 /f',
        log_fn,
    )
    run_cmd(
        'reg add "HKCU\\Control Panel\\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f',
        log_fn,
    )
    run_cmd('reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f', log_fn)
    run_cmd('reg add "HKCU\\Control Panel\\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f', log_fn)

    # prioritate CPU pentru aplicatiile din prim-plan
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" '
        '/v Win32PrioritySeparation /t REG_DWORD /d 38 /f',
        log_fn,
    )
    # prioritate maxima pentru task-uri multimedia (jocuri/video)
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" '
        '/v "GPU Priority" /t REG_DWORD /d 8 /f',
        log_fn,
    )
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" '
        '/v "Priority" /t REG_DWORD /d 6 /f',
        log_fn,
    )

    # opreste aplicatiile din fundal care nu sunt in uz activ
    run_cmd(
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" '
        '/v GlobalUserDisabled /t REG_DWORD /d 1 /f',
        log_fn,
    )

    log_fn("Plan de alimentare + prioritati sistem setate pentru performanta maxima.\n")


OPTIMIZATION_FUNCS = {
    "temp_cleaner": opt_temp_cleaner,
    "network_boost": opt_network_boost,
    "startup_optimizer": opt_startup_optimizer,
    "performance_mode": opt_performance_mode,
}


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------

class OptiForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OptiForge")
        self.geometry("560x620")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)

        self.license_info = None
        self.hwid = get_hwid()

        cfg = load_config()
        if cfg.get("license_key"):
            self.try_login(cfg["license_key"], silent=True)
        else:
            self.build_login_screen()

    # ---------------- LOGIN ----------------

    def build_login_screen(self):
        self.clear()
        wrap = tk.Frame(self, bg=COLORS["bg"])
        wrap.pack(expand=True, fill="both", padx=40, pady=60)

        tk.Label(wrap, text="OPTIFORGE", font=("Segoe UI", 28, "bold"),
                 fg=COLORS["forge"], bg=COLORS["bg"]).pack(pady=(20, 4))
        tk.Label(wrap, text="Introdu cheia de licenta pentru a continua",
                 font=("Segoe UI", 11), fg=COLORS["muted"], bg=COLORS["bg"]).pack(pady=(0, 30))

        self.key_entry = tk.Entry(wrap, font=("Consolas", 14), justify="center",
                                   bg=COLORS["panel2"], fg=COLORS["text"], insertbackground=COLORS["text"],
                                   relief="flat")
        self.key_entry.insert(0, "OF-XXXX-XXXX-XXXX-XXXX")
        self.key_entry.pack(fill="x", ipady=10, pady=(0, 16))
        self.key_entry.bind("<FocusIn>", lambda e: self.key_entry.select_range(0, "end"))

        self.login_btn = tk.Button(wrap, text="ACTIVEAZA", font=("Segoe UI", 11, "bold"),
                                    bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                                    activebackground=COLORS["forge"],
                                    command=self.on_activate_click)
        self.login_btn.pack(fill="x", ipady=10)

        self.status_label = tk.Label(wrap, text="", font=("Consolas", 10),
                                      fg=COLORS["danger"], bg=COLORS["bg"], wraplength=460)
        self.status_label.pack(pady=16)

    def on_activate_click(self):
        key = self.key_entry.get().strip()
        if not key or key == "OF-XXXX-XXXX-XXXX-XXXX":
            self.status_label.config(text="Introdu o cheie valida.")
            return
        self.login_btn.config(state="disabled", text="SE VERIFICA...")
        threading.Thread(target=self.try_login, args=(key,), daemon=True).start()

    def try_login(self, key, silent=False):
        data, status = call_api("/api/license/validate", {"key": key, "hwid": self.hwid})
        if data.get("valid"):
            save_config({"license_key": key})
            self.license_info = data
            self.after(0, self.build_dashboard)
        else:
            reason = data.get("reason", "Nu ma pot conecta la server.")
            if silent:
                self.after(0, self.build_login_screen)
                self.after(0, lambda: self.status_label.config(text=reason))
            else:
                self.after(0, lambda: self.status_label.config(text=reason))
                self.after(0, lambda: self.login_btn.config(state="normal", text="ACTIVEAZA"))

    # ---------------- DASHBOARD ----------------

    def build_dashboard(self):
        self.clear()
        info = self.license_info

        header = tk.Frame(self, bg=COLORS["panel"])
        header.pack(fill="x")
        tk.Label(header, text="OPTIFORGE", font=("Segoe UI", 16, "bold"),
                 fg=COLORS["forge"], bg=COLORS["panel"]).pack(side="left", padx=20, pady=16)
        tier_txt = f"Licenta {info.get('tier_label', info.get('tier'))}"
        tk.Label(header, text=tier_txt, font=("Consolas", 10),
                 fg=COLORS["spark"], bg=COLORS["panel"]).pack(side="right", padx=20)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=16)

        enabled = info.get("optimizations", [])

        tk.Label(body, text="Incluse in planul tau:", font=("Segoe UI", 11, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 8))

        checklist = tk.Frame(body, bg=COLORS["panel"])
        checklist.pack(fill="x", pady=(0, 16))
        for key in enabled:
            label, desc = OPTIMIZATION_LABELS[key]
            row = tk.Frame(checklist, bg=COLORS["panel"])
            row.pack(fill="x", padx=14, pady=8)
            tk.Label(row, text="\u2713", font=("Segoe UI", 11, "bold"),
                     fg=COLORS["spark"], bg=COLORS["panel"]).pack(side="left", padx=(0, 10))
            col = tk.Frame(row, bg=COLORS["panel"])
            col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=label, font=("Segoe UI", 10, "bold"),
                     fg=COLORS["text"], bg=COLORS["panel"]).pack(anchor="w")
            tk.Label(col, text=desc, font=("Segoe UI", 8),
                     fg=COLORS["muted"], bg=COLORS["panel"], wraplength=420, justify="left").pack(anchor="w")

        self.start_btn = tk.Button(body, text="PORNESTE OPTIMIZAREA", font=("Segoe UI", 12, "bold"),
                                    bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                                    command=self.run_all_optimizations)
        self.start_btn.pack(fill="x", ipady=12, pady=(0, 16))

        tk.Label(body, text="Jurnal", font=("Segoe UI", 11, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 6))

        log_frame = tk.Frame(body, bg=COLORS["panel2"])
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, bg=COLORS["panel2"], fg=COLORS["muted"],
                                 font=("Consolas", 9), relief="flat", height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.config(state="disabled")

    def run_all_optimizations(self):
        enabled = self.license_info.get("optimizations", [])
        self.start_btn.config(state="disabled", text="OPTIMIZARE IN CURS...")
        threading.Thread(target=self._run_all_worker, args=(enabled,), daemon=True).start()

    def _run_all_worker(self, enabled):
        self.log(f"Pornesc optimizarea completa ({len(enabled)} module)...\n")
        for key in enabled:
            func = OPTIMIZATION_FUNCS[key]
            func(self.log)
        self.log("=== TOATE OPTIMIZARILE AU FOST APLICATE ===")
        self.after(0, lambda: self.start_btn.config(state="normal", text="RULEAZA DIN NOU"))

    def log(self, msg):
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.after(0, append)

    def clear(self):
        for w in self.winfo_children():
            w.destroy()


if __name__ == "__main__":
    app = OptiForgeApp()
    app.mainloop()
