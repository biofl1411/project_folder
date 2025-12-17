#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
로그인 화면
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# 사용자 모델 클래스 - 나중에 구현할 예정
# from ..models.users import User

class LoginWindow(QWidget):
    # 로그인 성공 시그널 (사용자 정보를 전달)
    login_successful = pyqtSignal(dict)
    # 로그인 없이 창이 닫힐 때 시그널
    closed_without_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._login_success = False
        self.initUI()

    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        if not self._login_success:
            # 로그인하지 않고 닫으면 시그널 발생
            self.closed_without_login.emit()
        event.accept()
    
    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle("식품 실험 관리 시스템 - 로그인")
        self.setGeometry(100, 100, 400, 250)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 로고 및 타이틀
        title_layout = QHBoxLayout()
        logo_label = QLabel("🧪")
        logo_label.setStyleSheet("font-size: 32px;")
        title_label = QLabel("식품 실험 관리 시스템")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addStretch()
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # 간격 추가
        main_layout.addSpacing(20)
        
        # 사용자명 입력
        username_layout = QHBoxLayout()
        username_label = QLabel("사용자명:")
        username_label.setMinimumWidth(80)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("사용자 아이디 입력")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        main_layout.addLayout(username_layout)
        
        # 비밀번호 입력
        password_layout = QHBoxLayout()
        password_label = QLabel("비밀번호:")
        password_label.setMinimumWidth(80)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("비밀번호 입력")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        main_layout.addLayout(password_layout)
        
        # 간격 추가
        main_layout.addSpacing(20)
        
        # 로그인 버튼
        button_layout = QHBoxLayout()
        login_button = QPushButton("로그인")
        login_button.setMinimumHeight(30)
        login_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        login_button.clicked.connect(self.attempt_login)
        button_layout.addStretch()
        button_layout.addWidget(login_button)
        main_layout.addLayout(button_layout)
        
        # 간격 추가
        main_layout.addStretch()
        
        # 하단 메시지
        footer_label = QLabel("기본 계정: admin / 비밀번호: admin123")
        footer_label.setStyleSheet("color: gray; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer_label)
        
        # 엔터 키로 로그인
        self.password_input.returnPressed.connect(self.attempt_login)
    
    def attempt_login(self):
        """로그인 시도"""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "입력 오류", "사용자명과 비밀번호를 모두 입력하세요.")
            return

        # 연결 모드 확인
        try:
            from connection_manager import is_internal_mode, connection_manager

            if is_internal_mode():
                # 내부망: DB 직접 연결
                self._login_internal(username, password)
            else:
                # 외부망: API 연결
                self._login_external(username, password)

        except Exception as e:
            print(f"로그인 중 오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"로그인 처리 중 오류가 발생했습니다: {str(e)}")

    def _login_internal(self, username, password):
        """내부망 로그인 (DB 직접 연결)"""
        from models.users import User
        from models.activity_log import ActivityLog

        user_data = User.authenticate(username, password)

        if user_data:
            # 로그인 활동 로그 기록
            ActivityLog.log(
                user=user_data,
                action_type='user_login',
                details={'username': username, 'mode': 'internal'}
            )

            # API 토큰도 설정 (서버 이미지 업로드 등에 필요)
            try:
                from connection_manager import connection_manager
                api = connection_manager.get_api_client()
                api.login(username, password)
                print(f"[로그인] 내부망 API 토큰 설정 완료")
            except Exception as e:
                print(f"[로그인] API 토큰 설정 실패 (무시): {str(e)}")

            self._login_success = True
            self.login_successful.emit(user_data)
            self.close()
        else:
            QMessageBox.warning(self, "로그인 실패", "사용자명 또는 비밀번호가 올바르지 않습니다.")

    def _login_external(self, username, password):
        """외부망 로그인 (API 연결)"""
        from connection_manager import connection_manager

        api = connection_manager.get_api_client()
        user_data = api.login(username, password)

        if user_data:
            self._login_success = True
            self.login_successful.emit(user_data)
            self.close()
        else:
            QMessageBox.warning(self, "로그인 실패", "사용자명 또는 비밀번호가 올바르지 않습니다.")