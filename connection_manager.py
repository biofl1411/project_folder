#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
연결 모드 관리자
내부망(DB 직접 연결) / 외부망(API 연결) 자동 전환
'''

import os
import json
import socket

# 설정 파일 경로
CONFIG_PATH = 'config/connection_config.json'

# 연결 모드
MODE_INTERNAL = 'internal'  # 내부망 - DB 직접 연결
MODE_EXTERNAL = 'external'  # 외부망 - API 연결


class ConnectionManager:
    """연결 모드 관리 클래스"""

    _instance = None
    _mode = None
    _api_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._detect_mode()
        return cls._instance

    def _get_base_path(self):
        """기본 경로 반환"""
        import sys
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _load_config(self):
        """설정 파일 로드"""
        config_file = os.path.join(self._get_base_path(), CONFIG_PATH)

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_config(self, config):
        """설정 파일 저장"""
        config_dir = os.path.join(self._get_base_path(), 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_file = os.path.join(self._get_base_path(), CONFIG_PATH)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def _detect_mode(self):
        """연결 모드 자동 감지"""
        config = self._load_config()

        # 수동 설정이 있으면 사용
        if config.get('mode'):
            self._mode = config['mode']
            return

        # 자동 감지: 내부망 서버에 연결 시도
        internal_host = config.get('internal_host', '192.168.0.96')
        internal_port = config.get('internal_port', 3306)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((internal_host, internal_port))
            sock.close()

            if result == 0:
                self._mode = MODE_INTERNAL
                print(f"[연결 모드] 내부망 감지됨 - DB 직접 연결 사용")
            else:
                self._mode = MODE_EXTERNAL
                print(f"[연결 모드] 외부망 감지됨 - API 연결 사용")
        except:
            self._mode = MODE_EXTERNAL
            print(f"[연결 모드] 외부망으로 설정 - API 연결 사용")

    def get_mode(self):
        """현재 연결 모드 반환"""
        return self._mode

    def is_internal(self):
        """내부망 모드인지 확인"""
        return self._mode == MODE_INTERNAL

    def is_external(self):
        """외부망 모드인지 확인"""
        return self._mode == MODE_EXTERNAL

    def set_mode(self, mode):
        """연결 모드 수동 설정"""
        if mode in [MODE_INTERNAL, MODE_EXTERNAL]:
            self._mode = mode
            config = self._load_config()
            config['mode'] = mode
            self._save_config(config)

    def get_api_client(self):
        """API 클라이언트 인스턴스 반환 (외부망용)"""
        if self._api_client is None:
            from api_client import ApiClient
            self._api_client = ApiClient()
        return self._api_client


# 싱글톤 인스턴스
connection_manager = ConnectionManager()


def get_connection_mode():
    """현재 연결 모드 반환"""
    return connection_manager.get_mode()


def is_internal_mode():
    """내부망 모드인지 확인"""
    return connection_manager.is_internal()


def is_external_mode():
    """외부망 모드인지 확인"""
    return connection_manager.is_external()
