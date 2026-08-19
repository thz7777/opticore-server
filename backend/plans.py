"""
Definiția planurilor (Standard / Pro / Ultimate) și catalogul complet
de module de optimizare.
"""

# ----------------------------------------------------------------------------
# CATALOG complet de optimizari
# ----------------------------------------------------------------------------
# Fiecare modul: key, label, descriere, categoria (pentru grupare in UI)

OPTIMIZATIONS = {
    # ---- STANDARD ----
    "system_cleaner": {
        "label": "System Cleaner",
        "category": "cleaning",
        "description": "Curăță fișierele temporare, cache DNS și deșeuri de sistem pentru a elibera spațiu.",
    },
    "network_connectivity": {
        "label": "Network & Connectivity",
        "category": "network",
        "description": "Flush DNS, resetare Winsock și adaptor pentru conexiuni mai stabile.",
    },
    "windows_responsiveness": {
        "label": "Windows Responsiveness",
        "category": "windows",
        "description": "Reduce latența de răspuns a interfeței și accelerează menu-urile.",
    },
    "ram_memory": {
        "label": "RAM & Memory",
        "category": "memory",
        "description": "Eliberează memorie RAM ocupată inutil și optimizează cache-ul de sistem.",
    },
    "performance_gaming": {
        "label": "Performance & Gaming",
        "category": "performance",
        "description": "Activează modul de performanță maximă și prioritate CPU pentru aplicații.",
    },
    "windows_startup": {
        "label": "Windows Startup",
        "category": "startup",
        "description": "Analizează și optimizează programele care pornesc odată cu Windows.",
    },
    "restore_point": {
        "label": "Restore Point",
        "category": "restore",
        "description": "Creează un punct de restaurare înainte de modificări majore.",
    },
    "optimization_history": {
        "label": "Optimization History",
        "category": "logs",
        "description": "Vizualizează istoricul complet al optimizărilor aplicate și rezultatele.",
    },

    # ---- PRO ----
    "disk_storage": {
        "label": "Disk & Storage",
        "category": "storage",
        "description": "Defragmentare SSD/HDD, cleanup și optimizare spațiu de stocare.",
    },
    "advanced_memory": {
        "label": "Advanced Memory Management",
        "category": "memory",
        "description": "Ajustează cache manager, working set și paginare pentru eficiență maximă.",
    },
    "cpu_optimization": {
        "label": "CPU Optimization",
        "category": "performance",
        "description": "Core parking, frequency scaling și alocare core-uri pentru workload-uri intense.",
    },
    "gpu_optimization": {
        "label": "GPU Optimization",
        "category": "performance",
        "description": "Optimizează driver-ul GPU, power management și priorități de randare.",
    },
    "process_management": {
        "label": "Process Management",
        "category": "performance",
        "description": "Identifică și suspendă procesele care consumă resurse inutil.",
    },
    "windows_services": {
        "label": "Windows Services",
        "category": "windows",
        "description": "Dezactivează servicii Windows neesențiale care rulează în fundal.",
    },
    "power_management": {
        "label": "Power Management",
        "category": "windows",
        "description": "Profile de alimentare customizate pentru performanță vs eficiență.",
    },
    "advanced_network": {
        "label": "Advanced Network",
        "category": "network",
        "description": "Tuning avansat TCP/IP, MTU, RSS și network throttling.",
    },
    "gaming_optimization": {
        "label": "Gaming Optimization",
        "category": "gaming",
        "description": "Game Mode, priorități multimedia și减少 input lag pentru jocuri.",
    },
    "system_resources": {
        "label": "System Resources",
        "category": "performance",
        "description": "Monitorizare și alocare dinamică a resurselor sistem.",
    },
    "custom_profiles": {
        "label": "Custom Optimization Profiles",
        "category": "performance",
        "description": "Creează și salvează profiluri de optimizare personalizate.",
    },

    # ---- ULTIMATE ----
    "privacy": {
        "label": "Privacy",
        "category": "privacy",
        "description": "Dezactivează telemetrie, reclame și colectare de date de confidențialitate.",
    },
    "diagnostics_telemetry": {
        "label": "Diagnostics & Telemetry",
        "category": "privacy",
        "description": "Oprește serviciile de diagnosticare și telemetrie Windows.",
    },
    "advanced_gaming": {
        "label": "Advanced Gaming",
        "category": "gaming",
        "description": "Tuning profund pentru gaming: GPU scheduling, hardware-accelerated GPU scheduling.",
    },
    "advanced_network_opt": {
        "label": "Advanced Network Optimization",
        "category": "network",
        "description": "Optimizare UDP, packet prioritization și QoS pentru gaming/streaming.",
    },
    "input_lag_diagnostics": {
        "label": "Input-Lag Diagnostics",
        "category": "gaming",
        "description": "Măsoară și reduce input lag-ul perifericelor și al display-ului.",
    },
    "frame_time_optimization": {
        "label": "Frame-Time Optimization",
        "category": "gaming",
        "description": "Stabilizează frame times și reduce stutter-ul în jocuri.",
    },
    "windows_debloat": {
        "label": "Windows Debloat",
        "category": "windows",
        "description": "Elimină aplicațiile preinstalate și bloatware-ul inutil.",
    },
    "background_process_mgmt": {
        "label": "Background Process Management",
        "category": "performance",
        "description": "Gestionare avansată a proceselor de fundal și a aplicațiilor startup fantomă.",
    },
    "advanced_startup": {
        "label": "Advanced Startup",
        "category": "startup",
        "description": "Control granular asupra serviciilor și task-urilor de la pornire.",
    },
    "automatic_optimization": {
        "label": "Automatic Optimization",
        "category": "performance",
        "description": "Optimizare automată programată — menține sistemul mereu rapid.",
    },
    "per_game_profiles": {
        "label": "Per-Game Profiles",
        "category": "gaming",
        "description": "Profiluri de optimizare specifice fiecărui joc detectat.",
    },
    "benchmark_results": {
        "label": "Benchmark & Before/After Results",
        "category": "performance",
        "description": "Rulează benchmark-uri și compară performanța înainte/după optimizare.",
    },
}

