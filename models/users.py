# models/users.py
from database import get_connection
import datetime

class User:
    @staticmethod
    def authenticate(username, password):
        """사용자 인증"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password, name, role
                FROM users
                WHERE username = ? AND password = ?
            """, (username, password))
            user = cursor.fetchone()

            if user:
                # 마지막 로그인 시간 업데이트
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
                conn.commit()

            conn.close()

            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'role': user['role']
                }
            return None
        except Exception as e:
            print(f"사용자 인증 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_id(user_id):
        """ID로 사용자 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, name, role, last_login, created_at
                FROM users
                WHERE id = ?
            """, (user_id,))
            user = cursor.fetchone()
            conn.close()

            if user:
                return dict(user)
            return None
        except Exception as e:
            print(f"사용자 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 사용자 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, name, role, last_login, created_at
                FROM users
                ORDER BY name
            """)
            users = cursor.fetchall()
            conn.close()

            return [dict(user) for user in users]
        except Exception as e:
            print(f"사용자 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def create(username, password, name, role='user'):
        """새 사용자 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, name, role)
                VALUES (?, ?, ?, ?)
            """, (username, password, name, role))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except Exception as e:
            print(f"사용자 생성 중 오류: {str(e)}")
            return None

    @staticmethod
    def update_password(user_id, new_password):
        """비밀번호 변경"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET password = ? WHERE id = ?
            """, (new_password, user_id))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"비밀번호 변경 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(user_id):
        """사용자 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"사용자 삭제 중 오류: {str(e)}")
            return False
