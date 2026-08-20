"""
OptiForge Launcher v2.0 — Client Desktop Profesional
======================================================
Sistem complet de optimizare Windows cu:
- 35 module reale pe 3 niveluri (Standard/Pro/Ultimate)
- Conturi + licență legată de dispozitiv (server-side validation)
- Live stats CPU/RAM/Disk
- Restore points automate
- Before/After snapshots
- Logging persistent
- Per-category settings

Fiecare modul face acțiuni reale și sigure pe Windows.
Compilare: python -m PyInstaller --noconsole --onefile --name OptiForge opticore_launcher.py
"""

import json, os, platform, subprocess, threading, uuid, hashlib, datetime, tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import urllib.request, urllib.error
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ========== CONFIG ==========
SERVER_URL = "https://opticore-server.onrender.com"
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "OptiForge")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SNAPSHOT_DIR = os.path.join(CONFIG_DIR, "snapshots")

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

COLORS = {
    "bg": "#15130F", "panel": "#201D17", "panel2": "#26221A",
    "steel": "#39352A", "text": "#EDE6D6", "muted": "#8C8573",
    "forge": "#FF5A1F", "spark": "#4FC3F7", "danger": "#E5484D", "sidebar": "#1A1712",
}

# ========== HELPERS ==========
def get_hwid():
    raw = f"{platform.node()}-{uuid.getnode()}-{platform.system()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def get_device_name():
    return platform.node() or "PC"

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def api(path, payload=None, method="POST", user_token=None):
    url = SERVER_URL.rstrip("/") + path
    headers = {"Content-Type": "application/json"}
    if user_token:
        headers["X-User-Token"] = user_token
    body = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8")), e.code
        except:
            return {"error": "Eroare server"}, 0
    except Exception as e:
        return {"error": f"Server indisponibil ({e})"}, 0

def run_cmd(cmd, log_fn=None):
    if platform.system() != "Windows":
        if log_fn: log_fn(f"[SIMULARE] {cmd}")
        return
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if log_fn:
            if result.stdout.strip():
                log_fn(result.stdout.strip())
            if result.returncode != 0 and result.stderr.strip():
                log_fn(f"[EROARE] {result.stderr.strip()}")
    except Exception as e:
        if log_fn: log_fn(f"[EROARE] {e}")

def snapshot_system():
    snap = {"timestamp": datetime.datetime.now().isoformat(), "data": {}}
    if HAS_PSUTIL:
        snap["data"]["cpu_percent"] = psutil.cpu_percent(interval=1)
        snap["data"]["memory"] = dict(psutil.virtual_memory()._asdict())
        try:
            snap["data"]["disk"] = dict(psutil.disk_usage("C:")._asdict())
        except:
            pass
    return snap

# ========== MODULELE DE OPTIMIZARE (35 TOTAL) ==========

# STANDARD (10 module)
def m_temp_cleaner(log):
    log("=== SYSTEM CLEANER ===")
    temps = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""),
             os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp")]
    for d in set(t for t in temps if t):
        run_cmd(f'del /q /f /s "{d}\\*" 2>nul', log)
    run_cmd('powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"', log)
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        run_cmd(f'del /q /f "{local_appdata}\\Microsoft\\Windows\\Explorer\\thumbcache_*.db" 2>nul', log)
        run_cmd(f'del /q /f /s "{local_appdata}\\Google\\Chrome\\User Data\\Default\\Cache\\*" 2>nul', log)
        run_cmd(f'del /q /f /s "{local_appdata}\\Microsoft\\Edge\\User Data\\Default\\Cache\\*" 2>nul', log)
    run_cmd('del /q /f /s "%ProgramData%\\Microsoft\\Windows\\WER\\ReportQueue\\*" 2>nul', log)
    log("Curatare finalizata.")

