from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QFileDialog, QProgressDialog,
                          QDialog, QFormLayout, QLineEdit, QCheckBox)
from PyQt5.QtCore import Qt, QCoreApplication
import pandas as pd

from models.product_types import ProductType

class FoodTypeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_food_types()
    
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
        
        new_type_btn = QPushButton("새 식품유형 등록")
        new_type_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_type_btn.clicked.connect(self.create_new_food_type)
        
        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_food_type)
        
        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_food_type)
        
        import_btn = QPushButton("엑셀 가져오기")
        import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        import_btn.clicked.connect(self.import_from_excel)
        
        export_btn = QPushButton("엑셀 내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_to_excel)
        
        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addWidget(new_type_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # 2. 식품유형 목록 테이블
        self.food_type_table = QTableWidget()
        self.food_type_table.setColumnCount(7)
        self.food_type_table.setHorizontalHeaderLabels([
            "선택", "식품유형", "카테고리", "살균여부", "멸균여부", "성상", "생성일"
        ])
        
        # 체크박스 열의 너비 설정
        self.food_type_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.food_type_table.setColumnWidth(0, 50)
        
        # 나머지 열은 자동 조정
        for i in range(1, 7):
            self.food_type_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            
        self.food_type_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.food_type_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
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
        food_types = ProductType.get_all()
        
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
                self.food_type_table.setItem(row, 1, QTableWidgetItem(food_type['type_name']))
                self.food_type_table.setItem(row, 2, QTableWidgetItem(food_type['category'] or ""))
                self.food_type_table.setItem(row, 3, QTableWidgetItem(food_type['sterilization'] or ""))
                self.food_type_table.setItem(row, 4, QTableWidgetItem(food_type['pasteurization'] or ""))
                self.food_type_table.setItem(row, 5, QTableWidgetItem(food_type['appearance'] or ""))
                self.food_type_table.setItem(row, 6, QTableWidgetItem(food_type['created_at'] or ""))
    
    def create_new_food_type(self):
        """새 식품유형 등록"""
        dialog = FoodTypeDialog(self)
        if dialog.exec_():
            self.load_food_types()
    
    def edit_food_type(self):
        """식품유형 정보 수정"""
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
            QMessageBox.warning(self, "선택 오류", "수정할 식품유형을 선택하세요.")
            return
        
        # 선택된 행의 데이터 가져오기
        type_name = self.food_type_table.item(selected_row, 1).text()
        
        # 해당 식품유형 정보 가져오기
        food_type = ProductType.get_by_name(type_name)
        if not food_type:
            QMessageBox.warning(self, "데이터 오류", "선택한 식품유형 정보를 찾을 수 없습니다.")
            return
        
        # 수정 다이얼로그 표시
        dialog = FoodTypeDialog(self, food_type)
        if dialog.exec_():
            self.load_food_types()
    
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
                type_name = self.food_type_table.item(row, 1).text()
                
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
            
            # 필수 열 확인
            required_columns = ["식품유형"]
            for col in required_columns:
                if col not in df.columns:
                    QMessageBox.warning(self, "파일 오류", f"엑셀 파일에 '{col}' 열이 없습니다.")
                    return
            
            # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
            column_mapping = {
                "식품유형": "type_name",
                "카테고리": "category",
                "살균여부": "sterilization",
                "멸균여부": "pasteurization",
                "성상": "appearance",
                "검사항목": "test_items"
            }
            
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
                if pd.isna(row["식품유형"]) or str(row["식품유형"]).strip() == "":
                    skipped_count += 1
                    continue
                
                # 데이터 준비
                food_type_data = {}
                for excel_col, db_field in column_mapping.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        food_type_data[db_field] = str(row[excel_col]).strip()
                    else:
                        food_type_data[db_field] = ""
                
                # 이미 존재하는 식품유형인지 확인
                existing_type = ProductType.get_by_name(food_type_data["type_name"])
                
                if existing_type:
                    # 기존 식품유형 정보 업데이트
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
                data.append({
                    "식품유형": food_type["type_name"],
                    "카테고리": food_type["category"] or "",
                    "살균여부": food_type["sterilization"] or "",
                    "멸균여부": food_type["pasteurization"] or "",
                    "성상": food_type["appearance"] or "",
                    "검사항목": food_type["test_items"] or "",
                    "생성일": food_type["created_at"] or ""
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
        form_layout.addRow("살균여부:", self.sterilization_input)
        
        self.pasteurization_input = QLineEdit()
        form_layout.addRow("멸균여부:", self.pasteurization_input)
        
        self.appearance_input = QLineEdit()
        form_layout.addRow("성상:", self.appearance_input)
        
        self.test_items_input = QLineEdit()
        self.test_items_input.setPlaceholderText("쉼표로 구분하여 입력")
        form_layout.addRow("검사항목:", self.test_items_input)
        
        layout.addLayout(form_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_food_type)
        
        cancel_btn = QPushButton("취소")
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