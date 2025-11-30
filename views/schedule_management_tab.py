#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 관리 탭 - 스케줄 조회, 상세 실험 스케줄 표시
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QMessageBox, QComboBox, QLineEdit, QDateEdit,
                             QDialog, QFormLayout, QTextEdit, QCheckBox, QGroupBox,
                             QFileDialog, QGridLayout, QSpinBox, QSplitter,
                             QScrollArea, QTabWidget, QListWidget, QListWidgetItem,
                             QDialogButtonBox, QCalendarWidget)
from PyQt5.QtCore import Qt, QDate, QDateTime, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QBrush
import pandas as pd
from datetime import datetime

from models.schedules import Schedule
from models.fees import Fee
from models.product_types import ProductType
from utils.logger import log_message, log_error, log_exception, safe_get


class DisplaySettingsDialog(QDialog):
    """표시 항목 설정 다이얼로그"""

    # 설정 가능한 필드 목록
    FIELD_OPTIONS = [
        ('company', '회사명', True),
        ('test_method', '실험방법', True),
        ('product', '제품명', True),
        ('expiry', '소비기한', True),
        ('storage', '보관조건', True),
        ('food_type', '식품유형', True),
        ('period', '실험기간', True),
        ('interim_report', '중간보고서', True),
        ('extension', '연장실험', True),
        ('sampling_count', '샘플링횟수', True),
        ('sampling_interval', '샘플링간격', True),
        ('start_date', '시작일', True),
        ('interim_date', '중간보고일', True),
        ('last_test_date', '마지막실험일', True),
        ('status', '상태', True),
        ('sample_per_test', '1회실험검체량', True),
        ('packaging', '포장단위', True),
        ('required_sample', '필요검체량', True),
        ('temp_zone1', '온도 1구간', True),
        ('temp_zone2', '온도 2구간', True),
        ('temp_zone3', '온도 3구간', True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("표시 항목 설정")
        self.setMinimumSize(400, 500)
        self.checkboxes = {}
        self.initUI()
        self.load_settings()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 설명 라벨
        info_label = QLabel("스케줄 관리 화면에서 표시할 항목을 선택하세요:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 실험 계획 정보 그룹
        info_group = QGroupBox("실험 계획 정보")
        info_layout = QVBoxLayout(info_group)

        for field_key, field_name, default_visible in self.FIELD_OPTIONS[:15]:
            checkbox = QCheckBox(field_name)
            checkbox.setChecked(default_visible)
            self.checkboxes[field_key] = checkbox
            info_layout.addWidget(checkbox)

        scroll_layout.addWidget(info_group)

        # 온도 구간 그룹
        temp_group = QGroupBox("온도 구간")
        temp_layout = QVBoxLayout(temp_group)

        for field_key, field_name, default_visible in self.FIELD_OPTIONS[15:]:
            checkbox = QCheckBox(field_name)
            checkbox.setChecked(default_visible)
            self.checkboxes[field_key] = checkbox
            temp_layout.addWidget(checkbox)

        scroll_layout.addWidget(temp_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 전체 선택/해제 버튼
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("전체 해제")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 저장/취소 버튼
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
        """데이터베이스에서 설정 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_display_fields'")
            result = cursor.fetchone()
            conn.close()

            if result:
                visible_fields = result['value'].split(',')
                for field_key, checkbox in self.checkboxes.items():
                    checkbox.setChecked(field_key in visible_fields)
        except Exception as e:
            print(f"설정 로드 오류: {e}")

    def save_settings(self):
        """설정 저장"""
        try:
            from database import get_connection

            visible_fields = [key for key, cb in self.checkboxes.items() if cb.isChecked()]
            value = ','.join(visible_fields)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = 'schedule_display_fields'
            """, (value,))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (key, value, description)
                    VALUES ('schedule_display_fields', ?, '스케줄 관리 표시 필드')
                """, (value,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "저장 완료", "표시 항목 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류: {str(e)}")

    def get_visible_fields(self):
        """현재 체크된 필드 목록 반환"""
        return [key for key, cb in self.checkboxes.items() if cb.isChecked()]


class TestItemSelectDialog(QDialog):
    """검사항목 선택 다이얼로그"""

    def __init__(self, parent=None, exclude_items=None):
        super().__init__(parent)
        self.selected_item = None
        self.exclude_items = exclude_items or []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("검사항목 선택")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # 검색
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검사항목 검색...")
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # 검사항목 목록 테이블
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(4)
        self.item_table.setHorizontalHeaderLabels(["검사항목", "카테고리", "가격", "검체량(g)"])

        header = self.item_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.item_table.doubleClicked.connect(self.accept)
        layout.addWidget(self.item_table)

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.load_items()

    def load_items(self):
        """수수료 목록에서 검사항목 로드"""
        try:
            log_message('ItemSelectDialog', '검사항목 목록 로드 시작')
            raw_fees = Fee.get_all() or []
            self.all_items = []

            for fee in raw_fees:
                test_item = safe_get(fee, 'test_item', '')
                # 이미 추가된 항목은 제외
                if test_item and test_item not in self.exclude_items:
                    self.all_items.append({
                        'test_item': test_item,
                        'food_category': safe_get(fee, 'food_category', ''),
                        'price': safe_get(fee, 'price', 0) or 0,
                        'sample_quantity': safe_get(fee, 'sample_quantity', 0) or 0
                    })

            self.display_items(self.all_items)
            log_message('ItemSelectDialog', f'검사항목 {len(self.all_items)}개 로드 완료')
        except Exception as e:
            log_exception('ItemSelectDialog', f'검사항목 로드 중 오류: {str(e)}')

    def display_items(self, items):
        """테이블에 항목 표시"""
        self.item_table.setRowCount(0)
        for row, item in enumerate(items):
            self.item_table.insertRow(row)
            self.item_table.setItem(row, 0, QTableWidgetItem(item['test_item']))
            self.item_table.setItem(row, 1, QTableWidgetItem(item['food_category']))
            price_item = QTableWidgetItem(f"{int(item['price']):,}원")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.item_table.setItem(row, 2, price_item)
            qty_item = QTableWidgetItem(f"{item['sample_quantity']}g")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.item_table.setItem(row, 3, qty_item)

    def filter_items(self, text):
        """검색 필터"""
        try:
            if not text:
                self.display_items(self.all_items)
            else:
                filtered = [item for item in self.all_items
                           if text.lower() in (item.get('test_item', '') or '').lower()]
                self.display_items(filtered)
                log_message('ItemSelectDialog', f'검사항목 검색 "{text}": {len(filtered)}개 결과')
        except Exception as e:
            log_exception('ItemSelectDialog', f'검사항목 검색 중 오류: {str(e)}')

    def accept(self):
        selected = self.item_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.selected_item = self.item_table.item(row, 0).text()
        super().accept()


class DateSelectDialog(QDialog):
    """날짜 선택 다이얼로그 (달력 표시)"""

    def __init__(self, parent=None, current_date=None, title="날짜 선택"):
        super().__init__(parent)
        self.selected_date = None
        self.current_date = current_date
        self.setWindowTitle(title)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(350, 300)
        layout = QVBoxLayout(self)

        # 안내 라벨
        info_label = QLabel("실험 날짜를 선택하세요:")
        info_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(info_label)

        # 달력 위젯
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

        # 현재 날짜가 있으면 설정
        if self.current_date:
            try:
                if isinstance(self.current_date, str):
                    # MM-DD 또는 YYYY-MM-DD 형식 파싱
                    if len(self.current_date) == 5:  # MM-DD
                        year = datetime.now().year
                        date_obj = datetime.strptime(f"{year}-{self.current_date}", '%Y-%m-%d')
                    else:
                        date_obj = datetime.strptime(self.current_date, '%Y-%m-%d')
                    self.calendar.setSelectedDate(QDate(date_obj.year, date_obj.month, date_obj.day))
                elif isinstance(self.current_date, datetime):
                    self.calendar.setSelectedDate(QDate(self.current_date.year, self.current_date.month, self.current_date.day))
            except:
                pass

        layout.addWidget(self.calendar)

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        q_date = self.calendar.selectedDate()
        self.selected_date = datetime(q_date.year(), q_date.month(), q_date.day())
        super().accept()


class ScheduleSelectDialog(QDialog):
    """스케줄 선택 팝업 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_schedule_id = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("스케줄 선택")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # 검색 영역
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("업체명, 제품명 검색...")
        self.search_input.returnPressed.connect(self.search_schedules)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self.search_schedules)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels([
            "ID", "업체명", "제품명", "실험방법", "시작일", "상태"
        ])
        self.schedule_table.setColumnHidden(0, True)

        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.doubleClicked.connect(self.accept)
        layout.addWidget(self.schedule_table)

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.load_schedules()

    def load_schedules(self):
        try:
            schedules = Schedule.get_all()
            self.schedule_table.setRowCount(0)

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)
                self.schedule_table.setItem(row, 0, QTableWidgetItem(str(schedule.get('id', ''))))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(schedule.get('client_name', '') or '-'))
                self.schedule_table.setItem(row, 2, QTableWidgetItem(schedule.get('product_name', '') or '-'))

                test_method = schedule.get('test_method', '') or ''
                test_method_text = {
                    'real': '실측', 'acceleration': '가속',
                    'custom_real': '의뢰자(실측)', 'custom_acceleration': '의뢰자(가속)'
                }.get(test_method, '-')
                self.schedule_table.setItem(row, 3, QTableWidgetItem(test_method_text))
                self.schedule_table.setItem(row, 4, QTableWidgetItem(schedule.get('start_date', '') or '-'))

                status = schedule.get('status', 'pending') or 'pending'
                status_text = {
                    'pending': '대기', 'scheduled': '입고예정', 'received': '입고', 'completed': '종료',
                    'in_progress': '입고', 'cancelled': '종료'
                }.get(status, status)
                self.schedule_table.setItem(row, 5, QTableWidgetItem(status_text))
        except Exception as e:
            print(f"스케줄 로드 오류: {e}")

    def search_schedules(self):
        keyword = self.search_input.text().strip()
        schedules = Schedule.search(keyword) if keyword else Schedule.get_all()

        self.schedule_table.setRowCount(0)
        for row, schedule in enumerate(schedules):
            self.schedule_table.insertRow(row)
            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(schedule.get('id', ''))))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(schedule.get('client_name', '') or '-'))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(schedule.get('product_name', '') or '-'))
            test_method = schedule.get('test_method', '') or ''
            test_method_text = {'real': '실측', 'acceleration': '가속', 'custom_real': '의뢰자(실측)', 'custom_acceleration': '의뢰자(가속)'}.get(test_method, '-')
            self.schedule_table.setItem(row, 3, QTableWidgetItem(test_method_text))
            self.schedule_table.setItem(row, 4, QTableWidgetItem(schedule.get('start_date', '') or '-'))
            status = schedule.get('status', 'pending') or 'pending'
            status_text = {
                'pending': '대기', 'scheduled': '입고예정', 'received': '입고', 'completed': '종료',
                'in_progress': '입고', 'cancelled': '종료'
            }.get(status, status)
            self.schedule_table.setItem(row, 5, QTableWidgetItem(status_text))

    def accept(self):
        selected = self.schedule_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.selected_schedule_id = int(self.schedule_table.item(row, 0).text())
        super().accept()


