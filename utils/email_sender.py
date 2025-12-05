#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
이메일 발송 유틸리티
SMTP를 사용하여 실제 이메일을 발송합니다.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header


class EmailSender:
    """이메일 발송 클래스"""

    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None, use_ssl=True):
        """
        SMTP 설정 초기화

        Args:
            smtp_server: SMTP 서버 주소
            smtp_port: SMTP 포트 (SSL: 465, TLS: 587)
            username: SMTP 사용자명 (이메일 주소)
            password: SMTP 비밀번호 (앱 비밀번호)
            use_ssl: SSL 사용 여부
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    @staticmethod
    def load_smtp_settings():
        """DB에서 SMTP 설정 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            settings = {}
            keys = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_ssl', 'smtp_sender_name']

            for key in keys:
                cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
                result = cursor.fetchone()
                if result:
                    settings[key] = result['value']

            conn.close()
            return settings
        except Exception as e:
            print(f"SMTP 설정 로드 오류: {e}")
            return {}

    @staticmethod
    def save_smtp_settings(smtp_server, smtp_port, smtp_username, smtp_password, smtp_use_ssl, smtp_sender_name):
        """SMTP 설정 저장"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            settings = [
                ('smtp_server', smtp_server, 'SMTP 서버 주소'),
                ('smtp_port', str(smtp_port), 'SMTP 포트'),
                ('smtp_username', smtp_username, 'SMTP 사용자명'),
                ('smtp_password', smtp_password, 'SMTP 비밀번호'),
                ('smtp_use_ssl', '1' if smtp_use_ssl else '0', 'SSL 사용 여부'),
                ('smtp_sender_name', smtp_sender_name, '발신자 이름'),
            ]

            for key, value, description in settings:
                cursor.execute("""
                    UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE `key` = %s
                """, (value, key))

                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO settings (`key`, value, description)
                        VALUES (%s, %s, %s)
                    """, (key, value, description))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"SMTP 설정 저장 오류: {e}")
            return False

    def send_email(self, to_emails, subject, body, cc_emails=None, attachments=None, sender_name=None):
        """
        이메일 발송

        Args:
            to_emails: 수신자 이메일 목록 (리스트)
            subject: 메일 제목
            body: 메일 본문
            cc_emails: 참조 이메일 목록 (리스트)
            attachments: 첨부파일 경로 목록 (리스트)
            sender_name: 발신자 이름

        Returns:
            (success: bool, message: str)
        """
        if not self.smtp_server or not self.username or not self.password:
            return False, "SMTP 설정이 완료되지 않았습니다."

        if not to_emails:
            return False, "수신자가 없습니다."

        try:
            # 메일 메시지 생성
            msg = MIMEMultipart()

            # 발신자 설정
            if sender_name:
                msg['From'] = f"{sender_name} <{self.username}>"
            else:
                msg['From'] = self.username

            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = Header(subject, 'utf-8')

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # 본문 추가
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 첨부파일 추가
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)

                            filename = os.path.basename(file_path)
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=('utf-8', '', filename)
                            )
                            msg.attach(part)

            # 모든 수신자 목록
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)

            # SMTP 서버 연결 및 발송
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.username, self.password)
            server.sendmail(self.username, all_recipients, msg.as_string())
            server.quit()

            return True, f"메일이 성공적으로 발송되었습니다. (수신자: {len(to_emails)}명)"

        except smtplib.SMTPAuthenticationError:
            return False, "SMTP 인증 실패: 사용자명 또는 비밀번호를 확인하세요."
        except smtplib.SMTPConnectError:
            return False, "SMTP 서버 연결 실패: 서버 주소와 포트를 확인하세요."
        except smtplib.SMTPException as e:
            return False, f"SMTP 오류: {str(e)}"
        except Exception as e:
            return False, f"이메일 발송 중 오류: {str(e)}"

    @staticmethod
    def test_connection(smtp_server, smtp_port, username, password, use_ssl):
        """SMTP 연결 테스트"""
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, int(smtp_port), timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
                server.starttls()

            server.login(username, password)
            server.quit()
            return True, "연결 성공!"
        except smtplib.SMTPAuthenticationError:
            return False, "인증 실패: 사용자명 또는 비밀번호를 확인하세요."
        except smtplib.SMTPConnectError:
            return False, "연결 실패: 서버 주소와 포트를 확인하세요."
        except Exception as e:
            return False, f"연결 테스트 실패: {str(e)}"
