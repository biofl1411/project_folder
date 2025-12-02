# models/users.py
from database import get_connection
import datetime
import json

# 부서 목록
DEPARTMENTS = [
    '관리자',
    '이화학팀',
    '미생물팀',
    '분원',
    '고객관리팀',
    '고객지원팀',
    '마케팅팀',
    '지사'
]

# 권한 카테고리별 설명 (UI 그룹화용)
PERMISSION_CATEGORIES = {
    'schedule': '스케줄 작성',
    'client': '업체 관리',
    'food_type': '식품 유형 관리',
    'fee': '수수료 관리',
    'schedule_mgmt': '스케줄 관리',
    'system': '시스템'
}

# 세부 권한 설명 (카테고리별)
PERMISSION_LABELS = {
    # 스케줄 작성 TAB
    'schedule_create': '새 스케줄 작성',
    'schedule_edit': '수정하기',
    'schedule_delete': '선택 삭제',
    'schedule_status_change': '상태변경',
    'schedule_import_excel': '엑셀 불러오기',
    'schedule_export_excel': '엑셀 내보내기',
    # 업체관리
    'client_view_all': '모든 업체보기',
    'client_view_own': '해당 업체만 보기',
    'client_create': '신규업체등록',
    'client_edit': '업체 수정',
    'client_delete': '삭제',
    'client_import_excel': '엑셀 가져오기',
    'client_export_excel': '엑셀 내보내기',
    # 식품 유형 관리
    'food_type_create': '새 식품유형 등록',
    'food_type_edit': '수정',
    'food_type_delete': '삭제',
    'food_type_reset': '전체 초기화',
    'food_type_import_excel': '엑셀 가져오기',
    'food_type_update_excel': '엑셀 업데이트',
    'food_type_export_excel': '엑셀 내보내기',
    'food_type_db_info': 'DB정보',
    # 수수료 관리
    'fee_create': '새 수수료 등록',
    'fee_edit': '수정',
    'fee_delete': '삭제',
    'fee_import_excel': '엑셀 가져오기',
    'fee_export_excel': '엑셀 내보내기',
    # 스케줄 관리
    'schedule_mgmt_view_estimate': '견적서 보기',
    'schedule_mgmt_display_settings': '표시설정',
    'schedule_mgmt_select': '스케줄선택',
    'schedule_mgmt_add_item': '항목추가',
    'schedule_mgmt_delete_item': '항목삭제',
    'schedule_mgmt_save': '저장',
    # 시스템
    'user_manage': '사용자 관리',
    'settings_full': '설정 전체 접근',
}

# 카테고리별 권한 키 매핑
PERMISSION_BY_CATEGORY = {
    'schedule': ['schedule_create', 'schedule_edit', 'schedule_delete',
                 'schedule_status_change', 'schedule_import_excel', 'schedule_export_excel'],
    'client': ['client_view_all', 'client_view_own', 'client_create',
               'client_edit', 'client_delete', 'client_import_excel', 'client_export_excel'],
    'food_type': ['food_type_create', 'food_type_edit', 'food_type_delete',
                  'food_type_reset', 'food_type_import_excel', 'food_type_update_excel',
                  'food_type_export_excel', 'food_type_db_info'],
    'fee': ['fee_create', 'fee_edit', 'fee_delete', 'fee_import_excel', 'fee_export_excel'],
    'schedule_mgmt': ['schedule_mgmt_view_estimate', 'schedule_mgmt_display_settings',
                      'schedule_mgmt_select', 'schedule_mgmt_add_item',
                      'schedule_mgmt_delete_item', 'schedule_mgmt_save'],
    'system': ['user_manage', 'settings_full'],
}

# 모든 권한 키 가져오기 (기본값 False로)
def get_all_permission_keys():
    """모든 권한 키 목록 반환"""
    return list(PERMISSION_LABELS.keys())

def get_default_permissions(all_true=False):
    """기본 권한 딕셔너리 반환"""
    return {key: all_true for key in PERMISSION_LABELS.keys()}

# 기본 권한 설정 (관리자용 - 모든 권한)
DEFAULT_ADMIN_PERMISSIONS = get_default_permissions(all_true=True)

# 세컨드 비밀번호 (관리자 비밀번호 분실 시)
SECOND_PASSWORD = 'biofl1411*'

# 초기 비밀번호
DEFAULT_PASSWORD = 'bfl1411'


