# models/settings.py
"""
애플리케이션 설정 관리 모델
Dual-mode 지원: 내부망(DB 직접 접근), 외부망(API)
"""

from database import get_connection


def _is_internal_mode():
    """내부망 모드 여부 확인"""
    try:
        from connection_manager import is_internal_mode
        return is_internal_mode()
    except:
        return True


def _get_api():
    """API 클라이언트 반환"""
    from api_client import get_api_client
    return get_api_client()


class Settings:
    """공용 설정 관리 클래스"""

    @staticmethod
    def get_all():
        """모든 설정 조회 (Dual-mode)

        Returns:
            dict: {key: value} 형식의 설정 딕셔너리
        """
        if _is_internal_mode():
            return Settings._get_all_from_db()
        else:
            return Settings._get_all_from_api()

    @staticmethod
    def _get_all_from_db():
        """내부망: DB에서 모든 설정 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT `key`, value FROM settings")
            settings = cursor.fetchall()
            conn.close()
            return {s['key']: s['value'] for s in settings}
        except Exception as e:
            print(f"설정 조회 오류: {str(e)}")
            return {}

    @staticmethod
    def _get_all_from_api():
        """외부망: API에서 모든 설정 조회"""
        try:
            api = _get_api()
            return api.get_settings()
        except Exception as e:
            print(f"설정 조회 오류 (API): {str(e)}")
            return {}

    @staticmethod
    def get(key, default=None):
        """특정 설정 조회 (Dual-mode)

        Args:
            key: 설정 키
            default: 기본값

        Returns:
            설정 값 또는 기본값
        """
        if _is_internal_mode():
            return Settings._get_from_db(key, default)
        else:
            return Settings._get_from_api(key, default)

    @staticmethod
    def _get_from_db(key, default=None):
        """내부망: DB에서 특정 설정 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result['value']
            return default
        except Exception as e:
            print(f"설정 조회 오류: {str(e)}")
            return default

    @staticmethod
    def _get_from_api(key, default=None):
        """외부망: API에서 특정 설정 조회"""
        try:
            api = _get_api()
            value = api.get_setting(key)
            return value if value is not None else default
        except Exception as e:
            print(f"설정 조회 오류 (API): {str(e)}")
            return default

    @staticmethod
    def set(key, value):
        """설정 저장/업데이트 (Dual-mode)

        Args:
            key: 설정 키
            value: 설정 값

        Returns:
            bool: 성공 여부
        """
        if _is_internal_mode():
            return Settings._set_to_db(key, value)
        else:
            return Settings._set_to_api(key, value)

    @staticmethod
    def _set_to_db(key, value):
        """내부망: DB에 설정 저장"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE `key` = %s
            """, (value, key))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (`key`, value) VALUES (%s, %s)
                """, (key, value))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"설정 저장 오류: {str(e)}")
            return False

    @staticmethod
    def _set_to_api(key, value):
        """외부망: API로 설정 저장"""
        try:
            api = _get_api()
            return api.update_setting(key, value)
        except Exception as e:
            print(f"설정 저장 오류 (API): {str(e)}")
            return False

    @staticmethod
    def set_batch(settings_dict):
        """여러 설정 일괄 저장 (Dual-mode)

        Args:
            settings_dict: {key: value} 형식의 설정 딕셔너리

        Returns:
            bool: 성공 여부
        """
        if _is_internal_mode():
            return Settings._set_batch_to_db(settings_dict)
        else:
            return Settings._set_batch_to_api(settings_dict)

    @staticmethod
    def _set_batch_to_db(settings_dict):
        """내부망: DB에 여러 설정 일괄 저장"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            for key, value in settings_dict.items():
                cursor.execute("""
                    UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE `key` = %s
                """, (value, key))

                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO settings (`key`, value) VALUES (%s, %s)
                    """, (key, value))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"설정 일괄 저장 오류: {str(e)}")
            return False

    @staticmethod
    def _set_batch_to_api(settings_dict):
        """외부망: API로 여러 설정 일괄 저장"""
        try:
            api = _get_api()
            return api.update_settings_batch(settings_dict)
        except Exception as e:
            print(f"설정 일괄 저장 오류 (API): {str(e)}")
            return False


class UserSettings:
    """사용자별 설정 관리 클래스"""

    @staticmethod
    def get_all(user_id):
        """사용자의 모든 설정 조회 (Dual-mode)

        Args:
            user_id: 사용자 ID

        Returns:
            dict: {key: value} 형식의 설정 딕셔너리
        """
        if _is_internal_mode():
            return UserSettings._get_all_from_db(user_id)
        else:
            return UserSettings._get_all_from_api(user_id)

    @staticmethod
    def _get_all_from_db(user_id):
        """내부망: DB에서 사용자 설정 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT `key`, value FROM user_settings WHERE user_id = %s", (user_id,))
            settings = cursor.fetchall()
            conn.close()
            return {s['key']: s['value'] for s in settings}
        except Exception as e:
            print(f"사용자 설정 조회 오류: {str(e)}")
            return {}

    @staticmethod
    def _get_all_from_api(user_id):
        """외부망: API에서 사용자 설정 조회"""
        try:
            api = _get_api()
            return api.get_user_settings(user_id)
        except Exception as e:
            print(f"사용자 설정 조회 오류 (API): {str(e)}")
            return {}

    @staticmethod
    def get(user_id, key, default=None):
        """사용자의 특정 설정 조회 (Dual-mode)

        Args:
            user_id: 사용자 ID
            key: 설정 키
            default: 기본값

        Returns:
            설정 값 또는 기본값
        """
        if _is_internal_mode():
            return UserSettings._get_from_db(user_id, key, default)
        else:
            return UserSettings._get_from_api(user_id, key, default)

    @staticmethod
    def _get_from_db(user_id, key, default=None):
        """내부망: DB에서 사용자 설정 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE user_id = %s AND `key` = %s", (user_id, key))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result['value']
            return default
        except Exception as e:
            print(f"사용자 설정 조회 오류: {str(e)}")
            return default

    @staticmethod
    def _get_from_api(user_id, key, default=None):
        """외부망: API에서 사용자 설정 조회"""
        try:
            api = _get_api()
            value = api.get_user_setting(user_id, key)
            return value if value is not None else default
        except Exception as e:
            print(f"사용자 설정 조회 오류 (API): {str(e)}")
            return default

    @staticmethod
    def set(user_id, key, value):
        """사용자 설정 저장/업데이트 (Dual-mode)

        Args:
            user_id: 사용자 ID
            key: 설정 키
            value: 설정 값

        Returns:
            bool: 성공 여부
        """
        if _is_internal_mode():
            return UserSettings._set_to_db(user_id, key, value)
        else:
            return UserSettings._set_to_api(user_id, key, value)

    @staticmethod
    def _set_to_db(user_id, key, value):
        """내부망: DB에 사용자 설정 저장"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE user_settings SET value = %s
                WHERE user_id = %s AND `key` = %s
            """, (value, user_id, key))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, `key`, value) VALUES (%s, %s, %s)
                """, (user_id, key, value))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"사용자 설정 저장 오류: {str(e)}")
            return False

    @staticmethod
    def _set_to_api(user_id, key, value):
        """외부망: API로 사용자 설정 저장"""
        try:
            api = _get_api()
            return api.update_user_setting(user_id, key, value)
        except Exception as e:
            print(f"사용자 설정 저장 오류 (API): {str(e)}")
            return False

    @staticmethod
    def set_batch(user_id, settings_dict):
        """사용자의 여러 설정 일괄 저장 (Dual-mode)

        Args:
            user_id: 사용자 ID
            settings_dict: {key: value} 형식의 설정 딕셔너리

        Returns:
            bool: 성공 여부
        """
        if _is_internal_mode():
            return UserSettings._set_batch_to_db(user_id, settings_dict)
        else:
            return UserSettings._set_batch_to_api(user_id, settings_dict)

    @staticmethod
    def _set_batch_to_db(user_id, settings_dict):
        """내부망: DB에 사용자 설정 일괄 저장"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            for key, value in settings_dict.items():
                # INSERT ON DUPLICATE KEY UPDATE 사용 (UPSERT)
                cursor.execute("""
                    INSERT INTO user_settings (user_id, `key`, value)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE value = VALUES(value)
                """, (user_id, key, value))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"사용자 설정 일괄 저장 오류: {str(e)}")
            return False

    @staticmethod
    def _set_batch_to_api(user_id, settings_dict):
        """외부망: API로 사용자 설정 일괄 저장"""
        try:
            api = _get_api()
            return api.update_user_settings_batch(user_id, settings_dict)
        except Exception as e:
            print(f"사용자 설정 일괄 저장 오류 (API): {str(e)}")
            return False
