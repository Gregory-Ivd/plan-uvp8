# -*- mode: python ; coding: utf-8 -*-
"""Збірка портативної версії: тека з .exe, яку можна покласти на флешку."""

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("resources/template.json", "resources"),
        ("resources/logo.png", "resources"),
        ("resources/logo_small.png", "resources"),
        ("resources/app.ico", "resources"),
    ],
    hiddenimports=["reportlab.pdfbase._fontdata"],
    hookspath=[],
    runtime_hooks=[],
    # PIL не виключати: reportlab тягне його при імпорті.
    excludes=["numpy", "matplotlib", "pytest", "pandas", "IPython", "tornado"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Мій план",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Мій план",
)
