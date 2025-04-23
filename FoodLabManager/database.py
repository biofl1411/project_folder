#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
데이터베이스 연결 및 기본 함수
'''

import sqlite3
import os
import datetime

DB_PATH = 'data/app.db'

def get_connection():
    '''데이터베이스 연결 객체 반환'''
    # DB 파일이 있는 디렉토리 확인 및 생성
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn

def init_database():
    '''데이터베이스 초기화 및 테이블 생성'''
    conn = get_connection()
    cursor = conn.cursor()
    
    # 실험 항목 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 수수료 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pricing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        food_type TEXT NOT NULL,
        price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')
    
    # 업체정보 테이블 - 필드 수정
    cursor.execute('''
    DROP TABLE IF EXISTS clients
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ceo TEXT,
        phone TEXT,
        address TEXT,
        contact_person TEXT,
        mobile TEXT,
        sales_rep TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 스케줄 및 견적 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        title TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        total_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients (id)
    )
    ''')
    
    # 스케줄 항목 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        item_id INTEGER,
        quantity INTEGER DEFAULT 1,
        price REAL,
        discount REAL DEFAULT 0,
        FOREIGN KEY (schedule_id) REFERENCES schedules (id),
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')
    
    # 사용자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 설정 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 로그 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 식품 유형 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL,
        category TEXT,
        sterilization TEXT,
        pasteurization TEXT,
        appearance TEXT,
        test_items TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 수수료 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_item TEXT NOT NULL,
        food_category TEXT,
        price REAL NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 기본 설정 데이터 삽입
    default_settings = [
        ('tax_rate', '10', '부가세율 (%)'),
        ('default_discount', '0', '기본 할인율 (%)'),
        ('output_path', 'output', '기본 출력 파일 저장 경로'),
        ('template_path', 'templates', '템플릿 파일 경로')
    ]
    
    for key, value, description in default_settings:
        cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value, description)
        VALUES (?, ?, ?)
        ''', (key, value, description))
    
    # 관리자 계정 생성 (기본 비밀번호: admin123)
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, name, role)
    VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin123', '관리자', 'admin'))
    
    # 샘플 업체 데이터
    sample_clients = [
        ('계림농장', '김대표', '02-123-4567', '경기도 용인시 처인구', '김담당', '010-1234-5678', '박영업'),
        ('거성씨푸드', '이사장', '051-987-6543', '부산시 해운대구 우동', '최담당', '010-8765-4321', '정영업')
    ]
    
    for name, ceo, phone, address, contact, mobile, sales_rep in sample_clients:
        cursor.execute('''
        INSERT OR IGNORE INTO clients (name, ceo, phone, address, contact_person, mobile, sales_rep)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, ceo, phone, address, contact, mobile, sales_rep))
    
    # 샘플 식품 유형 데이터
    sample_food_types = [
        ('일반제품', '일반', '살균', '멸균', '성상', '관능평가, 대장균군(정량), 세균수, 수분'),
        ('과채음료', '음료', '살균', '', '성상', '관능평가, 대장균군(정량), 세균수, pH'),
        ('조미료', '조미', '', '', '성상', '관능평가, 대장균군(정량), 발효도수 세균수(정량), 세균수, pH'),
        ('과채가공품', '가공', '', '', '성상', '관능평가, 대장균(정량), 세균수'),
        ('과채가공품2', '가공', '', '', '향미', '관능평가, 대장균(정량), 세균수, 총아플라톡신'),
        ('육류', '육가공', '', '', '성상', '관능평가, 대장균(정량), 세균수'),
        ('음류', '음료', '', '', '성상', '관능평가, 대장균(정량), 세균수'),
        ('기타수산가공품', '수산', '', '', '성상', '관능평가, 대장균(정량), 세균수'),
        ('두유/음료', '음료', '', '', '성상', '관능평가, 대장균군(정량), 세균수, pH')
    ]
    
    for type_name, category, sterilization, pasteurization, appearance, test_items in sample_food_types:
        cursor.execute('''
        INSERT OR IGNORE INTO food_types (type_name, category, sterilization, pasteurization, appearance, test_items)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (type_name, category, sterilization, pasteurization, appearance, test_items))
    
    # 샘플 수수료 데이터
    sample_fees = [
        ('일반세균', '일반', 20000, '일반세균 검사'),
        ('대장균군', '일반', 25000, '대장균군 검사'),
        ('세균수', '일반', 22000, '세균수 검사'),
        ('pH', '일반', 15000, 'pH 검사'),
        ('수분', '일반', 18000, '수분 함량 검사'),
        ('발효도수', '일반', 30000, '발효도수 검사'),
        ('총아플라톡신', '일반', 50000, '총아플라톡신 검사')
    ]
    
    for test_item, food_category, price, description in sample_fees:
        cursor.execute('''
        INSERT OR IGNORE INTO fees (test_item, food_category, price, description)
        VALUES (?, ?, ?, ?)
        ''', (test_item, food_category, price, description))
    
    conn.commit()
    conn.close()
    
    print("데이터베이스 초기화 완료!")
        

if __name__ == "__main__":
    init_database()