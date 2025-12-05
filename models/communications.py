# models/communications.py
"""커뮤니케이션 모델 - 사용자 간 메시지 및 메일 공지"""

from database import get_connection
from datetime import datetime


class Message:
    """사용자 간 채팅 메시지"""

    @staticmethod
    def _ensure_tables():
        """필요한 테이블 생성"""
        try:
            conn = get_connection()
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
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 메시지 읽음 상태 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_reads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message_id INT NOT NULL,
                    user_id INT NOT NULL,
                    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_message_user (message_id, user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 메일 공지 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mail_notices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 메일 수신자 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mail_recipients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    mail_id INT NOT NULL,
                    user_id INT NOT NULL,
                    recipient_type VARCHAR(20) DEFAULT 'to',
                    read_at TIMESTAMP NULL,
                    FOREIGN KEY (mail_id) REFERENCES mail_notices(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"테이블 생성 오류: {e}")

    @staticmethod
    def send(sender_id, receiver_id, content, message_type='chat', subject=None):
        """메시지 전송"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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
    def get_conversation(user1_id, user2_id, limit=100):
        """두 사용자 간의 대화 내역 조회"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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
    def get_chat_partners(user_id):
        """대화 상대 목록 조회 (최근 메시지 순)"""
        try:
            Message._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT
                    CASE
                        WHEN m.sender_id = %s THEN m.receiver_id
                        ELSE m.sender_id
                    END as partner_id,
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
                WHERE m.sender_id = %s OR m.receiver_id = %s
                GROUP BY partner_id, u.name, u.department
                ORDER BY last_message_time DESC
            """, (user_id, user_id, user_id, user_id, user_id, user_id))

            partners = cursor.fetchall()
            conn.close()
            return [dict(p) for p in partners]
        except Exception as e:
            print(f"대화 상대 목록 조회 오류: {e}")
            return []

    @staticmethod
    def mark_as_read(message_id, user_id):
        """메시지 읽음 처리"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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
    def mark_conversation_as_read(user_id, partner_id):
        """특정 대화의 모든 메시지 읽음 처리"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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
    def get_unread_count(user_id):
        """읽지 않은 메시지 수"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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
    def get_unread_by_partner(user_id):
        """상대별 읽지 않은 메시지 수"""
        try:
            Message._ensure_tables()
            conn = get_connection()
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


class MailNotice:
    """메일 공지"""

    @staticmethod
    def send(sender_id, subject, content, to_user_ids, cc_user_ids=None):
        """메일 공지 전송"""
        try:
            Message._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            # 메일 공지 생성
            cursor.execute("""
                INSERT INTO mail_notices (sender_id, subject, content)
                VALUES (%s, %s, %s)
            """, (sender_id, subject, content))

            mail_id = cursor.lastrowid

            # 수신자 추가
            for user_id in to_user_ids:
                cursor.execute("""
                    INSERT INTO mail_recipients (mail_id, user_id, recipient_type)
                    VALUES (%s, %s, 'to')
                """, (mail_id, user_id))

            # 참조자 추가
            if cc_user_ids:
                for user_id in cc_user_ids:
                    cursor.execute("""
                        INSERT INTO mail_recipients (mail_id, user_id, recipient_type)
                        VALUES (%s, %s, 'cc')
                    """, (mail_id, user_id))

            conn.commit()
            conn.close()
            return mail_id
        except Exception as e:
            print(f"메일 공지 전송 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_received(user_id, limit=50):
        """받은 메일 공지 목록"""
        try:
            Message._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT mn.*,
                       u.name as sender_name,
                       mr.recipient_type,
                       mr.read_at
                FROM mail_notices mn
                JOIN mail_recipients mr ON mn.id = mr.mail_id
                JOIN users u ON mn.sender_id = u.id
                WHERE mr.user_id = %s
                ORDER BY mn.created_at DESC
                LIMIT %s
            """, (user_id, limit))

            mails = cursor.fetchall()
            conn.close()
            return [dict(m) for m in mails]
        except Exception as e:
            print(f"받은 메일 조회 오류: {e}")
            return []

    @staticmethod
    def get_sent(user_id, limit=50):
        """보낸 메일 공지 목록"""
        try:
            Message._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT mn.*,
                       GROUP_CONCAT(CASE WHEN mr.recipient_type = 'to' THEN u.name END) as to_names,
                       GROUP_CONCAT(CASE WHEN mr.recipient_type = 'cc' THEN u.name END) as cc_names
                FROM mail_notices mn
                LEFT JOIN mail_recipients mr ON mn.id = mr.mail_id
                LEFT JOIN users u ON mr.user_id = u.id
                WHERE mn.sender_id = %s
                GROUP BY mn.id
                ORDER BY mn.created_at DESC
                LIMIT %s
            """, (user_id, limit))

            mails = cursor.fetchall()
            conn.close()
            return [dict(m) for m in mails]
        except Exception as e:
            print(f"보낸 메일 조회 오류: {e}")
            return []

    @staticmethod
    def mark_as_read(mail_id, user_id):
        """메일 읽음 처리"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE mail_recipients
                SET read_at = CURRENT_TIMESTAMP
                WHERE mail_id = %s AND user_id = %s
            """, (mail_id, user_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"메일 읽음 처리 오류: {e}")
            return False

    @staticmethod
    def get_unread_count(user_id):
        """읽지 않은 메일 수"""
        try:
            Message._ensure_tables()
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count
                FROM mail_recipients
                WHERE user_id = %s AND read_at IS NULL
            """, (user_id,))

            result = cursor.fetchone()
            conn.close()
            return result['count'] if result else 0
        except Exception as e:
            print(f"미읽음 메일 수 조회 오류: {e}")
            return 0

    @staticmethod
    def get_by_id(mail_id):
        """메일 상세 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT mn.*, u.name as sender_name
                FROM mail_notices mn
                JOIN users u ON mn.sender_id = u.id
                WHERE mn.id = %s
            """, (mail_id,))

            mail = cursor.fetchone()

            if mail:
                mail = dict(mail)

                # 수신자 목록
                cursor.execute("""
                    SELECT u.id, u.name, mr.recipient_type, mr.read_at
                    FROM mail_recipients mr
                    JOIN users u ON mr.user_id = u.id
                    WHERE mr.mail_id = %s
                """, (mail_id,))

                recipients = cursor.fetchall()
                mail['recipients'] = [dict(r) for r in recipients]

            conn.close()
            return mail
        except Exception as e:
            print(f"메일 상세 조회 오류: {e}")
            return None
