#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
데이터베이스 기능 테스트
'''

import pytest
import os
import sys
import tempfile
import shutil

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabase:
    '''데이터베이스 테스트 클래스'''

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        '''테스트 전 임시 데이터베이스 설정'''
        # 임시 디렉토리로 작업 디렉토리 변경
        self.original_dir = os.getcwd()
        os.chdir(tmp_path)

        # data 폴더 생성
        os.makedirs('data', exist_ok=True)

        yield

        # 테스트 후 원래 디렉토리로 복귀
        os.chdir(self.original_dir)

    def test_get_connection(self):
        '''데이터베이스 연결 테스트'''
        import database

        conn = database.get_connection()
        assert conn is not None

        # 연결이 정상적으로 작동하는지 확인
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

        conn.close()

    def test_init_database(self):
        '''데이터베이스 초기화 테스트'''
        import database

        # 초기화 실행
        database.init_database()

        # 테이블이 생성되었는지 확인
        conn = database.get_connection()
        cursor = conn.cursor()

        # 필수 테이블 목록
        required_tables = [
            'items', 'pricing', 'clients', 'schedules',
            'schedule_items', 'users', 'settings', 'logs',
            'food_types', 'fees'
        ]

        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            assert result is not None, f"테이블 '{table}'이 생성되지 않았습니다"

        conn.close()

    def test_default_admin_user(self):
        '''기본 관리자 계정 생성 테스트'''
        import database

        database.init_database()

        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
        result = cursor.fetchone()

        assert result is not None, "관리자 계정이 생성되지 않았습니다"
        assert result['username'] == 'admin'
        assert result['role'] == 'admin'

        conn.close()

    def test_default_settings(self):
        '''기본 설정값 테스트'''
        import database

        database.init_database()

        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT key, value FROM settings WHERE key = 'tax_rate'")
        result = cursor.fetchone()

        assert result is not None, "기본 설정이 생성되지 않았습니다"
        assert result['value'] == '10'

        conn.close()

    def test_sample_data_insertion(self):
        '''샘플 데이터 삽입 테스트'''
        import database

        database.init_database()

        conn = database.get_connection()
        cursor = conn.cursor()

        # 샘플 업체 데이터 확인
        cursor.execute("SELECT COUNT(*) as count FROM clients")
        result = cursor.fetchone()
        assert result['count'] >= 2, "샘플 업체 데이터가 삽입되지 않았습니다"

        # 샘플 식품 유형 데이터 확인
        cursor.execute("SELECT COUNT(*) as count FROM food_types")
        result = cursor.fetchone()
        assert result['count'] >= 1, "샘플 식품 유형 데이터가 삽입되지 않았습니다"

        # 참고: 수수료 데이터는 cash_db.xlsx에서 가져오므로 여기서 검증하지 않음

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
