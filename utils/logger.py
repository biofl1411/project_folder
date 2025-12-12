#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
애플리케이션 로깅 유틸리티
- Python logging 모듈과 통합
- 기존 API(log_message, log_error 등) 호환 유지
- 통일된 로그 형식 사용
"""

import logging
import datetime
import traceback
import os
import sys

# 로그 디렉토리 및 파일 경로 설정
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.join(BASE_PATH, 'logs')
LOG_FILE_PATH = os.path.join(BASE_PATH, 'app_log.txt')

# 로그 디렉토리 생성
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except:
        pass


class AppLogger:
    """
    애플리케이션 로거 클래스
    Python logging을 래핑하여 카테고리 기반 로깅 제공
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if AppLogger._initialized:
            return
        AppLogger._initialized = True
        self._setup_logging()

    def _setup_logging(self):
        """Python logging 설정"""
        # 루트 로거 가져오기
        self.root_logger = logging.getLogger('FoodLabManager')
        self.root_logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거 (중복 방지)
        self.root_logger.handlers.clear()

        # 통일된 로그 형식
        # 형식: [2025-12-12 09:41:37.587] [INFO] [ScheduleTab] 메시지
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.root_logger.addHandler(console_handler)

        # 일반 로그 파일 핸들러 (app_log.txt)
        try:
            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"[WARNING] 로그 파일 핸들러 생성 실패: {e}")

        # 일별 로그 파일 핸들러 (logs/app_YYYYMMDD.log)
        try:
            daily_log_file = os.path.join(LOG_DIR, f"app_{datetime.datetime.now().strftime('%Y%m%d')}.log")
            daily_handler = logging.FileHandler(daily_log_file, encoding='utf-8')
            daily_handler.setLevel(logging.DEBUG)
            daily_handler.setFormatter(formatter)
            self.root_logger.addHandler(daily_handler)
        except Exception as e:
            print(f"[WARNING] 일별 로그 파일 핸들러 생성 실패: {e}")

    def _get_logger(self, category):
        """카테고리별 로거 반환"""
        return logging.getLogger(f'FoodLabManager.{category}')

    def info(self, category, message):
        """정보 로그"""
        self._get_logger(category).info(message)

    def warning(self, category, message):
        """경고 로그"""
        self._get_logger(category).warning(message)

    def error(self, category, message):
        """오류 로그"""
        self._get_logger(category).error(message)

    def critical(self, category, message):
        """치명적 오류 로그"""
        self._get_logger(category).critical(message)

    def exception(self, category, message, exc_info=None):
        """예외 로그 (트레이스백 포함)"""
        if exc_info is None:
            exc_info = sys.exc_info()

        tb_str = ''.join(traceback.format_exception(*exc_info))
        full_message = f"{message}\n{tb_str}"
        self._get_logger(category).error(full_message)

    def debug(self, category, message):
        """디버그 로그"""
        self._get_logger(category).debug(message)


# 전역 로거 인스턴스
_logger = AppLogger()


def log_message(category, message, level='INFO'):
    """
    간편한 로그 함수

    Args:
        category: 로그 카테고리 (예: 'ScheduleTab', 'ClientTab')
        message: 로그 메시지
        level: 로그 레벨 ('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL')
    """
    level = level.upper()
    if level == 'INFO':
        _logger.info(category, message)
    elif level == 'WARNING':
        _logger.warning(category, message)
    elif level == 'ERROR':
        _logger.error(category, message)
    elif level == 'DEBUG':
        _logger.debug(category, message)
    elif level == 'CRITICAL':
        _logger.critical(category, message)
    else:
        _logger.info(category, message)


def log_error(category, message):
    """오류 로그 함수"""
    _logger.error(category, message)


def log_exception(category, message, exc_info=None):
    """예외 로그 함수 (트레이스백 포함)"""
    _logger.exception(category, message, exc_info)


def log_debug(category, message):
    """디버그 로그 함수"""
    _logger.debug(category, message)


def log_warning(category, message):
    """경고 로그 함수"""
    _logger.warning(category, message)


def get_logger(category):
    """
    카테고리별 Python 로거 반환
    Python logging API 직접 사용 가능

    Args:
        category: 로그 카테고리

    Returns:
        logging.Logger 인스턴스
    """
    return logging.getLogger(f'FoodLabManager.{category}')


def safe_get(obj, key, default=''):
    """
    sqlite3.Row 또는 딕셔너리에서 안전하게 값을 가져옵니다.

    Args:
        obj: sqlite3.Row 또는 딕셔너리 객체
        key: 가져올 키
        default: 기본값 (기본: 빈 문자열)

    Returns:
        키에 해당하는 값 또는 기본값
    """
    try:
        if obj is None:
            return default

        # 딕셔너리인 경우 .get() 사용
        if isinstance(obj, dict):
            value = obj.get(key, default)
            return value if value is not None else default

        # sqlite3.Row 또는 기타 객체인 경우 인덱스 접근
        try:
            value = obj[key]
            return value if value is not None else default
        except (KeyError, IndexError, TypeError):
            return default

    except Exception as e:
        log_error('safe_get', f"키 '{key}' 접근 중 오류: {str(e)}")
        return default
