# models/communications.py
"""
커뮤니케이션 모델 - 사용자 간 메시지 및 이메일 로그
- Dual-mode 지원: 내부망(MySQL 직접) / 외부망(API 호출)
"""

from datetime import datetime


def _is_internal_mode():
    """내부망 모드 여부 확인"""
    try:
        from connection_manager import is_internal_mode
        return is_internal_mode()
    except:
        return True  # 기본값: 내부망


def _get_connection():
    """DB 연결 반환 (내부망 전용)"""
    from database import get_connection
    return get_connection()


def _get_api():
    """외부망용 API 클라이언트"""
    from api_client import api
    return api


class Message:
    """사용자 간 채팅 메시지"""

    @staticmethod
    def _ensure_tables():
        """필요한 테이블 생성 (MySQL) - 내부망 전용"""
        if not _is_internal_mode():
            return  # 외부망에서는 테이블 생성 불가
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 메시지 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    receiver_id INT,
                    message_type VARCHAR(50) DEFAULT 'chat',
                    subject VARCHAR(255),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_sender (sender_id),
                    INDEX idx_receiver (receiver_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 메시지 읽음 상태 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_reads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message_id INT NOT NULL,
                    user_id INT NOT NULL,
                    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_read (message_id, user_id),
                    INDEX idx_message (message_id),
                    INDEX idx_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 이메일 발송 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    schedule_id INT,
                    estimate_type VARCHAR(50),
                    sender_email VARCHAR(255),
                    to_emails TEXT,
                    cc_emails TEXT,
                    subject VARCHAR(500),
                    body TEXT,
                    attachment_name VARCHAR(255),
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_by INT,
                    client_name VARCHAR(255),
                    status VARCHAR(50) DEFAULT '정상',
                    received VARCHAR(10) DEFAULT '아니오',
                    received_at TIMESTAMP NULL,
                    INDEX idx_schedule (schedule_id),
                    INDEX idx_sent_at (sent_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 기존 테이블에 새 컬럼 추가 (없는 경우)
            try:
                cursor.execute("ALTER TABLE email_logs ADD COLUMN status VARCHAR(50) DEFAULT '정상'")
            except:
                pass
            try:
                cursor.execute("ALTER TABLE email_logs ADD COLUMN received VARCHAR(10) DEFAULT '아니오'")
            except:
                pass
            try:
                cursor.execute("ALTER TABLE email_logs ADD COLUMN received_at TIMESTAMP NULL")
            except:
                pass

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def send(sender_id, receiver_id, content, message_type='chat', subject=None):
        """메시지 전송 (Dual-mode)"""
        if _is_internal_mode():
            return Message._send_to_db(sender_id, receiver_id, content, message_type, subject)
        else:
            return Message._send_to_api(sender_id, receiver_id, content, message_type, subject)

    @staticmethod
    def _send_to_db(sender_id, receiver_id, content, message_type, subject):
        """내부망: DB에 메시지 저장"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message_type, subject, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (sender_id, receiver_id, message_type, subject, content))

            message_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return message_id
        except Exception as e:
            print(f"메시지 전송 오류: {e}")
            return None

    @staticmethod
    def _send_to_api(sender_id, receiver_id, content, message_type, subject):
        """외부망: API로 메시지 전송"""
        try:
            api = _get_api()
            return api.send_message(sender_id, receiver_id, content, message_type, subject)
        except Exception as e:
            print(f"메시지 전송 API 오류: {e}")
            return None

    @staticmethod
    def get_conversation(user1_id, user2_id, limit=100):
        """두 사용자 간의 대화 내역 조회 (Dual-mode)"""
        if _is_internal_mode():
            return Message._get_conversation_from_db(user1_id, user2_id, limit)
        else:
            return Message._get_conversation_from_api(user1_id, user2_id, limit)

    @staticmethod
    def _get_conversation_from_db(user1_id, user2_id, limit):
        """내부망: DB에서 대화 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.*,
                       s.name as sender_name,
                       r.name as receiver_name
                FROM messages m
                LEFT JOIN users s ON m.sender_id = s.id
                LEFT JOIN users r ON m.receiver_id = r.id
                WHERE (m.sender_id = %s AND m.receiver_id = %s)
                   OR (m.sender_id = %s AND m.receiver_id = %s)
                ORDER BY m.created_at ASC
                LIMIT %s
            """, (user1_id, user2_id, user2_id, user1_id, limit))

            messages = cursor.fetchall()
            conn.close()
            return [dict(m) for m in messages]
        except Exception as e:
            print(f"대화 조회 오류: {e}")
            return []

    @staticmethod
    def _get_conversation_from_api(user1_id, user2_id, limit):
        """외부망: API에서 대화 조회"""
        try:
            api = _get_api()
            return api.get_conversation(user1_id, user2_id, limit)
        except Exception as e:
            print(f"대화 조회 API 오류: {e}")
            return []

    @staticmethod
    def get_chat_partners(user_id):
        """대화 상대 목록 조회 (최근 메시지 순, Dual-mode)"""
        if _is_internal_mode():
            return Message._get_chat_partners_from_db(user_id)
        else:
            return Message._get_chat_partners_from_api(user_id)

    @staticmethod
    def _get_chat_partners_from_db(user_id):
        """내부망: DB에서 대화 상대 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    u.id as partner_id,
                    u.name as partner_name,
                    u.department as partner_department,
                    MAX(m.created_at) as last_message_time,
                    (SELECT content FROM messages m2
                     WHERE ((m2.sender_id = %s AND m2.receiver_id = u.id)
                         OR (m2.sender_id = u.id AND m2.receiver_id = %s))
                     ORDER BY m2.created_at DESC LIMIT 1) as last_message
                FROM messages m
                JOIN users u ON u.id = CASE
                    WHEN m.sender_id = %s THEN m.receiver_id
                    ELSE m.sender_id
                END
                WHERE (m.sender_id = %s OR m.receiver_id = %s)
                  AND u.id != %s
                GROUP BY u.id, u.name, u.department
                ORDER BY last_message_time DESC
            """, (user_id, user_id, user_id, user_id, user_id, user_id))

            partners = cursor.fetchall()
            conn.close()
            return [dict(p) for p in partners]
        except Exception as e:
            print(f"대화 상대 목록 조회 오류: {e}")
            return []

    @staticmethod
    def _get_chat_partners_from_api(user_id):
        """외부망: API에서 대화 상대 조회"""
        try:
            api = _get_api()
            return api.get_chat_partners(user_id)
        except Exception as e:
            print(f"대화 상대 목록 API 오류: {e}")
            return []

    @staticmethod
    def mark_as_read(message_id, user_id):
        """메시지 읽음 처리 (Dual-mode)"""
        if _is_internal_mode():
            return Message._mark_as_read_to_db(message_id, user_id)
        else:
            return Message._mark_as_read_to_api(message_id, user_id)

    @staticmethod
    def _mark_as_read_to_db(message_id, user_id):
        """내부망: DB에서 읽음 처리"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT IGNORE INTO message_reads (message_id, user_id)
                VALUES (%s, %s)
            """, (message_id, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"읽음 처리 오류: {e}")
            return False

    @staticmethod
    def _mark_as_read_to_api(message_id, user_id):
        """외부망: API로 읽음 처리"""
        try:
            api = _get_api()
            return api.mark_message_read(message_id, user_id)
        except Exception as e:
            print(f"읽음 처리 API 오류: {e}")
            return False

    @staticmethod
    def mark_conversation_as_read(user_id, partner_id):
        """특정 대화의 모든 메시지 읽음 처리 (Dual-mode)"""
        if _is_internal_mode():
            return Message._mark_conversation_as_read_to_db(user_id, partner_id)
        else:
            return Message._mark_conversation_as_read_to_api(user_id, partner_id)

    @staticmethod
    def _mark_conversation_as_read_to_db(user_id, partner_id):
        """내부망: DB에서 대화 읽음 처리"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            # 상대방이 보낸 메시지 중 안 읽은 것들 조회
            cursor.execute("""
                SELECT id FROM messages
                WHERE sender_id = %s AND receiver_id = %s
                AND id NOT IN (SELECT message_id FROM message_reads WHERE user_id = %s)
            """, (partner_id, user_id, user_id))

            unread_ids = [row['id'] for row in cursor.fetchall()]

            # 읽음 처리
            for msg_id in unread_ids:
                cursor.execute("""
                    INSERT IGNORE INTO message_reads (message_id, user_id)
                    VALUES (%s, %s)
                """, (msg_id, user_id))

            conn.commit()
            conn.close()
            return len(unread_ids)
        except Exception as e:
            print(f"대화 읽음 처리 오류: {e}")
            return 0

    @staticmethod
    def _mark_conversation_as_read_to_api(user_id, partner_id):
        """외부망: API로 대화 읽음 처리"""
        try:
            api = _get_api()
            return api.mark_conversation_read(user_id, partner_id)
        except Exception as e:
            print(f"대화 읽음 처리 API 오류: {e}")
            return 0

    @staticmethod
    def get_unread_count(user_id):
        """읽지 않은 메시지 수 (Dual-mode)"""
        if _is_internal_mode():
            return Message._get_unread_count_from_db(user_id)
        else:
            return Message._get_unread_count_from_api(user_id)

    @staticmethod
    def _get_unread_count_from_db(user_id):
        """내부망: DB에서 미읽음 수 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages m
                WHERE m.receiver_id = %s
                AND m.id NOT IN (SELECT message_id FROM message_reads WHERE user_id = %s)
            """, (user_id, user_id))

            result = cursor.fetchone()
            conn.close()
            return result['count'] if result else 0
        except Exception as e:
            print(f"미읽음 수 조회 오류: {e}")
            return 0

    @staticmethod
    def _get_unread_count_from_api(user_id):
        """외부망: API에서 미읽음 수 조회"""
        try:
            api = _get_api()
            return api.get_unread_count(user_id)
        except Exception as e:
            print(f"미읽음 수 API 오류: {e}")
            return 0

    @staticmethod
    def get_unread_by_partner(user_id):
        """상대별 읽지 않은 메시지 수 (Dual-mode)"""
        if _is_internal_mode():
            return Message._get_unread_by_partner_from_db(user_id)
        else:
            return Message._get_unread_by_partner_from_api(user_id)

    @staticmethod
    def _get_unread_by_partner_from_db(user_id):
        """내부망: DB에서 상대별 미읽음 수 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.sender_id as partner_id, COUNT(*) as unread_count
                FROM messages m
                WHERE m.receiver_id = %s
                AND m.id NOT IN (SELECT message_id FROM message_reads WHERE user_id = %s)
                GROUP BY m.sender_id
            """, (user_id, user_id))

            result = cursor.fetchall()
            conn.close()
            return {row['partner_id']: row['unread_count'] for row in result}
        except Exception as e:
            print(f"상대별 미읽음 수 조회 오류: {e}")
            return {}

    @staticmethod
    def _get_unread_by_partner_from_api(user_id):
        """외부망: API에서 상대별 미읽음 수 조회"""
        try:
            api = _get_api()
            return api.get_unread_by_partner(user_id)
        except Exception as e:
            print(f"상대별 미읽음 수 API 오류: {e}")
            return {}

    @staticmethod
    def delete_message(message_id, user_id):
        """메시지 삭제 (본인이 보낸 메시지만, Dual-mode)"""
        if _is_internal_mode():
            return Message._delete_message_from_db(message_id, user_id)
        else:
            return Message._delete_message_from_api(message_id, user_id)

    @staticmethod
    def _delete_message_from_db(message_id, user_id):
        """내부망: DB에서 메시지 삭제"""
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 읽음 상태도 함께 삭제
            cursor.execute("DELETE FROM message_reads WHERE message_id = %s", (message_id,))

            # 본인이 보낸 메시지만 삭제
            cursor.execute("""
                DELETE FROM messages WHERE id = %s AND sender_id = %s
            """, (message_id, user_id))

            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"메시지 삭제 오류: {e}")
            return False

    @staticmethod
    def _delete_message_from_api(message_id, user_id):
        """외부망: API로 메시지 삭제"""
        try:
            api = _get_api()
            return api.delete_message(message_id, user_id)
        except Exception as e:
            print(f"메시지 삭제 API 오류: {e}")
            return False

    @staticmethod
    def delete_conversation(user_id, partner_id):
        """두 사용자 간의 대화 전체 삭제 (Dual-mode)"""
        if _is_internal_mode():
            return Message._delete_conversation_from_db(user_id, partner_id)
        else:
            return Message._delete_conversation_from_api(user_id, partner_id)

    @staticmethod
    def _delete_conversation_from_db(user_id, partner_id):
        """내부망: DB에서 대화 삭제"""
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 해당 대화의 메시지 ID들 조회
            cursor.execute("""
                SELECT id FROM messages
                WHERE (sender_id = %s AND receiver_id = %s)
                   OR (sender_id = %s AND receiver_id = %s)
            """, (user_id, partner_id, partner_id, user_id))

            message_ids = [row['id'] for row in cursor.fetchall()]

            if message_ids:
                # 읽음 상태 삭제
                placeholders = ','.join(['%s'] * len(message_ids))
                cursor.execute(f"DELETE FROM message_reads WHERE message_id IN ({placeholders})", message_ids)

                # 메시지 삭제
                cursor.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", message_ids)

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
        except Exception as e:
            print(f"대화 삭제 오류: {e}")
            return 0

    @staticmethod
    def _delete_conversation_from_api(user_id, partner_id):
        """외부망: API로 대화 삭제"""
        try:
            api = _get_api()
            return api.delete_conversation(user_id, partner_id)
        except Exception as e:
            print(f"대화 삭제 API 오류: {e}")
            return 0


