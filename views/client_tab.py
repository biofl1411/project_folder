#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
업체 관리 탭
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
                          QFileDialog, QProgressDialog, QGridLayout, QScrollArea,
                          QGroupBox, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QCoreApplication, QSettings
import pandas as pd
import os

from models.clients import Client

class DisplaySettingsDialog(QDialog):
    """표시 설정 다이얼로그"""
    def __init__(self, parent=None, columns=None, visible_columns=None):
        super().__init__(parent)
        self.setWindowTitle("표시 설정")
        self.setMinimumWidth(300)
        self.columns = columns or []
        self.visible_columns = visible_columns or []
        self.checkboxes = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 설명 라벨
        layout.addWidget(QLabel("표시할 필드를 선택하세요:"))

        # 전체 선택/해제 버튼
        all_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("전체 해제")
        deselect_all_btn.clicked.connect(self.deselect_all)
        all_btn_layout.addWidget(select_all_btn)
        all_btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(all_btn_layout)

        # 컬럼 체크박스들
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for col_name, field in self.columns:
            checkbox = QCheckBox(col_name)
            checkbox.setChecked(field in self.visible_columns)
            self.checkboxes[field] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def select_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def get_visible_columns(self):
        return [field for field, checkbox in self.checkboxes.items() if checkbox.isChecked()]


class ClientTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("MyApp", "ClientTab")
        self.initUI()
        self.load_visible_columns()
        self.load_clients()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")

        button_layout = QHBoxLayout(button_frame)

        # 전체 선택 체크박스
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)

        new_client_btn = QPushButton("신규 업체 등록")
        new_client_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_client_btn.clicked.connect(self.create_new_client)

        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_client)

        delete_btn = QPushButton("선택 삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_client)

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

        # 컬럼 정의 (무료번호 삭제, 영업→영문 변경)
        self.all_columns = [
            ("선택", "select"),  # 체크박스 컬럼
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
            ("영문(업체명)", "eng_company_name"),
            ("영문(대표자)", "eng_ceo"),
            ("영문(우편번호)", "eng_zip_code"),
            ("영문(업체주소)", "eng_address"),
            ("핸드폰", "mobile"),
        ]

        # 기본 표시 컬럼 (처음에는 모두 표시)
        self.visible_columns = [col[1] for col in self.all_columns]

        self.setup_table()

    def load_visible_columns(self):
        """저장된 표시 설정 불러오기"""
        saved = self.settings.value("visible_columns", None)
        if saved:
            self.visible_columns = saved
        else:
            self.visible_columns = [col[1] for col in self.all_columns]

    def save_visible_columns(self):
        """표시 설정 저장"""
        self.settings.setValue("visible_columns", self.visible_columns)

    def setup_table(self):
        """테이블 설정"""
        # 표시할 컬럼만 필터링
        self.columns = [(name, field) for name, field in self.all_columns if field in self.visible_columns]

        self.client_table.setColumnCount(len(self.columns))
        self.client_table.setHorizontalHeaderLabels([col[0] for col in self.columns])

        # 열 너비 설정
        header = self.client_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # 선택 컬럼이 있으면 고정 너비
        for i, (name, field) in enumerate(self.columns):
            if field == "select":
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.client_table.setColumnWidth(i, 50)
            elif field == "name":
                self.client_table.setColumnWidth(i, 150)
            elif field in ["ceo", "contact_person", "sales_rep", "category"]:
                self.client_table.setColumnWidth(i, 80)
            elif field in ["business_no", "phone", "fax"]:
                self.client_table.setColumnWidth(i, 120)
            elif field == "email":
                self.client_table.setColumnWidth(i, 150)
            elif field in ["address", "eng_address"]:
                self.client_table.setColumnWidth(i, 200)
            elif field in ["zip_code", "eng_zip_code"]:
                self.client_table.setColumnWidth(i, 80)

        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_table.doubleClicked.connect(self.edit_client)

        # 기존 레이아웃에 테이블이 없으면 추가
        if self.client_table.parent() is None:
            self.layout().addWidget(self.client_table)

    def select_all_rows(self, checked):
        """모든 행 선택/해제"""
        try:
            if self.client_table.rowCount() == 0:
                return

            # 선택 컬럼 인덱스 찾기
            select_col = -1
            for i, (name, field) in enumerate(self.columns):
                if field == "select":
                    select_col = i
                    break

            if select_col == -1:
                return

            for row in range(self.client_table.rowCount()):
                checkbox_widget = self.client_table.cellWidget(row, select_col)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(checked)
        except Exception as e:
            print(f"전체 선택 중 오류 발생: {str(e)}")

    def show_display_settings(self):
        """표시 설정 다이얼로그 표시"""
        # 선택 컬럼 제외한 컬럼 목록
        display_columns = [(name, field) for name, field in self.all_columns if field != "select"]
        visible_without_select = [f for f in self.visible_columns if f != "select"]

        dialog = DisplaySettingsDialog(self, display_columns, visible_without_select)
        if dialog.exec_():
            new_visible = dialog.get_visible_columns()
            # 선택 컬럼은 항상 포함
            self.visible_columns = ["select"] + new_visible
            self.save_visible_columns()
            self.setup_table()
            self.load_clients()

    def load_clients(self):
        """업체 목록 로드"""
        clients = Client.get_all()

        self.client_table.setRowCount(len(clients) if clients else 0)

        # 선택 컬럼 인덱스 찾기
        select_col = -1
        for i, (name, field) in enumerate(self.columns):
            if field == "select":
                select_col = i
                break

        if clients:
            for row, client in enumerate(clients):
                for col, (header, field) in enumerate(self.columns):
                    if field == "select":
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

    def edit_client(self):
        """업체 정보 수정"""
        # 체크박스가 선택된 행 찾기
        selected_row = -1
        select_col = -1

        for i, (name, field) in enumerate(self.columns):
            if field == "select":
                select_col = i
                break

        if select_col != -1:
            for row in range(self.client_table.rowCount()):
                checkbox_widget = self.client_table.cellWidget(row, select_col)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_row = row
                        break

        # 체크박스로 선택된 행이 없으면 테이블 선택 확인
        if selected_row == -1:
            selected_items = self.client_table.selectedItems()
            if selected_items:
                selected_row = selected_items[0].row()

        if selected_row == -1:
            QMessageBox.warning(self, "선택 오류", "수정할 업체를 선택하세요.")
            return

        # 이름 컬럼 인덱스 찾기
        name_col = -1
        for i, (name, field) in enumerate(self.columns):
            if field == "name":
                name_col = i
                break

        if name_col == -1:
            QMessageBox.warning(self, "오류", "업체명 컬럼을 찾을 수 없습니다.")
            return

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
        """선택된 업체들 삭제"""
        # 선택 컬럼 인덱스 찾기
        select_col = -1
        name_col = -1
        for i, (name, field) in enumerate(self.columns):
            if field == "select":
                select_col = i
            if field == "name":
                name_col = i

        if select_col == -1 or name_col == -1:
            QMessageBox.warning(self, "오류", "테이블 구성 오류입니다.")
            return

        # 체크박스가 선택된 모든 행 찾기
        selected_rows = []
        for row in range(self.client_table.rowCount()):
            checkbox_widget = self.client_table.cellWidget(row, select_col)
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
            # 선택된 행의 역순으로 삭제 (인덱스 변화 방지)
            for row in sorted(selected_rows, reverse=True):
                client_name = self.client_table.item(row, name_col).text()

                clients = Client.search(client_name)
                if clients and Client.delete(clients[0]['id']):
                    deleted_count += 1

            self.load_clients()

            if deleted_count > 0:
                QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 업체가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "삭제 실패", "업체 삭제 중 오류가 발생했습니다.")

        # 전체 선택 체크박스 해제
        self.select_all_checkbox.setChecked(False)

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
                "영문(업체명)": "eng_company_name", "영문업체명": "eng_company_name",
                "영문(대표자)": "eng_ceo", "영문대표자": "eng_ceo",
                "영문(우편번호)": "eng_zip_code", "영문우편번호": "eng_zip_code",
                "영문(업체주소)": "eng_address", "영문업체주소": "eng_address",
                "핸드폰": "mobile",
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
                        client_data.get("zip_code"),
                        client_data.get("address"),
                        client_data.get("notes"),
                        client_data.get("eng_company_name"),
                        client_data.get("eng_ceo"),
                        client_data.get("eng_zip_code"),
                        client_data.get("eng_address"),
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
                        client_data.get("zip_code"),
                        client_data.get("address"),
                        client_data.get("notes"),
                        client_data.get("eng_company_name"),
                        client_data.get("eng_ceo"),
                        client_data.get("eng_zip_code"),
                        client_data.get("eng_address"),
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

            # 선택 컬럼 제외하고 내보내기
            export_columns = [(name, field) for name, field in self.columns if field != "select"]

            data = []
            for client in clients:
                row_data = {}
                for header, field in export_columns:
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

        basic_layout.addWidget(QLabel("핸드폰:"), 4, 2)
        self.mobile_input = QLineEdit()
        basic_layout.addWidget(self.mobile_input, 4, 3)

        # Row 5
        basic_layout.addWidget(QLabel("우편번호:"), 5, 0)
        self.zip_code_input = QLineEdit()
        basic_layout.addWidget(self.zip_code_input, 5, 1)

        # Row 6
        basic_layout.addWidget(QLabel("소재지:"), 6, 0)
        self.address_input = QLineEdit()
        basic_layout.addWidget(self.address_input, 6, 1, 1, 3)

        # Row 7
        basic_layout.addWidget(QLabel("메모:"), 7, 0)
        self.notes_input = QLineEdit()
        basic_layout.addWidget(self.notes_input, 7, 1, 1, 3)

        scroll_layout.addWidget(basic_group)

        # 영문 정보 그룹 (영업→영문으로 변경)
        eng_group = QGroupBox("영문 정보")
        eng_layout = QGridLayout(eng_group)

        eng_layout.addWidget(QLabel("영문(업체명):"), 0, 0)
        self.eng_company_name_input = QLineEdit()
        eng_layout.addWidget(self.eng_company_name_input, 0, 1)

        eng_layout.addWidget(QLabel("영문(대표자):"), 0, 2)
        self.eng_ceo_input = QLineEdit()
        eng_layout.addWidget(self.eng_ceo_input, 0, 3)

        eng_layout.addWidget(QLabel("영문(우편번호):"), 1, 0)
        self.eng_zip_code_input = QLineEdit()
        eng_layout.addWidget(self.eng_zip_code_input, 1, 1)

        eng_layout.addWidget(QLabel("영문(업체주소):"), 1, 2)
        self.eng_address_input = QLineEdit()
        eng_layout.addWidget(self.eng_address_input, 1, 3)

        scroll_layout.addWidget(eng_group)
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
        self.mobile_input.setText(client.get('mobile', '') or '')
        self.zip_code_input.setText(client.get('zip_code', '') or '')
        self.address_input.setText(client.get('address', '') or '')
        self.notes_input.setText(client.get('notes', '') or '')
        self.eng_company_name_input.setText(client.get('eng_company_name', '') or '')
        self.eng_ceo_input.setText(client.get('eng_ceo', '') or '')
        self.eng_zip_code_input.setText(client.get('eng_zip_code', '') or '')
        self.eng_address_input.setText(client.get('eng_address', '') or '')

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
        mobile = self.mobile_input.text().strip()
        zip_code = self.zip_code_input.text().strip()
        address = self.address_input.text().strip()
        notes = self.notes_input.text().strip()
        eng_company_name = self.eng_company_name_input.text().strip()
        eng_ceo = self.eng_ceo_input.text().strip()
        eng_zip_code = self.eng_zip_code_input.text().strip()
        eng_address = self.eng_address_input.text().strip()

        if self.client:  # 기존 업체 수정
            if Client.update(
                self.client['id'], name, ceo, business_no, category, phone, fax,
                contact_person, email, sales_rep, zip_code, address,
                notes, eng_company_name, eng_ceo, eng_zip_code, eng_address, mobile
            ):
                QMessageBox.information(self, "저장 완료", "업체 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "업체 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 업체 등록
            client_id = Client.create(
                name, ceo, business_no, category, phone, fax,
                contact_person, email, sales_rep, zip_code, address,
                notes, eng_company_name, eng_ceo, eng_zip_code, eng_address, mobile
            )
            if client_id:
                QMessageBox.information(self, "등록 완료", "새 업체가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "업체 등록 중 오류가 발생했습니다.")