class ScheduleManagementTab(QWidget):
    """스케줄 관리 탭"""

    # 견적서 보기 요청 시그널
    show_estimate_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule = None
        self.memo_history = []  # 메모 이력
        self.initUI()

    def initUI(self):
        """UI 초기화"""
        # 메인 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 스크롤 내부 컨텐츠
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(8)

        # 0. 스케줄 선택 버튼 영역
        self.create_schedule_selector_button(main_layout)

        # 1. 소비기한 설정 실험 계획 (안)
        self.create_info_summary_panel(main_layout)

        # 2. 보관 온도 구간
        self.create_temperature_panel(main_layout)

        # 3. 메모 (1/3) + 메모 이력 (2/3)
        self.create_memo_panel(main_layout)

        # 4. 온도조건별 실험 스케줄
        self.create_experiment_schedule_panel(main_layout)

        scroll.setWidget(content_widget)

        # 최종 레이아웃
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        # 초기 표시 설정 적용
        self.apply_display_settings()

    def create_schedule_selector_button(self, parent_layout):
        """스케줄 선택 버튼 영역"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #34495e; border-radius: 5px; padding: 5px;")
        layout = QHBoxLayout(frame)

        # 현재 선택된 스케줄 표시
        self.selected_schedule_label = QLabel("선택된 스케줄 없음")
        self.selected_schedule_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.selected_schedule_label)

        layout.addStretch()

        # 견적서 보기 버튼
        estimate_btn = QPushButton("견적서 보기")
        estimate_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 15px; font-weight: bold;")
        estimate_btn.clicked.connect(self.show_estimate)
        layout.addWidget(estimate_btn)

        # 표시 설정 버튼
        settings_btn = QPushButton("표시 설정")
        settings_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px 15px; font-weight: bold;")
        settings_btn.clicked.connect(self.open_display_settings)
        layout.addWidget(settings_btn)

        # 스케줄 선택 버튼
        select_btn = QPushButton("스케줄 선택")
        select_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px 20px; font-weight: bold;")
        select_btn.clicked.connect(self.open_schedule_selector)
        layout.addWidget(select_btn)

        parent_layout.addWidget(frame)

    def create_info_summary_panel(self, parent_layout):
        """소비기한 설정 실험 계획 (안) - 4열 레이아웃"""
        group = QGroupBox("1. 소비기한 설정 실험 계획 (안)")
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #3498db; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #2980b9; }
        """)

        grid = QGridLayout(group)
        grid.setSpacing(2)

        # 8열 균등 배분 (라벨+값 4쌍)
        for col in range(8):
            grid.setColumnStretch(col, 1)

        label_style = "font-weight: bold; background-color: #ecf0f1; padding: 3px; border: 1px solid #bdc3c7; font-size: 11px;"
        value_style = "background-color: white; padding: 3px; border: 1px solid #bdc3c7; color: #2c3e50; font-size: 11px;"
        temp_label_style = "font-weight: bold; background-color: #d5f5e3; padding: 3px; border: 1px solid #27ae60; font-size: 11px;"
        temp_value_style = "background-color: white; padding: 3px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 11px;"

        # 행 1: 회사명, 제품명, 식품유형, 보관조건
        self.company_label = self._create_label("회 사 명", label_style)
        grid.addWidget(self.company_label, 0, 0)
        self.company_value = self._create_value_label("-", value_style)
        grid.addWidget(self.company_value, 0, 1)
        self.product_label = self._create_label("제 품 명", label_style)
        grid.addWidget(self.product_label, 0, 2)
        self.product_value = self._create_value_label("-", value_style)
        grid.addWidget(self.product_value, 0, 3)
        self.food_type_label = self._create_label("식품유형", label_style)
        grid.addWidget(self.food_type_label, 0, 4)
        self.food_type_value = self._create_value_label("-", value_style)
        grid.addWidget(self.food_type_value, 0, 5)
        self.storage_label = self._create_label("보관조건", label_style)
        grid.addWidget(self.storage_label, 0, 6)
        self.storage_value = self._create_value_label("-", value_style)
        grid.addWidget(self.storage_value, 0, 7)

        # 행 2: 실험방법, 중간보고서, 연장실험, 시작일
        self.test_method_label = self._create_label("실험방법", label_style)
        grid.addWidget(self.test_method_label, 1, 0)
        self.test_method_value = self._create_value_label("-", value_style)
        grid.addWidget(self.test_method_value, 1, 1)
        self.interim_report_label = self._create_label("중간보고서", label_style)
        grid.addWidget(self.interim_report_label, 1, 2)
        self.interim_report_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_report_value, 1, 3)
        self.extension_label = self._create_label("연장실험", label_style)
        grid.addWidget(self.extension_label, 1, 4)
        self.extension_value = self._create_value_label("-", value_style)
        grid.addWidget(self.extension_value, 1, 5)
        self.start_date_label = self._create_label("시 작 일", label_style)
        grid.addWidget(self.start_date_label, 1, 6)
        self.start_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.start_date_value, 1, 7)

        # 행 3: 소비기한, 실험기간, 샘플링간격, 중간보고일
        self.expiry_label = self._create_label("소비기한", label_style)
        grid.addWidget(self.expiry_label, 2, 0)
        self.expiry_value = self._create_value_label("-", value_style)
        grid.addWidget(self.expiry_value, 2, 1)
        self.period_label = self._create_label("실험기간", label_style)
        grid.addWidget(self.period_label, 2, 2)
        self.period_value = self._create_value_label("-", value_style)
        grid.addWidget(self.period_value, 2, 3)
        self.sampling_interval_label = self._create_label("샘플링간격", label_style)
        grid.addWidget(self.sampling_interval_label, 2, 4)
        self.sampling_interval_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_interval_value, 2, 5)
        self.interim_date_label = self._create_label("중간보고일", label_style)
        grid.addWidget(self.interim_date_label, 2, 6)
        self.interim_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_date_value, 2, 7)

        # 행 4: 1회실험검체량, 포장단위, 필요검체량, 마지막실험일
        self.sample_per_test_label = self._create_label("1회검체량", label_style)
        grid.addWidget(self.sample_per_test_label, 3, 0)
        self.sample_per_test_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sample_per_test_value, 3, 1)
        self.packaging_label = self._create_label("포장단위", label_style)
        grid.addWidget(self.packaging_label, 3, 2)
        self.packaging_value = self._create_value_label("-", value_style)
        grid.addWidget(self.packaging_value, 3, 3)
        self.required_sample_label = self._create_label("필요검체량", label_style)
        grid.addWidget(self.required_sample_label, 3, 4)
        self.required_sample_value = QLineEdit("-")
        self.required_sample_value.setStyleSheet(value_style + " color: #e67e22; font-weight: bold;")
        self.required_sample_value.setAlignment(Qt.AlignCenter)
        self.required_sample_value.setPlaceholderText("개수")
        grid.addWidget(self.required_sample_value, 3, 5)
        self.current_required_sample = 0
        self.last_test_date_label = self._create_label("마지막실험일", label_style)
        grid.addWidget(self.last_test_date_label, 3, 6)
        self.last_test_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.last_test_date_value, 3, 7)

        # 행 5: 상태, 보관온도 (1구간, 2구간, 3구간)
        self.status_label = self._create_label("상    태", label_style)
        grid.addWidget(self.status_label, 4, 0)
        self.status_value = self._create_value_label("-", value_style)
        grid.addWidget(self.status_value, 4, 1)
        self.temp_zone1_label = self._create_label("1 구 간", temp_label_style)
        grid.addWidget(self.temp_zone1_label, 4, 2)
        self.temp_zone1_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone1_value, 4, 3)
        self.temp_zone2_label = self._create_label("2 구 간", temp_label_style)
        grid.addWidget(self.temp_zone2_label, 4, 4)
        self.temp_zone2_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone2_value, 4, 5)
        self.temp_zone3_label = self._create_label("3 구 간", temp_label_style)
        grid.addWidget(self.temp_zone3_label, 4, 6)
        self.temp_zone3_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone3_value, 4, 7)

        # 샘플링횟수는 다른 곳에서 사용하므로 숨겨진 라벨로 유지 (부모 지정 필수)
        self.sampling_count_label = QLabel("샘플링횟수", self)
        self.sampling_count_label.hide()
        self.sampling_count_value = QLabel("-", self)
        self.sampling_count_value.hide()

        parent_layout.addWidget(group)

    def create_temperature_panel(self, parent_layout):
        """보관 온도 구간 패널 - 이제 create_info_summary_panel에 통합됨"""
        # 기존 호환성을 위해 빈 메서드로 유지
        pass

    def create_memo_panel(self, parent_layout):
        """메모 입력 (1/3) + 메모 이력 (2/3)"""
        group = QGroupBox("2. 메모")
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #9b59b6; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #9b59b6; }
        """)
        group.setMaximumHeight(120)  # 메모 영역 전체 높이 제한

        layout = QHBoxLayout(group)

        # 왼쪽: 메모 입력 (1/3)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("새 메모를 입력하세요...")
        self.memo_edit.setMaximumHeight(50)
        left_layout.addWidget(self.memo_edit)

        save_btn = QPushButton("메모 저장")
        save_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 5px;")
        save_btn.clicked.connect(self.save_memo)
        left_layout.addWidget(save_btn)

        # 오른쪽: 메모 이력 (2/3)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.memo_history_list = QListWidget()
        self.memo_history_list.setMaximumHeight(50)
        self.memo_history_list.itemDoubleClicked.connect(self.edit_memo_history)
        right_layout.addWidget(self.memo_history_list)

        edit_memo_btn = QPushButton("메모 수정")
        edit_memo_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")
        edit_memo_btn.clicked.connect(self.edit_selected_memo)
        right_layout.addWidget(edit_memo_btn)

        # 비율 설정 (1:2 - 메모 입력 1/3, 메모 이력 2/3)
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 2)

        parent_layout.addWidget(group)

    def create_experiment_schedule_panel(self, parent_layout):
        """온도조건별 실험 스케줄"""
        group = QGroupBox("3. 온도조건별 실험 스케줄")
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #e67e22; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #e67e22; }
        """)

        layout = QVBoxLayout(group)

        # 단일 테이블
        self.experiment_table = QTableWidget()
        self.experiment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.experiment_table.setMinimumHeight(250)
        self.experiment_table.cellClicked.connect(self.on_experiment_cell_clicked)
        layout.addWidget(self.experiment_table)

        # 항목 추가/삭제 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.add_item_btn = QPushButton("+ 항목 추가")
        self.add_item_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 5px 15px; font-weight: bold;")
        self.add_item_btn.clicked.connect(self.add_test_item)
        btn_layout.addWidget(self.add_item_btn)

        self.remove_item_btn = QPushButton("- 항목 삭제")
        self.remove_item_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 15px; font-weight: bold;")
        self.remove_item_btn.clicked.connect(self.remove_test_item)
        btn_layout.addWidget(self.remove_item_btn)

        self.save_items_btn = QPushButton("💾 항목 저장")
        self.save_items_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 15px; font-weight: bold;")
        self.save_items_btn.clicked.connect(self.save_test_items)
        btn_layout.addWidget(self.save_items_btn)

        layout.addLayout(btn_layout)

        # 추가/삭제된 항목 저장용 리스트
        self.additional_test_items = []
        self.removed_base_items = []

        # 사용자 정의 날짜 저장용 딕셔너리 {column_index: datetime}
        self.custom_dates = {}

        # 비용 요약
        self.create_cost_summary(layout)

        parent_layout.addWidget(group)

    def create_cost_summary(self, parent_layout):
        """비용 요약 (2줄 레이아웃) - 위: 항목비용+계산식, 아래: 1회/회차/보고서/중간"""
        cost_frame = QFrame()
        cost_frame.setStyleSheet("background-color: #fef9e7; border: 1px solid #f39c12; border-radius: 5px; padding: 2px;")
        cost_layout = QHBoxLayout(cost_frame)
        cost_layout.setSpacing(3)
        cost_layout.setContentsMargins(5, 3, 5, 3)

        # 좌측: 2줄 레이아웃
        left_layout = QVBoxLayout()
        left_layout.setSpacing(3)

        # 공통 스타일
        label_style = "font-size: 11px; letter-spacing: 1px;"
        bold_style = "font-size: 11px; letter-spacing: 1px; font-weight: bold;"
        input_style = "font-size: 11px; background-color: white; border: 1px solid #ccc; padding: 1px;"
        formula_style = "font-size: 12px; letter-spacing: 1px; font-weight: bold; color: #d35400; background-color: #fdebd0; padding: 2px 5px; border-radius: 3px;"

        # 1행: 항목별 비용 내역 + 계산식 (옆으로 배열)
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # 항목별 비용 내역
        self.item_cost_detail = QLabel("-")
        self.item_cost_detail.setStyleSheet(f"{label_style} color: #555;")
        row1.addWidget(self.item_cost_detail)

        # 계산식
        self.final_cost_formula = QLabel("-")
        self.final_cost_formula.setStyleSheet(formula_style)
        row1.addWidget(self.final_cost_formula)

        row1.addStretch()
        left_layout.addLayout(row1)

        # 2행: | 1회/회차/보고서/중간
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        separator = QLabel("|")
        separator.setStyleSheet(label_style)
        row2.addWidget(separator)

        lbl1 = QLabel("1회:")
        lbl1.setStyleSheet(label_style)
        row2.addWidget(lbl1)
        self.cost_per_test = QLabel("-")
        self.cost_per_test.setStyleSheet(bold_style)
        row2.addWidget(self.cost_per_test)

        lbl2 = QLabel("회차:")
        lbl2.setStyleSheet(label_style)
        row2.addWidget(lbl2)
        self.total_rounds_cost = QLabel("-")
        self.total_rounds_cost.setStyleSheet(bold_style)
        row2.addWidget(self.total_rounds_cost)

        lbl3 = QLabel("보고서:")
        lbl3.setStyleSheet(label_style)
        row2.addWidget(lbl3)
        self.report_cost_input = QLineEdit("300,000")
        self.report_cost_input.setAlignment(Qt.AlignRight)
        self.report_cost_input.setStyleSheet(input_style)
        self.report_cost_input.setFixedWidth(70)
        self.report_cost_input.textChanged.connect(self.on_cost_input_changed)
        row2.addWidget(self.report_cost_input)

        self.interim_cost_label = QLabel("중간:")
        self.interim_cost_label.setStyleSheet(label_style)
        row2.addWidget(self.interim_cost_label)
        self.interim_report_cost_input = QLineEdit("200,000")
        self.interim_report_cost_input.setAlignment(Qt.AlignRight)
        self.interim_report_cost_input.setStyleSheet(input_style)
        self.interim_report_cost_input.setFixedWidth(70)
        self.interim_report_cost_input.textChanged.connect(self.on_cost_input_changed)
        row2.addWidget(self.interim_report_cost_input)
        self.interim_cost_label.hide()
        self.interim_report_cost_input.hide()

        row2.addStretch()
        left_layout.addLayout(row2)

        cost_layout.addLayout(left_layout)

        # 우측: 공급가 + 세액 = 총계
        self.final_cost_with_vat = QLabel("-")
        self.final_cost_with_vat.setStyleSheet("font-size: 13px; letter-spacing: 2px; font-weight: bold; color: white; background-color: #e67e22; padding: 3px 8px; border-radius: 3px;")
        self.final_cost_with_vat.setAlignment(Qt.AlignCenter)
        self.final_cost_with_vat.setMinimumWidth(220)
        cost_layout.addWidget(self.final_cost_with_vat)

        parent_layout.addWidget(cost_frame)

    def _create_label(self, text, style):
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        return label

    def _create_value_label(self, text, style):
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumWidth(60)
        return label

    def open_schedule_selector(self):
        """스케줄 선택 팝업 열기"""
        dialog = ScheduleSelectDialog(self)
        if dialog.exec_() and dialog.selected_schedule_id:
            self.select_schedule_by_id(dialog.selected_schedule_id)

    def select_schedule_by_id(self, schedule_id):
        """ID로 스케줄 선택"""
        schedule = Schedule.get_by_id(schedule_id)
        if schedule:
            self.current_schedule = schedule
            # 저장된 추가/삭제 항목 로드
            self.load_test_items(schedule_id)
            # 사용자 정의 날짜 초기화
            self.custom_dates = {}
            client_name = schedule.get('client_name', '-') or '-'
            product_name = schedule.get('product_name', '-') or '-'
            self.selected_schedule_label.setText(f"선택: {client_name} - {product_name}")
            self.update_info_panel(schedule)
            self.update_experiment_schedule(schedule)
            self.load_memo_history()

    def update_info_panel(self, schedule):
        """정보 패널 업데이트"""
        self.company_value.setText(schedule.get('client_name', '-') or '-')
        self.product_value.setText(schedule.get('product_name', '-') or '-')

        test_method = schedule.get('test_method', '') or ''
        test_method_text = {'real': '실측실험', 'acceleration': '가속실험', 'custom_real': '의뢰자요청(실측)', 'custom_acceleration': '의뢰자요청(가속)'}.get(test_method, '-')
        self.test_method_value.setText(test_method_text)

        days = schedule.get('test_period_days', 0) or 0
        months = schedule.get('test_period_months', 0) or 0
        years = schedule.get('test_period_years', 0) or 0
        total_days = days + (months * 30) + (years * 365)

        expiry_parts = []
        if years > 0: expiry_parts.append(f"{years}년")
        if months > 0: expiry_parts.append(f"{months}개월")
        if days > 0: expiry_parts.append(f"{days}일")
        self.expiry_value.setText(' '.join(expiry_parts) if expiry_parts else '-')

        storage = schedule.get('storage_condition', '') or ''
        storage_text = {'room_temp': '상온', 'warm': '실온', 'cool': '냉장', 'freeze': '냉동'}.get(storage, '-')
        self.storage_value.setText(storage_text)

        food_type_id = schedule.get('food_type_id', '')
        # 식품유형 ID로 이름 조회
        food_type_name = '-'
        if food_type_id:
            try:
                from models.product_types import ProductType
                food_type = ProductType.get_by_id(food_type_id)
                if food_type:
                    food_type_name = food_type.get('type_name', '-') or '-'
            except Exception as e:
                print(f"식품유형 조회 오류: {e}")
        self.food_type_value.setText(food_type_name)

        if test_method in ['real', 'custom_real']:
            experiment_days = int(total_days * 1.5)
        else:
            experiment_days = total_days // 2 if total_days > 0 else 0

        exp_years = experiment_days // 365
        exp_months = (experiment_days % 365) // 30
        exp_days = experiment_days % 30
        period_parts = []
        if exp_years > 0: period_parts.append(f"{exp_years}년")
        if exp_months > 0: period_parts.append(f"{exp_months}개월")
        if exp_days > 0: period_parts.append(f"{exp_days}일")
        self.period_value.setText(' '.join(period_parts) if period_parts else '-')

        self.interim_report_value.setText("요청" if schedule.get('report_interim') else "미요청")
        self.extension_value.setText("진행" if schedule.get('extension_test') else "미진행")

        sampling_count = schedule.get('sampling_count', 6) or 6

        # 온도 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 샘플링 횟수 × 온도 구간 수
        total_sampling = sampling_count * zone_count
        self.sampling_count_value.setText(f"{total_sampling}회 ({sampling_count}×{zone_count}구간)")

        if experiment_days > 0 and sampling_count > 0:
            interval = experiment_days // sampling_count
            self.sampling_interval_value.setText(f"{interval}일")
        else:
            self.sampling_interval_value.setText('-')

        start_date = schedule.get('start_date', '-') or '-'
        self.start_date_value.setText(start_date)

        # 중간보고서가 요청된 경우에만 중간보고일 표시
        report_interim = schedule.get('report_interim', False)
        if report_interim and start_date != '-' and experiment_days > 0 and sampling_count >= 6:
            try:
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                interval = experiment_days // sampling_count
                interim_date = start + timedelta(days=interval * 6)
                self.interim_date_value.setText(interim_date.strftime('%Y-%m-%d'))
            except:
                self.interim_date_value.setText('-')
        else:
            self.interim_date_value.setText('-')

        if start_date != '-' and experiment_days > 0:
            try:
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                last_date = start + timedelta(days=experiment_days)
                self.last_test_date_value.setText(last_date.strftime('%Y-%m-%d'))
            except:
                self.last_test_date_value.setText('-')
        else:
            self.last_test_date_value.setText('-')

        status = schedule.get('status', 'pending') or 'pending'
        status_text = {
            'pending': '대기', 'scheduled': '입고예정', 'received': '입고', 'completed': '종료',
            'in_progress': '입고', 'cancelled': '종료'
        }.get(status, status)
        self.status_value.setText(status_text)

        # 검체량 계산
        self.update_sample_info(schedule, sampling_count)

        self.update_temperature_panel(schedule)

    def get_test_items_from_food_type(self, schedule):
        """식품유형에서 검사항목 가져오기"""
        default_items = ['관능평가', '세균수', '대장균(정량)', 'pH']

        food_type_id = schedule.get('food_type_id')
        if not food_type_id:
            base_items = default_items
        else:
            try:
                food_type = ProductType.get_by_id(food_type_id)
                if food_type:
                    test_items_str = food_type.get('test_items', '') or ''
                    if test_items_str:
                        # 쉼표로 구분된 문자열을 리스트로 변환
                        items = [item.strip() for item in test_items_str.split(',') if item.strip()]
                        if items:
                            base_items = items
                        else:
                            base_items = default_items
                    else:
                        base_items = default_items
                else:
                    base_items = default_items
            except Exception as e:
                print(f"식품유형에서 검사항목 로드 오류: {e}")
                base_items = default_items

        # 삭제된 기본 항목 제외
        return [item for item in base_items if item not in self.removed_base_items]

    def update_temperature_panel(self, schedule):
        """온도 구간 패널 업데이트"""
        test_method = schedule.get('test_method', '') or ''
        storage = schedule.get('storage_condition', '') or ''
        custom_temps = schedule.get('custom_temperatures', '') or ''

        real_temps = {'room_temp': '15℃', 'warm': '25℃', 'cool': '10℃', 'freeze': '-18℃'}
        accel_temps = {'room_temp': ['15℃', '25℃', '35℃'], 'warm': ['25℃', '35℃', '45℃'], 'cool': ['5℃', '10℃', '15℃'], 'freeze': ['-6℃', '-12℃', '-18℃']}

        self.temp_zone1_value.setText('-')
        self.temp_zone2_value.setText('-')
        self.temp_zone3_value.setText('-')

        if test_method in ['real', 'custom_real']:
            if custom_temps:
                temps = custom_temps.split(',')
                self.temp_zone1_value.setText(temps[0] + '℃' if temps else '-')
                if len(temps) > 1: self.temp_zone2_value.setText(temps[1] + '℃')
                if len(temps) > 2: self.temp_zone3_value.setText(temps[2] + '℃')
            else:
                self.temp_zone1_value.setText(real_temps.get(storage, '-'))
        elif test_method in ['acceleration', 'custom_acceleration']:
            if custom_temps:
                temps = custom_temps.split(',')
                self.temp_zone1_value.setText(temps[0] + '℃' if len(temps) > 0 else '-')
                self.temp_zone2_value.setText(temps[1] + '℃' if len(temps) > 1 else '-')
                self.temp_zone3_value.setText(temps[2] + '℃' if len(temps) > 2 else '-')
            else:
                temps = accel_temps.get(storage, ['-', '-', '-'])
                self.temp_zone1_value.setText(temps[0])
                self.temp_zone2_value.setText(temps[1])
                self.temp_zone3_value.setText(temps[2])

    def update_sample_info(self, schedule, sampling_count, zone_count=None):
        """검체량 정보 업데이트"""
        try:
            import math

            # 식품유형에서 검사항목 가져오기 + 추가된 항목
            base_items = self.get_test_items_from_food_type(schedule)
            test_items = base_items + self.additional_test_items

            # 온도 구간 수 결정
            if zone_count is None:
                test_method = schedule.get('test_method', '') or ''
                if test_method in ['real', 'custom_real']:
                    zone_count = 1
                else:
                    zone_count = 3

            # 수수료 정보에서 sample_quantity 가져오기 (식품유형의 검사항목 기반)
            sample_per_test = 0
            try:
                all_fees = Fee.get_all()
                for fee in all_fees:
                    if fee['test_item'] in test_items:
                        sample_qty = fee['sample_quantity'] or 0
                        sample_per_test += sample_qty
            except Exception as e:
                print(f"수수료 정보 로드 오류: {e}")

            # 1회 실험 검체량 표시
            self.sample_per_test_value.setText(f"{sample_per_test}g")

            # 포장단위 가져오기
            packaging_weight = schedule.get('packaging_weight', 0) or 0
            packaging_unit = schedule.get('packaging_unit', 'g') or 'g'

            # kg인 경우 g로 변환
            packaging_weight_g = packaging_weight * 1000 if packaging_unit == 'kg' else packaging_weight

            # 포장단위 표시
            self.packaging_value.setText(f"{packaging_weight}{packaging_unit}")

            # 총 샘플링 횟수 (샘플링횟수 × 온도구간수)
            total_sampling = sampling_count * zone_count

            # 필요 검체량 계산 (개수로 표현)
            if packaging_weight_g > 0:
                if sample_per_test > packaging_weight_g:
                    # 1회 검체량이 포장단위보다 큰 경우
                    # 1회당 필요한 포장 수 = ceil(1회검체량 / 포장단위)
                    packages_per_test = math.ceil(sample_per_test / packaging_weight_g)
                    required_packages = total_sampling * packages_per_test
                else:
                    # 1회 검체량이 포장단위 이하인 경우
                    # 1회당 1개 필요
                    required_packages = total_sampling

                # 개수로 표시
                self.required_sample_value.setText(f"{required_packages}개")
                self.current_required_sample = required_packages
            else:
                self.required_sample_value.setText("-")
                self.current_required_sample = 0

        except Exception as e:
            print(f"검체량 정보 업데이트 오류: {e}")
            self.sample_per_test_value.setText("-")
            self.packaging_value.setText("-")
            self.required_sample_value.setText("-")
            self.current_required_sample = 0

    def load_memo_history(self):
        """메모 이력 로드"""
        self.memo_history_list.clear()
        if not self.current_schedule:
            return

        memo = self.current_schedule.get('memo', '') or ''
        if memo:
            # 메모를 줄바꿈으로 분리하여 이력으로 표시
            lines = memo.strip().split('\n')
            for line in lines:
                if line.strip():
                    item = QListWidgetItem(line.strip())
                    self.memo_history_list.addItem(item)

    def edit_memo_history(self, item):
        """메모 이력 더블클릭 시 편집"""
        self.memo_edit.setText(item.text())

    def edit_selected_memo(self):
        """선택된 메모를 수정창에 로드"""
        current_item = self.memo_history_list.currentItem()
        if current_item:
            self.memo_edit.setText(current_item.text())
        else:
            QMessageBox.warning(self, "선택 필요", "수정할 메모를 선택하세요.")

    def save_memo(self):
        """메모 저장"""
        if not self.current_schedule:
            QMessageBox.warning(self, "저장 실패", "먼저 스케줄을 선택하세요.")
            return

        new_memo = self.memo_edit.toPlainText().strip()
        if not new_memo:
            QMessageBox.warning(self, "저장 실패", "메모 내용을 입력하세요.")
            return

        schedule_id = self.current_schedule.get('id')
        existing_memo = self.current_schedule.get('memo', '') or ''

        # 타임스탬프 추가하여 저장
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        formatted_memo = f"[{timestamp}] {new_memo}"

        # 기존 메모에 추가
        if existing_memo:
            updated_memo = f"{existing_memo}\n{formatted_memo}"
        else:
            updated_memo = formatted_memo

        try:
            success = Schedule.update_memo(schedule_id, updated_memo)
            if success:
                self.current_schedule['memo'] = updated_memo
                self.memo_edit.clear()
                self.load_memo_history()
                QMessageBox.information(self, "저장 완료", "메모가 저장되었습니다.")
            else:
                QMessageBox.warning(self, "저장 실패", "메모 저장에 실패했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"메모 저장 중 오류:\n{str(e)}")

    def update_experiment_schedule(self, schedule):
        """온도조건별 실험 스케줄 테이블 업데이트"""
        test_method = schedule.get('test_method', '') or ''
        sampling_count = schedule.get('sampling_count', 6) or 6

        days = schedule.get('test_period_days', 0) or 0
        months = schedule.get('test_period_months', 0) or 0
        years = schedule.get('test_period_years', 0) or 0
        total_days = days + (months * 30) + (years * 365)

        if test_method in ['real', 'custom_real']:
            experiment_days = int(total_days * 1.5)
        else:
            experiment_days = total_days // 2 if total_days > 0 else 0

        # 시작일(0일)과 마지막실험일(experiment_days) 사이를 균등 분배
        # 첫 회차(0일)부터 마지막 회차(experiment_days)까지
        if sampling_count > 1:
            interval_days = experiment_days / (sampling_count - 1)
        else:
            interval_days = 0

        # 시작일 파싱
        start_date_str = schedule.get('start_date', '')
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except:
                pass

        # 식품유형에서 검사항목 가져오기 + 추가된 항목
        base_items = self.get_test_items_from_food_type(schedule)
        test_items = base_items + self.additional_test_items

        fees = {}
        sample_quantities = {}
        try:
            all_fees = Fee.get_all()
            for fee in all_fees:
                fees[fee['test_item']] = fee['price']
                sample_quantities[fee['test_item']] = fee['sample_quantity'] or 0
        except:
            pass

        # 단일 테이블 업데이트
        table = self.experiment_table
        col_count = sampling_count + 2
        table.setColumnCount(col_count)
        headers = ['구 분'] + [f'{i+1}회' for i in range(sampling_count)] + ['가격']
        table.setHorizontalHeaderLabels(headers)

        # 행 수: 날짜 + 제조후시간 + 검사항목들 + 1회기준
        row_count = 2 + len(test_items) + 1
        table.setRowCount(row_count)

        # 행 0: 날짜
        date_label = QTableWidgetItem("날짜")
        date_label.setBackground(QColor('#ADD8E6'))
        table.setItem(0, 0, date_label)

        # 각 회차별 날짜 저장 (제조후 일수 계산용)
        sample_dates = {}

        for i in range(sampling_count):
            col_idx = i + 1

            # 사용자 정의 날짜가 있으면 우선 사용
            if col_idx in self.custom_dates:
                sample_date = self.custom_dates[col_idx]
                date_value = sample_date.strftime('%m-%d')
                sample_dates[col_idx] = sample_date
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setBackground(QColor('#FFE4B5'))  # 수정된 날짜 강조
            elif start_date:
                from datetime import timedelta
                # 마지막 회차는 정확히 experiment_days, 그 외는 균등 분배
                if i == sampling_count - 1:
                    days_offset = experiment_days
                else:
                    days_offset = round(i * interval_days)
                sample_date = start_date + timedelta(days=days_offset)
                date_value = sample_date.strftime('%m-%d')  # 짧은 날짜 형식
                sample_dates[col_idx] = sample_date
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setBackground(QColor('#E6F3FF'))
            else:
                date_value = "-"
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setBackground(QColor('#E6F3FF'))

            table.setItem(0, col_idx, date_item)
        table.setItem(0, col_count - 1, QTableWidgetItem(""))

        # 행 1: 제조후 일수
        time_item = QTableWidgetItem("제조후 일수")
        time_item.setBackground(QColor('#90EE90'))
        table.setItem(1, 0, time_item)

        for i in range(sampling_count):
            col_idx = i + 1

            # sample_dates에 날짜가 있으면 시작일로부터 일수 계산
            if col_idx in sample_dates and start_date:
                days_elapsed = (sample_dates[col_idx] - start_date).days
                # 사용자 정의 날짜인 경우 강조 표시
                is_custom = col_idx in self.custom_dates
            else:
                # 마지막 회차는 정확히 experiment_days
                if i == sampling_count - 1:
                    days_elapsed = experiment_days
                else:
                    days_elapsed = int(round(i * interval_days))
                is_custom = False

            time_value = f"{days_elapsed}일"
            item = QTableWidgetItem(time_value)
            item.setTextAlignment(Qt.AlignCenter)
            if is_custom:
                item.setBackground(QColor('#FFE4B5'))  # 수정된 값 강조
            table.setItem(1, col_idx, item)
        table.setItem(1, col_count - 1, QTableWidgetItem(""))

        total_price_per_test = 0
        for row_idx, test_item in enumerate(test_items):
            item_label = QTableWidgetItem(test_item)
            item_label.setBackground(QColor('#90EE90'))
            table.setItem(row_idx + 2, 0, item_label)  # +2 because of date and time rows

            for i in range(sampling_count):
                check_item = QTableWidgetItem("O")
                check_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx + 2, i + 1, check_item)

            price = int(fees.get(test_item, 0))
            total_price_per_test += price
            price_item = QTableWidgetItem(f"{price:,}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row_idx + 2, col_count - 1, price_item)

        basis_item = QTableWidgetItem("(1회 기준)")
        basis_item.setBackground(QColor('#FFFF99'))
        table.setItem(row_count - 1, 0, basis_item)

        for i in range(sampling_count):
            cost_item = QTableWidgetItem(f"{total_price_per_test:,}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            cost_item.setBackground(QColor('#FFFF99'))
            table.setItem(row_count - 1, i + 1, cost_item)

        total_item = QTableWidgetItem(f"{total_price_per_test:,}")
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_item.setBackground(QColor('#FFFF99'))
        table.setItem(row_count - 1, col_count - 1, total_item)

        # 모든 열 균등 배분
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.update_cost_summary(schedule, test_items, fees, sampling_count)

    def update_cost_summary(self, schedule, test_items, fees, sampling_count):
        """비용 요약 업데이트"""
        test_method = schedule.get('test_method', '') or ''

        # 실험 방법에 따른 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 항목별 비용 내역 (초기: 모두 O 체크 상태이므로 sampling_count회)
        detail_parts = []
        for test_item in test_items:
            unit_price = int(fees.get(test_item, 0))
            total_cost = unit_price * sampling_count
            detail_parts.append(f"{test_item}({sampling_count}회)={total_cost:,}원")
        self.item_cost_detail.setText(" | ".join(detail_parts))

        # 1. 1회 기준 (합계) - 모든 검사항목 합계
        cost_per_test = int(sum(fees.get(item, 0) for item in test_items))
        self.cost_per_test.setText(f"{cost_per_test:,}원")

        # 2. 회차별 총계 (합계) - 초기 로드 시 모든 O가 체크되어 있으므로 1회기준 × 샘플링횟수
        total_rounds_cost = int(cost_per_test * sampling_count)
        self.total_rounds_cost.setText(f"{total_rounds_cost:,}원")

        # 3. 보고서 비용: 실측/의뢰자요청(실측) = 200,000원, 가속/의뢰자요청(가속) = 300,000원
        if test_method in ['real', 'custom_real']:
            report_cost = 200000
        elif test_method in ['acceleration', 'custom_acceleration']:
            report_cost = 300000
        else:
            report_cost = 200000  # 기본값
        self.report_cost_input.setText(f"{report_cost:,}")

        # 3-1. 중간 보고서 비용 (중간보고서 체크 시에만 표시)
        report_interim = schedule.get('report_interim', False)
        interim_report_cost = 0
        if report_interim:
            interim_report_cost = 200000
            self.interim_report_cost_input.setText(f"{interim_report_cost:,}")
            self.interim_cost_label.show()
            self.interim_report_cost_input.show()
        else:
            self.interim_cost_label.hide()
            self.interim_report_cost_input.hide()

        # 4. 최종비용 (부가세별도) - 계산식 표시
        final_cost_no_vat = int(total_rounds_cost * zone_count + report_cost + interim_report_cost)
        if interim_report_cost > 0:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} + {interim_report_cost:,} = {final_cost_no_vat:,}원"
        else:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} = {final_cost_no_vat:,}원"
        self.final_cost_formula.setText(formula_text)

        # 5. 최종비용 (부가세 포함) - 10% 부가세
        vat = int(final_cost_no_vat * 0.1)
        final_cost_with_vat = final_cost_no_vat + vat
        self.final_cost_with_vat.setText(f"{final_cost_no_vat:,} + {vat:,} = {final_cost_with_vat:,}원")

    def show_estimate(self):
        """견적서 보기 버튼 클릭 시 처리"""
        if not self.current_schedule:
            QMessageBox.warning(self, "알림", "먼저 스케줄을 선택해주세요.")
            return

        # DB에서 최신 스케줄 데이터 가져오기
        schedule_id = self.current_schedule.get('id')
        if schedule_id:
            from models.schedules import Schedule
            fresh_schedule = Schedule.get_by_id(schedule_id)
            if fresh_schedule:
                schedule_data = dict(fresh_schedule)
            else:
                schedule_data = dict(self.current_schedule)
        else:
            schedule_data = dict(self.current_schedule)

        # 식품유형 이름 및 검사항목 추가
        if schedule_data.get('food_type_id'):
            food_type = ProductType.get_by_id(schedule_data['food_type_id'])
            if food_type:
                schedule_data['food_type_name'] = food_type.get('type_name', '')
                # 기본 검사항목 + 추가 검사항목
                base_items = food_type.get('test_items', '')
                if self.additional_test_items:
                    additional = ', '.join(self.additional_test_items)
                    if base_items:
                        schedule_data['test_items'] = f"{base_items}, {additional}"
                    else:
                        schedule_data['test_items'] = additional
                else:
                    schedule_data['test_items'] = base_items

        # 업체명 추가
        if schedule_data.get('client_id'):
            from models.clients import Client
            client = Client.get_by_id(schedule_data['client_id'])
            if client:
                schedule_data['client_name'] = client.get('name', '')

        # 스케줄 관리에서 계산된 비용 정보 추가
        try:
            # 보고서 비용
            report_cost = int(self.report_cost_input.text().replace(',', '').replace('원', ''))
            schedule_data['report_cost'] = report_cost

            # 중간 보고서 비용
            if self.interim_report_cost_input.isVisible():
                interim_cost = int(self.interim_report_cost_input.text().replace(',', '').replace('원', ''))
                schedule_data['interim_report_cost'] = interim_cost
            else:
                schedule_data['interim_report_cost'] = 0

            # 1회 검사비
            cost_per_test_text = self.cost_per_test.text().replace(',', '').replace('원', '')
            if cost_per_test_text and cost_per_test_text != '-':
                schedule_data['cost_per_test'] = int(cost_per_test_text)

            # 회차 총계
            total_rounds_text = self.total_rounds_cost.text().replace(',', '').replace('원', '')
            if total_rounds_text and total_rounds_text != '-':
                schedule_data['total_rounds_cost'] = int(total_rounds_text)

        except Exception as e:
            print(f"비용 정보 추가 중 오류: {e}")

        # 시그널 발생
        self.show_estimate_requested.emit(schedule_data)

    def open_display_settings(self):
        """표시 설정 다이얼로그 열기"""
        dialog = DisplaySettingsDialog(self)
        if dialog.exec_():
            # 설정이 저장되면 화면 새로고침
            self.apply_display_settings()

    def get_display_settings(self):
        """데이터베이스에서 표시 설정 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_display_fields'")
            result = cursor.fetchone()
            conn.close()

            if result:
                return result['value'].split(',')
            else:
                # 기본값: 모든 필드 표시
                return [opt[0] for opt in DisplaySettingsDialog.FIELD_OPTIONS]
        except Exception as e:
            print(f"표시 설정 로드 오류: {e}")
            return [opt[0] for opt in DisplaySettingsDialog.FIELD_OPTIONS]

    def apply_display_settings(self):
        """표시 설정을 UI에 적용"""
        visible_fields = self.get_display_settings()

        # 필드 키와 해당 위젯 매핑
        field_widgets = {
            'company': (self.company_label, self.company_value),
            'test_method': (self.test_method_label, self.test_method_value),
            'product': (self.product_label, self.product_value),
            'expiry': (self.expiry_label, self.expiry_value),
            'storage': (self.storage_label, self.storage_value),
            'food_type': (self.food_type_label, self.food_type_value),
            'period': (self.period_label, self.period_value),
            'interim_report': (self.interim_report_label, self.interim_report_value),
            'extension': (self.extension_label, self.extension_value),
            'sampling_count': (self.sampling_count_label, self.sampling_count_value),
            'sampling_interval': (self.sampling_interval_label, self.sampling_interval_value),
            'start_date': (self.start_date_label, self.start_date_value),
            'interim_date': (self.interim_date_label, self.interim_date_value),
            'last_test_date': (self.last_test_date_label, self.last_test_date_value),
            'status': (self.status_label, self.status_value),
            'sample_per_test': (self.sample_per_test_label, self.sample_per_test_value),
            'packaging': (self.packaging_label, self.packaging_value),
            'required_sample': (self.required_sample_label, self.required_sample_value),
            'temp_zone1': (self.temp_zone1_label, self.temp_zone1_value),
            'temp_zone2': (self.temp_zone2_label, self.temp_zone2_value),
            'temp_zone3': (self.temp_zone3_label, self.temp_zone3_value),
        }

        for field_key, (label_widget, value_widget) in field_widgets.items():
            is_visible = field_key in visible_fields
            label_widget.setVisible(is_visible)
            value_widget.setVisible(is_visible)

    def add_test_item(self):
        """검사항목 추가"""
        if not self.current_schedule:
            QMessageBox.warning(self, "추가 실패", "먼저 스케줄을 선택하세요.")
            return

        # 현재 테이블에 있는 항목들 수집
        current_items = self.get_test_items_from_food_type(self.current_schedule) + self.additional_test_items

        # 항목 선택 다이얼로그
        dialog = TestItemSelectDialog(self, exclude_items=current_items)
        if dialog.exec_() and dialog.selected_item:
            # 추가된 항목 저장
            self.additional_test_items.append(dialog.selected_item)

            # 테이블 새로고침
            self.update_experiment_schedule(self.current_schedule)

            # 검체량 정보 업데이트
            sampling_count = self.current_schedule.get('sampling_count', 6) or 6
            self.update_sample_info(self.current_schedule, sampling_count)

            QMessageBox.information(self, "추가 완료", f"'{dialog.selected_item}' 항목이 추가되었습니다.")

    def remove_test_item(self):
        """검사항목 삭제"""
        if not self.current_schedule:
            QMessageBox.warning(self, "삭제 실패", "먼저 스케줄을 선택하세요.")
            return

        # 현재 표시된 모든 항목 수집 (기본 + 추가)
        base_items = self.get_test_items_from_food_type(self.current_schedule)
        all_current_items = base_items + self.additional_test_items

        if not all_current_items:
            QMessageBox.warning(self, "삭제 실패", "삭제할 항목이 없습니다.")
            return

        # 모든 항목 중에서 선택하여 삭제
        from PyQt5.QtWidgets import QInputDialog
        item, ok = QInputDialog.getItem(
            self, "항목 삭제", "삭제할 항목을 선택하세요:",
            all_current_items, 0, False
        )

        if ok and item:
            if item in self.additional_test_items:
                # 추가된 항목 삭제
                self.additional_test_items.remove(item)
            else:
                # 기본 항목 삭제 (removed_base_items에 추가)
                self.removed_base_items.append(item)

            # 테이블 새로고침
            self.update_experiment_schedule(self.current_schedule)

            # 검체량 정보 업데이트
            sampling_count = self.current_schedule.get('sampling_count', 6) or 6
            self.update_sample_info(self.current_schedule, sampling_count)

            QMessageBox.information(self, "삭제 완료", f"'{item}' 항목이 삭제되었습니다.")

    def save_test_items(self):
        """검사항목 변경사항을 데이터베이스에 저장"""
        if not self.current_schedule:
            QMessageBox.warning(self, "저장 실패", "먼저 스케줄을 선택하세요.")
            return

        schedule_id = self.current_schedule.get('id')
        if not schedule_id:
            QMessageBox.warning(self, "저장 실패", "스케줄 ID를 찾을 수 없습니다.")
            return

        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            # schedule_test_items 테이블 생성 (없으면)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule_test_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER NOT NULL,
                    additional_items TEXT,
                    removed_items TEXT,
                    UNIQUE(schedule_id)
                )
            """)

            # 추가/삭제된 항목을 콤마로 구분하여 저장
            additional_str = ','.join(self.additional_test_items) if self.additional_test_items else ''
            removed_str = ','.join(self.removed_base_items) if self.removed_base_items else ''

            # 기존 데이터가 있으면 업데이트, 없으면 삽입
            cursor.execute("""
                INSERT OR REPLACE INTO schedule_test_items (schedule_id, additional_items, removed_items)
                VALUES (?, ?, ?)
            """, (schedule_id, additional_str, removed_str))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "저장 완료", "검사항목 변경사항이 저장되었습니다.")
            log_message('ScheduleManagementTab', f'검사항목 저장 완료: schedule_id={schedule_id}')

        except Exception as e:
            log_exception('ScheduleManagementTab', f'검사항목 저장 오류: {str(e)}')
            QMessageBox.critical(self, "저장 오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")

    def load_test_items(self, schedule_id):
        """데이터베이스에서 저장된 검사항목 변경사항 로드"""
        self.additional_test_items = []
        self.removed_base_items = []

        if not schedule_id:
            return

        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schedule_test_items'
            """)
            if not cursor.fetchone():
                conn.close()
                return

            # 저장된 항목 로드
            cursor.execute("""
                SELECT additional_items, removed_items
                FROM schedule_test_items
                WHERE schedule_id = ?
            """, (schedule_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                additional_str = result['additional_items'] or ''
                removed_str = result['removed_items'] or ''

                if additional_str:
                    self.additional_test_items = [item.strip() for item in additional_str.split(',') if item.strip()]
                if removed_str:
                    self.removed_base_items = [item.strip() for item in removed_str.split(',') if item.strip()]

                log_message('ScheduleManagementTab', f'검사항목 로드 완료: 추가={len(self.additional_test_items)}, 삭제={len(self.removed_base_items)}')

        except Exception as e:
            log_exception('ScheduleManagementTab', f'검사항목 로드 오류: {str(e)}')

    def on_experiment_cell_clicked(self, row, col):
        """실험 테이블 셀 클릭 시 O/X 토글 또는 날짜 수정"""
        if not self.current_schedule:
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6

        # 행 0: 날짜 클릭 시 달력으로 날짜 수정
        if row == 0 and col >= 1 and col <= sampling_count:
            self.edit_date_with_calendar(col)
            return

        # 검사항목 행 범위 확인 (행 2부터 마지막 행-1까지가 검사항목)
        # 행 0: 날짜, 행 1: 제조후 일수, 행 2~n-1: 검사항목, 행 n: 1회 기준
        test_item_start_row = 2
        test_item_end_row = table.rowCount() - 2  # 마지막 행(1회 기준) 제외

        # 검사항목 셀만 토글 가능 (열 1~sampling_count)
        if row < test_item_start_row or row > test_item_end_row:
            return
        if col < 1 or col > sampling_count:
            return

        item = table.item(row, col)
        if item is None:
            return

        current_value = item.text()

        # O → X → O 순환
        if current_value == 'O':
            new_value = 'X'
            item.setForeground(QBrush(QColor('#e74c3c')))  # 빨간색
        else:
            new_value = 'O'
            item.setForeground(QBrush(QColor('#000000')))  # 검정색

        item.setText(new_value)

        # 비용 재계산
        self.recalculate_costs()

    def edit_date_with_calendar(self, col):
        """달력을 통해 날짜 수정"""
        table = self.experiment_table
        current_date_text = table.item(0, col).text() if table.item(0, col) else "-"

        # 시작일 가져오기
        start_date_str = self.current_schedule.get('start_date', '')
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except:
                pass

        # 현재 표시된 날짜를 파싱하여 달력 초기값으로 설정
        current_date = None
        if current_date_text != "-":
            try:
                # MM-DD 형식이면 현재 연도 추가
                if len(current_date_text) == 5:
                    year = datetime.now().year
                    # 시작일이 있으면 그 연도 사용
                    if start_date:
                        year = start_date.year
                    current_date = datetime.strptime(f"{year}-{current_date_text}", '%Y-%m-%d')
                else:
                    current_date = datetime.strptime(current_date_text, '%Y-%m-%d')
            except:
                current_date = start_date

        # 날짜 선택 다이얼로그 표시
        dialog = DateSelectDialog(self, current_date=current_date, title=f"{col}회차 날짜 선택")
        if dialog.exec_() and dialog.selected_date:
            # 선택된 날짜 저장
            self.custom_dates[col] = dialog.selected_date

            # 테이블 날짜 업데이트
            date_item = table.item(0, col)
            if date_item:
                date_item.setText(dialog.selected_date.strftime('%m-%d'))
                date_item.setBackground(QColor('#FFE4B5'))  # 수정된 날짜 강조

            # 제조후 일수 업데이트
            if start_date:
                days_elapsed = (dialog.selected_date - start_date).days
                time_item = table.item(1, col)
                if time_item:
                    time_item.setText(f"{days_elapsed}일")
                    time_item.setBackground(QColor('#FFE4B5'))  # 수정된 값 강조

    def recalculate_costs(self):
        """셀 변경 시 비용 재계산"""
        if not self.current_schedule:
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        test_method = self.current_schedule.get('test_method', '') or ''

        # 수수료 정보 로드
        fees = {}
        try:
            all_fees = Fee.get_all()
            for fee in all_fees:
                fees[fee['test_item']] = fee['price']
        except:
            pass

        # 식품유형에서 검사항목 가져오기 + 추가된 항목
        base_items = self.get_test_items_from_food_type(self.current_schedule)
        test_items = base_items + self.additional_test_items

        # 검사항목 행 시작 (행 2부터)
        test_item_start_row = 2

        # 각 검사항목별 O 체크 수 및 비용 계산
        item_o_counts = {}  # {항목명: O 체크 수}
        item_costs = {}     # {항목명: 총 비용}

        # 각 회차별 활성 항목 비용 합계 계산
        column_costs = []  # 각 회차별 비용
        for col_idx in range(1, sampling_count + 1):
            col_cost = 0
            for row_idx, test_item in enumerate(test_items):
                item = table.item(test_item_start_row + row_idx, col_idx)
                if item and item.text() == 'O':
                    col_cost += int(fees.get(test_item, 0))
                    # 항목별 O 체크 수 카운트
                    item_o_counts[test_item] = item_o_counts.get(test_item, 0) + 1
            column_costs.append(col_cost)

        # 항목별 총 비용 계산 (O 체크 수 × 단가)
        for test_item in test_items:
            o_count = item_o_counts.get(test_item, 0)
            unit_price = int(fees.get(test_item, 0))
            item_costs[test_item] = o_count * unit_price

        # 항목별 비용 내역 텍스트 생성
        detail_parts = []
        for test_item in test_items:
            o_count = item_o_counts.get(test_item, 0)
            total_cost = item_costs.get(test_item, 0)
            if o_count > 0:
                detail_parts.append(f"{test_item}({o_count}회)={total_cost:,}원")
            else:
                detail_parts.append(f"{test_item}(제외)")

        self.item_cost_detail.setText(" | ".join(detail_parts))

        # (1회 기준) 행 업데이트
        basis_row = table.rowCount() - 1
        for i, col_cost in enumerate(column_costs):
            cost_item = table.item(basis_row, i + 1)
            if cost_item:
                cost_item.setText(f"{col_cost:,}")

        # 실험 방법에 따른 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 1. 1회 기준 (합계) - 모든 검사항목 합계
        cost_per_test = int(sum(fees.get(item, 0) for item in test_items))
        self.cost_per_test.setText(f"{cost_per_test:,}원")

        # 2. 회차별 총계 (합계) - 모든 활성 항목의 합계
        total_rounds_cost = sum(column_costs)
        self.total_rounds_cost.setText(f"{total_rounds_cost:,}원")

        # 3. 보고서 비용 (입력 필드에서 값 가져오기)
        try:
            report_cost = int(self.report_cost_input.text().replace(',', '').replace('원', ''))
        except:
            report_cost = 200000

        # 3-1. 중간 보고서 비용 (표시 중인 경우에만 계산에 포함)
        interim_report_cost = 0
        if self.interim_report_cost_input.isVisible():
            try:
                interim_report_cost = int(self.interim_report_cost_input.text().replace(',', '').replace('원', ''))
            except:
                interim_report_cost = 200000

        # 4. 최종비용 (부가세별도) - 계산식 표시
        # 실측: 회차별총계 × 1 + 보고서비용 + 중간보고서비용
        # 가속: 회차별총계 × 3 + 보고서비용 + 중간보고서비용
        final_cost_no_vat = int(total_rounds_cost * zone_count + report_cost + interim_report_cost)
        if interim_report_cost > 0:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} + {interim_report_cost:,} = {final_cost_no_vat:,}원"
        else:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} = {final_cost_no_vat:,}원"
        self.final_cost_formula.setText(formula_text)

        # 5. 최종비용 (부가세 포함) - 10% 부가세
        vat = int(final_cost_no_vat * 0.1)
        final_cost_with_vat = final_cost_no_vat + vat
        self.final_cost_with_vat.setText(f"{final_cost_no_vat:,} + {vat:,} = {final_cost_with_vat:,}원")

    def on_cost_input_changed(self):
        """보고서 비용 입력 변경 시 총비용 재계산"""
        if not self.current_schedule:
            return

        # 현재 회차별 총계 가져오기
        try:
            total_rounds_text = self.total_rounds_cost.text().replace(',', '').replace('원', '')
            total_rounds_cost = int(total_rounds_text)
        except:
            return

        # 실험 방법에 따른 구간 수 결정
        test_method = self.current_schedule.get('test_method', 'real')
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 보고서 비용 가져오기
        try:
            report_cost = int(self.report_cost_input.text().replace(',', '').replace('원', ''))
        except:
            report_cost = 0

        # 중간 보고서 비용 가져오기 (표시 중인 경우에만)
        interim_report_cost = 0
        if self.interim_report_cost_input.isVisible():
            try:
                interim_report_cost = int(self.interim_report_cost_input.text().replace(',', '').replace('원', ''))
            except:
                interim_report_cost = 0

        # 최종비용 계산 및 표시
        final_cost_no_vat = int(total_rounds_cost * zone_count + report_cost + interim_report_cost)
        if interim_report_cost > 0:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} + {interim_report_cost:,} = {final_cost_no_vat:,}원"
        else:
            formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} = {final_cost_no_vat:,}원"
        self.final_cost_formula.setText(formula_text)

        # 부가세 포함 금액
        vat = int(final_cost_no_vat * 0.1)
        final_cost_with_vat = final_cost_no_vat + vat
        self.final_cost_with_vat.setText(f"{final_cost_no_vat:,} + {vat:,} = {final_cost_with_vat:,}원")
