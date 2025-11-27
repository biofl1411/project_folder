from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QTabWidget, QPushButton, QLabel, QMessageBox,
                           QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from .login import LoginWindow
from .schedule_tab import ScheduleTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 사용자 정보
        self.current_user = None
        
        # UI 초기화
        self.initUI()
        
        # 로그인 창 표시
        self.show_login()
    
    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle("식품 실험 관리 시스템")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 메인 레이아웃
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 상단 타이틀 바
        self.create_title_bar()
        
        # 탭 위젯 생성
        self.create_tab_widget()
        
        # 하단 상태 바
        self.create_status_bar()
    
    def create_title_bar(self):
        """상단 타이틀 바 생성"""
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.StyledPanel)
        title_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # 로고 및 제목
        logo_label = QLabel("🧪")
        logo_label.setStyleSheet("font-size: 24px;")
        title_label = QLabel("식품 실험 관리 시스템")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # 우측 버튼들
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("color: #666;")
        
        settings_btn = QPushButton("⚙️ 설정")
        settings_btn.setStyleSheet("background-color: #ddd;")
        settings_btn.clicked.connect(self.show_settings)
        
        logout_btn = QPushButton("로그아웃")
        logout_btn.setStyleSheet("background-color: #f44336; color: white;")
        logout_btn.clicked.connect(self.logout)
        
        # 레이아웃에 위젯 추가
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.user_label)
        title_layout.addWidget(settings_btn)
        title_layout.addWidget(logout_btn)
        
        # 메인 레이아웃에 추가
        self.main_layout.addWidget(title_frame)
    
    def create_tab_widget(self):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { height: 30px; width: 120px; }")
        
        # 대시보드 탭
        dashboard_tab = QWidget()
        self.create_dashboard_tab(dashboard_tab)
        self.tab_widget.addTab(dashboard_tab, "대시보드")
        
        # 스케줄 작성 탭
        from .schedule_tab import ScheduleTab
        schedule_create_tab = ScheduleTab()
        self.tab_widget.addTab(schedule_create_tab, "스케줄 작성")
        
        # 업체 관리 탭
        from .client_tab import ClientTab
        clients_tab = ClientTab()
        self.tab_widget.addTab(clients_tab, "업체 관리")
        
        # 식품 유형 관리 탭
        from .food_type_tab import FoodTypeTab
        food_type_tab = FoodTypeTab()
        self.tab_widget.addTab(food_type_tab, "식품 유형 관리")
        
        # 수수료 관리 탭
        from .fee_tab import FeeTab
        fee_tab = FeeTab()
        self.tab_widget.addTab(fee_tab, "수수료 관리")
        
        # 견적서 관리 탭
        estimates_tab = QWidget()
        self.tab_widget.addTab(estimates_tab, "견적서 관리")
        
        # 스케줄 관리 탭
        schedule_tab = QWidget()
        self.tab_widget.addTab(schedule_tab, "스케줄 관리")
        
        # 사용자 관리 탭 (관리자만 접근 가능)
        users_tab = QWidget()
        self.tab_widget.addTab(users_tab, "사용자 관리")
        
        # 메인 레이아웃에 탭 위젯 추가
        self.main_layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self, tab):
        """대시보드 탭 내용 생성"""
        layout = QVBoxLayout(tab)
        
        # 상단 요약 정보
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.StyledPanel)
        summary_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        summary_layout = QHBoxLayout(summary_frame)
        
        # 요약 정보 항목들
        info_items = [
            {"title": "등록 업체", "value": "0", "color": "#2196F3"},
            {"title": "실험 항목", "value": "0", "color": "#4CAF50"},
            {"title": "진행 중 실험", "value": "0", "color": "#FF9800"},
            {"title": "이번 달 견적", "value": "0", "color": "#9C27B0"}
        ]
        
        for item in info_items:
            item_frame = QFrame()
            item_frame.setStyleSheet(f"border: 1px solid {item['color']}; border-radius: 5px;")
            item_layout = QVBoxLayout(item_frame)
            
            title_label = QLabel(item["title"])
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-weight: bold;")
            
            value_label = QLabel(item["value"])
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"font-size: 24px; color: {item['color']};")
            
            item_layout.addWidget(title_label)
            item_layout.addWidget(value_label)
            
            summary_layout.addWidget(item_frame)
        
        layout.addWidget(summary_frame)
        
        # 최근 스케줄 목록
        schedule_frame = QFrame()
        schedule_frame.setFrameShape(QFrame.StyledPanel)
        schedule_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        schedule_layout = QVBoxLayout(schedule_frame)
        
        schedule_title = QLabel("최근 스케줄")
        schedule_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        schedule_layout.addWidget(schedule_title)
        
        schedule_table = QTableWidget(0, 4)
        schedule_table.setHorizontalHeaderLabels(["업체명", "제목", "시작일", "상태"])
        schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        schedule_layout.addWidget(schedule_table)
        
        layout.addWidget(schedule_frame)
        
        # 최근 견적 목록
        estimate_frame = QFrame()
        estimate_frame.setFrameShape(QFrame.StyledPanel)
        estimate_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        estimate_layout = QVBoxLayout(estimate_frame)
        
        estimate_title = QLabel("최근 견적")
        estimate_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        estimate_layout.addWidget(estimate_title)
        
        estimate_table = QTableWidget(0, 4)
        estimate_table.setHorizontalHeaderLabels(["업체명", "제목", "작성일", "총액"])
        estimate_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        estimate_layout.addWidget(estimate_table)
        
        layout.addWidget(estimate_frame)
    
    def create_status_bar(self):
        """하단 상태 바 생성"""
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        status_frame.setMaximumHeight(30)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 0, 10, 0)
        
        # 좌측 상태 정보
        self.status_label = QLabel("준비 완료")
        
        # 우측 버전 정보
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignRight)
        
        # 레이아웃에 위젯 추가
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(version_label)
        
        # 메인 레이아웃에 추가
        self.main_layout.addWidget(status_frame)
    
    def show_login(self):
        """로그인 창 표시"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()
    
    def on_login_successful(self, user_data):
        """로그인 성공 시 처리"""
        self.current_user = user_data
        self.user_label.setText(f"사용자: {user_data['name']} ({user_data['role']})")
        
        # 관리자가 아닌 경우 사용자 관리 탭 비활성화
        if user_data['role'] != 'admin':
            self.tab_widget.setTabEnabled(5, False)  # 사용자 관리 탭 비활성화
        
        self.status_label.setText(f"{user_data['name']}님으로 로그인됨")
        self.show()
    
    def show_settings(self):
        """설정 창 표시"""
        # 여기에 설정 창 표시 코드 구현
        QMessageBox.information(self, "설정", "설정 기능은 아직 구현되지 않았습니다.\n여기에 실험 항목과 수수료 관리 기능이 포함될 예정입니다.")
    
    def logout(self):
        """로그아웃 처리"""
        reply = QMessageBox.question(self, '로그아웃', 
                                     '정말 로그아웃 하시겠습니까?',
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.current_user = None
            self.hide()
            self.show_login()