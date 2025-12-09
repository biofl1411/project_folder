#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
커뮤니케이션 탭 - 사용자 간 채팅 및 이메일 발송 기록
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFrame, QSplitter, QListWidget, QListWidgetItem,
                           QTextEdit, QLineEdit, QTabWidget, QTableWidget,
                           QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
                           QComboBox, QMessageBox, QScrollArea, QCheckBox,
                           QGroupBox, QDialogButtonBox, QPlainTextEdit, QDateEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QFont, QBrush
import os


class CommunicationTab(QWidget):
    """커뮤니케이션 탭 (채팅 + 이메일 로그)"""

    # 새 메시지 알림 시그널 (unread_count)
    unread_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.current_chat_partner_id = None
        self.all_users = []

        # 자동 새로고침 타이머 (5초마다)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)

        self.initUI()

    def set_current_user(self, user):
        """현재 사용자 설정"""
        self.current_user = user
        self.load_users()
        self.load_chat_partners()
        self.load_email_logs()
        self.check_unread()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 메인 탭 위젯 (채팅 / 이메일 로그)
        self.main_tab = QTabWidget()
        self.main_tab.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; }
            QTabBar::tab { padding: 8px 20px; }
            QTabBar::tab:selected { background-color: #9b59b6; color: white; }
        """)

        # 채팅 탭
        chat_widget = QWidget()
        self.setup_chat_tab(chat_widget)
        self.main_tab.addTab(chat_widget, "채팅")

        # 이메일 발송 기록 탭
        email_log_widget = QWidget()
        self.setup_email_log_tab(email_log_widget)
        self.main_tab.addTab(email_log_widget, "이메일 발송 기록")

        layout.addWidget(self.main_tab)

    def setup_chat_tab(self, widget):
        """채팅 탭 설정"""
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Horizontal)

        # 좌측: 대화 상대 목록
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_frame.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # 새 대화 버튼
        new_chat_btn = QPushButton("+ 새 대화")
        new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        new_chat_btn.clicked.connect(self.start_new_chat)
        left_layout.addWidget(new_chat_btn)

        # 대화 상대 목록
        left_layout.addWidget(QLabel("대화 목록"))
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget::item { padding: 10px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background-color: #e1bee7; }
            QListWidget::item:hover { background-color: #f3e5f5; }
        """)
        self.chat_list.itemClicked.connect(self.on_chat_partner_selected)
        left_layout.addWidget(self.chat_list)

        splitter.addWidget(left_frame)

        # 우측: 채팅 영역
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # 채팅 상대 이름
        self.chat_partner_label = QLabel("대화 상대를 선택하세요")
        self.chat_partner_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        right_layout.addWidget(self.chat_partner_label)

        # 메시지 영역
        self.message_area = QTextEdit()
        self.message_area.setReadOnly(True)
        self.message_area.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        right_layout.addWidget(self.message_area)

        # 메시지 입력 영역
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("메시지를 입력하세요...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #9b59b6;
                border-radius: 5px;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton("전송")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        right_layout.addLayout(input_layout)

        splitter.addWidget(right_frame)
        splitter.setSizes([250, 600])

        layout.addWidget(splitter)

    def setup_email_log_tab(self, widget):
        """이메일 발송 기록 탭 설정"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 검색 영역
        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px; padding: 5px;")
        search_layout = QHBoxLayout(search_frame)

        # 검색어
        search_layout.addWidget(QLabel("검색:"))
        self.email_search_input = QLineEdit()
        self.email_search_input.setPlaceholderText("업체명, 수신자, 제목 검색...")
        self.email_search_input.setFixedWidth(200)
        self.email_search_input.returnPressed.connect(self.search_email_logs)
        search_layout.addWidget(self.email_search_input)

        # 기간 검색
        search_layout.addWidget(QLabel("기간:"))
        self.email_start_date = QDateEdit()
        self.email_start_date.setCalendarPopup(True)
        self.email_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.email_start_date.setFixedWidth(120)
        search_layout.addWidget(self.email_start_date)

        search_layout.addWidget(QLabel("~"))

        self.email_end_date = QDateEdit()
        self.email_end_date.setCalendarPopup(True)
        self.email_end_date.setDate(QDate.currentDate())
        self.email_end_date.setFixedWidth(120)
        search_layout.addWidget(self.email_end_date)

        # 검색 버튼
        search_btn = QPushButton("검색")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        search_btn.clicked.connect(self.search_email_logs)
        search_layout.addWidget(search_btn)

        # 새로고침 버튼
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_email_logs)
        search_layout.addWidget(refresh_btn)

        search_layout.addStretch()
        layout.addWidget(search_frame)

        # 이메일 로그 테이블
        self.email_log_table = QTableWidget(0, 9)
        self.email_log_table.setHorizontalHeaderLabels(["발송일시", "업체명", "견적유형", "수신자", "제목", "발송자", "상태", "수신여부", "수신일시"])
        self.email_log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.email_log_table.setColumnWidth(0, 140)
        self.email_log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.email_log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.email_log_table.setColumnWidth(2, 80)
        self.email_log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.email_log_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.email_log_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.email_log_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.email_log_table.setColumnWidth(6, 60)
        self.email_log_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.email_log_table.setColumnWidth(7, 70)
        self.email_log_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.email_log_table.setColumnWidth(8, 140)
        self.email_log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.email_log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.email_log_table.doubleClicked.connect(self.view_email_log_detail)
        self.email_log_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; }
            QHeaderView::section { background-color: #9b59b6; color: white; padding: 8px; }
        """)
        layout.addWidget(self.email_log_table)

        # 삭제 버튼
        delete_btn_layout = QHBoxLayout()
        delete_btn_layout.addStretch()
        self.delete_email_log_btn = QPushButton("선택 항목 삭제")
        self.delete_email_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_email_log_btn.clicked.connect(self.delete_email_log)
        delete_btn_layout.addWidget(self.delete_email_log_btn)
        layout.addLayout(delete_btn_layout)

    def load_users(self):
        """사용자 목록 로드"""
        try:
            from models.users import User
            self.all_users = User.get_all() or []
        except Exception as e:
            print(f"사용자 목록 로드 오류: {e}")
            self.all_users = []

    def load_chat_partners(self):
        """대화 상대 목록 로드"""
        if not self.current_user:
            return

        try:
            from models.communications import Message

            partners = Message.get_chat_partners(self.current_user['id'])
            unread_counts = Message.get_unread_by_partner(self.current_user['id'])

            self.chat_list.clear()

            for partner in partners:
                item = QListWidgetItem()
                partner_id = partner['partner_id']
                unread = unread_counts.get(partner_id, 0)

                # 표시 텍스트
                name = partner['partner_name'] or '알 수 없음'
                dept = partner['partner_department'] or ''
                last_msg = (partner['last_message'] or '')[:30]
                if len(partner['last_message'] or '') > 30:
                    last_msg += '...'

                display_text = f"{name}"
                if dept:
                    display_text += f" ({dept})"
                if unread > 0:
                    display_text += f" [{unread}]"
                display_text += f"\n{last_msg}"

                item.setText(display_text)
                item.setData(Qt.UserRole, partner_id)

                # 안 읽은 메시지가 있으면 굵게 표시
                if unread > 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(QBrush(QColor("#f3e5f5")))

                self.chat_list.addItem(item)

        except Exception as e:
            print(f"대화 상대 목록 로드 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_chat_partner_selected(self, item):
        """대화 상대 선택"""
        partner_id = item.data(Qt.UserRole)
        self.current_chat_partner_id = partner_id

        # 파트너 이름 표시
        partner_name = item.text().split('\n')[0].split(' [')[0]
        self.chat_partner_label.setText(partner_name)

        # 대화 내용 로드
        self.load_conversation()

        # 읽음 처리
        self.mark_conversation_read()

    def load_conversation(self):
        """대화 내용 로드"""
        if not self.current_user or not self.current_chat_partner_id:
            return

        try:
            from models.communications import Message

            messages = Message.get_conversation(
                self.current_user['id'],
                self.current_chat_partner_id
            )

            self.message_area.clear()

            for msg in messages:
                is_mine = msg['sender_id'] == self.current_user['id']
                sender_name = msg['sender_name'] or '알 수 없음'
                content = msg['content']
                created_at = msg['created_at']
                if created_at and not isinstance(created_at, str):
                    created_at = str(created_at)
                time_str = created_at[:16] if created_at else ''

                if is_mine:
                    html = f"""
                        <div style="text-align: right; margin: 5px 0;">
                            <span style="color: #666; font-size: 10px;">{time_str}</span><br>
                            <span style="background-color: #9b59b6; color: white; padding: 8px 12px;
                                         border-radius: 15px; display: inline-block; max-width: 70%;">
                                {content}
                            </span>
                        </div>
                    """
                else:
                    html = f"""
                        <div style="text-align: left; margin: 5px 0;">
                            <span style="color: #666; font-size: 10px;">{sender_name} - {time_str}</span><br>
                            <span style="background-color: #e0e0e0; color: black; padding: 8px 12px;
                                         border-radius: 15px; display: inline-block; max-width: 70%;">
                                {content}
                            </span>
                        </div>
                    """

                self.message_area.insertHtml(html)

            # 스크롤 맨 아래로
            scrollbar = self.message_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            print(f"대화 내용 로드 오류: {e}")

    def mark_conversation_read(self):
        """현재 대화 읽음 처리"""
        if not self.current_user or not self.current_chat_partner_id:
            return

        try:
            from models.communications import Message
            Message.mark_conversation_as_read(
                self.current_user['id'],
                self.current_chat_partner_id
            )
            self.load_chat_partners()
            self.check_unread()
        except Exception as e:
            print(f"읽음 처리 오류: {e}")

    def send_message(self):
        """메시지 전송"""
        if not self.current_user or not self.current_chat_partner_id:
            QMessageBox.warning(self, "알림", "대화 상대를 선택하세요.")
            return

        content = self.message_input.text().strip()
        if not content:
            return

        try:
            from models.communications import Message

            Message.send(
                self.current_user['id'],
                self.current_chat_partner_id,
                content
            )

            self.message_input.clear()
            self.load_conversation()
            self.load_chat_partners()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"메시지 전송 실패: {e}")

    def start_new_chat(self):
        """새 대화 시작"""
        if not self.current_user:
            return

        dialog = SelectUserDialog(self, self.all_users, self.current_user['id'])
        if dialog.exec_():
            selected_user = dialog.get_selected_user()
            if selected_user:
                self.current_chat_partner_id = selected_user['id']
                self.chat_partner_label.setText(f"{selected_user['name']} ({selected_user.get('department', '')})")
                self.load_conversation()

    def load_email_logs(self):
        """이메일 발송 기록 로드 (본인 계정만 표시)"""
        try:
            from models.communications import EmailLog

            # 본인 계정만 표시
            sent_by = self.current_user.get('id') if self.current_user else None
            logs = EmailLog.get_all(limit=100, sent_by=sent_by)
            self._populate_email_log_table(logs)

        except Exception as e:
            print(f"이메일 로그 로드 오류: {e}")

    def search_email_logs(self):
        """이메일 발송 기록 검색 (본인 계정만 표시)"""
        try:
            from models.communications import EmailLog

            keyword = self.email_search_input.text().strip()
            start_date = self.email_start_date.date().toString("yyyy-MM-dd")
            end_date = self.email_end_date.date().toString("yyyy-MM-dd")

            # 본인 계정만 표시
            sent_by = self.current_user.get('id') if self.current_user else None
            logs = EmailLog.search(
                keyword=keyword if keyword else None,
                start_date=start_date,
                end_date=end_date,
                limit=100,
                sent_by=sent_by
            )
            self._populate_email_log_table(logs)

        except Exception as e:
            print(f"이메일 로그 검색 오류: {e}")

    def delete_email_log(self):
        """선택한 이메일 로그 삭제"""
        selected_rows = self.email_log_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "알림", "삭제할 항목을 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "삭제 확인",
            f"선택한 {len(selected_rows)}개의 이메일 발송 기록을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from models.communications import EmailLog

                user_id = self.current_user.get('id') if self.current_user else None
                deleted_count = 0

                for index in selected_rows:
                    row = index.row()
                    log_id = self.email_log_table.item(row, 0).data(Qt.UserRole)
                    if EmailLog.delete(log_id, user_id):
                        deleted_count += 1

                if deleted_count > 0:
                    QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 기록이 삭제되었습니다.")
                    self.load_email_logs()
                else:
                    QMessageBox.warning(self, "삭제 실패", "삭제할 수 없는 기록입니다.")

            except Exception as e:
                QMessageBox.critical(self, "오류", f"삭제 중 오류가 발생했습니다:\n{str(e)}")

    def _populate_email_log_table(self, logs):
        """이메일 로그 테이블 채우기"""
        self.email_log_table.setRowCount(0)

        for log in logs:
            row = self.email_log_table.rowCount()
            self.email_log_table.insertRow(row)

            # 발송일시
            sent_at = log.get('sent_at', '')
            if sent_at and not isinstance(sent_at, str):
                sent_at = str(sent_at)
            sent_at_str = sent_at[:16] if sent_at else ''
            sent_item = QTableWidgetItem(sent_at_str)
            sent_item.setData(Qt.UserRole, log.get('id'))
            self.email_log_table.setItem(row, 0, sent_item)

            # 업체명
            self.email_log_table.setItem(row, 1, QTableWidgetItem(log.get('client_name', '') or ''))

            # 견적유형
            estimate_type = log.get('estimate_type', '') or ''
            type_map = {'first': '1차', 'suspend': '중단', 'extend': '연장'}
            estimate_type_str = type_map.get(estimate_type, estimate_type)
            self.email_log_table.setItem(row, 2, QTableWidgetItem(estimate_type_str))

            # 수신자
            to_emails = log.get('to_emails', '') or ''
            if len(to_emails) > 30:
                to_emails = to_emails[:30] + '...'
            self.email_log_table.setItem(row, 3, QTableWidgetItem(to_emails))

            # 제목
            subject = log.get('subject', '') or ''
            self.email_log_table.setItem(row, 4, QTableWidgetItem(subject))

            # 발송자
            sent_by_name = log.get('sent_by_name', '') or ''
            self.email_log_table.setItem(row, 5, QTableWidgetItem(sent_by_name))

            # 상태 (정상/반송)
            status = log.get('status', '정상') or '정상'
            status_item = QTableWidgetItem(status)
            if status == '반송':
                status_item.setForeground(Qt.red)
            self.email_log_table.setItem(row, 6, status_item)

            # 수신여부 (예/아니오)
            received = log.get('received', '아니오') or '아니오'
            received_item = QTableWidgetItem(received)
            if received == '예':
                received_item.setForeground(Qt.darkGreen)
            self.email_log_table.setItem(row, 7, received_item)

            # 수신일시
            received_at = log.get('received_at', '')
            if received_at and not isinstance(received_at, str):
                received_at = str(received_at)
            received_at_str = received_at[:16] if received_at else ''
            self.email_log_table.setItem(row, 8, QTableWidgetItem(received_at_str))

    def view_email_log_detail(self, index):
        """이메일 로그 상세 보기"""
        row = index.row()
        log_id = self.email_log_table.item(row, 0).data(Qt.UserRole)

        try:
            from models.communications import EmailLog
            log = EmailLog.get_by_id(log_id)
            if log:
                dialog = ViewEmailLogDialog(self, log)
                dialog.exec_()
        except Exception as e:
            print(f"이메일 로그 상세 조회 오류: {e}")

    def check_unread(self):
        """읽지 않은 메시지 확인"""
        if not self.current_user:
            return

        try:
            from models.communications import Message

            msg_unread = Message.get_unread_count(self.current_user['id'])
            self.unread_changed.emit(msg_unread)

        except Exception as e:
            print(f"미읽음 확인 오류: {e}")

    def refresh_data(self):
        """데이터 자동 새로고침"""
        if not self.current_user:
            return

        self.load_chat_partners()
        self.check_unread()

        # 현재 대화 중이면 대화 내용도 새로고침
        if self.current_chat_partner_id:
            self.load_conversation()


