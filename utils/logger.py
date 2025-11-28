#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
애플리케이션 로깅 유틸리티
모든 작업과 오류를 기록합니다.
"""

import datetime
import traceback
import os
import sys

# 로그 파일 경로 설정
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app_log.txt')


class AppLogger:
    """애플리케이션 로거 클래스"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.log_file_path = LOG_FILE_PATH

    def _write_log(self, level, category, message):
        """로그를 파일과 콘솔에 기록"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] [{level}] [{category}] {message}"

        # 콘솔 출력
        print(log_entry)

        # 파일 출력
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(log_entry + '\n')
        except Exception as e:
            print(f"[{timestamp}] [ERROR] [Logger] 로그 파일 쓰기 실패: {str(e)}")

    def info(self, category, message):
        """정보 로그"""
        self._write_log('INFO', category, message)

    def warning(self, category, message):
        """경고 로그"""
        self._write_log('WARNING', category, message)

    def error(self, category, message):
        """오류 로그"""
        self._write_log('ERROR', category, message)

    def critical(self, category, message):
        """치명적 오류 로그"""
        self._write_log('CRITICAL', category, message)

    def exception(self, category, message, exc_info=None):
        """예외 로그 (트레이스백 포함)"""
        if exc_info is None:
            exc_info = sys.exc_info()

        tb_str = ''.join(traceback.format_exception(*exc_info))
        full_message = f"{message}\n{tb_str}"
        self._write_log('EXCEPTION', category, full_message)

    def debug(self, category, message):
        """디버그 로그"""
        self._write_log('DEBUG', category, message)


# 전역 로거 인스턴스
_logger = AppLogger()


def log_message(category, message, level='INFO'):
    """간편한 로그 함수"""
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


def log_error(category, message):
    """오류 로그 함수"""
    _logger.error(category, message)


def log_exception(category, message, exc_info=None):
    """예외 로그 함수"""
    _logger.exception(category, message, exc_info)


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