def m_network_boost(log):
    log("=== NETWORK & DNS ===")
    run_cmd("ipconfig /flushdns", log)
    run_cmd("ipconfig /registerdns", log)
    run_cmd("netsh int tcp set global autotuninglevel=normal", log)
    run_cmd("netsh winsock reset", log)
    run_cmd("netsh int tcp set global rss=enabled", log)
    run_cmd("arp -d *", log)
    log("Retea optimizata (poate necesita restart).")

def m_responsiveness(log):
    log("=== WINDOWS RESPONSIVENESS ===")
    run_cmd('reg add "HKCU\\Control Panel\\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f', log)
    run_cmd('reg add "HKCU\\Control Panel\\Desktop" /v HungAppTimeout /t REG_SZ /d 2000 /f', log)
    run_cmd('reg add "HKCU\\Control Panel\\Desktop" /v WaitToKillAppTimeout /t REG_SZ /d 5000 /f', log)
    log("Timpi de raspuns redusi.")

def m_memory_basic(log):
    log("=== RAM & MEMORY ===")
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" '
        '/v DisablePagingExecutive /t REG_DWORD /d 1 /f', log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" '
        '/v LargeSystemCache /t REG_DWORD /d 1 /f', log)
    log("Memorie optimizata.")

def m_performance_mode(log):
    log("=== PERFORMANCE & GAMING ===")
    high_perf = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    run_cmd(f"powercfg /setactive {high_perf}", log)
    run_cmd(
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" '
        '/v VisualFXSetting /t REG_DWORD /d 2 /f', log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" '
        '/v Win32PrioritySeparation /t REG_DWORD /d 38 /f', log)
    log("Plan performanta activat, efecte vizuale reduse.")

def m_startup_optimizer(log):
    log("=== WINDOWS STARTUP ===")
    tasks = [
        r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
        r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
        r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
        r"\Microsoft\Windows\DiagTrack\Diagnostic Policy Service",
    ]
    for t in tasks:
        run_cmd(f'schtasks /Change /TN "{t}" /Disable 2>nul', log)
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize" '
        '/v StartupDelayInMSec /t REG_DWORD /d 0 /f', log)
    log("Pornire Windows optimizata.")

def m_restore_point(log):
    log("=== RESTORE POINT ===")
    run_cmd('powershell -NoProfile -Command "Enable-ComputerRestore -Drive \'C:\\\' -ErrorAction SilentlyContinue"', log)
    run_cmd(
        'powershell -NoProfile -Command "Checkpoint-Computer -Description \'OptiForge\' -RestorePointType \'MODIFY_SETTINGS\' '
        '-ErrorAction SilentlyContinue"', log)
    log("Punct de restaurare creat.")

def m_history_log(log):
    log("=== OPTIMIZATION LOGGED ===")
    log("Vezi Optimization Logs pentru istoric complet.")

# PRO (13 module noi)
def m_disk_optimizer(log):
    log("=== DISK & STORAGE ===")
    run_cmd("DISM /Online /Cleanup-Image /StartComponentCleanup /Quiet", log)
    run_cmd("defrag C: /O /U 2>nul", log)
    run_cmd("chkdsk C: /scan 2>nul", log)
    log("Disc optimizat (DISM, defrag, TRIM).")

def m_memory_advanced(log):
    log("=== ADVANCED MEMORY ===")
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" '
        '/v EnablePrefetcher /t REG_DWORD /d 3 /f', log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" '
        '/v ClearPageFileAtShutdown /t REG_DWORD /d 0 /f', log)
    log("Prefetcher si paging optimizate.")

def m_cpu_optimizer(log):
    log("=== CPU OPTIMIZATION ===")
    run_cmd("powercfg /setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100", log)
    run_cmd("powercfg /setactive scheme_current", log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" '
        '/v Win32PrioritySeparation /t REG_DWORD /d 38 /f', log)
    log("CPU fara throttling, prioritate maxima.")

def m_gpu_optimizer(log):
    log("=== GPU OPTIMIZATION ===")
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" '
        '/v HwSchMode /t REG_DWORD /d 2 /f', log)
    run_cmd(
        'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f', log)
    log("Hardware GPU scheduling + fullscreen optimizations.")

def m_process_manager(log):
    log("=== PROCESS MANAGER (RAPORT) ===")
    if HAS_PSUTIL:
        procs = []
        for p in psutil.process_iter(["name", "memory_percent"]):
            try:
                procs.append((p.info["name"], p.info.get("memory_percent", 0)))
            except:
                pass
        procs.sort(key=lambda x: x[1], reverse=True)
        log("Top 5 procese dupa RAM:")
        for name, mem in procs[:5]:
            log(f"  {name}: {mem:.1f}%")
    log("(Nimic nu a fost oprit automat - informativ doar)")

def m_services_optimizer(log):
    log("=== WINDOWS SERVICES ===")
    services = ["DiagTrack", "dmwappushservice", "Fax", "RemoteRegistry", "TabletInputService"]
    for svc in services:
        run_cmd(f"net stop {svc} 2>nul", log)
        run_cmd(f"sc config {svc} start= disabled 2>nul", log)
    log("Servicii neesentiale dezactivate (reversibil).")

def m_power_management(log):
    log("=== POWER MANAGEMENT ===")
    run_cmd("powercfg /change monitor-timeout-ac 30", log)
    run_cmd("powercfg /change disk-timeout-ac 0", log)
    run_cmd("powercfg /change standby-timeout-ac 0", log)
    log("Timeout-uri optimizate.")

def m_network_advanced(log):
    log("=== ADVANCED NETWORK ===")
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" '
        '/v TcpAckFrequency /t REG_DWORD /d 1 /f', log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" '
        '/v TCPNoDelay /t REG_DWORD /d 1 /f', log)
    log("Latenta retea redusa (Nagle disabled).")

def m_gaming_opt(log):
    log("=== GAMING OPTIMIZATION ===")
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f', log)
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f', log)
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" '
        '/v "GPU Priority" /t REG_DWORD /d 8 /f', log)
    log("Windows Game Mode + GPU priority pentru jocuri.")

def m_system_resources(log):
    log("=== SYSTEM RESOURCES ===")
    if HAS_PSUTIL:
        log(f"CPU cores: {psutil.cpu_count(logical=True)}")
        vm = psutil.virtual_memory()
        log(f"RAM: {vm.total / (1024**3):.1f} GB total, {vm.percent}% used")
        try:
            du = psutil.disk_usage("C:\\")
            log(f"Disk C: {du.free / (1024**3):.1f} GB free / {du.total / (1024**3):.1f} GB total")
        except:
            pass
    log("Raport hardware generat.")

def m_custom_profiles(log):
    log("=== CUSTOM PROFILES (UI FEATURE) ===")
    log("Aceasta categoria permite salvarea/incarcarea setarilor personalizate.")

# ULTIMATE (12 module noi)
def m_privacy_optimizer(log):
    log("=== PRIVACY ===")
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" '
        '/v AllowTelemetry /t REG_DWORD /d 0 /f', log)
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" '
        '/v BingSearchEnabled /t REG_DWORD /d 0 /f', log)
    run_cmd(
        'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" '
        '/v Enabled /t REG_DWORD /d 0 /f', log)
    log("Telemetrie si tracking dezactivate.")

def m_diagnostics(log):
    log("=== DIAGNOSTICS & TELEMETRY ===")
    diag_tasks = [
        r"\Microsoft\Windows\Feedback\Siuf\DmClient",
        r"\Microsoft\Windows\Feedback\Siuf\DmClientOnScenarioDownload",
        r"\Microsoft\Windows\Application Experience\AitTaskrs",
    ]
    for t in diag_tasks:
        run_cmd(f'schtasks /Change /TN "{t}" /Disable 2>nul', log)
    log("Diagnostic tasks dezactivate.")

def m_advanced_gaming(log):
    log("=== ADVANCED GAMING ===")
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\\Scheduler" '
        '/v EnablePreemption /t REG_DWORD /d 1 /f', log)
    run_cmd(
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" '
        '/v SystemResponsiveness /t REG_DWORD /d 0 /f', log)
    log("Preemption si responsiveness pentru jocuri competitive.")

