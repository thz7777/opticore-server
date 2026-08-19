# OptiForge — Build .exe (pe Windows)

Acesta este clientul desktop premium. Încarcă același UI web ca în browser,
dar rulează optimizările **reale** pe sistemul tău prin `psutil` + comenzi Windows.

## Cerințe
- Windows 10/11
- Python 3.11+ (https://python.org — bifează "Add Python to PATH")

## Pași build

```bat
cd client\desktop
pip install -r requirements.txt
pyinstaller OptiForge.spec
```

Rezultatul: `client\desktop\dist\OptiForge.exe`

## Structură
```
client/desktop/
├── main.py              → entry point: pornește server local + fereastra pywebview
├── local_api.py         → server Flask local: stats reale (psutil) + execuție optimizări + proxy către server
├── optimizations.py     → motorul de optimizări Windows (31 module, legitime)
├── requirements.txt
└── OptiForge.spec       → configurație PyInstaller (fără UPX, build curat)
```

UI-ul (`../web/`) este bundle-uit în exe prin `datas` din spec.

## Cum funcționează
1. La pornire, `main.py` lansează un server Flask local pe `127.0.0.1:5959`
2. pywebview deschide o fereastră către `http://127.0.0.1:5959/`
3. UI-ul comunică cu serverul local pentru:
   - **Stats reale** (`/api/local/stats`) — CPU/RAM/GPU/Disk via psutil
   - **Execuție optimizări** (`/api/local/run-optimization`) — comenzi Windows reale
4. Toate celelalte `/api/*` sunt proxy-uite către serverul remote OptiForge:
   - **Auth/licențe** — secrete rămân server-side, nu în exe
   - **Device binding** — verificat pe server
   - **Istoric** — stocat server-side

## Configurare server remote
În `local_api.py` (sau variabilă de mediu):
```python
SERVER_URL = "https://opticore-server.onrender.com"
# sau: set OPTIFORGE_SERVER_URL=https://serverul-tau.com
```

## Build curat & transparent (anti false-positive)
- **FĂRĂ UPX** (`upx=False` în spec) — reduce masiv false-positive-urile
- **FĂRĂ code injection, bypass, exclusions automate**
- **FĂRĂ packere/obfuscatoare**
- Comenzi documentate și reversibile

## Authenticode signing (recomandat)
Pentru a elimina complet alertele SmartScreen:
1. Obține un certificat de code signing (DigiCert, Sectigo etc.)
2. Semnează exe-ul:
   ```bat
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\OptiForge.exe
   ```
3. Publică SHA-256 hash-ul fiecărui release:
   ```bat
   certutil -hashfile dist\OptiForge.exe SHA256
   ```

## Microsoft false-positive
Dacă apare un false-positive:
- Trimite exe-ul la Microsoft pentru analiză: https://www.microsoft.com/wdsi/filesubmission
- Include sursa (acest repo) și descrierea build-ului curat

## Dev (fără build)
Pentru a testa rapid fără PyInstaller:
```bat
cd client\desktop
pip install -r requirements.txt
python main.py
```
