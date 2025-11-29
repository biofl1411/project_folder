# views/client_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QPushButton, QLabel, QMessageBox,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QGridLayout, QScrollArea, QGroupBox, QComboBox, QWidget)
from PyQt5.QtCore import Qt, QSettings
from models.clients import Client


class ClientSearchDialog(QDialog):
    """업체 검색 및 선택 다이얼로그"""

    # 한글 초성 매핑
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    # 컬럼 정의 (키, 헤더명, 기본너비)
    COLUMNS = [
        ('id', 'ID', 40),
        ('name', '고객/회사명', 150),
        ('ceo', '대표자', 80),
        ('business_no', '사업자번호', 100),
        ('contact_person', '담당자', 80),
        ('phone', '전화번호', 100),
        ('email', 'EMAIL', 150),
        ('sales_rep', '영업담당', 80),
        ('category', '분류', 70),
        ('address', '소재지', 200),
        ('detail_address', '상세주소', 150),
        ('notes', '메모', 100),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("업체 검색")
        self.setMinimumWidth(1100)
        self.setMinimumHeight(500)
        self.selected_client = None
        self.all_clients = []  # 전체 업체 목록 저장
        self.settings = QSettings("MyApp", "ClientSearchDialog")
        self.initUI()
        self.loadColumnSettings()
        self.loadClients()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 검색 영역
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("업체명, CEO, 담당자명, 사업자번호로 검색... (초성 검색 가능: ㅂㅇㅍㄷㄹ)")
        search_btn = QPushButton("검색")
        search_btn.setAutoDefault(False)
        search_btn.setDefault(False)
        search_btn.clicked.connect(self.searchClients)
        self.search_input.returnPressed.connect(self.searchClients)
        # 실시간 검색 필터링
        self.search_input.textChanged.connect(self.filterClients)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # 업체 목록 테이블
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(len(self.COLUMNS))
        self.client_table.setHorizontalHeaderLabels([col[1] for col in self.COLUMNS])
        self.client_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_table.doubleClicked.connect(self.selectClient)

        # 헤더 설정 - 드래그로 열 순서 변경 가능
        header = self.client_table.horizontalHeader()
        header.setSectionsMovable(True)  # 열 순서 변경 가능
        header.setDragEnabled(True)
        header.setDragDropMode(QHeaderView.InternalMove)
        header.setSectionResizeMode(QHeaderView.Interactive)  # 마우스로 너비 조절 가능
        header.setStretchLastSection(True)

        # 기본 열 너비 설정
        for i, (key, name, width) in enumerate(self.COLUMNS):
            self.client_table.setColumnWidth(i, width)

        # 열 순서/너비 변경 시 저장
        header.sectionMoved.connect(self.saveColumnSettings)
        header.sectionResized.connect(self.saveColumnSettings)

        layout.addWidget(self.client_table)

        # 버튼 영역
        btn_layout = QHBoxLayout()

        # 열 설정 초기화 버튼
        reset_btn = QPushButton("열 설정 초기화")
        reset_btn.setAutoDefault(False)
        reset_btn.clicked.connect(self.resetColumnSettings)

        select_btn = QPushButton("선택")
        select_btn.setAutoDefault(False)
        select_btn.setDefault(False)
        select_btn.clicked.connect(self.selectClient)
        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def saveColumnSettings(self):
        """열 순서 및 너비 저장"""
        header = self.client_table.horizontalHeader()

        # 열 순서 저장 (논리적 인덱스 -> 시각적 인덱스 매핑)
        column_order = []
        for logical in range(header.count()):
            visual = header.visualIndex(logical)
            column_order.append(visual)
        self.settings.setValue("column_order", column_order)

        # 열 너비 저장
        column_widths = []
        for i in range(header.count()):
            column_widths.append(header.sectionSize(i))
        self.settings.setValue("column_widths", column_widths)

    def loadColumnSettings(self):
        """저장된 열 순서 및 너비 불러오기"""
        header = self.client_table.horizontalHeader()

        # 열 순서 복원
        column_order = self.settings.value("column_order", None)
        if column_order:
            try:
                for logical, visual in enumerate(column_order):
                    current_visual = header.visualIndex(logical)
                    if current_visual != visual:
                        header.moveSection(current_visual, visual)
            except:
                pass

        # 열 너비 복원
        column_widths = self.settings.value("column_widths", None)
        if column_widths:
            try:
                for i, width in enumerate(column_widths):
                    if isinstance(width, int) and width > 0:
                        self.client_table.setColumnWidth(i, width)
            except:
                pass

    def resetColumnSettings(self):
        """열 설정 초기화"""
        # 저장된 설정 삭제
        self.settings.remove("column_order")
        self.settings.remove("column_widths")

        # 헤더 초기화
        header = self.client_table.horizontalHeader()

        # 열 순서 초기화
        for logical in range(header.count()):
            current_visual = header.visualIndex(logical)
            if current_visual != logical:
                header.moveSection(current_visual, logical)

        # 열 너비 초기화
        for i, (key, name, width) in enumerate(self.COLUMNS):
            self.client_table.setColumnWidth(i, width)

        QMessageBox.information(self, "초기화", "열 설정이 초기화되었습니다.")

    def loadClients(self):
        """데이터베이스에서 업체 정보 불러오기"""
        try:
            self.all_clients = Client.get_all()
            self.displayClients(self.all_clients)
        except Exception as e:
            print(f"업체 정보 로드 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")

    def searchClients(self):
        """검색어로 업체 검색 (DB 검색)"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.loadClients()
            return

        try:
            clients = Client.search(search_text)
            self.displayClients(clients)
        except Exception as e:
            print(f"업체 검색 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 검색 중 오류가 발생했습니다: {str(e)}")

    def get_chosung(self, text):
        """문자열에서 초성 추출"""
        result = ""
        for char in text:
            if '가' <= char <= '힣':
                # 한글 유니코드에서 초성 인덱스 계산
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

    def filterClients(self, search_text):
        """실시간 필터링 (초성 검색 지원)"""
        search_text = search_text.strip()
        if not search_text:
            self.displayClients(self.all_clients)
            return

        filtered = []
        is_chosung = self.is_chosung_only(search_text)

        for client in self.all_clients:
            name = client.get('name', '') or ''
            ceo = client.get('ceo', '') or ''
            contact_person = client.get('contact_person', '') or ''
            business_no = client.get('business_no', '') or ''

            if is_chosung:
                # 초성 검색
                if (self.match_chosung(name, search_text) or
                    self.match_chosung(ceo, search_text) or
                    self.match_chosung(contact_person, search_text)):
                    filtered.append(client)
            else:
                # 일반 검색
                search_lower = search_text.lower()
                if (search_lower in name.lower() or
                    search_lower in ceo.lower() or
                    search_lower in contact_person.lower() or
                    search_lower in business_no.lower()):
                    filtered.append(client)

        self.displayClients(filtered)

    def displayClients(self, clients):
        """업체 목록을 테이블에 표시"""
        self.client_table.setRowCount(0)

        if not clients:
            return

        for row, client in enumerate(clients):
            self.client_table.insertRow(row)
            # COLUMNS 정의 순서대로 데이터 표시
            for col, (key, name, width) in enumerate(self.COLUMNS):
                if key == 'id':
                    value = str(client.get('id', ''))
                else:
                    value = client.get(key, '') or ''
                self.client_table.setItem(row, col, QTableWidgetItem(value))

    def selectClient(self):
        """선택한 업체 정보 반환"""
        selected_rows = self.client_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "업체를 선택해주세요.")
            return

        row = selected_rows[0].row()

        # COLUMNS 정의에서 데이터 추출 (논리적 인덱스 기준)
        client_data = {}
        client_id = None
        for col, (key, name, width) in enumerate(self.COLUMNS):
            item = self.client_table.item(row, col)
            value = item.text() if item else ''
            if key == 'id':
                client_id = int(value) if value else 0
            else:
                client_data[key] = value

        self.selected_client = (client_id, client_data)
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

        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.initUI()

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
        self.contact_person_input = QLineEdit()
        basic_layout.addWidget(self.contact_person_input, 3, 1)

        basic_layout.addWidget(QLabel("EMAIL:"), 3, 2)
        self.email_input = QLineEdit()
        basic_layout.addWidget(self.email_input, 3, 3)

        # Row 4
        basic_layout.addWidget(QLabel("영업담당:"), 4, 0)
        self.sales_rep_input = QLineEdit()
        basic_layout.addWidget(self.sales_rep_input, 4, 1)

        basic_layout.addWidget(QLabel("무료번호:"), 4, 2)
        self.toll_free_input = QLineEdit()
        basic_layout.addWidget(self.toll_free_input, 4, 3)

        # Row 5
        basic_layout.addWidget(QLabel("우편번호:"), 5, 0)
        self.zip_code_input = QLineEdit()
        basic_layout.addWidget(self.zip_code_input, 5, 1)

        basic_layout.addWidget(QLabel("담당자 핸드폰:"), 5, 2)
        self.mobile_input = QLineEdit()
        basic_layout.addWidget(self.mobile_input, 5, 3)

        # Row 6
        basic_layout.addWidget(QLabel("소재지:"), 6, 0)
        self.address_input = QLineEdit()
        basic_layout.addWidget(self.address_input, 6, 1, 1, 3)

        # Row 7
        basic_layout.addWidget(QLabel("메모:"), 7, 0)
        self.notes_input = QLineEdit()
        basic_layout.addWidget(self.notes_input, 7, 1, 1, 3)

        scroll_layout.addWidget(basic_group)

        # 영업 정보 그룹
        sales_group = QGroupBox("영업 정보")
        sales_layout = QGridLayout(sales_group)

        sales_layout.addWidget(QLabel("(영업)업무:"), 0, 0)
        self.sales_business_input = QLineEdit()
        sales_layout.addWidget(self.sales_business_input, 0, 1)

        sales_layout.addWidget(QLabel("(영업)대표번호:"), 0, 2)
        self.sales_phone_input = QLineEdit()
        sales_layout.addWidget(self.sales_phone_input, 0, 3)

        sales_layout.addWidget(QLabel("(영업)핸드폰:"), 1, 0)
        self.sales_mobile_input = QLineEdit()
        sales_layout.addWidget(self.sales_mobile_input, 1, 1)

        sales_layout.addWidget(QLabel("(영업)업체주소:"), 1, 2)
        self.sales_address_input = QLineEdit()
        sales_layout.addWidget(self.sales_address_input, 1, 3)

        scroll_layout.addWidget(sales_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.saveClient)
        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 기존 데이터 채우기
        if self.client_data:
            self.fillData()

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

    def fillData(self):
        """폼에 데이터 채우기"""
        self.name_input.setText(self.client_data.get('name', '') or '')
        self.ceo_input.setText(self.client_data.get('ceo', '') or '')
        self.business_no_input.setText(self.client_data.get('business_no', '') or '')
        self.category_input.setCurrentText(self.client_data.get('category', '') or '')
        self.phone_input.setText(self.client_data.get('phone', '') or '')
        self.fax_input.setText(self.client_data.get('fax', '') or '')
        self.contact_person_input.setText(self.client_data.get('contact_person', '') or '')
        self.email_input.setText(self.client_data.get('email', '') or '')
        self.sales_rep_input.setText(self.client_data.get('sales_rep', '') or '')
        self.toll_free_input.setText(self.client_data.get('toll_free', '') or '')
        self.zip_code_input.setText(self.client_data.get('zip_code', '') or '')
        self.mobile_input.setText(self.client_data.get('mobile', '') or '')
        self.address_input.setText(self.client_data.get('address', '') or '')
        self.notes_input.setText(self.client_data.get('notes', '') or '')
        self.sales_business_input.setText(self.client_data.get('sales_business', '') or '')
        self.sales_phone_input.setText(self.client_data.get('sales_phone', '') or '')
        self.sales_mobile_input.setText(self.client_data.get('sales_mobile', '') or '')
        self.sales_address_input.setText(self.client_data.get('sales_address', '') or '')

    def saveClient(self):
        """업체 정보 저장"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "입력 오류", "고객/회사명은 필수 입력항목입니다.")
            self.name_input.setFocus()
            return

        # 데이터 수집
        client_data = {
            'name': self.name_input.text().strip(),
            'ceo': self.ceo_input.text().strip(),
            'business_no': self.business_no_input.text().strip(),
            'category': self.category_input.currentText().strip(),
            'phone': self.phone_input.text().strip(),
            'fax': self.fax_input.text().strip(),
            'contact_person': self.contact_person_input.text().strip(),
            'email': self.email_input.text().strip(),
            'sales_rep': self.sales_rep_input.text().strip(),
            'toll_free': self.toll_free_input.text().strip(),
            'zip_code': self.zip_code_input.text().strip(),
            'address': self.address_input.text().strip(),
            'notes': self.notes_input.text().strip(),
            'sales_business': self.sales_business_input.text().strip(),
            'sales_phone': self.sales_phone_input.text().strip(),
            'sales_mobile': self.sales_mobile_input.text().strip(),
            'sales_address': self.sales_address_input.text().strip(),
            'mobile': self.mobile_input.text().strip()
        }

        try:
            if self.client_id:  # 기존 업체 수정
                success = Client.update(
                    self.client_id,
                    client_data['name'],
                    client_data['ceo'],
                    client_data['business_no'],
                    client_data['category'],
                    client_data['phone'],
                    client_data['fax'],
                    client_data['contact_person'],
                    client_data['email'],
                    client_data['sales_rep'],
                    client_data['toll_free'],
                    client_data['zip_code'],
                    client_data['address'],
                    client_data['notes'],
                    client_data['sales_business'],
                    client_data['sales_phone'],
                    client_data['sales_mobile'],
                    client_data['sales_address'],
                    client_data['mobile']
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
                    client_data['business_no'],
                    client_data['category'],
                    client_data['phone'],
                    client_data['fax'],
                    client_data['contact_person'],
                    client_data['email'],
                    client_data['sales_rep'],
                    client_data['toll_free'],
                    client_data['zip_code'],
                    client_data['address'],
                    client_data['notes'],
                    client_data['sales_business'],
                    client_data['sales_phone'],
                    client_data['sales_mobile'],
                    client_data['sales_address'],
                    client_data['mobile']
                )
                if self.client_id:
                    msg = "새 업체가 등록되었습니다."
                else:
                    QMessageBox.warning(self, "저장 실패", "새 업체를 등록하지 못했습니다.")
                    return

            self.client_data = client_data

            QMessageBox.information(self, "저장 완료", msg)
            self.accept()
        except Exception as e:
            print(f"업체 정보 저장 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"업체 정보를 저장하는 중 오류가 발생했습니다: {str(e)}")
