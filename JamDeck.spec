# -*- mode: python ; coding: utf-8 -*-

# itch-dl artık uygulamaya GÖMÜLÜ: indirme harici "itch-dl" CLI'ına shell-out
# etmek yerine, frozen exe kendini "__itch-dl__" argümanıyla yeniden çağırıp
# bundled itch_dl.cli.run()'ı çalıştırır (her sistemde çalışır, pip kurulumu gerekmez).
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

_hidden = (collect_submodules('itch_dl')
           + collect_submodules('bs4')
           + ['lxml.etree', 'lxml._elementpath', 'tqdm', 'requests', 'certifi'])
_datas = [('frontend', 'frontend')] + collect_data_files('certifi')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JamDeck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['JamDeck.ico'],
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JamDeck',
)
