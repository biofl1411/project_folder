# models/schedules.py
from database import get_connection
import datetime

class Schedule:
    @staticmethod
    def _ensure_columns():
        """필요한 컬럼이 없으면 추가"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(schedules)")
            columns = [col[1] for col in cursor.fetchall()]

            # 필요한 컬럼 목록
            new_columns = {
                'estimate_date': 'TEXT',
                'expected_date': 'TEXT',
                'interim_report_date': 'TEXT'
            }

            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE schedules ADD COLUMN {col_name} {col_type}")
                    print(f"컬럼 추가됨: {col_name}")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"컬럼 추가 중 오류: {str(e)}")

    @staticmethod
    def _ensure_estimate_date_column():
        """estimate_date 컬럼이 없으면 추가 (하위 호환성 유지)"""
        Schedule._ensure_columns()
    @staticmethod
    def create(client_id, product_name, food_type_id=None, test_method=None,
               storage_condition=None, test_start_date=None, expected_date=None,
               interim_report_date=None, test_period_days=0,
               test_period_months=0, test_period_years=0, sampling_count=6,
               report_interim=False, report_korean=True, report_english=False,
               extension_test=False, custom_temperatures=None, status='pending',
               packaging_weight=0, packaging_unit='g', estimate_date=None):
        """새 스케줄 생성"""
        try:
            Schedule._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()

            # 실험 종료일 계산
            if test_start_date:
                from datetime import datetime, timedelta
                start = datetime.strptime(test_start_date, '%Y-%m-%d')
                total_days = test_period_days + (test_period_months * 30) + (test_period_years * 365)
                end_date = (start + timedelta(days=total_days)).strftime('%Y-%m-%d')
            else:
                end_date = None

            cursor.execute("""
                INSERT INTO schedules (
                    client_id, title, start_date, end_date, status,
                    product_name, food_type_id, test_method, storage_condition,
                    test_period_days, test_period_months, test_period_years,
                    sampling_count, report_interim, report_korean, report_english,
                    extension_test, custom_temperatures, packaging_weight, packaging_unit,
                    estimate_date, expected_date, interim_report_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id, product_name, test_start_date, end_date, status,
                product_name, food_type_id, test_method, storage_condition,
                test_period_days, test_period_months, test_period_years,
                sampling_count, report_interim, report_korean, report_english,
                extension_test, custom_temperatures, packaging_weight, packaging_unit,
                estimate_date, expected_date, interim_report_date
            ))

            schedule_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return schedule_id
        except Exception as e:
            print(f"스케줄 생성 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            raise  # 예외를 다시 발생시켜 호출자에게 전달

    @staticmethod
    def get_by_id(schedule_id):
        """ID로 스케줄 조회"""
        try:
            Schedule._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.name as client_name
                FROM schedules s
                LEFT JOIN clients c ON s.client_id = c.id
                WHERE s.id = ?
            """, (schedule_id,))
            schedule = cursor.fetchone()
            conn.close()

            if schedule:
                return dict(schedule)
            return None
        except Exception as e:
            print(f"스케줄 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 스케줄 조회"""
        try:
            Schedule._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*,
                       c.name as client_name,
                       c.ceo as client_ceo,
                       c.contact_person as client_contact,
                       c.email as client_email,
                       c.phone as client_phone,
                       c.sales_rep as sales_rep
                FROM schedules s
                LEFT JOIN clients c ON s.client_id = c.id
                ORDER BY s.created_at DESC
            """)
            schedules = cursor.fetchall()
            conn.close()

            return [dict(s) for s in schedules]
        except Exception as e:
            print(f"스케줄 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def update_status(schedule_id, status):
        """스케줄 상태 업데이트"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedules
                SET status = ?
                WHERE id = ?
            """, (status, schedule_id))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"스케줄 상태 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(schedule_id):
        """스케줄 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"스케줄 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def search(keyword):
        """스케줄 검색"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.name as client_name
                FROM schedules s
                LEFT JOIN clients c ON s.client_id = c.id
                WHERE s.title LIKE ? OR c.name LIKE ? OR s.product_name LIKE ?
                ORDER BY s.created_at DESC
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            schedules = cursor.fetchall()
            conn.close()

            return [dict(s) for s in schedules]
        except Exception as e:
            print(f"스케줄 검색 중 오류: {str(e)}")
            return []

    @staticmethod
    def update_memo(schedule_id, memo):
        """스케줄 메모 업데이트"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedules
                SET memo = ?
                WHERE id = ?
            """, (memo, schedule_id))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"스케줄 메모 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def update(schedule_id, data):
        """스케줄 전체 업데이트"""
        try:
            Schedule._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()

            # 실험 종료일 계산
            start_date = data.get('start_date')
            end_date = None
            if start_date:
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                total_days = (data.get('test_period_days', 0) or 0) + \
                             ((data.get('test_period_months', 0) or 0) * 30) + \
                             ((data.get('test_period_years', 0) or 0) * 365)
                end_date = (start + timedelta(days=total_days)).strftime('%Y-%m-%d')

            cursor.execute("""
                UPDATE schedules SET
                    client_id = ?,
                    title = ?,
                    start_date = ?,
                    end_date = ?,
                    product_name = ?,
                    food_type_id = ?,
                    test_method = ?,
                    storage_condition = ?,
                    test_period_days = ?,
                    test_period_months = ?,
                    test_period_years = ?,
                    sampling_count = ?,
                    report_interim = ?,
                    report_korean = ?,
                    report_english = ?,
                    extension_test = ?,
                    custom_temperatures = ?,
                    packaging_weight = ?,
                    packaging_unit = ?,
                    estimate_date = ?,
                    expected_date = ?,
                    interim_report_date = ?
                WHERE id = ?
            """, (
                data.get('client_id'),
                data.get('product_name'),
                start_date,
                end_date,
                data.get('product_name'),
                data.get('food_type_id'),
                data.get('test_method'),
                data.get('storage_condition'),
                data.get('test_period_days', 0),
                data.get('test_period_months', 0),
                data.get('test_period_years', 0),
                data.get('sampling_count', 6),
                data.get('report_interim', 0),
                data.get('report_korean', 1),
                data.get('report_english', 0),
                data.get('extension_test', 0),
                data.get('custom_temperatures'),
                data.get('packaging_weight', 0),
                data.get('packaging_unit', 'g'),
                data.get('estimate_date'),
                data.get('expected_date'),
                data.get('interim_report_date'),
                schedule_id
            ))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            print(f"스케줄 업데이트 완료: ID {schedule_id}")
            return success
        except Exception as e:
            print(f"스케줄 업데이트 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def get_filtered(keyword=None, status=None, date_from=None, date_to=None):
        """필터링된 스케줄 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT s.*, c.name as client_name
                FROM schedules s
                LEFT JOIN clients c ON s.client_id = c.id
                WHERE 1=1
            """
            params = []

            # 키워드 검색
            if keyword:
                query += " AND (s.title LIKE ? OR c.name LIKE ? OR s.product_name LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

            # 상태 필터
            if status:
                query += " AND s.status = ?"
                params.append(status)

            # 기간 필터
            if date_from:
                query += " AND s.start_date >= ?"
                params.append(date_from)

            if date_to:
                query += " AND (s.end_date <= ? OR s.start_date <= ?)"
                params.extend([date_to, date_to])

            query += " ORDER BY s.created_at DESC"

            cursor.execute(query, params)
            schedules = cursor.fetchall()
            conn.close()

            return [dict(s) for s in schedules]
        except Exception as e:
            print(f"스케줄 필터 조회 중 오류: {str(e)}")
            return []
