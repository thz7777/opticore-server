# -*- mode: python ; coding: utf-8 -*-
# Build curat, transparent, fără obfuscatoare sau packere suspecte.
#   cd client/desktop
#   pyinstaller OptiForge.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # Bundle UI-ul web premium împreună cu executabilul
    datas=[
        ('../web/index.html', 'web'),
        ('../web/styles.css', 'web'),
        ('../web/app.js', 'web'),
    ],
    hiddenimports=['psutil', 'requests', 'webview', 'flask'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OptiForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # FĂRĂ UPX — reduce false-positive-uri antivirus
    console=False,       # aplicație GUI, fără consolă
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,   # vezi secțiunea Authenticode din README
    entitlements_file=None,
)
