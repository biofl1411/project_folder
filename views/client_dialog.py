# views/client_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QPushButton, QLabel, QMessageBox, 
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from models.clients import Client

class ClientSearchDialog(QDialog):
    """업체 검색 및 선택 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("업체 검색")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.selected_client = None
        self.initUI()
        self.loadClients()
    
    def initUI(self):
        """UI 초기화"""
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        
        # 검색 영역
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("업체명, CEO, 또는 담당자명으로 검색...")
        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self.searchClients)
        self.search_input.returnPressed.connect(self.searchClients)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # 업체 목록 테이블
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(6)
        self.client_table.setHorizontalHeaderLabels(["ID", "업체명", "CEO", "담당자", "연락처", "모바일"])
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_table.doubleClicked.connect(self.selectClient)
        
        # 각 열의 너비 설정
        self.client_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.client_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 업체명
        self.client_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # CEO
        self.client_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 담당자
        self.client_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 연락처
        self.client_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 모바일
        
        layout.addWidget(self.client_table)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("선택")
        select_btn.clicked.connect(self.selectClient)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def loadClients(self):
        """데이터베이스에서 업체 정보 불러오기"""
        try:
            clients = Client.get_all()
            self.displayClients(clients)
        except Exception as e:
            print(f"업체 정보 로드 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    def searchClients(self):
        """검색어로 업체 검색"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.loadClients()  # 검색어가 없으면 모든 업체 표시
            return
        
        try:
            clients = Client.search(search_text)
            self.displayClients(clients)
        except Exception as e:
            print(f"업체 검색 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 검색 중 오류가 발생했습니다: {str(e)}")
    
    def displayClients(self, clients):
        """업체 목록을 테이블에 표시"""
        self.client_table.setRowCount(0)
        
        if not clients:
            QMessageBox.information(self, "정보", "표시할 업체가 없습니다.")
            return
        
        for row, client in enumerate(clients):
            self.client_table.insertRow(row)
            self.client_table.setItem(row, 0, QTableWidgetItem(str(client['id'])))
            self.client_table.setItem(row, 1, QTableWidgetItem(client['name'] or ""))
            self.client_table.setItem(row, 2, QTableWidgetItem(client['ceo'] or ""))
            self.client_table.setItem(row, 3, QTableWidgetItem(client['contact_person'] or ""))
            self.client_table.setItem(row, 4, QTableWidgetItem(client['phone'] or ""))
            self.client_table.setItem(row, 5, QTableWidgetItem(client['mobile'] or ""))
    
    def selectClient(self):
        """선택한 업체 정보 반환"""
        selected_rows = self.client_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "업체를 선택해주세요.")
            return
        
        # 선택된 행의 ID 가져오기
        row = selected_rows[0].row()
        client_id = int(self.client_table.item(row, 0).text())
        
        # 선택된 업체 정보 구성
        self.selected_client = (
            client_id,
            {
                'name': self.client_table.item(row, 1).text(),
                'ceo': self.client_table.item(row, 2).text(),
                'manager_name': self.client_table.item(row, 3).text(),
                'contact_person': self.client_table.item(row, 3).text(),
                'phone': self.client_table.item(row, 4).text(),
                'mobile': self.client_table.item(row, 5).text()
            }
        )
        
        self.accept()


class ClientDialog(QDialog):
    """업체 등록/수정 다이얼로그"""
    
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.client_id = client_id
        self.client_data = None
        
        if client_id:
            self.setWindowTitle("업체 정보 수정")
            self.loadClientData()
        else:
            self.setWindowTitle("새 업체 등록")
        
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        # 업체명
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("필수 입력")
        form_layout.addRow("* 업체명:", self.name_input)
        
        # CEO
        self.ceo_input = QLineEdit()
        form_layout.addRow("CEO:", self.ceo_input)
        
        # 담당자명
        self.contact_person_input = QLineEdit()
        form_layout.addRow("담당자명:", self.contact_person_input)
        
        # 연락처 (업체)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("02-0000-0000")
        form_layout.addRow("업체 연락처:", self.phone_input)
        
        # 연락처 (담당자)
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("010-0000-0000")
        form_layout.addRow("담당자 연락처:", self.mobile_input)
        
        # 주소
        self.address_input = QLineEdit()
        form_layout.addRow("주소:", self.address_input)
        
        # 영업담당자
        self.sales_rep_input = QLineEdit()
        form_layout.addRow("영업담당자:", self.sales_rep_input)
        
        # 메모
        self.notes_input = QLineEdit()
        form_layout.addRow("메모:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.saveClient)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # 기존 데이터 채우기
        if self.client_data:
            self.name_input.setText(self.client_data.get('name', ''))
            self.ceo_input.setText(self.client_data.get('ceo', ''))
            self.contact_person_input.setText(self.client_data.get('contact_person', ''))
            self.phone_input.setText(self.client_data.get('phone', ''))
            self.mobile_input.setText(self.client_data.get('mobile', ''))
            self.address_input.setText(self.client_data.get('address', ''))
            self.sales_rep_input.setText(self.client_data.get('sales_rep', ''))
            self.notes_input.setText(self.client_data.get('notes', ''))
    
    def loadClientData(self):
        """업체 ID로 데이터 로드"""
        try:
            client = Client.get_by_id(self.client_id)
            if client:
                self.client_data = client
            else:
                QMessageBox.warning(self, "오류", f"ID {self.client_id}인 업체를 찾을 수 없습니다.")
                self.reject()
        except Exception as e:
            print(f"업체 정보 로드 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
            self.reject()
    
    def saveClient(self):
        """업체 정보 저장"""
        # 필수 입력 확인
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "업체명은 필수 입력항목입니다.")
            self.name_input.setFocus()
            return
        
        # 데이터 수집
        client_data = {
            'name': self.name_input.text().strip(),
            'ceo': self.ceo_input.text().strip(),
            'contact_person': self.contact_person_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'mobile': self.mobile_input.text().strip(),
            'address': self.address_input.text().strip(),
            'sales_rep': self.sales_rep_input.text().strip(),
            'notes': self.notes_input.text().strip()
        }
        
        try:
            if self.client_id:  # 기존 업체 수정
                success = Client.update(
                    self.client_id, 
                    client_data['name'],
                    client_data['ceo'],
                    client_data['phone'],
                    client_data['address'],
                    client_data['contact_person'],
                    client_data['mobile'],
                    client_data['sales_rep'],
                    client_data['notes']
                )
                if success:
                    msg = "업체 정보가 수정되었습니다."
                else:
                    QMessageBox.warning(self, "저장 실패", "업체 정보를 수정하지 못했습니다.")
                    return
            else:  # 새 업체 추가
                self.client_id = Client.create(
                    client_data['name'],
                    client_data['ceo'],
                    client_data['phone'],
                    client_data['address'],
                    client_data['contact_person'],
                    client_data['mobile'],
                    client_data['sales_rep'],
                    client_data['notes']
                )
                if self.client_id:
                    msg = "새 업체가 등록되었습니다."
                else:
                    QMessageBox.warning(self, "저장 실패", "새 업체를 등록하지 못했습니다.")
                    return
            
            # 정보 저장
            self.client_data = client_data
            
            QMessageBox.information(self, "저장 완료", msg)
            self.accept()
        except Exception as e:
            print(f"업체 정보 저장 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 정보를 저장하는 중 오류가 발생했습니다: {str(e)}")