# models/activity_log.py
"""
사용자 활동 로그 모델
- 관리자 이외의 사용자가 기록하는 모든 활동을 아이디별로 기록
"""
from database import get_connection
import datetime
import json


def _is_internal_mode():
    """내부망 모드 여부 확인"""
    try:
        from connection_manager import is_internal_mode
        return is_internal_mode()
    except:
        return True


# 활동 유형 정의
ACTION_TYPES = {
    # 스케줄 관련
    'schedule_create': '스케줄 생성',
    'schedule_edit': '스케줄 수정',
    'schedule_delete': '스케줄 삭제',
    'schedule_status_change': '스케줄 상태 변경',
    'schedule_item_add': '검사항목 추가',
    'schedule_item_delete': '검사항목 삭제',
    'schedule_date_edit': '실험일자 수정',
    'schedule_experiment_toggle': '실험 O/X 변경',

    # 업체 관련
    'client_create': '업체 등록',
    'client_edit': '업체 수정',
    'client_delete': '업체 삭제',

    # 식품유형 관련
    'food_type_create': '식품유형 등록',
    'food_type_edit': '식품유형 수정',
    'food_type_delete': '식품유형 삭제',

    # 수수료 관련
    'fee_create': '수수료 등록',
    'fee_edit': '수수료 수정',
    'fee_delete': '수수료 삭제',

    # 견적서 관련
    'estimate_create': '견적서 생성',
    'estimate_print': '견적서 인쇄',
    'estimate_pdf': '견적서 PDF 저장',
    'estimate_email': '견적서 이메일 전송',

    # 사용자 관련
    'user_login': '로그인',
    'user_logout': '로그아웃',
    'password_change': '비밀번호 변경',

    # 시스템
    'settings_change': '설정 변경',
    'data_import': '데이터 가져오기',
    'data_export': '데이터 내보내기',
}


