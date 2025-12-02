#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
커뮤니케이션 탭 - 사용자 간 채팅 및 메일 공지
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFrame, QSplitter, QListWidget, QListWidgetItem,
                           QTextEdit, QLineEdit, QTabWidget, QTableWidget,
                           QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
                           QComboBox, QMessageBox, QScrollArea, QCheckBox,
                           QGroupBox, QDialogButtonBox, QPlainTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QBrush


class CommunicationTab(QWidget):
    """커뮤니케이션 탭 (채팅 + 메일 공지)"""

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
        self.load_mails()
        self.check_unread()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 메인 탭 위젯 (채팅 / 메일 공지)
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

        # 메일 공지 탭
        mail_widget = QWidget()
        self.setup_mail_tab(mail_widget)
        self.main_tab.addTab(mail_widget, "메일 공지")

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

    def setup_mail_tab(self, widget):
        """메일 공지 탭 설정"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 상단 버튼
        btn_layout = QHBoxLayout()

        new_mail_btn = QPushButton("새 메일 작성")
        new_mail_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        new_mail_btn.clicked.connect(self.compose_mail)
        btn_layout.addWidget(new_mail_btn)

        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_mails)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 메일 탭 (받은 메일 / 보낸 메일)
        self.mail_tab = QTabWidget()

        # 받은 메일
        received_widget = QWidget()
        received_layout = QVBoxLayout(received_widget)
        self.received_mail_table = QTableWidget(0, 4)
        self.received_mail_table.setHorizontalHeaderLabels(["", "보낸 사람", "제목", "날짜"])
        self.received_mail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.received_mail_table.setColumnWidth(0, 30)
        self.received_mail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.received_mail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.received_mail_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.received_mail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.received_mail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.received_mail_table.doubleClicked.connect(self.view_received_mail)
        received_layout.addWidget(self.received_mail_table)
        self.mail_tab.addTab(received_widget, "받은 메일")

        # 보낸 메일
        sent_widget = QWidget()
        sent_layout = QVBoxLayout(sent_widget)
        self.sent_mail_table = QTableWidget(0, 3)
        self.sent_mail_table.setHorizontalHeaderLabels(["받는 사람", "제목", "날짜"])
        self.sent_mail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.sent_mail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.sent_mail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.sent_mail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sent_mail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sent_mail_table.doubleClicked.connect(self.view_sent_mail)
        sent_layout.addWidget(self.sent_mail_table)
        self.mail_tab.addTab(sent_widget, "보낸 메일")

        layout.addWidget(self.mail_tab)

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
                time_str = msg['created_at'][:16] if msg['created_at'] else ''

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

    def load_mails(self):
        """메일 목록 로드"""
        if not self.current_user:
            return

        try:
            from models.communications import MailNotice

            # 받은 메일
            received = MailNotice.get_received(self.current_user['id'])
            self.received_mail_table.setRowCount(0)

            for mail in received:
                row = self.received_mail_table.rowCount()
                self.received_mail_table.insertRow(row)

                # 읽음 여부
                read_item = QTableWidgetItem("" if mail['read_at'] else "●")
                read_item.setForeground(QBrush(QColor("#9b59b6")))
                read_item.setTextAlignment(Qt.AlignCenter)
                self.received_mail_table.setItem(row, 0, read_item)

                # 보낸 사람
                sender_item = QTableWidgetItem(mail['sender_name'] or '')
                self.received_mail_table.setItem(row, 1, sender_item)

                # 제목
                subject_item = QTableWidgetItem(mail['subject'] or '')
                subject_item.setData(Qt.UserRole, mail['id'])
                if not mail['read_at']:
                    font = subject_item.font()
                    font.setBold(True)
                    subject_item.setFont(font)
                self.received_mail_table.setItem(row, 2, subject_item)

                # 날짜
                date_str = mail['created_at'][:10] if mail['created_at'] else ''
                self.received_mail_table.setItem(row, 3, QTableWidgetItem(date_str))

            # 보낸 메일
            sent = MailNotice.get_sent(self.current_user['id'])
            self.sent_mail_table.setRowCount(0)

            for mail in sent:
                row = self.sent_mail_table.rowCount()
                self.sent_mail_table.insertRow(row)

                # 받는 사람
                to_names = mail['to_names'] or ''
                self.sent_mail_table.setItem(row, 0, QTableWidgetItem(to_names))

                # 제목
                subject_item = QTableWidgetItem(mail['subject'] or '')
                subject_item.setData(Qt.UserRole, mail['id'])
                self.sent_mail_table.setItem(row, 1, subject_item)

                # 날짜
                date_str = mail['created_at'][:10] if mail['created_at'] else ''
                self.sent_mail_table.setItem(row, 2, QTableWidgetItem(date_str))

        except Exception as e:
            print(f"메일 목록 로드 오류: {e}")

    def compose_mail(self):
        """새 메일 작성"""
        if not self.current_user:
            return

        dialog = ComposeMailDialog(self, self.all_users, self.current_user)
        if dialog.exec_():
            self.load_mails()
            self.check_unread()
            QMessageBox.information(self, "완료", "메일이 전송되었습니다.")

    def view_received_mail(self, index):
        """받은 메일 보기"""
        row = index.row()
        mail_id = self.received_mail_table.item(row, 2).data(Qt.UserRole)

        try:
            from models.communications import MailNotice

            # 읽음 처리
            MailNotice.mark_as_read(mail_id, self.current_user['id'])

            # 메일 상세
            mail = MailNotice.get_by_id(mail_id)
            if mail:
                dialog = ViewMailDialog(self, mail)
                dialog.exec_()

            self.load_mails()
            self.check_unread()

        except Exception as e:
            print(f"메일 보기 오류: {e}")

    def view_sent_mail(self, index):
        """보낸 메일 보기"""
        row = index.row()
        mail_id = self.sent_mail_table.item(row, 1).data(Qt.UserRole)

        try:
            from models.communications import MailNotice
            mail = MailNotice.get_by_id(mail_id)
            if mail:
                dialog = ViewMailDialog(self, mail, is_sent=True)
                dialog.exec_()
        except Exception as e:
            print(f"메일 보기 오류: {e}")

    def check_unread(self):
        """읽지 않은 메시지/메일 확인"""
        if not self.current_user:
            return

        try:
            from models.communications import Message, MailNotice

            msg_unread = Message.get_unread_count(self.current_user['id'])
            mail_unread = MailNotice.get_unread_count(self.current_user['id'])

            total_unread = msg_unread + mail_unread
            self.unread_changed.emit(total_unread)

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


class ComposeMailDialog(QDialog):
    """메일 작성 다이얼로그"""

    def __init__(self, parent, users, current_user):
        super().__init__(parent)
        self.setWindowTitle("새 메일 작성")
        self.setMinimumSize(600, 600)
        self.current_user = current_user
        self.to_checkboxes = {}
        self.cc_checkboxes = {}

        # 사용자 목록 로드 (DB에서 직접)
        self.users = self._load_users()
        self.initUI()

    def _load_users(self):
        """사용자 관리에서 등록된 사용자 목록 로드"""
        try:
            from models.users import User
            all_users = User.get_all() or []
            # 현재 사용자 제외
            return [u for u in all_users if u.get('id') != self.current_user.get('id')]
        except Exception as e:
            print(f"사용자 목록 로드 오류: {e}")
            return []

    def initUI(self):
        layout = QVBoxLayout(self)

        # 사용자가 없는 경우 안내
        if not self.users:
            no_user_label = QLabel("등록된 사용자가 없습니다.\n사용자 관리에서 사용자를 먼저 등록해주세요.")
            no_user_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
            no_user_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_user_label)

            close_btn = QPushButton("닫기")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return

        # 수신자 선택
        to_group = QGroupBox("수신자 (To) - 필수")
        to_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        to_main_layout = QVBoxLayout(to_group)

        # 수신자 버튼
        to_btn_layout = QHBoxLayout()
        to_select_all_btn = QPushButton("전체 선택")
        to_select_all_btn.setStyleSheet("padding: 3px 10px;")
        to_select_all_btn.clicked.connect(lambda: self.select_all_users('to'))
        to_deselect_all_btn = QPushButton("전체 해제")
        to_deselect_all_btn.setStyleSheet("padding: 3px 10px;")
        to_deselect_all_btn.clicked.connect(lambda: self.deselect_all_users('to'))
        to_btn_layout.addWidget(to_select_all_btn)
        to_btn_layout.addWidget(to_deselect_all_btn)
        to_btn_layout.addStretch()
        to_main_layout.addLayout(to_btn_layout)

        # 수신자 스크롤 영역
        to_scroll = QScrollArea()
        to_scroll.setWidgetResizable(True)
        to_scroll.setMaximumHeight(150)
        to_widget = QWidget()
        to_grid = QVBoxLayout(to_widget)
        to_grid.setSpacing(3)

        for user in self.users:
            name = user.get('name', '')
            dept = user.get('department', '')
            display_text = f"{name} ({dept})" if dept else name
            cb = QCheckBox(display_text)
            cb.setProperty('user_id', user.get('id'))
            self.to_checkboxes[user.get('id')] = cb
            to_grid.addWidget(cb)
        to_grid.addStretch()

        to_scroll.setWidget(to_widget)
        to_main_layout.addWidget(to_scroll)
        layout.addWidget(to_group)

        # 참조자 선택
        cc_group = QGroupBox("참조 (CC) - 선택사항")
        cc_main_layout = QVBoxLayout(cc_group)

        # 참조자 버튼
        cc_btn_layout = QHBoxLayout()
        cc_select_all_btn = QPushButton("전체 선택")
        cc_select_all_btn.setStyleSheet("padding: 3px 10px;")
        cc_select_all_btn.clicked.connect(lambda: self.select_all_users('cc'))
        cc_deselect_all_btn = QPushButton("전체 해제")
        cc_deselect_all_btn.setStyleSheet("padding: 3px 10px;")
        cc_deselect_all_btn.clicked.connect(lambda: self.deselect_all_users('cc'))
        cc_btn_layout.addWidget(cc_select_all_btn)
        cc_btn_layout.addWidget(cc_deselect_all_btn)
        cc_btn_layout.addStretch()
        cc_main_layout.addLayout(cc_btn_layout)

        # 참조자 스크롤 영역
        cc_scroll = QScrollArea()
        cc_scroll.setWidgetResizable(True)
        cc_scroll.setMaximumHeight(150)
        cc_widget = QWidget()
        cc_grid = QVBoxLayout(cc_widget)
        cc_grid.setSpacing(3)

        for user in self.users:
            name = user.get('name', '')
            dept = user.get('department', '')
            display_text = f"{name} ({dept})" if dept else name
            cb = QCheckBox(display_text)
            cb.setProperty('user_id', user.get('id'))
            self.cc_checkboxes[user.get('id')] = cb
            cc_grid.addWidget(cb)
        cc_grid.addStretch()

        cc_scroll.setWidget(cc_widget)
        cc_main_layout.addWidget(cc_scroll)
        layout.addWidget(cc_group)

        # 제목
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("제목:"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("메일 제목을 입력하세요")
        subject_layout.addWidget(self.subject_input)
        layout.addLayout(subject_layout)

        # 내용
        layout.addWidget(QLabel("내용:"))
        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText("메일 내용을 입력하세요")
        layout.addWidget(self.content_input)

        # 버튼
        btn_layout = QHBoxLayout()
        send_btn = QPushButton("보내기")
        send_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px 20px; font-weight: bold;")
        send_btn.clicked.connect(self.send_mail)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def select_all_users(self, target):
        """전체 선택"""
        checkboxes = self.to_checkboxes if target == 'to' else self.cc_checkboxes
        for cb in checkboxes.values():
            cb.setChecked(True)

    def deselect_all_users(self, target):
        """전체 해제"""
        checkboxes = self.to_checkboxes if target == 'to' else self.cc_checkboxes
        for cb in checkboxes.values():
            cb.setChecked(False)

    def send_mail(self):
        to_ids = [uid for uid, cb in self.to_checkboxes.items() if cb.isChecked()]
        cc_ids = [uid for uid, cb in self.cc_checkboxes.items() if cb.isChecked()]
        subject = self.subject_input.text().strip()
        content = self.content_input.toPlainText().strip()

        if not to_ids:
            QMessageBox.warning(self, "알림", "수신자를 선택하세요.")
            return

        if not subject:
            QMessageBox.warning(self, "알림", "제목을 입력하세요.")
            return

        if not content:
            QMessageBox.warning(self, "알림", "내용을 입력하세요.")
            return

        try:
            from models.communications import MailNotice

            MailNotice.send(
                self.current_user['id'],
                subject,
                content,
                to_ids,
                cc_ids if cc_ids else None
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"메일 전송 실패: {e}")


class ViewMailDialog(QDialog):
    """메일 보기 다이얼로그"""

    def __init__(self, parent, mail, is_sent=False):
        super().__init__(parent)
        self.setWindowTitle("메일 보기")
        self.setMinimumSize(500, 400)
        self.mail = mail
        self.is_sent = is_sent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 메일 정보
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        info_layout = QFormLayout(info_frame)

        if self.is_sent:
            # 받는 사람
            to_names = ', '.join([r['name'] for r in self.mail.get('recipients', [])
                                  if r['recipient_type'] == 'to'])
            cc_names = ', '.join([r['name'] for r in self.mail.get('recipients', [])
                                  if r['recipient_type'] == 'cc'])
            info_layout.addRow("받는 사람:", QLabel(to_names))
            if cc_names:
                info_layout.addRow("참조:", QLabel(cc_names))
        else:
            info_layout.addRow("보낸 사람:", QLabel(self.mail.get('sender_name', '')))

        info_layout.addRow("제목:", QLabel(self.mail.get('subject', '')))
        info_layout.addRow("날짜:", QLabel(self.mail.get('created_at', '')[:16]))

        layout.addWidget(info_frame)

        # 내용
        content_area = QTextEdit()
        content_area.setReadOnly(True)
        content_area.setPlainText(self.mail.get('content', ''))
        layout.addWidget(content_area)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
