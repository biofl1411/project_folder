# models/clients.py
from database import get_connection
import datetime

class Client:
    # 모든 필드 정의
    FIELDS = [
        'id', 'name', 'ceo', 'business_no', 'category', 'phone', 'fax',
        'contact_person', 'email', 'sales_rep', 'toll_free', 'zip_code',
        'address', 'notes', 'sales_business', 'sales_phone', 'sales_mobile',
        'sales_address', 'mobile', 'created_at'
    ]

    @staticmethod
    def create(name, ceo=None, business_no=None, category=None, phone=None, fax=None,
               contact_person=None, email=None, sales_rep=None, toll_free=None,
               zip_code=None, address=None, notes=None, sales_business=None,
               sales_phone=None, sales_mobile=None, sales_address=None, mobile=None):
        """새 업체 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, ceo, business_no, category, phone, fax,
                    contact_person, email, sales_rep, toll_free, zip_code, address,
                    notes, sales_business, sales_phone, sales_mobile, sales_address, mobile)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, ceo, business_no, category, phone, fax, contact_person, email,
                  sales_rep, toll_free, zip_code, address, notes, sales_business,
                  sales_phone, sales_mobile, sales_address, mobile))
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
                SELECT id, name, ceo, business_no, category, phone, fax,
                    contact_person, email, sales_rep, toll_free, zip_code,
                    address, notes, sales_business, sales_phone, sales_mobile,
                    sales_address, mobile, created_at
                FROM clients
                WHERE id = ?
            """, (client_id,))
            client = cursor.fetchone()
            conn.close()

            if client:
                return dict(client)
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
                SELECT id, name, ceo, business_no, category, phone, fax,
                    contact_person, email, sales_rep, toll_free, zip_code,
                    address, notes, sales_business, sales_phone, sales_mobile,
                    sales_address, mobile, created_at
                FROM clients
                ORDER BY name
            """)
            clients = cursor.fetchall()
            conn.close()

            return [dict(client) for client in clients]
        except Exception as e:
            print(f"업체 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def update(client_id, name, ceo=None, business_no=None, category=None, phone=None,
               fax=None, contact_person=None, email=None, sales_rep=None, toll_free=None,
               zip_code=None, address=None, notes=None, sales_business=None,
               sales_phone=None, sales_mobile=None, sales_address=None, mobile=None):
        """업체 정보 업데이트"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clients
                SET name = ?, ceo = ?, business_no = ?, category = ?, phone = ?,
                    fax = ?, contact_person = ?, email = ?, sales_rep = ?, toll_free = ?,
                    zip_code = ?, address = ?, notes = ?, sales_business = ?,
                    sales_phone = ?, sales_mobile = ?, sales_address = ?, mobile = ?
                WHERE id = ?
            """, (name, ceo, business_no, category, phone, fax, contact_person, email,
                  sales_rep, toll_free, zip_code, address, notes, sales_business,
                  sales_phone, sales_mobile, sales_address, mobile, client_id))
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
        """업체명, 담당자, CEO, 사업자번호로 검색"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, ceo, business_no, category, phone, fax,
                    contact_person, email, sales_rep, toll_free, zip_code,
                    address, notes, sales_business, sales_phone, sales_mobile,
                    sales_address, mobile, created_at
                FROM clients
                WHERE name LIKE ? OR contact_person LIKE ? OR ceo LIKE ? OR business_no LIKE ?
                ORDER BY name
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            clients = cursor.fetchall()
            conn.close()

            return [dict(client) for client in clients]
        except Exception as e:
            print(f"업체 검색 중 오류: {str(e)}")
            return []