class User:
    @staticmethod
    def _ensure_columns():
        """필요한 컬럼이 없으면 추가"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]

            new_columns = {
                'department': 'TEXT DEFAULT ""',
                'permissions': 'TEXT DEFAULT "{}"',
            }

            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"users 테이블에 컬럼 추가됨: {col_name}")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"users 컬럼 추가 중 오류: {str(e)}")

    @staticmethod
    def authenticate(username, password):
        """사용자 인증"""
        try:
            User._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()

            # 세컨드 비밀번호 체크 (admin 계정에만 적용)
            if username == 'admin' and password == SECOND_PASSWORD:
                cursor.execute("""
                    SELECT id, username, password, name, role, department, permissions
                    FROM users
                    WHERE username = 'admin'
                """)
            else:
                cursor.execute("""
                    SELECT id, username, password, name, role, department, permissions
                    FROM users
                    WHERE username = ? AND password = ?
                """, (username, password))

            user = cursor.fetchone()

            if user:
                # 마지막 로그인 시간 업데이트
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
                conn.commit()

            conn.close()

            if user:
                # 권한 파싱
                permissions = {}
                if user['permissions']:
                    try:
                        permissions = json.loads(user['permissions'])
                    except:
                        pass

                # 관리자는 모든 권한
                department = user['department'] or ''
                if user['role'] == 'admin':
                    department = '관리자'
                    permissions = DEFAULT_ADMIN_PERMISSIONS.copy()
                elif not permissions:
                    # 권한이 없으면 기본값 (모두 False)
                    permissions = get_default_permissions(all_true=False)

                return {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'role': user['role'],
                    'department': department,
                    'permissions': permissions
                }
            return None
        except Exception as e:
            print(f"사용자 인증 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_id(user_id):
        """ID로 사용자 조회"""
        try:
            User._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, name, role, department, permissions, last_login, created_at
                FROM users
                WHERE id = ?
            """, (user_id,))
            user = cursor.fetchone()
            conn.close()

            if user:
                result = dict(user)
                if result.get('permissions'):
                    try:
                        result['permissions'] = json.loads(result['permissions'])
                    except:
                        result['permissions'] = {}
                else:
                    result['permissions'] = {}
                return result
            return None
        except Exception as e:
            print(f"사용자 조회 중 오류: {str(e)}")
            return None

    @staticmethod
    def get_all():
        """모든 사용자 조회"""
        try:
            User._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, name, role, department, permissions, last_login, created_at
                FROM users
                ORDER BY name
            """)
            users = cursor.fetchall()
            conn.close()

            result = []
            for user in users:
                user_dict = dict(user)
                if user_dict.get('permissions'):
                    try:
                        user_dict['permissions'] = json.loads(user_dict['permissions'])
                    except:
                        user_dict['permissions'] = {}
                else:
                    user_dict['permissions'] = {}
                result.append(user_dict)
            return result
        except Exception as e:
            print(f"사용자 목록 조회 중 오류: {str(e)}")
            return []

    @staticmethod
    def create(username, password, name, role='user', department='', permissions=None):
        """새 사용자 생성"""
        try:
            User._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()

            # 기본 권한 설정 (모두 False)
            if permissions is None:
                permissions = get_default_permissions(all_true=False)

            permissions_json = json.dumps(permissions or {}, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO users (username, password, name, role, department, permissions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password, name, role, department, permissions_json))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except Exception as e:
            print(f"사용자 생성 중 오류: {str(e)}")
            return None

    @staticmethod
    def update(user_id, name=None, department=None, permissions=None):
        """사용자 정보 업데이트"""
        try:
            User._ensure_columns()
            conn = get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)

            if department is not None:
                updates.append("department = ?")
                params.append(department)

            if permissions is not None:
                updates.append("permissions = ?")
                params.append(json.dumps(permissions, ensure_ascii=False))

            if updates:
                params.append(user_id)
                cursor.execute(f"""
                    UPDATE users SET {', '.join(updates)} WHERE id = ?
                """, params)
                conn.commit()

            conn.close()
            return True
        except Exception as e:
            print(f"사용자 업데이트 중 오류: {str(e)}")
            return False

    @staticmethod
    def update_password(user_id, new_password):
        """비밀번호 변경"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET password = ? WHERE id = ?
            """, (new_password, user_id))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"비밀번호 변경 중 오류: {str(e)}")
            return False

    @staticmethod
    def verify_password(user_id, password):
        """현재 비밀번호 확인"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM users WHERE id = ? AND password = ?
            """, (user_id, password))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"비밀번호 확인 중 오류: {str(e)}")
            return False

    @staticmethod
    def delete(user_id):
        """사용자 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"사용자 삭제 중 오류: {str(e)}")
            return False

    @staticmethod
    def has_permission(user, permission_key):
        """특정 권한이 있는지 확인"""
        if not user:
            return False

        # 관리자는 모든 권한
        if user.get('role') == 'admin':
            return True

        permissions = user.get('permissions', {})
        return permissions.get(permission_key, False)

    @staticmethod
    def reset_password(user_id):
        """비밀번호를 초기값으로 리셋"""
        return User.update_password(user_id, DEFAULT_PASSWORD)