class SelectUserDialog(QDialog):
    """사용자 선택 다이얼로그"""

    def __init__(self, parent, users, exclude_user_id):
        super().__init__(parent)
        self.setWindowTitle("대화 상대 선택")
        self.setMinimumSize(300, 400)
        self.users = [u for u in users if u['id'] != exclude_user_id]
        self.selected_user = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 검색
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("이름 검색...")
        self.search_input.textChanged.connect(self.filter_users)
        layout.addWidget(self.search_input)

        # 사용자 목록
        self.user_list = QListWidget()
        self.user_list.itemDoubleClicked.connect(self.on_select)
        layout.addWidget(self.user_list)

        # 버튼
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("선택")
        select_btn.clicked.connect(self.on_select)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.populate_users()

    def populate_users(self, filter_text=''):
        self.user_list.clear()
        for user in self.users:
            name = user.get('name', '')
            dept = user.get('department', '')
            if filter_text and filter_text.lower() not in name.lower():
                continue

            item = QListWidgetItem(f"{name} ({dept})" if dept else name)
            item.setData(Qt.UserRole, user)
            self.user_list.addItem(item)

    def filter_users(self, text):
        self.populate_users(text)

    def on_select(self):
        item = self.user_list.currentItem()
        if item:
            self.selected_user = item.data(Qt.UserRole)
            self.accept()

    def get_selected_user(self):
        return self.selected_user


