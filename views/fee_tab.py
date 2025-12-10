from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QFileDialog, QProgressDialog,
                          QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
                          QComboBox)
from PyQt5.QtCore import Qt, QCoreApplication, QTimer
import pandas as pd

from models.fees import Fee
from utils.logger import log_message, log_error, log_exception

class FeeTab(QWidget):
    # 한글 초성 매핑
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_fees = []  # 전체 수수료 목록 저장
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder
        self.current_user = None  # 현재 로그인한 사용자

        # 버튼 참조 저장 (권한 체크용)
        self.new_fee_btn = None
        self.edit_btn = None
        self.delete_btn = None
        self.import_btn = None
        self.export_btn = None

        # 검색 디바운싱을 위한 타이머 (300ms 지연)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_fees)

        self.initUI()
        self.load_fees()

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
        if self.new_fee_btn:
            has_perm = User.has_permission(self.current_user, 'fee_create')
            self.new_fee_btn.setEnabled(has_perm)
            if not has_perm:
                self.new_fee_btn.setToolTip("권한이 없습니다")

        if self.edit_btn:
            has_perm = User.has_permission(self.current_user, 'fee_edit')
            self.edit_btn.setEnabled(has_perm)
            if not has_perm:
                self.edit_btn.setToolTip("권한이 없습니다")

        if self.delete_btn:
            has_perm = User.has_permission(self.current_user, 'fee_delete')
            self.delete_btn.setEnabled(has_perm)
            if not has_perm:
                self.delete_btn.setToolTip("권한이 없습니다")

        if self.import_btn:
            has_perm = User.has_permission(self.current_user, 'fee_import_excel')
            self.import_btn.setEnabled(has_perm)
            if not has_perm:
                self.import_btn.setToolTip("권한이 없습니다")

        if self.export_btn:
            has_perm = User.has_permission(self.current_user, 'fee_export_excel')
            self.export_btn.setEnabled(has_perm)
            if not has_perm:
                self.export_btn.setToolTip("권한이 없습니다")
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        button_layout = QHBoxLayout(button_frame)
        
        self.new_fee_btn = QPushButton("새 수수료 등록")
        self.new_fee_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        self.new_fee_btn.clicked.connect(self.create_new_fee)

        self.edit_btn = QPushButton("수정")
        self.edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        self.edit_btn.clicked.connect(self.edit_fee)

        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        self.delete_btn.clicked.connect(self.delete_fee)

        # 일괄 선택 체크박스 추가
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)

        self.import_btn = QPushButton("엑셀 가져오기")
        self.import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        self.import_btn.clicked.connect(self.import_from_excel)

        self.export_btn = QPushButton("엑셀 내보내기")
        self.export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        self.export_btn.clicked.connect(self.export_to_excel)

        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addWidget(self.new_fee_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
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
        self.search_field_combo.addItems(["전체", "검사항목", "식품 카테고리"])
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

        # 2. 수수료 목록 테이블
        self.fee_table = QTableWidget()
        self.fee_table.setColumnCount(7)  # 정렬순서 열 추가로 7개 열로 증가
        self.fee_table.setHorizontalHeaderLabels([
            "선택", "검사항목", "식품 카테고리", "가격", "검체 수량(g)", "정렬순서", "생성일"
        ])
        # 열 너비 조절 설정
        header = self.fee_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 사용자가 마우스로 조절 가능
        header.setStretchLastSection(True)  # 마지막 열이 남은 공간을 채움

        # 체크박스 열(0번) 고정
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.fee_table.setColumnWidth(0, 50)

        # 정렬순서 열(5번) 고정
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.fee_table.setColumnWidth(5, 80)

        # 각 열의 기본 너비 설정
        column_widths = {
            1: 150,   # 검사항목
            2: 150,   # 식품 카테고리
            3: 100,   # 가격
            4: 100,   # 검체 수량(g)
            6: 100,   # 생성일
        }
        for col, width in column_widths.items():
            self.fee_table.setColumnWidth(col, width)
            
        self.fee_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fee_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 헤더 클릭으로 정렬 기능 활성화
        self.fee_table.setSortingEnabled(True)
        self.fee_table.horizontalHeader().setSortIndicatorShown(True)
        self.fee_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        layout.addWidget(self.fee_table)
    
    def select_all_rows(self, checked):
        """모든 행 선택/해제"""
        try:
            # 행이 없는 경우 처리
            if self.fee_table.rowCount() == 0:
                return
                
            for row in range(self.fee_table.rowCount()):
                checkbox_widget = self.fee_table.cellWidget(row, 0)
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
    
    def load_fees(self):
        """수수료 목록 로드"""
        try:
            log_message('FeeTab', '수수료 목록 로드 시작')
            raw_fees = Fee.get_all() or []
            # sqlite3.Row를 딕셔너리로 변환하여 .get() 메서드 사용 가능하게 함
            self.all_fees = [dict(f) for f in raw_fees]
            self.display_fees(self.all_fees)
            log_message('FeeTab', f'수수료 {len(self.all_fees)}개 로드 완료')
        except Exception as e:
            log_exception('FeeTab', f'수수료 로드 중 오류: {str(e)}')

    def display_fees(self, fees):
        """수수료 목록을 테이블에 표시"""
        # UI 업데이트 일시 중지 (성능 최적화)
        self.fee_table.setUpdatesEnabled(False)
        try:
            self.fee_table.setRowCount(len(fees) if fees else 0)

            if fees:
                for row, fee in enumerate(fees):
                    # 체크박스 추가
                    checkbox = QCheckBox()
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    self.fee_table.setCellWidget(row, 0, checkbox_widget)

                    # 나머지 데이터 설정 (안전한 .get() 사용)
                    self.fee_table.setItem(row, 1, QTableWidgetItem(str(fee.get('test_item', '') or '')))
                    self.fee_table.setItem(row, 2, QTableWidgetItem(fee.get('food_category', '') or ""))

                    price = fee.get('price', 0) or 0
                    price_item = QTableWidgetItem(f"{int(price):,}")
                    price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.fee_table.setItem(row, 3, price_item)

                    # 검체 수량 표시
                    sample_qty = fee.get('sample_quantity', 0) or 0
                    sample_qty_item = QTableWidgetItem(str(sample_qty))
                    sample_qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.fee_table.setItem(row, 4, sample_qty_item)

                    # 정렬순서 설정 (0도 유효한 값으로 처리)
                    display_order = fee.get('display_order')
                    if display_order is None:
                        display_order = row + 1
                    order_item = QTableWidgetItem(str(display_order))
                    order_item.setTextAlignment(Qt.AlignCenter)
                    self.fee_table.setItem(row, 5, order_item)

                    # datetime 객체를 문자열로 변환
                    created_at = fee.get('created_at', '')
                    if created_at and not isinstance(created_at, str):
                        created_at = str(created_at)
                    self.fee_table.setItem(row, 6, QTableWidgetItem(created_at or ""))

            log_message('FeeTab', f'수수료 {len(fees) if fees else 0}개 표시 완료')
        except Exception as e:
            log_exception('FeeTab', f'수수료 표시 중 오류: {str(e)}')
        finally:
            # UI 업데이트 재개
            self.fee_table.setUpdatesEnabled(True)

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

    def filter_fees(self):
        """실시간 검색 필터링 (초성 검색 지원)"""
        try:
            search_text = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            if not search_text:
                self.display_fees(self.all_fees)
                return

            log_message('FeeTab', f'수수료 검색 시작: "{search_text}" (필드: {search_field})')

            filtered = []
            is_chosung = self.is_chosung_only(search_text)

            for fee in self.all_fees:
                test_item = fee.get('test_item', '') or ''
                food_category = fee.get('food_category', '') or ''

                match = False

                if search_field == "전체":
                    if is_chosung:
                        match = (self.match_chosung(test_item, search_text) or
                                 self.match_chosung(food_category, search_text))
                    else:
                        search_lower = search_text.lower()
                        match = (search_lower in test_item.lower() or
                                 search_lower in food_category.lower())
                elif search_field == "검사항목":
                    if is_chosung:
                        match = self.match_chosung(test_item, search_text)
                    else:
                        match = search_text.lower() in test_item.lower()
                elif search_field == "식품 카테고리":
                    if is_chosung:
                        match = self.match_chosung(food_category, search_text)
                    else:
                        match = search_text.lower() in food_category.lower()

                if match:
                    filtered.append(fee)

            log_message('FeeTab', f'수수료 검색 완료: {len(filtered)}개 결과')
            self.display_fees(filtered)
        except Exception as e:
            log_exception('FeeTab', f'수수료 검색 중 오류: {str(e)}')

    def reset_search(self):
        """검색 초기화"""
        self.search_input.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.display_fees(self.all_fees)

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
        self.fee_table.sortItems(logical_index, self.current_sort_order)
    
    def create_new_fee(self):
        """새 수수료 등록"""
        dialog = FeeDialog(self)
        if dialog.exec_():
            self.load_fees()
    
    def edit_fee(self):
        """수수료 정보 수정"""
        # 체크박스가 선택된 행 찾기
        selected_row = -1
        for row in range(self.fee_table.rowCount()):
            checkbox_widget = self.fee_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_row = row
                    break
        
        if selected_row == -1:
            QMessageBox.warning(self, "선택 오류", "수정할 수수료를 선택하세요.")
            return

        # 선택된 행의 데이터 가져오기
        test_item_cell = self.fee_table.item(selected_row, 1)
        if not test_item_cell:
            QMessageBox.warning(self, "데이터 오류", "검사항목을 찾을 수 없습니다.")
            return
        test_item = test_item_cell.text()
        
        # 해당 수수료 정보 가져오기
        fee = Fee.get_by_item(test_item)
        if not fee:
            QMessageBox.warning(self, "데이터 오류", "선택한 수수료 정보를 찾을 수 없습니다.")
            return
        
        # 정렬순서 값 가져오기
        order_item = self.fee_table.item(selected_row, 5)
        if order_item and order_item.text():
            try:
                # 딕셔너리로 변환하여 display_order 추가
                fee_dict = dict(fee)
                fee_dict['display_order'] = int(order_item.text())
                fee = fee_dict
            except ValueError:
                fee_dict = dict(fee)
                fee_dict['display_order'] = selected_row + 1
                fee = fee_dict
        else:
            fee_dict = dict(fee)
            fee_dict['display_order'] = selected_row + 1
            fee = fee_dict
        
        # 수정 다이얼로그 표시
        dialog = FeeDialog(self, fee)
        if dialog.exec_():
            self.load_fees()
    
    def delete_fee(self):
        """수수료 삭제"""
        # 체크박스가 선택된 모든 행 찾기
        selected_rows = []
        for row in range(self.fee_table.rowCount()):
            checkbox_widget = self.fee_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "삭제할 수수료를 선택하세요.")
            return
        
        # 확인 메시지 표시
        count = len(selected_rows)
        reply = QMessageBox.question(
            self, "수수료 삭제", 
            f"선택한 {count}개의 수수료를 정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            # 선택된 행의 역순으로 삭제 (인덱스 변화 방지)
            for row in sorted(selected_rows, reverse=True):
                test_item_cell = self.fee_table.item(row, 1)
                if not test_item_cell:
                    continue
                test_item = test_item_cell.text()

                # 해당 수수료 정보 가져오기
                fee = Fee.get_by_item(test_item)
                if fee and Fee.delete(fee['id']):
                    self.fee_table.removeRow(row)
                    deleted_count += 1
            
            # 삭제 결과 메시지
            if deleted_count > 0:
                QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 수수료가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "삭제 실패", "수수료 삭제 중 오류가 발생했습니다.")
    
    def import_from_excel(self):
        """엑셀 파일에서 수수료 정보 가져오기"""
        # 파일 선택 대화상자 표시
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 필수 열 확인
            required_columns = ["검사항목", "가격"]
            for col in required_columns:
                if col not in df.columns:
                    QMessageBox.warning(self, "파일 오류", f"엑셀 파일에 '{col}' 열이 없습니다.")
                    return
            
            # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
            column_mapping = {
                "검사항목": "test_item",
                "식품 카테고리": "food_category",
                "가격": "price",
                "검체 수량(g)": "sample_quantity",
                "정렬순서": "display_order"
            }
            
            # 진행 상황 대화상자 표시
            progress = QProgressDialog("수수료 정보 가져오는 중...", "취소", 0, len(df), self)
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
                if pd.isna(row["검사항목"]) or str(row["검사항목"]).strip() == "" or pd.isna(row["가격"]):
                    skipped_count += 1
                    continue
                
                # 데이터 준비
                fee_data = {}
                for excel_col, db_field in column_mapping.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        if excel_col == "가격":
                            fee_data[db_field] = int(float(row[excel_col]))
                        elif excel_col == "정렬순서":
                            fee_data[db_field] = int(float(row[excel_col]))
                        elif excel_col == "검체 수량(g)":
                            fee_data[db_field] = int(float(row[excel_col]))
                        else:
                            fee_data[db_field] = str(row[excel_col]).strip()
                    else:
                        if excel_col == "가격":
                            fee_data[db_field] = 0
                        elif excel_col == "정렬순서":
                            fee_data[db_field] = i + 1
                        elif excel_col == "검체 수량(g)":
                            fee_data[db_field] = 0
                        else:
                            fee_data[db_field] = ""
                
                # 이미 존재하는 수수료인지 확인
                existing_fee = Fee.get_by_item(fee_data["test_item"])
                
                if existing_fee:
                    # 기존 수수료 정보 업데이트
                    if Fee.update(
                        existing_fee["id"],
                        fee_data["test_item"],
                        fee_data.get("food_category", ""),
                        fee_data.get("price", 0),
                        "",  # description
                        fee_data.get("display_order", i + 1),
                        fee_data.get("sample_quantity", 0)
                    ):
                        updated_count += 1
                else:
                    # 새 수수료 생성
                    if Fee.create(
                        fee_data["test_item"],
                        fee_data.get("food_category", ""),
                        fee_data.get("price", 0),
                        "",  # description
                        fee_data.get("display_order", i + 1),
                        fee_data.get("sample_quantity", 0)
                    ):
                        imported_count += 1
            
            # 진행 상황 대화상자 종료
            progress.setValue(len(df))
            
            # 테이블 새로고침
            self.load_fees()
            
            # 결과 메시지 표시
            QMessageBox.information(
                self, "가져오기 완료",
                f"수수료 정보 가져오기가 완료되었습니다.\n"
                f"- 새로 추가된 항목: {imported_count}개\n"
                f"- 업데이트된 항목: {updated_count}개\n"
                f"- 건너뛴 항목: {skipped_count}개"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일을 처리하는 중 오류가 발생했습니다.\n{str(e)}")
    
    def export_to_excel(self):
        """수수료 정보를 엑셀 파일로 내보내기"""
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
            # DB에서 모든 수수료 정보 가져오기
            fees = Fee.get_all()
            
            if not fees:
                QMessageBox.warning(self, "데이터 없음", "내보낼 수수료 정보가 없습니다.")
                return
            
            # 데이터 변환
            data = []
            for i, fee in enumerate(fees):
                # sqlite3.Row 객체를 딕셔너리로 변환
                fee_dict = dict(fee)
                
                # 정렬순서 필드가 없으면 기본값 추가
                if 'display_order' not in fee_dict:
                    fee_dict['display_order'] = i + 1
                
                # datetime 객체를 문자열로 변환
                created_at_val = fee_dict["created_at"]
                if created_at_val and not isinstance(created_at_val, str):
                    created_at_val = str(created_at_val)
                data.append({
                    "검사항목": fee_dict["test_item"],
                    "식품 카테고리": fee_dict["food_category"] or "",
                    "가격": fee_dict["price"],
                    "검체 수량(g)": fee_dict.get("sample_quantity", "") or "",  # 수정: description -> sample_quantity
                    "정렬순서": fee_dict["display_order"],
                    "생성일": created_at_val or ""
                })
            
            # DataFrame 생성 및 엑셀 파일로 저장
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            # 성공 메시지
            QMessageBox.information(
                self, "내보내기 완료", 
                f"수수료 정보가 엑셀 파일로 저장되었습니다.\n파일 위치: {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일로 내보내는 중 오류가 발생했습니다.\n{str(e)}")
            
class FeeDialog(QDialog):
    def __init__(self, parent=None, fee=None):
        super().__init__(parent)
        
        self.fee = fee
        self.setWindowTitle("수수료 정보" if fee else "새 수수료 등록")
        self.setMinimumWidth(400)
        
        self.initUI()
        
        # 기존 데이터 채우기
        if fee:
            self.test_item_input.setText(fee['test_item'])
            self.food_category_input.setText(fee['food_category'] or "")
            # 소수점 값을 정수로 변환하여 설정
            self.price_input.setValue(int(fee['price']))
            # 검체 수량 설정
            try:
                sample_qty = fee['sample_quantity'] or 0
                self.sample_quantity_input.setValue(int(sample_qty))
            except (KeyError, IndexError, TypeError):
                self.sample_quantity_input.setValue(0)
            # 정렬순서 값 설정
            try:
                self.order_input.setValue(fee['display_order'] or 100)
            except (KeyError, IndexError):
                self.order_input.setValue(100)
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        self.test_item_input = QLineEdit()
        self.test_item_input.setPlaceholderText("필수 입력")
        form_layout.addRow("* 검사항목:", self.test_item_input)
        
        self.food_category_input = QLineEdit()
        form_layout.addRow("식품 카테고리:", self.food_category_input)
        
        # 가격 입력 (정수만 입력 가능)
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 1000000)
        self.price_input.setValue(0)
        self.price_input.setSingleStep(1000)
        self.price_input.setPrefix("₩ ")
        self.price_input.setSuffix(" 원")
        self.price_input.setGroupSeparatorShown(True)
        form_layout.addRow("* 가격:", self.price_input)
        
        self.sample_quantity_input = QSpinBox()
        self.sample_quantity_input.setRange(0, 10000)
        self.sample_quantity_input.setValue(0)
        self.sample_quantity_input.setSuffix(" g")
        form_layout.addRow("검체 수량(g):", self.sample_quantity_input)
        
        # 정렬순서 입력 추가
        self.order_input = QSpinBox()
        self.order_input.setRange(1, 9999)
        self.order_input.setValue(100)  # 기본값 100
        self.order_input.setSingleStep(10)
        form_layout.addRow("정렬순서:", self.order_input)
        
        layout.addLayout(form_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()

        save_btn = QPushButton("저장")
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.save_fee)

        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
    
    def save_fee(self):
        """수수료 정보 저장"""
        # 필수 입력 확인
        if not self.test_item_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "검사항목은 필수 입력입니다.")
            return
        
        if self.price_input.value() <= 0:
            QMessageBox.warning(self, "입력 오류", "가격은 0보다 커야 합니다.")
            return
        
        # 데이터 수집
        test_item = self.test_item_input.text().strip()
        food_category = self.food_category_input.text().strip()
        price = self.price_input.value()
        sample_quantity = self.sample_quantity_input.value()
        display_order = self.order_input.value()

        # 저장 (신규 또는 수정)
        if self.fee:  # 기존 수수료 수정
            if Fee.update(self.fee['id'], test_item, food_category, price, "", display_order, sample_quantity):
                QMessageBox.information(self, "저장 완료", "수수료 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "수수료 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 수수료 등록
            fee_id = Fee.create(test_item, food_category, price, "", display_order, sample_quantity)
            if fee_id:
                QMessageBox.information(self, "등록 완료", "새 수수료가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "수수료 등록 중 오류가 발생했습니다.")