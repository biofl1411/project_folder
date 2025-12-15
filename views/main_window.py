from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QTabWidget, QPushButton, QLabel, QMessageBox,
                           QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                           QDialog, QCheckBox, QScrollArea, QGroupBox,
                           QDialogButtonBox)
from PyQt5.QtCore import Qt, QSize, QSettings, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor

from .login import LoginWindow

# 탭 식별자 상수
TAB_IDS = {
    'dashboard': '대시보드',
    'schedule': '스케줄 작성',
    'client': '업체 관리',
    'food_type': '식품 유형 관리',
    'fee': '수수료 관리',
    'estimate': '견적서 관리',
    'schedule_mgmt': '스케줄 관리',
    'communication': '커뮤니케이션',
    'user_mgmt': '사용자 관리',
}

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

        update_btn = QPushButton("🔄 업데이트")
        update_btn.setStyleSheet("background-color: #27ae60; color: white;")
        update_btn.clicked.connect(self.check_for_updates)

        logout_btn = QPushButton("로그아웃")
        logout_btn.setStyleSheet("background-color: #f44336; color: white;")
        logout_btn.clicked.connect(self.logout)

        # 레이아웃에 위젯 추가
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.user_label)
        title_layout.addWidget(update_btn)
        title_layout.addWidget(settings_btn)
        title_layout.addWidget(logout_btn)
        
        # 메인 레이아웃에 추가
        self.main_layout.addWidget(title_frame)
    
    def create_tab_widget(self):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { height: 30px; width: 120px; }")

        # 탭 이동 가능하게 설정
        self.tab_widget.setMovable(True)

        # 탭 위젯 저장용 딕셔너리 (탭 ID -> 위젯)
        self.tab_widgets = {}
        
        # 대시보드 탭
        dashboard_tab = QWidget()
        self.create_dashboard_tab(dashboard_tab)
        self.tab_widgets['dashboard'] = dashboard_tab
        self.tab_widget.addTab(dashboard_tab, TAB_IDS['dashboard'])

        # 스케줄 작성 탭
        from .schedule_tab import ScheduleTab
        self.schedule_tab = ScheduleTab()
        self.tab_widgets['schedule'] = self.schedule_tab
        self.tab_widget.addTab(self.schedule_tab, TAB_IDS['schedule'])

        # 업체 관리 탭
        from .client_tab import ClientTab
        self.client_tab = ClientTab()
        self.tab_widgets['client'] = self.client_tab
        self.tab_widget.addTab(self.client_tab, TAB_IDS['client'])

        # 식품 유형 관리 탭
        from .food_type_tab import FoodTypeTab
        self.food_type_tab = FoodTypeTab()
        self.tab_widgets['food_type'] = self.food_type_tab
        self.tab_widget.addTab(self.food_type_tab, TAB_IDS['food_type'])

        # 수수료 관리 탭
        from .fee_tab import FeeTab
        self.fee_tab = FeeTab()
        self.tab_widgets['fee'] = self.fee_tab
        self.tab_widget.addTab(self.fee_tab, TAB_IDS['fee'])

        # 견적서 관리 탭
        from .estimate_tab import EstimateTab
        self.estimate_tab = EstimateTab()
        self.tab_widgets['estimate'] = self.estimate_tab
        self.tab_widget.addTab(self.estimate_tab, TAB_IDS['estimate'])

        # 스케줄 관리 탭
        from .schedule_management_tab import ScheduleManagementTab
        self.schedule_management_tab = ScheduleManagementTab()
        self.tab_widgets['schedule_mgmt'] = self.schedule_management_tab
        self.tab_widget.addTab(self.schedule_management_tab, TAB_IDS['schedule_mgmt'])

        # 스케줄 작성 탭 더블클릭 시 스케줄 관리 탭으로 이동
        self.schedule_tab.schedule_double_clicked.connect(self.show_schedule_detail)

        # 스케줄 작성 탭에서 스케줄 삭제 시 스케줄 관리 탭에 알림
        self.schedule_tab.schedule_deleted.connect(self.schedule_management_tab.on_schedule_deleted)

        # 스케줄 관리 탭에서 견적서 보기 버튼 연결
        self.schedule_management_tab.show_estimate_requested.connect(self.show_estimate)

        # 스케줄 관리 탭에서 저장 시 스케줄 작성 탭 및 대시보드 새로고침
        self.schedule_management_tab.schedule_saved.connect(self.schedule_tab.load_schedules)
        self.schedule_management_tab.schedule_saved.connect(self.load_dashboard_data)

        # 커뮤니케이션 탭
        from .communication_tab import CommunicationTab
        self.communication_tab = CommunicationTab()
        self.tab_widgets['communication'] = self.communication_tab
        self.tab_widget.addTab(self.communication_tab, TAB_IDS['communication'])

        # 커뮤니케이션 탭 새 메시지 알림 연결
        self.communication_tab.unread_changed.connect(self.on_unread_changed)

        # 새 메시지 알림 깜빡임 타이머
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_state = False
        self.unread_count = 0

        # 사용자 관리 탭 (관리자만 접근 가능)
        from .user_management_tab import UserManagementTab
        self.user_management_tab = UserManagementTab()
        self.tab_widgets['user_mgmt'] = self.user_management_tab
        self.tab_widget.addTab(self.user_management_tab, TAB_IDS['user_mgmt'])

        # 저장된 탭 순서 복원
        self.restore_tab_order()

        # 탭 이동 시 순서 저장
        self.tab_widget.tabBar().tabMoved.connect(self.save_tab_order)

        # 탭 변경 시 대시보드 새로고침
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # 메인 레이아웃에 탭 위젯 추가
        self.main_layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self, tab):
        """대시보드 탭 내용 생성"""
        layout = QVBoxLayout(tab)

        # 대시보드 위젯 참조 저장
        self.dashboard_cards = {}
        self.dashboard_detail_table = None
        self.dashboard_current_filter = None
        self.dashboard_all_schedules = []

        # 상단 요약 정보 카드들
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.StyledPanel)
        summary_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        summary_layout = QHBoxLayout(summary_frame)

        # 요약 정보 항목들 (클릭 가능)
        info_items = [
            {"key": "scheduled", "title": "입고 예정", "value": "0", "color": "#00BFFF"},
            {"key": "interim", "title": "중간보고", "value": "0", "color": "#4CAF50"},
            {"key": "received", "title": "입고", "value": "0", "color": "#FF9800"},
            {"key": "extension", "title": "연장실험", "value": "0", "color": "#9C27B0"}
        ]

        for item in info_items:
            item_frame = QFrame()
            item_frame.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {item['color']};
                    border-radius: 8px;
                    background-color: white;
                }}
                QFrame:hover {{
                    background-color: {item['color']}20;
                    border: 2px solid {item['color']};
                }}
            """)
            item_frame.setCursor(QCursor(Qt.PointingHandCursor))
            item_frame.mousePressEvent = lambda event, key=item['key']: self.on_dashboard_card_click(key)
            item_layout = QVBoxLayout(item_frame)

            title_label = QLabel(item["title"])
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")

            value_label = QLabel(item["value"])
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {item['color']}; border: none;")
            value_label.setObjectName(f"dashboard_value_{item['key']}")

            item_layout.addWidget(title_label)
            item_layout.addWidget(value_label)

            # 카드 참조 저장
            self.dashboard_cards[item['key']] = {
                'frame': item_frame,
                'value_label': value_label,
                'color': item['color']
            }

            summary_layout.addWidget(item_frame)

        layout.addWidget(summary_frame)

        # 세부 내역 섹션
        detail_frame = QFrame()
        detail_frame.setFrameShape(QFrame.StyledPanel)
        detail_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        detail_layout = QVBoxLayout(detail_frame)

        # 세부 내역 헤더 (타이틀 + 표시 설정 버튼)
        detail_header_layout = QHBoxLayout()

        self.detail_title_label = QLabel("세부 내역")
        self.detail_title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        detail_header_layout.addWidget(self.detail_title_label)

        detail_header_layout.addStretch()

        # 표시 설정 버튼
        display_settings_btn = QPushButton("표시 설정")
        display_settings_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 5px 15px;")
        display_settings_btn.clicked.connect(self.open_dashboard_display_settings)
        detail_header_layout.addWidget(display_settings_btn)

        detail_layout.addLayout(detail_header_layout)

        # 세부 내역 테이블
        self.dashboard_detail_table = QTableWidget(0, 0)
        self.dashboard_detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dashboard_detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dashboard_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dashboard_detail_table.horizontalHeader().setStretchLastSection(True)
        # 헤더 이동(드래그) 및 정렬 기능 추가
        self.dashboard_detail_table.horizontalHeader().setSectionsMovable(True)
        self.dashboard_detail_table.setSortingEnabled(True)
        self.dashboard_detail_table.horizontalHeader().sortIndicatorChanged.connect(self.on_dashboard_sort_changed)
        self.dashboard_detail_table.doubleClicked.connect(self.on_dashboard_detail_double_click)
        detail_layout.addWidget(self.dashboard_detail_table)

        # 현재 정렬 상태 저장
        self.dashboard_sort_column = -1
        self.dashboard_sort_order = Qt.AscendingOrder

        layout.addWidget(detail_frame)

        # 최근 견적 목록
        estimate_frame = QFrame()
        estimate_frame.setFrameShape(QFrame.StyledPanel)
        estimate_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        estimate_layout = QVBoxLayout(estimate_frame)

        estimate_title = QLabel("최근 견적")
        estimate_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        estimate_layout.addWidget(estimate_title)

        self.dashboard_estimate_table = QTableWidget(0, 4)
        self.dashboard_estimate_table.setHorizontalHeaderLabels(["업체명", "제목", "작성일", "총액"])
        self.dashboard_estimate_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        estimate_layout.addWidget(self.dashboard_estimate_table)

        layout.addWidget(estimate_frame)

    def on_tab_changed(self, index):
        """탭 변경 시 호출 - 해당 탭 데이터 로드 (Lazy Loading)"""
        current_widget = self.tab_widget.widget(index)
        dashboard_widget = self.tab_widgets.get('dashboard')
        schedule_widget = self.tab_widgets.get('schedule')

        if current_widget == dashboard_widget:
            self.load_dashboard_data()
        elif current_widget == schedule_widget:
            # 스케줄 작성 탭 활성화 시 데이터 로드
            if hasattr(self.schedule_tab, 'on_tab_activated'):
                self.schedule_tab.on_tab_activated()

    def load_dashboard_data(self):
        """대시보드 데이터 로드 및 카드 업데이트"""
        try:
            from models.schedules import Schedule
            from .settings_dialog import get_status_map

            # 모든 스케줄 가져오기
            all_schedules = Schedule.get_all() or []
            self.dashboard_all_schedules = [dict(s) for s in all_schedules]

            # 사용자 권한에 따라 필터링
            if self.current_user:
                department = self.current_user.get('department', '')
                user_name = self.current_user.get('name', '')
                role = self.current_user.get('role', '')

                if role != 'admin' and department not in ['고객지원팀', '마케팅팀']:
                    self.dashboard_all_schedules = [
                        s for s in self.dashboard_all_schedules
                        if (s.get('sales_rep', '') or '') == user_name
                    ]

            # 각 카드별 건수 계산
            scheduled_count = sum(1 for s in self.dashboard_all_schedules if s.get('status') == 'scheduled')
            # 중간보고: 입고 상태이면서 report_interim=True인 경우
            interim_count = sum(1 for s in self.dashboard_all_schedules
                              if s.get('status') == 'received' and s.get('report_interim'))
            received_count = sum(1 for s in self.dashboard_all_schedules if s.get('status') == 'received')
            # 연장실험: 입고 상태이면서 extension_test=True인 경우
            extension_count = sum(1 for s in self.dashboard_all_schedules
                                if s.get('status') == 'received' and s.get('extension_test'))

            # 카드 값 업데이트
            if hasattr(self, 'dashboard_cards') and self.dashboard_cards:
                self.dashboard_cards['scheduled']['value_label'].setText(str(scheduled_count))
                self.dashboard_cards['interim']['value_label'].setText(str(interim_count))
                self.dashboard_cards['received']['value_label'].setText(str(received_count))
                self.dashboard_cards['extension']['value_label'].setText(str(extension_count))

            # 기본으로 입고 예정 데이터 표시
            self.on_dashboard_card_click('scheduled')

        except Exception as e:
            print(f"대시보드 데이터 로드 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_dashboard_card_click(self, card_key):
        """대시보드 카드 클릭 시 해당 데이터를 세부 내역에 표시"""
        self.dashboard_current_filter = card_key

        # 카드별 타이틀 및 필터링
        titles = {
            'scheduled': '세부 내역 - 입고 예정',
            'interim': '세부 내역 - 중간보고',
            'received': '세부 내역 - 입고',
            'extension': '세부 내역 - 연장실험'
        }

        if hasattr(self, 'detail_title_label'):
            self.detail_title_label.setText(titles.get(card_key, '세부 내역'))

        # 선택된 카드 강조 표시
        for key, card in self.dashboard_cards.items():
            if key == card_key:
                card['frame'].setStyleSheet(f"""
                    QFrame {{
                        border: 3px solid {card['color']};
                        border-radius: 8px;
                        background-color: {card['color']}30;
                    }}
                """)
            else:
                card['frame'].setStyleSheet(f"""
                    QFrame {{
                        border: 2px solid {card['color']};
                        border-radius: 8px;
                        background-color: white;
                    }}
                    QFrame:hover {{
                        background-color: {card['color']}20;
                    }}
                """)

        # 데이터 필터링
        filtered_schedules = []
        if card_key == 'scheduled':
            filtered_schedules = [s for s in self.dashboard_all_schedules if s.get('status') == 'scheduled']
        elif card_key == 'interim':
            # 입고 상태이면서 중간보고가 있는 경우
            filtered_schedules = [s for s in self.dashboard_all_schedules
                                if s.get('status') == 'received' and s.get('report_interim')]
        elif card_key == 'received':
            filtered_schedules = [s for s in self.dashboard_all_schedules if s.get('status') == 'received']
        elif card_key == 'extension':
            # 입고 상태이면서 연장실험이 있는 경우
            filtered_schedules = [s for s in self.dashboard_all_schedules
                                if s.get('status') == 'received' and s.get('extension_test')]

        # 테이블에 데이터 표시
        self.display_dashboard_detail(filtered_schedules)

    def get_dashboard_column_settings(self):
        """대시보드 세부 내역 컬럼 설정 가져오기"""
        default_columns = ['client_name', 'product_name', 'start_date', 'end_date', 'status', 'interim_date']
        try:
            from connection_manager import is_internal_mode
            if not is_internal_mode():
                return default_columns  # 외부망에서는 기본값 사용

            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'dashboard_detail_columns'")
            result = cursor.fetchone()
            conn.close()

            if result and result['value']:
                return result['value'].split(',')
        except Exception as e:
            print(f"대시보드 컬럼 설정 로드 오류: {e}")

        return default_columns

    def display_dashboard_detail(self, schedules):
        """세부 내역 테이블에 스케줄 표시"""
        if not self.dashboard_detail_table:
            return

        try:
            from .settings_dialog import get_status_map, get_status_colors

            # 표시할 컬럼 설정
            visible_columns = self.get_dashboard_column_settings()

            # 컬럼 정의
            all_columns = [
                ('client_name', '업체명'),
                ('product_name', '샘플명'),
                ('sales_rep', '영업담당'),
                ('food_type', '식품유형'),
                ('test_method', '실험방법'),
                ('storage_condition', '보관조건'),
                ('expiry_period', '소비기한'),
                ('sampling_count', '샘플링횟수'),
                ('start_date', '시작일'),
                ('end_date', '종료일'),
                ('interim_date', '중간보고일'),
                ('extension_test', '연장실험'),
                ('status', '상태'),
                ('memo', '메모'),
            ]

            # 표시할 컬럼만 필터링
            display_columns = [(key, name) for key, name in all_columns if key in visible_columns]

            # 테이블 설정
            self.dashboard_detail_table.setColumnCount(len(display_columns) + 1)  # +1 for hidden ID
            headers = ['ID'] + [col[1] for col in display_columns]
            self.dashboard_detail_table.setHorizontalHeaderLabels(headers)
            self.dashboard_detail_table.setColumnHidden(0, True)  # ID 숨김

            self.dashboard_detail_table.setRowCount(0)

            status_map = get_status_map()
            status_colors = get_status_colors()

            for row, schedule in enumerate(schedules):
                self.dashboard_detail_table.insertRow(row)

                # ID 저장 (숨김)
                self.dashboard_detail_table.setItem(row, 0, QTableWidgetItem(str(schedule.get('id', ''))))

                for col_idx, (col_key, col_name) in enumerate(display_columns):
                    value = ''

                    if col_key == 'client_name':
                        value = schedule.get('client_name', '') or ''
                    elif col_key == 'product_name':
                        value = schedule.get('product_name', '') or ''
                    elif col_key == 'sales_rep':
                        value = schedule.get('sales_rep', '') or ''
                    elif col_key == 'food_type':
                        food_type_id = schedule.get('food_type_id')
                        if food_type_id:
                            try:
                                from models.product_types import ProductType
                                food_type = ProductType.get_by_id(food_type_id)
                                if food_type:
                                    value = food_type.get('type_name', '') or ''
                            except Exception:
                                pass
                    elif col_key == 'test_method':
                        method = schedule.get('test_method', '') or ''
                        method_map = {'real': '실측', 'acceleration': '가속',
                                     'custom_real': '의뢰자(실측)', 'custom_acceleration': '의뢰자(가속)'}
                        value = method_map.get(method, method)
                    elif col_key == 'storage_condition':
                        storage = schedule.get('storage_condition', '') or ''
                        storage_map = {'room_temp': '상온', 'warm': '실온', 'cool': '냉장', 'freeze': '냉동'}
                        value = storage_map.get(storage, storage)
                    elif col_key == 'expiry_period':
                        days = schedule.get('test_period_days', 0) or 0
                        months = schedule.get('test_period_months', 0) or 0
                        years = schedule.get('test_period_years', 0) or 0
                        parts = []
                        if years > 0:
                            parts.append(f"{years}년")
                        if months > 0:
                            parts.append(f"{months}개월")
                        if days > 0:
                            parts.append(f"{days}일")
                        value = ' '.join(parts) if parts else ''
                    elif col_key == 'sampling_count':
                        value = str(schedule.get('sampling_count', '') or '')
                    elif col_key == 'start_date':
                        value = schedule.get('start_date', '') or ''
                    elif col_key == 'end_date':
                        value = schedule.get('end_date', '') or ''
                    elif col_key == 'interim_date':
                        # 중간보고일 계산
                        report_interim = schedule.get('report_interim', False)
                        start_date = schedule.get('start_date', '') or ''
                        sampling_count = schedule.get('sampling_count', 6) or 6

                        test_method = schedule.get('test_method', 'real') or 'real'
                        days = schedule.get('test_period_days', 0) or 0
                        months = schedule.get('test_period_months', 0) or 0
                        years = schedule.get('test_period_years', 0) or 0
                        total_expiry_days = days + (months * 30) + (years * 365)

                        if test_method in ['acceleration', 'custom_acceleration']:
                            experiment_days = total_expiry_days // 2
                        else:
                            experiment_days = int(total_expiry_days * 1.5)

                        value = '-'
                        if report_interim and start_date and experiment_days > 0 and sampling_count >= 6:
                            try:
                                from datetime import datetime, timedelta
                                start = datetime.strptime(start_date, '%Y-%m-%d')
                                interval = experiment_days // sampling_count
                                interim_date = start + timedelta(days=interval * 6)
                                value = interim_date.strftime('%Y-%m-%d')
                            except (ValueError, TypeError, ZeroDivisionError):
                                value = '-'
                    elif col_key == 'extension_test':
                        ext = schedule.get('extension_test', False)
                        value = '진행' if ext else '미진행'
                    elif col_key == 'status':
                        status = schedule.get('status', 'pending') or 'pending'
                        value = status_map.get(status, status)
                    elif col_key == 'memo':
                        value = schedule.get('memo', '') or ''

                    item = QTableWidgetItem(str(value))

                    # 상태 컬럼에 색상 적용
                    if col_key == 'status':
                        status = schedule.get('status', 'pending') or 'pending'
                        if status in status_colors:
                            color = QColor(status_colors[status])
                            item.setBackground(color)
                            if color.lightness() < 128:
                                item.setForeground(QColor('#FFFFFF'))

                    self.dashboard_detail_table.setItem(row, col_idx + 1, item)

        except Exception as e:
            print(f"세부 내역 표시 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_dashboard_detail_double_click(self, index):
        """세부 내역 더블클릭 시 스케줄 관리 탭으로 이동"""
        row = index.row()
        id_item = self.dashboard_detail_table.item(row, 0)
        if id_item:
            schedule_id = int(id_item.text())
            self.show_schedule_detail(schedule_id)

    def on_dashboard_sort_changed(self, logical_index, order):
        """대시보드 세부 내역 정렬 변경 시"""
        self.dashboard_sort_column = logical_index
        self.dashboard_sort_order = order

    def open_dashboard_display_settings(self):
        """대시보드 세부 내역 표시 설정 다이얼로그"""
        dialog = DashboardDisplaySettingsDialog(self)
        if dialog.exec_():
            # 현재 필터 유지하며 데이터 다시 표시
            if self.dashboard_current_filter:
                self.on_dashboard_card_click(self.dashboard_current_filter)

    def create_status_bar(self):
        """하단 상태 바 생성"""
        from version import VERSION

        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        status_frame.setMaximumHeight(30)

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 0, 10, 0)

        # 좌측 상태 정보
        self.status_label = QLabel("준비 완료")

        # 중앙 개발자 정보
        dev_info_label = QLabel("Copyright © 2025 KIM HEE SUNG. All rights reserved. 프로그램 문의(오류) 김희성 070-7410-1411")
        dev_info_label.setStyleSheet("color: #666; font-size: 11px;")
        dev_info_label.setAlignment(Qt.AlignCenter)

        # 우측 버전 정보
        version_label = QLabel(f"v{VERSION}")
        version_label.setAlignment(Qt.AlignRight)

        # 레이아웃에 위젯 추가
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(dev_info_label)
        status_layout.addStretch()
        status_layout.addWidget(version_label)

        # 메인 레이아웃에 추가
        self.main_layout.addWidget(status_frame)
    
    def show_login(self):
        """로그인 창 표시"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.closed_without_login.connect(self.on_login_closed)
        self.login_window.show()

    def on_login_closed(self):
        """로그인 없이 로그인 창이 닫힐 때 처리"""
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        # EXE에서 이벤트 루프 타이밍 문제 방지를 위해 지연 호출
        QTimer.singleShot(0, QApplication.quit)
    
    def on_login_successful(self, user_data):
        """로그인 성공 시 처리"""
        self.current_user = user_data
        department = user_data.get('department', '')
        self.user_label.setText(f"사용자: {user_data['name']} ({department or user_data['role']})")

        # 각 탭에 현재 사용자 설정 (권한 적용) - 데이터 로드는 지연 (Lazy Loading)
        if hasattr(self, 'schedule_tab') and self.schedule_tab:
            self.schedule_tab.set_current_user(user_data)
        if hasattr(self, 'client_tab') and self.client_tab:
            self.client_tab.set_current_user(user_data)
        if hasattr(self, 'food_type_tab') and self.food_type_tab:
            self.food_type_tab.set_current_user(user_data)
        if hasattr(self, 'fee_tab') and self.fee_tab:
            self.fee_tab.set_current_user(user_data)
        if hasattr(self, 'schedule_management_tab') and self.schedule_management_tab:
            self.schedule_management_tab.set_current_user(user_data)
        if hasattr(self, 'communication_tab') and self.communication_tab:
            self.communication_tab.set_current_user(user_data)
        if hasattr(self, 'user_management_tab') and self.user_management_tab:
            self.user_management_tab.set_current_user(user_data)
        if hasattr(self, 'estimate_tab') and self.estimate_tab:
            self.estimate_tab.set_current_user(user_data)

        # 권한 기반 탭 활성화/비활성화
        self.apply_tab_permissions(user_data)

        self.status_label.setText(f"{user_data['name']}님으로 로그인됨")
        self.show()

        # 대시보드 데이터 지연 로드 (UI 먼저 표시 후 데이터 로드)
        QTimer.singleShot(100, self.load_dashboard_data)

    def on_unread_changed(self, unread_count):
        """미읽은 메시지 수 변경 시 탭 이름 업데이트"""
        self.unread_count = unread_count

        comm_widget = self.tab_widgets.get('communication')
        if not comm_widget:
            return

        tab_index = self.tab_widget.indexOf(comm_widget)
        if tab_index < 0:
            return

        if unread_count > 0:
            # 깜빡임 시작
            if not self.blink_timer.isActive():
                self.blink_timer.start(500)  # 500ms 간격으로 깜빡임
        else:
            # 깜빡임 중지
            self.blink_timer.stop()
            self.tab_widget.setTabText(tab_index, TAB_IDS['communication'])

    def toggle_blink(self):
        """탭 이름 깜빡임 토글"""
        comm_widget = self.tab_widgets.get('communication')
        if not comm_widget:
            return

        tab_index = self.tab_widget.indexOf(comm_widget)
        if tab_index < 0:
            return

        self.blink_state = not self.blink_state

        if self.blink_state:
            # N 표시 (보라색 스타일은 탭 스타일시트로 제한적이므로 텍스트로 표현)
            self.tab_widget.setTabText(tab_index, f"커뮤니케이션 [N:{self.unread_count}]")
            # 탭 색상 변경 시도
            self.tab_widget.tabBar().setTabTextColor(tab_index, QColor("#9b59b6"))
        else:
            self.tab_widget.setTabText(tab_index, TAB_IDS['communication'])
            self.tab_widget.tabBar().setTabTextColor(tab_index, QColor("#000000"))

    def apply_tab_permissions(self, user_data):
        """권한에 따라 탭 활성화/비활성화"""
        from models.users import User

        # 관리자는 모든 탭 접근 가능
        if user_data.get('role') == 'admin':
            return

        # 탭 ID별 필요 권한 (하나라도 있으면 탭 접근 가능)
        tab_permission_groups = {
            'schedule': ['schedule_create', 'schedule_edit', 'schedule_delete',
                        'schedule_status_change', 'schedule_import_excel', 'schedule_export_excel'],
            'client': ['client_view_all', 'client_view_own', 'client_create',
                      'client_edit', 'client_delete', 'client_import_excel', 'client_export_excel'],
            'food_type': ['food_type_create', 'food_type_edit', 'food_type_delete',
                         'food_type_reset', 'food_type_import_excel', 'food_type_update_excel',
                         'food_type_export_excel', 'food_type_db_info'],
            'fee': ['fee_create', 'fee_edit', 'fee_delete', 'fee_import_excel', 'fee_export_excel'],
            'estimate': ['estimate_print', 'estimate_pdf', 'estimate_email'],
            'schedule_mgmt': ['schedule_mgmt_view_estimate', 'schedule_mgmt_display_settings',
                             'schedule_mgmt_select', 'schedule_mgmt_add_item',
                             'schedule_mgmt_delete_item', 'schedule_mgmt_save'],
            'user_mgmt': ['user_manage'],
        }

        for tab_id, permissions in tab_permission_groups.items():
            widget = self.tab_widgets.get(tab_id)
            if not widget:
                continue

            tab_index = self.tab_widget.indexOf(widget)
            if tab_index < 0:
                continue

            # 권한 목록 중 하나라도 있으면 탭 접근 가능
            has_any_perm = any(User.has_permission(user_data, perm) for perm in permissions)
            # 탭 이동은 항상 허용 (내부 기능은 각 탭에서 권한 체크)
            self.tab_widget.setTabEnabled(tab_index, True)

            # 권한이 없으면 잠금 표시만 추가
            current_text = self.tab_widget.tabText(tab_index)
            if not has_any_perm:
                if not current_text.startswith("🔒"):
                    self.tab_widget.setTabText(tab_index, f"🔒 {current_text}")
            else:
                # 권한이 있으면 잠금 표시 제거
                if current_text.startswith("🔒 "):
                    self.tab_widget.setTabText(tab_index, current_text[3:])
    
    def show_settings(self):
        """설정 창 표시"""
        try:
            from .settings_dialog import SettingsDialog

            dialog = SettingsDialog(self, current_user=self.current_user)
            if dialog.exec_():
                # 설정이 저장되면 견적서 탭의 회사 정보 새로고침
                if hasattr(self, 'estimate_tab') and self.estimate_tab:
                    self.estimate_tab.load_company_info()
        except Exception as e:
            import traceback
            print(f"설정 창 표시 중 오류: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"설정 창을 열 수 없습니다: {str(e)}")

    def check_for_updates(self):
        """수동으로 업데이트 확인"""
        try:
            from updater import AutoUpdater
            self._updater = AutoUpdater(self)
            self._updater.check_for_updates(silent=False)  # 결과 항상 표시
        except Exception as e:
            import traceback
            print(f"업데이트 확인 중 오류: {str(e)}")
            traceback.print_exc()
            QMessageBox.warning(self, "오류", f"업데이트를 확인할 수 없습니다: {str(e)}")

    def logout(self):
        """로그아웃 처리"""
        reply = QMessageBox.question(self, '로그아웃',
                                     '정말 로그아웃 하시겠습니까?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.current_user = None

            # 각 탭의 데이터 초기화
            self.clear_all_tab_data()

            self.hide()
            self.show_login()

    def clear_all_tab_data(self):
        """모든 탭의 데이터를 초기화 (로그아웃 시 호출)"""
        # 스케줄 작성 탭 초기화
        if hasattr(self, 'schedule_tab') and self.schedule_tab:
            self.schedule_tab.clear_data()

        # 스케줄 관리 탭 초기화
        if hasattr(self, 'schedule_management_tab') and self.schedule_management_tab:
            self.schedule_management_tab.clear_data()

        # 업체 관리 탭 초기화
        if hasattr(self, 'client_tab') and self.client_tab:
            self.client_tab.clear_data()

        # 식품 유형 탭 초기화
        if hasattr(self, 'food_type_tab') and self.food_type_tab:
            self.food_type_tab.clear_data()

        # 수수료 탭 초기화
        if hasattr(self, 'fee_tab') and self.fee_tab:
            self.fee_tab.clear_data()

        # 견적서 탭 초기화
        if hasattr(self, 'estimate_tab') and self.estimate_tab:
            self.estimate_tab.clear_data()

        # 커뮤니케이션 탭 초기화
        if hasattr(self, 'communication_tab') and self.communication_tab:
            self.communication_tab.clear_data()

        # 사용자 관리 탭 초기화
        if hasattr(self, 'user_management_tab') and self.user_management_tab:
            self.user_management_tab.clear_data()

        # 대시보드 데이터 초기화
        self.dashboard_all_schedules = []
        if hasattr(self, 'dashboard_detail_table') and self.dashboard_detail_table:
            self.dashboard_detail_table.setRowCount(0)
        if hasattr(self, 'dashboard_estimate_table') and self.dashboard_estimate_table:
            self.dashboard_estimate_table.setRowCount(0)

    def show_schedule_detail(self, schedule_id):
        """스케줄 관리 탭으로 이동하고 해당 스케줄 선택"""
        # 스케줄 관리 탭으로 전환 (위젯으로 인덱스 찾기)
        tab_index = self.tab_widget.indexOf(self.tab_widgets.get('schedule_mgmt'))
        if tab_index >= 0:
            self.tab_widget.setCurrentIndex(tab_index)
        # 스케줄 관리 탭에서 해당 스케줄 선택
        self.schedule_management_tab.select_schedule_by_id(schedule_id)

    def show_estimate(self, schedule_data):
        """견적서 관리 탭으로 이동하고 해당 스케줄의 견적서 표시"""
        # 견적서 관리 탭으로 전환 (위젯으로 인덱스 찾기)
        tab_index = self.tab_widget.indexOf(self.tab_widgets.get('estimate'))
        if tab_index >= 0:
            self.tab_widget.setCurrentIndex(tab_index)
        # 견적서 탭에 스케줄 데이터 로드
        self.estimate_tab.load_schedule_data(schedule_data)

    def get_tab_index(self, tab_id):
        """탭 ID로 현재 인덱스 조회"""
        widget = self.tab_widgets.get(tab_id)
        if widget:
            return self.tab_widget.indexOf(widget)
        return -1

    def save_tab_order(self):
        """현재 탭 순서 저장"""
        settings = QSettings('BioFL', 'FoodLabManager')
        tab_order = []

        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            # 위젯으로 탭 ID 찾기
            for tab_id, tab_widget in self.tab_widgets.items():
                if tab_widget is widget:
                    tab_order.append(tab_id)
                    break

        settings.setValue('tab_order', tab_order)

    def restore_tab_order(self):
        """저장된 탭 순서 복원"""
        settings = QSettings('BioFL', 'FoodLabManager')
        saved_order = settings.value('tab_order', [])

        if not saved_order:
            return

        # 저장된 순서대로 탭 재배치
        tab_bar = self.tab_widget.tabBar()

        for target_index, tab_id in enumerate(saved_order):
            widget = self.tab_widgets.get(tab_id)
            if not widget:
                continue

            current_index = self.tab_widget.indexOf(widget)
            if current_index >= 0 and current_index != target_index:
                tab_bar.moveTab(current_index, target_index)


class DashboardDisplaySettingsDialog(QDialog):
    """대시보드 세부 내역 표시 설정 다이얼로그"""

    COLUMN_OPTIONS = [
        ('client_name', '업체명', True),
        ('product_name', '샘플명', True),
        ('sales_rep', '영업담당', False),
        ('food_type', '식품유형', False),
        ('test_method', '실험방법', False),
        ('storage_condition', '보관조건', False),
        ('expiry_period', '소비기한', False),
        ('sampling_count', '샘플링횟수', False),
        ('start_date', '시작일', True),
        ('end_date', '종료일', True),
        ('interim_date', '중간보고일', True),
        ('extension_test', '연장실험', False),
        ('status', '상태', True),
        ('memo', '메모', False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("세부 내역 표시 설정")
        self.setMinimumSize(350, 450)
        self.checkboxes = {}
        self.initUI()
        self.load_settings()

    def initUI(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("세부 내역에서 표시할 컬럼을 선택하세요:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        column_group = QGroupBox("표시 컬럼")
        column_layout = QVBoxLayout(column_group)

        for col_key, col_name, default_visible in self.COLUMN_OPTIONS:
            checkbox = QCheckBox(col_name)
            checkbox.setChecked(default_visible)
            self.checkboxes[col_key] = checkbox
            column_layout.addWidget(checkbox)

        scroll_layout.addWidget(column_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("전체 해제")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def load_settings(self):
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'dashboard_detail_columns'")
            result = cursor.fetchone()
            conn.close()

            if result and result['value']:
                visible_columns = result['value'].split(',')
                for col_key, checkbox in self.checkboxes.items():
                    checkbox.setChecked(col_key in visible_columns)
        except Exception as e:
            print(f"설정 로드 오류: {e}")

    def save_settings(self):
        try:
            from database import get_connection

            visible_columns = [key for key, cb in self.checkboxes.items() if cb.isChecked()]
            value = ','.join(visible_columns)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE `key` = 'dashboard_detail_columns'
            """, (value,))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (`key`, value, description)
                    VALUES ('dashboard_detail_columns', %s, '대시보드 세부 내역 표시 컬럼')
                """, (value,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "저장 완료", "표시 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류: {str(e)}")