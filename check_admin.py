#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
관리자 계정 확인 및 생성 스크립트
MySQL 데이터베이스에 접속하여 admin 계정을 확인하고 없으면 생성합니다.
"""

import json
import pymysql

def main():
    # 설정 파일 읽기
    try:
        with open('config/db_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"데이터베이스 설정 로드 완료: {config['host']}:{config['port']}/{config['database']}")
    except Exception as e:
        print(f"설정 파일 읽기 오류: {e}")
        return

    # 데이터베이스 연결
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset=config.get('charset', 'utf8mb4'),
            cursorclass=pymysql.cursors.DictCursor
        )
        print("데이터베이스 연결 성공!")
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return

    try:
        cursor = conn.cursor()

        # users 테이블 존재 여부 확인
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("users 테이블이 존재하지 않습니다. 테이블을 생성합니다...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    department VARCHAR(100),
                    position VARCHAR(100),
                    email VARCHAR(100),
                    phone VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("users 테이블 생성 완료!")

        # 현재 사용자 목록 조회
        print("\n=== 현재 등록된 사용자 목록 ===")
        cursor.execute("SELECT id, username, password, name, role FROM users")
        users = cursor.fetchall()

        if users:
            for user in users:
                print(f"  ID: {user['id']}, 사용자명: {user['username']}, 비밀번호: {user['password']}, 이름: {user['name']}, 역할: {user['role']}")
        else:
            print("  등록된 사용자가 없습니다.")

        # admin 계정 확인
        cursor.execute("SELECT * FROM users WHERE username = %s", ('admin',))
        admin = cursor.fetchone()

        if admin:
            print(f"\n관리자 계정이 존재합니다!")
            print(f"  사용자명: {admin['username']}")
            print(f"  비밀번호: {admin['password']}")
            print(f"  이름: {admin.get('name', 'N/A')}")
            print(f"  역할: {admin.get('role', 'N/A')}")

            # 비밀번호 초기화 옵션
            response = input("\n비밀번호를 'admin123'으로 초기화하시겠습니까? (y/n): ")
            if response.lower() == 'y':
                cursor.execute("UPDATE users SET password = %s WHERE username = %s", ('admin123', 'admin'))
                conn.commit()
                print("비밀번호가 'admin123'으로 초기화되었습니다.")
        else:
            print("\n관리자 계정이 존재하지 않습니다. 새로 생성합니다...")
            cursor.execute("""
                INSERT INTO users (username, password, name, role)
                VALUES (%s, %s, %s, %s)
            """, ('admin', 'admin123', '관리자', 'admin'))
            conn.commit()
            print("관리자 계정이 생성되었습니다!")
            print("  사용자명: admin")
            print("  비밀번호: admin123")

        conn.close()
        print("\n작업 완료!")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == "__main__":
    main()
