#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
식품 실험/분석 관련 견적 및 스케줄 관리 시스템
메인 실행 파일
'''

import sys
import os
import traceback

# 실행 파일 위치를 기준으로 경로 설정 (빌드 후 실행을 위해 필요)
if getattr(sys, 'frozen', False):
    # 실행 파일로 빌드된 경우
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    sys.path.insert(0, application_path)

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QIcon
    
    from views import MainWindow
    from database import init_database
except ImportError as e:
    print(f"필요한 라이브러리를 불러올 수 없습니다: {e}")
    sys.exit(1)

def check_dependencies():
    """필요한 라이브러리 체크"""
    try:
        import PyQt5
        import sqlite3
        return True
    except ImportError as e:
        return False

def setup_environment():
    """환경 설정"""
    # 필요한 폴더 확인 및 생성
    folders = ['data', 'output', 'templates', 'config']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # 데이터베이스 초기화
    try:
        init_database()
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    # 의존성 체크
    if not check_dependencies():
        print("필요한 라이브러리가 설치되지 않았습니다.")
        print("pip install -r requirements.txt 명령으로 필요한 라이브러리를 설치하세요.")
        return
    
    # 환경 설정
    if not setup_environment():
        print("환경 설정 중 오류가 발생했습니다.")
        return
    
    # QApplication 생성
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일 적용
    
    # 메인 윈도우 생성 및 표시
    try:
        window = MainWindow()
    except Exception as e:
        error_msg = f"프로그램 초기화 중 오류가 발생했습니다:\n{e}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        # GUI 오류 메시지
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("오류")
        error_dialog.setText("프로그램 초기화 중 오류가 발생했습니다")
        error_dialog.setDetailedText(error_msg)
        error_dialog.exec_()
        return
    
    # 앱 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")
        print(traceback.format_exc())
        sys.exit(1)