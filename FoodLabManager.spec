# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

block_cipher = None

# Visual C++ 런타임 DLL 자동 포함
binaries = []
try:
    # PyQt5의 DLL 경로에서 필요한 파일 수집
    import PyQt5
    pyqt5_path = os.path.dirname(PyQt5.__file__)

    # Qt 플랫폼 플러그인 포함
    plugins_path = os.path.join(pyqt5_path, 'Qt5', 'plugins', 'platforms')
    if os.path.exists(plugins_path):
        for f in os.listdir(plugins_path):
            if f.endswith('.dll'):
                binaries.append((os.path.join(plugins_path, f), 'platforms'))
except Exception as e:
    print(f"PyQt5 DLL 수집 중 오류: {e}")

# 모든 하위 모듈 수집
hidden_imports = [
    # 기본 모듈
    'logging',
    'traceback',
    'json',
    'datetime',
    'socket',
    'os',
    'sys',

    # 외부 라이브러리
    'requests',
    'urllib3',
    'charset_normalizer',
    'certifi',
    'idna',
    'pymysql',
    'pymysql.cursors',
    'openpyxl',
    'pandas',
    'reportlab',
    'packaging',

    # PyQt5
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.sip',

    # 프로젝트 모듈
    'version',
    'database',
    'connection_manager',
    'api_client',
    'updater',

    # models
    'models',
    'models.users',
    'models.clients',
    'models.schedules',
    'models.schedule_attachments',
    'models.fees',
    'models.items',
    'models.product_types',
    'models.activity_log',
    'models.communications',
    'models.frequent_recipients',

    # views
    'views',
    'views.login',
    'views.main_window',
    'views.schedule_tab',
    'views.schedule_dialog',
    'views.client_tab',
    'views.client_dialog',
    'views.food_type_tab',
    'views.fee_tab',
    'views.estimate_tab',
    'views.schedule_management_tab',
    'views.communication_tab',
    'views.user_management_tab',
    'views.settings_dialog',
]

# 추가 하위 모듈 수집
hidden_imports += collect_submodules('requests')
hidden_imports += collect_submodules('urllib3')
hidden_imports += collect_submodules('pymysql')
hidden_imports += collect_submodules('openpyxl')
hidden_imports += collect_submodules('reportlab')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=hidden_imports,
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
    name='FoodLabManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 디버깅을 위해 콘솔 모드
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name='FoodLabManager',
)
