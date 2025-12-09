# models/schedule_attachments.py
from database import get_connection
import os
import shutil
from datetime import datetime

class ScheduleAttachment:
    """스케줄 첨부파일 관리"""

    # 지원하는 파일 확장자
    ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.xlsx', '.xls',
                         '.doc', '.docx', '.hwp', '.hwpx']

    # 최대 파일 크기 (2MB)
    MAX_FILE_SIZE = 2 * 1024 * 1024

    # 첨부파일 저장 디렉토리
    UPLOAD_DIR = 'attachments'

    @staticmethod
    def _ensure_table():
        """테이블이 없으면 생성"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_attachments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    schedule_id INT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INT DEFAULT 0,
                    file_type VARCHAR(50),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"테이블 생성 중 오류: {str(e)}")

    @staticmethod
    def _get_upload_dir():
        """업로드 디렉토리 경로 반환 (없으면 생성)"""
        import sys
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        upload_dir = os.path.join(base_path, ScheduleAttachment.UPLOAD_DIR)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        return upload_dir

    @staticmethod
    def get_by_schedule(schedule_id):
        """스케줄 ID로 첨부파일 목록 조회"""
        ScheduleAttachment._ensure_table()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM schedule_attachments
                WHERE schedule_id = %s
                ORDER BY uploaded_at DESC
            ''', (schedule_id,))
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"첨부파일 조회 오류: {str(e)}")
            return []

    @staticmethod
    def add(schedule_id, source_file_path):
        """첨부파일 추가

        Args:
            schedule_id: 스케줄 ID
            source_file_path: 원본 파일 경로

        Returns:
            (success, message, attachment_id)
        """
        ScheduleAttachment._ensure_table()

        try:
            # 파일 존재 확인
            if not os.path.exists(source_file_path):
                return False, "파일을 찾을 수 없습니다.", None

            # 파일 정보
            file_name = os.path.basename(source_file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            file_size = os.path.getsize(source_file_path)

            # 확장자 확인
            if file_ext not in ScheduleAttachment.ALLOWED_EXTENSIONS:
                allowed = ', '.join(ScheduleAttachment.ALLOWED_EXTENSIONS)
                return False, f"지원하지 않는 파일 형식입니다.\n지원 형식: {allowed}", None

            # 파일 크기 확인
            if file_size > ScheduleAttachment.MAX_FILE_SIZE:
                max_mb = ScheduleAttachment.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"파일 크기가 {max_mb}MB를 초과합니다.", None

            # 저장 경로 생성 (schedule_id별 폴더)
            upload_dir = ScheduleAttachment._get_upload_dir()
            schedule_dir = os.path.join(upload_dir, str(schedule_id))
            if not os.path.exists(schedule_dir):
                os.makedirs(schedule_dir)

            # 중복 파일명 처리
            dest_file_name = file_name
            dest_path = os.path.join(schedule_dir, dest_file_name)
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(file_name)
                dest_file_name = f"{name}_{counter}{ext}"
                dest_path = os.path.join(schedule_dir, dest_file_name)
                counter += 1

            # 파일 복사
            shutil.copy2(source_file_path, dest_path)

            # 상대 경로로 저장
            relative_path = os.path.join(ScheduleAttachment.UPLOAD_DIR, str(schedule_id), dest_file_name)

            # DB에 저장
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO schedule_attachments
                (schedule_id, file_name, file_path, file_size, file_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', (schedule_id, dest_file_name, relative_path, file_size, file_ext))
            conn.commit()
            attachment_id = cursor.lastrowid
            conn.close()

            return True, "파일이 업로드되었습니다.", attachment_id

        except Exception as e:
            return False, f"파일 업로드 오류: {str(e)}", None

    @staticmethod
    def delete(attachment_id):
        """첨부파일 삭제

        Args:
            attachment_id: 첨부파일 ID

        Returns:
            (success, message)
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 파일 정보 조회
            cursor.execute('SELECT file_path FROM schedule_attachments WHERE id = %s', (attachment_id,))
            result = cursor.fetchone()

            if not result:
                conn.close()
                return False, "첨부파일을 찾을 수 없습니다."

            # 실제 파일 삭제
            import sys
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            file_path = os.path.join(base_path, result['file_path'])
            if os.path.exists(file_path):
                os.remove(file_path)

            # DB에서 삭제
            cursor.execute('DELETE FROM schedule_attachments WHERE id = %s', (attachment_id,))
            conn.commit()
            conn.close()

            return True, "첨부파일이 삭제되었습니다."

        except Exception as e:
            return False, f"첨부파일 삭제 오류: {str(e)}"

    @staticmethod
    def get_file_path(attachment_id):
        """첨부파일의 실제 경로 반환

        Args:
            attachment_id: 첨부파일 ID

        Returns:
            절대 경로 또는 None
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM schedule_attachments WHERE id = %s', (attachment_id,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            import sys
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            file_path = os.path.join(base_path, result['file_path'])

            if os.path.exists(file_path):
                return file_path
            return None

        except Exception as e:
            print(f"파일 경로 조회 오류: {str(e)}")
            return None

    @staticmethod
    def get_by_id(attachment_id):
        """ID로 첨부파일 정보 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM schedule_attachments WHERE id = %s', (attachment_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            print(f"첨부파일 조회 오류: {str(e)}")
            return None

    @staticmethod
    def format_file_size(size_bytes):
        """파일 크기를 읽기 쉬운 형식으로 변환"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
