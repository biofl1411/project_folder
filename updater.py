#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
자동 업데이트 모듈
서버에서 새 버전 확인 및 업데이트 수행
'''

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 서버 설정
SERVER_IP = "192.168.0.96"
SHARE_NAME = "shared"
SERVER_PATH = f"\\\\{SERVER_IP}\\{SHARE_NAME}"

# 현재 버전 파일
VERSION_FILE = "version.txt"
EXE_NAME = "소비기한설정.exe"

def get_local_version():
    """로컬 버전 가져오기"""
    try:
        version_path = get_resource_path(VERSION_FILE)
        if os.path.exists(version_path):
            with open(version_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"로컬 버전 확인 오류: {e}")
    return "0.0.0"

def get_server_version():
    """서버 버전 가져오기"""
    try:
        server_version_path = os.path.join(SERVER_PATH, VERSION_FILE)
        if os.path.exists(server_version_path):
            with open(server_version_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"서버 버전 확인 오류: {e}")
    return None

def get_resource_path(relative_path):
    """리소스 경로 가져오기 (exe 빌드 시에도 작동)"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def compare_versions(local, server):
    """버전 비교 (server가 더 높으면 True)"""
    try:
        local_parts = [int(x) for x in local.split('.')]
        server_parts = [int(x) for x in server.split('.')]

        for i in range(max(len(local_parts), len(server_parts))):
            l = local_parts[i] if i < len(local_parts) else 0
            s = server_parts[i] if i < len(server_parts) else 0
            if s > l:
                return True
            elif l > s:
                return False
        return False
    except:
        return False

def check_for_updates():
    """업데이트 확인"""
    local_version = get_local_version()
    server_version = get_server_version()

    if server_version is None:
        return False, local_version, None, "서버에 연결할 수 없습니다"

    needs_update = compare_versions(local_version, server_version)
    return needs_update, local_version, server_version, None

def perform_update():
    """업데이트 수행"""
    try:
        # 실행 파일인 경우에만 업데이트
        if not getattr(sys, 'frozen', False):
            return False, "개발 모드에서는 업데이트가 지원되지 않습니다"

        current_exe = sys.executable
        current_dir = os.path.dirname(current_exe)

        # 서버에서 새 파일 복사
        server_exe = os.path.join(SERVER_PATH, EXE_NAME)
        server_version = os.path.join(SERVER_PATH, VERSION_FILE)

        if not os.path.exists(server_exe):
            return False, "서버에서 업데이트 파일을 찾을 수 없습니다"

        # 임시 파일로 다운로드
        temp_exe = os.path.join(current_dir, "update_temp.exe")
        temp_version = os.path.join(current_dir, "version_temp.txt")

        shutil.copy2(server_exe, temp_exe)
        shutil.copy2(server_version, temp_version)

        # 업데이트 스크립트 생성 (현재 프로그램 종료 후 실행)
        update_script = os.path.join(current_dir, "do_update.bat")
        with open(update_script, 'w', encoding='utf-8') as f:
            f.write(f'''@echo off
chcp 65001 > nul
echo 업데이트 중...
timeout /t 2 /nobreak > nul
del "{current_exe}"
move "{temp_exe}" "{current_exe}"
del "{os.path.join(current_dir, VERSION_FILE)}"
move "{temp_version}" "{os.path.join(current_dir, VERSION_FILE)}"
echo 업데이트 완료! 프로그램을 재시작합니다...
start "" "{current_exe}"
del "%~f0"
''')

        # 업데이트 스크립트 실행
        subprocess.Popen(['cmd', '/c', update_script],
                        creationflags=subprocess.CREATE_NO_WINDOW)

        return True, "업데이트를 시작합니다. 프로그램이 재시작됩니다."

    except Exception as e:
        return False, f"업데이트 중 오류 발생: {e}"
