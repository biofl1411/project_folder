# models/fees.py
from database import get_connection

class Fee:
    @staticmethod
    def get_all():
        """모든 수수료 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # 열 정보 확인
        cursor.execute("PRAGMA table_info(fees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # display_order 열이 있는지 확인
        if "display_order" in columns:
            cursor.execute("SELECT * FROM fees ORDER BY display_order, test_item")
        else:
            # display_order 열 추가
            try:
                cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
                conn.commit()
                # 기존 데이터에 기본값 설정
                cursor.execute("UPDATE fees SET display_order = 100")
                conn.commit()
                cursor.execute("SELECT * FROM fees ORDER BY display_order, test_item")
            except Exception:
                # 실패하면 기존 정렬 방식 사용
                cursor.execute("SELECT * FROM fees ORDER BY test_item")
        
        fees = cursor.fetchall()
        conn.close()
        return fees
    
    @staticmethod
    def get_by_item(test_item):
        """검사 항목으로 수수료 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fees WHERE test_item = ?", (test_item,))
        fee = cursor.fetchone()
        conn.close()
        return fee
    
    @staticmethod
    def create(test_item, food_category="", price=0, description="", display_order=100):
        """새 수수료 생성"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO fees (test_item, food_category, price, description, display_order) VALUES (?, ?, ?, ?, ?)",
                (test_item, food_category, price, description, display_order)
            )
        except Exception as e:
            # display_order 열이 없는 경우를 처리
            if "no such column: display_order" in str(e):
                # 열 추가 시도
                cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
                # 다시 삽입 시도
                cursor.execute(
                    "INSERT INTO fees (test_item, food_category, price, description, display_order) VALUES (?, ?, ?, ?, ?)",
                    (test_item, food_category, price, description, display_order)
                )
            else:
                # 다른 예외는 다시 발생시킴
                raise
        conn.commit()
        fee_id = cursor.lastrowid
        conn.close()
        return fee_id
    
    @staticmethod
    def update(fee_id, test_item, food_category="", price=0, description="", display_order=None):
        """수수료 정보 수정"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if display_order is not None:
                cursor.execute(
                    "UPDATE fees SET test_item = ?, food_category = ?, price = ?, description = ?, display_order = ? WHERE id = ?",
                    (test_item, food_category, price, description, display_order, fee_id)
                )
            else:
                cursor.execute(
                    "UPDATE fees SET test_item = ?, food_category = ?, price = ?, description = ? WHERE id = ?",
                    (test_item, food_category, price, description, fee_id)
                )
        except Exception as e:
            # display_order 열이 없는 경우를 처리
            if "no such column: display_order" in str(e) and display_order is not None:
                # 열 추가 시도
                cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
                # 다시 업데이트 시도
                cursor.execute(
                    "UPDATE fees SET test_item = ?, food_category = ?, price = ?, description = ?, display_order = ? WHERE id = ?",
                    (test_item, food_category, price, description, display_order, fee_id)
                )
            else:
                # 다른 예외는 다시 발생시킴
                raise
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(fee_id):
        """수수료 삭제"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fees WHERE id = ?", (fee_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def calculate_total_fee(test_items):
        """검사 항목 목록의 총 수수료 계산"""
        if not test_items:
            return 0
            
        # 쉼표로 구분된 문자열을 목록으로 변환
        if isinstance(test_items, str):
            items_list = [item.strip() for item in test_items.split(',')]
        else:
            items_list = test_items
            
        conn = get_connection()
        cursor = conn.cursor()
        
        total_price = 0
        for item in items_list:
            cursor.execute("SELECT price FROM fees WHERE test_item = ?", (item,))
            fee = cursor.fetchone()
            if fee:
                total_price += fee['price']
        
        conn.close()
        return total_price