#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
자주 사용하는 수신자 목록 모델
"""

from database import get_connection
import json


class FrequentRecipient:
    """자주 사용하는 수신자 목록 관리 클래스"""

    @staticmethod
    def _ensure_table():
        """테이블이 없으면 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frequent_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    recipient_ids TEXT NOT NULL,
                    cc_ids TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"frequent_recipients 테이블 생성 오류: {e}")

    @staticmethod
    def get_all(user_id):
        """사용자의 자주 사용하는 수신자 목록 조회"""
        try:
            FrequentRecipient._ensure_table()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, recipient_ids, cc_ids, created_at
                FROM frequent_recipients
                WHERE user_id = ?
                ORDER BY name
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()

            result = []
            for row in rows:
                item = dict(row)
                item['recipient_ids'] = json.loads(item['recipient_ids'] or '[]')
                item['cc_ids'] = json.loads(item['cc_ids'] or '[]')
                result.append(item)
            return result
        except Exception as e:
            print(f"자주 사용하는 수신자 목록 조회 오류: {e}")
            return []

    @staticmethod
    def get_by_id(recipient_list_id):
        """ID로 수신자 목록 조회"""
        try:
            FrequentRecipient._ensure_table()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, name, recipient_ids, cc_ids, created_at
                FROM frequent_recipients
                WHERE id = ?
            """, (recipient_list_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                item = dict(row)
                item['recipient_ids'] = json.loads(item['recipient_ids'] or '[]')
                item['cc_ids'] = json.loads(item['cc_ids'] or '[]')
                return item
            return None
        except Exception as e:
            print(f"수신자 목록 조회 오류: {e}")
            return None

    @staticmethod
    def create(user_id, name, recipient_ids, cc_ids=None):
        """새 수신자 목록 생성"""
        try:
            FrequentRecipient._ensure_table()
            conn = get_connection()
            cursor = conn.cursor()

            recipient_ids_json = json.dumps(recipient_ids or [], ensure_ascii=False)
            cc_ids_json = json.dumps(cc_ids or [], ensure_ascii=False)

            cursor.execute("""
                INSERT INTO frequent_recipients (user_id, name, recipient_ids, cc_ids)
                VALUES (?, ?, ?, ?)
            """, (user_id, name, recipient_ids_json, cc_ids_json))

            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return new_id
        except Exception as e:
            print(f"수신자 목록 생성 오류: {e}")
            return None

    @staticmethod
    def update(recipient_list_id, name=None, recipient_ids=None, cc_ids=None):
        """수신자 목록 수정"""
        try:
            FrequentRecipient._ensure_table()
            conn = get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)

            if recipient_ids is not None:
                updates.append("recipient_ids = ?")
                params.append(json.dumps(recipient_ids, ensure_ascii=False))

            if cc_ids is not None:
                updates.append("cc_ids = ?")
                params.append(json.dumps(cc_ids, ensure_ascii=False))

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(recipient_list_id)
                cursor.execute(f"""
                    UPDATE frequent_recipients
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                conn.commit()

            conn.close()
            return True
        except Exception as e:
            print(f"수신자 목록 수정 오류: {e}")
            return False

    @staticmethod
    def delete(recipient_list_id):
        """수신자 목록 삭제"""
        try:
            FrequentRecipient._ensure_table()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM frequent_recipients WHERE id = ?", (recipient_list_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"수신자 목록 삭제 오류: {e}")
            return False