class ViewEmailLogDialog(QDialog):
    """이메일 로그 상세 보기 다이얼로그"""

    def __init__(self, parent, log):
        super().__init__(parent)
        self.setWindowTitle("이메일 발송 기록 상세")
        self.setMinimumSize(600, 550)
        self.log = log
        self.parent_widget = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 정보 영역
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        info_layout = QFormLayout(info_frame)

        # 발송일시
        sent_at = self.log.get('sent_at', '')
        if sent_at and not isinstance(sent_at, str):
            sent_at = str(sent_at)
        info_layout.addRow("발송일시:", QLabel(sent_at[:19] if sent_at else ''))

        # 업체명
        info_layout.addRow("업체명:", QLabel(self.log.get('client_name', '') or '-'))

        # 견적유형
        estimate_type = self.log.get('estimate_type', '') or ''
        type_map = {'first': '1차 견적', 'suspend': '중단 견적', 'extend': '연장 견적'}
        info_layout.addRow("견적유형:", QLabel(type_map.get(estimate_type, estimate_type)))

        # 발송자
        info_layout.addRow("발송자:", QLabel(self.log.get('sent_by_name', '') or '-'))

        # 수신자
        to_label = QLabel(self.log.get('to_emails', '') or '-')
        to_label.setWordWrap(True)
        info_layout.addRow("수신자(To):", to_label)

        # 참조
        cc_emails = self.log.get('cc_emails', '')
        if cc_emails:
            cc_label = QLabel(cc_emails)
            cc_label.setWordWrap(True)
            info_layout.addRow("참조(CC):", cc_label)

        # 제목
        subject_label = QLabel(self.log.get('subject', '') or '-')
        subject_label.setWordWrap(True)
        info_layout.addRow("제목:", subject_label)

        # 첨부파일
        attachment = self.log.get('attachment_name', '')
        if attachment:
            info_layout.addRow("첨부파일:", QLabel(attachment))

        layout.addWidget(info_frame)

        # 상태 정보 영역 (편집 가능)
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #e8f4e8; padding: 10px;")
        status_layout = QFormLayout(status_frame)

        # 상태 (정상/반송)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["정상", "반송"])
        current_status = self.log.get('status', '정상') or '정상'
        self.status_combo.setCurrentText(current_status)
        status_layout.addRow("상태:", self.status_combo)

        # 수신여부 (예/아니오)
        self.received_combo = QComboBox()
        self.received_combo.addItems(["아니오", "예"])
        current_received = self.log.get('received', '아니오') or '아니오'
        self.received_combo.setCurrentText(current_received)
        self.received_combo.currentTextChanged.connect(self.on_received_changed)
        status_layout.addRow("수신여부:", self.received_combo)

        # 수신일시
        received_at_layout = QHBoxLayout()
        self.received_at_label = QLabel()
        received_at = self.log.get('received_at', '')
        if received_at and not isinstance(received_at, str):
            received_at = str(received_at)
        self.received_at_label.setText(received_at[:19] if received_at else '-')
        received_at_layout.addWidget(self.received_at_label)

        self.set_now_btn = QPushButton("현재시간")
        self.set_now_btn.setFixedWidth(80)
        self.set_now_btn.clicked.connect(self.set_received_now)
        received_at_layout.addWidget(self.set_now_btn)
        received_at_layout.addStretch()

        received_at_widget = QWidget()
        received_at_widget.setLayout(received_at_layout)
        status_layout.addRow("수신일시:", received_at_widget)

        layout.addWidget(status_frame)

        # 본문
        layout.addWidget(QLabel("본문:"))
        body_area = QTextEdit()
        body_area.setReadOnly(True)
        body_area.setPlainText(self.log.get('body', '') or '')
        layout.addWidget(body_area)

        # 버튼 영역
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_status)
        btn_layout.addWidget(save_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def on_received_changed(self, text):
        """수신여부 변경시 수신일시 자동 설정"""
        if text == "예" and self.received_at_label.text() == '-':
            self.set_received_now()

    def set_received_now(self):
        """수신일시를 현재 시간으로 설정"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.received_at_label.setText(now)

    def save_status(self):
        """상태 저장"""
        try:
            from models.communications import EmailLog

            status = self.status_combo.currentText()
            received = self.received_combo.currentText()
            received_at_text = self.received_at_label.text()
            received_at = received_at_text if received_at_text != '-' else None

            success = EmailLog.update_status(
                self.log['id'],
                status=status,
                received=received,
                received_at=received_at
            )

            if success:
                QMessageBox.information(self, "성공", "상태가 저장되었습니다.")
                # 부모 테이블 새로고침
                if hasattr(self.parent_widget, 'load_email_logs'):
                    self.parent_widget.load_email_logs()
            else:
                QMessageBox.warning(self, "오류", "상태 저장에 실패했습니다.")

        except Exception as e:
            QMessageBox.warning(self, "오류", f"저장 오류: {str(e)}")
