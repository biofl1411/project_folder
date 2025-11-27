# models/schedules.py
from database import get_connection
import datetime

class Schedule:
    @staticmethod
    def create(client_id, product_name, food_type_id=None, test_method=None,
               storage_condition=None, test_start_date=None, test_period_days=0,
               test_period_months=0, test_period_years=0, sampling_count=6,
               report_interim=False, report_korean=True, report_english=False,
               extension_test=False, custom_temperatures=None, status='pending'):
        """새 스케줄 생성"""
        try:
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
                    extension_test, custom_temperatures
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id, product_name, test_start_date, end_date, status,
                product_name, food_type_id, test_method, storage_condition,
                test_period_days, test_period_months, test_period_years,
                sampling_count, report_interim, report_korean, report_english,
                extension_test, custom_temperatures
            ))

            schedule_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return schedule_id
        except Exception as e:
            print(f"스케줄 생성 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_by_id(schedule_id):
        """ID로 스케줄 조회"""
        try:
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
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.name as client_name
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
