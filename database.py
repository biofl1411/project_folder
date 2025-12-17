#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
데이터베이스 연결 및 기본 함수
MySQL 서버 연결 버전 (연결 풀링 지원)
'''

import os
import json
import datetime
import threading

# MySQL 연결 라이브러리
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("pymysql이 설치되지 않았습니다. pip install pymysql 명령으로 설치하세요.")

# 연결 풀링 라이브러리
try:
    from dbutils.pooled_db import PooledDB
    POOL_AVAILABLE = True
except ImportError:
    POOL_AVAILABLE = False
    print("[DB] dbutils 미설치 - 연결 풀링 비활성화 (pip install dbutils)")

# 설정 파일 경로
CONFIG_PATH = 'config/db_config.json'

# 연결 풀 (싱글톤)
_connection_pool = None
_pool_lock = threading.Lock()


def load_db_config():
    '''데이터베이스 설정 로드'''
    # 실행 파일 위치 기준으로 경로 설정
    import sys
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    config_file = os.path.join(base_path, CONFIG_PATH)

    # config 파일이 없으면 _internal/config 경로도 확인 (PyInstaller 빌드용)
    if not os.path.exists(config_file):
        internal_config = os.path.join(base_path, '_internal', CONFIG_PATH)
        if os.path.exists(internal_config):
            config_file = internal_config

    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 기본 설정
        return {
            "host": "192.168.0.96",
            "port": 3306,
            "database": "foodlab",
            "user": "foodlab",
            "password": "bphsk*1411**",
            "charset": "utf8mb4"
        }


def _is_external_client():
    '''외부망 클라이언트인지 확인 (API 서버가 아닌 외부망 클라이언트)'''
    import os
    # API 서버에서 실행 중이면 False (DB 접근 필요)
    if os.environ.get('FOODLAB_API_SERVER', '').lower() == 'true':
        return False
    # 외부망 클라이언트인지 확인
    try:
        from connection_manager import is_external_mode
        return is_external_mode()
    except:
        return False


def _get_pool():
    '''연결 풀 반환 (싱글톤, 스레드 안전)'''
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    with _pool_lock:
        # 더블 체크 락킹
        if _connection_pool is not None:
            return _connection_pool

        if not POOL_AVAILABLE:
            return None

        # 외부망 클라이언트에서는 DB 연결 풀 사용하지 않음 (API 사용)
        if _is_external_client():
            print("[DB] 외부망 클라이언트 - DB 연결 풀 사용 안함 (API 사용)")
            return None

        config = load_db_config()

        try:
            _connection_pool = PooledDB(
                creator=pymysql,
                maxconnections=20,  # 최대 연결 수
                mincached=3,        # 최소 유휴 연결 수
                maxcached=10,       # 최대 유휴 연결 수
                maxusage=None,      # 연결 재사용 횟수 (None=무제한)
                blocking=True,      # 풀이 가득 찼을 때 대기
                setsession=[],      # 세션 시작 시 실행할 SQL
                ping=1,             # 연결 상태 확인 (0=없음, 1=요청시, 2=커서생성시)
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset=config['charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print(f"[DB] 연결 풀 초기화 완료 (최대 {20}개 연결)")
        except Exception as e:
            print(f"[DB] 연결 풀 초기화 실패: {e}")
            _connection_pool = None

        return _connection_pool


def get_connection():
    '''데이터베이스 연결 객체 반환 (풀링 지원)'''
    if not MYSQL_AVAILABLE:
        raise Exception("pymysql이 설치되지 않았습니다.")

    # 외부망 클라이언트에서는 DB 직접 연결 불가 (API 사용해야 함)
    if _is_external_client():
        raise Exception("외부망 클라이언트에서는 DB 직접 연결이 불가합니다. API를 사용하세요.")

    # 연결 풀 사용 시도
    pool = _get_pool()
    if pool is not None:
        try:
            return pool.connection()
        except Exception as e:
            print(f"[DB] 풀에서 연결 가져오기 실패: {e}, 직접 연결 시도...")

    # 풀 사용 불가 시 직접 연결 (폴백)
    config = load_db_config()

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset=config['charset'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return conn

def test_connection():
    '''데이터베이스 연결 테스트'''
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True, "연결 성공"
    except Exception as e:
        return False, str(e)

def init_database():
    '''데이터베이스 초기화 및 테이블 생성'''
    conn = get_connection()
    cursor = conn.cursor()

    # 실험 항목 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(255) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 수수료 테이블 (pricing)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pricing (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT,
        food_type VARCHAR(255) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 업체정보 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ceo VARCHAR(100),
        business_no VARCHAR(50),
        category VARCHAR(100),
        phone VARCHAR(50),
        fax VARCHAR(50),
        contact_person VARCHAR(100),
        email VARCHAR(255),
        sales_rep VARCHAR(100),
        toll_free VARCHAR(50),
        zip_code VARCHAR(20),
        address TEXT,
        notes TEXT,
        sales_business VARCHAR(255),
        sales_phone VARCHAR(50),
        sales_mobile VARCHAR(50),
        sales_address TEXT,
        mobile VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 스케줄 및 견적 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT,
        title VARCHAR(255) NOT NULL,
        start_date VARCHAR(50),
        end_date VARCHAR(50),
        status VARCHAR(50) DEFAULT 'pending',
        total_price DECIMAL(15,2),
        product_name VARCHAR(255),
        food_type_id INT,
        test_method TEXT,
        storage_condition VARCHAR(255),
        test_period_days INT DEFAULT 0,
        test_period_months INT DEFAULT 0,
        test_period_years INT DEFAULT 0,
        sampling_count INT DEFAULT 6,
        report_interim INT DEFAULT 0,
        report_korean INT DEFAULT 1,
        report_english INT DEFAULT 0,
        extension_test INT DEFAULT 0,
        custom_temperatures TEXT,
        memo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        packaging_weight INT DEFAULT 0,
        packaging_unit VARCHAR(20) DEFAULT 'g',
        additional_test_items TEXT,
        removed_test_items TEXT,
        experiment_schedule_data TEXT,
        custom_dates TEXT,
        actual_experiment_days INT,
        estimate_date VARCHAR(50),
        expected_date VARCHAR(50),
        interim_report_date VARCHAR(50),
        FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 스케줄 항목 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        schedule_id INT,
        item_id INT,
        quantity INT DEFAULT 1,
        price DECIMAL(10,2),
        discount DECIMAL(5,2) DEFAULT 0,
        FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 사용자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        name VARCHAR(100) NOT NULL,
        role VARCHAR(50) DEFAULT 'user',
        last_login TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 설정 테이블 (공용 설정)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        `key` VARCHAR(100) UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 사용자별 설정 테이블 (계정별 설정)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        `key` VARCHAR(100) NOT NULL,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY unique_user_key (user_id, `key`),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 로그 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(255) NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 식품 유형 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_types (
        id INT AUTO_INCREMENT PRIMARY KEY,
        type_name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        sterilization VARCHAR(100),
        pasteurization VARCHAR(100),
        appearance VARCHAR(255),
        test_items TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 수수료 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fees (
        id INT AUTO_INCREMENT PRIMARY KEY,
        test_item VARCHAR(255) NOT NULL,
        food_category VARCHAR(255),
        price DECIMAL(10,2) NOT NULL,
        description TEXT,
        sample_quantity INT DEFAULT 0,
        display_order INT DEFAULT 100,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    # 스케줄 첨부파일 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule_attachments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        schedule_id INT NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_size INT DEFAULT 0,
        file_type VARCHAR(50),
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')

    conn.commit()

    # 기본 설정 데이터 삽입
    default_settings = [
        ('tax_rate', '10', '부가세율 (%)'),
        ('default_discount', '0', '기본 할인율 (%)'),
        ('output_path', 'output', '기본 출력 파일 저장 경로'),
        ('template_path', 'templates', '템플릿 파일 경로')
    ]

    for key, value, description in default_settings:
        cursor.execute('''
        INSERT IGNORE INTO settings (`key`, value, description)
        VALUES (%s, %s, %s)
        ''', (key, value, description))

    # 관리자 계정 생성 (기본 비밀번호: admin123)
    cursor.execute('''
    INSERT IGNORE INTO users (username, password, name, role)
    VALUES (%s, %s, %s, %s)
    ''', ('admin', 'admin123', '관리자', 'admin'))

    # 수수료 데이터가 비어있으면 cash_db.xlsx에서 자동 가져오기
    cursor.execute("SELECT COUNT(*) as cnt FROM fees")
    if cursor.fetchone()['cnt'] == 0:
        # cash_db.xlsx 파일 찾기
        excel_paths = ['cash_db.xlsx', '../cash_db.xlsx', 'data/cash_db.xlsx']
        excel_file = None
        for path in excel_paths:
            if os.path.exists(path):
                excel_file = path
                break

        if excel_file:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active

                # Excel 데이터 삽입 (첫 번째 행은 헤더)
                inserted_count = 0
                for row in ws.iter_rows(min_row=2, values_only=True):
                    display_order, food_category, test_item, price, sample_qty = row

                    if not test_item:
                        continue

                    display_order = display_order if display_order is not None else 100
                    food_category = food_category if food_category else ""
                    price = price if price is not None else 0
                    sample_qty = int(sample_qty) if sample_qty is not None else 0

                    cursor.execute('''
                        INSERT INTO fees (test_item, food_category, price, description, display_order, sample_quantity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (test_item, food_category, price, "", display_order, sample_qty))
                    inserted_count += 1

                print(f"cash_db.xlsx에서 {inserted_count}개 수수료 데이터 자동 로드 완료!")
            except ImportError:
                print("openpyxl 모듈이 없어 Excel 파일을 로드할 수 없습니다.")
            except Exception as e:
                print(f"Excel 파일 로드 중 오류: {e}")

    conn.commit()
    conn.close()

    print("데이터베이스 초기화 완료!")


if __name__ == "__main__":
    # 연결 테스트
    success, message = test_connection()
    if success:
        print(f"MySQL 서버 연결 성공!")
        init_database()
    else:
        print(f"MySQL 서버 연결 실패: {message}")