class ActivityLog:
    @staticmethod
    def _ensure_table():
        """activity_logs 테이블이 없으면 생성"""
        if not _is_internal_mode():
            return  # 외부망에서는 테이블 생성 불필요
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                username VARCHAR(100) NOT NULL,
                user_name VARCHAR(100) NOT NULL,
                department VARCHAR(100),
                action_type VARCHAR(50) NOT NULL,
                action_name VARCHAR(100) NOT NULL,
                target_type VARCHAR(50),
                target_id INT,
                target_name VARCHAR(200),
                details TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

            # 인덱스 생성 (빠른 검색을 위해) - 이미 존재하면 무시
            try:
                cursor.execute('''
                CREATE INDEX idx_activity_logs_user_id ON activity_logs (user_id)
                ''')
            except:
                pass  # 인덱스가 이미 존재함

            try:
                cursor.execute('''
                CREATE INDEX idx_activity_logs_created_at ON activity_logs (created_at)
                ''')
            except:
                pass  # 인덱스가 이미 존재함

            try:
                cursor.execute('''
                CREATE INDEX idx_activity_logs_action_type ON activity_logs (action_type)
                ''')
            except:
                pass  # 인덱스가 이미 존재함

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"activity_logs 테이블 생성 중 오류: {str(e)}")

    @staticmethod
    def log(user, action_type, target_type=None, target_id=None, target_name=None, details=None):
        """
        사용자 활동 로그 기록

        Args:
            user: 현재 로그인한 사용자 정보 (dict)
            action_type: 활동 유형 (ACTION_TYPES 키)
            target_type: 대상 타입 (예: 'schedule', 'client', 'fee' 등)
            target_id: 대상 ID
            target_name: 대상 이름 (예: 업체명, 제품명 등)
            details: 추가 상세 정보 (dict 또는 문자열)
        """
        # 외부망에서는 로그 기록 생략
        if not _is_internal_mode():
            return None

        # 관리자는 로그 기록 제외 (선택사항 - 필요시 주석 처리)
        # if user and user.get('role') == 'admin':
        #     return None

        if not user:
            return None

        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            # 활동 유형 이름 가져오기
            action_name = ACTION_TYPES.get(action_type, action_type)

            # details가 dict이면 JSON으로 변환
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)

            cursor.execute('''
                INSERT INTO activity_logs
                (user_id, username, user_name, department, action_type, action_name,
                 target_type, target_id, target_name, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user.get('id'),
                user.get('username', ''),
                user.get('name', ''),
                user.get('department', ''),
                action_type,
                action_name,
                target_type,
                target_id,
                target_name,
                details
            ))

            log_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return log_id
        except Exception as e:
            print(f"활동 로그 기록 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_user(user_id, limit=100, offset=0):
        """특정 사용자의 활동 로그 조회"""
        if not _is_internal_mode():
            return []  # 외부망에서는 빈 목록 반환
        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM activity_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            ''', (user_id, limit, offset))

            logs = cursor.fetchall()
            conn.close()

            return [dict(log) for log in logs]
        except Exception as e:
            print(f"사용자별 활동 로그 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_all(limit=500, offset=0, filters=None):
        """
        모든 활동 로그 조회 (필터 지원)

        Args:
            limit: 조회 개수 제한
            offset: 시작 위치
            filters: 필터 조건 (dict)
                - user_id: 사용자 ID
                - username: 사용자 아이디
                - action_type: 활동 유형
                - date_from: 시작 날짜 (YYYY-MM-DD)
                - date_to: 종료 날짜 (YYYY-MM-DD)
                - target_type: 대상 타입
        """
        if not _is_internal_mode():
            return []  # 외부망에서는 빈 목록 반환
        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM activity_logs WHERE 1=1"
            params = []

            if filters:
                if filters.get('user_id'):
                    query += " AND user_id = %s"
                    params.append(filters['user_id'])

                if filters.get('username'):
                    query += " AND username LIKE %s"
                    params.append(f"%{filters['username']}%")

                if filters.get('action_type'):
                    query += " AND action_type = %s"
                    params.append(filters['action_type'])

                if filters.get('date_from'):
                    query += " AND date(created_at) >= %s"
                    params.append(filters['date_from'])

                if filters.get('date_to'):
                    query += " AND date(created_at) <= %s"
                    params.append(filters['date_to'])

                if filters.get('target_type'):
                    query += " AND target_type = %s"
                    params.append(filters['target_type'])

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            logs = cursor.fetchall()
            conn.close()

            return [dict(log) for log in logs]
        except Exception as e:
            print(f"활동 로그 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def get_count(filters=None):
        """활동 로그 총 개수 조회"""
        if not _is_internal_mode():
            return 0  # 외부망에서는 0 반환
        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            query = "SELECT COUNT(*) as count FROM activity_logs WHERE 1=1"
            params = []

            if filters:
                if filters.get('user_id'):
                    query += " AND user_id = %s"
                    params.append(filters['user_id'])

                if filters.get('username'):
                    query += " AND username LIKE %s"
                    params.append(f"%{filters['username']}%")

                if filters.get('action_type'):
                    query += " AND action_type = %s"
                    params.append(filters['action_type'])

                if filters.get('date_from'):
                    query += " AND date(created_at) >= %s"
                    params.append(filters['date_from'])

                if filters.get('date_to'):
                    query += " AND date(created_at) <= %s"
                    params.append(filters['date_to'])

            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()

            return result['count'] if result else 0
        except Exception as e:
            print(f"활동 로그 개수 조회 중 오류: {str(e)}")
            return 0

    @staticmethod
    def get_user_summary():
        """사용자별 활동 요약 (최근 활동 수)"""
        if not _is_internal_mode():
            return []  # 외부망에서는 빈 목록 반환
        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    user_id,
                    username,
                    user_name,
                    department,
                    COUNT(*) as total_actions,
                    MAX(created_at) as last_activity
                FROM activity_logs
                GROUP BY user_id
                ORDER BY last_activity DESC
            ''')

            result = cursor.fetchall()
            conn.close()

            return [dict(row) for row in result]
        except Exception as e:
            print(f"사용자별 활동 요약 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def delete_old_logs(days=365):
        """오래된 로그 삭제 (기본 1년)"""
        try:
            ActivityLog._ensure_table()

            conn = get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')

            cursor.execute('''
                DELETE FROM activity_logs
                WHERE date(created_at) < %s
            ''', (cutoff_date,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            return deleted_count
        except Exception as e:
            print(f"오래된 로그 삭제 중 오류: {str(e)}")
            return 0
