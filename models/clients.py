# models/client.py
from database import get_connection
import datetime

class Client:
    @staticmethod
    def create(name, ceo=None, phone=None, address=None, contact_person=None, mobile=None, sales_rep=None, notes=None):
        """새 업체 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, ceo, phone, address, contact_person, mobile, sales_rep, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, ceo, phone, address, contact_person, mobile, sales_rep, notes))
            client_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return client_id
        except Exception as e:
            print(f"업체 생성 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_id(client_id):
        """ID로 업체 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, ceo, phone, address, contact_person, mobile, sales_rep, notes, created_at
                FROM clients
                WHERE id = ?
            """, (client_id,))
            client = cursor.fetchone()
            conn.close()
            
            if client:
                return dict(client)  # sqlite3.Row를 딕셔너리로 변환
            return None
        except Exception as e:
            print(f"업체 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 업체 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, ceo, phone, address, contact_person, mobile, sales_rep, notes, created_at
                FROM clients
                ORDER BY name
            """)
            clients = cursor.fetchall()
            conn.close()
            
            return [dict(client) for client in clients]  # sqlite3.Row 목록을 딕셔너리 목록으로 변환
        except Exception as e:
            print(f"업체 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def update(client_id, name, ceo=None, phone=None, address=None, contact_person=None, mobile=None, sales_rep=None, notes=None):
        """업체 정보 업데이트"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clients
                SET name = ?, ceo = ?, phone = ?, address = ?, contact_person = ?, mobile = ?, sales_rep = ?, notes = ?
                WHERE id = ?
            """, (name, ceo, phone, address, contact_person, mobile, sales_rep, notes, client_id))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"업체 정보 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(client_id):
        """업체 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"업체 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def search(keyword):
        """업체명이나 담당자로 검색"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, ceo, phone, address, contact_person, mobile, sales_rep, notes, created_at
                FROM clients
                WHERE name LIKE ? OR contact_person LIKE ? OR ceo LIKE ?
                ORDER BY name
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            clients = cursor.fetchall()
            conn.close()
            
            return [dict(client) for client in clients]  # sqlite3.Row 목록을 딕셔너리 목록으로 변환
        except Exception as e:
            print(f"업체 검색 중 오류: {str(e)}")
            return []