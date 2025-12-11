#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
프로그램 빌드 스크립트
PyInstaller를 사용하여 실행 파일 생성
'''

import os
import sys
import shutil
import subprocess

def build_executable():
    """PyInstaller를 사용하여 실행 파일 생성"""
    print("빌드 준비 중...")
    
    # 임시 폴더 정리
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # PyInstaller 명령어 구성
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=FoodLabManager",
        "--windowed",  # GUI 애플리케이션
        "--onedir",    # 폴더로 빌드 (--onefile 옵션을 사용하면 단일 파일로 빌드)
        "--add-data=config;config",  # 추가 데이터 파일 (Windows 형식)
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=charset_normalizer",
        "--hidden-import=certifi",
        "--hidden-import=idna",
        "--hidden-import=connection_manager",
        "--hidden-import=api_client",
        "--collect-submodules=requests",
        "main.py"
    ]

    # 아이콘 파일이 있으면 추가
    if os.path.exists("config/icon.ico"):
        pyinstaller_cmd.insert(5, "--icon=config/icon.ico")

    # 운영체제에 따라 경로 구분자 조정
    if sys.platform != "win32":
        # Windows가 아닌 경우 경로 구분자를 콜론으로 변경
        for i, cmd in enumerate(pyinstaller_cmd):
            if cmd.startswith("--add-data=") and ";" in cmd:
                pyinstaller_cmd[i] = cmd.replace(";", ":")
    
    print("실행 파일 빌드 중...")
    print(f"명령어: {' '.join(pyinstaller_cmd)}")
    result = subprocess.call(pyinstaller_cmd)

    if result != 0:
        print(f"\n빌드 실패! (종료 코드: {result})")
        print("해결 방법:")
        print("  1. pip install --upgrade pyinstaller")
        print("  2. pip cache purge")
        print("  3. 다시 python build.py 실행")
        return
    
    print("추가 리소스 복사 중...")
    # 필요한 폴더 생성
    os.makedirs("dist/FoodLabManager/data", exist_ok=True)
    os.makedirs("dist/FoodLabManager/output", exist_ok=True)
    os.makedirs("dist/FoodLabManager/config", exist_ok=True)

    # config 폴더 복사 (exe 파일과 같은 레벨에)
    if os.path.exists("config"):
        for file in os.listdir("config"):
            src = os.path.join("config", file)
            dst = os.path.join("dist/FoodLabManager/config", file)
            if os.path.isfile(src):
                shutil.copy(src, dst)
        print("  - config 폴더 복사 완료")

    # 데이터베이스 파일 복사 (있는 경우)
    if os.path.exists("data/app.db"):
        shutil.copy("data/app.db", "dist/FoodLabManager/data/app.db")
        print("  - 데이터베이스 복사 완료")

    # Excel 파일 복사 (있는 경우)
    if os.path.exists("cash_db.xlsx"):
        shutil.copy("cash_db.xlsx", "dist/FoodLabManager/cash_db.xlsx")
        print("  - cash_db.xlsx 복사 완료")

    print("\n빌드 완료!")
    print(f"생성된 실행 파일: {os.path.abspath('dist/FoodLabManager')}")
    print("\n실행 방법: dist/FoodLabManager/FoodLabManager.exe 실행")

if __name__ == "__main__":
    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치하세요: pip install pyinstaller")
        sys.exit(1)
    
    build_executable()