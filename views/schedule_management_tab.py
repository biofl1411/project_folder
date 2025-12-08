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
                             QDialogButtonBox, QCalendarWidget, QMenu, QAction,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QDateTime, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QBrush, QCursor
import pandas as pd
import os
from datetime import datetime

from models.schedules import Schedule
from models.fees import Fee
from models.product_types import ProductType
from models.activity_log import ActivityLog
from utils.logger import log_message, log_error, log_exception, safe_get
from .settings_dialog import get_status_settings, get_status_map, get_status_colors, get_status_names, get_status_code_by_name


def get_korean_holidays(year):
    """한국 공휴일 목록 반환 (고정 공휴일 + 음력 공휴일 + 대체공휴일)

    대체공휴일 적용 기준:
    - 설날/추석 연휴: 일요일과 겹치면 연휴 다음 첫 평일 (2014년~)
    - 어린이날: 토요일 또는 일요일과 겹치면 다음 평일 (2014년~)
    - 삼일절, 광복절, 개천절, 한글날: 일요일과 겹치면 다음 월요일 (2021년~)
    - 부처님오신날, 크리스마스: 일요일과 겹치면 다음 월요일 (2023년~)
    """
    from datetime import date, timedelta

    holidays = set()

    # 고정 공휴일 처리
    # substitute_type: 'none'=미적용, 'sunday'=일요일만, 'weekend'=토/일 모두
    fixed_holidays = [
        (1, 1, '신정', 'none'),           # 신정 - 대체공휴일 미적용
        (3, 1, '삼일절', 'sunday'),       # 삼일절 - 일요일만 대체공휴일
        (5, 5, '어린이날', 'weekend'),    # 어린이날 - 토/일 모두 대체공휴일
        (6, 6, '현충일', 'none'),         # 현충일 - 대체공휴일 미적용
        (8, 15, '광복절', 'sunday'),      # 광복절 - 일요일만 대체공휴일
        (10, 3, '개천절', 'sunday'),      # 개천절 - 일요일만 대체공휴일
        (10, 9, '한글날', 'sunday'),      # 한글날 - 일요일만 대체공휴일
        (12, 25, '크리스마스', 'sunday'), # 크리스마스 - 일요일만 대체공휴일
    ]

    for month, day, name, substitute_type in fixed_holidays:
        try:
            holiday_date = date(year, month, day)
            holidays.add(holiday_date)

            # 대체공휴일 계산
            if substitute_type == 'weekend':
                # 토요일(5) 또는 일요일(6)이면 다음 월요일
                if holiday_date.weekday() == 5:  # 토요일
                    substitute = holiday_date + timedelta(days=2)
                    holidays.add(substitute)
                elif holiday_date.weekday() == 6:  # 일요일
                    substitute = holiday_date + timedelta(days=1)
                    holidays.add(substitute)
            elif substitute_type == 'sunday':
                # 일요일이면 다음 월요일
                if holiday_date.weekday() == 6:
                    substitute = holiday_date + timedelta(days=1)
                    holidays.add(substitute)
        except (ValueError, TypeError):
            pass

    # 음력 공휴일 (양력 변환 - 연도별 정확한 날짜)
    # 설날 연휴 (전날, 당일, 다음날), 추석 연휴 (전날, 당일, 다음날)
    lunar_holidays = {
        # 2025-2030년
        2025: {
            'seollal': [(1, 28), (1, 29), (1, 30)],
            'chuseok': [(10, 5), (10, 6), (10, 7)],
        },
        2026: {
            'seollal': [(2, 16), (2, 17), (2, 18)],
            'chuseok': [(9, 24), (9, 25), (9, 26)],
        },
        2027: {
            'seollal': [(2, 5), (2, 6), (2, 7)],
            'chuseok': [(10, 13), (10, 14), (10, 15)],
        },
        2028: {
            'seollal': [(1, 25), (1, 26), (1, 27)],
            'chuseok': [(10, 1), (10, 2), (10, 3)],
        },
        2029: {
            'seollal': [(2, 12), (2, 13), (2, 14)],
            'chuseok': [(9, 21), (9, 22), (9, 23)],
        },
        2030: {
            'seollal': [(2, 2), (2, 3), (2, 4)],
            'chuseok': [(10, 11), (10, 12), (10, 13)],
        },
        # 2031-2035년
        2031: {
            'seollal': [(1, 22), (1, 23), (1, 24)],
            'chuseok': [(9, 27), (9, 28), (9, 29)],  # 9/28 일요일 → 대체공휴일
        },
        2032: {
            'seollal': [(2, 10), (2, 11), (2, 12)],
            'chuseok': [(9, 18), (9, 19), (9, 20)],  # 9/19 일요일 → 대체공휴일
        },
        2033: {
            'seollal': [(1, 30), (1, 31), (2, 1)],   # 1/30 일요일 → 대체공휴일
            'chuseok': [(9, 7), (9, 8), (9, 9)],
        },
        2034: {
            'seollal': [(2, 18), (2, 19), (2, 20)],  # 2/19 일요일 → 대체공휴일
            'chuseok': [(9, 26), (9, 27), (9, 28)],
        },
        2035: {
            'seollal': [(2, 7), (2, 8), (2, 9)],
            'chuseok': [(9, 15), (9, 16), (9, 17)],  # 9/16 일요일 → 대체공휴일
        },
    }

    if year in lunar_holidays:
        # 설날과 추석 연휴 처리
        for holiday_type in ['seollal', 'chuseok']:
            dates = lunar_holidays[year].get(holiday_type, [])
            holiday_dates = []

            for month, day in dates:
                try:
                    hdate = date(year, month, day)
                    holidays.add(hdate)
                    holiday_dates.append(hdate)
                except (ValueError, TypeError):
                    pass

            # 대체공휴일 계산: 연휴 중 일요일이 있으면 연휴 다음 첫 평일
            if holiday_dates:
                has_sunday = any(d.weekday() == 6 for d in holiday_dates)
                if has_sunday:
                    last_holiday = max(holiday_dates)
                    substitute = last_holiday + timedelta(days=1)
                    # 이미 공휴일이면 다음날로
                    while substitute in holidays or substitute.weekday() >= 5:
                        substitute += timedelta(days=1)
                    holidays.add(substitute)

    # 부처님오신날 (음력 4월 8일 - 대체공휴일 적용 2024년~)
    buddha_birthday = {
        2025: (5, 5),
        2026: (5, 24),   # 일요일 → 5/25 대체공휴일
        2027: (5, 13),
        2028: (5, 2),
        2029: (5, 20),
        2030: (5, 9),
        2031: (5, 28),
        2032: (5, 16),   # 일요일 → 5/17 대체공휴일
        2033: (5, 6),
        2034: (5, 25),
        2035: (5, 15),
    }

    if year in buddha_birthday:
        month, day = buddha_birthday[year]
        try:
            hdate = date(year, month, day)
            holidays.add(hdate)

            # 대체공휴일: 일요일이면 다음 월요일
            if hdate.weekday() == 6:
                substitute = hdate + timedelta(days=1)
                holidays.add(substitute)
        except (ValueError, TypeError):
            pass

    return holidays


def add_business_days(start_date, business_days):
    """시작일로부터 영업일(주말, 공휴일 제외) 기준 날짜 계산

    Args:
        start_date: 시작일 (datetime 또는 date 객체)
        business_days: 추가할 영업일 수

    Returns:
        영업일 기준 계산된 날짜 (datetime 객체)
    """
    from datetime import timedelta, date

    if business_days <= 0:
        return start_date

    # datetime을 date로 변환
    if hasattr(start_date, 'date'):
        current_date = start_date.date()
    else:
        current_date = start_date

    # 해당 연도와 다음 연도의 공휴일 가져오기
    holidays = get_korean_holidays(current_date.year)
    holidays.update(get_korean_holidays(current_date.year + 1))

    days_added = 0

    while days_added < business_days:
        current_date += timedelta(days=1)

        # 토요일(5), 일요일(6) 또는 공휴일이면 건너뛰기
        if current_date.weekday() < 5 and current_date not in holidays:
            days_added += 1

    # datetime으로 반환
    return datetime(current_date.year, current_date.month, current_date.day)


