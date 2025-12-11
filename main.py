#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
식품 실험/분석 관련 견적 및 스케줄 관리 시스템
메인 실행 파일
'''

import sys
import os

# 가장 먼저 오류 로그 설정 (모든 오류 캡처)
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# 오류 로그 파일 경로
error_log_path = os.path.join(application_path, 'startup_error.log')

def write_error(msg):
    """오류를 파일에 기록"""
    try:
        with open(error_log_path, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now()}] {msg}\n")
    except:
        pass

# 모든 예외를 파일에 기록
def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    write_error(f"Unhandled exception:\n{error_msg}")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook

try:
    write_error("프로그램 시작...")

    import traceback
    import logging
    from datetime import datetime

    # 실행 파일 위치를 기준으로 경로 설정
    os.chdir(application_path)
    sys.path.insert(0, application_path)
    write_error(f"작업 경로: {application_path}")

    # 로그 파일 설정
    log_dir = os.path.join(application_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    write_error("로깅 설정 완료")

    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import QTimer
    write_error("PyQt5 임포트 완료")

    from views import MainWindow
    from version import VERSION, APP_DISPLAY_NAME
    write_error("views, version 임포트 완료")
    logger.info("기본 모듈 로드 완료")

except Exception as e:
    import traceback
    write_error(f"초기화 오류: {e}\n{traceback.format_exc()}")
    sys.exit(1)

def check_dependencies():
    """필요한 라이브러리 체크"""
    try:
        import PyQt5
        import pymysql
        return True
    except ImportError as e:
        return False

def setup_environment():
    """환경 설정"""
    # 필요한 폴더 확인 및 생성
    folders = ['data', 'output', 'templates', 'config', 'logs']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"폴더 생성: {folder}")

    # 연결 모드 확인
    try:
        from connection_manager import is_internal_mode, get_connection_mode
        mode = get_connection_mode()
        logger.info(f"연결 모드: {mode}")

        if is_internal_mode():
            # 내부망: 데이터베이스 직접 초기화
            from database import init_database
            init_database()
            logger.info("데이터베이스 초기화 완료 (내부망)")
        else:
            # 외부망: API 서버 연결 확인
            from api_client import ApiClient
            api = ApiClient()
            if api.health_check():
                logger.info("API 서버 연결 확인 완료 (외부망)")
            else:
                logger.warning("API 서버 연결 실패 - 오프라인 모드")

    except Exception as e:
        logger.error(f"환경 설정 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        # 오류가 발생해도 계속 진행 (로그인 시도 가능)

    return True

def check_for_updates(window):
    """업데이트 확인 (비동기)"""
    try:
        from updater import check_for_updates_on_startup
        # 참조를 유지하기 위해 window에 저장
        window._updater = check_for_updates_on_startup(window)
    except Exception as e:
        # 업데이트 확인 실패는 조용히 무시
        print(f"업데이트 확인 오류: {e}")

def main():
    """메인 함수"""
    logger.info("=" * 50)
    logger.info("프로그램 시작")
    logger.info(f"버전: {VERSION}")
    logger.info("=" * 50)

    # 의존성 체크
    if not check_dependencies():
        logger.error("필요한 라이브러리가 설치되지 않았습니다.")
        print("필요한 라이브러리가 설치되지 않았습니다.")
        print("pip install -r requirements.txt 명령으로 필요한 라이브러리를 설치하세요.")
        return

    # 환경 설정
    logger.info("환경 설정 시작...")
    if not setup_environment():
        logger.error("환경 설정 중 오류가 발생했습니다.")
        print("환경 설정 중 오류가 발생했습니다.")
        return

    logger.info("환경 설정 완료")

    # QApplication 생성
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 모던한 스타일 적용
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationVersion(VERSION)
    logger.info("QApplication 생성 완료")

    # 메인 윈도우 생성 및 표시
    try:
        logger.info("메인 윈도우 생성 중...")
        window = MainWindow()
        logger.info("메인 윈도우 생성 완료")

        # 2초 후 업데이트 확인 (비동기)
        QTimer.singleShot(2000, lambda: check_for_updates(window))

    except Exception as e:
        error_msg = f"프로그램 초기화 중 오류가 발생했습니다:\n{e}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
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
    logger.info("앱 실행 시작")
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"예상치 못한 오류가 발생했습니다: {e}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        print(error_msg)
        sys.exit(1)
