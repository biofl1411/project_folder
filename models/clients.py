# models/clients.py
"""
업체 관리 모델
내부망: DB 직접 연결
외부망: API 사용
"""

from connection_manager import is_internal_mode, connection_manager
import datetime

def _get_api():
    """API 클라이언트 반환"""
    return connection_manager.get_api_client()

def _get_connection():
    """DB 연결 반환 (내부망 전용)"""
    from database import get_connection
    return get_connection()

class Client:
    # 모든 필드 정의
    FIELDS = [
        'id', 'name', 'ceo', 'business_no', 'category', 'phone', 'fax',
        'contact_person', 'email', 'sales_rep', 'toll_free', 'zip_code',
        'address', 'detail_address', 'notes', 'sales_business', 'sales_phone', 'sales_mobile',
        'sales_address', 'mobile', 'created_at'
    ]

    @staticmethod
    def _ensure_detail_address_column():
        """detail_address 컬럼이 없으면 추가 (내부망 전용)"""
        if not is_internal_mode():
            return
        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM clients")
            columns = [col['Field'] for col in cursor.fetchall()]
            if 'detail_address' not in columns:
                cursor.execute("ALTER TABLE clients ADD COLUMN detail_address TEXT")
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"컬럼 추가 중 오류: {str(e)}")

    @staticmethod
    def create(name, ceo=None, business_no=None, category=None, phone=None, fax=None,
               contact_person=None, email=None, sales_rep=None, toll_free=None,
               zip_code=None, address=None, notes=None, sales_business=None,
               sales_phone=None, sales_mobile=None, sales_address=None, mobile=None,
               detail_address=None):
        """새 업체 생성"""
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clients (name, ceo, business_no, category, phone, fax,
                        contact_person, email, sales_rep, toll_free, zip_code, address,
                        detail_address, notes, sales_business, sales_phone, sales_mobile, sales_address, mobile)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, ceo, business_no, category, phone, fax, contact_person, email,
                      sales_rep, toll_free, zip_code, address, detail_address, notes, sales_business,
                      sales_phone, sales_mobile, sales_address, mobile))
                client_id = cursor.lastrowid
                conn.commit()
                conn.close()
                return client_id
            else:
                api = _get_api()
                return api.create_client(
                    name=name, ceo=ceo, business_no=business_no, category=category,
                    phone=phone, fax=fax, contact_person=contact_person, email=email,
                    sales_rep=sales_rep, toll_free=toll_free, zip_code=zip_code,
                    address=address, detail_address=detail_address, notes=notes,
                    sales_business=sales_business, sales_phone=sales_phone,
                    sales_mobile=sales_mobile, sales_address=sales_address, mobile=mobile
                )
        except Exception as e:
            print(f"업체 생성 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_id(client_id):
        """ID로 업체 조회"""
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, ceo, business_no, category, phone, fax,
                        contact_person, email, sales_rep, toll_free, zip_code,
                        address, detail_address, notes, sales_business, sales_phone, sales_mobile,
                        sales_address, mobile, created_at
                    FROM clients
                    WHERE id = %s
                """, (client_id,))
                client = cursor.fetchone()
                conn.close()

                if client:
                    return dict(client)
                return None
            else:
                api = _get_api()
                return api.get_client(client_id)
        except Exception as e:
            print(f"업체 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 업체 조회"""
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, ceo, business_no, category, phone, fax,
                        contact_person, email, sales_rep, toll_free, zip_code,
                        address, detail_address, notes, sales_business, sales_phone, sales_mobile,
                        sales_address, mobile, created_at
                    FROM clients
                    ORDER BY name
                """)
                clients = cursor.fetchall()
                conn.close()

                return [dict(client) for client in clients]
            else:
                api = _get_api()
                return api.get_all_clients()
        except Exception as e:
            print(f"업체 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_total_count():
        """전체 업체 수 조회"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as cnt FROM clients")
                result = cursor.fetchone()
                conn.close()
                return result['cnt'] if result else 0
            else:
                api = _get_api()
                return api.get_clients_count()
        except Exception as e:
            print(f"업체 수 조회 중 오류: {str(e)}")
            return 0

    @staticmethod
    def get_paginated(page=1, per_page=100, search_keyword=None, search_field=None, sales_rep_filter=None):
        """페이지네이션 업체 조회

        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            search_keyword: 검색어
            search_field: 검색 필드
            sales_rep_filter: 영업담당 필터 (해당 업체만 보기용)
        """
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()

                offset = (page - 1) * per_page
                where_conditions = []
                params = []

                # 영업담당 필터 (해당 업체만 보기)
                if sales_rep_filter:
                    where_conditions.append("sales_rep = %s")
                    params.append(sales_rep_filter)

                # 검색 조건이 있는 경우
                if search_keyword:
                    if search_field == "고객/회사명":
                        where_conditions.append("name LIKE %s")
                        params.append(f"%{search_keyword}%")
                    elif search_field == "대표자":
                        where_conditions.append("ceo LIKE %s")
                        params.append(f"%{search_keyword}%")
                    elif search_field == "담당자":
                        where_conditions.append("contact_person LIKE %s")
                        params.append(f"%{search_keyword}%")
                    elif search_field == "사업자번호":
                        where_conditions.append("business_no LIKE %s")
                        params.append(f"%{search_keyword}%")
                    else:  # 전체
                        where_conditions.append("(name LIKE %s OR ceo LIKE %s OR contact_person LIKE %s OR business_no LIKE %s)")
                        params.extend([f"%{search_keyword}%", f"%{search_keyword}%", f"%{search_keyword}%", f"%{search_keyword}%"])

                # WHERE 절 생성
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)

                # 총 개수 조회
                cursor.execute(f"SELECT COUNT(*) as cnt FROM clients {where_clause}", params)
                result = cursor.fetchone()
                total_count = result['cnt'] if result else 0

                # 데이터 조회
                cursor.execute(f"""
                    SELECT id, name, ceo, business_no, category, phone, fax,
                        contact_person, email, sales_rep, toll_free, zip_code,
                        address, detail_address, notes, sales_business, sales_phone, sales_mobile,
                        sales_address, mobile, created_at
                    FROM clients
                    {where_clause}
                    ORDER BY name
                    LIMIT %s OFFSET %s
                """, params + [per_page, offset])

                clients = cursor.fetchall()
                conn.close()

                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

                return {
                    'clients': [dict(client) for client in clients],
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'current_page': page,
                    'per_page': per_page
                }
            else:
                api = _get_api()
                return api.get_clients(
                    page=page,
                    per_page=per_page,
                    search_keyword=search_keyword,
                    search_field=search_field,
                    sales_rep_filter=sales_rep_filter
                )
        except Exception as e:
            print(f"페이지네이션 업체 조회 중 오류: {str(e)}")
            return {'clients': [], 'total_count': 0, 'total_pages': 1, 'current_page': 1, 'per_page': per_page}

    @staticmethod
    def update(client_id, name, ceo=None, business_no=None, category=None, phone=None,
               fax=None, contact_person=None, email=None, sales_rep=None, toll_free=None,
               zip_code=None, address=None, notes=None, sales_business=None,
               sales_phone=None, sales_mobile=None, sales_address=None, mobile=None,
               detail_address=None):
        """업체 정보 업데이트"""
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE clients
                    SET name = %s, ceo = %s, business_no = %s, category = %s, phone = %s,
                        fax = %s, contact_person = %s, email = %s, sales_rep = %s, toll_free = %s,
                        zip_code = %s, address = %s, detail_address = %s, notes = %s, sales_business = %s,
                        sales_phone = %s, sales_mobile = %s, sales_address = %s, mobile = %s
                    WHERE id = %s
                """, (name, ceo, business_no, category, phone, fax, contact_person, email,
                      sales_rep, toll_free, zip_code, address, detail_address, notes, sales_business,
                      sales_phone, sales_mobile, sales_address, mobile, client_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            else:
                api = _get_api()
                return api.update_client(
                    client_id,
                    name=name, ceo=ceo, business_no=business_no, category=category,
                    phone=phone, fax=fax, contact_person=contact_person, email=email,
                    sales_rep=sales_rep, toll_free=toll_free, zip_code=zip_code,
                    address=address, detail_address=detail_address, notes=notes,
                    sales_business=sales_business, sales_phone=sales_phone,
                    sales_mobile=sales_mobile, sales_address=sales_address, mobile=mobile
                )
        except Exception as e:
            print(f"업체 정보 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(client_id):
        """업체 삭제"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            else:
                api = _get_api()
                return api.delete_client(client_id)
        except Exception as e:
            print(f"업체 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def search(keyword):
        """업체명, 담당자, CEO, 사업자번호로 검색"""
        try:
            if is_internal_mode():
                Client._ensure_detail_address_column()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, ceo, business_no, category, phone, fax,
                        contact_person, email, sales_rep, toll_free, zip_code,
                        address, detail_address, notes, sales_business, sales_phone, sales_mobile,
                        sales_address, mobile, created_at
                    FROM clients
                    WHERE name LIKE %s OR contact_person LIKE %s OR ceo LIKE %s OR business_no LIKE %s
                    ORDER BY name
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                clients = cursor.fetchall()
                conn.close()

                return [dict(client) for client in clients]
            else:
                api = _get_api()
                return api.search_clients(keyword)
        except Exception as e:
            print(f"업체 검색 중 오류: {str(e)}")
            return []
