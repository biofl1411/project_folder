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

        # 비용 요약
        self.create_cost_summary(layout)

        parent_layout.addWidget(group)

    def create_cost_summary(self, parent_layout):
        """비용 요약"""
        cost_frame = QFrame()
        cost_frame.setStyleSheet("background-color: #fef9e7; border: 1px solid #f39c12; border-radius: 5px; padding: 5px;")
        cost_layout = QGridLayout(cost_frame)
        cost_layout.setSpacing(5)

        cost_layout.addWidget(QLabel("(1회 기준)"), 0, 0)
        self.cost_per_test = QLabel("-")
        self.cost_per_test.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.cost_per_test, 0, 1)

        cost_layout.addWidget(QLabel("실험 방법 가격"), 0, 2)
        self.test_method_cost = QLabel("-")
        self.test_method_cost.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.test_method_cost, 0, 3)

        cost_layout.addWidget(QLabel("보고서 비용"), 1, 0)
        self.report_cost = QLabel("-")
        self.report_cost.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.report_cost, 1, 1)

        final_label = QLabel("최종비용")
        final_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #e67e22;")
        cost_layout.addWidget(final_label, 1, 2)

        self.final_cost = QLabel("-")
        self.final_cost.setStyleSheet("font-weight: bold; font-size: 13px; color: white; background-color: #e67e22; padding: 5px; border-radius: 3px;")
        self.final_cost.setAlignment(Qt.AlignRight)
        cost_layout.addWidget(self.final_cost, 1, 3)

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
        self.sampling_count_value.setText(f"{sampling_count}회")

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

        self.update_temperature_panel(schedule)

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

        test_items = ['관능평가', '세균수', '대장균(정량)', 'pH']

        fees = {}
        try:
            all_fees = Fee.get_all()
            for fee in all_fees:
                fees[fee['test_item']] = fee['price']
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

        # 1회 기준 비용 (소수점 제거)
        cost_per_test = int(sum(fees.get(item, 0) for item in test_items))
        self.cost_per_test.setText(f"{cost_per_test:,}원")

        # 실험 방법 가격 (검사항목 합계 × 샘플링 횟수 × 구간 수)
        test_method_cost = int(cost_per_test * sampling_count * zone_count)
        self.test_method_cost.setText(f"{test_method_cost:,}원")

        # 보고서 비용: 실측/의뢰자요청(실측) = 200,000원, 가속/의뢰자요청(가속) = 300,000원
        if test_method in ['real', 'custom_real']:
            report_cost = 200000
        elif test_method in ['acceleration', 'custom_acceleration']:
            report_cost = 300000
        else:
            report_cost = 200000  # 기본값
        self.report_cost.setText(f"{report_cost:,}원")

        final_cost = test_method_cost + report_cost
        self.final_cost.setText(f"{final_cost:,}원")

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
            'temp_zone1': (self.temp_zone1_label, self.temp_zone1_value),
            'temp_zone2': (self.temp_zone2_label, self.temp_zone2_value),
            'temp_zone3': (self.temp_zone3_label, self.temp_zone3_value),
        }

        for field_key, (label_widget, value_widget) in field_widgets.items():
            is_visible = field_key in visible_fields
            label_widget.setVisible(is_visible)
            value_widget.setVisible(is_visible)

    def on_experiment_cell_clicked(self, row, col):
        """실험 테이블 셀 클릭 시 O/X/- 토글"""
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

        # O → X → - → O 순환
        if current_value == 'O':
            new_value = 'X'
            item.setForeground(QBrush(QColor('#e74c3c')))  # 빨간색
        elif current_value == 'X':
            new_value = '-'
            item.setForeground(QBrush(QColor('#95a5a6')))  # 회색
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

        test_items = ['관능평가', '세균수', '대장균(정량)', 'pH']

        # 검사항목 행 시작 (행 2부터)
        test_item_start_row = 2
        col_count = table.columnCount()

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

        # 전체 합계 계산
        total_active_cost = sum(column_costs)

        # 실험 방법에 따른 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 1회 기준 비용 (첫 번째 회차 기준으로 표시)
        first_col_cost = column_costs[0] if column_costs else 0
        self.cost_per_test.setText(f"{first_col_cost:,}원")

        # 실험 방법 가격 (모든 회차 비용 합계 × 구간 수)
        test_method_cost = int(total_active_cost * zone_count)
        self.test_method_cost.setText(f"{test_method_cost:,}원")

        # 보고서 비용
        if test_method in ['real', 'custom_real']:
            report_cost = 200000
        elif test_method in ['acceleration', 'custom_acceleration']:
            report_cost = 300000
        else:
            report_cost = 200000
        self.report_cost.setText(f"{report_cost:,}원")

        # 최종 비용
        final_cost = test_method_cost + report_cost
        self.final_cost.setText(f"{final_cost:,}원")
