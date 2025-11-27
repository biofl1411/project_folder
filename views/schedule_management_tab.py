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
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QColor, QFont, QBrush
import pandas as pd
from datetime import datetime

from models.schedules import Schedule
from models.fees import Fee
from models.product_types import ProductType


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
            all_fees = Fee.get_all()
            self.all_items = []

            for fee in all_fees:
                test_item = fee['test_item']
                # 이미 추가된 항목은 제외
                if test_item not in self.exclude_items:
                    self.all_items.append({
                        'test_item': test_item,
                        'food_category': fee['food_category'] or '',
                        'price': fee['price'] or 0,
                        'sample_quantity': fee['sample_quantity'] or 0
                    })

            self.display_items(self.all_items)
        except Exception as e:
            print(f"검사항목 로드 오류: {e}")

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
        if not text:
            self.display_items(self.all_items)
        else:
            filtered = [item for item in self.all_items if text.lower() in item['test_item'].lower()]
            self.display_items(filtered)

    def accept(self):
        selected = self.item_table.selectedIndexes()
        if selected:
            row = selected[0].row()
            self.selected_item = self.item_table.item(row, 0).text()
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
        """소비기한 설정 실험 계획 (안)"""
        group = QGroupBox("1. 소비기한 설정 실험 계획 (안)")
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #3498db; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #2980b9; }
        """)

        grid = QGridLayout(group)
        grid.setSpacing(2)

        # 열 균등 배분
        for col in range(6):
            grid.setColumnStretch(col, 1)

        label_style = "font-weight: bold; background-color: #ecf0f1; padding: 4px; border: 1px solid #bdc3c7; font-size: 13px;"
        value_style = "background-color: white; padding: 4px; border: 1px solid #bdc3c7; color: #2c3e50; font-size: 13px;"

        # 행 1
        self.company_label = self._create_label("회사명", label_style)
        grid.addWidget(self.company_label, 0, 0)
        self.company_value = self._create_value_label("-", value_style)
        grid.addWidget(self.company_value, 0, 1)
        self.test_method_label = self._create_label("실험방법", label_style)
        grid.addWidget(self.test_method_label, 0, 2)
        self.test_method_value = self._create_value_label("-", value_style)
        grid.addWidget(self.test_method_value, 0, 3)
        self.product_label = self._create_label("제품명", label_style)
        grid.addWidget(self.product_label, 0, 4)
        self.product_value = self._create_value_label("-", value_style)
        grid.addWidget(self.product_value, 0, 5)

        # 행 2
        self.expiry_label = self._create_label("소비기한", label_style)
        grid.addWidget(self.expiry_label, 1, 0)
        self.expiry_value = self._create_value_label("-", value_style)
        grid.addWidget(self.expiry_value, 1, 1)
        self.storage_label = self._create_label("보관조건", label_style)
        grid.addWidget(self.storage_label, 1, 2)
        self.storage_value = self._create_value_label("-", value_style)
        grid.addWidget(self.storage_value, 1, 3)
        self.food_type_label = self._create_label("식품유형", label_style)
        grid.addWidget(self.food_type_label, 1, 4)
        self.food_type_value = self._create_value_label("-", value_style)
        grid.addWidget(self.food_type_value, 1, 5)

        # 행 3
        self.period_label = self._create_label("실험기간", label_style)
        grid.addWidget(self.period_label, 2, 0)
        self.period_value = self._create_value_label("-", value_style)
        grid.addWidget(self.period_value, 2, 1)
        self.interim_report_label = self._create_label("중간보고서", label_style)
        grid.addWidget(self.interim_report_label, 2, 2)
        self.interim_report_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_report_value, 2, 3)
        self.extension_label = self._create_label("연장실험", label_style)
        grid.addWidget(self.extension_label, 2, 4)
        self.extension_value = self._create_value_label("-", value_style)
        grid.addWidget(self.extension_value, 2, 5)

        # 행 4
        self.sampling_count_label = self._create_label("샘플링횟수", label_style)
        grid.addWidget(self.sampling_count_label, 3, 0)
        self.sampling_count_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_count_value, 3, 1)
        self.sampling_interval_label = self._create_label("샘플링간격", label_style)
        grid.addWidget(self.sampling_interval_label, 3, 2)
        self.sampling_interval_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_interval_value, 3, 3)
        self.start_date_label = self._create_label("시작일", label_style)
        grid.addWidget(self.start_date_label, 3, 4)
        self.start_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.start_date_value, 3, 5)

        # 행 5
        self.interim_date_label = self._create_label("중간보고일", label_style)
        grid.addWidget(self.interim_date_label, 4, 0)
        self.interim_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_date_value, 4, 1)
        self.last_test_date_label = self._create_label("마지막실험일", label_style)
        grid.addWidget(self.last_test_date_label, 4, 2)
        self.last_test_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.last_test_date_value, 4, 3)
        self.status_label = self._create_label("상태", label_style)
        grid.addWidget(self.status_label, 4, 4)
        self.status_value = self._create_value_label("-", value_style)
        grid.addWidget(self.status_value, 4, 5)

        # 행 6 - 검체량 관련
        self.sample_per_test_label = self._create_label("1회실험검체량", label_style)
        grid.addWidget(self.sample_per_test_label, 5, 0)
        self.sample_per_test_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sample_per_test_value, 5, 1)
        self.packaging_label = self._create_label("포장단위", label_style)
        grid.addWidget(self.packaging_label, 5, 2)
        self.packaging_value = self._create_value_label("-", value_style)
        grid.addWidget(self.packaging_value, 5, 3)
        self.required_sample_label = self._create_label("필요검체량", label_style)
        grid.addWidget(self.required_sample_label, 5, 4)
        # 필요 검체량 - 수정 가능한 입력 필드
        self.required_sample_value = QLineEdit("-")
        self.required_sample_value.setStyleSheet(value_style + " color: #e67e22; font-weight: bold;")
        self.required_sample_value.setAlignment(Qt.AlignCenter)
        self.required_sample_value.setMinimumWidth(60)
        self.required_sample_value.setPlaceholderText("개수 입력")
        grid.addWidget(self.required_sample_value, 5, 5)
        self.current_required_sample = 0  # 계산된 필요 검체량 저장

        parent_layout.addWidget(group)

    def create_temperature_panel(self, parent_layout):
        """보관 온도 구간 패널"""
        group = QGroupBox("2. 보관 온도")
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #27ae60; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #27ae60; }
        """)

        grid = QGridLayout(group)
        grid.setSpacing(2)

        label_style = "font-weight: bold; background-color: #d5f5e3; padding: 4px; border: 1px solid #27ae60; font-size: 13px;"
        value_style = "background-color: white; padding: 4px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 13px;"

        grid.addWidget(self._create_label("구분", label_style), 0, 0)
        self.temp_zone1_label = self._create_label("1구간", label_style)
        grid.addWidget(self.temp_zone1_label, 0, 1)
        self.temp_zone2_label = self._create_label("2구간", label_style)
        grid.addWidget(self.temp_zone2_label, 0, 2)
        self.temp_zone3_label = self._create_label("3구간", label_style)
        grid.addWidget(self.temp_zone3_label, 0, 3)

        grid.addWidget(self._create_label("온도", label_style), 1, 0)
        self.temp_zone1_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone1_value, 1, 1)
        self.temp_zone2_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone2_value, 1, 2)
        self.temp_zone3_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone3_value, 1, 3)

        parent_layout.addWidget(group)

    def create_memo_panel(self, parent_layout):
        """메모 입력 (1/3) + 메모 이력 (2/3)"""
        group = QGroupBox("3. 메모")
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
        group = QGroupBox("4. 온도조건별 실험 스케줄")
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

        layout.addLayout(btn_layout)

        # 추가/삭제된 항목 저장용 리스트
        self.additional_test_items = []
        self.removed_base_items = []

        # 비용 요약
        self.create_cost_summary(layout)

        parent_layout.addWidget(group)

    def create_cost_summary(self, parent_layout):
        """비용 요약"""
        cost_frame = QFrame()
        cost_frame.setStyleSheet("background-color: #fef9e7; border: 1px solid #f39c12; border-radius: 5px; padding: 5px;")
        cost_layout = QGridLayout(cost_frame)
        cost_layout.setSpacing(5)

        # 1. 1회 기준 (합계)
        cost_layout.addWidget(QLabel("1. 1회 기준 (합계)"), 0, 0)
        self.cost_per_test = QLabel("-")
        self.cost_per_test.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.cost_per_test, 0, 1)

        # 2. 회차별 총계 (합계)
        cost_layout.addWidget(QLabel("2. 회차별 총계 (합계)"), 0, 2)
        self.total_rounds_cost = QLabel("-")
        self.total_rounds_cost.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.total_rounds_cost, 0, 3)

        # 3. 보고서 비용
        cost_layout.addWidget(QLabel("3. 보고서 비용"), 1, 0)
        self.report_cost = QLabel("-")
        self.report_cost.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.report_cost, 1, 1)

        # 4. 최종비용 (부가세별도) - 계산식 포함
        final_label = QLabel("4. 최종비용 (부가세별도)")
        final_label.setStyleSheet("font-weight: bold; color: #e67e22;")
        cost_layout.addWidget(final_label, 1, 2)

        self.final_cost_formula = QLabel("-")
        self.final_cost_formula.setStyleSheet("font-weight: bold; color: #e67e22;")
        self.final_cost_formula.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.final_cost_formula, 1, 3)

        # 5. 최종비용 (부가세 포함)
        final_vat_label = QLabel("5. 최종비용 (부가세 포함)")
        final_vat_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #c0392b;")
        cost_layout.addWidget(final_vat_label, 2, 2)

        self.final_cost_with_vat = QLabel("-")
        self.final_cost_with_vat.setStyleSheet("font-weight: bold; font-size: 13px; color: white; background-color: #e67e22; padding: 5px; border-radius: 3px;")
        self.final_cost_with_vat.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.final_cost_with_vat, 2, 3)

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
            # 추가/삭제 항목 초기화
            self.additional_test_items = []
            self.removed_base_items = []
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
            experiment_days = total_days * 2
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

        if start_date != '-' and experiment_days > 0 and sampling_count >= 6:
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
            experiment_days = total_days * 2
        else:
            experiment_days = total_days // 2 if total_days > 0 else 0

        # 시작일과 마지막실험일 사이의 간격을 샘플링 횟수로 나눔 (반올림 적용)
        interval_days = round(experiment_days / sampling_count) if sampling_count > 0 else 0

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

        for i in range(sampling_count):
            if start_date and interval_days > 0:
                from datetime import timedelta
                sample_date = start_date + timedelta(days=i * interval_days)
                date_value = sample_date.strftime('%m-%d')  # 짧은 날짜 형식
            else:
                date_value = "-"
            date_item = QTableWidgetItem(date_value)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setBackground(QColor('#E6F3FF'))
            table.setItem(0, i + 1, date_item)
        table.setItem(0, col_count - 1, QTableWidgetItem(""))

        # 행 1: 제조후 일수
        time_item = QTableWidgetItem("제조후 일수")
        time_item.setBackground(QColor('#90EE90'))
        table.setItem(1, 0, time_item)

        for i in range(sampling_count):
            days_elapsed = int(round(i * interval_days))
            time_value = f"{days_elapsed}일"
            item = QTableWidgetItem(time_value)
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(1, i + 1, item)
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
        self.report_cost.setText(f"{report_cost:,}원")

        # 4. 최종비용 (부가세별도) - 계산식 표시
        final_cost_no_vat = int(total_rounds_cost * zone_count + report_cost)
        formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} = {final_cost_no_vat:,}원"
        self.final_cost_formula.setText(formula_text)

        # 5. 최종비용 (부가세 포함) - 10% 부가세
        final_cost_with_vat = int(final_cost_no_vat * 1.1)
        self.final_cost_with_vat.setText(f"{final_cost_with_vat:,}원")

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

    def on_experiment_cell_clicked(self, row, col):
        """실험 테이블 셀 클릭 시 O/X 토글"""
        if not self.current_schedule:
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6

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

        # 각 회차별 활성 항목 비용 합계 계산
        column_costs = []  # 각 회차별 비용
        for col_idx in range(1, sampling_count + 1):
            col_cost = 0
            for row_idx, test_item in enumerate(test_items):
                item = table.item(test_item_start_row + row_idx, col_idx)
                if item and item.text() == 'O':
                    col_cost += int(fees.get(test_item, 0))
            column_costs.append(col_cost)

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

        # 3. 보고서 비용
        if test_method in ['real', 'custom_real']:
            report_cost = 200000
        elif test_method in ['acceleration', 'custom_acceleration']:
            report_cost = 300000
        else:
            report_cost = 200000
        self.report_cost.setText(f"{report_cost:,}원")

        # 4. 최종비용 (부가세별도) - 계산식 표시
        # 실측: 회차별총계 × 1 + 보고서비용
        # 가속: 회차별총계 × 3 + 보고서비용
        final_cost_no_vat = int(total_rounds_cost * zone_count + report_cost)
        formula_text = f"{total_rounds_cost:,} × {zone_count} + {report_cost:,} = {final_cost_no_vat:,}원"
        self.final_cost_formula.setText(formula_text)

        # 5. 최종비용 (부가세 포함) - 10% 부가세
        final_cost_with_vat = int(final_cost_no_vat * 1.1)
        self.final_cost_with_vat.setText(f"{final_cost_with_vat:,}원")
