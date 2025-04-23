from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QFileDialog, QProgressDialog,
                          QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, QCoreApplication
import pandas as pd

from models.fees import Fee

class FeeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_fees()
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        button_layout = QHBoxLayout(button_frame)
        
        new_fee_btn = QPushButton("새 수수료 등록")
        new_fee_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_fee_btn.clicked.connect(self.create_new_fee)
        
        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_fee)
        
        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_fee)
        
        # 일괄 선택 체크박스 추가
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)
        
        import_btn = QPushButton("엑셀 가져오기")
        import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        import_btn.clicked.connect(self.import_from_excel)
        
        export_btn = QPushButton("엑셀 내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_to_excel)
        
        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addWidget(new_fee_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # 2. 수수료 목록 테이블
        self.fee_table = QTableWidget()
        self.fee_table.setColumnCount(7)  # 정렬순서 열 추가로 7개 열로 증가
        self.fee_table.setHorizontalHeaderLabels([
            "선택", "검사항목", "식품 카테고리", "가격", "설명", "정렬순서", "생성일"
        ])
        # 체크박스 열의 너비 설정
        self.fee_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.fee_table.setColumnWidth(0, 50)
        # 정렬순서 열의 너비 설정
        self.fee_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.fee_table.setColumnWidth(5, 80)
        # 나머지 열은 자동 조정
        for i in [1, 2, 3, 4, 6]:
            self.fee_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            
        self.fee_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fee_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
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
        fees = Fee.get_all()
        
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
                
                # 나머지 데이터 설정
                self.fee_table.setItem(row, 1, QTableWidgetItem(fee['test_item']))
                self.fee_table.setItem(row, 2, QTableWidgetItem(fee['food_category'] or ""))
                price_item = QTableWidgetItem(f"{int(fee['price']):,}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.fee_table.setItem(row, 3, price_item)
                self.fee_table.setItem(row, 4, QTableWidgetItem(fee['description'] or ""))
                
                # 정렬순서 설정 - 기존 데이터에 없을 경우 기본값 사용
                # sqlite3.Row 객체는 get() 메서드가 없으므로 다른 방식으로 접근
                try:
                    display_order = fee['display_order']
                except (KeyError, IndexError):
                    display_order = row + 1  # 기본값으로 행 번호+1 사용
                
                order_item = QTableWidgetItem(str(display_order))
                order_item.setTextAlignment(Qt.AlignCenter)
                self.fee_table.setItem(row, 5, order_item)
                
                self.fee_table.setItem(row, 6, QTableWidgetItem(fee['created_at'] or ""))
    
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
        test_item = self.fee_table.item(selected_row, 1).text()
        
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
                test_item = self.fee_table.item(row, 1).text()
                
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
                "설명": "description",
                "정렬순서": "display_order"  # 정렬순서 필드 추가
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
                            # 정수로 변환 (소수점 제거)
                            fee_data[db_field] = int(float(row[excel_col]))
                        elif excel_col == "정렬순서":
                            # 정렬순서도 정수로 변환
                            fee_data[db_field] = int(float(row[excel_col]))
                        else:
                            fee_data[db_field] = str(row[excel_col]).strip()
                    else:
                        if excel_col == "가격":
                            fee_data[db_field] = 0
                        elif excel_col == "정렬순서":
                            fee_data[db_field] = i + 1  # 기본값으로 행 번호+1 사용
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
                        fee_data.get("description", ""),
                        fee_data.get("display_order", i + 1)  # 정렬순서 추가
                    ):
                        updated_count += 1
                else:
                    # 새 수수료 생성
                    if Fee.create(
                        fee_data["test_item"],
                        fee_data.get("food_category", ""),
                        fee_data.get("price", 0),
                        fee_data.get("description", ""),
                        fee_data.get("display_order", i + 1)  # 정렬순서 추가
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
                
                data.append({
                    "검사항목": fee_dict["test_item"],
                    "식품 카테고리": fee_dict["food_category"] or "",
                    "가격": fee_dict["price"],
                    "설명": fee_dict["description"] or "",
                    "정렬순서": fee_dict["display_order"],
                    "생성일": fee_dict["created_at"] or ""
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
            self.description_input.setText(fee['description'] or "")
            # 정렬순서 값 설정
            if 'display_order' in fee:
                self.order_input.setValue(fee['display_order'])
    
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
        
        self.description_input = QLineEdit()
        form_layout.addRow("설명:", self.description_input)
        
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
        save_btn.clicked.connect(self.save_fee)
        
        cancel_btn = QPushButton("취소")
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
        description = self.description_input.text().strip()
        display_order = self.order_input.value()  # 정렬순서 값 가져오기
        
        # 저장 (신규 또는 수정)
        if self.fee:  # 기존 수수료 수정
            if Fee.update(self.fee['id'], test_item, food_category, price, description, display_order):
                QMessageBox.information(self, "저장 완료", "수수료 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "수수료 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 수수료 등록
            fee_id = Fee.create(test_item, food_category, price, description, display_order)
            if fee_id:
                QMessageBox.information(self, "등록 완료", "새 수수료가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "수수료 등록 중 오류가 발생했습니다.")