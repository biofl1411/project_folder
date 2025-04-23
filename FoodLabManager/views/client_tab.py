#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
업체 관리 탭
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                          QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                          QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
                          QFileDialog, QProgressDialog)
from PyQt5.QtCore import Qt, QCoreApplication
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
        
        new_client_btn = QPushButton("신규 업체 등록")
        new_client_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_client_btn.clicked.connect(self.create_new_client)
        
        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_client)
        
        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_client)
        
        import_btn = QPushButton("엑셀 가져오기")
        import_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        import_btn.clicked.connect(self.import_from_excel)
        
        export_btn = QPushButton("엑셀 내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_to_excel)
        
        button_layout.addWidget(new_client_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # 2. 업체 목록 테이블
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(7)
        self.client_table.setHorizontalHeaderLabels([
            "업체명", "대표자", "전화번호", "업체주소", "담당자", "핸드폰", "영업담당자"
        ])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.client_table)
    
    def load_clients(self):
        """업체 목록 로드"""
        clients = Client.get_all()
        
        self.client_table.setRowCount(len(clients) if clients else 0)
        
        if clients:
            for row, client in enumerate(clients):
                self.client_table.setItem(row, 0, QTableWidgetItem(client['name']))
                self.client_table.setItem(row, 1, QTableWidgetItem(client['ceo'] or ""))
                self.client_table.setItem(row, 2, QTableWidgetItem(client['phone'] or ""))
                self.client_table.setItem(row, 3, QTableWidgetItem(client['address'] or ""))
                self.client_table.setItem(row, 4, QTableWidgetItem(client['contact_person'] or ""))
                self.client_table.setItem(row, 5, QTableWidgetItem(client['mobile'] or ""))
                self.client_table.setItem(row, 6, QTableWidgetItem(client['sales_rep'] or ""))
    
    def create_new_client(self):
        """신규 업체 등록"""
        dialog = ClientDialog(self)
        if dialog.exec_():
            # 테이블 새로고침
            self.load_clients()
    
    def edit_client(self):
        """업체 정보 수정"""
        selected_rows = self.client_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "수정할 업체를 선택하세요.")
            return
        
        # 선택된 행의 인덱스 가져오기
        row = selected_rows[0].row()
        client_name = self.client_table.item(row, 0).text()
        
        # 해당 업체 정보 가져오기
        clients = Client.search(client_name)
        if not clients:
            QMessageBox.warning(self, "데이터 오류", "선택한 업체 정보를 찾을 수 없습니다.")
            return
        
        client = clients[0]
        
        # 수정 다이얼로그 표시
        dialog = ClientDialog(self, client)
        if dialog.exec_():
            # 테이블 새로고침
            self.load_clients()
    
    def delete_client(self):
        """업체 삭제"""
        selected_rows = self.client_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "삭제할 업체를 선택하세요.")
            return
        
        # 선택된 행의 인덱스 가져오기
        row = selected_rows[0].row()
        client_name = self.client_table.item(row, 0).text()
        
        # 확인 메시지 표시
        reply = QMessageBox.question(
            self, "업체 삭제", 
            f"'{client_name}' 업체를 정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 해당 업체 정보 가져오기
            clients = Client.search(client_name)
            if not clients:
                QMessageBox.warning(self, "데이터 오류", "선택한 업체 정보를 찾을 수 없습니다.")
                return
            
            client = clients[0]
            
            # 업체 삭제
            if Client.delete(client['id']):
                # 테이블 새로고침
                self.load_clients()
                QMessageBox.information(self, "삭제 완료", f"'{client_name}' 업체가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "삭제 실패", "업체 삭제 중 오류가 발생했습니다.")
    
    def import_from_excel(self):
        """엑셀 파일에서 업체 정보 가져오기"""
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
            required_columns = ["업체명"]
            for col in required_columns:
                if col not in df.columns:
                    QMessageBox.warning(self, "파일 오류", f"엑셀 파일에 '{col}' 열이 없습니다.")
                    return
            
            # 컬럼 매핑 (엑셀 컬럼명 -> DB 필드명)
            column_mapping = {
                "업체명": "name",
                "대표자": "ceo",
                "전화번호": "phone",
                "업체주소": "address",
                "담당자": "contact_person",
                "핸드폰": "mobile",
                "영업담당자": "sales_rep"
            }
            
            # 진행 상황 대화상자 표시
            progress = QProgressDialog("업체 정보 가져오는 중...", "취소", 0, len(df), self)
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
                if pd.isna(row["업체명"]) or str(row["업체명"]).strip() == "":
                    skipped_count += 1
                    continue
                
                # 데이터 준비
                client_data = {}
                for excel_col, db_field in column_mapping.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        client_data[db_field] = str(row[excel_col]).strip()
                    else:
                        client_data[db_field] = ""
                
                # 이미 존재하는 업체인지 확인
                existing_clients = Client.search(client_data["name"])
                
                if existing_clients:
                    # 기존 업체 정보 업데이트
                    client = existing_clients[0]
                    if Client.update(
                        client["id"],
                        client_data["name"],
                        client_data["ceo"],
                        client_data["phone"],
                        client_data["address"],
                        client_data["contact_person"],
                        client_data["mobile"],
                        client_data["sales_rep"]
                    ):
                        updated_count += 1
                else:
                    # 새 업체 생성
                    if Client.create(
                        client_data["name"],
                        client_data["ceo"],
                        client_data["phone"],
                        client_data["address"],
                        client_data["contact_person"],
                        client_data["mobile"],
                        client_data["sales_rep"]
                    ):
                        imported_count += 1
            
            # 진행 상황 대화상자 종료
            progress.setValue(len(df))
            
            # 테이블 새로고침
            self.load_clients()
            
            # 결과 메시지 표시
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
            # DB에서 모든 업체 정보 가져오기
            clients = Client.get_all()
            
            if not clients:
                QMessageBox.warning(self, "데이터 없음", "내보낼 업체 정보가 없습니다.")
                return
            
            # 데이터 변환
            data = []
            for client in clients:
                data.append({
                    "업체명": client["name"],
                    "대표자": client["ceo"] or "",
                    "전화번호": client["phone"] or "",
                    "업체주소": client["address"] or "",
                    "담당자": client["contact_person"] or "",
                    "핸드폰": client["mobile"] or "",
                    "영업담당자": client["sales_rep"] or ""
                })
            
            # DataFrame 생성 및 엑셀 파일로 저장
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            # 성공 메시지
            QMessageBox.information(
                self, "내보내기 완료", 
                f"업체 정보가 엑셀 파일로 저장되었습니다.\n파일 위치: {file_path}"
            )
            
            # 파일 열기
            if os.path.exists(file_path):
                import subprocess
                os.startfile(file_path) if os.name == 'nt' else subprocess.call(('xdg-open', file_path))
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일로 내보내는 중 오류가 발생했습니다.\n{str(e)}")

class ClientDialog(QDialog):
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        
        self.client = client
        self.setWindowTitle("업체 정보" if client else "신규 업체 등록")
        self.setMinimumWidth(400)
        
        self.initUI()
        
        # 기존 데이터 채우기
        if client:
            self.name_input.setText(client['name'])
            self.ceo_input.setText(client['ceo'] or "")
            self.phone_input.setText(client['phone'] or "")
            self.address_input.setText(client['address'] or "")
            self.contact_input.setText(client['contact_person'] or "")
            self.mobile_input.setText(client['mobile'] or "")
            self.sales_rep_input.setText(client['sales_rep'] or "")
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("필수 입력")
        form_layout.addRow("* 업체명:", self.name_input)
        
        self.ceo_input = QLineEdit()
        form_layout.addRow("대표자:", self.ceo_input)
        
        self.phone_input = QLineEdit()
        form_layout.addRow("전화번호:", self.phone_input)
        
        self.address_input = QLineEdit()
        form_layout.addRow("업체주소:", self.address_input)
        
        self.contact_input = QLineEdit()
        form_layout.addRow("담당자:", self.contact_input)
        
        self.mobile_input = QLineEdit()
        form_layout.addRow("핸드폰:", self.mobile_input)
        
        self.sales_rep_input = QLineEdit()
        form_layout.addRow("영업담당자:", self.sales_rep_input)
        
        layout.addLayout(form_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_client)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def save_client(self):
        """업체 정보 저장"""
        # 필수 입력 확인
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "업체명은 필수 입력입니다.")
            return
        
        # 데이터 수집
        name = self.name_input.text().strip()
        ceo = self.ceo_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()
        contact_person = self.contact_input.text().strip()
        mobile = self.mobile_input.text().strip()
        sales_rep = self.sales_rep_input.text().strip()
        
        # 저장 (신규 또는 수정)
        if self.client:  # 기존 업체 수정
            if Client.update(self.client['id'], name, ceo, phone, address, contact_person, mobile, sales_rep):
                QMessageBox.information(self, "저장 완료", "업체 정보가 수정되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "저장 실패", "업체 정보 수정 중 오류가 발생했습니다.")
        else:  # 신규 업체 등록
            client_id = Client.create(name, ceo, phone, address, contact_person, mobile, sales_rep)
            if client_id:
                QMessageBox.information(self, "등록 완료", "새 업체가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "등록 실패", "업체 등록 중 오류가 발생했습니다.")