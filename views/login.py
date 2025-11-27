#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
로그인 화면
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# 사용자 모델 클래스 - 나중에 구현할 예정
# from ..models.users import User

class LoginWindow(QWidget):
    # 로그인 성공 시그널 (사용자 정보를 전달)
    login_successful = pyqtSignal(dict) 
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
    
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
        
        # 임시 인증 로직 (나중에 User 모델로 대체)
        if username == "admin" and password == "admin123":
            # 로그인 성공
            user_data = {
                "id": 1,
                "username": "admin",
                "name": "관리자",
                "role": "admin"
            }
            self.login_successful.emit(user_data)
            self.close()
        else:
            QMessageBox.warning(self, "로그인 실패", "사용자명 또는 비밀번호가 올바르지 않습니다.")