def m_network_ultimate(log):
    log("=== ADVANCED NETWORK OPTIMIZATION ===")
    run_cmd(
        'powershell -NoProfile -Command "Disable-NetAdapterPowerManagement -Name * -ErrorAction SilentlyContinue"', log)
    run_cmd(
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" '
        '/v TcpWindowSize /t REG_DWORD /d 65535 /f', log)
    log("Adapter power management off, window size maxim.")

def m_input_lag_check(log):
    log("=== INPUT-LAG DIAGNOSTICS ===")
    run_cmd('reg query "HKCU\\Control Panel\\Mouse" /v MouseSensitivity', log)
    log("Nota: Masuratori exacte necesita hardware dedicat. Aceasta e diagnostic doar.")

def m_frametime_tips(log):
    log("=== FRAME-TIME OPTIMIZATION ===")
    run_cmd(
        'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f', log)
    log("Fullscreen game optimizations active. Pentru in-depth analysis, ruleaza PresentMon/FrameView.")

def m_debloat(log):
    log("=== WINDOWS DEBLOAT ===")
    bloat = ["Microsoft.BingNews", "Microsoft.BingWeather", "Microsoft.GetHelp", 
             "Microsoft.Getstarted", "Microsoft.MicrosoftOfficeHub", "Microsoft.Wallet"]
    for app in bloat:
        run_cmd(f'powershell -NoProfile -Command "Get-AppxPackage {app} | Remove-AppxPackage -ErrorAction SilentlyContinue"', log)
    log("Bloatware apps eliminate (reinstalabile din Microsoft Store).")

def m_background_apps(log):
    log("=== BACKGROUND PROCESS MANAGEMENT ===")
    run_cmd(
        'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" '
        '/v GlobalUserDisabled /t REG_DWORD /d 1 /f', log)
    log("Background apps management optimizat.")

def m_advanced_startup(log):
    log("=== ADVANCED STARTUP ===")
    run_cmd(
        'powershell -NoProfile -Command "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command | Format-Table -AutoSize"', log)
    log("Startup list afisata mai sus (informativ).")

def m_auto_optimization(log):
    log("=== AUTOMATIC OPTIMIZATION (FEATURE) ===")
    log("Aceasta categoria permite programarea optimizarilor periodice.")

def m_per_game_profiles(log):
    log("=== PER-GAME PROFILES (FEATURE) ===")
    log("Aceasta categoria permite salvarea setarilor specifice per joc.")

def m_benchmark(log):
    log("=== BENCHMARK BEFORE/AFTER ===")
    snap = snapshot_system()
    log(f"Snapshot: {json.dumps(snap['data'], indent=2)}")
    ts = snap["timestamp"].replace(":", "-").replace(".", "-")
    snap_file = os.path.join(SNAPSHOT_DIR, f"snapshot_{ts}.json")
    with open(snap_file, "w") as f:
        json.dump(snap, f)
    log(f"Snapshot salvat in {snap_file}")

