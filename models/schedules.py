# models/schedules.py
"""
스케줄 관리 모델
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

class Schedule:
    @staticmethod
    def _ensure_columns():
        """필요한 컬럼이 없으면 추가 (내부망 전용)"""
        if not is_internal_mode():
            return
        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM schedules")
            columns = [col['Field'] for col in cursor.fetchall()]

            # 필요한 컬럼 목록
            new_columns = {
                'estimate_date': 'TEXT',
                'expected_date': 'TEXT',
                'interim_report_date': 'TEXT',
                'supply_amount': 'INTEGER DEFAULT 0',
                'tax_amount': 'INTEGER DEFAULT 0',
                'total_amount': 'INTEGER DEFAULT 0',
                'is_urgent': 'INTEGER DEFAULT 0',
                'report_date': 'TEXT',
                'report1_date': 'TEXT',
                'report2_date': 'TEXT',
                'report3_date': 'TEXT',
                'interim1_round': 'INTEGER DEFAULT 0',
                'interim2_round': 'INTEGER DEFAULT 0',
                'interim3_round': 'INTEGER DEFAULT 0',
                'extend_period_days': 'INTEGER DEFAULT 0',
                'extend_period_months': 'INTEGER DEFAULT 0',
                'extend_period_years': 'INTEGER DEFAULT 0',
                'extend_experiment_days': 'INTEGER DEFAULT 0',
                'extend_rounds': 'INTEGER DEFAULT 0',
                # 1차 견적 필드 (최초 생성 시 고정)
                'first_item_detail': 'TEXT',
                'first_cost_per_test': 'INTEGER DEFAULT 0',
                'first_rounds_cost': 'INTEGER DEFAULT 0',
                'first_report_cost': 'INTEGER DEFAULT 0',
                'first_interim_cost': 'INTEGER DEFAULT 0',
                'first_formula_text': 'TEXT',
                'first_supply_amount': 'INTEGER DEFAULT 0',
                'first_tax_amount': 'INTEGER DEFAULT 0',
                'first_total_amount': 'INTEGER DEFAULT 0',
                # 중단 견적 필드 (중단 시점 저장)
                'suspend_item_detail': 'TEXT',
                'suspend_cost_per_test': 'INTEGER DEFAULT 0',
                'suspend_rounds_cost': 'INTEGER DEFAULT 0',
                'suspend_report_cost': 'INTEGER DEFAULT 0',
                'suspend_interim_cost': 'INTEGER DEFAULT 0',
                'suspend_formula_text': 'TEXT',
                'suspend_supply_amount': 'INTEGER DEFAULT 0',
                'suspend_tax_amount': 'INTEGER DEFAULT 0',
                'suspend_total_amount': 'INTEGER DEFAULT 0',
                # 연장 견적 필드 (연장 설정 시 저장)
                'extend_item_detail': 'TEXT',
                'extend_cost_per_test': 'INTEGER DEFAULT 0',
                'extend_rounds_cost': 'INTEGER DEFAULT 0',
                'extend_report_cost': 'INTEGER DEFAULT 0',
                'extend_interim_cost': 'INTEGER DEFAULT 0',
                'extend_formula_text': 'TEXT',
                'extend_supply_amount': 'INTEGER DEFAULT 0',
                'extend_tax_amount': 'INTEGER DEFAULT 0',
                'extend_total_amount': 'INTEGER DEFAULT 0'
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
            if is_internal_mode():
                Schedule._ensure_columns()
                conn = _get_connection()
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            else:
                api = _get_api()
                return api.create_schedule(
                    client_id=client_id, product_name=product_name, food_type_id=food_type_id,
                    test_method=test_method, storage_condition=storage_condition,
                    test_start_date=test_start_date, expected_date=expected_date,
                    interim_report_date=interim_report_date, test_period_days=test_period_days,
                    test_period_months=test_period_months, test_period_years=test_period_years,
                    sampling_count=sampling_count, report_interim=report_interim,
                    report_korean=report_korean, report_english=report_english,
                    extension_test=extension_test, custom_temperatures=custom_temperatures,
                    status=status, packaging_weight=packaging_weight, packaging_unit=packaging_unit,
                    estimate_date=estimate_date
                )
        except Exception as e:
            print(f"스케줄 생성 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            raise  # 예외를 다시 발생시켜 호출자에게 전달

    @staticmethod
    def get_by_id(schedule_id):
        """ID로 스케줄 조회"""
        try:
            if is_internal_mode():
                Schedule._ensure_columns()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, c.name as client_name, c.email as client_email
                    FROM schedules s
                    LEFT JOIN clients c ON s.client_id = c.id
                    WHERE s.id = %s
                """, (schedule_id,))
                schedule = cursor.fetchone()
                conn.close()

                if schedule:
                    return dict(schedule)
                return None
            else:
                api = _get_api()
                return api.get_schedule(schedule_id)
        except Exception as e:
            print(f"스케줄 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 스케줄 조회"""
        try:
            if is_internal_mode():
                Schedule._ensure_columns()
                conn = _get_connection()
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
            else:
                api = _get_api()
                return api.get_schedules()
        except Exception as e:
            print(f"스케줄 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def update_status(schedule_id, status):
        """스케줄 상태 업데이트"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET status = %s
                    WHERE id = %s
                """, (status, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            else:
                api = _get_api()
                return api.update_schedule_status(schedule_id, status)
        except Exception as e:
            print(f"스케줄 상태 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(schedule_id):
        """스케줄 삭제"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            else:
                api = _get_api()
                return api.delete_schedule(schedule_id)
        except Exception as e:
            print(f"스케줄 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def search(keyword):
        """스케줄 검색"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, c.name as client_name
                    FROM schedules s
                    LEFT JOIN clients c ON s.client_id = c.id
                    WHERE s.title LIKE %s OR c.name LIKE %s OR s.product_name LIKE %s
                    ORDER BY s.created_at DESC
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                schedules = cursor.fetchall()
                conn.close()

                return [dict(s) for s in schedules]
            else:
                api = _get_api()
                return api.search_schedules(keyword)
        except Exception as e:
            print(f"스케줄 검색 중 오류: {str(e)}")
            return []

    @staticmethod
    def update_memo(schedule_id, memo):
        """스케줄 메모 업데이트"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET memo = %s
                    WHERE id = %s
                """, (memo, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            else:
                api = _get_api()
                return api.update_schedule_memo(schedule_id, memo)
        except Exception as e:
            print(f"스케줄 메모 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def update(schedule_id, data):
        """스케줄 전체 업데이트"""
        try:
            if is_internal_mode():
                Schedule._ensure_columns()
                conn = _get_connection()
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
                        client_id = %s,
                        title = %s,
                        start_date = %s,
                        end_date = %s,
                        product_name = %s,
                        food_type_id = %s,
                        test_method = %s,
                        storage_condition = %s,
                        test_period_days = %s,
                        test_period_months = %s,
                        test_period_years = %s,
                        sampling_count = %s,
                        report_interim = %s,
                        report_korean = %s,
                        report_english = %s,
                        extension_test = %s,
                        custom_temperatures = %s,
                        packaging_weight = %s,
                        packaging_unit = %s,
                        estimate_date = %s,
                        expected_date = %s,
                        interim_report_date = %s,
                        is_urgent = %s,
                        report_date = %s,
                        report1_date = %s,
                        report2_date = %s,
                        report3_date = %s,
                        extend_period_days = %s,
                        extend_period_months = %s,
                        extend_period_years = %s,
                        extend_experiment_days = %s,
                        extend_rounds = %s
                    WHERE id = %s
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
                    data.get('is_urgent', 0),
                    data.get('report_date'),
                    data.get('report1_date'),
                    data.get('report2_date'),
                    data.get('report3_date'),
                    data.get('extend_period_days', 0),
                    data.get('extend_period_months', 0),
                    data.get('extend_period_years', 0),
                    data.get('extend_experiment_days', 0),
                    data.get('extend_rounds', 0),
                    schedule_id
                ))

                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                print(f"스케줄 업데이트 완료: ID {schedule_id}")
                return success
            else:
                api = _get_api()
                return api.update_schedule(schedule_id, data)
        except Exception as e:
            print(f"스케줄 업데이트 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def get_filtered(keyword=None, status=None, date_from=None, date_to=None):
        """필터링된 스케줄 조회"""
        try:
            if is_internal_mode():
                conn = _get_connection()
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
                    query += " AND (s.title LIKE %s OR c.name LIKE %s OR s.product_name LIKE %s)"
                    params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

                # 상태 필터
                if status:
                    query += " AND s.status = %s"
                    params.append(status)

                # 기간 필터
                if date_from:
                    query += " AND s.start_date >= %s"
                    params.append(date_from)

                if date_to:
                    query += " AND (s.end_date <= %s OR s.start_date <= %s)"
                    params.extend([date_to, date_to])

                query += " ORDER BY s.created_at DESC"

                cursor.execute(query, params)
                schedules = cursor.fetchall()
                conn.close()

                return [dict(s) for s in schedules]
            else:
                api = _get_api()
                return api.get_schedules(keyword=keyword, status=status, date_from=date_from, date_to=date_to)
        except Exception as e:
            print(f"스케줄 필터 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def update_amounts(schedule_id, supply_amount, tax_amount, total_amount):
        """스케줄 금액 업데이트"""
        if is_internal_mode():
            try:
                Schedule._ensure_columns()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET supply_amount = %s, tax_amount = %s, total_amount = %s
                    WHERE id = %s
                """, (supply_amount, tax_amount, total_amount, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            except Exception as e:
                print(f"스케줄 금액 업데이트 중 오류: {str(e)}")
                return False
        else:
            # 외부망: API 사용
            try:
                api = _get_api()
                return api.update_schedule(schedule_id, {
                    'supply_amount': supply_amount,
                    'tax_amount': tax_amount,
                    'total_amount': total_amount
                })
            except Exception as e:
                print(f"스케줄 금액 업데이트 중 오류 (API): {str(e)}")
                return False

    @staticmethod
    def save_first_estimate(schedule_id, item_detail, cost_per_test, rounds_cost,
                           report_cost, interim_cost, formula_text, supply_amount,
                           tax_amount, total_amount):
        """1차 견적 저장 (최초 생성 시만 저장, 이후 고정)"""
        if is_internal_mode():
            try:
                Schedule._ensure_columns()
                conn = _get_connection()
                cursor = conn.cursor()

                # 이미 1차 견적이 저장되어 있는지 확인
                cursor.execute("""
                    SELECT first_supply_amount FROM schedules WHERE id = %s
                """, (schedule_id,))
                result = cursor.fetchone()

                # 이미 저장된 값이 있으면 저장하지 않음 (고정)
                if result and result.get('first_supply_amount', 0) > 0:
                    conn.close()
                    return False

                cursor.execute("""
                    UPDATE schedules
                    SET first_item_detail = %s, first_cost_per_test = %s, first_rounds_cost = %s,
                        first_report_cost = %s, first_interim_cost = %s, first_formula_text = %s,
                        first_supply_amount = %s, first_tax_amount = %s, first_total_amount = %s
                    WHERE id = %s
                """, (item_detail, cost_per_test, rounds_cost, report_cost, interim_cost,
                      formula_text, supply_amount, tax_amount, total_amount, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            except Exception as e:
                print(f"1차 견적 저장 중 오류: {str(e)}")
                return False
        else:
            # 외부망: API 사용
            try:
                # 이미 저장된 값이 있는지 확인
                schedule = Schedule.get_by_id(schedule_id)
                if schedule and schedule.get('first_supply_amount', 0) > 0:
                    return False

                api = _get_api()
                return api.update_schedule(schedule_id, {
                    'first_item_detail': item_detail,
                    'first_cost_per_test': cost_per_test,
                    'first_rounds_cost': rounds_cost,
                    'first_report_cost': report_cost,
                    'first_interim_cost': interim_cost,
                    'first_formula_text': formula_text,
                    'first_supply_amount': supply_amount,
                    'first_tax_amount': tax_amount,
                    'first_total_amount': total_amount
                })
            except Exception as e:
                print(f"1차 견적 저장 중 오류 (API): {str(e)}")
                return False

    @staticmethod
    def save_suspend_estimate(schedule_id, item_detail, cost_per_test, rounds_cost,
                             report_cost, interim_cost, formula_text, supply_amount,
                             tax_amount, total_amount):
        """중단 견적 저장 (중단 시점에 저장)"""
        if is_internal_mode():
            try:
                Schedule._ensure_columns()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET suspend_item_detail = %s, suspend_cost_per_test = %s, suspend_rounds_cost = %s,
                        suspend_report_cost = %s, suspend_interim_cost = %s, suspend_formula_text = %s,
                        suspend_supply_amount = %s, suspend_tax_amount = %s, suspend_total_amount = %s
                    WHERE id = %s
                """, (item_detail, cost_per_test, rounds_cost, report_cost, interim_cost,
                      formula_text, supply_amount, tax_amount, total_amount, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            except Exception as e:
                print(f"중단 견적 저장 중 오류: {str(e)}")
                return False
        else:
            # 외부망: API 사용
            try:
                api = _get_api()
                return api.update_schedule(schedule_id, {
                    'suspend_item_detail': item_detail,
                    'suspend_cost_per_test': cost_per_test,
                    'suspend_rounds_cost': rounds_cost,
                    'suspend_report_cost': report_cost,
                    'suspend_interim_cost': interim_cost,
                    'suspend_formula_text': formula_text,
                    'suspend_supply_amount': supply_amount,
                    'suspend_tax_amount': tax_amount,
                    'suspend_total_amount': total_amount
                })
            except Exception as e:
                print(f"중단 견적 저장 중 오류 (API): {str(e)}")
                return False

    @staticmethod
    def save_extend_estimate(schedule_id, item_detail, cost_per_test, rounds_cost,
                            report_cost, interim_cost, formula_text, supply_amount,
                            tax_amount, total_amount):
        """연장 견적 저장 (연장 설정 시 저장)"""
        if is_internal_mode():
            try:
                Schedule._ensure_columns()
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE schedules
                    SET extend_item_detail = %s, extend_cost_per_test = %s, extend_rounds_cost = %s,
                        extend_report_cost = %s, extend_interim_cost = %s, extend_formula_text = %s,
                        extend_supply_amount = %s, extend_tax_amount = %s, extend_total_amount = %s
                    WHERE id = %s
                """, (item_detail, cost_per_test, rounds_cost, report_cost, interim_cost,
                      formula_text, supply_amount, tax_amount, total_amount, schedule_id))
                success = cursor.rowcount > 0
                conn.commit()
                conn.close()
                return success
            except Exception as e:
                print(f"연장 견적 저장 중 오류: {str(e)}")
                return False
        else:
            # 외부망: API 사용
            try:
                api = _get_api()
                return api.update_schedule(schedule_id, {
                    'extend_item_detail': item_detail,
                    'extend_cost_per_test': cost_per_test,
                    'extend_rounds_cost': rounds_cost,
                    'extend_report_cost': report_cost,
                    'extend_interim_cost': interim_cost,
                    'extend_formula_text': formula_text,
                    'extend_supply_amount': supply_amount,
                    'extend_tax_amount': tax_amount,
                    'extend_total_amount': total_amount
                })
            except Exception as e:
                print(f"연장 견적 저장 중 오류 (API): {str(e)}")
                return False
