# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for macOS distribution."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include tax_rates directory
        (str(project_root / "tax_rates"), "tax_rates"),
    ],
    hiddenimports=[
        "pandas",
        "pandas._libs.tslibs.timedeltas",
        "pandas._libs.tslibs.nattype",
        "pandas._libs.tslibs.np_datetime",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Taximate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=True,  # Required for macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Taximate",
)

app = BUNDLE(
    coll,
    name="Taximate.app",
    icon=None,  # Add path to .icns file for custom icon: "assets/icon.icns"
    bundle_identifier="com.taximate.app",
    info_plist={
        "CFBundleName": "Taximate",
        "CFBundleDisplayName": "Taximate",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13.0",
    },
)