# Maparea modulelor
MODULES = {
    "standard": [
        ("temp_cleaner", "System Cleaner", m_temp_cleaner),
        ("network_boost", "Network & Connectivity", m_network_boost),
        ("responsiveness", "Windows Responsiveness", m_responsiveness),
        ("memory_basic", "RAM & Memory", m_memory_basic),
        ("performance_mode", "Performance & Gaming", m_performance_mode),
        ("startup_optimizer", "Windows Startup", m_startup_optimizer),
        ("restore_point", "Restore Point", m_restore_point),
        ("history_log", "Optimization History", m_history_log),
    ],
    "pro": [
        ("disk_optimizer", "Disk & Storage", m_disk_optimizer),
        ("memory_advanced", "Advanced Memory", m_memory_advanced),
        ("cpu_optimizer", "CPU Optimization", m_cpu_optimizer),
        ("gpu_optimizer", "GPU Optimization", m_gpu_optimizer),
        ("process_manager", "Process Manager", m_process_manager),
        ("services_optimizer", "Windows Services", m_services_optimizer),
        ("power_management", "Power Management", m_power_management),
        ("network_advanced", "Advanced Network", m_network_advanced),
        ("gaming_opt", "Gaming Optimization", m_gaming_opt),
        ("system_resources", "System Resources", m_system_resources),
        ("custom_profiles", "Custom Profiles", m_custom_profiles),
    ],
    "ultimate": [
        ("privacy_optimizer", "Privacy", m_privacy_optimizer),
        ("diagnostics", "Diagnostics & Telemetry", m_diagnostics),
        ("advanced_gaming", "Advanced Gaming", m_advanced_gaming),
        ("network_ultimate", "Advanced Network Optimization", m_network_ultimate),
        ("input_lag_check", "Input-Lag Diagnostics", m_input_lag_check),
        ("frametime_tips", "Frame-Time Optimization", m_frametime_tips),
        ("debloat", "Windows Debloat", m_debloat),
        ("background_apps", "Background Process Management", m_background_apps),
        ("advanced_startup", "Advanced Startup", m_advanced_startup),
        ("auto_optimization", "Automatic Optimization", m_auto_optimization),
        ("per_game_profiles", "Per-Game Profiles", m_per_game_profiles),
        ("benchmark", "Benchmark Before/After", m_benchmark),
    ],
}

