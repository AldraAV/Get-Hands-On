# -*- mode: python ; coding: utf-8 -*-
# MeterMano-onefile.spec
# Modo: --onefile → Un solo .exe portable. Tarda ~3-5 seg extra al lanzar porque
# extrae el entorno en %TEMP% automáticamente. La ventaja: copias el .exe a donde
# quieras y funciona sin llevar carpetas hermanas.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

# Recolectar modulos pesados ocultos que PyInstaller suele perder
hidden_imports = []
hidden_imports += collect_submodules('fitz')       # pymupdf
hidden_imports += collect_submodules('pdf2docx')   # pdf2docx
hidden_imports += collect_submodules('pikepdf')    # pikepdf
hidden_imports += collect_submodules('pytesseract')# ocr
hidden_imports += collect_submodules('img2pdf')    # img2pdf
hidden_imports += collect_submodules('pypdf')      # pypdf

# Recolectar datas de modules si las hubiere
datas = []
datas += collect_data_files('pdf2docx')
# OJO: Si agregas recursos propios como iconos, descomenta:
# datas += [('resources/*', 'resources')]

a = Analysis(
    ['get_hands_on\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'tkinter', 'matplotlib', 'IPython', 'notebook', 'scipy', 'pandas'],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

# ─── ONEFILE: Los binarios/datas van DENTRO del EXE, no en COLLECT ───────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,    # ← Diferencia clave: van aquí, no en COLLECT
    a.datas,       # ← Ídem con los datos
    [],
    name='MeterMano',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # runtime_tmpdir: dónde extrae los archivos temporales al ejecutarse.
    # None = usa %TEMP% del sistema (recomendado).
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None
)
# NOTA: Sin bloque COLLECT. El onefile lo incrusta todo internally.
