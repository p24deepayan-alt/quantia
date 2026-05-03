# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('sklearn')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('statsmodels')
hiddenimports += collect_submodules('seaborn')
hiddenimports += ['psutil', 'openpyxl', 'pyarrow', 'sklearn.utils._typedefs', 'sklearn.neighbors._partition_nodes', 'sklearn.utils._cython_blas', 'sklearn.neighbors._quad_tree', 'sklearn.tree._utils']

a = Analysis(
    ['src/quantia/__main__.py'],
    pathex=[os.path.abspath('src')],
    binaries=[],
    datas=[
        ('reference/logo', 'reference/logo'),
        ('reference/fonts', 'reference/fonts'),
        ('src/quantia/theme', 'quantia/theme'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['notebook', 'jedi', 'matplotlib.tests', 'numpy.tests', 'IPython', 'torch', 'pytest', 'scipy.stats.tests'],
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
    name='Quantia',
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
    icon='reference/logo/Quantia_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Quantia',
)