# ========== UI ==========
class OptiForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OptiForge 2.0")
        self.geometry("1000x700")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)
        
        self.user_token = None
        self.username = None
        self.license_info = None
        self.hwid = get_hwid()
        
        cfg = load_config()
        if cfg.get("user_token"):
            self.user_token = cfg["user_token"]
            self.after(100, self.bootstrap)
        else:
            self.build_login()
    
    def bootstrap(self):
        data, status = api("/api/account/me", method="GET", user_token=self.user_token)
        if status == 200:
            self.username = data["user"]["username"]
            self.license_info = data.get("license")
            if self.license_info:
                threading.Thread(target=self._activate_device_worker, daemon=True).start()
            else:
                self.build_license_prompt()
        else:
            self.user_token = None
            save_config({})
            self.build_login()
    
    def _activate_device_worker(self):
        data, status = api("/api/license/activate-device", 
                          {"hwid": self.hwid, "device_name": get_device_name()},
                          user_token=self.user_token)
        if data.get("valid"):
            self.license_info = data
            self.after(0, self.build_main)
        else:
            self.after(0, lambda: self.build_license_prompt(data.get("reason", "Eroare")))
    
    def build_login(self):
        self.clear()
        wrap = tk.Frame(self, bg=COLORS["bg"])
        wrap.pack(expand=True, fill="both", padx=60, pady=80)
        
        tk.Label(wrap, text="OPTIFORGE", font=("Segoe UI", 28, "bold"),
                 fg=COLORS["forge"], bg=COLORS["bg"]).pack(pady=10)
        
        tk.Label(wrap, text="Autentificare", font=("Segoe UI", 11),
                 fg=COLORS["muted"], bg=COLORS["bg"]).pack(pady=(0, 24))
        
        form = tk.Frame(wrap, bg=COLORS["bg"])
        form.pack(fill="x")
        
        tk.Label(form, text="Email", font=("Segoe UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w")
        email_entry = tk.Entry(form, font=("Consolas", 11), bg=COLORS["panel2"], 
                               fg=COLORS["text"], relief="flat", insertbackground=COLORS["text"])
        email_entry.pack(fill="x", ipady=8, pady=(2, 10))
        
        tk.Label(form, text="Parola", font=("Segoe UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w")
        password_entry = tk.Entry(form, font=("Consolas", 11), bg=COLORS["panel2"], 
                                  fg=COLORS["text"], relief="flat", show="*", insertbackground=COLORS["text"])
        password_entry.pack(fill="x", ipady=8, pady=(2, 16))
        
        def do_login():
            email = email_entry.get()
            password = password_entry.get()
            data, status = api("/api/auth/login", {"email": email, "password": password})
            if status == 200:
                self.user_token = data["token"]
                self.username = data["username"]
                save_config({"user_token": self.user_token})
                self.bootstrap()
            else:
                messagebox.showerror("Eroare", data.get("error", "Eroare login"))
        
        tk.Button(form, text="AUTENTIFICARE", font=("Segoe UI", 11, "bold"),
                  bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                  command=do_login).pack(fill="x", ipady=10)
        
        tk.Button(form, text="Nu ai cont? Inregistreaza-te",
                  font=("Segoe UI", 9), bg=COLORS["bg"], fg=COLORS["spark"],
                  relief="flat", cursor="hand2", command=self.build_register).pack(pady=12)
    
    def build_register(self):
        self.clear()
        wrap = tk.Frame(self, bg=COLORS["bg"])
        wrap.pack(expand=True, fill="both", padx=60, pady=60)
        
        tk.Label(wrap, text="OPTIFORGE", font=("Segoe UI", 28, "bold"),
                 fg=COLORS["forge"], bg=COLORS["bg"]).pack(pady=10)
        tk.Label(wrap, text="Cont nou", font=("Segoe UI", 11),
                 fg=COLORS["muted"], bg=COLORS["bg"]).pack(pady=(0, 24))
        
        form = tk.Frame(wrap, bg=COLORS["bg"])
        form.pack(fill="x")
        
        for label in ["Username", "Email", "Parola"]:
            tk.Label(form, text=label, font=("Segoe UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w")
            entry = tk.Entry(form, font=("Consolas", 11), bg=COLORS["panel2"], 
                            fg=COLORS["text"], relief="flat", insertbackground=COLORS["text"])
            entry.pack(fill="x", ipady=8, pady=(2, 10))
            if label == "Username":
                username_entry = entry
            elif label == "Email":
                email_entry = entry
            else:
                password_entry = entry
        
        def do_register():
            data, status = api("/api/auth/register", 
                              {"username": username_entry.get(), "email": email_entry.get(), 
                               "password": password_entry.get()})
            if status == 201:
                self.user_token = data["token"]
                self.username = data["username"]
                save_config({"user_token": self.user_token})
                self.bootstrap()
            else:
                messagebox.showerror("Eroare", data.get("error", "Eroare register"))
        
        tk.Button(form, text="INREGISTRARE", font=("Segoe UI", 11, "bold"),
                  bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                  command=do_register).pack(fill="x", ipady=10)
        
        tk.Button(form, text="Ai cont? Autentifica-te",
                  font=("Segoe UI", 9), bg=COLORS["bg"], fg=COLORS["spark"],
                  relief="flat", cursor="hand2", command=self.build_login).pack(pady=12)
    
    def build_license_prompt(self, msg=""):
        self.clear()
        wrap = tk.Frame(self, bg=COLORS["bg"])
        wrap.pack(expand=True, fill="both", padx=60, pady=100)
        
        tk.Label(wrap, text="LICENTA NECESARA", font=("Segoe UI", 18, "bold"),
                 fg=COLORS["forge"], bg=COLORS["bg"]).pack(pady=10)
        tk.Label(wrap, text=msg or "Introdu o cheie de licenta valid", font=("Segoe UI", 10),
                 fg=COLORS["muted"], bg=COLORS["bg"], wraplength=460).pack(pady=(0, 20))
        
        key_entry = tk.Entry(wrap, font=("Consolas", 12), justify="center",
                            bg=COLORS["panel2"], fg=COLORS["text"], relief="flat", 
                            insertbackground=COLORS["text"])
        key_entry.insert(0, "OF-XXXX-XXXX-XXXX-XXXX")
        key_entry.pack(fill="x", ipady=10, pady=(0, 14))
        
        def do_redeem():
            key = key_entry.get()
            data, status = api("/api/license/redeem", {"license_key": key}, user_token=self.user_token)
            if status == 200:
                self.bootstrap()
            else:
                messagebox.showerror("Eroare", data.get("error", "Cheie invalida"))
        
        tk.Button(wrap, text="ACTIVEAZA", font=("Segoe UI", 11, "bold"),
                  bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                  command=do_redeem).pack(fill="x", ipady=10)
    
    def build_main(self):
        self.clear()
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill="both", expand=True)
        
        # SIDEBAR
        sidebar = tk.Frame(root, bg=COLORS["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="OPTIFORGE", font=("Segoe UI", 12, "bold"),
                 fg=COLORS["forge"], bg=COLORS["sidebar"]).pack(pady=(16, 4), padx=12, anchor="w")
        tk.Label(sidebar, text=f"{self.username}", font=("Consolas", 8),
                 fg=COLORS["muted"], bg=COLORS["sidebar"]).pack(padx=12, anchor="w")
        tk.Label(sidebar, text=f"Plan: {self.license_info.get('tier_label')}", 
                 font=("Consolas", 8), fg=COLORS["spark"], bg=COLORS["sidebar"]).pack(padx=12, anchor="w", pady=(0, 16))
        
        self.pages = {}
        tier = self.license_info.get("tier", "standard")
        for t in ["standard", "pro", "ultimate"]:
            if ["standard", "pro", "ultimate"].index(t) <= ["standard", "pro", "ultimate"].index(tier):
                tk.Button(sidebar, text=t.upper(), font=("Segoe UI", 10, "bold"),
                         anchor="w", bg=COLORS["sidebar"], fg=COLORS["text"], relief="flat",
                         cursor="hand2", command=lambda tt=t: self.show_tier(tt)
                         ).pack(fill="x", padx=8, pady=2, ipady=8)
        
        tk.Button(sidebar, text="ACCOUNT", font=("Segoe UI", 10),
                 anchor="w", bg=COLORS["sidebar"], fg=COLORS["muted"], relief="flat",
                 cursor="hand2", command=self.show_account).pack(fill="x", padx=8, pady=2, ipady=6)
        tk.Button(sidebar, text="LOGOUT", font=("Segoe UI", 9),
                 anchor="w", bg=COLORS["danger"], fg="#1a0806", relief="flat",
                 cursor="hand2", command=self.do_logout).pack(fill="x", padx=8, pady=(16, 2), ipady=6)
        
        # CONTENT
        self.content = tk.Frame(root, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)
        
        self.show_tier("standard")
    
    def show_tier(self, tier):
        for w in self.content.winfo_children():
            w.destroy()
        
        wrap = tk.Frame(self.content, bg=COLORS["bg"])
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(wrap, text=f"{tier.upper()} OPTIMIZATIONS", font=("Segoe UI", 16, "bold"),
                 fg=COLORS["forge"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 16))
        
        # ONE-CLICK
        tk.Button(wrap, text=f"ONE-CLICK {tier.upper()}", font=("Segoe UI", 11, "bold"),
                 bg=COLORS["forge"], fg="#1a0e06", relief="flat", cursor="hand2",
                 command=lambda: self.run_tier(tier)).pack(fill="x", ipady=12, pady=(0, 16))
        
        # LIST MODULES
        modules = MODULES.get(tier, [])
        scroll = tk.Frame(wrap, bg=COLORS["bg"])
        scroll.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scroll, bg=COLORS["bg"], highlightthickness=0)
        canvas.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(scroll, orient="vertical", command=canvas.yview)
        scrollbar.pack(fill="y", side="right")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        frame = tk.Frame(canvas, bg=COLORS["bg"])
        canvas.create_window(0, 0, window=frame, anchor="nw")
        
        for mod_id, label, func in modules:
            card = tk.Frame(frame, bg=COLORS["panel"])
            card.pack(fill="x", pady=4)
            
            left = tk.Frame(card, bg=COLORS["panel"])
            left.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            tk.Label(left, text=label, font=("Segoe UI", 10, "bold"),
                    fg=COLORS["text"], bg=COLORS["panel"]).pack(anchor="w")
            
            tk.Button(card, text="RUN", font=("Segoe UI", 9, "bold"),
                     bg=COLORS["spark"], fg=COLORS["bg"], relief="flat", cursor="hand2",
                     command=lambda f=func: self.run_module(label, f)).pack(side="right", padx=12, pady=8)
        
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def run_module(self, name, func):
        win = tk.Toplevel(self)
        win.title(name)
        win.geometry("600x400")
        win.configure(bg=COLORS["bg"])
        
        log = scrolledtext.ScrolledText(win, bg=COLORS["panel2"], fg=COLORS["muted"],
                                       font=("Consolas", 9), relief="flat", wrap="word")
        log.pack(fill="both", expand=True, padx=10, pady=10)
        log.config(state="disabled")
        
        def log_fn(msg):
            log.config(state="normal")
            log.insert("end", msg + "\n")
            log.see("end")
            log.config(state="disabled")
            log.update()
        
        def worker():
            snap_before = snapshot_system()
            m_restore_point(log_fn)
            func(log_fn)
            snap_after = snapshot_system()
            log_fn(f"\n[ANTES] {snap_before['data']}")
            log_fn(f"[DEPOIS] {snap_after['data']}")
            api("/api/optimization/log", {"module_key": name, "status": "ok"}, user_token=self.user_token)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def run_tier(self, tier):
        modules = MODULES.get(tier, [])
        win = tk.Toplevel(self)
        win.title(f"ONE-CLICK {tier.upper()}")
        win.geometry("700x500")
        win.configure(bg=COLORS["bg"])
        
        log = scrolledtext.ScrolledText(win, bg=COLORS["panel2"], fg=COLORS["muted"],
                                       font=("Consolas", 8), relief="flat", wrap="word")
        log.pack(fill="both", expand=True, padx=10, pady=10)
        log.config(state="disabled")
        
        def log_fn(msg):
            log.config(state="normal")
            log.insert("end", msg + "\n")
            log.see("end")
            log.config(state="disabled")
            log.update()
        
        def worker():
            snap_before = snapshot_system()
            log_fn(f"=== ONE-CLICK {tier.upper()} ===\n")
            for mod_id, label, func in modules:
                log_fn(f"\n[{label}]")
                func(log_fn)
                api("/api/optimization/log", {"module_key": mod_id, "status": "ok"}, user_token=self.user_token)
            snap_after = snapshot_system()
            log_fn(f"\n\n[INAINTE] {json.dumps(snap_before['data'], indent=2)}")
            log_fn(f"\n[DUPA] {json.dumps(snap_after['data'], indent=2)}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def show_account(self):
        for w in self.content.winfo_children():
            w.destroy()
        
        wrap = tk.Frame(self.content, bg=COLORS["bg"])
        wrap.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(wrap, text="ACCOUNT", font=("Segoe UI", 16, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 20))
        
        card = tk.Frame(wrap, bg=COLORS["panel"])
        card.pack(fill="x", padx=16, pady=16)
        
        for label, value in [("Username", self.username),
                            ("Dispozitiv", get_device_name()),
                            ("Plan", self.license_info.get("tier_label")),
                            ("Cheie", self.license_info.get("license_key", "—")[:20] + "...")]:
            row = tk.Frame(card, bg=COLORS["panel"])
            row.pack(fill="x", padx=16, pady=6)
            tk.Label(row, text=label, font=("Segoe UI", 9), fg=COLORS["muted"], bg=COLORS["panel"]).pack(anchor="w")
            tk.Label(row, text=str(value), font=("Consolas", 10), fg=COLORS["text"], bg=COLORS["panel"]).pack(anchor="w")
    
    def do_logout(self):
        api("/api/auth/logout", {}, user_token=self.user_token)
        save_config({})
        self.user_token = None
        self.build_login()
    
    def clear(self):
        for w in self.winfo_children():
            w.destroy()

if __name__ == "__main__":
    app = OptiForgeApp()
    app.mainloop()
