# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# Collecter toutes les dépendances nécessaires
datas = []
binaries = []
hiddenimports = []

# Ajouter les données de PyMuPDF
datas += collect_data_files('fitz')
binaries += collect_data_files('fitz', include_py_files=True)
hiddenimports += collect_submodules('fitz')

# Ajouter les données de PyPDF2
datas += collect_data_files('PyPDF2')
hiddenimports += collect_submodules('PyPDF2')

# Ajouter les données de PIL
datas += collect_data_files('PIL')
hiddenimports += collect_submodules('PIL')

# Ajouter les données de img2pdf
datas += collect_data_files('img2pdf')
hiddenimports += collect_submodules('img2pdf')

# Ajouter le README
datas.append(('README.md', '.'))

a = Analysis(
    ['compress_pdf.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'pandas', 'PyQt5.QtWebEngineWidgets'],
    cipher=block_cipher,
    noarchive=False,
)

# Nettoyer les fichiers inutiles
a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-win')]
a.binaries = [x for x in a.binaries if not x[0].startswith('vcruntime')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDFCompressor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version='file_version_info.txt',
    uac_admin=False,
    manifest='app.manifest',
)
