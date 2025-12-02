# models/storage.py
"""보관구 관리 모델"""

from database import get_connection
import datetime
import json


# 기본 보관구 위치 목록
STORAGE_LOCATIONS = [
    '휴게실 복도',
    '칭량실 앞',
    '미생물실 (배지제조실)',
    '배양실'
]

# 기본 온도 목록
DEFAULT_TEMPERATURES = [
    '-18°C', '-12°C', '-6°C', '5°C', '10°C', '15°C',
    '25°C', '30°C', '35°C', '45°C'
]


class Storage:
    """보관구 관리 클래스"""

    @staticmethod
    def _ensure_tables():
        """보관구 관련 테이블 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 보관구 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS storage_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    temperature TEXT NOT NULL,
                    capacity INTEGER DEFAULT 100,
                    current_usage INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 보관구 사용 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS storage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    storage_id INTEGER NOT NULL,
                    previous_usage INTEGER,
                    new_usage INTEGER,
                    change_reason TEXT,
                    changed_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (storage_id) REFERENCES storage_units(id)
                )
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"보관구 테이블 생성 중 오류: {str(e)}")

    @staticmethod
    def initialize_default_storage():
        """기본 보관구 데이터 초기화 (데이터가 없을 때만)"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            # 기존 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM storage_units")
            count = cursor.fetchone()[0]

            if count == 0:
                # 기본 보관구 데이터 삽입
                default_units = [
                    # 휴게실 복도
                    ('휴게실 복도', '15°C', 100, 0, '', 1),
                    ('휴게실 복도', '25°C', 100, 0, '', 2),
                    ('휴게실 복도', '35°C', 100, 0, '', 3),
                    ('휴게실 복도', '25°C', 100, 0, '', 4),
                    ('휴게실 복도', '5°C', 100, 0, '', 5),
                    ('휴게실 복도', '10°C', 100, 0, '', 6),
                    ('휴게실 복도', '45°C', 100, 0, '', 7),
                    ('휴게실 복도', '45°C', 100, 0, '', 8),
                    ('휴게실 복도', '35°C', 100, 0, '', 9),
                    # 칭량실 앞
                    ('칭량실 앞', '35°C', 100, 0, '', 10),
                    ('칭량실 앞', '45°C', 100, 0, '', 11),
                    ('칭량실 앞', '-6°C', 100, 0, '', 12),
                    ('칭량실 앞', '-12°C', 100, 0, '', 13),
                    ('칭량실 앞', '-18°C', 100, 0, '', 14),
                    # 미생물실
                    ('미생물실 (배지제조실)', '-18°C', 100, 0, '', 15),
                    # 배양실
                    ('배양실', '25°C', 100, 0, '', 16),
                    ('배양실', '30°C', 100, 0, '', 17),
                    ('배양실', '35°C', 100, 0, '', 18),
                ]

                cursor.executemany("""
                    INSERT INTO storage_units (location, temperature, capacity, current_usage, notes, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, default_units)

                conn.commit()
                print("기본 보관구 데이터 초기화 완료")

            conn.close()
        except Exception as e:
            print(f"기본 보관구 초기화 중 오류: {str(e)}")

    @staticmethod
    def get_all():
        """모든 보관구 조회"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, location, temperature, capacity, current_usage, notes, display_order
                FROM storage_units
                ORDER BY display_order, location, temperature
            """)

            units = cursor.fetchall()
            conn.close()

            return [dict(unit) for unit in units]
        except Exception as e:
            print(f"보관구 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_by_location(location):
        """위치별 보관구 조회"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, location, temperature, capacity, current_usage, notes, display_order
                FROM storage_units
                WHERE location = ?
                ORDER BY display_order
            """, (location,))

            units = cursor.fetchall()
            conn.close()

            return [dict(unit) for unit in units]
        except Exception as e:
            print(f"위치별 보관구 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_by_id(storage_id):
        """ID로 보관구 조회"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, location, temperature, capacity, current_usage, notes, display_order
                FROM storage_units
                WHERE id = ?
            """, (storage_id,))

            unit = cursor.fetchone()
            conn.close()

            return dict(unit) if unit else None
        except Exception as e:
            print(f"보관구 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def create(location, temperature, capacity=100, current_usage=0, notes=''):
        """보관구 생성"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            # display_order 최대값 조회
            cursor.execute("SELECT MAX(display_order) FROM storage_units")
            max_order = cursor.fetchone()[0] or 0

            cursor.execute("""
                INSERT INTO storage_units (location, temperature, capacity, current_usage, notes, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (location, temperature, capacity, current_usage, notes, max_order + 1))

            storage_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return storage_id
        except Exception as e:
            print(f"보관구 생성 중 오류: {str(e)}")
            return None

    @staticmethod
    def update(storage_id, location=None, temperature=None, capacity=None, notes=None):
        """보관구 정보 수정"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if location is not None:
                updates.append("location = ?")
                params.append(location)

            if temperature is not None:
                updates.append("temperature = ?")
                params.append(temperature)

            if capacity is not None:
                updates.append("capacity = ?")
                params.append(capacity)

            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(storage_id)

                cursor.execute(f"""
                    UPDATE storage_units
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)

                conn.commit()

            conn.close()
            return True
        except Exception as e:
            print(f"보관구 수정 중 오류: {str(e)}")
            return False

    @staticmethod
    def update_usage(storage_id, new_usage, changed_by='', change_reason=''):
        """보관구 사용량 업데이트 (로그 기록)"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            # 현재 사용량 조회
            cursor.execute("SELECT current_usage FROM storage_units WHERE id = ?", (storage_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False

            previous_usage = result[0]

            # 사용량 업데이트
            cursor.execute("""
                UPDATE storage_units
                SET current_usage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_usage, storage_id))

            # 로그 기록
            cursor.execute("""
                INSERT INTO storage_logs (storage_id, previous_usage, new_usage, change_reason, changed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (storage_id, previous_usage, new_usage, change_reason, changed_by))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"보관구 사용량 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(storage_id):
        """보관구 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 로그 먼저 삭제
            cursor.execute("DELETE FROM storage_logs WHERE storage_id = ?", (storage_id,))

            # 보관구 삭제
            cursor.execute("DELETE FROM storage_units WHERE id = ?", (storage_id,))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return success
        except Exception as e:
            print(f"보관구 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def get_logs(storage_id, limit=50):
        """보관구 사용 로그 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, storage_id, previous_usage, new_usage, change_reason, changed_by, created_at
                FROM storage_logs
                WHERE storage_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (storage_id, limit))

            logs = cursor.fetchall()
            conn.close()

            return [dict(log) for log in logs]
        except Exception as e:
            print(f"보관구 로그 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_summary_by_temperature():
        """온도별 보관구 요약 정보"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT temperature,
                       COUNT(*) as unit_count,
                       SUM(capacity) as total_capacity,
                       SUM(current_usage) as total_usage
                FROM storage_units
                GROUP BY temperature
                ORDER BY
                    CASE
                        WHEN temperature LIKE '-%' THEN CAST(REPLACE(REPLACE(temperature, '°C', ''), '-', '') AS INTEGER) * -1
                        ELSE CAST(REPLACE(temperature, '°C', '') AS INTEGER)
                    END
            """)

            summary = cursor.fetchall()
            conn.close()

            return [dict(s) for s in summary]
        except Exception as e:
            print(f"온도별 요약 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_locations():
        """등록된 위치 목록 조회"""
        try:
            Storage._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT location
                FROM storage_units
                ORDER BY MIN(display_order)
            """)

            locations = cursor.fetchall()
            conn.close()

            return [loc[0] for loc in locations]
        except Exception as e:
            print(f"위치 목록 조회 중 오류: {str(e)}")
            return STORAGE_LOCATIONS
