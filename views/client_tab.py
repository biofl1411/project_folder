#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
업체 관리 탭
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
                          QFileDialog, QProgressDialog, QGridLayout, QScrollArea,
                          QGroupBox, QComboBox, QCheckBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QCoreApplication, QSettings
import pandas as pd
import os

from models.clients import Client

class ClientTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_clients()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")

        button_layout = QHBoxLayout(button_frame)

        # 일괄 선택 체크박스 추가
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)

        new_client_btn = QPushButton("신규 업체 등록")
        new_client_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_client_btn.clicked.connect(self.create_new_client)

        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_client)

        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_client)

        # 표시설정 버튼 추가
        display_settings_btn = QPushButton("표시설정")
        display_settings_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogListView))
        display_settings_btn.clicked.connect(self.show_display_settings)

        import_btn = QPushButton("엑셀 가져오기")
        import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        import_btn.clicked.connect(self.import_from_excel)

        export_btn = QPushButton("엑셀 내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_to_excel)

        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addWidget(new_client_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(display_settings_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()

        layout.addWidget(button_frame)

        # 2. 업체 목록 테이블
        self.client_table = QTableWidget()

        # 컬럼 정의 (선택 열 추가, 무료번호 삭제, 필드명 변경)
        self.all_columns = [
            ("선택", None),  # 체크박스 열
            ("고객/회사명", "name"),
            ("대표자", "ceo"),
            ("사업자번호", "business_no"),
            ("분류", "category"),
            ("전화번호", "phone"),
            ("팩스번호", "fax"),
            ("담당자", "contact_person"),
            ("EMAIL", "email"),
            ("영업담당", "sales_rep"),
            ("우편번호", "zip_code"),
            ("소재지", "address"),
            ("메모", "notes"),
            ("영문(업체명)", "sales_business"),
            ("영문(대표자)", "sales_phone"),
            ("영문(우편번호)", "sales_mobile"),
            ("영문(업체주소)", "sales_address"),
        ]

        # 표시 여부 설정 로드 (QSettings 사용)
        self.settings = QSettings("MyApp", "ClientTab")
        self.visible_columns = self.load_visible_columns()

        self.setup_table()

    def load_visible_columns(self):
        """저장된 컬럼 표시 설정 로드"""
        saved = self.settings.value("visible_columns", None)
        if saved:
            return saved
        # 기본값: 모든 컬럼 표시
        return [col[0] for col in self.all_columns]

    def save_visible_columns(self):
        """컬럼 표시 설정 저장"""
        self.settings.setValue("visible_columns", self.visible_columns)

    def setup_table(self):
        """테이블 컬럼 설정"""
        # 표시할 컬럼만 필터링 (선택 열은 항상 포함)
        self.columns = []
        for col in self.all_columns:
            if col[0] == "선택" or col[0] in self.visible_columns:
                self.columns.append(col)

        self.client_table.setColumnCount(len(self.columns))
        self.client_table.setHorizontalHeaderLabels([col[0] for col in self.columns])

        # 열 너비 설정
        header = self.client_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # 체크박스 열의 너비 설정
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.client_table.setColumnWidth(0, 50)

        # 나머지 열 기본 너비 설정
        column_widths = {
            "고객/회사명": 150, "대표자": 80, "사업자번호": 120, "분류": 80,
            "전화번호": 120, "팩스번호": 120, "담당자": 80, "EMAIL": 150,
            "영업담당": 80, "우편번호": 80, "소재지": 200, "메모": 150,
            "영문(업체명)": 120, "영문(대표자)": 100, "영문(우편번호)": 100, "영문(업체주소)": 200,
        }

        for i, (col_name, _) in enumerate(self.columns):
            if col_name in column_widths:
                self.client_table.setColumnWidth(i, column_widths[col_name])

        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_table.doubleClicked.connect(self.edit_client)

        layout = self.layout()
        # 기존 테이블이 레이아웃에 있으면 유지
        if layout.indexOf(self.client_table) == -1:
            layout.addWidget(self.client_table)

    def select_all_rows(self, checked):
        """모든 행 선택/해제"""
        try:
            if self.client_table.rowCount() == 0:
                return

            for row in range(self.client_table.rowCount()):
                checkbox_widget = self.client_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(checked)
        except Exception as e:
            print(f"전체 선택 중 오류 발생: {str(e)}")

    def show_display_settings(self):
        """표시설정 다이얼로그 표시"""
        dialog = DisplaySettingsDialog(self, self.all_columns, self.visible_columns)
        if dialog.exec_():
            self.visible_columns = dialog.get_selected_columns()
            self.save_visible_columns()
            self.setup_table()
            self.load_clients()

    def load_clients(self):
        """업체 목록 로드"""
        clients = Client.get_all()

        self.client_table.setRowCount(len(clients) if clients else 0)

        if clients:
            for row, client in enumerate(clients):
                for col, (header, field) in enumerate(self.columns):
                    if header == "선택":
                        # 체크박스 추가
                        checkbox = QCheckBox()
                        checkbox_widget = QWidget()
                        checkbox_layout = QHBoxLayout(checkbox_widget)
                        checkbox_layout.addWidget(checkbox)
                        checkbox_layout.setAlignment(Qt.AlignCenter)
                        checkbox_layout.setContentsMargins(0, 0, 0, 0)
                        self.client_table.setCellWidget(row, col, checkbox_widget)
                    else:
                        value = client.get(field, '') or ''
                        self.client_table.setItem(row, col, QTableWidgetItem(str(value)))

    def create_new_client(self):
        """신규 업체 등록"""
        dialog = ClientDialog(self)
        if dialog.exec_():
            self.load_clients()

    def get_name_column_index(self):
        """고객/회사명 컬럼의 인덱스 반환"""
        for i, (header, _) in enumerate(self.columns):
            if header == "고객/회사명":
                return i
        return 1  # 기본값

    def edit_client(self):
        """업체 정보 수정"""
        # 체크박스가 선택된 행 찾기
        selected_row = -1
        for row in range(self.client_table.rowCount()):
            checkbox_widget = self.client_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_row = row
                    break

        if selected_row == -1:
            QMessageBox.warning(self, "선택 오류", "수정할 업체를 선택하세요.")
            return

        # 고객/회사명 컬럼 인덱스 찾기
        name_col = self.get_name_column_index()
        client_name = self.client_table.item(selected_row, name_col).text()

        clients = Client.search(client_name)
        if not clients:
            QMessageBox.warning(self, "데이터 오류", "선택한 업체 정보를 찾을 수 없습니다.")
            return

        client = clients[0]

        dialog = ClientDialog(self, client)
        if dialog.exec_():
            self.load_clients()

    def delete_client(self):
        """업체 삭제"""
        # 체크박스가 선택된 모든 행 찾기
        selected_rows = []
        for row in range(self.client_table.rowCount()):
            checkbox_widget = self.client_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "삭제할 업체를 선택하세요.")
            return

        # 확인 메시지 표시
        count = len(selected_rows)
        reply = QMessageBox.question(
            self, "업체 삭제",
            f"선택한 {count}개의 업체를 정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            name_col = self.get_name_column_index()

            # 선택된 행의 역순으로 삭제 (인덱스 변화 방지)
            for row in sorted(selected_rows, reverse=True):
                client_name = self.client_table.item(row, name_col).text()

                clients = Client.search(client_name)
                if clients and Client.delete(clients[0]['id']):
                    deleted_count += 1

            # 삭제 결과 메시지
            if deleted_count > 0:
                self.load_clients()
                QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 업체가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "삭제 실패", "업체 삭제 중 오류가 발생했습니다.")

    def import_from_excel(self):
        """엑셀 파일에서 업체 정보 가져오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)

            # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
            column_mapping = {
                "고객/회사명": "name", "업체명": "name",
                "대표자": "ceo",
                "사업자번호": "business_no", "사업자": "business_no",
                "분류": "category",
                "전화번호": "phone",
                "팩스번호": "fax", "팩스": "fax",
                "담당자": "contact_person",
                "EMAIL": "email", "이메일": "email",
                "영업담당": "sales_rep", "영업담당자": "sales_rep",
                "우편번호": "zip_code",
                "소재지": "address", "업체주소": "address", "주소": "address",
                "메모": "notes",
                "영문(업체명)": "sales_business", "(영업)업무": "sales_business", "영업업무": "sales_business",
                "영문(대표자)": "sales_phone", "(영업)대표번호": "sales_phone", "영업대표번호": "sales_phone",
                "영문(우편번호)": "sales_mobile", "(영업)핸드폰": "sales_mobile", "영업핸드폰": "sales_mobile", "핸드폰": "mobile",
                "영문(업체주소)": "sales_address", "(영업)업체주소": "sales_address", "영업업체주소": "sales_address",
            }

            # 필수 열 확인
            name_col = None
            for col in ["고객/회사명", "업체명", "name"]:
                if col in df.columns:
                    name_col = col
                    break

            if not name_col:
                QMessageBox.warning(self, "파일 오류", "엑셀 파일에 '고객/회사명' 또는 '업체명' 열이 없습니다.")
                return

            progress = QProgressDialog("업체 정보 가져오는 중...", "취소", 0, len(df), self)
            progress.setWindowTitle("데이터 가져오기")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            imported_count = 0
            updated_count = 0
            skipped_count = 0

            for i, row in df.iterrows():
                progress.setValue(i)
                QCoreApplication.processEvents()

                if progress.wasCanceled():
                    break

                if pd.isna(row[name_col]) or str(row[name_col]).strip() == "":
                    skipped_count += 1
                    continue

                client_data = {}
                for excel_col, db_field in column_mapping.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        client_data[db_field] = str(row[excel_col]).strip()

                if 'name' not in client_data:
                    client_data['name'] = str(row[name_col]).strip()

                existing_clients = Client.search(client_data["name"])

                if existing_clients:
                    client = existing_clients[0]
                    if Client.update(
                        client["id"],
                        client_data.get("name"),
                        client_data.get("ceo"),
                        client_data.get("business_no"),
                        client_data.get("category"),
                        client_data.get("phone"),
                        client_data.get("fax"),
                        client_data.get("contact_person"),
                        client_data.get("email"),
                        client_data.get("sales_rep"),
                        client_data.get("toll_free"),
                        client_data.get("zip_code"),
                        client_data.get("address"),
                        client_data.get("notes"),
                        client_data.get("sales_business"),
                        client_data.get("sales_phone"),
                        client_data.get("sales_mobile"),
                        client_data.get("sales_address"),
                        client_data.get("mobile")
                    ):
                        updated_count += 1
                else:
                    if Client.create(
                        client_data.get("name"),
                        client_data.get("ceo"),
                        client_data.get("business_no"),
                        client_data.get("category"),
                        client_data.get("phone"),
                        client_data.get("fax"),
                        client_data.get("contact_person"),
                        client_data.get("email"),
                        client_data.get("sales_rep"),
                        client_data.get("toll_free"),
                        client_data.get("zip_code"),
                        client_data.get("address"),
                        client_data.get("notes"),
                        client_data.get("sales_business"),
                        client_data.get("sales_phone"),
                        client_data.get("sales_mobile"),
                        client_data.get("sales_address"),
                        client_data.get("mobile")
                    ):
                        imported_count += 1

            progress.setValue(len(df))
            self.load_clients()

            QMessageBox.information(
                self, "가져오기 완료",
                f"업체 정보 가져오기가 완료되었습니다.\n"
                f"- 새로 추가된 업체: {imported_count}개\n"
                f"- 업데이트된 업체: {updated_count}개\n"
                f"- 건너뛴 항목: {skipped_count}개"
            )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일을 처리하는 중 오류가 발생했습니다.\n{str(e)}")

    def export_to_excel(self):
        """업체 정보를 엑셀 파일로 내보내기"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", "", "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'

        try:
            clients = Client.get_all()

            if not clients:
                QMessageBox.warning(self, "데이터 없음", "내보낼 업체 정보가 없습니다.")
                return

            data = []
            for client in clients:
                row_data = {}
                for header, field in self.columns:
                    # "선택" 컬럼은 제외
                    if header == "선택":
                        continue
                    row_data[header] = client.get(field, '') or ''
                data.append(row_data)

            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)

            QMessageBox.information(
                self, "내보내기 완료",
                f"업체 정보가 엑셀 파일로 저장되었습니다.\n파일 위치: {file_path}"
            )

            if os.path.exists(file_path):
                import subprocess
                os.startfile(file_path) if os.name == 'nt' else subprocess.call(('xdg-open', file_path))

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일로 내보내는 중 오류가 발생했습니다.\n{str(e)}")


class ClientDialog(QDialog):
    def __init__(self, parent=None, client=None):
        super().__init__(parent)

        self.client = client
        self.setWindowTitle("업체 정보 수정" if client else "신규 업체 등록")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.initUI()

        if client:
            self.load_client_data(client)

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_layout = QGridLayout(basic_group)

        # Row 0
        basic_layout.addWidget(QLabel("* 고객/회사명:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("필수 입력")
        basic_layout.addWidget(self.name_input, 0, 1)

        basic_layout.addWidget(QLabel("대표자:"), 0, 2)
        self.ceo_input = QLineEdit()
        basic_layout.addWidget(self.ceo_input, 0, 3)

        # Row 1
        basic_layout.addWidget(QLabel("사업자번호:"), 1, 0)
        self.business_no_input = QLineEdit()
        self.business_no_input.setPlaceholderText("000-00-00000")
        basic_layout.addWidget(self.business_no_input, 1, 1)

        basic_layout.addWidget(QLabel("분류:"), 1, 2)
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(["", "식품", "제조", "유통", "기타"])
        basic_layout.addWidget(self.category_input, 1, 3)

        # Row 2
        basic_layout.addWidget(QLabel("전화번호:"), 2, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("02-0000-0000")
        basic_layout.addWidget(self.phone_input, 2, 1)

        basic_layout.addWidget(QLabel("팩스번호:"), 2, 2)
        self.fax_input = QLineEdit()
        basic_layout.addWidget(self.fax_input, 2, 3)

        # Row 3
        basic_layout.addWidget(QLabel("담당자:"), 3, 0)
        self.contact_input = QLineEdit()
        basic_layout.addWidget(self.contact_input, 3, 1)

        basic_layout.addWidget(QLabel("EMAIL:"), 3, 2)
        self.email_input = QLineEdit()
        basic_layout.addWidget(self.email_input, 3, 3)

        # Row 4
        basic_layout.addWidget(QLabel("영업담당:"), 4, 0)
        self.sales_rep_input = QLineEdit()
        basic_layout.addWidget(self.sales_rep_input, 4, 1)

        basic_layout.addWidget(QLabel("우편번호:"), 4, 2)
        self.zip_code_input = QLineEdit()
        basic_layout.addWidget(self.zip_code_input, 4, 3)

        # Row 5
        basic_layout.addWidget(QLabel("소재지:"), 5, 0)
        self.address_input = QLineEdit()
        basic_layout.addWidget(self.address_input, 5, 1, 1, 3)

        # Row 6
        basic_layout.addWidget(QLabel("메모:"), 6, 0)
        self.notes_input = QLineEdit()
        basic_layout.addWidget(self.notes_input, 6, 1, 1, 3)

        scroll_layout.addWidget(basic_group)

        # 영문 정보 그룹
        sales_group = QGroupBox("영문 정보")
        sales_layout = QGridLayout(sales_group)

        sales_layout.addWidget(QLabel("영문(업체명):"), 0, 0)
        self.sales_business_input = QLineEdit()
        sales_layout.addWidget(self.sales_business_input, 0, 1)

        sales_layout.addWidget(QLabel("영문(대표자):"), 0, 2)
        self.sales_phone_input = QLineEdit()
        sales_layout.addWidget(self.sales_phone_input, 0, 3)

        sales_layout.addWidget(QLabel("영문(우편번호):"), 1, 0)
        self.sales_mobile_input = QLineEdit()
        sales_layout.addWidget(self.sales_mobile_input, 1, 1)

        sales_layout.addWidget(QLabel("영문(업체주소):"), 1, 2)
        self.sales_address_input = QLineEdit()
        sales_layout.addWidget(self.sales_address_input, 1, 3)

        scroll_layout.addWidget(sales_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 버튼 영역
        button_layout = QHBoxLayout()

        save_btn = QPushButton("저장")
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.save_client)

        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def load_client_data(self, client):
        """기존 데이터 채우기"""
        self.name_input.setText(client.get('name', '') or '')
        self.ceo_input.setText(client.get('ceo', '') or '')
        self.business_no_input.setText(client.get('business_no', '') or '')
        self.category_input.setCurrentText(client.get('category', '') or '')
        self.phone_input.setText(client.get('phone', '') or '')
        self.fax_input.setText(client.get('fax', '') or '')
        self.contact_input.setText(client.get('contact_person', '') or '')
        self.email_input.setText(client.get('email', '') or '')
        self.sales_rep_input.setText(client.get('sales_rep', '') or '')
        self.zip_code_input.setText(client.get('zip_code', '') or '')
        self.address_input.setText(client.get('address', '') or '')
        self.notes_input.setText(client.get('notes', '') or '')
        self.sales_business_input.setText(client.get('sales_business', '') or '')
        self.sales_phone_input.setText(client.get('sales_phone', '') or '')
        self.sales_mobile_input.setText(client.get('sales_mobile', '') or '')
        self.sales_address_input.setText(client.get('sales_address', '') or '')

    def save_client(self):
        """업체 정보 저장"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "고객/회사명은 필수 입력입니다.")
            return

        # 데이터 수집
        name = self.name_input.text().strip()
        ceo = self.ceo_input.text().strip()
        business_no = self.business_no_input.text().strip()
        category = self.category_input.currentText().strip()
        phone = self.phone_input.text().strip()
        fax = self.fax_input.text().strip()
        contact_person = self.contact_input.text().strip()
        email = self.email_input.text().strip()
        sales_rep = self.sales_rep_input.text().strip()
        zip_code = self.zip_code_input.text().strip()
        address = self.address_input.text().strip()
        notes = self.notes_input.text().strip()
        sales_business = self.sales_business_input.text().strip()
        sales_phone = self.sales_phone_input.text().strip()
        sales_mobile = self.sales_mobile_input.text().strip()
        sales_address = self.sales_address_input.text().strip()

        if self.client:  # 기존 업체 수정
            if Client.update(
                self.client['id'], name, ceo, business_no, category, phone, fax,
                contact_person, email, sales_rep, None, zip_code, address,
                notes, sales_business, sales_phone, sales_mobile, sales_address
            ):
                QMessageBox.information(self, "저장 완료", "업체 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "업체 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 업체 등록
            client_id = Client.create(
                name, ceo, business_no, category, phone, fax,
                contact_person, email, sales_rep, None, zip_code, address,
                notes, sales_business, sales_phone, sales_mobile, sales_address
            )
            if client_id:
                QMessageBox.information(self, "등록 완료", "새 업체가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "업체 등록 중 오류가 발생했습니다.")


class DisplaySettingsDialog(QDialog):
    """표시할 컬럼을 선택하는 다이얼로그"""
    def __init__(self, parent=None, all_columns=None, visible_columns=None):
        super().__init__(parent)
        self.all_columns = all_columns or []
        self.visible_columns = visible_columns or []

        self.setWindowTitle("표시설정")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

        self.initUI()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 안내 라벨
        info_label = QLabel("표시할 컬럼을 선택하세요:")
        layout.addWidget(info_label)

        # 전체 선택/해제 체크박스
        self.select_all_cb = QCheckBox("전체 선택")
        self.select_all_cb.clicked.connect(self.toggle_all)
        layout.addWidget(self.select_all_cb)

        # 컬럼 목록 (체크박스 리스트)
        self.list_widget = QListWidget()
        for col_name, _ in self.all_columns:
            # "선택" 컬럼은 표시 안 함 (항상 표시)
            if col_name == "선택":
                continue
            item = QListWidgetItem(col_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if col_name in self.visible_columns:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # 버튼 영역
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # 전체 선택 체크박스 상태 업데이트
        self.update_select_all_state()

    def toggle_all(self, checked):
        """전체 선택/해제"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def update_select_all_state(self):
        """전체 선택 체크박스 상태 업데이트"""
        all_checked = True
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() != Qt.Checked:
                all_checked = False
                break
        self.select_all_cb.setChecked(all_checked)

    def get_selected_columns(self):
        """선택된 컬럼 목록 반환"""
        selected = ["선택"]  # "선택" 컬럼은 항상 포함
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected
