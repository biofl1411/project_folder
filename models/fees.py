# models/fees.py
"""
수수료 관리 모델
내부망: DB 직접 연결
외부망: API 사용
"""

from connection_manager import is_internal_mode, connection_manager
import os

def _get_api():
    """API 클라이언트 반환"""
    return connection_manager.get_api_client()

def _get_connection():
    """DB 연결 반환 (내부망 전용)"""
    from database import get_connection
    return get_connection()

class Fee:
    @staticmethod
    def get_all():
        """모든 수수료 조회"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()

            # 열 정보 확인 (MySQL)
            cursor.execute("SHOW COLUMNS FROM fees")
            columns = [column['Field'] for column in cursor.fetchall()]

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
        else:
            api = _get_api()
            return api.get_fees()

    @staticmethod
    def get_by_item(test_item):
        """검사 항목으로 수수료 조회"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fees WHERE test_item = %s", (test_item,))
            fee = cursor.fetchone()
            conn.close()
            return fee
        else:
            api = _get_api()
            return api.get_fee_by_item(test_item)

    @staticmethod
    def create(test_item, food_category="", price=0, description="", display_order=100, sample_quantity=0):
        """새 수수료 생성"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO fees (test_item, food_category, price, description, display_order, sample_quantity) VALUES (%s, %s, %s, %s, %s, %s)",
                    (test_item, food_category, price, description, display_order, sample_quantity)
                )
            except Exception as e:
                # display_order 또는 sample_quantity 열이 없는 경우를 처리
                if "no such column" in str(e):
                    # 열 추가 시도
                    try:
                        cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
                    except Exception:
                        pass
                    try:
                        cursor.execute("ALTER TABLE fees ADD COLUMN sample_quantity INTEGER DEFAULT 0")
                    except Exception:
                        pass
                    # 다시 삽입 시도
                    cursor.execute(
                        "INSERT INTO fees (test_item, food_category, price, description, display_order, sample_quantity) VALUES (%s, %s, %s, %s, %s, %s)",
                        (test_item, food_category, price, description, display_order, sample_quantity)
                    )
                else:
                    # 다른 예외는 다시 발생시킴
                    raise
            conn.commit()
            fee_id = cursor.lastrowid
            conn.close()
            return fee_id
        else:
            api = _get_api()
            return api.create_fee(
                test_item=test_item,
                food_category=food_category,
                price=price,
                description=description,
                display_order=display_order,
                sample_quantity=sample_quantity
            )

    @staticmethod
    def update(fee_id, test_item, food_category="", price=0, description="", display_order=None, sample_quantity=None):
        """수수료 정보 수정"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE fees SET test_item = %s, food_category = %s, price = %s, description = %s, display_order = %s, sample_quantity = %s WHERE id = %s",
                    (test_item, food_category, price, description, display_order or 100, sample_quantity or 0, fee_id)
                )
            except Exception as e:
                # 열이 없는 경우를 처리
                if "no such column" in str(e):
                    # 열 추가 시도
                    try:
                        cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
                    except Exception:
                        pass
                    try:
                        cursor.execute("ALTER TABLE fees ADD COLUMN sample_quantity INTEGER DEFAULT 0")
                    except Exception:
                        pass
                    # 다시 업데이트 시도
                    cursor.execute(
                        "UPDATE fees SET test_item = %s, food_category = %s, price = %s, description = %s, display_order = %s, sample_quantity = %s WHERE id = %s",
                        (test_item, food_category, price, description, display_order or 100, sample_quantity or 0, fee_id)
                    )
                else:
                    # 다른 예외는 다시 발생시킴
                    raise
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount > 0
        else:
            api = _get_api()
            return api.update_fee(
                fee_id,
                test_item=test_item,
                food_category=food_category,
                price=price,
                description=description,
                display_order=display_order,
                sample_quantity=sample_quantity
            )

    @staticmethod
    def delete(fee_id):
        """수수료 삭제"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fees WHERE id = %s", (fee_id,))
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount > 0
        else:
            api = _get_api()
            return api.delete_fee(fee_id)

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

        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()

            total_price = 0
            for item in items_list:
                cursor.execute("SELECT price FROM fees WHERE test_item = %s", (item,))
                fee = cursor.fetchone()
                if fee:
                    total_price += fee['price']

            conn.close()
            return total_price
        else:
            api = _get_api()
            return api.calculate_fee(items_list)

    @staticmethod
    def import_from_excel(file_path):
        """Excel 파일에서 수수료 데이터 가져오기 (기존 데이터 삭제 후) - 내부망 전용"""
        if not is_internal_mode():
            return False, "엑셀 가져오기는 내부망에서만 가능합니다."

        try:
            import openpyxl

            if not os.path.exists(file_path):
                return False, f"파일이 존재하지 않습니다: {file_path}"

            wb = openpyxl.load_workbook(file_path)
            ws = wb.active

            conn = _get_connection()
            cursor = conn.cursor()

            # 기존 데이터 삭제
            cursor.execute("DELETE FROM fees")

            # display_order 열 확인 및 추가 (MySQL)
            cursor.execute("SHOW COLUMNS FROM fees")
            columns = [column['Field'] for column in cursor.fetchall()]

            if "display_order" not in columns:
                cursor.execute("ALTER TABLE fees ADD COLUMN display_order INTEGER DEFAULT 100")
            if "sample_quantity" not in columns:
                cursor.execute("ALTER TABLE fees ADD COLUMN sample_quantity INTEGER DEFAULT 0")

            # Excel 데이터 삽입 (첫 번째 행은 헤더이므로 2번째 행부터)
            # 열: 정렬순서, 식품 카테고리, 검사항목, 가격, 검체 수량(g)
            inserted_count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                display_order, food_category, test_item, price, sample_qty = row

                # 빈 행 스킵
                if not test_item:
                    continue

                # None 값 처리
                display_order = display_order if display_order is not None else 100
                food_category = food_category if food_category else ""
                price = price if price is not None else 0

                # sample_quantity 처리 (숫자가 아닌 경우 0으로 설정)
                if sample_qty is None:
                    sample_qty = 0
                elif isinstance(sample_qty, str):
                    # 숫자만 추출 시도
                    try:
                        sample_qty = int(''.join(filter(str.isdigit, sample_qty.split('\n')[0][:10])))
                    except (ValueError, TypeError):
                        sample_qty = 0
                else:
                    try:
                        sample_qty = int(sample_qty)
                    except (ValueError, TypeError):
                        sample_qty = 0

                cursor.execute("""
                    INSERT INTO fees (test_item, food_category, price, description, display_order, sample_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (test_item, food_category, price, "", display_order, sample_qty))
                inserted_count += 1

            conn.commit()
            conn.close()

            return True, f"{inserted_count}개의 수수료 데이터가 성공적으로 가져와졌습니다."
        except Exception as e:
            return False, f"가져오기 오류: {str(e)}"

    @staticmethod
    def delete_all():
        """모든 수수료 데이터 삭제 - 내부망 전용"""
        if not is_internal_mode():
            print("전체 삭제는 내부망에서만 가능합니다.")
            return 0

        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fees")
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        return deleted_count