class EmailLog:
    """이메일 발송 로그"""

    @staticmethod
    def save(schedule_id, estimate_type, sender_email, to_emails, cc_emails,
             subject, body, attachment_name, sent_by=None, client_name=None):
        """이메일 발송 로그 저장 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._save_to_db(schedule_id, estimate_type, sender_email, to_emails,
                                        cc_emails, subject, body, attachment_name, sent_by, client_name)
        else:
            return EmailLog._save_to_api(schedule_id, estimate_type, sender_email, to_emails,
                                         cc_emails, subject, body, attachment_name, sent_by, client_name)

    @staticmethod
    def _save_to_db(schedule_id, estimate_type, sender_email, to_emails, cc_emails,
                    subject, body, attachment_name, sent_by, client_name):
        """내부망: DB에 이메일 로그 저장"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO email_logs
                (schedule_id, estimate_type, sender_email, to_emails, cc_emails,
                 subject, body, attachment_name, sent_by, client_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (schedule_id, estimate_type, sender_email, to_emails, cc_emails,
                  subject, body, attachment_name, sent_by, client_name))

            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            print(f"이메일 로그 저장 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _save_to_api(schedule_id, estimate_type, sender_email, to_emails, cc_emails,
                     subject, body, attachment_name, sent_by, client_name):
        """외부망: API로 이메일 로그 저장"""
        try:
            api = _get_api()
            return api.save_email_log(schedule_id, estimate_type, sender_email, to_emails,
                                      cc_emails, subject, body, attachment_name, sent_by, client_name)
        except Exception as e:
            print(f"이메일 로그 API 저장 오류: {e}")
            return None

    @staticmethod
    def get_all(limit=100, sent_by=None):
        """전체 이메일 로그 조회 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._get_all_from_db(limit, sent_by)
        else:
            return EmailLog._get_all_from_api(limit, sent_by)

    @staticmethod
    def _get_all_from_db(limit, sent_by):
        """내부망: DB에서 이메일 로그 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            if sent_by:
                cursor.execute("""
                    SELECT el.*, u.name as sent_by_name
                    FROM email_logs el
                    LEFT JOIN users u ON el.sent_by = u.id
                    WHERE el.sent_by = %s
                    ORDER BY el.sent_at DESC
                    LIMIT %s
                """, (sent_by, limit))
            else:
                cursor.execute("""
                    SELECT el.*, u.name as sent_by_name
                    FROM email_logs el
                    LEFT JOIN users u ON el.sent_by = u.id
                    ORDER BY el.sent_at DESC
                    LIMIT %s
                """, (limit,))

            logs = cursor.fetchall()
            conn.close()
            return [dict(log) for log in logs]
        except Exception as e:
            print(f"이메일 로그 조회 오류: {e}")
            return []

    @staticmethod
    def _get_all_from_api(limit, sent_by):
        """외부망: API에서 이메일 로그 조회"""
        try:
            api = _get_api()
            return api.get_email_logs(limit, sent_by)
        except Exception as e:
            print(f"이메일 로그 API 조회 오류: {e}")
            return []

    @staticmethod
    def get_by_schedule(schedule_id):
        """스케줄별 이메일 로그 조회 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._get_by_schedule_from_db(schedule_id)
        else:
            return EmailLog._get_by_schedule_from_api(schedule_id)

    @staticmethod
    def _get_by_schedule_from_db(schedule_id):
        """내부망: DB에서 스케줄별 이메일 로그 조회"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT el.*, u.name as sent_by_name
                FROM email_logs el
                LEFT JOIN users u ON el.sent_by = u.id
                WHERE el.schedule_id = %s
                ORDER BY el.sent_at DESC
            """, (schedule_id,))

            logs = cursor.fetchall()
            conn.close()
            return [dict(log) for log in logs]
        except Exception as e:
            print(f"스케줄별 이메일 로그 조회 오류: {e}")
            return []

    @staticmethod
    def _get_by_schedule_from_api(schedule_id):
        """외부망: API에서 스케줄별 이메일 로그 조회"""
        try:
            api = _get_api()
            return api.get_email_logs_by_schedule(schedule_id)
        except Exception as e:
            print(f"스케줄별 이메일 로그 API 조회 오류: {e}")
            return []

    @staticmethod
    def get_by_id(log_id):
        """이메일 로그 상세 조회 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._get_by_id_from_db(log_id)
        else:
            return EmailLog._get_by_id_from_api(log_id)

    @staticmethod
    def _get_by_id_from_db(log_id):
        """내부망: DB에서 이메일 로그 상세 조회"""
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT el.*, u.name as sent_by_name
                FROM email_logs el
                LEFT JOIN users u ON el.sent_by = u.id
                WHERE el.id = %s
            """, (log_id,))

            log = cursor.fetchone()
            conn.close()
            return dict(log) if log else None
        except Exception as e:
            print(f"이메일 로그 상세 조회 오류: {e}")
            return None

    @staticmethod
    def _get_by_id_from_api(log_id):
        """외부망: API에서 이메일 로그 상세 조회"""
        try:
            api = _get_api()
            return api.get_email_log(log_id)
        except Exception as e:
            print(f"이메일 로그 상세 API 조회 오류: {e}")
            return None

    @staticmethod
    def search(keyword=None, start_date=None, end_date=None, limit=100, sent_by=None):
        """이메일 로그 검색 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._search_from_db(keyword, start_date, end_date, limit, sent_by)
        else:
            return EmailLog._search_from_api(keyword, start_date, end_date, limit, sent_by)

    @staticmethod
    def _search_from_db(keyword, start_date, end_date, limit, sent_by):
        """내부망: DB에서 이메일 로그 검색"""
        try:
            Message._ensure_tables()
            conn = _get_connection()
            cursor = conn.cursor()

            query = """
                SELECT el.*, u.name as sent_by_name
                FROM email_logs el
                LEFT JOIN users u ON el.sent_by = u.id
                WHERE 1=1
            """
            params = []

            if sent_by:
                query += " AND el.sent_by = %s"
                params.append(sent_by)

            if keyword:
                query += " AND (el.client_name LIKE %s OR el.to_emails LIKE %s OR el.subject LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

            if start_date:
                query += " AND DATE(el.sent_at) >= %s"
                params.append(start_date)

            if end_date:
                query += " AND DATE(el.sent_at) <= %s"
                params.append(end_date)

            query += " ORDER BY el.sent_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            logs = cursor.fetchall()
            conn.close()
            return [dict(log) for log in logs]
        except Exception as e:
            print(f"이메일 로그 검색 오류: {e}")
            return []

    @staticmethod
    def _search_from_api(keyword, start_date, end_date, limit, sent_by):
        """외부망: API에서 이메일 로그 검색"""
        try:
            api = _get_api()
            return api.search_email_logs(keyword, start_date, end_date, limit, sent_by)
        except Exception as e:
            print(f"이메일 로그 API 검색 오류: {e}")
            return []

    @staticmethod
    def delete(log_id, user_id=None):
        """이메일 로그 삭제 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._delete_from_db(log_id, user_id)
        else:
            return EmailLog._delete_from_api(log_id, user_id)

    @staticmethod
    def _delete_from_db(log_id, user_id):
        """내부망: DB에서 이메일 로그 삭제"""
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            if user_id:
                # 본인 기록만 삭제 가능
                cursor.execute("""
                    DELETE FROM email_logs WHERE id = %s AND sent_by = %s
                """, (log_id, user_id))
            else:
                cursor.execute("""
                    DELETE FROM email_logs WHERE id = %s
                """, (log_id,))

            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"이메일 로그 삭제 오류: {e}")
            return False

    @staticmethod
    def _delete_from_api(log_id, user_id):
        """외부망: API로 이메일 로그 삭제"""
        try:
            api = _get_api()
            return api.delete_email_log(log_id, user_id)
        except Exception as e:
            print(f"이메일 로그 API 삭제 오류: {e}")
            return False

    @staticmethod
    def update_status(log_id, status=None, received=None, received_at=None):
        """이메일 로그 상태 업데이트 (Dual-mode)"""
        if _is_internal_mode():
            return EmailLog._update_status_to_db(log_id, status, received, received_at)
        else:
            return EmailLog._update_status_to_api(log_id, status, received, received_at)

    @staticmethod
    def _update_status_to_db(log_id, status, received, received_at):
        """내부망: DB에서 이메일 로그 상태 업데이트"""
        try:
            conn = _get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if status is not None:
                updates.append("status = %s")
                params.append(status)

            if received is not None:
                updates.append("received = %s")
                params.append(received)

            if received_at is not None:
                updates.append("received_at = %s")
                params.append(received_at)

            if not updates:
                return False

            params.append(log_id)
            query = f"UPDATE email_logs SET {', '.join(updates)} WHERE id = %s"

            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"이메일 로그 상태 업데이트 오류: {e}")
            return False

    @staticmethod
    def _update_status_to_api(log_id, status, received, received_at):
        """외부망: API로 이메일 로그 상태 업데이트"""
        try:
            api = _get_api()
            return api.update_email_log_status(log_id, status, received, received_at)
        except Exception as e:
            print(f"이메일 로그 상태 API 업데이트 오류: {e}")
            return False
