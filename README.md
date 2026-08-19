# OptiForge — Launcher de optimizare cu sistem de licențe

Trei componente:

```
opticore/
├── backend/    → server Flask + SQLite (generează/validează chei)
├── admin/      → panou web pentru admin (servit automat de backend)
└── client/     → launcher-ul desktop (sursă Python → se compilează în .exe)
```

## 1. Pornește serverul (backend + panou admin)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Serverul pornește pe `http://localhost:5000`. Panoul de admin e la
`http://localhost:5000/admin`.

**IMPORTANT:** schimbă parola implicită înainte de folosire reală, fie
direct în `app.py` (variabila `ADMIN_PASSWORD`), fie prin variabilă de mediu:

```bash
export OPTIFORGE_ADMIN_PASS="parola-ta-puternica"
python app.py
```

Pentru a fi accesibil de pe internet (nu doar local), trebuie găzduit pe un
server real (VPS, Railway, Render etc.) cu HTTPS — vezi secțiunea
"Recomandări pentru producție" mai jos.

## 2. Generează chei de licență (panou admin)

Deschide `http://localhost:5000/admin` în browser, autentifică-te cu parola
admin, apoi:

- Alege nivelul: **Standard** (2 optimizări) sau **Pro** (4 optimizări)
- Alege câte chei generezi și pentru câte zile sunt valabile (lasă gol = fără expirare)
- Apasă **„Forjează chei”** — cheile apar instant, format `OF-XXXX-XXXX-XXXX-XXXX`

Din tabelul de mai jos poți **revoca**, **reactiva**, **reseta device-ul**
(dacă un client își schimbă PC-ul) sau **șterge** orice cheie.

## 3. Configurează și compilează launcher-ul client

1. Deschide `client/opticore_launcher.py`
2. Modifică linia:
   ```python
   SERVER_URL = "http://localhost:5000"
   ```
   cu adresa reală a serverului tău (ex: `https://licente.site-ul-tau.ro`)

3. Compilează în `.exe` **pe o mașină Windows** (PyInstaller nu poate face
   cross-compile de pe Linux/Mac către Windows):

   ```bash
   cd client
   pip install -r requirements.txt
   pyinstaller --noconsole --onefile --name OptiForge opticore_launcher.py
   ```

   Executabilul rezultat apare în `client/dist/OptiForge.exe` — acesta e
   fișierul pe care îl distribui utilizatorilor.

## Cum funcționează licențierea

- La prima pornire, launcher-ul cere o cheie de licență
- Cheia se validează contra serverului tău și se **leagă de acel PC**
  (hardware ID calculat local, fără date personale)
- Dacă cineva încearcă aceeași cheie pe alt PC, serverul refuză —
  poți debloca manual din panoul admin ("Resetează device")
- La activări viitoare, launcher-ul reține cheia local și doar o
  reverifică la fiecare pornire

## Cele 4 optimizări incluse

| Optimizare | Nivel minim | Ce face |
|---|---|---|
| Curățare fișiere temporare | Standard | Șterge fișierele temp + golește cache DNS |
| Optimizare rețea & DNS | Standard | Flush DNS, resetare adaptor, reset Winsock |
| Optimizare pornire Windows | Pro | Deschide managerul de pornire pentru dezactivare manuală |
| Mod performanță maximă | Pro | Activează planul „Performanță ridicată" + reduce efecte vizuale |

Poți adăuga optimizări noi editând `OPTIMIZATION_LABELS` și
`OPTIMIZATION_FUNCS` din `opticore_launcher.py`, apoi actualizează
`TIERS` din `backend/app.py` ca să le incluzi în nivelul dorit.

## Recomandări pentru producție

Setup-ul actual e gata de folosit local/pentru teste. Pentru lansare reală:

- **Găzduiește backend-ul** pe un server cu HTTPS (Railway, Render, un VPS
  cu Nginx + certificat SSL) — nu lăsa cheile să circule prin HTTP simplu
- **Parolă admin puternică**, ideal cu autentificare 2FA în față (ex. prin
  Cloudflare Access) dacă panoul e expus public
- **Backup periodic** al fișierului `licenses.db`
- Token-urile de admin sunt ținute în memorie și se pierd la restart
  server — pentru volum mare, ia în calcul sesiuni persistente (Redis) și
  hash de parolă (bcrypt) în loc de comparație simplă