class ClickableLabel(QLabel):
    """클릭 가능한 라벨 - 클릭 시 시그널 발생"""
    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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
        ('last_experiment_date', '마지막실험일', True),
        ('report_date', '보고서작성일', True),
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
            cursor.execute("SELECT value FROM settings WHERE `key` = 'schedule_display_fields'")
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
                UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE `key` = 'schedule_display_fields'
            """, (value,))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (`key`, value, description)
                    VALUES ('schedule_display_fields', %s, '스케줄 관리 표시 필드')
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
            except (ValueError, TypeError, AttributeError):
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
    """스케줄 선택 팝업 다이얼로그 - 스케줄 작성 탭과 동일한 컬럼 표시"""

    # 한글 초성 매핑
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    # 컬럼 정의 (key, header_name, data_key, default_visible)
    ALL_COLUMNS = [
        ('id', 'ID', 'id', False),
        ('client_name', '업체명', 'client_name', True),
        ('sales_rep', '영업담당', 'sales_rep', True),
        ('product_name', '샘플명', 'product_name', True),
        ('food_type', '식품유형', 'food_type_id', False),
        ('test_method', '실험방법', 'test_method', True),
        ('storage_condition', '보관조건', 'storage_condition', True),
        ('expiry_period', '소비기한', None, True),
        ('test_period', '실험기간', None, False),
        ('sampling_count', '샘플링횟수', 'sampling_count', False),
        ('report_type', '보고서종류', None, False),
        ('last_experiment_date', '마지막실험일', None, False),
        ('start_date', '시작일', 'start_date', True),
        ('end_date', '종료일', 'end_date', True),
        ('status', '상태', 'status', True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_schedule_id = None
        self.all_schedules = []  # 전체 스케줄 목록 저장
        self.initUI()

    def initUI(self):
        self.setWindowTitle("스케줄 선택")
        self.setMinimumSize(1000, 500)
        self.resize(1200, 600)

        layout = QVBoxLayout(self)

        # 검색 영역
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #f3e5f5;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #ce93d8;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ce93d8;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #ab47bc;
            }
        """)
        search_layout = QHBoxLayout(search_frame)

        search_layout.addWidget(QLabel("검색:"))

        # 검색 필드 선택
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["전체", "업체명", "샘플명", "상태"])
        self.search_field_combo.setMinimumWidth(80)
        search_layout.addWidget(self.search_field_combo)

        # 검색 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력... (초성 검색 가능: ㅂㅇㅍㄷㄹ)")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.filter_schedules)
        search_layout.addWidget(self.search_input)

        # 검색 필드 변경 시에도 필터 적용
        self.search_field_combo.currentIndexChanged.connect(self.filter_schedules)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_btn)

        search_layout.addStretch()
        layout.addWidget(search_frame)

        # 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(len(self.ALL_COLUMNS))
        headers = [col[1] for col in self.ALL_COLUMNS]
        self.schedule_table.setHorizontalHeaderLabels(headers)

        # 열 너비 조절 설정
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # 각 열의 기본 너비 설정
        column_widths = {
            'id': 40,
            'client_name': 120,
            'sales_rep': 80,
            'product_name': 120,
            'food_type': 100,
            'test_method': 80,
            'storage_condition': 70,
            'expiry_period': 90,
            'test_period': 70,
            'sampling_count': 70,
            'report_type': 100,
            'last_experiment_date': 90,
            'start_date': 90,
            'end_date': 90,
            'status': 70,
        }
        for col_index, col_def in enumerate(self.ALL_COLUMNS):
            col_key = col_def[0]
            if col_key in column_widths:
                self.schedule_table.setColumnWidth(col_index, column_widths[col_key])

        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.doubleClicked.connect(self.accept)

        # 헤더 클릭으로 정렬 기능 활성화
        self.schedule_table.setSortingEnabled(True)
        self.schedule_table.horizontalHeader().setSortIndicatorShown(True)

        layout.addWidget(self.schedule_table)

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 컬럼 표시 설정 적용
        self.apply_column_settings()

        # 데이터 로드
        self.load_schedules()

    def get_column_settings(self):
        """데이터베이스에서 스케줄 작성 탭 컬럼 설정 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'schedule_tab_columns'")
            result = cursor.fetchone()
            conn.close()

            if result:
                return result['value'].split(',')
            else:
                # 기본값: 기본 표시 컬럼
                return [col[0] for col in self.ALL_COLUMNS if col[3]]
        except Exception as e:
            print(f"컬럼 설정 로드 오류: {e}")
            return [col[0] for col in self.ALL_COLUMNS if col[3]]

    def apply_column_settings(self):
        """컬럼 표시 설정을 테이블에 적용"""
        visible_columns = self.get_column_settings()

        for col_index, col_def in enumerate(self.ALL_COLUMNS):
            col_key = col_def[0]
            if col_key == 'id':
                # ID 열은 항상 숨김
                self.schedule_table.setColumnHidden(col_index, True)
            else:
                # 설정에 따라 표시/숨김
                is_hidden = col_key not in visible_columns
                self.schedule_table.setColumnHidden(col_index, is_hidden)

    def load_schedules(self):
        """스케줄 목록 로드"""
        try:
            raw_schedules = Schedule.get_all() or []
            self.all_schedules = [dict(s) for s in raw_schedules]
            self.display_schedules(self.all_schedules)
        except Exception as e:
            print(f"스케줄 로드 오류: {e}")

    def display_schedules(self, schedules):
        """스케줄 목록을 테이블에 표시"""
        self.schedule_table.setUpdatesEnabled(False)
        try:
            self.schedule_table.setRowCount(0)

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)

                for col_index, col_def in enumerate(self.ALL_COLUMNS):
                    col_key = col_def[0]
                    data_key = col_def[2]

                    if col_key == 'id':
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(str(schedule.get('id', ''))))

                    elif col_key == 'test_method':
                        test_method = schedule.get('test_method', '') or ''
                        test_method_text = {
                            'real': '실측', 'acceleration': '가속',
                            'custom_real': '의뢰자(실측)', 'custom_acceleration': '의뢰자(가속)'
                        }.get(test_method, test_method)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(test_method_text))

                    elif col_key == 'storage_condition':
                        storage = schedule.get('storage_condition', '') or ''
                        storage_text = {
                            'room_temp': '상온', 'warm': '실온', 'cool': '냉장', 'freeze': '냉동'
                        }.get(storage, storage)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(storage_text))

                    elif col_key == 'food_type':
                        food_type_id = schedule.get('food_type_id', '')
                        food_type_name = ''
                        if food_type_id:
                            try:
                                food_type = ProductType.get_by_id(food_type_id)
                                if food_type:
                                    food_type_name = food_type.get('type_name', '') or ''
                            except Exception:
                                pass
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(food_type_name))

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
                        expiry_text = ' '.join(parts) if parts else ''
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(expiry_text))

                    elif col_key == 'test_period':
                        test_method = schedule.get('test_method', 'real')
                        days = schedule.get('test_period_days', 0) or 0
                        months = schedule.get('test_period_months', 0) or 0
                        years = schedule.get('test_period_years', 0) or 0
                        total_days = days + (months * 30) + (years * 365)
                        if test_method in ['acceleration', 'custom_acceleration']:
                            test_days = total_days // 2
                        else:
                            test_days = int(total_days * 1.5)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(f"{test_days}일" if test_days > 0 else ''))

                    elif col_key == 'report_type':
                        types = []
                        if schedule.get('report_interim'):
                            types.append('중간')
                        if schedule.get('report_korean'):
                            types.append('국문')
                        if schedule.get('report_english'):
                            types.append('영문')
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(', '.join(types)))

                    elif col_key == 'status':
                        # 상태 (커스텀 설정 사용)
                        status = schedule.get('status', 'pending') or 'pending'
                        status_map = get_status_map()
                        status_colors = get_status_colors()
                        status_text = status_map.get(status, status)
                        status_item = QTableWidgetItem(status_text)
                        # 커스텀 색상 적용
                        if status in status_colors:
                            color = QColor(status_colors[status])
                            status_item.setBackground(color)
                            # 배경색이 어두우면 흰색 글씨, 밝으면 검정색 글씨
                            if color.lightness() < 128:
                                status_item.setForeground(QColor('#FFFFFF'))
                            else:
                                status_item.setForeground(QColor('#000000'))
                        self.schedule_table.setItem(row, col_index, status_item)

                    elif col_key == 'last_experiment_date':
                        # 마지막 실험일 계산 (마지막 샘플링 날짜)
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

                        last_experiment_date_text = '-'
                        if start_date and experiment_days > 0 and sampling_count > 0:
                            try:
                                from datetime import timedelta
                                start = datetime.strptime(start_date, '%Y-%m-%d')
                                interval = experiment_days // sampling_count
                                # 마지막 회차 날짜 (sampling_count번째 회차)
                                last_experiment_date = start + timedelta(days=interval * sampling_count)
                                last_experiment_date_text = last_experiment_date.strftime('%Y-%m-%d')
                            except (ValueError, TypeError, ZeroDivisionError):
                                last_experiment_date_text = '-'

                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(last_experiment_date_text))

                    else:
                        value = schedule.get(data_key, '') if data_key else ''
                        if value is None:
                            value = ''
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(str(value)))

        except Exception as e:
            print(f"스케줄 표시 중 오류: {e}")
        finally:
            self.schedule_table.setUpdatesEnabled(True)

    def get_chosung(self, text):
        """문자열에서 초성 추출"""
        result = ""
        for char in text:
            if '가' <= char <= '힣':
                char_code = ord(char) - ord('가')
                chosung_idx = char_code // 588
                result += self.CHOSUNG_LIST[chosung_idx]
            else:
                result += char
        return result

    def is_chosung_only(self, text):
        """문자열이 초성만으로 이루어져 있는지 확인"""
        for char in text:
            if char not in self.CHOSUNG_LIST and char != ' ':
                return False
        return True

    def match_chosung(self, text, search_text):
        """초성 검색 매칭"""
        text_chosung = self.get_chosung(text)
        return search_text.lower() in text_chosung.lower()

    def filter_schedules(self):
        """실시간 검색 필터링 (초성 검색 지원)"""
        try:
            search_text = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            if not search_text:
                self.display_schedules(self.all_schedules)
                return

            filtered = []
            is_chosung = self.is_chosung_only(search_text)

            for schedule in self.all_schedules:
                client_name = schedule.get('client_name', '') or ''
                product_name = schedule.get('product_name', '') or ''
                status = schedule.get('status', '') or ''
                status_map = get_status_map()
                status_text = status_map.get(status, status)

                match = False

                if search_field == "전체":
                    if is_chosung:
                        match = (self.match_chosung(client_name, search_text) or
                                 self.match_chosung(product_name, search_text) or
                                 self.match_chosung(status_text, search_text))
                    else:
                        search_lower = search_text.lower()
                        match = (search_lower in client_name.lower() or
                                 search_lower in product_name.lower() or
                                 search_lower in status_text.lower())
                elif search_field == "업체명":
                    if is_chosung:
                        match = self.match_chosung(client_name, search_text)
                    else:
                        match = search_text.lower() in client_name.lower()
                elif search_field == "샘플명":
                    if is_chosung:
                        match = self.match_chosung(product_name, search_text)
                    else:
                        match = search_text.lower() in product_name.lower()
                elif search_field == "상태":
                    if is_chosung:
                        match = self.match_chosung(status_text, search_text)
                    else:
                        match = search_text.lower() in status_text.lower()

                if match:
                    filtered.append(schedule)

            self.display_schedules(filtered)
        except Exception as e:
            print(f"스케줄 검색 중 오류: {e}")

    def reset_search(self):
        """검색 초기화"""
        self.search_input.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.display_schedules(self.all_schedules)

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
    # 스케줄 데이터 저장 완료 시그널
    schedule_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule = None
        self.current_user = None  # 현재 로그인한 사용자

        # 버튼 참조 저장 (권한 체크용)
        self.estimate_btn = None
        self.settings_btn = None
        self.select_btn = None
        self.add_item_btn = None
        self.remove_item_btn = None
        self.save_schedule_btn = None

        # 그룹 참조 저장 (JPG 저장용)
        self.info_group = None
        self.experiment_group = None

        self.initUI()

    def set_current_user(self, user):
        """현재 로그인한 사용자 설정 및 권한 적용"""
        self.current_user = user
        self.apply_permissions()

    def apply_permissions(self):
        """사용자 권한에 따라 버튼 활성화/비활성화"""
        if not self.current_user:
            return

        from models.users import User

        # 관리자는 모든 권한
        if self.current_user.get('role') == 'admin':
            return

        # 각 버튼에 대한 권한 체크
        if self.estimate_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_view_estimate')
            self.estimate_btn.setEnabled(has_perm)
            if not has_perm:
                self.estimate_btn.setToolTip("권한이 없습니다")

        if self.settings_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_display_settings')
            self.settings_btn.setEnabled(has_perm)
            if not has_perm:
                self.settings_btn.setToolTip("권한이 없습니다")

        if self.select_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_select')
            self.select_btn.setEnabled(has_perm)
            if not has_perm:
                self.select_btn.setToolTip("권한이 없습니다")

        if self.add_item_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_add_item')
            self.add_item_btn.setEnabled(has_perm)
            if not has_perm:
                self.add_item_btn.setToolTip("권한이 없습니다")

        if self.remove_item_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_delete_item')
            self.remove_item_btn.setEnabled(has_perm)
            if not has_perm:
                self.remove_item_btn.setToolTip("권한이 없습니다")

        if self.save_schedule_btn:
            has_perm = User.has_permission(self.current_user, 'schedule_mgmt_save')
            self.save_schedule_btn.setEnabled(has_perm)
            if not has_perm:
                self.save_schedule_btn.setToolTip("권한이 없습니다")

    def can_edit_plan(self, show_message=True, allow_suspended=False):
        """
        실험 계획안 수정 가능 여부 확인

        조건:
        1. 스케줄이 선택되어 있어야 함
        2. 상태가 'pending' (대기) 또는 'suspended' (중단, allow_suspended=True일 때)
        3. 권한이 있어야 함 (schedule_mgmt_edit_plan)

        Args:
            show_message: True이면 수정 불가 시 메시지 표시
            allow_suspended: True이면 중단 상태에서도 수정 허용

        Returns:
            bool: 수정 가능 여부
        """
        if not self.current_schedule:
            if show_message:
                QMessageBox.warning(self, "수정 불가", "먼저 스케줄을 선택하세요.")
            return False

        # 상태 확인 - 'pending' (대기) 상태 또는 'suspended' (중단, allow_suspended일 때)
        current_status = self.current_schedule.get('status', 'pending')
        allowed_statuses = ['pending']
        if allow_suspended:
            allowed_statuses.append('suspended')

        if current_status not in allowed_statuses:
            if show_message:
                status_map = get_status_map()
                status_name = status_map.get(current_status, current_status)
                QMessageBox.warning(
                    self, "수정 불가",
                    f"현재 상태가 '{status_name}'입니다.\n"
                    "상태가 '대기' 상태일 때만 실험 계획안을 수정할 수 있습니다."
                )
            return False

        # 권한 확인
        if self.current_user:
            from models.users import User
            # 관리자는 항상 수정 가능
            if self.current_user.get('role') != 'admin':
                if not User.has_permission(self.current_user, 'schedule_mgmt_edit_plan'):
                    if show_message:
                        QMessageBox.warning(self, "권한 없음", "실험 계획안 수정 권한이 없습니다.")
                    return False

        return True

    def log_activity(self, action_type, target_name=None, details=None):
        """활동 로그 기록 헬퍼 메서드"""
        if self.current_user and self.current_schedule:
            ActivityLog.log(
                user=self.current_user,
                action_type=action_type,
                target_type='schedule',
                target_id=self.current_schedule.get('id'),
                target_name=target_name or self.current_schedule.get('product_name', ''),
                details=details
            )

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

        # 3. 온도조건별 실험 스케줄
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
        frame.setFixedHeight(50)  # 높이 고정
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)  # 여백 최소화

        # 현재 선택된 스케줄 표시
        self.selected_schedule_label = QLabel("선택된 스케줄 없음")
        self.selected_schedule_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.selected_schedule_label)

        layout.addStretch()

        # JPG 저장 버튼
        self.save_jpg_btn = QPushButton("JPG 저장")
        self.save_jpg_btn.setStyleSheet("background-color: #e67e22; color: white; padding: 8px 15px; font-weight: bold;")
        self.save_jpg_btn.clicked.connect(self.save_as_jpg)
        layout.addWidget(self.save_jpg_btn)

        # 메일 발송 버튼
        self.send_mail_btn = QPushButton("메일 발송")
        self.send_mail_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 15px; font-weight: bold;")
        self.send_mail_btn.clicked.connect(self.open_mail_dialog)
        layout.addWidget(self.send_mail_btn)

        # 견적서 보기 버튼
        self.estimate_btn = QPushButton("견적서 보기")
        self.estimate_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 15px; font-weight: bold;")
        self.estimate_btn.clicked.connect(self.show_estimate)
        layout.addWidget(self.estimate_btn)

        # 표시 설정 버튼
        self.settings_btn = QPushButton("표시 설정")
        self.settings_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px 15px; font-weight: bold;")
        self.settings_btn.clicked.connect(self.open_display_settings)
        layout.addWidget(self.settings_btn)

        # 스케줄 선택 버튼
        self.select_btn = QPushButton("스케줄 선택")
        self.select_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px 20px; font-weight: bold;")
        self.select_btn.clicked.connect(self.open_schedule_selector)
        layout.addWidget(self.select_btn)

        parent_layout.addWidget(frame)

    def create_info_summary_panel(self, parent_layout):
        """소비기한 설정 실험 계획 (안) - 4열 레이아웃"""
        self.info_group = QGroupBox("1. 소비기한 설정 실험 계획 (안)")
        group = self.info_group
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #3498db; border-radius: 5px; margin-top: 10px; padding: 0px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #2980b9; }
        """)
        # GroupBox가 세로로 늘어나지 않도록 설정
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        grid = QGridLayout(group)
        grid.setSpacing(0)
        grid.setContentsMargins(2, 0, 2, 0)  # 하단 마진 제거
        grid.setVerticalSpacing(0)  # 행 간격 없음 (1~7행 붙임)
        grid.setHorizontalSpacing(0)

        # 8열 균등 배분 (라벨+값 4쌍)
        for col in range(8):
            grid.setColumnStretch(col, 1)

        # 각 행 높이 고정 (늘어나지 않도록)
        for row in range(7):
            grid.setRowStretch(row, 0)

        label_style = "font-weight: bold; background-color: #ecf0f1; padding: 1px; border: 1px solid #bdc3c7; font-size: 11px;"
        value_style = "background-color: white; padding: 1px; border: 1px solid #bdc3c7; color: #2c3e50; font-size: 11px;"
        temp_label_style = "font-weight: bold; background-color: #d5f5e3; padding: 1px; border: 1px solid #27ae60; font-size: 11px;"
        temp_value_style = "background-color: white; padding: 1px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 11px;"

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

        # 행 2: 긴급여부, 시작일, 마지막실험일, 보고서작성일
        self.urgent_label = self._create_label("긴급여부", label_style)
        grid.addWidget(self.urgent_label, 1, 0)
        self.urgent_value = ClickableLabel("-")
        self.urgent_value.setStyleSheet(value_style + " color: #2980b9; text-decoration: underline;")
        self.urgent_value.setAlignment(Qt.AlignCenter)
        self.urgent_value.setFixedHeight(25)
        self.urgent_value.clicked.connect(self.toggle_urgent_status)
        grid.addWidget(self.urgent_value, 1, 1)
        self.start_date_label = self._create_label("시 작 일", label_style)
        grid.addWidget(self.start_date_label, 1, 2)
        self.start_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.start_date_value, 1, 3)
        self.last_experiment_date_label = self._create_label("마지막실험일", label_style)
        grid.addWidget(self.last_experiment_date_label, 1, 4)
        self.last_experiment_date_value = ClickableLabel("-")
        self.last_experiment_date_value.setStyleSheet(value_style + " color: #2980b9; text-decoration: underline;")
        self.last_experiment_date_value.setAlignment(Qt.AlignCenter)
        self.last_experiment_date_value.setFixedHeight(25)
        self.last_experiment_date_value.clicked.connect(self.edit_last_experiment_date_with_calendar)
        grid.addWidget(self.last_experiment_date_value, 1, 5)
        self.report_date_label = self._create_label("보고서작성일", label_style)
        grid.addWidget(self.report_date_label, 1, 6)
        self.report_date_value = ClickableLabel("-")
        self.report_date_value.setStyleSheet(value_style + " color: #2980b9; text-decoration: underline;")
        self.report_date_value.setAlignment(Qt.AlignCenter)
        self.report_date_value.setFixedHeight(25)
        self.report_date_value.clicked.connect(self.edit_report_date_with_calendar)
        grid.addWidget(self.report_date_value, 1, 7)

        # 행 3: 실험방법, 소비기한, 실험기간, 샘플링간격
        self.test_method_label = self._create_label("실험방법", label_style)
        grid.addWidget(self.test_method_label, 2, 0)
        self.test_method_value = self._create_value_label("-", value_style)
        grid.addWidget(self.test_method_value, 2, 1)
        self.expiry_label = self._create_label("소비기한", label_style)
        grid.addWidget(self.expiry_label, 2, 2)
        self.expiry_value = self._create_value_label("-", value_style)
        grid.addWidget(self.expiry_value, 2, 3)
        self.period_label = self._create_label("실험기간", label_style)
        grid.addWidget(self.period_label, 2, 4)
        self.period_value = self._create_value_label("-", value_style)
        grid.addWidget(self.period_value, 2, 5)
        self.sampling_interval_label = self._create_label("샘플링간격", label_style)
        grid.addWidget(self.sampling_interval_label, 2, 6)
        self.sampling_interval_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_interval_value, 2, 7)

        # 행 4: 1회실험검체량, 포장단위, 필요검체량, 중간보고서
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
        self.required_sample_value.setFixedHeight(25)
        grid.addWidget(self.required_sample_value, 3, 5)
        self.current_required_sample = 0
        self.extension_test_label = self._create_label("연장실험", label_style)
        grid.addWidget(self.extension_test_label, 3, 6)
        self.extension_test_value = ClickableLabel("-")
        self.extension_test_value.setStyleSheet(value_style + " color: #2980b9; text-decoration: underline;")
        self.extension_test_value.setAlignment(Qt.AlignCenter)
        self.extension_test_value.setFixedHeight(25)
        self.extension_test_value.clicked.connect(self.toggle_extension_test)
        grid.addWidget(self.extension_test_value, 3, 7)

        # 행 5: 중간보고서(예/아니오), 1보고서, 2보고서, 3보고서
        report_label_style = "font-weight: bold; background-color: #fdebd0; padding: 1px; border: 1px solid #e67e22; font-size: 11px;"
        report_value_style = "background-color: white; padding: 1px; border: 1px solid #e67e22; color: #e67e22; font-weight: bold; font-size: 11px;"

        self.interim_report_yn_label = self._create_label("중간보고서", report_label_style)
        grid.addWidget(self.interim_report_yn_label, 4, 0)
        self.interim_report_yn_value = ClickableLabel("-")
        self.interim_report_yn_value.setStyleSheet(report_value_style + " color: #2980b9; text-decoration: underline;")
        self.interim_report_yn_value.setAlignment(Qt.AlignCenter)
        self.interim_report_yn_value.setFixedHeight(25)
        self.interim_report_yn_value.clicked.connect(self.toggle_interim_report)
        grid.addWidget(self.interim_report_yn_value, 4, 1)
        self.report1_label = self._create_label("1 보고서", report_label_style)
        grid.addWidget(self.report1_label, 4, 2)
        self.report1_value = ClickableLabel("-")
        self.report1_value.setStyleSheet(report_value_style + " color: #2980b9; text-decoration: underline;")
        self.report1_value.setAlignment(Qt.AlignCenter)
        self.report1_value.setFixedHeight(25)
        self.report1_value.clicked.connect(lambda: self.edit_report_date_with_calendar_n(1))
        grid.addWidget(self.report1_value, 4, 3)
        self.report2_label = self._create_label("2 보고서", report_label_style)
        grid.addWidget(self.report2_label, 4, 4)
        self.report2_value = ClickableLabel("-")
        self.report2_value.setStyleSheet(report_value_style + " color: #2980b9; text-decoration: underline;")
        self.report2_value.setAlignment(Qt.AlignCenter)
        self.report2_value.setFixedHeight(25)
        self.report2_value.clicked.connect(lambda: self.edit_report_date_with_calendar_n(2))
        grid.addWidget(self.report2_value, 4, 5)
        self.report3_label = self._create_label("3 보고서", report_label_style)
        grid.addWidget(self.report3_label, 4, 6)
        self.report3_value = ClickableLabel("-")
        self.report3_value.setStyleSheet(report_value_style + " color: #2980b9; text-decoration: underline;")
        self.report3_value.setAlignment(Qt.AlignCenter)
        self.report3_value.setFixedHeight(25)
        self.report3_value.clicked.connect(lambda: self.edit_report_date_with_calendar_n(3))
        grid.addWidget(self.report3_value, 4, 7)

        # 행 6: 상태, 보관온도 (1구간, 2구간, 3구간)
        self.status_label = self._create_label("상    태", label_style)
        grid.addWidget(self.status_label, 5, 0)
        self.status_value = ClickableLabel("-")
        self.status_value.setStyleSheet(value_style + " color: #2980b9; text-decoration: underline;")
        self.status_value.setAlignment(Qt.AlignCenter)
        self.status_value.setFixedHeight(25)
        self.status_value.clicked.connect(self.change_status)
        grid.addWidget(self.status_value, 5, 1)
        self.temp_zone1_label = self._create_label("1 구 간", temp_label_style)
        grid.addWidget(self.temp_zone1_label, 5, 2)
        self.temp_zone1_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone1_value, 5, 3)
        self.temp_zone2_label = self._create_label("2 구 간", temp_label_style)
        grid.addWidget(self.temp_zone2_label, 5, 4)
        self.temp_zone2_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone2_value, 5, 5)
        self.temp_zone3_label = self._create_label("3 구 간", temp_label_style)
        grid.addWidget(self.temp_zone3_label, 5, 6)
        self.temp_zone3_value = self._create_value_label("-", temp_value_style)
        grid.addWidget(self.temp_zone3_value, 5, 7)

        # 행 7: 연장기간, 연장 실험기간, 연장 회차
        extension_label_style = "font-weight: bold; background-color: #e8f8f5; padding: 2px; border: 1px solid #1abc9c; font-size: 11px;"
        extension_value_style = "background-color: white; padding: 2px; border: 1px solid #1abc9c; font-size: 11px;"

        self.extend_period_label = self._create_label("연장기간", extension_label_style)
        grid.addWidget(self.extend_period_label, 6, 0)

        # 연장기간 입력 위젯 (일, 월, 년) - 1.5배 크기
        extend_period_widget = QWidget()
        extend_period_layout = QHBoxLayout(extend_period_widget)
        extend_period_layout.setContentsMargins(2, 2, 2, 2)
        extend_period_layout.setSpacing(3)

        self.extend_days_input = QLineEdit()
        self.extend_days_input.setFixedWidth(45)  # 30 * 1.5 = 45
        self.extend_days_input.setFixedHeight(24)  # 높이도 키움
        self.extend_days_input.setAlignment(Qt.AlignCenter)
        self.extend_days_input.setPlaceholderText("0")
        self.extend_days_input.setStyleSheet("font-size: 12px;")
        self.extend_days_input.textChanged.connect(self.on_extend_period_changed)
        extend_period_layout.addWidget(self.extend_days_input)
        day_label = QLabel("일")
        day_label.setStyleSheet("font-size: 12px;")
        extend_period_layout.addWidget(day_label)

        self.extend_months_input = QLineEdit()
        self.extend_months_input.setFixedWidth(45)  # 30 * 1.5 = 45
        self.extend_months_input.setFixedHeight(24)
        self.extend_months_input.setAlignment(Qt.AlignCenter)
        self.extend_months_input.setPlaceholderText("0")
        self.extend_months_input.setStyleSheet("font-size: 12px;")
        self.extend_months_input.textChanged.connect(self.on_extend_period_changed)
        extend_period_layout.addWidget(self.extend_months_input)
        month_label = QLabel("월")
        month_label.setStyleSheet("font-size: 12px;")
        extend_period_layout.addWidget(month_label)

        self.extend_years_input = QLineEdit()
        self.extend_years_input.setFixedWidth(45)  # 30 * 1.5 = 45
        self.extend_years_input.setFixedHeight(24)
        self.extend_years_input.setAlignment(Qt.AlignCenter)
        self.extend_years_input.setPlaceholderText("0")
        self.extend_years_input.setStyleSheet("font-size: 12px;")
        self.extend_years_input.textChanged.connect(self.on_extend_period_changed)
        extend_period_layout.addWidget(self.extend_years_input)
        year_label = QLabel("년")
        year_label.setStyleSheet("font-size: 12px;")
        extend_period_layout.addWidget(year_label)
        extend_period_layout.addStretch()

        grid.addWidget(extend_period_widget, 6, 1, 1, 3)

        # 연장 실험기간 (자동 계산: 실측 1.5배, 가속 1/2)
        self.extend_experiment_period_label = self._create_label("연장실험기간", extension_label_style)
        grid.addWidget(self.extend_experiment_period_label, 6, 4)
        self.extend_experiment_period_value = self._create_value_label("-", extension_value_style)
        grid.addWidget(self.extend_experiment_period_value, 6, 5)

        # 연장 회차 - 1.5배 크기
        self.extend_rounds_label = self._create_label("연장회차", extension_label_style)
        grid.addWidget(self.extend_rounds_label, 6, 6)

        extend_rounds_widget = QWidget()
        extend_rounds_layout = QHBoxLayout(extend_rounds_widget)
        extend_rounds_layout.setContentsMargins(2, 2, 2, 2)
        extend_rounds_layout.setSpacing(3)

        self.extend_rounds_input = QLineEdit()
        self.extend_rounds_input.setFixedWidth(60)  # 40 * 1.5 = 60
        self.extend_rounds_input.setFixedHeight(24)
        self.extend_rounds_input.setAlignment(Qt.AlignCenter)
        self.extend_rounds_input.setPlaceholderText("0")
        self.extend_rounds_input.setStyleSheet("font-size: 12px;")
        self.extend_rounds_input.textChanged.connect(self.on_extend_rounds_changed)
        extend_rounds_layout.addWidget(self.extend_rounds_input)
        rounds_label = QLabel("회")
        rounds_label.setStyleSheet("font-size: 12px;")
        extend_rounds_layout.addWidget(rounds_label)

        # 회차계산 버튼 추가
        self.calc_rounds_btn = QPushButton("회차계산")
        self.calc_rounds_btn.setFixedWidth(60)
        self.calc_rounds_btn.setFixedHeight(24)
        self.calc_rounds_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6dad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.calc_rounds_btn.clicked.connect(self.show_extend_rounds_dialog)
        self.calc_rounds_btn.setEnabled(False)  # 초기에는 비활성화
        extend_rounds_layout.addWidget(self.calc_rounds_btn)
        extend_rounds_layout.addStretch()

        grid.addWidget(extend_rounds_widget, 6, 7)

        # 연장실험 필드 (호환성 유지, 숨김)
        self.extension_label = QLabel("연장실험", self)
        self.extension_label.hide()
        self.extension_value = QLabel("-", self)
        self.extension_value.hide()

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

    def create_experiment_schedule_panel(self, parent_layout):
        """온도조건별 실험 스케줄"""
        self.experiment_group = QGroupBox("2. 온도조건별 실험 스케줄")
        group = self.experiment_group
        group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 12px; border: 2px solid #e67e22; border-radius: 5px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #e67e22; }
        """)

        layout = QVBoxLayout(group)

        # 단일 테이블
        self.experiment_table = QTableWidget()
        self.experiment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 동적 높이 조절을 위해 고정 최소 높이 제거, 대신 SizePolicy 설정
        self.experiment_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.experiment_table.cellClicked.connect(self.on_experiment_cell_clicked)
        layout.addWidget(self.experiment_table)

        # 항목 추가/삭제/저장 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 버튼들을 담을 위젯 (JPG 저장 시 숨김용)
        self.experiment_btn_widget = QWidget()
        btn_widget_layout = QHBoxLayout(self.experiment_btn_widget)
        btn_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.add_item_btn = QPushButton("+ 항목 추가")
        self.add_item_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 5px 15px; font-weight: bold;")
        self.add_item_btn.clicked.connect(self.add_test_item)
        btn_widget_layout.addWidget(self.add_item_btn)

        self.remove_item_btn = QPushButton("- 항목 삭제")
        self.remove_item_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px 15px; font-weight: bold;")
        self.remove_item_btn.clicked.connect(self.remove_test_item)
        btn_widget_layout.addWidget(self.remove_item_btn)

        self.bulk_x_btn = QPushButton("선택 영역 X")
        self.bulk_x_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 5px 15px; font-weight: bold;")
        self.bulk_x_btn.clicked.connect(self.bulk_set_x)
        self.bulk_x_btn.setToolTip("테이블에서 드래그로 선택한 영역을 일괄 X로 변경")
        btn_widget_layout.addWidget(self.bulk_x_btn)

        self.save_schedule_btn = QPushButton("저장")
        self.save_schedule_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 15px; font-weight: bold;")
        self.save_schedule_btn.clicked.connect(self.save_schedule_changes)
        btn_widget_layout.addWidget(self.save_schedule_btn)

        btn_layout.addWidget(self.experiment_btn_widget)
        layout.addLayout(btn_layout)

        # 추가/삭제된 항목 저장용 리스트
        self.additional_test_items = []
        self.removed_base_items = []

        # 저장된 O/X 상태 데이터
        self.saved_experiment_data = {}

        # 사용자 정의 날짜 저장용 딕셔너리 {column_index: datetime}
        self.custom_dates = {}

        # 비용 요약
        self.create_cost_summary(layout)

        parent_layout.addWidget(group)

    def create_cost_summary(self, parent_layout):
        """비용 요약 (3줄 레이아웃) - 1차/중단/연장 각각 한 줄씩"""
        self.cost_frame = QFrame()
        cost_frame = self.cost_frame
        cost_frame.setStyleSheet("background-color: #fef9e7; border: 1px solid #f39c12; border-radius: 2px;")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.setSpacing(1)  # 행간 간격 1px
        cost_layout.setContentsMargins(2, 1, 2, 1)

        # 공통 스타일 (폰트 11px - 2포인트 증가)
        label_style = "font-size: 11px;"
        bold_style = "font-size: 11px; font-weight: bold;"
        input_style = "font-size: 11px; background-color: white; border: 1px solid #ccc; padding: 1px;"
        formula_style = "font-size: 11px; font-weight: bold; color: #d35400;"
        vat_style = "font-size: 11px; font-weight: bold; color: #27ae60;"
        first_label_style = "font-size: 11px; font-weight: bold; color: white; background-color: #3498db; padding: 1px 4px; border-radius: 2px;"
        suspend_label_style = "font-size: 11px; font-weight: bold; color: white; background-color: #e74c3c; padding: 1px 4px; border-radius: 2px;"
        extend_label_style = "font-size: 11px; font-weight: bold; color: white; background-color: #9b59b6; padding: 1px 4px; border-radius: 2px;"
        item_style = f"{label_style} color: #555;"

        # ========== 1행: 1차 견적 ==========
        self.row_first_widget = QWidget()
        self.row_first_widget.setMinimumHeight(50)  # 최소 높이 50px로 고정 (일정한 높이 유지)
        row_first = QHBoxLayout(self.row_first_widget)
        row_first.setSpacing(4)
        row_first.setContentsMargins(0, 0, 0, 0)

        first_type_label = QLabel("1차")
        first_type_label.setStyleSheet(first_label_style)
        first_type_label.setFixedWidth(32)
        row_first.addWidget(first_type_label)

        # 항목 (넓은 영역, 줄바꿈 가능)
        self.item_cost_detail = QLabel("-")
        self.item_cost_detail.setStyleSheet(item_style)
        self.item_cost_detail.setWordWrap(True)
        self.item_cost_detail.setMinimumWidth(300)
        row_first.addWidget(self.item_cost_detail, 1)

        # 1회 비용 (라벨+값 합침)
        self.cost_per_test = QLabel("1회:-")
        self.cost_per_test.setStyleSheet(bold_style)
        self.cost_per_test.setFixedWidth(85)
        row_first.addWidget(self.cost_per_test)

        # 회차 비용 (라벨+값 합침)
        self.total_rounds_cost = QLabel("회차:-")
        self.total_rounds_cost.setStyleSheet(bold_style)
        self.total_rounds_cost.setFixedWidth(110)
        row_first.addWidget(self.total_rounds_cost)

        lbl3 = QLabel("보고서:")
        lbl3.setStyleSheet(label_style)
        lbl3.setFixedWidth(40)
        row_first.addWidget(lbl3)
        self.first_report_cost_input = QLineEdit("300,000")
        self.first_report_cost_input.setAlignment(Qt.AlignRight)
        self.first_report_cost_input.setStyleSheet(input_style)
        self.first_report_cost_input.setFixedWidth(60)
        self.first_report_cost_input.setFixedHeight(20)
        self.first_report_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_first.addWidget(self.first_report_cost_input)

        self.first_interim_cost_label = QLabel("중간:")
        self.first_interim_cost_label.setStyleSheet(label_style)
        self.first_interim_cost_label.setFixedWidth(30)
        row_first.addWidget(self.first_interim_cost_label)
        self.first_interim_cost_input = QLineEdit("200,000")
        self.first_interim_cost_input.setAlignment(Qt.AlignRight)
        self.first_interim_cost_input.setStyleSheet(input_style)
        self.first_interim_cost_input.setFixedWidth(60)
        self.first_interim_cost_input.setFixedHeight(20)
        self.first_interim_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_first.addWidget(self.first_interim_cost_input)
        self.first_interim_cost_label.hide()
        self.first_interim_cost_input.hide()

        self.first_cost_formula = QLabel("-")
        self.first_cost_formula.setStyleSheet(formula_style)
        self.first_cost_formula.setMinimumWidth(250)
        row_first.addWidget(self.first_cost_formula)

        self.first_cost_vat = QLabel("-")
        self.first_cost_vat.setStyleSheet(vat_style)
        self.first_cost_vat.setFixedWidth(130)
        row_first.addWidget(self.first_cost_vat)

        cost_layout.addWidget(self.row_first_widget)

        # ========== 2행: 중단 견적 ==========
        self.row_suspend_widget = QWidget()
        self.row_suspend_widget.setMinimumHeight(50)  # 최소 높이 50px로 고정 (일정한 높이 유지)
        row_suspend = QHBoxLayout(self.row_suspend_widget)
        row_suspend.setSpacing(4)
        row_suspend.setContentsMargins(0, 0, 0, 0)

        suspend_type_label = QLabel("중단")
        suspend_type_label.setStyleSheet(suspend_label_style)
        suspend_type_label.setFixedWidth(32)
        row_suspend.addWidget(suspend_type_label)

        self.suspend_item_cost_detail = QLabel("-")
        self.suspend_item_cost_detail.setStyleSheet(item_style)
        self.suspend_item_cost_detail.setWordWrap(True)
        self.suspend_item_cost_detail.setMinimumWidth(300)
        row_suspend.addWidget(self.suspend_item_cost_detail, 1)

        self.suspend_cost_per_test = QLabel("1회:-")
        self.suspend_cost_per_test.setStyleSheet(bold_style)
        self.suspend_cost_per_test.setFixedWidth(85)
        row_suspend.addWidget(self.suspend_cost_per_test)

        self.suspend_rounds_cost = QLabel("회차:-")
        self.suspend_rounds_cost.setStyleSheet(bold_style)
        self.suspend_rounds_cost.setFixedWidth(110)
        row_suspend.addWidget(self.suspend_rounds_cost)

        lbl_s2 = QLabel("보고서:")
        lbl_s2.setStyleSheet(label_style)
        lbl_s2.setFixedWidth(40)
        row_suspend.addWidget(lbl_s2)
        self.suspend_report_cost_input = QLineEdit("300,000")
        self.suspend_report_cost_input.setAlignment(Qt.AlignRight)
        self.suspend_report_cost_input.setStyleSheet(input_style)
        self.suspend_report_cost_input.setFixedWidth(60)
        self.suspend_report_cost_input.setFixedHeight(20)
        self.suspend_report_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_suspend.addWidget(self.suspend_report_cost_input)

        self.suspend_interim_cost_label = QLabel("중간:")
        self.suspend_interim_cost_label.setStyleSheet(label_style)
        self.suspend_interim_cost_label.setFixedWidth(30)
        row_suspend.addWidget(self.suspend_interim_cost_label)
        self.suspend_interim_cost_input = QLineEdit("200,000")
        self.suspend_interim_cost_input.setAlignment(Qt.AlignRight)
        self.suspend_interim_cost_input.setStyleSheet(input_style)
        self.suspend_interim_cost_input.setFixedWidth(60)
        self.suspend_interim_cost_input.setFixedHeight(20)
        self.suspend_interim_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_suspend.addWidget(self.suspend_interim_cost_input)
        self.suspend_interim_cost_label.hide()
        self.suspend_interim_cost_input.hide()

        self.suspend_cost_formula = QLabel("-")
        self.suspend_cost_formula.setStyleSheet(formula_style)
        self.suspend_cost_formula.setMinimumWidth(250)
        row_suspend.addWidget(self.suspend_cost_formula)

        self.suspend_cost_vat = QLabel("-")
        self.suspend_cost_vat.setStyleSheet(vat_style)
        self.suspend_cost_vat.setFixedWidth(130)
        row_suspend.addWidget(self.suspend_cost_vat)

        self.row_suspend_widget.hide()
        cost_layout.addWidget(self.row_suspend_widget)

        # ========== 3행: 연장 견적 ==========
        self.row_extend_widget = QWidget()
        self.row_extend_widget.setMinimumHeight(50)  # 최소 높이 50px로 고정 (일정한 높이 유지)
        row_extend = QHBoxLayout(self.row_extend_widget)
        row_extend.setSpacing(4)
        row_extend.setContentsMargins(0, 0, 0, 0)

        extend_type_label = QLabel("연장")
        extend_type_label.setStyleSheet(extend_label_style)
        extend_type_label.setFixedWidth(32)
        row_extend.addWidget(extend_type_label)

        self.extend_item_cost_detail = QLabel("-")
        self.extend_item_cost_detail.setStyleSheet(item_style)
        self.extend_item_cost_detail.setWordWrap(True)
        self.extend_item_cost_detail.setMinimumWidth(300)
        row_extend.addWidget(self.extend_item_cost_detail, 1)

        self.extend_cost_per_test = QLabel("1회:-")
        self.extend_cost_per_test.setStyleSheet(bold_style)
        self.extend_cost_per_test.setFixedWidth(85)
        row_extend.addWidget(self.extend_cost_per_test)

        self.extend_rounds_cost = QLabel("회차:-")
        self.extend_rounds_cost.setStyleSheet(bold_style)
        self.extend_rounds_cost.setFixedWidth(110)
        row_extend.addWidget(self.extend_rounds_cost)

        lbl_e2 = QLabel("보고서:")
        lbl_e2.setStyleSheet(label_style)
        lbl_e2.setFixedWidth(40)
        row_extend.addWidget(lbl_e2)
        self.extend_report_cost_input = QLineEdit("300,000")
        self.extend_report_cost_input.setAlignment(Qt.AlignRight)
        self.extend_report_cost_input.setStyleSheet(input_style)
        self.extend_report_cost_input.setFixedWidth(60)
        self.extend_report_cost_input.setFixedHeight(20)
        self.extend_report_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_extend.addWidget(self.extend_report_cost_input)

        self.extend_interim_cost_label = QLabel("중간:")
        self.extend_interim_cost_label.setStyleSheet(label_style)
        self.extend_interim_cost_label.setFixedWidth(30)
        row_extend.addWidget(self.extend_interim_cost_label)
        self.extend_interim_cost_input = QLineEdit("200,000")
        self.extend_interim_cost_input.setAlignment(Qt.AlignRight)
        self.extend_interim_cost_input.setStyleSheet(input_style)
        self.extend_interim_cost_input.setFixedWidth(60)
        self.extend_interim_cost_input.setFixedHeight(20)
        self.extend_interim_cost_input.textChanged.connect(self.on_cost_input_changed)
        row_extend.addWidget(self.extend_interim_cost_input)
        self.extend_interim_cost_label.hide()
        self.extend_interim_cost_input.hide()

        self.extend_cost_formula = QLabel("-")
        self.extend_cost_formula.setStyleSheet(formula_style)
        self.extend_cost_formula.setMinimumWidth(250)
        row_extend.addWidget(self.extend_cost_formula)

        self.extend_cost_vat = QLabel("-")
        self.extend_cost_vat.setStyleSheet(vat_style)
        self.extend_cost_vat.setFixedWidth(130)
        row_extend.addWidget(self.extend_cost_vat)

        self.row_extend_widget.hide()
        cost_layout.addWidget(self.row_extend_widget)

        # 호환성을 위한 기존 변수 참조
        self.report_cost_input = self.first_report_cost_input
        self.interim_report_cost_input = self.first_interim_cost_input
        self.interim_cost_label = self.first_interim_cost_label
        self.final_cost_formula = self.first_cost_formula
        self.final_cost_with_vat = self.first_cost_vat

        parent_layout.addWidget(cost_frame)

    def _create_label(self, text, style):
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        label.setFixedHeight(25)
        return label

    def _create_value_label(self, text, style):
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumWidth(60)
        label.setFixedHeight(25)
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
            # 저장된 추가/삭제 항목 및 사용자 수정 날짜 불러오기
            self._load_saved_test_items(schedule)
            client_name = schedule.get('client_name', '-') or '-'
            product_name = schedule.get('product_name', '-') or '-'
            self.selected_schedule_label.setText(f"선택: {client_name} - {product_name}")
            self.update_info_panel(schedule)
            self.update_experiment_schedule(schedule)

    def _load_saved_test_items(self, schedule):
        """저장된 추가/삭제 검사항목, O/X 상태 및 사용자 수정 날짜 불러오기"""
        import json

        # 추가된 검사항목 불러오기
        additional_json = schedule.get('additional_test_items')
        if additional_json:
            try:
                self.additional_test_items = json.loads(additional_json)
            except (json.JSONDecodeError, TypeError):
                self.additional_test_items = []
        else:
            self.additional_test_items = []

        # 삭제된 기본 검사항목 불러오기
        removed_json = schedule.get('removed_test_items')
        if removed_json:
            try:
                self.removed_base_items = json.loads(removed_json)
            except (json.JSONDecodeError, TypeError):
                self.removed_base_items = []
        else:
            self.removed_base_items = []

        # O/X 상태 데이터 불러오기
        experiment_data_json = schedule.get('experiment_schedule_data')
        if experiment_data_json:
            try:
                self.saved_experiment_data = json.loads(experiment_data_json)
            except (json.JSONDecodeError, TypeError):
                self.saved_experiment_data = {}
        else:
            self.saved_experiment_data = {}

        # 사용자 수정 날짜 불러오기 (문자열을 datetime으로 변환)
        custom_dates_json = schedule.get('custom_dates')
        if custom_dates_json:
            try:
                from datetime import datetime
                loaded_dates = json.loads(custom_dates_json)
                self.custom_dates = {}
                for col, date_str in loaded_dates.items():
                    try:
                        self.custom_dates[int(col)] = datetime.strptime(date_str, '%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            except (json.JSONDecodeError, TypeError):
                self.custom_dates = {}
        else:
            self.custom_dates = {}

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

        # 저장된 실제 실험일수 사용 (없으면 기본 공식으로 계산)
        actual_experiment_days = schedule.get('actual_experiment_days')
        if actual_experiment_days is not None and actual_experiment_days > 0:
            experiment_days = actual_experiment_days
        else:
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

        # 긴급여부
        is_urgent = schedule.get('is_urgent', 0)
        if is_urgent:
            self.urgent_value.setText("긴급")
            self.urgent_value.setStyleSheet("background-color: #ffcccc; padding: 3px; border: 1px solid #e74c3c; color: #e74c3c; font-weight: bold; font-size: 11px; text-decoration: underline;")
        else:
            self.urgent_value.setText("일반")
            self.urgent_value.setStyleSheet("background-color: white; padding: 3px; border: 1px solid #bdc3c7; color: #2980b9; font-size: 11px; text-decoration: underline;")

        # 연장실험 (행 4 - 기존 중간보고서 위치)
        extension_test = schedule.get('extension_test', 0)
        if extension_test:
            self.extension_test_value.setText("진행")
            self.extension_test_value.setStyleSheet("background-color: #d5f5e3; padding: 1px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 11px; text-decoration: underline;")
        else:
            self.extension_test_value.setText("미진행")
            self.extension_test_value.setStyleSheet("background-color: white; padding: 1px; border: 1px solid #bdc3c7; color: #2980b9; font-size: 11px; text-decoration: underline;")

        # 연장실험 필드 활성화/비활성화
        self._update_extension_fields_visibility(extension_test)

        # 연장기간 값 로드
        self.extend_days_input.setText(str(schedule.get('extend_period_days', '') or ''))
        self.extend_months_input.setText(str(schedule.get('extend_period_months', '') or ''))
        self.extend_years_input.setText(str(schedule.get('extend_period_years', '') or ''))
        self.extend_rounds_input.setText(str(schedule.get('extend_rounds', '') or ''))

        # 중간보고서 (행 5 - 예/아니오)
        report_interim = schedule.get('report_interim', 0)
        if report_interim:
            self.interim_report_yn_value.setText("예")
            self.interim_report_yn_value.setStyleSheet("background-color: #d5f5e3; padding: 3px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 11px; text-decoration: underline;")
        else:
            self.interim_report_yn_value.setText("아니오")
            self.interim_report_yn_value.setStyleSheet("background-color: white; padding: 3px; border: 1px solid #e67e22; color: #2980b9; font-size: 11px; text-decoration: underline;")

        # N 보고서 날짜 (report1_date, report2_date, report3_date)
        self.report1_value.setText(schedule.get('report1_date', '-') or '-')
        self.report2_value.setText(schedule.get('report2_date', '-') or '-')
        self.report3_value.setText(schedule.get('report3_date', '-') or '-')

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

        # 마지막 실험일 계산 (마지막 회차 날짜)
        if start_date != '-' and experiment_days > 0:
            try:
                from datetime import datetime, timedelta
                from database import get_connection
                start = datetime.strptime(start_date, '%Y-%m-%d')

                # 마지막 회차 날짜 = 시작일 + 실험기간
                last_experiment_date = start + timedelta(days=experiment_days)
                self.last_experiment_date_value.setText(last_experiment_date.strftime('%Y-%m-%d'))

                # 보고서 작성일 계산 (마지막 실험일 + N 영업일, 기본 15일)
                report_offset = 15  # 기본값
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM settings WHERE `key` = 'report_date_offset'")
                    result = cursor.fetchone()
                    conn.close()
                    if result and result['value']:
                        report_offset = int(result['value'])
                except (ValueError, TypeError, Exception):
                    report_offset = 15

                # 영업일 기준으로 보고서 작성일 계산
                report_date = add_business_days(last_experiment_date, report_offset)
                self.report_date_value.setText(report_date.strftime('%Y-%m-%d'))
            except (ValueError, TypeError):
                self.last_experiment_date_value.setText('-')
                self.report_date_value.setText('-')
        else:
            self.last_experiment_date_value.setText('-')
            self.report_date_value.setText('-')

        status = schedule.get('status', 'pending') or 'pending'
        status_map = get_status_map()
        status_colors = get_status_colors()
        status_text = status_map.get(status, status)
        self.status_value.setText(status_text)

        # 상태 색상 적용 (텍스트 색상으로만, 배경색은 흰색 유지)
        status_color = status_colors.get(status, '#2980b9')
        self.status_value.setStyleSheet(
            f"background-color: white; padding: 3px; border: 1px solid #bdc3c7; "
            f"color: {status_color}; font-size: 11px; text-decoration: underline; font-weight: bold;"
        )

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

                # 연장실험 진행 시 2배로 계산
                extension_test = schedule.get('extension_test', 0)
                if extension_test:
                    required_packages = required_packages * 2
                    self.required_sample_value.setText(f"{required_packages}개 (연장×2)")
                else:
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
            except (ValueError, TypeError):
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
        except Exception:
            pass

        # 단일 테이블 업데이트
        table = self.experiment_table
        col_count = sampling_count + 2
        table.setColumnCount(col_count)
        headers = ['구 분'] + [f'{i+1}회' for i in range(sampling_count)] + ['가격']
        table.setHorizontalHeaderLabels(headers)

        # 행 수: 중간보고서 + 날짜 + 제조후시간 + 검사항목들 + 1회기준
        row_count = 3 + len(test_items) + 1
        table.setRowCount(row_count)

        # 행 0: 중간보고서 시점 선택
        interim_label = QTableWidgetItem("중간보고서")
        interim_label.setBackground(QColor('#E8D0FF'))  # 연보라색
        table.setItem(0, 0, interim_label)

        # 중간보고서 콤보박스 저장용 딕셔너리
        if not hasattr(self, 'interim_report_combos'):
            self.interim_report_combos = {}
        else:
            self.interim_report_combos.clear()

        # 저장된 중간보고서 회차 선택값 가져오기
        interim1_round = schedule.get('interim1_round', 0) or 0
        interim2_round = schedule.get('interim2_round', 0) or 0
        interim3_round = schedule.get('interim3_round', 0) or 0

        for i in range(sampling_count):
            col_idx = i + 1
            combo = QComboBox()
            combo.addItems(['', '1차', '2차', '3차'])

            # 1~5회차는 비활성화, 6회차부터는 활성화
            if col_idx <= 5:
                combo.setStyleSheet("font-size: 10px; background-color: #E0E0E0; color: #888888;")
                combo.setEnabled(False)
            else:
                combo.setStyleSheet("font-size: 10px; background-color: #90EE90; color: #000000;")
                combo.setEnabled(True)

            # 저장된 값 복원
            round_num = i + 1
            if interim1_round == round_num:
                combo.setCurrentText('1차')
            elif interim2_round == round_num:
                combo.setCurrentText('2차')
            elif interim3_round == round_num:
                combo.setCurrentText('3차')

            combo.setProperty('round_col', col_idx)
            combo.currentTextChanged.connect(self.on_interim_report_combo_changed)
            self.interim_report_combos[col_idx] = combo
            table.setCellWidget(0, col_idx, combo)

        table.setItem(0, col_count - 1, QTableWidgetItem(""))

        # 행 1: 날짜
        date_label = QTableWidgetItem("날짜")
        date_label.setBackground(QColor('#ADD8E6'))
        table.setItem(1, 0, date_label)

        # 각 회차별 날짜 저장 (제조후 일수 계산용 + 중간보고서 날짜 계산용)
        self.sample_dates = {}

        # 공휴일 목록 가져오기 (날짜 색상 결정용)
        holidays = set()
        if start_date:
            holidays = get_korean_holidays(start_date.year)
            holidays.update(get_korean_holidays(start_date.year + 1))

        for i in range(sampling_count):
            col_idx = i + 1

            # 사용자 정의 날짜가 있으면 우선 사용
            if col_idx in self.custom_dates:
                sample_date = self.custom_dates[col_idx]
                date_value = sample_date.strftime('%Y-%m-%d')  # 연-월-일 형식
                self.sample_dates[col_idx] = sample_date
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)

                # 사용자 정의 날짜도 주말/공휴일 체크
                sample_date_only = sample_date.date() if hasattr(sample_date, 'date') else sample_date
                is_weekend = sample_date.weekday() >= 5
                is_holiday = sample_date_only in holidays
                if is_weekend or is_holiday:
                    date_item.setBackground(QColor('#FF8C00'))  # 진한 주황색 (수정됨 + 검토 필요)
                    date_item.setToolTip("수정됨 - 주말 또는 공휴일 검토 필요")
                else:
                    date_item.setBackground(QColor('#FFE4B5'))  # 수정된 날짜 강조 (평일)
            elif start_date:
                from datetime import timedelta
                # 마지막 회차는 정확히 experiment_days, 그 외는 균등 분배
                if i == sampling_count - 1:
                    days_offset = experiment_days
                else:
                    days_offset = round(i * interval_days)
                sample_date = start_date + timedelta(days=days_offset)
                date_value = sample_date.strftime('%Y-%m-%d')  # 연-월-일 형식
                self.sample_dates[col_idx] = sample_date
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)

                # 토요일(5), 일요일(6), 공휴일이면 주황색으로 표시
                sample_date_only = sample_date.date() if hasattr(sample_date, 'date') else sample_date
                is_weekend = sample_date.weekday() >= 5  # 토요일(5) 또는 일요일(6)
                is_holiday = sample_date_only in holidays
                if is_weekend or is_holiday:
                    date_item.setBackground(QColor('#FFA500'))  # 주황색 (검토 필요)
                    date_item.setToolTip("주말 또는 공휴일 - 검토 필요")
                else:
                    date_item.setBackground(QColor('#E6F3FF'))  # 평일 - 기존 연한 파란색
            else:
                date_value = "-"
                date_item = QTableWidgetItem(date_value)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setBackground(QColor('#E6F3FF'))

            table.setItem(1, col_idx, date_item)
        table.setItem(1, col_count - 1, QTableWidgetItem(""))

        # 행 2: 제조후 일수
        time_item = QTableWidgetItem("제조후 일수")
        time_item.setBackground(QColor('#90EE90'))
        table.setItem(2, 0, time_item)

        for i in range(sampling_count):
            col_idx = i + 1

            # self.sample_dates에 날짜가 있으면 시작일로부터 일수 계산
            if col_idx in self.sample_dates and start_date:
                days_elapsed = (self.sample_dates[col_idx] - start_date).days
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
            table.setItem(2, col_idx, item)
        table.setItem(2, col_count - 1, QTableWidgetItem(""))

        total_price_per_test = 0
        for row_idx, test_item in enumerate(test_items):
            item_label = QTableWidgetItem(test_item)
            item_label.setBackground(QColor('#90EE90'))
            table.setItem(row_idx + 3, 0, item_label)  # +3 because of interim, date and time rows

            # 저장된 O/X 상태 불러오기
            saved_row_data = self.saved_experiment_data.get(test_item, [])

            for i in range(sampling_count):
                # 저장된 상태가 있으면 사용, 없으면 기본값 "O"
                if i < len(saved_row_data) and saved_row_data[i]:
                    check_value = saved_row_data[i]
                else:
                    check_value = "O"
                check_item = QTableWidgetItem(check_value)
                check_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx + 3, i + 1, check_item)

            price = int(fees.get(test_item, 0))
            total_price_per_test += price
            price_item = QTableWidgetItem(f"{price:,}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row_idx + 3, col_count - 1, price_item)

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

        # 구분 열은 내용에 맞게 자동 조정, 나머지 열은 균등 배분
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 구분 열
        for col in range(1, col_count):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        # 저장된 연장 회차가 있으면 테이블에 추가
        extend_rounds = schedule.get('extend_rounds', 0) or 0
        if extend_rounds > 0:
            self._add_extension_rounds_to_table(extend_rounds)
            # 저장된 연장 회차 O/X 상태 복원
            self._restore_extension_rounds_state(schedule, sampling_count, extend_rounds, test_items)
            # 연장 회차 O/X 상태가 복원되었으므로 비용 재계산
            self.recalculate_costs()

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

        # 3. 보고서 비용 설정 (견적 유형별)
        # 기본 보고서 비용: 실측=200,000원, 가속=300,000원
        if test_method in ['real', 'custom_real']:
            default_report_cost = 200000
        elif test_method in ['acceleration', 'custom_acceleration']:
            default_report_cost = 300000
        else:
            default_report_cost = 200000

        # 중간보고서 여부 확인
        report_interim = schedule.get('report_interim', False)
        default_interim_cost = 200000 if report_interim else 0

        # 1차 견적 비용 (저장된 값이 있으면 사용, 없으면 기본값)
        first_report = schedule.get('first_report_cost', default_report_cost)
        first_interim = schedule.get('first_interim_cost', default_interim_cost)
        self.first_report_cost_input.setText(f"{first_report:,}")
        self.first_interim_cost_input.setText(f"{first_interim:,}")

        # 중단 견적 비용 (저장된 값이 있으면 사용, 없으면 1차 값)
        suspend_report = schedule.get('suspend_report_cost', first_report)
        suspend_interim = schedule.get('suspend_interim_cost', first_interim)
        self.suspend_report_cost_input.setText(f"{suspend_report:,}")
        self.suspend_interim_cost_input.setText(f"{suspend_interim:,}")

        # 연장 견적 비용 (저장된 값이 있으면 사용, 없으면 1차 값)
        extend_report = schedule.get('extend_report_cost', first_report)
        self.extend_report_cost_input.setText(f"{extend_report:,}")

        # 중간 보고서 필드 표시/숨김
        if report_interim:
            self.first_interim_cost_label.show()
            self.first_interim_cost_input.show()
            self.suspend_interim_cost_label.show()
            self.suspend_interim_cost_input.show()
        else:
            self.first_interim_cost_label.hide()
            self.first_interim_cost_input.hide()
            self.suspend_interim_cost_label.hide()
            self.suspend_interim_cost_input.hide()

        # 중단/연장 행 표시/숨김
        schedule_status = schedule.get('status', '')
        extend_rounds = schedule.get('extend_rounds', 0) or 0
        if schedule_status == 'suspended':
            self.row_suspend_widget.show()
        else:
            self.row_suspend_widget.hide()
        if extend_rounds > 0:
            self.row_extend_widget.show()
        else:
            self.row_extend_widget.hide()

        # 4. 최종비용 (부가세별도) - 1차 견적 기준 계산식 표시
        first_total_rounds = cost_per_test * sampling_count
        first_cost_no_vat = int(first_total_rounds * zone_count + first_report + first_interim)
        if first_interim > 0:
            formula_text = f"{first_total_rounds:,} × {zone_count} + {first_report:,} + {first_interim:,} = {first_cost_no_vat:,}원"
        else:
            formula_text = f"{first_total_rounds:,} × {zone_count} + {first_report:,} = {first_cost_no_vat:,}원"
        self.first_cost_formula.setText(formula_text)

        # 5. 최종비용 (부가세 포함) - 1차 견적 기준
        vat = int(first_cost_no_vat * 0.1)
        final_cost_with_vat = first_cost_no_vat + vat
        self.final_cost_with_vat.setText(f"{first_cost_no_vat:,} + {vat:,} = {final_cost_with_vat:,}원")

        # 금액을 DB에 저장
        self._save_amounts_to_db(first_cost_no_vat, vat, final_cost_with_vat)

        # 테이블 높이를 내용에 맞게 조절
        self._adjust_table_height()

    def _adjust_table_height(self):
        """테이블 높이를 내용(행 수)에 맞게 자동 조절"""
        table = self.experiment_table
        if table.rowCount() == 0:
            table.setFixedHeight(100)  # 최소 높이
            return

        # 헤더 높이 + 모든 행 높이 + 여백
        header_height = table.horizontalHeader().height()
        rows_height = sum(table.rowHeight(i) for i in range(table.rowCount()))
        # 스크롤바, 테두리 등을 위한 여백
        margin = 10

        total_height = header_height + rows_height + margin

        # 최소/최대 높이 제한
        min_height = 150
        max_height = 500

        adjusted_height = max(min_height, min(total_height, max_height))
        table.setFixedHeight(adjusted_height)

    def _save_amounts_to_db(self, supply_amount, tax_amount, total_amount):
        """금액을 DB에 저장"""
        if not self.current_schedule:
            return
        try:
            from models.schedules import Schedule
            schedule_id = self.current_schedule.get('id')
            if schedule_id:
                Schedule.update_amounts(schedule_id, supply_amount, tax_amount, total_amount)
                # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
                self.schedule_saved.emit()
        except Exception as e:
            print(f"금액 저장 오류: {e}")

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

                # 기본 검사항목에서 삭제된 항목 제외
                base_items_str = food_type.get('test_items', '') or ''
                base_items_list = [item.strip() for item in base_items_str.split(',') if item.strip()]

                # DB에서 저장된 추가/삭제 항목 불러오기
                import json
                additional_json = schedule_data.get('additional_test_items')
                removed_json = schedule_data.get('removed_test_items')

                additional_items = []
                removed_items = []

                if additional_json:
                    try:
                        additional_items = json.loads(additional_json)
                    except (json.JSONDecodeError, TypeError):
                        additional_items = self.additional_test_items
                else:
                    additional_items = self.additional_test_items

                if removed_json:
                    try:
                        removed_items = json.loads(removed_json)
                    except (json.JSONDecodeError, TypeError):
                        removed_items = self.removed_base_items
                else:
                    removed_items = self.removed_base_items

                # 삭제된 항목 제외한 기본 항목
                filtered_base_items = [item for item in base_items_list if item not in removed_items]

                # 최종 검사항목 = 필터링된 기본항목 + 추가항목
                all_items = filtered_base_items + additional_items
                schedule_data['test_items'] = ', '.join(all_items) if all_items else ''

        # 업체명 추가
        if schedule_data.get('client_id'):
            from models.clients import Client
            client = Client.get_by_id(schedule_data['client_id'])
            if client:
                schedule_data['client_name'] = client.get('name', '')

        # 스케줄 관리에서 계산된 비용 정보 추가 (견적 유형별)
        try:
            # 1차 견적 비용
            first_report_cost = int(self.first_report_cost_input.text().replace(',', '').replace('원', ''))
            schedule_data['first_report_cost'] = first_report_cost
            schedule_data['report_cost'] = first_report_cost  # 호환성 유지

            if self.first_interim_cost_input.isVisible():
                first_interim_cost = int(self.first_interim_cost_input.text().replace(',', '').replace('원', ''))
                schedule_data['first_interim_cost'] = first_interim_cost
                schedule_data['interim_report_cost'] = first_interim_cost  # 호환성 유지
            else:
                schedule_data['first_interim_cost'] = 0
                schedule_data['interim_report_cost'] = 0

            # 중단 견적 비용
            suspend_report_cost = int(self.suspend_report_cost_input.text().replace(',', '').replace('원', ''))
            schedule_data['suspend_report_cost'] = suspend_report_cost

            if self.suspend_interim_cost_input.isVisible():
                suspend_interim_cost = int(self.suspend_interim_cost_input.text().replace(',', '').replace('원', ''))
                schedule_data['suspend_interim_cost'] = suspend_interim_cost
            else:
                schedule_data['suspend_interim_cost'] = 0

            # 연장 견적 비용
            extend_report_cost = int(self.extend_report_cost_input.text().replace(',', '').replace('원', ''))
            schedule_data['extend_report_cost'] = extend_report_cost

            # 1회 검사비
            cost_per_test_text = self.cost_per_test.text().replace('1회:', '').replace(',', '').replace('원', '')
            if cost_per_test_text and cost_per_test_text != '-':
                schedule_data['cost_per_test'] = int(cost_per_test_text)

            # 회차 총계 (O로 체크된 항목만)
            total_rounds_text = self.total_rounds_cost.text().replace('회차:', '').replace(',', '').replace('원', '')
            if total_rounds_text and total_rounds_text != '-':
                schedule_data['total_rounds_cost'] = int(total_rounds_text)

        except Exception as e:
            print(f"비용 정보 추가 중 오류: {e}")

        # 완료 회차 정보 추가 (중단 견적서용)
        schedule_data['completed_rounds'] = self.count_completed_rounds()

        # 연장 실험 정보 추가 (연장 견적서용)
        try:
            extend_rounds = int(self.extend_rounds_input.text() or 0)
            schedule_data['extend_rounds'] = extend_rounds
        except (ValueError, AttributeError):
            schedule_data['extend_rounds'] = 0
            extend_rounds = 0

        # 연장 회차 비용 계산 (O/X 상태 반영)
        if extend_rounds > 0:
            schedule_data['extend_rounds_cost'] = self._calculate_extend_rounds_cost()
        else:
            schedule_data['extend_rounds_cost'] = 0

        # 연장 실험기간 정보 추가 (current_schedule에서 가져오기)
        schedule_data['extend_experiment_days'] = self.current_schedule.get('extend_experiment_days', 0) or 0
        schedule_data['extend_period_days'] = self.current_schedule.get('extend_period_days', 0) or 0
        schedule_data['extend_period_months'] = self.current_schedule.get('extend_period_months', 0) or 0
        schedule_data['extend_period_years'] = self.current_schedule.get('extend_period_years', 0) or 0

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
            cursor.execute("SELECT value FROM settings WHERE `key` = 'schedule_display_fields'")
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
            'interim_report': (self.extension_test_label, self.extension_test_value),
            'extension': (self.extension_label, self.extension_value),
            'sampling_count': (self.sampling_count_label, self.sampling_count_value),
            'sampling_interval': (self.sampling_interval_label, self.sampling_interval_value),
            'start_date': (self.start_date_label, self.start_date_value),
            'last_experiment_date': (self.last_experiment_date_label, self.last_experiment_date_value),
            'report_date': (self.report_date_label, self.report_date_value),
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
        # 수정 가능 여부 확인 (상태가 '대기'일 때만)
        if not self.can_edit_plan():
            return

        # 현재 테이블에 있는 항목들 수집
        current_items = self.get_test_items_from_food_type(self.current_schedule) + self.additional_test_items

        # 항목 선택 다이얼로그
        dialog = TestItemSelectDialog(self, exclude_items=current_items)
        if dialog.exec_() and dialog.selected_item:
            # 추가된 항목 저장
            self.additional_test_items.append(dialog.selected_item)

            # 활동 로그 기록
            self.log_activity('schedule_item_add', details={'item': dialog.selected_item})

            # 테이블 새로고침
            self.update_experiment_schedule(self.current_schedule)

            # 검체량 정보 업데이트
            sampling_count = self.current_schedule.get('sampling_count', 6) or 6
            self.update_sample_info(self.current_schedule, sampling_count)

            QMessageBox.information(self, "추가 완료", f"'{dialog.selected_item}' 항목이 추가되었습니다.")

    def remove_test_item(self):
        """검사항목 삭제"""
        # 수정 가능 여부 확인 (상태가 '대기'일 때만)
        if not self.can_edit_plan():
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

            # 활동 로그 기록
            self.log_activity('schedule_item_delete', details={'item': item})

            # 테이블 새로고침
            self.update_experiment_schedule(self.current_schedule)

            # 검체량 정보 업데이트
            sampling_count = self.current_schedule.get('sampling_count', 6) or 6
            self.update_sample_info(self.current_schedule, sampling_count)

            QMessageBox.information(self, "삭제 완료", f"'{item}' 항목이 삭제되었습니다.")

    def save_schedule_changes(self):
        """스케줄 변경사항 저장 (상태, 중간보고서, 추가/삭제 항목, O/X 상태, 시작일 등)"""
        if not self.current_schedule:
            QMessageBox.warning(self, "저장 실패", "먼저 스케줄을 선택하세요.")
            return

        try:
            import json
            from database import get_connection

            schedule_id = self.current_schedule.get('id')
            if not schedule_id:
                QMessageBox.warning(self, "저장 실패", "스케줄 ID를 찾을 수 없습니다.")
                return

            # 추가된 검사항목을 JSON으로 변환
            additional_items_json = json.dumps(self.additional_test_items, ensure_ascii=False) if self.additional_test_items else None

            # 삭제된 기본 검사항목을 JSON으로 변환
            removed_items_json = json.dumps(self.removed_base_items, ensure_ascii=False) if self.removed_base_items else None

            # 실험 스케줄 O/X 상태 수집
            experiment_data = self._collect_experiment_schedule_data()
            experiment_data_json = json.dumps(experiment_data, ensure_ascii=False) if experiment_data else None

            # 상태 코드 가져오기
            status = self.current_schedule.get('status', 'pending')

            # 중간보고서 여부
            report_interim = self.current_schedule.get('report_interim', 0)

            # 시작일 (변경되었을 수 있음)
            start_date = self.current_schedule.get('start_date', '')

            # 사용자 수정 날짜를 JSON으로 변환 (datetime 객체를 문자열로 변환)
            custom_dates_serializable = {}
            if self.custom_dates:
                for col, date_val in self.custom_dates.items():
                    if hasattr(date_val, 'strftime'):
                        custom_dates_serializable[col] = date_val.strftime('%Y-%m-%d')
                    else:
                        custom_dates_serializable[col] = str(date_val)
            custom_dates_json = json.dumps(custom_dates_serializable, ensure_ascii=False) if custom_dates_serializable else None

            # 실제 실험일수 (날짜 수정 시 계산된 값)
            actual_experiment_days = self.current_schedule.get('actual_experiment_days')

            # 중간보고서 날짜 및 회차 정보
            report1_date = self.current_schedule.get('report1_date', '') or ''
            report2_date = self.current_schedule.get('report2_date', '') or ''
            report3_date = self.current_schedule.get('report3_date', '') or ''
            interim1_round = self.current_schedule.get('interim1_round', 0) or 0
            interim2_round = self.current_schedule.get('interim2_round', 0) or 0
            interim3_round = self.current_schedule.get('interim3_round', 0) or 0

            # 연장 실험 관련 정보
            extend_period_days = self.current_schedule.get('extend_period_days', 0) or 0
            extend_period_months = self.current_schedule.get('extend_period_months', 0) or 0
            extend_period_years = self.current_schedule.get('extend_period_years', 0) or 0
            extend_experiment_days = self.current_schedule.get('extend_experiment_days', 0) or 0
            extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0

            # 데이터베이스 업데이트
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE schedules SET
                    additional_test_items = %s,
                    removed_test_items = %s,
                    experiment_schedule_data = %s,
                    status = %s,
                    report_interim = %s,
                    start_date = %s,
                    custom_dates = %s,
                    actual_experiment_days = %s,
                    report1_date = %s,
                    report2_date = %s,
                    report3_date = %s,
                    interim1_round = %s,
                    interim2_round = %s,
                    interim3_round = %s,
                    extend_period_days = %s,
                    extend_period_months = %s,
                    extend_period_years = %s,
                    extend_experiment_days = %s,
                    extend_rounds = %s
                WHERE id = %s
            """, (additional_items_json, removed_items_json, experiment_data_json,
                  status, report_interim, start_date, custom_dates_json, actual_experiment_days,
                  report1_date, report2_date, report3_date,
                  interim1_round, interim2_round, interim3_round,
                  extend_period_days, extend_period_months, extend_period_years,
                  extend_experiment_days, extend_rounds, schedule_id))

            conn.commit()
            conn.close()

            # 활동 로그 기록
            self.log_activity(
                'schedule_edit',
                details={
                    'action': '스케줄 변경사항 저장',
                    'additional_items': len(self.additional_test_items) if self.additional_test_items else 0,
                    'removed_items': len(self.removed_base_items) if self.removed_base_items else 0
                }
            )

            QMessageBox.information(self, "저장 완료", "스케줄 변경사항이 저장되었습니다.")
            self.schedule_saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _collect_experiment_schedule_data(self):
        """실험 스케줄 테이블의 O/X 상태 수집 (연장 회차 포함)"""
        if not self.current_schedule:
            return None

        data = {}
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        total_rounds = sampling_count + extend_rounds
        row_count = self.experiment_table.rowCount()

        # 검사항목 행 (행 3부터 마지막 가격 행 제외 - 중간보고서, 날짜, 제조후일수 행 다음)
        for row in range(3, row_count - 1):
            item_cell = self.experiment_table.item(row, 0)
            if not item_cell:
                continue

            test_item = item_cell.text()
            if not test_item:
                continue

            row_data = []
            for col in range(1, total_rounds + 1):
                cell = self.experiment_table.item(row, col)
                if cell:
                    row_data.append(cell.text())
                else:
                    row_data.append('')

            data[test_item] = row_data

        return data

    def change_status(self):
        """상태 클릭 시 변경 가능하도록 (커스텀 상태 사용, 즉시 DB 저장)"""
        if not self.current_schedule:
            QMessageBox.warning(self, "변경 실패", "먼저 스케줄을 선택하세요.")
            return

        # 권한 확인 (상태 변경은 schedule_mgmt_edit_plan 권한 필요)
        if self.current_user and self.current_user.get('role') != 'admin':
            from models.users import User
            if not User.has_permission(self.current_user, 'schedule_mgmt_edit_plan'):
                QMessageBox.warning(self, "권한 없음", "실험 계획안 수정 권한이 없습니다.")
                return

        from PyQt5.QtWidgets import QInputDialog

        # 커스텀 상태 목록 가져오기
        status_options = get_status_names()
        status_colors = get_status_colors()
        current_status = self.status_value.text()
        old_status = current_status  # 로그용

        # 현재 상태의 인덱스 찾기
        try:
            current_index = status_options.index(current_status)
        except ValueError:
            current_index = 0

        new_status, ok = QInputDialog.getItem(
            self, "상태 변경", "새 상태를 선택하세요:",
            status_options, current_index, False
        )

        if ok and new_status:
            # 상태 코드로 변환
            status_code = get_status_code_by_name(new_status)

            # 현재 스케줄 정보 업데이트
            self.current_schedule['status'] = status_code
            self.status_value.setText(new_status)

            # 스타일 변경 (배경 흰색 유지, 텍스트 색상만 변경)
            color = status_colors.get(status_code, '#2980b9')
            self.status_value.setStyleSheet(
                f"background-color: white; padding: 3px; border: 1px solid #bdc3c7; "
                f"color: {color}; font-size: 11px; text-decoration: underline; font-weight: bold;"
            )

            # DB에 즉시 저장
            try:
                from database import get_connection
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE schedules SET status = %s WHERE id = %s", (status_code, schedule_id))
                    conn.commit()
                    conn.close()

                    # 활동 로그 기록
                    self.log_activity(
                        'schedule_status_change',
                        details={'old_status': old_status, 'new_status': new_status}
                    )

                    # 스케줄 저장 시그널 발생 (스케줄 작성 탭 새로고침용)
                    self.schedule_saved.emit()
            except Exception as e:
                print(f"상태 저장 오류: {e}")

    def toggle_interim_report(self):
        """중간보고서 요청/미요청 토글"""
        # 수정 가능 여부 확인 (상태가 '대기'일 때만, 권한 확인)
        if not self.can_edit_plan():
            return

        from PyQt5.QtWidgets import QInputDialog

        options = ["예", "아니오"]
        current_value = self.interim_report_yn_value.text()
        old_value = current_value  # 로그용

        try:
            current_index = options.index(current_value)
        except ValueError:
            current_index = 1

        new_value, ok = QInputDialog.getItem(
            self, "중간보고서 설정", "중간보고서 요청 여부:",
            options, current_index, False
        )

        if ok and new_value:
            is_requested = (new_value == "예")
            self.current_schedule['report_interim'] = 1 if is_requested else 0

            # 스타일 업데이트
            if is_requested:
                self.interim_report_yn_value.setText("예")
                self.interim_report_yn_value.setStyleSheet("background-color: #d5f5e3; padding: 3px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold; font-size: 11px; text-decoration: underline;")
            else:
                self.interim_report_yn_value.setText("아니오")
                self.interim_report_yn_value.setStyleSheet("background-color: white; padding: 3px; border: 1px solid #e67e22; color: #2980b9; font-size: 11px; text-decoration: underline;")

            # DB에 저장
            try:
                from models.schedules import Schedule
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    Schedule.update(schedule_id, report_interim=1 if is_requested else 0)
            except Exception as e:
                print(f"중간보고서 저장 오류: {e}")

            # 활동 로그 기록
            self.log_activity(
                'schedule_edit',
                details={'field': '중간보고서', 'old_value': old_value, 'new_value': new_value}
            )

            # 비용 요약 업데이트
            self._update_cost_after_interim_change()

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def _update_cost_after_interim_change(self):
        """중간보고서 변경 후 비용 업데이트"""
        if not self.current_schedule:
            return

        report_interim = self.current_schedule.get('report_interim', 0)

        if report_interim:
            self.interim_cost_label.show()
            self.interim_report_cost_input.show()
            self.interim_report_cost_input.setText("200,000")
        else:
            self.interim_cost_label.hide()
            self.interim_report_cost_input.hide()

        # 비용 재계산
        self.recalculate_costs()

    def toggle_extension_test(self):
        """연장실험 진행/미진행 토글"""
        # 수정 가능 여부 확인
        if not self.can_edit_plan():
            return

        from PyQt5.QtWidgets import QInputDialog

        options = ["진행", "미진행"]
        current_value = self.extension_test_value.text()
        old_value = current_value

        try:
            current_index = options.index(current_value)
        except ValueError:
            current_index = 1

        new_value, ok = QInputDialog.getItem(
            self, "연장실험 설정", "연장실험 진행 여부:",
            options, current_index, False
        )

        if ok and new_value:
            is_extension = (new_value == "진행")
            self.current_schedule['extension_test'] = 1 if is_extension else 0
            self.extension_test_value.setText(new_value)

            # 연장실험 진행 시 연장기간 입력 활성화
            self._update_extension_fields_visibility(is_extension)

            # DB에 저장
            try:
                from models.schedules import Schedule
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    Schedule.update(schedule_id, extension_test=1 if is_extension else 0)
            except Exception as e:
                print(f"연장실험 저장 오류: {e}")

            # 활동 로그 기록
            self.log_activity(
                'schedule_edit',
                details={'field': '연장실험', 'old_value': old_value, 'new_value': new_value}
            )

            # 스케줄 저장 시그널 발생
            self.schedule_saved.emit()

    def _update_extension_fields_visibility(self, is_extension):
        """연장실험 필드 활성화/비활성화"""
        enabled = is_extension
        self.extend_days_input.setEnabled(enabled)
        self.extend_months_input.setEnabled(enabled)
        self.extend_years_input.setEnabled(enabled)
        self.extend_rounds_input.setEnabled(enabled)
        self.calc_rounds_btn.setEnabled(enabled)

        if not enabled:
            self.extend_days_input.clear()
            self.extend_months_input.clear()
            self.extend_years_input.clear()
            self.extend_rounds_input.clear()
            self.extend_experiment_period_value.setText("-")

    def on_extend_period_changed(self):
        """연장기간 변경 시 연장 실험기간 자동 계산"""
        if not self.current_schedule:
            return

        try:
            days = int(self.extend_days_input.text() or 0)
            months = int(self.extend_months_input.text() or 0)
            years = int(self.extend_years_input.text() or 0)

            # 총 연장기간 (일수로 변환)
            total_days = days + (months * 30) + (years * 365)

            if total_days <= 0:
                self.extend_experiment_period_value.setText("-")
                return

            # 실험방법에 따른 실험기간 계산
            test_method = self.current_schedule.get('test_method', 'real')

            if test_method in ['real', 'custom_real']:
                # 실측: 1.5배
                experiment_days = int(total_days * 1.5)
            else:
                # 가속: 1/2
                experiment_days = total_days // 2

            # 년/월/일 형식으로 변환
            exp_years = experiment_days // 365
            exp_months = (experiment_days % 365) // 30
            exp_days = experiment_days % 30

            period_parts = []
            if exp_years > 0:
                period_parts.append(f"{exp_years}년")
            if exp_months > 0:
                period_parts.append(f"{exp_months}개월")
            if exp_days > 0:
                period_parts.append(f"{exp_days}일")

            period_str = " ".join(period_parts) if period_parts else f"{experiment_days}일"
            self.extend_experiment_period_value.setText(period_str)

            # 현재 스케줄에 저장
            self.current_schedule['extend_period_days'] = days
            self.current_schedule['extend_period_months'] = months
            self.current_schedule['extend_period_years'] = years
            self.current_schedule['extend_experiment_days'] = experiment_days

        except ValueError:
            self.extend_experiment_period_value.setText("-")

    def add_business_days(self, start_date, num_days):
        """영업일 기준으로 날짜 계산 (주말 및 공휴일 제외)"""
        from datetime import timedelta

        holidays = get_korean_holidays(start_date.year)
        holidays.update(get_korean_holidays(start_date.year + 1))

        current_date = start_date
        days_added = 0

        while days_added < num_days:
            current_date += timedelta(days=1)
            # 주말(토=5, 일=6) 또는 공휴일이면 건너뜀
            current_date_only = current_date.date() if hasattr(current_date, 'date') else current_date
            if current_date.weekday() < 5 and current_date_only not in holidays:
                days_added += 1

        return current_date

    def on_interim_report_combo_changed(self, text):
        """중간보고서 시점 선택 변경 시 처리"""
        if not self.current_schedule:
            return

        sender = self.sender()
        if not sender:
            return

        col_idx = sender.property('round_col')
        if col_idx is None:
            return

        round_num = col_idx  # 회차 번호 (1, 2, 3, ...)

        # 다른 콤보박스에서 같은 값이 선택되어 있으면 해제
        if text:
            for idx, combo in self.interim_report_combos.items():
                if idx != col_idx and combo.currentText() == text:
                    combo.blockSignals(True)
                    combo.setCurrentText('')
                    combo.blockSignals(False)

        # 선택된 회차의 날짜 가져오기
        if col_idx in self.sample_dates and text:
            sample_date = self.sample_dates[col_idx]
            # 영업일 기준 +15일 계산
            report_date = self.add_business_days(sample_date, 15)
            report_date_str = report_date.strftime('%Y-%m-%d')

            # 해당 중간보고서 날짜 업데이트
            if text == '1차':
                self.report1_value.setText(report_date_str)
                if self.current_schedule:
                    self.current_schedule['report1_date'] = report_date_str
                    self.current_schedule['interim1_round'] = round_num
            elif text == '2차':
                self.report2_value.setText(report_date_str)
                if self.current_schedule:
                    self.current_schedule['report2_date'] = report_date_str
                    self.current_schedule['interim2_round'] = round_num
            elif text == '3차':
                self.report3_value.setText(report_date_str)
                if self.current_schedule:
                    self.current_schedule['report3_date'] = report_date_str
                    self.current_schedule['interim3_round'] = round_num
        else:
            # 선택 해제된 경우 해당 보고서 날짜 초기화
            if text == '' and self.current_schedule:
                # 어떤 보고서가 해제되었는지 확인
                for report_num in ['1차', '2차', '3차']:
                    found = False
                    for idx, combo in self.interim_report_combos.items():
                        if combo.currentText() == report_num:
                            found = True
                            break
                    if not found:
                        if report_num == '1차':
                            self.report1_value.setText('-')
                            self.current_schedule['report1_date'] = ''
                            self.current_schedule['interim1_round'] = 0
                        elif report_num == '2차':
                            self.report2_value.setText('-')
                            self.current_schedule['report2_date'] = ''
                            self.current_schedule['interim2_round'] = 0
                        elif report_num == '3차':
                            self.report3_value.setText('-')
                            self.current_schedule['report3_date'] = ''
                            self.current_schedule['interim3_round'] = 0

    def _update_interim_report_date_for_round(self, round_num):
        """특정 회차의 날짜가 변경되었을 때 연결된 중간보고서 날짜 재계산"""
        if not self.current_schedule:
            return

        # 해당 회차에 연결된 중간보고서 확인
        interim1_round = self.current_schedule.get('interim1_round', 0) or 0
        interim2_round = self.current_schedule.get('interim2_round', 0) or 0
        interim3_round = self.current_schedule.get('interim3_round', 0) or 0

        # 해당 회차의 새 날짜 가져오기
        if round_num not in self.sample_dates:
            return

        sample_date = self.sample_dates[round_num]

        # 영업일 기준 +15일 계산
        report_date = self.add_business_days(sample_date, 15)
        report_date_str = report_date.strftime('%Y-%m-%d')

        # 해당 회차에 연결된 중간보고서 날짜 업데이트
        if interim1_round == round_num:
            self.report1_value.setText(report_date_str)
            self.current_schedule['report1_date'] = report_date_str

        if interim2_round == round_num:
            self.report2_value.setText(report_date_str)
            self.current_schedule['report2_date'] = report_date_str

        if interim3_round == round_num:
            self.report3_value.setText(report_date_str)
            self.current_schedule['report3_date'] = report_date_str

    def show_extend_rounds_dialog(self):
        """연장 회차 계산 다이얼로그 표시"""
        if not self.current_schedule:
            QMessageBox.warning(self, "경고", "스케줄을 먼저 선택해주세요.")
            return

        # 연장 실험기간 확인
        extend_experiment_days = self.current_schedule.get('extend_experiment_days', 0)
        if not extend_experiment_days or extend_experiment_days <= 0:
            QMessageBox.warning(self, "경고", "연장기간을 먼저 입력해주세요.")
            return

        # 샘플링 간격 가져오기
        sampling_interval = self.current_schedule.get('sampling_interval', 15) or 15

        # 자동 계산 가능 회차
        auto_rounds = extend_experiment_days // sampling_interval
        if auto_rounds <= 0:
            auto_rounds = 1

        # 다이얼로그 표시
        msg = QMessageBox(self)
        msg.setWindowTitle("연장 회차 설정")
        msg.setText(f"기존 샘플링 주기({sampling_interval}일)로 회차를 자동 계산하시겠습니까?\n\n"
                   f"연장 실험기간: {extend_experiment_days}일\n"
                   f"자동 계산 시: {auto_rounds}회차 추가")
        msg.setIcon(QMessageBox.Question)

        yes_btn = msg.addButton("예 (자동 계산)", QMessageBox.YesRole)
        no_btn = msg.addButton("아니요 (직접 입력)", QMessageBox.NoRole)
        cancel_btn = msg.addButton("취소", QMessageBox.RejectRole)

        msg.exec_()

        clicked = msg.clickedButton()

        if clicked == yes_btn:
            # 자동 계산으로 회차 설정
            self.extend_rounds_input.setText(str(auto_rounds))
        elif clicked == no_btn:
            # 직접 입력 다이얼로그
            self._show_manual_rounds_dialog(extend_experiment_days, sampling_interval)

    def _show_manual_rounds_dialog(self, extend_experiment_days, sampling_interval):
        """연장 회차 직접 입력 다이얼로그"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("연장 회차 직접 입력")
        dialog.setFixedWidth(350)

        layout = QVBoxLayout(dialog)

        # 안내 메시지
        info_label = QLabel(f"연장 실험기간: {extend_experiment_days}일\n"
                           f"기존 샘플링 주기: {sampling_interval}일\n\n"
                           f"추가할 회차 수를 입력하세요:")
        info_label.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 회차 입력
        input_layout = QHBoxLayout()
        input_label = QLabel("추가 회차:")
        input_label.setStyleSheet("font-size: 12px;")
        input_layout.addWidget(input_label)

        rounds_spin = QSpinBox()
        rounds_spin.setRange(1, 50)
        rounds_spin.setValue(1)
        rounds_spin.setFixedWidth(80)
        rounds_spin.setStyleSheet("font-size: 12px;")
        input_layout.addWidget(rounds_spin)

        unit_label = QLabel("회")
        unit_label.setStyleSheet("font-size: 12px;")
        input_layout.addWidget(unit_label)
        input_layout.addStretch()

        layout.addLayout(input_layout)

        # 새 샘플링 간격 표시
        interval_info = QLabel("")
        interval_info.setStyleSheet("font-size: 11px; color: #666; margin-top: 10px;")
        layout.addWidget(interval_info)

        def update_interval_info():
            rounds = rounds_spin.value()
            if rounds > 0:
                new_interval = extend_experiment_days // rounds
                interval_info.setText(f"→ 새 샘플링 간격: 약 {new_interval}일")

        rounds_spin.valueChanged.connect(update_interval_info)
        update_interval_info()

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            self.extend_rounds_input.setText(str(rounds_spin.value()))

    def on_extend_rounds_changed(self):
        """연장 회차 변경 시 스케줄 테이블 업데이트"""
        if not self.current_schedule:
            return

        try:
            extend_rounds = int(self.extend_rounds_input.text() or 0)

            if extend_rounds <= 0:
                return

            # 현재 스케줄에 저장
            self.current_schedule['extend_rounds'] = extend_rounds

            # 연장 회차 스케줄 생성 및 테이블 업데이트
            self._add_extension_rounds_to_table(extend_rounds)

        except ValueError:
            pass

    def _add_extension_rounds_to_table(self, extend_rounds):
        """연장 회차를 스케줄 테이블에 추가"""
        if not hasattr(self, 'experiment_table') or not self.current_schedule:
            return

        from datetime import datetime, timedelta
        from PyQt5.QtWidgets import QTableWidgetItem, QComboBox
        from PyQt5.QtGui import QColor
        from PyQt5.QtCore import Qt

        # 기존 샘플링 횟수와 간격 가져오기
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        sampling_interval = self.current_schedule.get('sampling_interval', 15) or 15

        # 마지막 실험일 가져오기
        last_date_str = self.current_schedule.get('last_experiment_date', '')
        if not last_date_str:
            last_date_str = self.last_experiment_date_value.text()

        if not last_date_str or last_date_str == '-':
            return

        try:
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return

        # 시작일 가져오기 (제조후 일수 계산용)
        start_date_str = self.current_schedule.get('start_date', '')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                start_date = last_date
        else:
            start_date = last_date

        # 연장 회차 데이터 생성
        extension_schedules = []
        for i in range(extend_rounds):
            round_num = sampling_count + i + 1  # 기존 회차에 이어서
            round_date = last_date + timedelta(days=sampling_interval * (i + 1))
            days_after_start = (round_date - start_date).days

            extension_schedules.append({
                'round': round_num,
                'date': round_date.strftime('%Y-%m-%d'),
                'days_after': days_after_start
            })

            # 연장 회차 날짜를 sample_dates에 저장 (중간보고서 날짜 계산용)
            col_idx = sampling_count + 1 + i
            self.sample_dates[col_idx] = round_date

        # 현재 스케줄에 연장 데이터 저장
        self.current_schedule['extension_schedules'] = extension_schedules

        # 테이블에 연장 회차 열 추가
        table = self.experiment_table
        current_col_count = table.columnCount()
        row_count = table.rowCount()

        # 기존 열 수: 구분(1) + 기존회차(sampling_count) + 가격(1) = sampling_count + 2
        # 가격 열 위치: 마지막 열
        price_col = current_col_count - 1

        # 새 열 수: 기존 + 연장 회차
        new_col_count = sampling_count + 2 + extend_rounds
        table.setColumnCount(new_col_count)

        # 헤더 업데이트
        headers = ['구 분'] + [f'{i+1}회' for i in range(sampling_count + extend_rounds)] + ['가격']
        table.setHorizontalHeaderLabels(headers)

        # 가격 열 데이터를 새 마지막 열로 이동
        for row in range(row_count):
            old_price_item = table.takeItem(row, price_col)
            if old_price_item:
                table.setItem(row, new_col_count - 1, old_price_item)

        # 1회 기준 가격 계산용 (기존 1회차 열의 1회기준 값 사용)
        total_price_per_test = 0
        basis_row = row_count - 1  # 마지막 행 (1회 기준)

        # 기존 1회차의 1회기준 가격 가져오기
        basis_item = table.item(basis_row, 1)  # 1회 열
        if basis_item:
            try:
                price_text = basis_item.text().replace(',', '')
                total_price_per_test = int(price_text)
            except (ValueError, AttributeError):
                total_price_per_test = 0

        # 연장 회차 데이터 채우기
        for i, ext_schedule in enumerate(extension_schedules):
            col_idx = sampling_count + 1 + i  # 기존 회차 다음 열

            # 행 0: 중간보고서 콤보박스 (연장 회차는 활성화)
            combo = QComboBox()
            combo.addItems(['', '1차', '2차', '3차'])
            combo.setStyleSheet("font-size: 10px; background-color: #90EE90; color: #000000;")  # 연두색 배경 (활성화)
            combo.setEnabled(True)

            # 저장된 중간보고서 값 복원
            interim1_round = self.current_schedule.get('interim1_round', 0) or 0
            interim2_round = self.current_schedule.get('interim2_round', 0) or 0
            interim3_round = self.current_schedule.get('interim3_round', 0) or 0
            if interim1_round == col_idx:
                combo.setCurrentText('1차')
            elif interim2_round == col_idx:
                combo.setCurrentText('2차')
            elif interim3_round == col_idx:
                combo.setCurrentText('3차')

            combo.setProperty('round_col', col_idx)
            combo.currentTextChanged.connect(self.on_interim_report_combo_changed)
            self.interim_report_combos[col_idx] = combo
            table.setCellWidget(0, col_idx, combo)

            # 행 1: 날짜 (연장 회차는 연두색 배경)
            date_item = QTableWidgetItem(ext_schedule['date'])
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setBackground(QColor('#90EE90'))  # 연두색 (연장 회차 표시)
            date_item.setToolTip("연장 회차")
            table.setItem(1, col_idx, date_item)

            # 행 2: 제조후 일수
            days_item = QTableWidgetItem(f"{ext_schedule['days_after']}일")
            days_item.setTextAlignment(Qt.AlignCenter)
            days_item.setBackground(QColor('#90EE90'))  # 연두색
            table.setItem(2, col_idx, days_item)

            # 행 3 이후: 검사항목에 O 표시
            for row in range(3, row_count - 1):  # 마지막 행(1회기준)은 제외
                o_item = QTableWidgetItem("O")
                o_item.setTextAlignment(Qt.AlignCenter)
                o_item.setBackground(QColor('#F0FFF0'))  # 연한 연두색
                table.setItem(row, col_idx, o_item)

            # 마지막 행: 1회기준 소계
            cost_item = QTableWidgetItem(f"{total_price_per_test:,}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            cost_item.setBackground(QColor('#FFFF99'))  # 노란색 (1회기준 행)
            table.setItem(row_count - 1, col_idx, cost_item)

        # 열 너비 재설정: 구분 열은 자동 조정, 나머지 열은 균등 배분
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 구분 열
        for col in range(1, new_col_count):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        # 스케줄 저장 시그널 발생
        self.schedule_saved.emit()

    def _restore_extension_rounds_state(self, schedule, sampling_count, extend_rounds, test_items):
        """저장된 연장 회차 O/X 상태 복원"""
        import json
        from PyQt5.QtGui import QColor, QBrush

        # 저장된 실험 데이터 가져오기
        experiment_data_json = schedule.get('experiment_schedule_data', '')
        if not experiment_data_json:
            return

        try:
            saved_data = json.loads(experiment_data_json)
        except (json.JSONDecodeError, TypeError):
            return

        table = self.experiment_table
        row_count = table.rowCount()

        # 각 검사항목에 대해 연장 회차 상태 복원
        for row in range(3, row_count - 1):
            item_cell = table.item(row, 0)
            if not item_cell:
                continue

            test_item = item_cell.text()
            if test_item not in saved_data:
                continue

            saved_row_data = saved_data[test_item]

            # 연장 회차 열에 대해서만 상태 복원
            for i in range(extend_rounds):
                col_idx = sampling_count + 1 + i
                data_idx = sampling_count + i

                if data_idx < len(saved_row_data):
                    saved_value = saved_row_data[data_idx]
                    cell = table.item(row, col_idx)
                    if cell and saved_value:
                        cell.setText(saved_value)
                        if saved_value == 'X':
                            cell.setForeground(QBrush(QColor('#e74c3c')))  # 빨간색

    def edit_last_experiment_date_with_calendar(self):
        """달력을 통해 마지막 실험일 수정"""
        # 수정 가능 여부 확인 (상태가 '대기'일 때만, 권한 확인)
        if not self.can_edit_plan():
            return

        current_date_text = self.last_experiment_date_value.text()
        old_date = current_date_text  # 로그용

        # 현재 표시된 날짜를 파싱하여 달력 초기값으로 설정
        current_date = None
        if current_date_text and current_date_text != "-":
            try:
                from datetime import datetime
                current_date = datetime.strptime(current_date_text, '%Y-%m-%d')
            except (ValueError, TypeError):
                current_date = None

        # 날짜 선택 다이얼로그 표시
        dialog = DateSelectDialog(self, current_date=current_date, title="마지막 실험일 선택")
        if dialog.exec_() and dialog.selected_date:
            # 선택된 날짜 저장
            new_date_str = dialog.selected_date.strftime('%Y-%m-%d')
            self.last_experiment_date_value.setText(new_date_str)

            # 활동 로그 기록
            self.log_activity(
                'schedule_date_edit',
                details={'field': '마지막실험일', 'old_date': old_date, 'new_date': new_date_str}
            )

            # 스타일 변경 (수정된 날짜 강조)
            value_style = "background-color: #FFE4B5; padding: 3px; border: 1px solid #bdc3c7; color: #2980b9; font-size: 11px; text-decoration: underline;"
            self.last_experiment_date_value.setStyleSheet(value_style)

            # 현재 스케줄에도 저장 (저장 시 반영됨)
            self.current_schedule['last_experiment_date_custom'] = new_date_str

            # 보고서 작성일 재계산
            self._update_report_date(dialog.selected_date)

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def _update_report_date(self, last_experiment_date):
        """마지막 실험일 기준으로 보고서 작성일 재계산"""
        from database import get_connection

        # 설정에서 보고서 작성일 오프셋 가져오기 (영업일 기준, 기본 15일)
        report_offset = 15
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'report_date_offset'")
            result = cursor.fetchone()
            conn.close()
            if result and result['value']:
                report_offset = int(result['value'])
        except (ValueError, TypeError, Exception):
            report_offset = 15

        # 영업일 기준으로 보고서 작성일 계산
        report_date = add_business_days(last_experiment_date, report_offset)
        self.report_date_value.setText(report_date.strftime('%Y-%m-%d'))

    def toggle_urgent_status(self):
        """긴급여부 토글"""
        # 수정 가능 여부 확인 (상태가 '대기'일 때만, 권한 확인)
        if not self.can_edit_plan():
            return

        from PyQt5.QtWidgets import QInputDialog

        options = ["일반", "긴급"]
        current_value = self.urgent_value.text()
        old_value = current_value  # 로그용

        try:
            current_index = options.index(current_value)
        except ValueError:
            current_index = 0

        new_value, ok = QInputDialog.getItem(
            self, "긴급여부 설정", "긴급 여부:",
            options, current_index, False
        )

        if ok and new_value:
            is_urgent = (new_value == "긴급")
            self.current_schedule['is_urgent'] = 1 if is_urgent else 0
            self.urgent_value.setText(new_value)

            # 긴급일 경우 빨간색으로 스타일 변경
            if is_urgent:
                self.urgent_value.setStyleSheet("background-color: #ffcccc; padding: 3px; border: 1px solid #e74c3c; color: #e74c3c; font-weight: bold; font-size: 11px; text-decoration: underline;")
            else:
                self.urgent_value.setStyleSheet("background-color: white; padding: 3px; border: 1px solid #bdc3c7; color: #2980b9; font-size: 11px; text-decoration: underline;")

            # DB에 저장
            try:
                from models.schedules import Schedule
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    Schedule.update(schedule_id, is_urgent=1 if is_urgent else 0)
            except Exception as e:
                print(f"긴급여부 저장 오류: {e}")

            # 활동 로그 기록
            self.log_activity(
                'schedule_edit',
                details={'field': '긴급여부', 'old_value': old_value, 'new_value': new_value}
            )

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def edit_report_date_with_calendar(self):
        """달력을 통해 보고서 작성일 수정"""
        # 수정 가능 여부 확인
        if not self.can_edit_plan():
            return

        current_date_text = self.report_date_value.text()
        old_date = current_date_text  # 로그용

        # 현재 표시된 날짜를 파싱하여 달력 초기값으로 설정
        current_date = None
        if current_date_text and current_date_text != "-":
            try:
                from datetime import datetime
                current_date = datetime.strptime(current_date_text, '%Y-%m-%d')
            except (ValueError, TypeError):
                current_date = None

        # 날짜 선택 다이얼로그 표시
        dialog = DateSelectDialog(self, current_date=current_date, title="보고서 작성일 선택")
        if dialog.exec_() and dialog.selected_date:
            # 선택된 날짜 저장
            new_date_str = dialog.selected_date.strftime('%Y-%m-%d')
            self.report_date_value.setText(new_date_str)

            # 활동 로그 기록
            self.log_activity(
                'schedule_date_edit',
                details={'field': '보고서작성일', 'old_date': old_date, 'new_date': new_date_str}
            )

            # 스타일 변경 (수정된 날짜 강조)
            value_style = "background-color: #FFE4B5; padding: 3px; border: 1px solid #bdc3c7; color: #2980b9; font-size: 11px; text-decoration: underline;"
            self.report_date_value.setStyleSheet(value_style)

            # 현재 스케줄에도 저장 (저장 시 반영됨)
            self.current_schedule['report_date_custom'] = new_date_str

            # DB에 저장
            try:
                from models.schedules import Schedule
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    Schedule.update(schedule_id, report_date=new_date_str)
            except Exception as e:
                print(f"보고서 작성일 저장 오류: {e}")

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def edit_report_date_with_calendar_n(self, report_num):
        """달력을 통해 N번 보고서 날짜 수정 (1, 2, 3)"""
        # 수정 가능 여부 확인
        if not self.can_edit_plan():
            return

        # 해당 보고서 날짜 위젯 가져오기
        report_value_widgets = {
            1: self.report1_value,
            2: self.report2_value,
            3: self.report3_value
        }
        report_value = report_value_widgets.get(report_num)
        if not report_value:
            return

        current_date_text = report_value.text()
        old_date = current_date_text  # 로그용

        # 현재 표시된 날짜를 파싱하여 달력 초기값으로 설정
        current_date = None
        if current_date_text and current_date_text != "-":
            try:
                from datetime import datetime
                current_date = datetime.strptime(current_date_text, '%Y-%m-%d')
            except (ValueError, TypeError):
                current_date = None

        # 날짜 선택 다이얼로그 표시
        dialog = DateSelectDialog(self, current_date=current_date, title=f"{report_num} 보고서 날짜 선택")
        if dialog.exec_() and dialog.selected_date:
            # 선택된 날짜 저장
            new_date_str = dialog.selected_date.strftime('%Y-%m-%d')
            report_value.setText(new_date_str)

            # 활동 로그 기록
            self.log_activity(
                'schedule_date_edit',
                details={'field': f'{report_num}보고서', 'old_date': old_date, 'new_date': new_date_str}
            )

            # 스타일 변경 (수정된 날짜 강조)
            value_style = "background-color: #FFE4B5; padding: 3px; border: 1px solid #e67e22; color: #e67e22; font-weight: bold; font-size: 11px; text-decoration: underline;"
            report_value.setStyleSheet(value_style)

            # 현재 스케줄에도 저장 (저장 시 반영됨)
            self.current_schedule[f'report{report_num}_date'] = new_date_str

            # DB에 저장
            try:
                from models.schedules import Schedule
                schedule_id = self.current_schedule.get('id')
                if schedule_id:
                    update_data = {f'report{report_num}_date': new_date_str}
                    Schedule.update(schedule_id, **update_data)
            except Exception as e:
                print(f"{report_num} 보고서 날짜 저장 오류: {e}")

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def on_experiment_cell_clicked(self, row, col):
        """실험 테이블 셀 클릭 시 O/X 토글 또는 날짜 수정"""
        if not self.current_schedule:
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        total_rounds = sampling_count + extend_rounds

        # 행 0: 중간보고서 - 콤보박스가 있으므로 클릭 무시
        if row == 0:
            return

        # 행 1: 날짜 클릭 시 달력으로 날짜 수정 (기존 회차만)
        if row == 1 and col >= 1 and col <= sampling_count:
            self.edit_date_with_calendar(col)
            return

        # 검사항목 행 범위 확인 (행 3부터 마지막 행-1까지가 검사항목)
        # 행 0: 중간보고서, 행 1: 날짜, 행 2: 제조후 일수, 행 3~n-1: 검사항목, 행 n: 1회 기준
        test_item_start_row = 3
        test_item_end_row = table.rowCount() - 2  # 마지막 행(1회 기준) 제외

        # 검사항목 셀만 토글 가능 (열 1~total_rounds, 연장 회차 포함)
        if row < test_item_start_row or row > test_item_end_row:
            return
        if col < 1 or col > total_rounds:
            return

        # 수정 가능 여부 확인 (대기 또는 중단 상태에서 수정 가능)
        # 중단 상태에서는 X 표시로 미완료 회차를 표시할 수 있음
        if not self.can_edit_plan(allow_suspended=True):
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

        # 활동 로그 기록 (검사항목명 가져오기)
        test_item_name = table.item(row, 0).text() if table.item(row, 0) else ''
        self.log_activity(
            'schedule_experiment_toggle',
            details={'test_item': test_item_name, 'round': col, 'old_value': current_value, 'new_value': new_value}
        )

        # 비용 재계산
        self.recalculate_costs()

    def bulk_set_x(self):
        """선택한 영역의 셀을 일괄 X로 변경"""
        if not self.current_schedule:
            return

        # 수정 가능 여부 확인 (대기 또는 중단 상태에서 수정 가능)
        if not self.can_edit_plan(allow_suspended=True):
            QMessageBox.warning(self, "수정 불가", "대기 또는 중단 상태에서만 수정 가능합니다.")
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        total_rounds = sampling_count + extend_rounds

        # 검사항목 행 범위 (행 3부터 마지막-1 행까지)
        test_item_start_row = 3
        test_item_end_row = table.rowCount() - 2  # 마지막 행(1회 기준) 제외

        # 선택된 셀 범위 가져오기
        selected_ranges = table.selectedRanges()
        if not selected_ranges:
            QMessageBox.information(self, "선택 영역 없음", "변경할 영역을 먼저 드래그로 선택해주세요.")
            return

        changed_count = 0

        for selection in selected_ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                # 검사항목 행만 처리
                if row < test_item_start_row or row > test_item_end_row:
                    continue

                for col in range(selection.leftColumn(), selection.rightColumn() + 1):
                    # 회차 열만 처리 (열 1~total_rounds)
                    if col < 1 or col > total_rounds:
                        continue

                    item = table.item(row, col)
                    if item is None:
                        continue

                    current_value = item.text()
                    if current_value != 'X':
                        item.setText('X')
                        item.setForeground(QBrush(QColor('#e74c3c')))  # 빨간색
                        changed_count += 1

        if changed_count > 0:
            # 활동 로그 기록
            self.log_activity(
                'schedule_experiment_bulk_x',
                details={'changed_cells': changed_count}
            )
            # 비용 재계산
            self.recalculate_costs()
            QMessageBox.information(self, "일괄 변경 완료", f"{changed_count}개 셀이 X로 변경되었습니다.")
        else:
            QMessageBox.information(self, "변경 없음", "변경된 셀이 없습니다.\n검사항목 영역을 선택해주세요.")

    def count_completed_rounds(self):
        """온도조건별 실험 테이블에서 완료된 회차 수를 계산

        중단 견적서에서 실제 완료된 회차만 정산하기 위해 사용
        각 회차(열)에서:
        - X 표시가 하나라도 있으면 미완료 회차로 간주
        - O 표시만 있으면 완료 회차로 간주
        """
        if not hasattr(self, 'experiment_table') or not self.current_schedule:
            return 0

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        total_rounds = sampling_count + extend_rounds

        # 검사항목 행 범위 (행 3부터 마지막-1 행까지)
        # 행 0: 중간보고서, 행 1: 날짜, 행 2: 제조후 일수, 행 3~: 검사항목
        test_item_start_row = 3
        test_item_end_row = table.rowCount() - 2  # 마지막 행(1회 기준) 제외

        if test_item_end_row < test_item_start_row:
            return 0

        completed_rounds = 0

        # 각 회차(열) 확인 (연장 회차 포함)
        for col in range(1, total_rounds + 1):
            has_incomplete = False
            has_any_test = False

            # 해당 회차의 모든 검사항목 확인
            for row in range(test_item_start_row, test_item_end_row + 1):
                item = table.item(row, col)
                if item:
                    text = item.text()
                    if text == 'X':
                        # X 표시가 있으면 미완료 회차
                        has_incomplete = True
                        break
                    elif text == 'O':
                        has_any_test = True

            if has_incomplete:
                # X 표시가 있는 첫 회차에서 중단 (연속된 완료 회차만 카운트)
                break
            elif has_any_test:
                completed_rounds += 1
            else:
                # O도 X도 없으면 미완료로 간주하고 중단
                break

        return completed_rounds

    def edit_date_with_calendar(self, col):
        """달력을 통해 날짜 수정 - 1회차 날짜 변경 시 시작일도 연동"""
        # 수정 가능 여부 확인 (상태가 '대기'일 때만)
        if not self.can_edit_plan():
            return

        table = self.experiment_table
        # 행 1이 날짜 행 (행 0: 중간보고서, 행 1: 날짜, 행 2: 제조후 일수)
        current_date_text = table.item(1, col).text() if table.item(1, col) else "-"
        old_date = current_date_text  # 로그용

        # 시작일 가져오기
        start_date_str = self.current_schedule.get('start_date', '')
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                pass

        # 현재 표시된 날짜를 파싱하여 달력 초기값으로 설정
        current_date = None
        if current_date_text != "-":
            try:
                # YYYY-MM-DD 형식 파싱
                current_date = datetime.strptime(current_date_text, '%Y-%m-%d')
            except (ValueError, TypeError):
                try:
                    # MM-DD 형식이면 현재 연도 추가
                    if len(current_date_text) == 5:
                        year = datetime.now().year
                        if start_date:
                            year = start_date.year
                        current_date = datetime.strptime(f"{year}-{current_date_text}", '%Y-%m-%d')
                except (ValueError, TypeError):
                    current_date = start_date

        # 날짜 선택 다이얼로그 표시
        dialog = DateSelectDialog(self, current_date=current_date, title=f"{col}회차 날짜 선택")
        if dialog.exec_() and dialog.selected_date:
            # 선택된 날짜 저장
            self.custom_dates[col] = dialog.selected_date

            # 활동 로그 기록
            new_date_str = dialog.selected_date.strftime('%Y-%m-%d')
            self.log_activity(
                'schedule_date_edit',
                details={'round': col, 'old_date': old_date, 'new_date': new_date_str}
            )

            # 테이블 날짜 업데이트 (행 1: 날짜)
            date_item = table.item(1, col)
            if date_item:
                date_item.setText(dialog.selected_date.strftime('%Y-%m-%d'))

                # 주말/공휴일 체크하여 배경색 결정
                selected_date = dialog.selected_date
                selected_date_only = selected_date.date() if hasattr(selected_date, 'date') else selected_date
                holidays = get_korean_holidays(selected_date.year)
                is_weekend = selected_date.weekday() >= 5
                is_holiday = selected_date_only in holidays
                if is_weekend or is_holiday:
                    date_item.setBackground(QColor('#FF8C00'))  # 진한 주황색 (수정됨 + 검토 필요)
                    date_item.setToolTip("수정됨 - 주말 또는 공휴일 검토 필요")
                else:
                    date_item.setBackground(QColor('#FFE4B5'))  # 수정된 날짜 강조 (평일)

            # 1회차(col=1) 날짜 변경 시 시작일 연동
            if col == 1:
                new_start_date = dialog.selected_date
                self.current_schedule['start_date'] = new_start_date.strftime('%Y-%m-%d')
                self.start_date_value.setText(new_start_date.strftime('%Y-%m-%d'))

                # 전체 실험 스케줄 재계산
                self._recalculate_all_dates(new_start_date)
            else:
                # 제조후 일수 업데이트 (행 2: 제조후 일수, 1회차가 아닌 경우)
                if start_date:
                    days_elapsed = (dialog.selected_date - start_date).days
                    time_item = table.item(2, col)
                    if time_item:
                        time_item.setText(f"{days_elapsed}일")
                        time_item.setBackground(QColor('#FFE4B5'))

                # 실험기간 업데이트 (날짜 변경 반영)
                self._update_experiment_period_display()

            # sample_dates 업데이트
            self.sample_dates[col] = dialog.selected_date

            # 해당 회차에 연결된 중간보고서가 있으면 날짜 재계산
            self._update_interim_report_date_for_round(col)

            # 스케줄 저장 시그널 발생 (다른 탭 새로고침용)
            self.schedule_saved.emit()

    def _recalculate_all_dates(self, new_start_date):
        """시작일 변경 시 모든 날짜 재계산"""
        if not self.current_schedule:
            return

        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        days = self.current_schedule.get('test_period_days', 0) or 0
        months = self.current_schedule.get('test_period_months', 0) or 0
        years = self.current_schedule.get('test_period_years', 0) or 0
        experiment_days = days + (months * 30) + (years * 365)

        table = self.experiment_table

        # 공휴일 목록 가져오기
        holidays = get_korean_holidays(new_start_date.year)
        holidays.update(get_korean_holidays(new_start_date.year + 1))

        # 각 회차별 날짜 재계산
        for i in range(sampling_count):
            col_idx = i + 1

            # 사용자가 직접 수정한 날짜가 아닌 경우에만 재계산
            if col_idx not in self.custom_dates or col_idx == 1:
                from datetime import timedelta
                if i == sampling_count - 1:
                    days_offset = experiment_days
                elif sampling_count > 1:
                    interval_days = experiment_days / (sampling_count - 1)
                    days_offset = round(i * interval_days)
                else:
                    days_offset = 0

                sample_date = new_start_date + timedelta(days=days_offset)

                # 테이블 업데이트 (행 1: 날짜)
                date_item = table.item(1, col_idx)
                if date_item:
                    date_item.setText(sample_date.strftime('%Y-%m-%d'))

                    # 주말/공휴일 체크하여 배경색 결정
                    sample_date_only = sample_date.date() if hasattr(sample_date, 'date') else sample_date
                    is_weekend = sample_date.weekday() >= 5
                    is_holiday = sample_date_only in holidays
                    if is_weekend or is_holiday:
                        if col_idx == 1:
                            date_item.setBackground(QColor('#FF8C00'))  # 진한 주황색 (시작일 + 검토 필요)
                        else:
                            date_item.setBackground(QColor('#FFA500'))  # 주황색 (검토 필요)
                        date_item.setToolTip("주말 또는 공휴일 - 검토 필요")
                    else:
                        if col_idx == 1:
                            date_item.setBackground(QColor('#FFE4B5'))  # 변경된 시작일 강조
                        else:
                            date_item.setBackground(QColor('#E6F3FF'))  # 평일 - 기존 색상

                # 제조후 일수 업데이트 (행 2: 제조후 일수)
                time_item = table.item(2, col_idx)
                if time_item:
                    time_item.setText(f"{days_offset}일")
                    time_item.setBackground(QColor('#90EE90'))

        # 마지막 실험일 및 보고서 작성일 업데이트
        from datetime import timedelta
        last_date = new_start_date + timedelta(days=experiment_days)
        self.last_experiment_date_value.setText(last_date.strftime('%Y-%m-%d'))
        self._update_report_date(last_date)

        # 실험기간 업데이트
        self._update_experiment_period_display()

    def _update_experiment_period_display(self):
        """테이블의 실제 날짜를 기준으로 실험기간 업데이트"""
        if not self.current_schedule:
            return

        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        table = self.experiment_table

        # 시작일 (1회차 날짜)
        start_date_item = table.item(0, 1)
        # 마지막 회차 날짜
        last_date_item = table.item(0, sampling_count)

        if not start_date_item or not last_date_item:
            return

        start_date_text = start_date_item.text()
        last_date_text = last_date_item.text()

        if start_date_text == '-' or last_date_text == '-':
            return

        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_text, '%Y-%m-%d')
            last_date = datetime.strptime(last_date_text, '%Y-%m-%d')

            # 실제 실험일수 계산
            actual_days = (last_date - start_date).days

            # 실험기간 표시 업데이트
            exp_years = actual_days // 365
            exp_months = (actual_days % 365) // 30
            exp_days = actual_days % 30

            period_parts = []
            if exp_years > 0: period_parts.append(f"{exp_years}년")
            if exp_months > 0: period_parts.append(f"{exp_months}개월")
            if exp_days > 0: period_parts.append(f"{exp_days}일")
            self.period_value.setText(' '.join(period_parts) if period_parts else '-')

            # 마지막 실험일 및 보고서 작성일 업데이트
            self.last_experiment_date_value.setText(last_date.strftime('%Y-%m-%d'))
            self._update_report_date(last_date)

            # 현재 스케줄에 실제 실험일수 저장 (저장 시 DB에 반영)
            self.current_schedule['actual_experiment_days'] = actual_days

            # 샘플링 간격도 재계산
            if sampling_count > 0:
                interval = actual_days // sampling_count
                self.sampling_interval_value.setText(f"{interval}일")

        except Exception as e:
            print(f"실험기간 업데이트 오류: {e}")

    def recalculate_costs(self):
        """셀 변경 시 비용 재계산"""
        if not self.current_schedule:
            return

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        total_rounds = sampling_count + extend_rounds
        test_method = self.current_schedule.get('test_method', '') or ''

        # 수수료 정보 로드
        fees = {}
        try:
            all_fees = Fee.get_all()
            for fee in all_fees:
                fees[fee['test_item']] = fee['price']
        except Exception:
            pass

        # 식품유형에서 검사항목 가져오기 + 추가된 항목
        base_items = self.get_test_items_from_food_type(self.current_schedule)
        test_items = base_items + self.additional_test_items

        # 검사항목 행 시작 (행 3부터: 0=중간보고서, 1=날짜, 2=제조후일수, 3~=검사항목)
        test_item_start_row = 3

        # 각 검사항목별 O 체크 수 및 비용 계산
        item_o_counts = {}  # {항목명: O 체크 수}
        item_costs = {}     # {항목명: 총 비용}

        # 각 회차별 활성 항목 비용 합계 계산 (연장 회차 포함)
        column_costs = []  # 각 회차별 비용
        for col_idx in range(1, total_rounds + 1):
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

        # 1차 견적 항목별 비용 내역 텍스트 생성 (전체 회차 기준 - 모든 항목 O로 가정)
        first_detail_parts = []
        for test_item in test_items:
            unit_price = int(fees.get(test_item, 0))
            full_cost = unit_price * sampling_count
            first_detail_parts.append(f"{test_item}({sampling_count}회)={full_cost:,}원")
        self.item_cost_detail.setText(" | ".join(first_detail_parts))

        # 중단 견적 항목별 비용 내역 텍스트 생성 (O로 체크된 것만)
        suspend_detail_parts = []
        for test_item in test_items:
            o_count = item_o_counts.get(test_item, 0)
            total_cost = item_costs.get(test_item, 0)
            if o_count > 0:
                suspend_detail_parts.append(f"{test_item}({o_count}회)={total_cost:,}원")
        if hasattr(self, 'suspend_item_cost_detail'):
            self.suspend_item_cost_detail.setText(" | ".join(suspend_detail_parts) if suspend_detail_parts else "-")

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

        # 1. 1회 기준 (합계) - 모든 검사항목 합계 (전체 항목, O/X 상태 무관)
        cost_per_test = int(sum(fees.get(item, 0) for item in test_items))
        self.cost_per_test.setText(f"1회:{cost_per_test:,}원")

        # 2. 기본 회차별 총계 (O로 체크된 항목만)
        total_rounds_cost = sum(column_costs[:sampling_count])  # 기본 회차만
        self.total_rounds_cost.setText(f"회차:{total_rounds_cost:,}원")

        # ========== 1차 견적 계산 ==========
        # 1차 견적은 O/X 상태와 무관하게 원래 전체 비용 (모든 항목 O로 가정)
        first_total_rounds = cost_per_test * sampling_count
        try:
            first_report_cost = int(self.first_report_cost_input.text().replace(',', '').replace('원', ''))
        except (ValueError, TypeError):
            first_report_cost = 200000

        first_interim_cost = 0
        if self.first_interim_cost_input.isVisible():
            try:
                first_interim_cost = int(self.first_interim_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                first_interim_cost = 200000

        first_cost_no_vat = int(first_total_rounds * zone_count + first_report_cost + first_interim_cost)
        if first_interim_cost > 0:
            first_formula = f"{first_total_rounds:,}×{zone_count}+{first_report_cost:,}+{first_interim_cost:,}={first_cost_no_vat:,}원"
        else:
            first_formula = f"{first_total_rounds:,}×{zone_count}+{first_report_cost:,}={first_cost_no_vat:,}원"
        self.first_cost_formula.setText(first_formula)

        # 1차 부가세 포함
        first_vat = int(first_cost_no_vat * 0.1)
        first_with_vat = first_cost_no_vat + first_vat
        if hasattr(self, 'first_cost_vat'):
            self.first_cost_vat.setText(f"(VAT포함:{first_with_vat:,}원)")

        # ========== 중단 견적 계산 (상태가 중단일 때만) ==========
        schedule_status = self.current_schedule.get('status', '')
        if schedule_status == 'suspended':
            self.row_suspend_widget.show()

            # 중단 1회 비용 (O로 체크된 항목들의 평균)
            suspend_o_count = sum(item_o_counts.values())
            if suspend_o_count > 0:
                suspend_per_test = total_rounds_cost // suspend_o_count if suspend_o_count > 0 else 0
            else:
                suspend_per_test = 0
            if hasattr(self, 'suspend_cost_per_test'):
                self.suspend_cost_per_test.setText(f"1회:{cost_per_test:,}원")

            # 중단 견적은 O로 체크된 항목만 비용에 포함
            self.suspend_rounds_cost.setText(f"회차:{total_rounds_cost:,}원")

            try:
                suspend_report_cost = int(self.suspend_report_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                suspend_report_cost = first_report_cost

            suspend_interim_cost = 0
            if self.suspend_interim_cost_input.isVisible():
                try:
                    suspend_interim_cost = int(self.suspend_interim_cost_input.text().replace(',', '').replace('원', ''))
                except (ValueError, TypeError):
                    suspend_interim_cost = first_interim_cost

            suspend_cost_no_vat = int(total_rounds_cost * zone_count + suspend_report_cost + suspend_interim_cost)
            if suspend_interim_cost > 0:
                suspend_formula = f"{total_rounds_cost:,}×{zone_count}+{suspend_report_cost:,}+{suspend_interim_cost:,}={suspend_cost_no_vat:,}원"
            else:
                suspend_formula = f"{total_rounds_cost:,}×{zone_count}+{suspend_report_cost:,}={suspend_cost_no_vat:,}원"
            self.suspend_cost_formula.setText(suspend_formula)

            # 중단 부가세 포함
            suspend_vat = int(suspend_cost_no_vat * 0.1)
            suspend_with_vat = suspend_cost_no_vat + suspend_vat
            if hasattr(self, 'suspend_cost_vat'):
                self.suspend_cost_vat.setText(f"(VAT포함:{suspend_with_vat:,}원)")
        else:
            self.row_suspend_widget.hide()

        # ========== 연장 견적 계산 (연장 계획 있을 때만) ==========
        if extend_rounds > 0:
            self.row_extend_widget.show()

            # 연장 회차 비용 (O로 체크된 것만)
            extend_total_cost = sum(column_costs[sampling_count:])
            self.extend_rounds_cost.setText(f"회차:{extend_total_cost:,}원")

            # 연장 1회 비용
            if hasattr(self, 'extend_cost_per_test'):
                self.extend_cost_per_test.setText(f"1회:{cost_per_test:,}원")

            # 연장 항목별 비용 내역
            extend_detail_parts = []
            for test_item in test_items:
                unit_price = int(fees.get(test_item, 0))
                extend_item_cost = unit_price * extend_rounds
                extend_detail_parts.append(f"{test_item}({extend_rounds}회)={extend_item_cost:,}원")
            if hasattr(self, 'extend_item_cost_detail'):
                self.extend_item_cost_detail.setText(" | ".join(extend_detail_parts))

            try:
                extend_report_cost = int(self.extend_report_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                extend_report_cost = first_report_cost

            extend_interim_cost = 0
            if hasattr(self, 'extend_interim_cost_input') and self.extend_interim_cost_input.isVisible():
                try:
                    extend_interim_cost = int(self.extend_interim_cost_input.text().replace(',', '').replace('원', ''))
                except (ValueError, TypeError):
                    extend_interim_cost = 0

            extend_cost_no_vat = int(extend_total_cost * zone_count + extend_report_cost + extend_interim_cost)
            if extend_interim_cost > 0:
                extend_formula = f"{extend_total_cost:,}×{zone_count}+{extend_report_cost:,}+{extend_interim_cost:,}={extend_cost_no_vat:,}원"
            else:
                extend_formula = f"{extend_total_cost:,}×{zone_count}+{extend_report_cost:,}={extend_cost_no_vat:,}원"
            self.extend_cost_formula.setText(extend_formula)

            # 연장 부가세 포함
            extend_vat = int(extend_cost_no_vat * 0.1)
            extend_with_vat = extend_cost_no_vat + extend_vat
            if hasattr(self, 'extend_cost_vat'):
                self.extend_cost_vat.setText(f"(VAT포함:{extend_with_vat:,}원)")
        else:
            self.row_extend_widget.hide()

        # 금액을 DB에 저장 (1차 견적 기준)
        self._save_amounts_to_db(first_cost_no_vat, first_vat, first_with_vat)

    def _calculate_extend_rounds_cost(self):
        """연장 회차만의 비용 계산 (O/X 상태 반영)"""
        if not self.current_schedule:
            return 0

        table = self.experiment_table
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0

        if extend_rounds == 0:
            return 0

        # 수수료 정보 로드
        fees = {}
        try:
            all_fees = Fee.get_all()
            for fee in all_fees:
                fees[fee['test_item']] = fee['price']
        except Exception:
            pass

        # 식품유형에서 검사항목 가져오기 + 추가된 항목
        base_items = self.get_test_items_from_food_type(self.current_schedule)
        test_items = base_items + self.additional_test_items

        # 검사항목 행 시작 (행 3부터)
        test_item_start_row = 3

        # 연장 회차 열만 계산 (sampling_count + 1 부터 sampling_count + extend_rounds 까지)
        extend_cost = 0
        for col_idx in range(sampling_count + 1, sampling_count + extend_rounds + 1):
            for row_idx, test_item in enumerate(test_items):
                item = table.item(test_item_start_row + row_idx, col_idx)
                if item and item.text() == 'O':
                    extend_cost += int(fees.get(test_item, 0))

        return extend_cost

    def on_cost_input_changed(self):
        """보고서 비용 입력 변경 시 총비용 재계산 (1차/중단/연장 개별 처리)"""
        if not self.current_schedule:
            return

        # 실험 방법에 따른 구간 수 결정
        test_method = self.current_schedule.get('test_method', 'real')
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        sampling_count = self.current_schedule.get('sampling_count', 6) or 6

        # ========== 1차 견적 계산 ==========
        try:
            cost_per_test = int(self.cost_per_test.text().replace('1회:', '').replace(',', '').replace('원', ''))
        except (ValueError, TypeError, AttributeError):
            cost_per_test = 0

        first_total_rounds = cost_per_test * sampling_count

        try:
            first_report_cost = int(self.first_report_cost_input.text().replace(',', '').replace('원', ''))
        except (ValueError, TypeError):
            first_report_cost = 0

        first_interim_cost = 0
        if self.first_interim_cost_input.isVisible():
            try:
                first_interim_cost = int(self.first_interim_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                first_interim_cost = 0

        first_cost_no_vat = int(first_total_rounds * zone_count + first_report_cost + first_interim_cost)
        if first_interim_cost > 0:
            first_formula = f"{first_total_rounds:,}×{zone_count}+{first_report_cost:,}+{first_interim_cost:,}={first_cost_no_vat:,}원"
        else:
            first_formula = f"{first_total_rounds:,}×{zone_count}+{first_report_cost:,}={first_cost_no_vat:,}원"
        self.first_cost_formula.setText(first_formula)

        # 1차 부가세 포함
        first_vat = int(first_cost_no_vat * 0.1)
        first_with_vat = first_cost_no_vat + first_vat
        if hasattr(self, 'first_cost_vat'):
            self.first_cost_vat.setText(f"(VAT포함:{first_with_vat:,}원)")

        # 금액을 DB에 저장 (1차 견적 기준)
        self._save_amounts_to_db(first_cost_no_vat, first_vat, first_with_vat)

        # ========== 중단 견적 계산 (상태가 중단일 때만) ==========
        schedule_status = self.current_schedule.get('status', '')
        if schedule_status == 'suspended' and hasattr(self, 'suspend_cost_formula'):
            try:
                suspend_rounds_cost = int(self.suspend_rounds_cost.text().replace('회차:', '').replace(',', '').replace('원', ''))
            except (ValueError, TypeError, AttributeError):
                suspend_rounds_cost = 0

            try:
                suspend_report_cost = int(self.suspend_report_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                suspend_report_cost = 0

            suspend_interim_cost = 0
            if self.suspend_interim_cost_input.isVisible():
                try:
                    suspend_interim_cost = int(self.suspend_interim_cost_input.text().replace(',', '').replace('원', ''))
                except (ValueError, TypeError):
                    suspend_interim_cost = 0

            suspend_cost_no_vat = int(suspend_rounds_cost * zone_count + suspend_report_cost + suspend_interim_cost)
            if suspend_interim_cost > 0:
                suspend_formula = f"{suspend_rounds_cost:,}×{zone_count}+{suspend_report_cost:,}+{suspend_interim_cost:,}={suspend_cost_no_vat:,}원"
            else:
                suspend_formula = f"{suspend_rounds_cost:,}×{zone_count}+{suspend_report_cost:,}={suspend_cost_no_vat:,}원"
            self.suspend_cost_formula.setText(suspend_formula)

            # 중단 부가세 포함
            suspend_vat = int(suspend_cost_no_vat * 0.1)
            suspend_with_vat = suspend_cost_no_vat + suspend_vat
            if hasattr(self, 'suspend_cost_vat'):
                self.suspend_cost_vat.setText(f"(VAT포함:{suspend_with_vat:,}원)")

        # ========== 연장 견적 계산 (연장 회차 있을 때만) ==========
        extend_rounds = self.current_schedule.get('extend_rounds', 0) or 0
        if extend_rounds > 0 and hasattr(self, 'extend_cost_formula'):
            try:
                extend_rounds_cost = int(self.extend_rounds_cost.text().replace('회차:', '').replace(',', '').replace('원', ''))
            except (ValueError, TypeError, AttributeError):
                extend_rounds_cost = 0

            try:
                extend_report_cost = int(self.extend_report_cost_input.text().replace(',', '').replace('원', ''))
            except (ValueError, TypeError):
                extend_report_cost = 0

            extend_interim_cost = 0
            if hasattr(self, 'extend_interim_cost_input') and self.extend_interim_cost_input.isVisible():
                try:
                    extend_interim_cost = int(self.extend_interim_cost_input.text().replace(',', '').replace('원', ''))
                except (ValueError, TypeError):
                    extend_interim_cost = 0

            extend_cost_no_vat = int(extend_rounds_cost * zone_count + extend_report_cost + extend_interim_cost)
            if extend_interim_cost > 0:
                extend_formula = f"{extend_rounds_cost:,}×{zone_count}+{extend_report_cost:,}+{extend_interim_cost:,}={extend_cost_no_vat:,}원"
            else:
                extend_formula = f"{extend_rounds_cost:,}×{zone_count}+{extend_report_cost:,}={extend_cost_no_vat:,}원"
            self.extend_cost_formula.setText(extend_formula)

            # 연장 부가세 포함
            extend_vat = int(extend_cost_no_vat * 0.1)
            extend_with_vat = extend_cost_no_vat + extend_vat
            if hasattr(self, 'extend_cost_vat'):
                self.extend_cost_vat.setText(f"(VAT포함:{extend_with_vat:,}원)")

    def save_as_jpg(self):
        """스케줄 관리 화면을 JPG로 저장"""
        if not self.current_schedule:
            QMessageBox.warning(self, "알림", "먼저 스케줄을 선택하세요.")
            return

        # 파일명 생성: 접수일자+업체명+식품유형+실험방법+보관방법
        start_date = self.current_schedule.get('start_date', '') or ''
        company = self.current_schedule.get('company_name', '') or ''
        food_type = self.current_schedule.get('food_type', '') or ''
        test_method = self.current_schedule.get('test_method', '') or ''
        storage_condition = self.current_schedule.get('storage_condition', '') or ''

        # 파일명에 사용할 수 없는 문자 제거
        def sanitize_filename(name):
            import re
            return re.sub(r'[\\/*?:"<>|]', '', name).strip()

        filename_parts = [
            start_date.replace('-', ''),
            sanitize_filename(company),
            sanitize_filename(food_type),
            sanitize_filename(test_method),
            sanitize_filename(storage_condition)
        ]
        filename = '_'.join([p for p in filename_parts if p]) + '.jpg'

        # 저장 폴더 선택
        import os
        default_folder = os.path.join(os.getcwd(), '스케줄관리')
        if not os.path.exists(default_folder):
            os.makedirs(default_folder)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "JPG 파일 저장",
            os.path.join(default_folder, filename),
            "JPEG Files (*.jpg)"
        )

        if not file_path:
            return

        try:
            from PyQt5.QtGui import QPixmap, QPainter, QImage
            from PyQt5.QtCore import QRect

            # JPG 저장 시 버튼과 금액 영역 숨기기
            hidden_widgets = []
            if hasattr(self, 'experiment_btn_widget') and self.experiment_btn_widget:
                self.experiment_btn_widget.hide()
                hidden_widgets.append(self.experiment_btn_widget)
            if hasattr(self, 'cost_frame') and self.cost_frame:
                self.cost_frame.hide()
                hidden_widgets.append(self.cost_frame)

            # 테이블의 마지막 행 "(1회 기준)" 숨기기
            last_row_hidden = False
            if hasattr(self, 'experiment_table') and self.experiment_table.rowCount() > 0:
                last_row = self.experiment_table.rowCount() - 1
                self.experiment_table.hideRow(last_row)
                last_row_hidden = True

            # 레이아웃 업데이트를 위해 잠시 대기
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

            # 캡처할 위젯들의 총 높이와 최대 너비 계산
            widgets_to_capture = []
            if self.info_group:
                widgets_to_capture.append(self.info_group)
            if self.experiment_group:
                widgets_to_capture.append(self.experiment_group)

            if not widgets_to_capture:
                # 숨긴 위젯 복원
                for w in hidden_widgets:
                    w.show()
                # 테이블 마지막 행 복원
                if last_row_hidden:
                    self.experiment_table.showRow(last_row)
                QMessageBox.warning(self, "오류", "캡처할 영역이 없습니다.")
                return

            # 각 위젯의 크기 계산
            total_height = sum(w.height() for w in widgets_to_capture) + 20  # 여백
            max_width = max(w.width() for w in widgets_to_capture)

            # 이미지 생성
            image = QImage(max_width, total_height, QImage.Format_RGB32)
            image.fill(Qt.white)

            painter = QPainter(image)
            current_y = 0

            for widget in widgets_to_capture:
                # 위젯을 픽스맵으로 렌더링
                pixmap = widget.grab()
                painter.drawPixmap(0, current_y, pixmap)
                current_y += widget.height() + 5

            painter.end()

            # 숨긴 위젯 복원
            for w in hidden_widgets:
                w.show()
            # 테이블 마지막 행 복원
            if last_row_hidden:
                self.experiment_table.showRow(last_row)

            # JPG로 저장
            if image.save(file_path, "JPEG", 95):
                QMessageBox.information(self, "저장 완료", f"이미지가 저장되었습니다.\n{file_path}")
                # 저장된 파일 경로 기억 (메일 발송용)
                self.last_saved_image_path = file_path
            else:
                QMessageBox.critical(self, "저장 실패", "이미지 저장에 실패했습니다.")

        except Exception as e:
            # 숨긴 위젯 복원
            if 'hidden_widgets' in locals():
                for w in hidden_widgets:
                    w.show()
            # 테이블 마지막 행 복원
            if 'last_row_hidden' in locals() and last_row_hidden:
                self.experiment_table.showRow(last_row)
            QMessageBox.critical(self, "오류", f"이미지 저장 중 오류가 발생했습니다.\n{str(e)}")

    def open_mail_dialog(self):
        """스케줄 관리 메일 발송 다이얼로그 열기"""
        if not self.current_schedule:
            QMessageBox.warning(self, "알림", "먼저 스케줄을 선택하세요.")
            return

        # 메일 발송 전 자동으로 JPG 스크린샷 생성
        self._create_temp_screenshot()

        dialog = ScheduleMailDialog(self, self.current_schedule, self.current_user)
        if dialog.exec_():
            QMessageBox.information(self, "완료", "메일이 전송되었습니다.")

    def _create_temp_screenshot(self):
        """메일 첨부용 임시 스크린샷 생성"""
        try:
            import os
            import tempfile
            from PyQt5.QtGui import QPixmap, QPainter, QImage
            from PyQt5.QtWidgets import QApplication

            # JPG 저장 시 버튼과 금액 영역 숨기기
            hidden_widgets = []
            if hasattr(self, 'experiment_btn_widget') and self.experiment_btn_widget:
                self.experiment_btn_widget.hide()
                hidden_widgets.append(self.experiment_btn_widget)
            if hasattr(self, 'cost_frame') and self.cost_frame:
                self.cost_frame.hide()
                hidden_widgets.append(self.cost_frame)

            # 테이블의 마지막 행 "(1회 기준)" 숨기기
            last_row_hidden = False
            last_row = 0
            if hasattr(self, 'experiment_table') and self.experiment_table.rowCount() > 0:
                last_row = self.experiment_table.rowCount() - 1
                self.experiment_table.hideRow(last_row)
                last_row_hidden = True

            # 레이아웃 업데이트를 위해 잠시 대기
            QApplication.processEvents()

            # 캡처할 위젯들의 총 높이와 최대 너비 계산
            widgets_to_capture = []
            if self.info_group:
                widgets_to_capture.append(self.info_group)
            if self.experiment_group:
                widgets_to_capture.append(self.experiment_group)

            if not widgets_to_capture:
                for w in hidden_widgets:
                    w.show()
                if last_row_hidden:
                    self.experiment_table.showRow(last_row)
                return

            # 각 위젯의 크기 계산
            total_height = sum(w.height() for w in widgets_to_capture) + 20
            max_width = max(w.width() for w in widgets_to_capture)

            # 이미지 생성
            image = QImage(max_width, total_height, QImage.Format_RGB32)
            image.fill(Qt.white)

            painter = QPainter(image)
            current_y = 0

            for widget in widgets_to_capture:
                pixmap = widget.grab()
                painter.drawPixmap(0, current_y, pixmap)
                current_y += widget.height() + 5

            painter.end()

            # 숨긴 위젯 복원
            for w in hidden_widgets:
                w.show()
            # 테이블 마지막 행 복원
            if last_row_hidden:
                self.experiment_table.showRow(last_row)

            # 파일명 생성
            start_date = self.current_schedule.get('start_date', '') or ''
            client_name = self.current_schedule.get('client_name', '') or ''
            product_name = self.current_schedule.get('product_name', '') or ''

            import re
            def sanitize_filename(name):
                return re.sub(r'[\\/*?:"<>|]', '', name).strip()

            filename_parts = [
                start_date.replace('-', ''),
                sanitize_filename(client_name),
                sanitize_filename(product_name)
            ]
            filename = '_'.join([p for p in filename_parts if p]) + '.jpg'

            # 파일명이 비어있으면 기본값 사용
            if filename == '.jpg':
                from datetime import datetime
                filename = datetime.now().strftime('%Y%m%d') + '.jpg'

            # 임시 폴더에 저장
            temp_dir = os.path.join(os.getcwd(), '스케줄관리')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            file_path = os.path.join(temp_dir, filename)

            # JPG로 저장
            if image.save(file_path, "JPEG", 95):
                self.last_saved_image_path = file_path

        except Exception as e:
            print(f"스크린샷 생성 오류: {e}")
            # 숨긴 위젯 복원
            if 'hidden_widgets' in locals():
                for w in hidden_widgets:
                    w.show()
            # 테이블 마지막 행 복원
            if 'last_row_hidden' in locals() and last_row_hidden:
                self.experiment_table.showRow(last_row)


class ScheduleMailDialog(QDialog):
    """스케줄 관리 메일 발송 다이얼로그"""

    def __init__(self, parent, schedule, current_user):
        super().__init__(parent)
        self.setWindowTitle("스케줄 메일 발송")
        self.setMinimumSize(700, 800)
        self.schedule = schedule
        self.current_user = current_user
        self.to_checkboxes = {}
        self.cc_checkboxes = {}
        self.attachment_files = []

        # 사용자 목록 로드
        self.users = self._load_users()
        self.initUI()

    def _load_users(self):
        """사용자 목록 로드"""
        try:
            from models.users import User
            all_users = User.get_all() or []
            # 현재 사용자 제외
            if self.current_user:
                return [u for u in all_users if u.get('id') != self.current_user.get('id')]
            return all_users
        except Exception as e:
            print(f"사용자 목록 로드 오류: {e}")
            return []

    def initUI(self):
        layout = QVBoxLayout(self)

        # 자주 사용하는 수신자 영역
        freq_group = QGroupBox("자주 사용하는 수신자")
        freq_layout = QHBoxLayout(freq_group)

        self.freq_combo = QComboBox()
        self.freq_combo.addItem("-- 선택 --")
        self._load_frequent_recipients()
        self.freq_combo.currentIndexChanged.connect(self.apply_frequent_recipients)
        freq_layout.addWidget(self.freq_combo)

        save_freq_btn = QPushButton("현재 선택 저장")
        save_freq_btn.setStyleSheet("padding: 5px 10px;")
        save_freq_btn.clicked.connect(self.save_frequent_recipients)
        freq_layout.addWidget(save_freq_btn)

        delete_freq_btn = QPushButton("삭제")
        delete_freq_btn.setStyleSheet("padding: 5px 10px;")
        delete_freq_btn.clicked.connect(self.delete_frequent_recipients)
        freq_layout.addWidget(delete_freq_btn)

        freq_layout.addStretch()
        layout.addWidget(freq_group)

        # 수신자 선택
        to_group = QGroupBox("수신자 (To) - 필수")
        to_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        to_main_layout = QVBoxLayout(to_group)

        to_btn_layout = QHBoxLayout()
        to_select_all_btn = QPushButton("전체 선택")
        to_select_all_btn.clicked.connect(lambda: self.select_all_users('to'))
        to_deselect_all_btn = QPushButton("전체 해제")
        to_deselect_all_btn.clicked.connect(lambda: self.deselect_all_users('to'))
        to_btn_layout.addWidget(to_select_all_btn)
        to_btn_layout.addWidget(to_deselect_all_btn)
        to_btn_layout.addStretch()
        to_main_layout.addLayout(to_btn_layout)

        to_scroll = QScrollArea()
        to_scroll.setWidgetResizable(True)
        to_scroll.setMaximumHeight(100)
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

        cc_btn_layout = QHBoxLayout()
        cc_select_all_btn = QPushButton("전체 선택")
        cc_select_all_btn.clicked.connect(lambda: self.select_all_users('cc'))
        cc_deselect_all_btn = QPushButton("전체 해제")
        cc_deselect_all_btn.clicked.connect(lambda: self.deselect_all_users('cc'))
        cc_btn_layout.addWidget(cc_select_all_btn)
        cc_btn_layout.addWidget(cc_deselect_all_btn)
        cc_btn_layout.addStretch()
        cc_main_layout.addLayout(cc_btn_layout)

        cc_scroll = QScrollArea()
        cc_scroll.setWidgetResizable(True)
        cc_scroll.setMaximumHeight(100)
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

        # 외부 이메일 발송 영역
        email_group = QGroupBox("외부 이메일 발송 (그룹웨어 SMTP)")
        email_layout = QVBoxLayout(email_group)

        email_to_layout = QHBoxLayout()
        email_to_layout.addWidget(QLabel("수신자 이메일:"))
        self.external_email_to = QLineEdit()
        self.external_email_to.setPlaceholderText("이메일 주소 입력 (여러 개는 쉼표로 구분)")
        email_to_layout.addWidget(self.external_email_to)
        email_layout.addLayout(email_to_layout)

        email_cc_layout = QHBoxLayout()
        email_cc_layout.addWidget(QLabel("참조 이메일:"))
        self.external_email_cc = QLineEdit()
        self.external_email_cc.setPlaceholderText("참조 이메일 (선택사항)")
        email_cc_layout.addWidget(self.external_email_cc)
        email_layout.addLayout(email_cc_layout)

        # 업체 이메일 자동 입력 버튼
        self.auto_fill_btn = QPushButton("업체 이메일 자동 입력")
        self.auto_fill_btn.clicked.connect(self._auto_fill_client_email)
        email_layout.addWidget(self.auto_fill_btn)

        layout.addWidget(email_group)

        # 제목
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("제목:"))
        self.subject_input = QLineEdit()
        self._set_default_subject()
        subject_layout.addWidget(self.subject_input)
        layout.addLayout(subject_layout)

        # 내용
        layout.addWidget(QLabel("내용:"))
        self.content_input = QTextEdit()
        self._set_default_content()
        self.content_input.setMaximumHeight(200)
        layout.addWidget(self.content_input)

        # 첨부파일
        attach_group = QGroupBox("첨부파일")
        attach_layout = QVBoxLayout(attach_group)

        attach_btn_layout = QHBoxLayout()
        add_attach_btn = QPushButton("파일 추가")
        add_attach_btn.clicked.connect(self.add_attachment)
        remove_attach_btn = QPushButton("선택 삭제")
        remove_attach_btn.clicked.connect(self.remove_attachment)
        attach_btn_layout.addWidget(add_attach_btn)
        attach_btn_layout.addWidget(remove_attach_btn)
        attach_btn_layout.addStretch()
        attach_layout.addLayout(attach_btn_layout)

        self.attachment_list = QListWidget()
        self.attachment_list.setMaximumHeight(60)
        attach_layout.addWidget(self.attachment_list)

        # 마지막 저장된 JPG 자동 추가
        if hasattr(self.parent(), 'last_saved_image_path'):
            last_path = self.parent().last_saved_image_path
            if last_path and os.path.exists(last_path):
                self._add_attachment_file(last_path)

        layout.addWidget(attach_group)

        # 버튼
        btn_layout = QHBoxLayout()
        send_btn = QPushButton("보내기")
        send_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 20px; font-weight: bold;")
        send_btn.clicked.connect(self.send_mail)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_frequent_recipients(self):
        """자주 사용하는 수신자 목록 로드"""
        try:
            from models.frequent_recipients import FrequentRecipient
            if self.current_user:
                freq_list = FrequentRecipient.get_all(self.current_user.get('id'))
                for item in freq_list:
                    self.freq_combo.addItem(item['name'], item['id'])
        except Exception as e:
            print(f"자주 사용하는 수신자 로드 오류: {e}")

    def apply_frequent_recipients(self, index):
        """자주 사용하는 수신자 적용"""
        if index <= 0:
            return

        try:
            from models.frequent_recipients import FrequentRecipient
            freq_id = self.freq_combo.itemData(index)
            freq_data = FrequentRecipient.get_by_id(freq_id)

            if freq_data:
                # 모든 체크 해제
                self.deselect_all_users('to')
                self.deselect_all_users('cc')

                # 수신자 체크
                for uid in freq_data.get('recipient_ids', []):
                    if uid in self.to_checkboxes:
                        self.to_checkboxes[uid].setChecked(True)

                # 참조자 체크
                for uid in freq_data.get('cc_ids', []):
                    if uid in self.cc_checkboxes:
                        self.cc_checkboxes[uid].setChecked(True)

        except Exception as e:
            print(f"수신자 적용 오류: {e}")

    def save_frequent_recipients(self):
        """현재 선택을 자주 사용하는 수신자로 저장"""
        to_ids = [uid for uid, cb in self.to_checkboxes.items() if cb.isChecked()]
        cc_ids = [uid for uid, cb in self.cc_checkboxes.items() if cb.isChecked()]

        if not to_ids:
            QMessageBox.warning(self, "알림", "저장할 수신자를 선택하세요.")
            return

        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "이름 입력", "자주 사용하는 수신자 이름:")

        if ok and name:
            try:
                from models.frequent_recipients import FrequentRecipient
                FrequentRecipient.create(
                    self.current_user.get('id'),
                    name,
                    to_ids,
                    cc_ids
                )
                # 콤보박스 새로고침
                self.freq_combo.clear()
                self.freq_combo.addItem("-- 선택 --")
                self._load_frequent_recipients()
                QMessageBox.information(self, "저장 완료", "자주 사용하는 수신자가 저장되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    def delete_frequent_recipients(self):
        """선택된 자주 사용하는 수신자 삭제"""
        index = self.freq_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "알림", "삭제할 항목을 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{self.freq_combo.currentText()}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from models.frequent_recipients import FrequentRecipient
                freq_id = self.freq_combo.itemData(index)
                FrequentRecipient.delete(freq_id)
                # 콤보박스 새로고침
                self.freq_combo.clear()
                self.freq_combo.addItem("-- 선택 --")
                self._load_frequent_recipients()
            except Exception as e:
                QMessageBox.critical(self, "오류", f"삭제 실패: {e}")

    def _set_default_subject(self):
        """기본 메일 제목 설정"""
        company = self.schedule.get('client_name', '') or ''
        self.subject_input.setText(f"[{company}] 소비기한 입고 알림")

    def _set_default_content(self):
        """기본 메일 내용 설정"""
        # 설정에서 회사 정보 가져오기
        company_name = "(주)바이오푸드랩"
        company_phone = ""
        company_mobile = ""
        company_email = ""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()
            conn.close()
            settings_dict = {s['key']: s['value'] for s in settings}
            company_name = settings_dict.get('company_name', '(주)바이오푸드랩') or '(주)바이오푸드랩'
            company_phone = settings_dict.get('company_phone', '') or ''
            company_mobile = settings_dict.get('company_mobile', '') or ''
            company_email = settings_dict.get('company_email', '') or settings_dict.get('smtp_email', '') or ''
        except Exception as e:
            print(f"설정 로드 오류: {e}")

        # 스케줄 정보 추출
        start_date = self.schedule.get('start_date', '') or '-'
        client_name = self.schedule.get('client_name', '') or '-'
        product_name = self.schedule.get('product_name', '') or '-'

        # 식품유형 조회
        food_type_id = self.schedule.get('food_type_id', '')
        food_type_name = '-'
        if food_type_id:
            try:
                from models.product_types import ProductType
                food_type = ProductType.get_by_id(food_type_id)
                if food_type:
                    food_type_name = food_type.get('type_name', '-') or '-'
            except Exception:
                pass

        # 보관조건 변환
        storage_code = self.schedule.get('storage_condition', '') or ''
        storage_map = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }
        storage_condition = storage_map.get(storage_code, storage_code) if storage_code else '-'

        # 실험방법 변환
        test_method_code = self.schedule.get('test_method', '') or ''
        method_map = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_accel': '의뢰자요청(가속)',
            'custom_acceleration': '의뢰자요청(가속)'
        }
        test_method = method_map.get(test_method_code, test_method_code) if test_method_code else '-'

        # 검사 항목 (식품유형에서 가져오기 + 추가 항목)
        test_items = []
        if food_type_id:
            try:
                from models.product_types import ProductType
                food_type_data = ProductType.get_by_id(food_type_id)
                if food_type_data:
                    test_items_str_raw = food_type_data.get('test_items', '') or ''
                    if test_items_str_raw:
                        test_items = [item.strip() for item in test_items_str_raw.split(',') if item.strip()]
            except Exception:
                pass

        # 기본 검사항목이 없으면 기본값
        if not test_items:
            test_items = ['관능평가', '세균수', '대장균(정량)', 'pH']

        # 추가된 검사항목
        import json
        additional_json = self.schedule.get('additional_test_items', '')
        if additional_json:
            try:
                additional_items = json.loads(additional_json)
                test_items = test_items + additional_items
            except (json.JSONDecodeError, TypeError):
                pass

        test_items_str = ', '.join(test_items) if test_items else '-'

        # 중간보고서
        report_interim = self.schedule.get('report_interim', 0)
        interim_date = self.schedule.get('interim_report_date', '') or ''
        if report_interim:
            interim_str = f"있음 ({interim_date})" if interim_date else "있음"
        else:
            interim_str = "없음"

        # 완료일 (마지막 실험일)
        # 실험 일수 계산
        test_period_days = self.schedule.get('test_period_days', 0) or 0
        test_period_months = self.schedule.get('test_period_months', 0) or 0
        test_period_years = self.schedule.get('test_period_years', 0) or 0
        total_days = test_period_days + test_period_months * 30 + test_period_years * 365

        last_test_date = '-'
        if start_date and start_date != '-':
            try:
                from datetime import datetime, timedelta
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                last_dt = start_dt + timedelta(days=total_days)
                last_test_date = last_dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass

        # 서명 정보 구성
        signature_lines = [company_name]
        if company_phone:
            signature_lines.append(f"Tel: {company_phone}")
        if company_mobile:
            signature_lines.append(f"Mobile: {company_mobile}")
        if company_email:
            signature_lines.append(f"Email: {company_email}")
        signature = '\n'.join(signature_lines)

        content = f"""안녕하세요, {company_name}입니다.

