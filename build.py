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
        "--icon=config/icon.ico",  # 아이콘 파일 (나중에 추가해야 함)
        "--add-data=config;config",  # 추가 데이터 파일 (Windows 형식)
        "--add-data=templates;templates",
        "main.py"
    ]
    
    # 운영체제에 따라 경로 구분자 조정
    if sys.platform != "win32":
        pyinstaller_cmd[5] = "--add-data=config:config"  # Unix 형식
        pyinstaller_cmd[6] = "--add-data=templates:templates"
    
    print("실행 파일 빌드 중...")
    subprocess.call(pyinstaller_cmd)
    
    print("추가 리소스 복사 중...")
    # 빈 폴더 생성 (실행 시 필요한 폴더들)
    os.makedirs("dist/FoodLabManager/data", exist_ok=True)
    os.makedirs("dist/FoodLabManager/output", exist_ok=True)
    
    print("빌드 완료!")
    print(f"생성된 실행 파일: {os.path.abspath('dist/FoodLabManager')}")

if __name__ == "__main__":
    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치하세요: pip install pyinstaller")
        sys.exit(1)
    
    build_executable()