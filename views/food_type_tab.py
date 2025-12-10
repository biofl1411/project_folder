from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QFileDialog, QProgressDialog,
                          QDialog, QFormLayout, QLineEdit, QCheckBox, QApplication,
                          QComboBox)
from PyQt5.QtCore import Qt, QCoreApplication, QTimer
import pandas as pd
import os

from models.product_types import ProductType
from database import get_connection
from utils.logger import log_message, log_error, log_exception

class FoodTypeTab(QWidget):
    # 한글 초성 매핑
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_food_types = []  # 전체 식품유형 목록 저장
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder
        self.current_user = None  # 현재 로그인한 사용자

        # 버튼 참조 저장 (권한 체크용)
        self.new_type_btn = None
        self.edit_btn = None
        self.delete_btn = None
        self.clear_btn = None
        self.import_btn = None
        self.update_btn = None
        self.export_btn = None
        self.db_info_btn = None

        # 검색 디바운싱을 위한 타이머 (300ms 지연)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_food_types)

        self.initUI()
        self.load_food_types()

    def set_current_user(self, user):
        """현재 로그인한 사용자 설정 및 권한 적용"""
        self.current_user = user
        self.apply_permissions()
        # 사용자 변경 시 데이터 다시 로드
        self.load_food_types()

    def clear_data(self):
        """탭 데이터 초기화 (로그아웃 시 호출)"""
        self.all_food_types = []
        self.current_user = None
        if hasattr(self, 'food_type_table') and self.food_type_table:
            self.food_type_table.setRowCount(0)

    def apply_permissions(self):
        """사용자 권한에 따라 버튼 활성화/비활성화"""
        if not self.current_user:
            return

        from models.users import User

        # 관리자는 모든 권한
        if self.current_user.get('role') == 'admin':
            return

        # 각 버튼에 대한 권한 체크
        if self.new_type_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_create')
            self.new_type_btn.setEnabled(has_perm)
            if not has_perm:
                self.new_type_btn.setToolTip("권한이 없습니다")

        if self.edit_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_edit')
            self.edit_btn.setEnabled(has_perm)
            if not has_perm:
                self.edit_btn.setToolTip("권한이 없습니다")

        if self.delete_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_delete')
            self.delete_btn.setEnabled(has_perm)
            if not has_perm:
                self.delete_btn.setToolTip("권한이 없습니다")

        if self.clear_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_reset')
            self.clear_btn.setEnabled(has_perm)
            if not has_perm:
                self.clear_btn.setToolTip("권한이 없습니다")

        if self.import_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_import_excel')
            self.import_btn.setEnabled(has_perm)
            if not has_perm:
                self.import_btn.setToolTip("권한이 없습니다")

        if self.update_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_update_excel')
            self.update_btn.setEnabled(has_perm)
            if not has_perm:
                self.update_btn.setToolTip("권한이 없습니다")

        if self.export_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_export_excel')
            self.export_btn.setEnabled(has_perm)
            if not has_perm:
                self.export_btn.setToolTip("권한이 없습니다")

        if self.db_info_btn:
            has_perm = User.has_permission(self.current_user, 'food_type_db_info')
            self.db_info_btn.setEnabled(has_perm)
            if not has_perm:
                self.db_info_btn.setToolTip("권한이 없습니다")
        
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        button_layout = QHBoxLayout(button_frame)
        
        # 전체 선택 체크박스 추가
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)
        
        self.new_type_btn = QPushButton("새 식품유형 등록")
        self.new_type_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        self.new_type_btn.clicked.connect(self.create_new_food_type)

        self.edit_btn = QPushButton("수정")
        self.edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        self.edit_btn.clicked.connect(self.edit_food_type)

        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        self.delete_btn.clicked.connect(self.delete_food_type)

        # 전체 초기화 버튼 추가
        self.clear_btn = QPushButton("전체 초기화")
        self.clear_btn.setIcon(self.style().standardIcon(self.style().SP_DialogResetButton))
        self.clear_btn.clicked.connect(self.clear_all_food_types)

        self.import_btn = QPushButton("엑셀 가져오기")
        self.import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        self.import_btn.clicked.connect(self.import_from_excel)

        # 엑셀 업데이트 버튼 추가
        self.update_btn = QPushButton("엑셀 업데이트")
        self.update_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        self.update_btn.clicked.connect(self.update_from_excel)

        self.export_btn = QPushButton("엑셀 내보내기")
        self.export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        self.export_btn.clicked.connect(self.export_to_excel)

        # 데이터베이스 정보 버튼
        self.db_info_btn = QPushButton("DB 정보")
        self.db_info_btn.setIcon(self.style().standardIcon(self.style().SP_FileIcon))
        self.db_info_btn.clicked.connect(self.check_database_location)

        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addWidget(self.new_type_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.db_info_btn)
        button_layout.addStretch()
        
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
        self.search_field_combo.addItems(["전체", "식품유형", "카테고리", "검사항목"])
        self.search_field_combo.setMinimumWidth(100)
        search_layout.addWidget(self.search_field_combo)

        # 검색 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력... (초성 검색 가능: ㄱㄹㄴㅈ)")
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

        # 2. 식품유형 목록 테이블
        self.food_type_table = QTableWidget()
        self.food_type_table.setColumnCount(8)  # 8개 열 (검사항목 필드 추가)
        self.food_type_table.setHorizontalHeaderLabels([
            "선택", "식품유형", "카테고리", "단서조항_1", "단서조항_2", "성상", "검사항목", "생성일"
        ])
        
        # 열 너비 조절 설정
        header = self.food_type_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 사용자가 마우스로 조절 가능
        header.setStretchLastSection(True)  # 마지막 열이 남은 공간을 채움

        # 체크박스 열(0번) 고정
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.food_type_table.setColumnWidth(0, 50)

        # 각 열의 기본 너비 설정
        column_widths = {
            1: 150,   # 식품유형
            2: 100,   # 카테고리
            3: 100,   # 단서조항_1
            4: 100,   # 단서조항_2
            5: 80,    # 성상
            6: 200,   # 검사항목
            7: 100,   # 생성일
        }
        for col, width in column_widths.items():
            self.food_type_table.setColumnWidth(col, width)
            
        self.food_type_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.food_type_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 헤더 클릭으로 정렬 기능 활성화
        self.food_type_table.setSortingEnabled(True)
        self.food_type_table.horizontalHeader().setSortIndicatorShown(True)
        self.food_type_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        layout.addWidget(self.food_type_table)
    
    def select_all_rows(self, checked):
        """모든 행 선택/해제"""
        try:
            # 행이 없는 경우 처리
            if self.food_type_table.rowCount() == 0:
                return
                
            for row in range(self.food_type_table.rowCount()):
                checkbox_widget = self.food_type_table.cellWidget(row, 0)
                if checkbox_widget:
                    # 위젯 내의 체크박스 찾기
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(checked)
                    else:
                        print(f"행 {row}의 체크박스를 찾을 수 없습니다.")
                else:
                    print(f"행 {row}의 위젯을 찾을 수 없습니다.")
        except Exception as e:
            print(f"전체 선택 중 오류 발생: {str(e)}")
    
    def load_food_types(self):
        """식품유형 목록 로드"""
        try:
            log_message('FoodTypeTab', '식품유형 목록 로드 시작')
            raw_food_types = ProductType.get_all() or []
            # sqlite3.Row를 딕셔너리로 변환
            self.all_food_types = [dict(ft) for ft in raw_food_types]
            self.display_food_types(self.all_food_types)
            log_message('FoodTypeTab', f'식품유형 {len(self.all_food_types)}개 로드 완료')
        except Exception as e:
            log_exception('FoodTypeTab', f'식품유형 로드 중 오류: {str(e)}')
            QMessageBox.critical(self, "오류", f"식품유형 로드 중 오류 발생: {str(e)}")

    def display_food_types(self, food_types):
        """식품유형 목록을 테이블에 표시"""
        # UI 업데이트 일시 중지 (성능 최적화)
        self.food_type_table.setUpdatesEnabled(False)
        try:
            self.food_type_table.setRowCount(len(food_types) if food_types else 0)

            if food_types:
                for row, food_type in enumerate(food_types):
                    # 체크박스 추가
                    checkbox = QCheckBox()
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    self.food_type_table.setCellWidget(row, 0, checkbox_widget)

                    # 나머지 데이터 설정
                    self.food_type_table.setItem(row, 1, QTableWidgetItem(str(food_type['type_name'] or '')))
                    self.food_type_table.setItem(row, 2, QTableWidgetItem(food_type['category'] or ""))
                    self.food_type_table.setItem(row, 3, QTableWidgetItem(food_type['sterilization'] or ""))
                    self.food_type_table.setItem(row, 4, QTableWidgetItem(food_type['pasteurization'] or ""))
                    self.food_type_table.setItem(row, 5, QTableWidgetItem(food_type['appearance'] or ""))
                    self.food_type_table.setItem(row, 6, QTableWidgetItem(food_type['test_items'] or ""))
                    # datetime 객체를 문자열로 변환
                    created_at = food_type['created_at']
                    if created_at:
                        created_at = str(created_at) if not isinstance(created_at, str) else created_at
                    self.food_type_table.setItem(row, 7, QTableWidgetItem(created_at or ""))
        finally:
            # UI 업데이트 재개
            self.food_type_table.setUpdatesEnabled(True)

    def get_chosung(self, text):
        """문자열에서 초성 추출"""
        result = ""
        for char in text:
            if '가' <= char <= '힣':
                char_code = ord(char) - ord('가')
                chosung_idx = char_code // 588
                # 인덱스 범위 확인 (0-18)
                if 0 <= chosung_idx < len(self.CHOSUNG_LIST):
                    result += self.CHOSUNG_LIST[chosung_idx]
                else:
                    result += char  # 범위 밖이면 원래 문자 유지
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

    def filter_food_types(self):
        """실시간 검색 필터링 (초성 검색 지원)"""
        try:
            search_text = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            if not search_text:
                self.display_food_types(self.all_food_types)
                return

            filtered = []
            is_chosung = self.is_chosung_only(search_text)

            for food_type in self.all_food_types:
                # 안전한 값 접근 (딕셔너리로 변환됨)
                type_name = str(food_type.get('type_name', '') or '')
                category = str(food_type.get('category', '') or '')
                test_items = str(food_type.get('test_items', '') or '')

                match = False

                if search_field == "전체":
                    if is_chosung:
                        match = (self.match_chosung(type_name, search_text) or
                                 self.match_chosung(category, search_text) or
                                 self.match_chosung(test_items, search_text))
                    else:
                        search_lower = search_text.lower()
                        match = (search_lower in type_name.lower() or
                                 search_lower in category.lower() or
                                 search_lower in test_items.lower())
                elif search_field == "식품유형":
                    if is_chosung:
                        match = self.match_chosung(type_name, search_text)
                    else:
                        match = search_text.lower() in type_name.lower()
                elif search_field == "카테고리":
                    if is_chosung:
                        match = self.match_chosung(category, search_text)
                    else:
                        match = search_text.lower() in category.lower()
                elif search_field == "검사항목":
                    if is_chosung:
                        match = self.match_chosung(test_items, search_text)
                    else:
                        match = search_text.lower() in test_items.lower()

                if match:
                    filtered.append(food_type)

            self.display_food_types(filtered)
        except Exception as e:
            log_exception('FoodTypeTab', f'검색 필터링 중 오류: {str(e)}')

    def reset_search(self):
        """검색 초기화"""
        self.search_input.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.display_food_types(self.all_food_types)

    def on_header_clicked(self, logical_index):
        """헤더 클릭 시 해당 컬럼으로 정렬"""
        # 선택 열(0번)은 정렬 제외
        if logical_index == 0:
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
        self.food_type_table.sortItems(logical_index, self.current_sort_order)

    def create_new_food_type(self):
        """새 식품유형 등록"""
        try:
            log_message('FoodTypeTab', '새 식품유형 등록 시작')
            dialog = FoodTypeDialog(self)
            if dialog.exec_():
                log_message('FoodTypeTab', '새 식품유형 등록 성공')
                self.load_food_types()
        except Exception as e:
            log_exception('FoodTypeTab', f'식품유형 등록 중 오류: {str(e)}')
            QMessageBox.critical(self, "오류", f"식품유형 등록 중 오류 발생: {str(e)}")

    def edit_food_type(self):
        """식품유형 정보 수정"""
        try:
            log_message('FoodTypeTab', '식품유형 수정 시작')
            # 체크박스가 선택된 행 찾기
            selected_row = -1
            for row in range(self.food_type_table.rowCount()):
                checkbox_widget = self.food_type_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_row = row
                        break

            if selected_row == -1:
                log_message('FoodTypeTab', '수정할 식품유형이 선택되지 않음', 'WARNING')
                QMessageBox.warning(self, "선택 오류", "수정할 식품유형을 선택하세요.")
                return

            # 선택된 행의 데이터 가져오기
            type_name_item = self.food_type_table.item(selected_row, 1)
            if not type_name_item:
                QMessageBox.warning(self, "데이터 오류", "식품유형명을 찾을 수 없습니다.")
                return
            type_name = type_name_item.text()
            log_message('FoodTypeTab', f"식품유형 '{type_name}' 수정 시도")

            # 해당 식품유형 정보 가져오기
            raw_food_type = ProductType.get_by_name(type_name)
            if not raw_food_type:
                log_error('FoodTypeTab', f"식품유형 '{type_name}' 정보를 찾을 수 없음")
                QMessageBox.warning(self, "데이터 오류", "선택한 식품유형 정보를 찾을 수 없습니다.")
                return

            # sqlite3.Row를 딕셔너리로 변환
            food_type = dict(raw_food_type)

            # 수정 다이얼로그 표시
            dialog = FoodTypeDialog(self, food_type)
            if dialog.exec_():
                log_message('FoodTypeTab', f"식품유형 '{type_name}' 수정 성공")
                self.load_food_types()
            else:
                log_message('FoodTypeTab', f"식품유형 '{type_name}' 수정 취소")
        except Exception as e:
            log_exception('FoodTypeTab', f'식품유형 수정 중 오류: {str(e)}')
            QMessageBox.critical(self, "오류", f"식품유형 수정 중 오류 발생: {str(e)}")
    
    def delete_food_type(self):
        """식품유형 삭제"""
        # 체크박스가 선택된 모든 행 찾기
        selected_rows = []
        for row in range(self.food_type_table.rowCount()):
            checkbox_widget = self.food_type_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "삭제할 식품유형을 선택하세요.")
            return
        
        # 확인 메시지 표시
        count = len(selected_rows)
        reply = QMessageBox.question(
            self, "식품유형 삭제", 
            f"선택한 {count}개의 식품유형을 정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            # 선택된 행의 역순으로 삭제 (인덱스 변화 방지)
            for row in sorted(selected_rows, reverse=True):
                type_name_item = self.food_type_table.item(row, 1)
                if not type_name_item:
                    continue
                type_name = type_name_item.text()

                # 해당 식품유형 정보 가져오기
                food_type = ProductType.get_by_name(type_name)
                if food_type and ProductType.delete(food_type['id']):
                    self.food_type_table.removeRow(row)
                    deleted_count += 1
            
            # 삭제 결과 메시지
            if deleted_count > 0:
                QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 식품유형이 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "삭제 실패", "식품유형 삭제 중 오류가 발생했습니다.")
    
    def clear_all_food_types(self):
        """식품 유형 데이터 전체 초기화"""
        # 확인 메시지 표시
        reply = QMessageBox.question(
            self, "데이터 초기화", 
            "모든 식품 유형 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 두 번째 최종 확인
            reply2 = QMessageBox.critical(
                self, "최종 확인",
                "정말로 모든 식품유형을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없으며 데이터가 영구적으로 손실됩니다.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply2 != QMessageBox.Yes:
                return
                
            try:
                log_message('FoodTypeTab', '식품유형 전체 초기화 시작')

                # DB 연결 직접 사용하여 삭제 확인
                conn = get_connection()
                cursor = conn.cursor()

                # 트랜잭션 시작
                cursor.execute("BEGIN TRANSACTION")

                # 삭제 전 데이터 백업 (선택사항)
                cursor.execute("SELECT * FROM food_types")
                backup_data = cursor.fetchall()

                # 데이터 삭제
                cursor.execute("DELETE FROM food_types")

                # 자동 증가 ID 초기화
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='food_types'")

                # 커밋
                conn.commit()
                conn.close()

                # 테이블 갱신
                self.food_type_table.setRowCount(0)
                self.load_food_types()

                log_message('FoodTypeTab', f'식품유형 전체 초기화 완료: {len(backup_data)}개 항목 삭제')
                QMessageBox.information(self, "초기화 완료", f"모든 식품 유형 데이터({len(backup_data)}개)가 삭제되었습니다.")

            except Exception as e:
                log_exception('FoodTypeTab', f'데이터 초기화 중 오류: {str(e)}')
                QMessageBox.critical(self, "초기화 실패", f"데이터 초기화 중 오류가 발생했습니다: {str(e)}")
    
    def update_from_excel(self):
        """엑셀 파일에서 데이터 업데이트 후 저장"""
        # 파일 선택 대화상자 표시
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 열 이름 표준화 함수
            def normalize_column_name(name):
                if isinstance(name, str):
                    return name.lower().replace(" ", "")
                return ""
            
            # 표준화된 열 이름으로 매핑 생성
            normalized_columns = {normalize_column_name(col): col for col in df.columns}
            
            # 필수 열 확인
            required_column = "식품유형"
            required_normalized = normalize_column_name(required_column)
            
            if required_normalized not in normalized_columns.keys():
                QMessageBox.warning(self, "파일 오류", f"엑셀 파일에 '{required_column}' 열이 없습니다.")
                return
            
            actual_required_col = normalized_columns[required_normalized]
            
            # 기존 데이터 모두 삭제 (초기화)
            reply = QMessageBox.question(
                self, "데이터 갱신", 
                "기존 식품 유형 데이터를 모두 삭제하고 엑셀 파일의 데이터로 대체하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
                column_mapping = {
                    "식품유형": "type_name",
                    "카테고리": "category",
                    "단서조항_1": "sterilization",
                    "단서조항_2": "pasteurization",
                    "성상": "appearance",
                    "검사항목": "test_items"
                }
                
                # 표준화된 컬럼 매핑 생성
                normalized_mapping = {normalize_column_name(k): v for k, v in column_mapping.items()}
                
                # 데이터베이스 연결
                conn = get_connection()
                cursor = conn.cursor()
                
                # 기존 데이터 삭제
                cursor.execute("DELETE FROM food_types")
                
                # 엑셀 데이터 삽입
                inserted_count = 0
                for i, row in df.iterrows():
                    if pd.isna(row[actual_required_col]) or str(row[actual_required_col]).strip() == "":
                        continue
                    
                    # 데이터 준비
                    food_type_data = {}
                    food_type_data["type_name"] = str(row[actual_required_col]).strip()
                    
                    # 다른 필드 처리
                    for excel_col, db_field in column_mapping.items():
                        if excel_col == "식품유형":  # 이미 처리함
                            continue
                            
                        norm_excel_col = normalize_column_name(excel_col)
                        if norm_excel_col in normalized_columns:
                            actual_col = normalized_columns[norm_excel_col]
                            if actual_col in row and not pd.isna(row[actual_col]):
                                food_type_data[db_field] = str(row[actual_col]).strip()
                            else:
                                food_type_data[db_field] = ""
                        else:
                            food_type_data[db_field] = ""
                    
                    # 데이터 삽입
                    cursor.execute(
                        "INSERT INTO food_types (type_name, category, sterilization, pasteurization, appearance, test_items) VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            food_type_data["type_name"],
                            food_type_data.get("category", ""),
                            food_type_data.get("sterilization", ""),
                            food_type_data.get("pasteurization", ""),
                            food_type_data.get("appearance", ""),
                            food_type_data.get("test_items", "")
                        )
                    )
                    inserted_count += 1
                
                # 변경사항 저장
                conn.commit()
                conn.close()
                
                # 테이블 새로고침
                self.load_food_types()
                
                QMessageBox.information(
                    self, "업데이트 완료", 
                    f"기존 데이터를 삭제하고 {inserted_count}개의 새 데이터를 추가했습니다."
                )
        except Exception as e:
            QMessageBox.critical(self, "업데이트 실패", f"데이터 업데이트 중 오류가 발생했습니다:\n{str(e)}")
    
    def import_from_excel(self):
        """엑셀 파일에서 식품유형 정보 가져오기"""
        # 파일 선택 대화상자 표시
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 열 이름 표준화 함수
            def normalize_column_name(name):
                if isinstance(name, str):
                    return name.lower().replace(" ", "")
                return ""
            
            # 표준화된 열 이름으로 매핑 생성
            normalized_columns = {normalize_column_name(col): col for col in df.columns}
            
            # 필수 열 확인
            required_column = "식품유형"
            required_normalized = normalize_column_name(required_column)
            
            if required_normalized not in normalized_columns.keys():
                QMessageBox.warning(self, "파일 오류", f"엑셀 파일에 '{required_column}' 열이 없습니다.")
                return
            
            actual_required_col = normalized_columns[required_normalized]
            
            # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
            column_mapping = {
                "식품유형": "type_name",
                "카테고리": "category",
                "단서조항_1": "sterilization",
                "단서조항_2": "pasteurization",
                "성상": "appearance",
                "검사항목": "test_items"
            }
            
            # 표준화된 컬럼 매핑 생성
            normalized_mapping = {normalize_column_name(k): v for k, v in column_mapping.items()}
            
            # 디버깅 - 엑셀 열 이름 및 정규화된 매핑 출력
            print("엑셀 원본 열 이름:", df.columns.tolist())
            print("정규화된 열 이름 매핑:", normalized_columns)
            print("정규화된 컬럼 매핑:", normalized_mapping)
            
            # 진행 상황 대화상자 표시
            progress = QProgressDialog("식품유형 정보 가져오는 중...", "취소", 0, len(df), self)
            progress.setWindowTitle("데이터 가져오기")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # 각 행 처리
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            for i, row in df.iterrows():
                # 진행 상황 업데이트
                progress.setValue(i)
                QCoreApplication.processEvents()
                
                # 사용자 취소 확인
                if progress.wasCanceled():
                    break
                
                # 필수 필드가 비어있는지 확인
                if pd.isna(row[actual_required_col]) or str(row[actual_required_col]).strip() == "":
                    skipped_count += 1
                    continue
                
                # 데이터 준비
                food_type_data = {}
                food_type_data["type_name"] = str(row[actual_required_col]).strip()
                
                # 디버깅 - 현재 처리 중인 행 정보 출력
                print(f"\n처리 중인 행 {i+1}: 식품유형 = {food_type_data['type_name']}")
                
                # 다른 필드 처리
                for excel_col, db_field in column_mapping.items():
                    if excel_col == "식품유형":  # 이미 처리함
                        continue
                        
                    norm_excel_col = normalize_column_name(excel_col)
                    if norm_excel_col in normalized_columns:
                        actual_col = normalized_columns[norm_excel_col]
                        if actual_col in row and not pd.isna(row[actual_col]):
                            food_type_data[db_field] = str(row[actual_col]).strip()
                            print(f"  - {excel_col}({actual_col}) -> {db_field}: {food_type_data[db_field]}")
                        else:
                            food_type_data[db_field] = ""
                            print(f"  - {excel_col}({actual_col}) -> {db_field}: 값 없음")
                    else:
                        food_type_data[db_field] = ""
                        print(f"  - {excel_col} 열을 찾을 수 없음")
                
                # 이미 존재하는 식품유형인지 확인
                existing_type = ProductType.get_by_name(food_type_data["type_name"])
                
                if existing_type:
                    # 기존 식품유형 정보 업데이트
                    print(f"  -> 기존 항목 업데이트: ID = {existing_type['id']}")
                    if ProductType.update(
                        existing_type["id"],
                        food_type_data["type_name"],
                        food_type_data.get("category", ""),
                        food_type_data.get("sterilization", ""),
                        food_type_data.get("pasteurization", ""),
                        food_type_data.get("appearance", ""),
                        food_type_data.get("test_items", "")
                    ):
                        updated_count += 1
                else:
                    # 새 식품유형 생성
                    print(f"  -> 새 항목 추가")
                    if ProductType.create(
                        food_type_data["type_name"],
                        food_type_data.get("category", ""),
                        food_type_data.get("sterilization", ""),
                        food_type_data.get("pasteurization", ""),
                        food_type_data.get("appearance", ""),
                        food_type_data.get("test_items", "")
                    ):
                        imported_count += 1
            
            # 진행 상황 대화상자 종료
            progress.setValue(len(df))
            
            # 테이블 새로고침
            self.load_food_types()
            
            # 결과 메시지 표시
            QMessageBox.information(
                self, "가져오기 완료",
                f"식품유형 정보 가져오기가 완료되었습니다.\n"
                f"- 새로 추가된 항목: {imported_count}개\n"
                f"- 업데이트된 항목: {updated_count}개\n"
                f"- 건너뛴 항목: {skipped_count}개"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일을 처리하는 중 오류가 발생했습니다.\n{str(e)}")
    
    def export_to_excel(self):
        """식품유형 정보를 엑셀 파일로 내보내기"""
        # 파일 저장 대화상자 표시
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # 파일 확장자 확인 및 추가
        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'
        
        try:
            # DB에서 모든 식품유형 정보 가져오기
            food_types = ProductType.get_all()
            
            if not food_types:
                QMessageBox.warning(self, "데이터 없음", "내보낼 식품유형 정보가 없습니다.")
                return
            
            # 데이터 변환
            data = []
            for food_type in food_types:
                # datetime 객체를 문자열로 변환
                created_at_val = food_type["created_at"]
                if created_at_val and not isinstance(created_at_val, str):
                    created_at_val = str(created_at_val)
                data.append({
                    "식품유형": food_type["type_name"],
                    "카테고리": food_type["category"] or "",
                    "단서조항_1": food_type["sterilization"] or "",
                    "단서조항_2": food_type["pasteurization"] or "",
                    "성상": food_type["appearance"] or "",
                    "검사항목": food_type["test_items"] or "",
                    "생성일": created_at_val or ""
                })
            
            # DataFrame 생성 및 엑셀 파일로 저장
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            # 성공 메시지
            QMessageBox.information(
                self, "내보내기 완료", 
                f"식품유형 정보가 엑셀 파일로 저장되었습니다.\n파일 위치: {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일로 내보내는 중 오류가 발생했습니다.\n{str(e)}")
    
    def check_database_location(self):
        """데이터베이스 파일 위치 확인"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db_info = cursor.fetchone()
            db_path = db_info['DATABASE()'] if db_info else "Unknown"
            conn.close()
            
            QMessageBox.information(
                self, "데이터베이스 정보", 
                f"데이터베이스 파일 위치:\n{db_path}\n\n변경사항이 이 파일에 저장됩니다."
            )
        except Exception as e:
            QMessageBox.warning(self, "정보 확인 실패", f"데이터베이스 정보 확인 중 오류 발생:\n{str(e)}")


class FoodTypeDialog(QDialog):
    def __init__(self, parent=None, food_type=None):
        super().__init__(parent)
        
        self.food_type = food_type
        self.setWindowTitle("식품유형 정보" if food_type else "새 식품유형 등록")
        self.setMinimumWidth(400)
        
        self.initUI()
        
        # 기존 데이터 채우기
        if food_type:
            self.name_input.setText(food_type['type_name'])
            self.category_input.setText(food_type['category'] or "")
            self.sterilization_input.setText(food_type['sterilization'] or "")
            self.pasteurization_input.setText(food_type['pasteurization'] or "")
            self.appearance_input.setText(food_type['appearance'] or "")
            self.test_items_input.setText(food_type['test_items'] or "")
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("필수 입력")
        form_layout.addRow("* 식품유형:", self.name_input)
        
        self.category_input = QLineEdit()
        form_layout.addRow("카테고리:", self.category_input)
        
        self.sterilization_input = QLineEdit()
        form_layout.addRow("단서조항_1:", self.sterilization_input)
        
        self.pasteurization_input = QLineEdit()
        form_layout.addRow("단서조항_2:", self.pasteurization_input)
        
        self.appearance_input = QLineEdit()
        form_layout.addRow("성상:", self.appearance_input)
        
        self.test_items_input = QLineEdit()
        self.test_items_input.setPlaceholderText("쉼표로 구분하여 입력")
        form_layout.addRow("검사항목:", self.test_items_input)
        
        layout.addLayout(form_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()

        save_btn = QPushButton("저장")
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.save_food_type)

        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def save_food_type(self):
        """식품유형 정보 저장"""
        # 필수 입력 확인
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "식품유형은 필수 입력입니다.")
            return

        # 데이터 수집
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        sterilization = self.sterilization_input.text().strip()
        pasteurization = self.pasteurization_input.text().strip()
        appearance = self.appearance_input.text().strip()
        test_items = self.test_items_input.text().strip()

        # 저장 (신규 또는 수정)
        if self.food_type:  # 기존 식품유형 수정
            if ProductType.update(self.food_type['id'], name, category, sterilization, pasteurization, appearance, test_items):
                QMessageBox.information(self, "저장 완료", "식품유형 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "식품유형 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 식품유형 등록
            type_id = ProductType.create(name, category, sterilization, pasteurization, appearance, test_items)
            if type_id:
                QMessageBox.information(self, "등록 완료", "새 식품유형이 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "식품유형 등록 중 오류가 발생했습니다.")