# ----------------------------------------------------------------------------
# PLANURI (tier-e)
# ----------------------------------------------------------------------------
# Fiecare plan include modulele sale + tot ce au planurile inferioare.

TIERS = {
    "standard": {
        "label": "Standard",
        "price_label": "Gratuit / Basic",
        "optimizations": [
            "system_cleaner",
            "network_connectivity",
            "windows_responsiveness",
            "ram_memory",
            "performance_gaming",
            "windows_startup",
            "restore_point",
            "optimization_history",
        ],
    },
    "pro": {
        "label": "Pro",
        "price_label": "Pro",
        "optimizations": [
            # Standard
            "system_cleaner", "network_connectivity", "windows_responsiveness",
            "ram_memory", "performance_gaming", "windows_startup",
            "restore_point", "optimization_history",
            # Pro extras
            "disk_storage", "advanced_memory", "cpu_optimization",
            "gpu_optimization", "process_management", "windows_services",
            "power_management", "advanced_network", "gaming_optimization",
            "system_resources", "custom_profiles",
        ],
    },
    "ultimate": {
        "label": "Ultimate",
        "price_label": "Ultimate",
        "optimizations": list(OPTIMIZATIONS.keys()),
    },
}

# Ordinea planurilor pentru comparare (standard < pro < ultimate)
TIER_RANK = {"standard": 0, "pro": 1, "ultimate": 2}


def tier_includes(tier, optimization_key):
    """Returnează True dacă planul include modulul dat."""
    return optimization_key in TIERS.get(tier, TIERS["standard"])["optimizations"]


def get_optimizations_for_tier(tier):
    """Lista de module disponibile pentru un plan, cu metadate complete."""
    keys = TIERS.get(tier, TIERS["standard"])["optimizations"]
    return [{"key": k, **OPTIMIZATIONS[k]} for k in keys]


def get_catalog(tier=None):
    """Catalog complet cu disponibilitatea per plan."""
    result = []
    for key, meta in OPTIMIZATIONS.items():
        available = tier_includes(tier, key) if tier else False
        result.append({"key": key, **meta, "available": available})
    return result


# Categorii pentru grupare în UI (sidebar tabs)
CATEGORIES = [
    {"key": "cleaning", "label": "Cleaning"},
    {"key": "network", "label": "Network"},
    {"key": "memory", "label": "Memory"},
    {"key": "windows", "label": "Windows"},
    {"key": "gaming", "label": "Gaming"},
    {"key": "startup", "label": "Startup"},
    {"key": "storage", "label": "Storage"},
    {"key": "privacy", "label": "Privacy"},
    {"key": "performance", "label": "Performance"},
    {"key": "restore", "label": "Restore Center"},
    {"key": "logs", "label": "Optimization Logs"},
]
