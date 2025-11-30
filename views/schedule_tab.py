#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 작성 탭
'''
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QFrame, QMessageBox, QComboBox, QCheckBox, QLabel,
                           QApplication, QDialog, QGroupBox, QScrollArea,
                           QDialogButtonBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

# ScheduleCreateDialog 클래스를 schedule_dialog.py에서 임포트
from .schedule_dialog import ScheduleCreateDialog
from utils.logger import log_message, log_error, log_exception


class ScheduleDisplaySettingsDialog(QDialog):
    """스케줄 작성 탭 표시 컬럼 설정 다이얼로그"""

    # 설정 가능한 컬럼 목록 (key, display_name, default_visible)
    COLUMN_OPTIONS = [
        # 업체 정보
        ('client_name', '업체명', True),
        ('client_ceo', '대표자', False),
        ('client_contact', '담당자', False),
        ('client_email', '이메일', False),
        ('client_phone', '전화번호', False),
        # 제품/실험 정보
        ('product_name', '샘플명', True),
        ('food_type', '식품유형', False),
        ('test_method', '실험방법', False),
        ('storage_condition', '보관조건', False),
        ('custom_temperatures', '실험온도', False),
        ('expiry_period', '소비기한', False),
        ('test_period', '실험기간', False),
        ('sampling_count', '샘플링횟수', False),
        ('report_type', '보고서종류', False),
        ('extension_test', '연장실험', False),
        # 포장/기타
        ('packaging', '포장단위', False),
        # 일정
        ('start_date', '시작일', True),
        ('end_date', '종료일', True),
        ('estimate_date', '견적일자', True),
        ('status', '상태', True),
        ('memo', '메모', False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("표시 항목 설정")
        self.setMinimumSize(350, 400)
        self.checkboxes = {}
        self.initUI()
        self.load_settings()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 설명 라벨
        info_label = QLabel("스케줄 목록에서 표시할 컬럼을 선택하세요:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 컬럼 설정 그룹
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
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_tab_columns'")
            result = cursor.fetchone()
            conn.close()

            if result:
                visible_columns = result['value'].split(',')
                for col_key, checkbox in self.checkboxes.items():
                    checkbox.setChecked(col_key in visible_columns)
        except Exception as e:
            print(f"설정 로드 오류: {e}")

    def save_settings(self):
        """설정 저장"""
        try:
            from database import get_connection

            visible_columns = [key for key, cb in self.checkboxes.items() if cb.isChecked()]
            value = ','.join(visible_columns)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = 'schedule_tab_columns'
            """, (value,))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (key, value, description)
                    VALUES ('schedule_tab_columns', ?, '스케줄 작성 탭 표시 컬럼')
                """, (value,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "저장 완료", "표시 항목 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류: {str(e)}")

class ScheduleTab(QWidget):
    # 더블클릭 시 스케줄 ID를 전달하는 시그널
    schedule_double_clicked = pyqtSignal(int)

    # 한글 초성 매핑
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_schedules = []  # 전체 스케줄 목록 저장

        # 검색 디바운싱을 위한 타이머 (300ms 지연)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_schedules)

        self.initUI()
    
    # 컬럼 정의 (key, header_name, data_key, column_index)
    # column_index는 동적으로 계산되므로 None으로 설정
    ALL_COLUMNS = [
        ('select', '선택', None),
        ('id', 'ID', 'id'),
        # 업체 정보
        ('client_name', '업체명', 'client_name'),
        ('client_ceo', '대표자', 'client_ceo'),
        ('client_contact', '담당자', 'client_contact'),
        ('client_email', '이메일', 'client_email'),
        ('client_phone', '전화번호', 'client_phone'),
        # 제품/실험 정보
        ('product_name', '샘플명', 'product_name'),
        ('food_type', '식품유형', 'food_type_id'),
        ('test_method', '실험방법', 'test_method'),
        ('storage_condition', '보관조건', 'storage_condition'),
        ('custom_temperatures', '실험온도', 'custom_temperatures'),
        ('expiry_period', '소비기한', 'expiry_period'),
        ('test_period', '실험기간', 'test_period'),
        ('sampling_count', '샘플링횟수', 'sampling_count'),
        ('report_type', '보고서종류', 'report_type'),
        ('extension_test', '연장실험', 'extension_test'),
        # 포장/기타
        ('packaging', '포장단위', 'packaging'),
        # 일정
        ('start_date', '시작일', 'start_date'),
        ('end_date', '종료일', 'end_date'),
        ('estimate_date', '견적일자', 'estimate_date'),
        ('status', '상태', 'status'),
        ('memo', '메모', 'memo'),
    ]

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")

        button_layout = QHBoxLayout(button_frame)

        new_schedule_btn = QPushButton("새 스케줄 작성")
        new_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_schedule_btn.clicked.connect(self.create_new_schedule)

        edit_schedule_btn = QPushButton("수정하기")
        edit_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogContentsView))
        edit_schedule_btn.setStyleSheet("background-color: #3498db; color: white;")
        edit_schedule_btn.clicked.connect(self.edit_selected_schedule)

        delete_schedule_btn = QPushButton("선택 삭제")
        delete_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_schedule_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        delete_schedule_btn.clicked.connect(self.delete_selected_schedule)

        button_layout.addWidget(new_schedule_btn)
        button_layout.addWidget(edit_schedule_btn)
        button_layout.addWidget(delete_schedule_btn)

        # 구분선
        button_layout.addSpacing(20)

        # 상태 변경 영역
        button_layout.addWidget(QLabel("상태 변경:"))

        self.status_combo = QComboBox()
        self.status_combo.addItems(["대기", "입고예정", "입고", "종료"])
        self.status_combo.setMinimumWidth(100)
        button_layout.addWidget(self.status_combo)

        change_status_btn = QPushButton("일괄 변경")
        change_status_btn.setStyleSheet("background-color: #27ae60; color: white;")
        change_status_btn.clicked.connect(self.change_selected_status)
        button_layout.addWidget(change_status_btn)

        button_layout.addStretch()

        # 표시 설정 버튼
        settings_btn = QPushButton("표시 설정")
        settings_btn.setStyleSheet("background-color: #9b59b6; color: white;")
        settings_btn.clicked.connect(self.open_display_settings)
        button_layout.addWidget(settings_btn)

        layout.addWidget(button_frame)

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
            QComboBox:hover {
                border: 1px solid #ab47bc;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #e1bee7;
                selection-color: #000000;
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
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)

        # 검색 필드 변경 시에도 필터 적용
        self.search_field_combo.currentIndexChanged.connect(self.on_search_text_changed)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_btn)

        search_layout.addStretch()

        layout.addWidget(search_frame)

        # 스케줄 목록 테이블 - 전체 컬럼 생성
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(len(self.ALL_COLUMNS))
        headers = [col[1] for col in self.ALL_COLUMNS]
        self.schedule_table.setHorizontalHeaderLabels(headers)
        self.schedule_table.setColumnHidden(1, True)  # ID 열 항상 숨김
        # 열 너비 조절 설정
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 사용자가 마우스로 조절 가능
        header.setStretchLastSection(True)  # 마지막 열이 남은 공간을 채움
        header.setSectionsMovable(True)  # 열 드래그 앤 드롭으로 순서 변경 가능
        header.setFirstSectionMovable(False)  # 첫 번째 열(선택)은 고정
        header.sectionMoved.connect(self.on_column_moved)  # 열 이동 시 저장

        # 체크박스 열(0번) 고정
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.schedule_table.setColumnWidth(0, 50)

        # 각 열의 기본 너비 설정 (컬럼 키 기반)
        column_widths = {
            'client_name': 120,
            'client_ceo': 80,
            'client_contact': 80,
            'client_email': 150,
            'client_phone': 100,
            'product_name': 120,
            'food_type': 100,
            'test_method': 80,
            'storage_condition': 70,
            'custom_temperatures': 120,
            'expiry_period': 90,
            'test_period': 70,
            'sampling_count': 70,
            'report_type': 100,
            'extension_test': 70,
            'packaging': 80,
            'start_date': 90,
            'end_date': 90,
            'estimate_date': 90,
            'status': 70,
            'memo': 150,
        }
        for col_index, col_def in enumerate(self.ALL_COLUMNS):
            col_key = col_def[0]
            if col_key in column_widths:
                self.schedule_table.setColumnWidth(col_index, column_widths[col_key])
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 헤더 클릭으로 정렬 기능 활성화
        self.schedule_table.setSortingEnabled(True)
        self.schedule_table.horizontalHeader().setSortIndicatorShown(True)
        self.schedule_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        # 정렬 상태 저장
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder

        # 더블클릭 이벤트 연결
        self.schedule_table.doubleClicked.connect(self.on_double_click)

        layout.addWidget(self.schedule_table)

        # 초기 컬럼 표시 설정 적용
        self.apply_column_settings()

        # 저장된 열 순서 적용
        self.apply_column_order()

        # 초기 데이터 로드
        self.load_schedules()
    
    def load_schedules(self):
        """스케줄 목록 로드"""
        try:
            from models.schedules import Schedule
            log_message('ScheduleTab', '스케줄 목록 로드 시작')

            raw_schedules = Schedule.get_all() or []
            # sqlite3.Row를 딕셔너리로 변환하여 .get() 메서드 사용 가능하게 함
            self.all_schedules = [dict(s) for s in raw_schedules]
            self.display_schedules(self.all_schedules)
            log_message('ScheduleTab', f'스케줄 {len(self.all_schedules)}개 로드 완료')
        except Exception as e:
            log_exception('ScheduleTab', f'스케줄 로드 중 오류: {str(e)}')

    def display_schedules(self, schedules):
        """스케줄 목록을 테이블에 표시"""
        # UI 업데이트 일시 중지 (성능 최적화)
        self.schedule_table.setUpdatesEnabled(False)
        try:
            self.schedule_table.setRowCount(0)

            # 컬럼 키와 인덱스 매핑
            col_map = {col[0]: idx for idx, col in enumerate(self.ALL_COLUMNS)}

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)

                # 각 컬럼에 대해 데이터 채우기
                for col_index, col_def in enumerate(self.ALL_COLUMNS):
                    col_key = col_def[0]
                    data_key = col_def[2] if len(col_def) > 2 else None

                    if col_key == 'select':
                        # 체크박스
                        checkbox = QCheckBox()
                        checkbox_widget = QWidget()
                        checkbox_layout = QHBoxLayout(checkbox_widget)
                        checkbox_layout.addWidget(checkbox)
                        checkbox_layout.setAlignment(Qt.AlignCenter)
                        checkbox_layout.setContentsMargins(0, 0, 0, 0)
                        self.schedule_table.setCellWidget(row, col_index, checkbox_widget)

                    elif col_key == 'id':
                        # ID
                        schedule_id = schedule.get('id', '')
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(str(schedule_id)))

                    elif col_key == 'test_method':
                        # 실험방법 (코드 → 텍스트 변환)
                        test_method = schedule.get('test_method', '') or ''
                        test_method_text = {
                            'real': '실측', 'acceleration': '가속',
                            'custom_real': '의뢰자(실측)', 'custom_acceleration': '의뢰자(가속)'
                        }.get(test_method, test_method)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(test_method_text))

                    elif col_key == 'storage_condition':
                        # 보관조건 (코드 → 텍스트 변환)
                        storage = schedule.get('storage_condition', '') or ''
                        storage_text = {
                            'room_temp': '상온', 'warm': '실온', 'cool': '냉장', 'freeze': '냉동'
                        }.get(storage, storage)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(storage_text))

                    elif col_key == 'food_type':
                        # 식품유형 (ID → 이름 변환)
                        food_type_id = schedule.get('food_type_id', '')
                        food_type_name = ''
                        if food_type_id:
                            try:
                                from models.product_types import ProductType
                                food_type = ProductType.get_by_id(food_type_id)
                                if food_type:
                                    food_type_name = food_type.get('type_name', '') or ''
                            except:
                                pass
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(food_type_name))

                    elif col_key == 'expiry_period':
                        # 소비기한 (일/월/년 조합)
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
                        # 실험기간 계산
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
                        # 보고서 종류
                        types = []
                        if schedule.get('report_interim'):
                            types.append('중간')
                        if schedule.get('report_korean'):
                            types.append('국문')
                        if schedule.get('report_english'):
                            types.append('영문')
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(', '.join(types)))

                    elif col_key == 'extension_test':
                        # 연장실험
                        ext = schedule.get('extension_test', False)
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem('진행' if ext else '미진행'))

                    elif col_key == 'packaging':
                        # 포장단위
                        weight = schedule.get('packaging_weight', 0) or 0
                        unit = schedule.get('packaging_unit', 'g') or 'g'
                        packaging_text = f"{weight}{unit}" if weight > 0 else ''
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(packaging_text))

                    elif col_key == 'status':
                        # 상태 (배경색 포함)
                        status = schedule.get('status', 'pending') or 'pending'
                        status_text = {
                            'pending': '대기', 'scheduled': '입고예정',
                            'received': '입고', 'completed': '종료',
                            'in_progress': '입고', 'cancelled': '종료'
                        }.get(status, status)
                        status_item = QTableWidgetItem(status_text)
                        if status in ['scheduled']:
                            status_item.setBackground(Qt.cyan)
                        elif status in ['received', 'in_progress']:
                            status_item.setBackground(Qt.yellow)
                        elif status in ['completed', 'cancelled']:
                            status_item.setBackground(Qt.green)
                        self.schedule_table.setItem(row, col_index, status_item)

                    elif col_key == 'custom_temperatures':
                        # 실험온도 표시 - 의뢰자 요청 온도 또는 보관조건에 따른 온도
                        custom_temps = schedule.get('custom_temperatures', '') or ''
                        if custom_temps:
                            # 의뢰자 요청 온도가 있으면 표시
                            temp_text = custom_temps.replace(',', ', ')
                            self.schedule_table.setItem(row, col_index, QTableWidgetItem(f"{temp_text}℃"))
                        else:
                            # 보관조건과 실험방법에 따라 온도 결정
                            test_method = schedule.get('test_method', 'real') or 'real'
                            storage = schedule.get('storage_condition', 'room_temp') or 'room_temp'

                            if test_method in ['acceleration', 'custom_acceleration']:
                                # 가속실험 온도
                                temp_map = {
                                    'room_temp': '15℃, 25℃, 35℃',
                                    'warm': '25℃, 35℃, 45℃',
                                    'cool': '5℃, 10℃, 15℃',
                                    'freeze': '-6℃, -12℃, -18℃'
                                }
                            else:
                                # 실측실험 온도
                                temp_map = {
                                    'room_temp': '15℃',
                                    'warm': '25℃',
                                    'cool': '10℃',
                                    'freeze': '-18℃ 이하'
                                }
                            temp_text = temp_map.get(storage, '')
                            self.schedule_table.setItem(row, col_index, QTableWidgetItem(temp_text))

                    else:
                        # 기타 필드 (직접 매핑)
                        value = schedule.get(data_key, '') if data_key else ''
                        if value is None:
                            value = ''
                        self.schedule_table.setItem(row, col_index, QTableWidgetItem(str(value)))

            log_message('ScheduleTab', f'스케줄 {len(schedules)}개 표시 완료')
        except Exception as e:
            log_exception('ScheduleTab', f'스케줄 표시 중 오류: {str(e)}')
        finally:
            # UI 업데이트 재개
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

    def on_search_text_changed(self):
        """검색어 변경 시 타이머 시작 (디바운싱)"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms 후 필터링 실행

    def filter_schedules(self):
        """실시간 검색 필터링 (초성 검색 지원)"""
        try:
            search_text = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            if not search_text:
                self.display_schedules(self.all_schedules)
                return

            log_message('ScheduleTab', f'스케줄 검색 시작: "{search_text}" (필드: {search_field})')

            filtered = []
            is_chosung = self.is_chosung_only(search_text)

            for schedule in self.all_schedules:
                client_name = schedule.get('client_name', '') or ''
                product_name = schedule.get('product_name', '') or ''
                status = schedule.get('status', '') or ''
                status_text = {
                    'pending': '대기', 'scheduled': '입고예정',
                    'received': '입고', 'completed': '종료',
                    'in_progress': '입고', 'cancelled': '종료'
                }.get(status, status)

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

            log_message('ScheduleTab', f'스케줄 검색 완료: {len(filtered)}개 결과')
            self.display_schedules(filtered)
        except Exception as e:
            log_exception('ScheduleTab', f'스케줄 검색 중 오류: {str(e)}')

    def reset_search(self):
        """검색 초기화"""
        self.search_input.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.display_schedules(self.all_schedules)

    def on_double_click(self, index):
        """더블클릭 시 스케줄 관리 탭으로 이동"""
        row = index.row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if schedule_id_item:
            schedule_id = int(schedule_id_item.text())
            self.schedule_double_clicked.emit(schedule_id)

    def delete_selected_schedule(self):
        """선택된 스케줄 삭제"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "삭제 실패", "삭제할 스케줄을 선택하세요.")
            return

        row = selected_rows[0].row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if not schedule_id_item:
            return

        schedule_id = int(schedule_id_item.text())
        client_name = self.schedule_table.item(row, 2).text()  # 업체명은 2번 열
        product_name = self.schedule_table.item(row, 3).text()  # 제품명은 3번 열

        reply = QMessageBox.question(
            self, '삭제 확인',
            f'다음 스케줄을 삭제하시겠습니까?\n\n업체: {client_name}\n제품: {product_name}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from models.schedules import Schedule
                success = Schedule.delete(schedule_id)
                if success:
                    QMessageBox.information(self, "삭제 완료", "스케줄이 삭제되었습니다.")
                    self.load_schedules()
                else:
                    QMessageBox.warning(self, "삭제 실패", "스케줄 삭제에 실패했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"삭제 중 오류가 발생했습니다:\n{str(e)}")

    def create_new_schedule(self):
        """새 스케줄 작성 다이얼로그 표시"""
        try:
            print("스케줄 생성 시작")  # 디버깅 로그
            dialog = ScheduleCreateDialog(self)
            print("ScheduleCreateDialog 인스턴스 생성 성공")  # 디버깅 로그

            if dialog.exec_():
                print("다이얼로그 실행 성공")  # 디버깅 로그
                # 스케줄 저장 후 목록 새로고침
                self.load_schedules()
        except Exception as e:
            import traceback
            error_msg = f"스케줄 생성 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)  # 콘솔에 오류 출력
            QMessageBox.critical(self, "오류", error_msg)

    def edit_selected_schedule(self):
        """선택된 스케줄 수정 다이얼로그 표시"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "수정 실패", "수정할 스케줄을 선택하세요.")
            return

        row = selected_rows[0].row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if not schedule_id_item:
            return

        schedule_id = int(schedule_id_item.text())

        try:
            print(f"스케줄 수정 시작: ID {schedule_id}")
            dialog = ScheduleCreateDialog(self, schedule_id=schedule_id)

            if dialog.exec_():
                print("스케줄 수정 완료")
                self.load_schedules()
        except Exception as e:
            import traceback
            error_msg = f"스케줄 수정 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "오류", error_msg)

    def change_selected_status(self):
        """체크된 스케줄들의 상태를 일괄 변경"""
        try:
            from models.schedules import Schedule

            # 선택된 상태 가져오기
            selected_status_text = self.status_combo.currentText()
            status_map = {
                '대기': 'pending',
                '입고예정': 'scheduled',
                '입고': 'received',
                '종료': 'completed'
            }
            new_status = status_map.get(selected_status_text, 'pending')

            # 체크된 행 찾기
            checked_rows = []
            for row in range(self.schedule_table.rowCount()):
                checkbox_widget = self.schedule_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        checked_rows.append(row)

            if not checked_rows:
                QMessageBox.warning(self, "변경 실패", "변경할 스케줄을 체크하세요.")
                return

            # 확인 대화상자
            reply = QMessageBox.question(
                self, '상태 변경 확인',
                f'{len(checked_rows)}개의 스케줄 상태를 "{selected_status_text}"(으)로 변경하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success_count = 0
                for row in checked_rows:
                    schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
                    if schedule_id_item:
                        schedule_id = int(schedule_id_item.text())
                        if Schedule.update_status(schedule_id, new_status):
                            success_count += 1

                QMessageBox.information(
                    self, "변경 완료",
                    f"{success_count}개의 스케줄 상태가 변경되었습니다."
                )
                self.load_schedules()

        except Exception as e:
            import traceback
            error_msg = f"상태 변경 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "오류", error_msg)

    def add_sample_data(self):
        """샘플 데이터 추가 (테스트용)"""
        sample_data = [
            {"client": "계림농장", "sample": "계란 샘플", "start": "2023-07-10", "end": "2023-07-30", "status": "진행중"},
            {"client": "거성씨푸드", "sample": "생선 샘플", "start": "2023-07-05", "end": "2023-07-25", "status": "완료"}
        ]
        
        self.schedule_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(data["client"]))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(data["sample"]))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(data["start"]))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(data["end"]))
            
            status_item = QTableWidgetItem(data["status"])
            if data["status"] == "진행중":
                status_item.setBackground(Qt.yellow)
            elif data["status"] == "완료":
                status_item.setBackground(Qt.green)

            self.schedule_table.setItem(row, 4, status_item)

    def open_display_settings(self):
        """표시 설정 다이얼로그 열기"""
        dialog = ScheduleDisplaySettingsDialog(self)
        if dialog.exec_():
            self.apply_column_settings()

    def get_column_settings(self):
        """데이터베이스에서 컬럼 설정 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_tab_columns'")
            result = cursor.fetchone()
            conn.close()

            if result:
                return result['value'].split(',')
            else:
                # 기본값: 기본 표시 컬럼
                return [opt[0] for opt in ScheduleDisplaySettingsDialog.COLUMN_OPTIONS if opt[2]]
        except Exception as e:
            print(f"컬럼 설정 로드 오류: {e}")
            return [opt[0] for opt in ScheduleDisplaySettingsDialog.COLUMN_OPTIONS if opt[2]]

    def apply_column_settings(self):
        """컬럼 표시 설정을 테이블에 적용"""
        visible_columns = self.get_column_settings()

        # 컬럼 키와 인덱스 매핑 (enumerate로 동적 인덱스 생성)
        for col_index, col_def in enumerate(self.ALL_COLUMNS):
            col_key = col_def[0]
            if col_key == 'select':
                # 선택 열은 항상 표시
                self.schedule_table.setColumnHidden(col_index, False)
            elif col_key == 'id':
                # ID 열은 항상 숨김
                self.schedule_table.setColumnHidden(col_index, True)
            else:
                # 설정에 따라 표시/숨김
                is_hidden = col_key not in visible_columns
                self.schedule_table.setColumnHidden(col_index, is_hidden)

    def on_column_moved(self, logical_index, old_visual_index, new_visual_index):
        """열이 이동되면 순서 저장"""
        self.save_column_order()

    def save_column_order(self):
        """현재 열 순서를 데이터베이스에 저장"""
        try:
            from database import get_connection
            header = self.schedule_table.horizontalHeader()

            # 현재 visual 순서대로 logical index 수집
            order = []
            for visual_idx in range(header.count()):
                logical_idx = header.logicalIndex(visual_idx)
                order.append(str(logical_idx))

            order_str = ','.join(order)

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES ('schedule_column_order', ?)
            """, (order_str,))
            conn.commit()
            conn.close()
            print(f"열 순서 저장됨: {order_str}")
        except Exception as e:
            print(f"열 순서 저장 오류: {e}")

    def get_column_order(self):
        """데이터베이스에서 열 순서 로드"""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_column_order'")
            result = cursor.fetchone()
            conn.close()

            if result:
                return [int(x) for x in result['value'].split(',')]
            return None
        except Exception as e:
            print(f"열 순서 로드 오류: {e}")
            return None

    def apply_column_order(self):
        """저장된 열 순서를 테이블에 적용"""
        order = self.get_column_order()
        if not order:
            return

        header = self.schedule_table.horizontalHeader()

        # order 리스트는 각 visual position에 어떤 logical index가 있어야 하는지를 나타냄
        for visual_idx, logical_idx in enumerate(order):
            current_visual = header.visualIndex(logical_idx)
            if current_visual != visual_idx:
                header.moveSection(current_visual, visual_idx)

    def on_header_clicked(self, logical_index):
        """헤더 클릭 시 해당 컬럼으로 정렬"""
        # 선택 열(0번)과 ID 열(1번)은 정렬 제외
        if logical_index in [0, 1]:
            return

        # 같은 컬럼을 다시 클릭하면 정렬 순서 변경
        if self.current_sort_column == logical_index:
            if self.current_sort_order == Qt.AscendingOrder:
                self.current_sort_order = Qt.DescendingOrder
            else:
                self.current_sort_order = Qt.AscendingOrder
        else:
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder

        # 정렬 실행
        self.schedule_table.sortItems(logical_index, self.current_sort_order)