{client_name} 귀하

소비기한 설정 실험 입고 건에 대해 안내드립니다.

■ 접수일자: {start_date}
■ 업체명: {client_name}
■ 제품명: {product_name}
■ 식품유형: {food_type_name}
■ 실험방법: {test_method}
■ 보관방법: {storage_condition}
■ 검사항목: {test_items_str}
■ 중간보고서: {interim_str}
■ 완료예정일: {last_test_date}

첨부파일을 확인해주시기 바랍니다.

감사합니다.

─────────────────────────
{signature}
─────────────────────────"""

        self.content_input.setPlainText(content)

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

    def add_attachment(self):
        """첨부파일 추가"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "첨부파일 선택", "",
            "All Files (*);;Images (*.jpg *.png);;PDF (*.pdf)"
        )
        for file_path in files:
            self._add_attachment_file(file_path)

    def _add_attachment_file(self, file_path):
        """첨부파일 목록에 추가"""
        import os
        if file_path not in self.attachment_files:
            self.attachment_files.append(file_path)
            filename = os.path.basename(file_path)
            item = QListWidgetItem(filename)
            item.setData(Qt.UserRole, file_path)
            self.attachment_list.addItem(item)

    def remove_attachment(self):
        """선택된 첨부파일 삭제"""
        selected_items = self.attachment_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.attachment_files:
                self.attachment_files.remove(file_path)
            self.attachment_list.takeItem(self.attachment_list.row(item))

    def _auto_fill_client_email(self):
        """업체 이메일 자동 입력"""
        client_email = self.schedule.get('client_email', '')
        if client_email:
            self.external_email_to.setText(client_email)
        else:
            QMessageBox.information(self, "알림", "등록된 업체 이메일이 없습니다.")

    def send_mail(self):
        """메일 전송 (시스템 내 메일 + SMTP 이메일)"""
        import os
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        from email.header import Header

        to_ids = [uid for uid, cb in self.to_checkboxes.items() if cb.isChecked()]
        cc_ids = [uid for uid, cb in self.cc_checkboxes.items() if cb.isChecked()]
        subject = self.subject_input.text().strip()
        content = self.content_input.toPlainText().strip()
        external_to = self.external_email_to.text().strip()
        external_cc = self.external_email_cc.text().strip()

        # 시스템 내 메일 수신자 또는 외부 이메일 중 하나는 필수
        if not to_ids and not external_to:
            QMessageBox.warning(self, "알림", "수신자를 선택하거나 외부 이메일을 입력하세요.")
            return

        if not subject:
            QMessageBox.warning(self, "알림", "제목을 입력하세요.")
            return

        if not self.attachment_files:
            reply = QMessageBox.question(
                self, "첨부파일 없음",
                "첨부파일이 없습니다. 그래도 보내시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        system_mail_sent = False
        smtp_mail_sent = False
        errors = []

        # 1. 시스템 내 메일 전송
        if to_ids:
            try:
                from models.communications import MailNotice
                MailNotice.send(
                    self.current_user['id'],
                    subject,
                    content,
                    to_ids,
                    cc_ids if cc_ids else None
                )
                system_mail_sent = True
            except Exception as e:
                errors.append(f"시스템 내 메일: {e}")

        # 2. 외부 SMTP 이메일 전송
        if external_to:
            try:
                # SMTP 설정 가져오기
                from database import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM settings")
                settings = cursor.fetchall()
                conn.close()

                settings_dict = {s['key']: s['value'] for s in settings}
                smtp_server = settings_dict.get('smtp_server', '')
                smtp_port = int(settings_dict.get('smtp_port', '587'))
                smtp_security = settings_dict.get('smtp_security', 'TLS')
                smtp_email = settings_dict.get('smtp_email', '')
                smtp_password = settings_dict.get('smtp_password', '')
                sender_name = settings_dict.get('smtp_sender_name', '') or settings_dict.get('company_name', '(주)바이오푸드랩')

                if not smtp_server or not smtp_email or not smtp_password:
                    errors.append("SMTP 설정이 완료되지 않았습니다. 설정 > 이메일 탭에서 SMTP 설정을 완료해주세요.")
                else:
                    # 이메일 구성
                    msg = MIMEMultipart()
                    msg['From'] = f"{sender_name} <{smtp_email}>"

                    # 수신자 처리
                    to_list = [email.strip() for email in external_to.split(',') if email.strip()]
                    msg['To'] = ', '.join(to_list)

                    # 참조 처리
                    cc_list = []
                    if external_cc:
                        cc_list = [email.strip() for email in external_cc.split(',') if email.strip()]
                        msg['Cc'] = ', '.join(cc_list)

                    msg['Subject'] = subject

                    # 본문
                    msg.attach(MIMEText(content, 'plain', 'utf-8'))

                    # 첨부파일
                    for file_path in self.attachment_files:
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as attachment:
                                filename = os.path.basename(file_path)
                                ext = os.path.splitext(filename)[1].lower()

                                # MIME 타입 결정
                                if ext in ['.jpg', '.jpeg']:
                                    mime_type = 'image/jpeg'
                                elif ext == '.png':
                                    mime_type = 'image/png'
                                elif ext == '.pdf':
                                    mime_type = 'application/pdf'
                                else:
                                    mime_type = 'application/octet-stream'

                                maintype, subtype = mime_type.split('/', 1)
                                part = MIMEBase(maintype, subtype)
                                part.set_payload(attachment.read())
                                encoders.encode_base64(part)

                                # 한글 파일명 인코딩
                                encoded_filename = Header(filename, 'utf-8').encode()
                                part.add_header(
                                    'Content-Disposition',
                                    'attachment',
                                    filename=('utf-8', '', filename)
                                )
                                part.add_header('Content-Type', mime_type, name=encoded_filename)
                                msg.attach(part)

                    # SMTP 연결 및 발송
                    all_recipients = to_list + cc_list

                    if smtp_security == "SSL":
                        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
                    else:
                        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                        if smtp_security == "TLS":
                            server.starttls()

                    server.login(smtp_email, smtp_password)
                    server.sendmail(smtp_email, all_recipients, msg.as_string())
                    server.quit()
                    smtp_mail_sent = True

            except smtplib.SMTPAuthenticationError:
                errors.append("SMTP 인증 실패. 이메일 또는 비밀번호를 확인해주세요.")
            except smtplib.SMTPException as e:
                errors.append(f"SMTP 오류: {str(e)}")
            except Exception as e:
                errors.append(f"외부 이메일: {str(e)}")

        # 결과 표시
        if errors:
            error_msg = '\n'.join(errors)
            if system_mail_sent or smtp_mail_sent:
                sent_parts = []
                if system_mail_sent:
                    sent_parts.append("시스템 내 메일")
                if smtp_mail_sent:
                    sent_parts.append("외부 이메일")
                QMessageBox.warning(self, "부분 성공",
                    f"{', '.join(sent_parts)} 발송 완료.\n\n오류:\n{error_msg}")
                self.accept()
            else:
                QMessageBox.critical(self, "오류", f"메일 전송 실패:\n{error_msg}")
        else:
            sent_parts = []
            if system_mail_sent:
                sent_parts.append("시스템 내 메일")
            if smtp_mail_sent:
                sent_parts.append("외부 이메일")
            QMessageBox.information(self, "완료", f"메일 발송 완료: {', '.join(sent_parts)}")
            self.accept()
