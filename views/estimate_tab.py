# views/estimate_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QGridLayout, QGroupBox, QTextEdit, QMessageBox,
    QLineEdit, QSizePolicy, QSplitter, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from models.fees import Fee


class EstimateTab(QWidget):
    """견적서 관리 탭"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule = None
        self.current_user = None
        self.initUI()

    def set_current_user(self, user):
        """로그인 사용자 정보 설정"""
        self.current_user = user

    def initUI(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 상단 버튼 영역
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)

        self.print_btn = QPushButton("인쇄")
        self.print_btn.clicked.connect(self.print_estimate)

        self.pdf_btn = QPushButton("PDF 저장")
        self.pdf_btn.clicked.connect(self.save_as_pdf)

        self.excel_btn = QPushButton("엑셀 저장")
        self.excel_btn.clicked.connect(self.save_as_excel)

        self.email_toggle_btn = QPushButton("이메일 전송 ▼")
        self.email_toggle_btn.clicked.connect(self.toggle_email_panel)

        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.pdf_btn)
        button_layout.addWidget(self.excel_btn)
        button_layout.addWidget(self.email_toggle_btn)
        button_layout.addStretch()

        # 견적서 유형 버튼 (1차, 중단, 연장)
        self.estimate_type = "first"  # 기본값: 1차 견적

        # 버튼 스타일 정의
        self.btn_active_style = """
            QPushButton {
                background-color: #1e90ff;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1873cc;
            }
        """
        self.btn_inactive_style = """
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """
        self.btn_disabled_style = """
            QPushButton {
                background-color: #f0f0f0;
                color: #aaa;
                padding: 8px 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
        """

        self.first_estimate_btn = QPushButton("1차")
        self.first_estimate_btn.setStyleSheet(self.btn_active_style)
        self.first_estimate_btn.clicked.connect(lambda: self.switch_estimate_type("first"))

        self.suspend_estimate_btn = QPushButton("중단")
        self.suspend_estimate_btn.setStyleSheet(self.btn_disabled_style)
        self.suspend_estimate_btn.setEnabled(False)  # 초기 비활성화
        self.suspend_estimate_btn.clicked.connect(lambda: self.switch_estimate_type("suspend"))

        self.extend_estimate_btn = QPushButton("연장")
        self.extend_estimate_btn.setStyleSheet(self.btn_inactive_style)
        self.extend_estimate_btn.clicked.connect(lambda: self.switch_estimate_type("extend"))

        button_layout.addWidget(self.first_estimate_btn)
        button_layout.addWidget(self.suspend_estimate_btn)
        button_layout.addWidget(self.extend_estimate_btn)

        main_layout.addWidget(button_frame)

        # 스크롤 영역 - 수직 스크롤만
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #e0e0e0; }")

        # 견적서 컨테이너 - A4 비율에 맞게 너비 제한 (210:297)
        self.estimate_container = QWidget()
        self.estimate_container.setStyleSheet("background-color: white;")
        self.estimate_container.setFixedWidth(700)  # A4 비율에 맞는 고정 너비

        self.estimate_layout = QVBoxLayout(self.estimate_container)
        self.estimate_layout.setContentsMargins(30, 25, 30, 25)  # 여백 축소
        self.estimate_layout.setSpacing(10)

        # 견적서 내용 생성
        self.create_estimate_content()

        # 스크롤 영역에 컨테이너 배치 (중앙 정렬)
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.addStretch()
        scroll_layout.addWidget(self.estimate_container)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)

        # 스플리터로 견적서와 이메일 패널 분리
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(scroll_area)

        # 이메일 패널 생성
        self.email_panel = self.create_email_panel()
        self.email_panel.setVisible(False)  # 기본적으로 숨김
        splitter.addWidget(self.email_panel)

        # 스플리터 비율 설정 (견적서 70%, 이메일 30%)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)

    def create_estimate_content(self):
        """견적서 내용 생성"""
        # 1. 헤더 (로고 + 견적서 타이틀)
        header_layout = QHBoxLayout()

        # 로고 (기본값은 텍스트, 이미지가 있으면 이미지로 대체)
        self.logo_label = QLabel("BFL")
        self.logo_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #1e90ff;
            font-family: Arial;
        """)
        self.logo_label.setFixedHeight(60)  # 로고 높이 고정

        # 견적서 타이틀
        title_label = QLabel("견 적 서")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #1e90ff;
            border-bottom: 3px solid #1e90ff;
            padding-bottom: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.logo_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.estimate_layout.addLayout(header_layout)

        # 회사명 + 주소 + 홈페이지 (한 줄로 배치, 같은 크기)
        company_address_layout = QHBoxLayout()
        company_address_layout.setSpacing(15)

        self.header_company_label = QLabel("(주)바이오푸드랩")
        self.header_company_label.setStyleSheet("font-size: 10px; color: #666;")

        self.header_address_label = QLabel("")
        self.header_address_label.setStyleSheet("font-size: 10px; color: #666;")

        self.website_label = QLabel("https://www.biofl.co.kr")
        self.website_label.setStyleSheet("font-size: 10px; color: #1e90ff;")

        company_address_layout.addWidget(self.header_company_label)
        company_address_layout.addWidget(self.header_address_label)
        company_address_layout.addWidget(self.website_label)
        company_address_layout.addStretch()

        self.estimate_layout.addLayout(company_address_layout)

        # 구분선
        self.add_separator()

        # 2. 견적 정보 테이블
        info_frame = QFrame()
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(8)
        info_layout.setColumnStretch(1, 1)  # 입력창 영역 확장

        # 입력창 스타일 (스케줄에서 가져온 데이터임을 표시)
        input_style = """
            QLineEdit {
                border: 1px solid #a0c4ff;
                border-radius: 3px;
                padding: 4px 8px;
                background-color: #f0f8ff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #1e90ff;
                background-color: #ffffff;
            }
        """

        # 왼쪽 정보 - 제목(라벨) + 값(입력창)
        # 견적번호
        estimate_no_title = QLabel("견 적 번 호 :")
        estimate_no_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.estimate_no_input = QLineEdit("BFL_소비기한_20250401-2")
        self.estimate_no_input.setStyleSheet(input_style)
        self.estimate_no_input.setPlaceholderText("스케줄에서 자동 생성")

        # 견적일자
        estimate_date_title = QLabel("견 적 일 자 :")
        estimate_date_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.estimate_date_input = QLineEdit("2025년 04월 01일")
        self.estimate_date_input.setStyleSheet(input_style)
        self.estimate_date_input.setPlaceholderText("스케줄에서 자동 생성")

        # 수신
        receiver_title = QLabel("수       신 :")
        receiver_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.receiver_input = QLineEdit("")
        self.receiver_input.setStyleSheet(input_style)
        self.receiver_input.setPlaceholderText("업체명 (스케줄에서 가져옴)")

        # 발신
        sender_title = QLabel("발       신 :")
        sender_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.sender_input = QLineEdit("㈜바이오푸드랩")
        self.sender_input.setStyleSheet(input_style)

        # 오른쪽 정보 (회사 정보 - 설정에서 불러옴) + 직인
        right_info_widget = QWidget()
        right_info_widget.setFixedSize(320, 140)

        # 직인 이미지 (대표자 이름에 겹치도록 위치 지정) - 먼저 생성하여 글 뒤로
        self.stamp_label = QLabel("")
        self.stamp_label.setFixedSize(60, 60)
        self.stamp_label.setStyleSheet("border: none; background: transparent;")
        self.stamp_label.setParent(right_info_widget)
        self.stamp_label.move(140, 5)  # 대표자 이름 옆에 위치
        self.stamp_label.lower()  # 글 뒤로 이동

        # 회사 정보 라벨 (글씨 2포인트 크게: 11px → 13px, 왼쪽 여백 추가)
        self.right_company_info = QLabel("")
        self.right_company_info.setStyleSheet("font-size: 13px; padding-left: 40px;")
        self.right_company_info.setFixedSize(320, 140)
        self.right_company_info.setParent(right_info_widget)
        self.right_company_info.move(0, 0)
        self.right_company_info.setAttribute(Qt.WA_TranslucentBackground)  # 배경 투명

        # 그리드 레이아웃에 배치
        info_layout.addWidget(estimate_no_title, 0, 0)
        info_layout.addWidget(self.estimate_no_input, 0, 1)
        info_layout.addWidget(right_info_widget, 0, 2, 4, 1, Qt.AlignRight | Qt.AlignTop)

        info_layout.addWidget(estimate_date_title, 1, 0)
        info_layout.addWidget(self.estimate_date_input, 1, 1)

        info_layout.addWidget(receiver_title, 2, 0)
        info_layout.addWidget(self.receiver_input, 2, 1)

        info_layout.addWidget(sender_title, 3, 0)
        info_layout.addWidget(self.sender_input, 3, 1)

        self.estimate_layout.addWidget(info_frame)

        # 구분선
        self.add_separator()

        # 3. 견적 상세 정보
        detail_frame = QFrame()
        detail_layout = QGridLayout(detail_frame)
        detail_layout.setSpacing(8)

        self.title_value = QLabel("소비기한설정시험의 건")
        self.total_text_label = QLabel("일금 이백사십일만천칠백 원정")
        self.total_amount_label = QLabel("( ₩2,471,700 )")
        self.total_amount_label.setStyleSheet("color: red; font-weight: bold;")
        self.validity_label = QLabel("견적 후 1개월")
        self.payment_label = QLabel("온라인입금 ( 기업은행: 024-088021-01-017 )")

        detail_layout.addWidget(QLabel("1.   견 적 명 칭"), 0, 0)
        detail_layout.addWidget(QLabel(":"), 0, 1)
        detail_layout.addWidget(self.title_value, 0, 2)

        detail_layout.addWidget(QLabel("2.   합 계 금 액"), 1, 0)
        detail_layout.addWidget(QLabel(":"), 1, 1)
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(self.total_text_label)
        amount_layout.addWidget(self.total_amount_label)
        amount_layout.addStretch()
        detail_layout.addLayout(amount_layout, 1, 2)

        detail_layout.addWidget(QLabel("3.   견적유효기간"), 2, 0)
        detail_layout.addWidget(QLabel(":"), 2, 1)
        detail_layout.addWidget(self.validity_label, 2, 2)

        detail_layout.addWidget(QLabel("4.   결 제 조 건"), 3, 0)
        detail_layout.addWidget(QLabel(":"), 3, 1)
        detail_layout.addWidget(self.payment_label, 3, 2)

        self.estimate_layout.addWidget(detail_frame)

        # 아래와 같이 견적합니다
        note_label = QLabel("아래와 같이 견적합니다.")
        note_label.setStyleSheet("font-size: 12px; margin: 10px 0;")
        self.estimate_layout.addWidget(note_label)

        # 구분선
        self.add_separator()

        # 4. 품목 테이블
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["No.", "식품유형", "검사 항목", "계", "소 계"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 식품유형 열 확장
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.items_table.setColumnWidth(0, 35)
        self.items_table.setColumnWidth(3, 80)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setMinimumHeight(200)
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                gridline-color: #ccc;
            }
            QTableWidget::item {
                padding: 8px 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 5px;
                font-weight: bold;
                text-align: center;
            }
        """)
        # 수직 정렬을 위한 기본 설정
        self.items_table.verticalHeader().setDefaultAlignment(Qt.AlignVCenter)
        self.items_table.verticalHeader().setVisible(False)  # 행 헤더 숨김

        self.estimate_layout.addWidget(self.items_table)

        # 5. Remark 섹션 (편집 가능)
        remark_group = QGroupBox("※ Remark")
        remark_layout = QVBoxLayout(remark_group)

        self.remark_text = QTextEdit()
        self.remark_text.setStyleSheet("""
            QTextEdit {
                font-size: 11px;
                line-height: 1.4;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        self.remark_text.setMinimumHeight(300)
        remark_layout.addWidget(self.remark_text)

        self.estimate_layout.addWidget(remark_group)

        # 6. 합계 금액
        total_frame = QFrame()
        total_frame.setStyleSheet("border-top: 2px solid #333;")
        total_layout = QGridLayout(total_frame)

        self.subtotal_label = QLabel("2,247,000 원")
        self.vat_label = QLabel("224,700 원")

        total_layout.addWidget(QLabel("합계 금액"), 0, 0)
        total_layout.addWidget(QLabel(":"), 0, 1)
        total_layout.addWidget(self.subtotal_label, 0, 2, Qt.AlignRight)

        total_layout.addWidget(QLabel("V. A. T"), 1, 0)
        total_layout.addWidget(QLabel(":"), 1, 1)
        total_layout.addWidget(self.vat_label, 1, 2, Qt.AlignRight)

        self.estimate_layout.addWidget(total_frame)

        # 7. 푸터
        footer_layout = QHBoxLayout()
        footer_left = QLabel("BFL-QI-002-F18")
        footer_center = QLabel("㈜바이오푸드랩")
        footer_right = QLabel("A4(210×297)")
        footer_left.setStyleSheet("font-size: 10px; color: #666;")
        footer_center.setStyleSheet("font-size: 10px; color: #666;")
        footer_right.setStyleSheet("font-size: 10px; color: #666;")

        footer_layout.addWidget(footer_left)
        footer_layout.addStretch()
        footer_layout.addWidget(footer_center)
        footer_layout.addStretch()
        footer_layout.addWidget(footer_right)

        self.estimate_layout.addLayout(footer_layout)

        # 8. 저장 버튼 (인쇄/메일 전송 시 숨김)
        self.save_btn_widget = QWidget()
        save_btn_layout = QHBoxLayout(self.save_btn_widget)
        save_btn_layout.setContentsMargins(0, 10, 0, 0)
        save_btn_layout.addStretch()

        self.save_remark_btn = QPushButton("Remark 저장")
        self.save_remark_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        self.save_remark_btn.clicked.connect(self.save_remark_content)
        save_btn_layout.addWidget(self.save_remark_btn)

        # Remark 초기화 버튼
        self.reset_remark_btn = QPushButton("Remark 초기화")
        self.reset_remark_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        self.reset_remark_btn.clicked.connect(self.reset_remark_content)
        save_btn_layout.addWidget(self.reset_remark_btn)

        save_btn_layout.addStretch()

        self.estimate_layout.addWidget(self.save_btn_widget)

    def add_separator(self):
        """구분선 추가"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ccc;")
        separator.setFixedHeight(1)
        self.estimate_layout.addWidget(separator)

    def load_company_info(self):
        """설정에서 회사 정보 불러오기"""
        import os
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT `key`, value FROM settings")
            settings = cursor.fetchall()
            conn.close()

            settings_dict = {s['key']: s['value'] for s in settings}

            # 회사명
            company_name = settings_dict.get('company_name', '(주)바이오푸드랩')
            self.header_company_label.setText(company_name)
            self.sender_input.setText(company_name)

            # 주소
            address = settings_dict.get('company_address', '서울특별시 구로구 디지털로 30길 28, 마리오타워 1410~1414호')
            self.header_address_label.setText(address)

            # 기본 경로 설정 (실행파일/스크립트 위치 기준)
            import sys
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # 로고 이미지 로드
            logo_path_setting = settings_dict.get('logo_path', '')
            logo_path = logo_path_setting
            print(f"[로고 로드] DB에서 가져온 경로: '{logo_path_setting}'")
            print(f"[로고 로드] base_path: '{base_path}'")

            if logo_path:
                # 상대 경로인 경우 절대 경로로 변환
                if not os.path.isabs(logo_path):
                    logo_path = os.path.join(base_path, logo_path)
                logo_path = os.path.normpath(logo_path)
                print(f"[로고 로드] 최종 경로: '{logo_path}'")
                print(f"[로고 로드] 파일 존재 여부: {os.path.exists(logo_path)}")

            if logo_path and os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                print(f"[로고 로드] QPixmap isNull: {pixmap.isNull()}")
                if not pixmap.isNull():
                    # 로고 크기 조정 (높이 60px 기준으로 비율 유지)
                    scaled_pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setStyleSheet("")  # 기존 텍스트 스타일 제거
                    print("[로고 로드] 로고 이미지 적용 완료")
            else:
                # 기본 텍스트 로고
                print(f"[로고 로드] 기본 텍스트 로고 사용 (경로 없음 또는 파일 없음)")
                self.logo_label.setText("BFL")
                self.logo_label.setStyleSheet("""
                    font-size: 36px;
                    font-weight: bold;
                    color: #1e90ff;
                    font-family: Arial;
                """)

            # 직인 이미지 로드
            stamp_path_setting = settings_dict.get('stamp_path', '')
            stamp_path = stamp_path_setting
            print(f"[도장 로드] DB에서 가져온 경로: '{stamp_path_setting}'")

            if stamp_path:
                # 상대 경로인 경우 절대 경로로 변환
                if not os.path.isabs(stamp_path):
                    stamp_path = os.path.join(base_path, stamp_path)
                stamp_path = os.path.normpath(stamp_path)
                print(f"[도장 로드] 최종 경로: '{stamp_path}'")
                print(f"[도장 로드] 파일 존재 여부: {os.path.exists(stamp_path)}")

            if stamp_path and os.path.exists(stamp_path):
                stamp_pixmap = QPixmap(stamp_path)
                print(f"[도장 로드] QPixmap isNull: {stamp_pixmap.isNull()}")
                if not stamp_pixmap.isNull():
                    # 직인 크기 조정 (60x60px)
                    scaled_stamp = stamp_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.stamp_label.setPixmap(scaled_stamp)
                    self.stamp_label.show()
                    self.stamp_label.raise_()  # 다른 위젯 앞으로 이동
                    print("[도장 로드] 도장 이미지 적용 완료")
            else:
                print(f"[도장 로드] 도장 표시 안함 (경로 없음 또는 파일 없음)")
                self.stamp_label.clear()

            # 오른쪽 회사 정보 구성 (제목열 맞춤)
            ceo = settings_dict.get('company_ceo', '이용표')
            manager = settings_dict.get('company_manager', '')
            phone = settings_dict.get('company_phone', '')
            mobile = settings_dict.get('company_mobile', '')
            fax = settings_dict.get('company_fax', '070-7410-1430')

            # 고정값 사용
            company_name = '(주)바이오푸드랩'
            ceo = '이용표'
            fax = '070-7410-1430'
            address_line1 = '서울특별시 구로구 디지털로 30길 28,'
            address_line2 = '마리오타워 1410~1414호'

            info_lines = []
            info_lines.append(f"회사명 : {company_name}")
            info_lines.append(f"대표자 : {ceo}")
            if manager:
                info_lines.append(f"담당자 : {manager}")
            if phone:
                info_lines.append(f"연락처 : {phone}")
            if mobile:
                info_lines.append(f"핸드폰 : {mobile}")
            info_lines.append(f"팩  스 : {fax}")
            info_lines.append(f"주  소 : {address_line1}")
            info_lines.append(f"          {address_line2}")

            self.right_company_info.setText('\n'.join(info_lines))

        except Exception as e:
            print(f"회사 정보 로드 오류: {e}")
            # 기본값 설정
            self.right_company_info.setText("""회사명 : (주)바이오푸드랩
대표자 : 이용표
담당자 :
연락처 :
핸드폰 :
팩  스 : 070-7410-1430
주  소 : 서울특별시 구로구 디지털로 30길 28,
          마리오타워 1410~1414호""")

    def load_schedule_data(self, schedule):
        """스케줄 데이터로 견적서 로드"""
        self.current_schedule = schedule
        if not schedule:
            return

        from datetime import datetime

        # 스케줄 상태 확인하여 중단 버튼 활성화/비활성화
        schedule_status = schedule.get('status', '')
        if schedule_status == 'suspended':
            # 상태가 '중단'인 경우에만 중단 버튼 활성화
            self.suspend_estimate_btn.setEnabled(True)
            self.suspend_estimate_btn.setStyleSheet(self.btn_inactive_style)
        else:
            # 중단 상태가 아닌 경우 중단 버튼 비활성화
            self.suspend_estimate_btn.setEnabled(False)
            self.suspend_estimate_btn.setStyleSheet(self.btn_disabled_style)
            # 현재 중단 견적서를 보고 있었다면 1차로 전환
            if self.estimate_type == "suspend":
                self.estimate_type = "first"
                self.first_estimate_btn.setStyleSheet(self.btn_active_style)

        # 연장 실험 계획 확인하여 연장 버튼 활성화/비활성화
        extend_rounds = schedule.get('extend_rounds', 0) or 0
        extension_test = schedule.get('extension_test', 0) or 0
        if extend_rounds > 0 or extension_test:
            # 연장 실험 계획이 있으면 연장 버튼 활성화
            self.extend_estimate_btn.setEnabled(True)
            if self.estimate_type == "extend":
                self.extend_estimate_btn.setStyleSheet(self.btn_active_style)
            else:
                self.extend_estimate_btn.setStyleSheet(self.btn_inactive_style)
        else:
            # 연장 실험 계획이 없으면 연장 버튼 비활성화
            self.extend_estimate_btn.setEnabled(False)
            self.extend_estimate_btn.setStyleSheet(self.btn_disabled_style)
            # 현재 연장 견적서를 보고 있었다면 1차로 전환
            if self.estimate_type == "extend":
                self.estimate_type = "first"
                self.first_estimate_btn.setStyleSheet(self.btn_active_style)

        # 회사 정보 로드
        self.load_company_info()

        # 견적번호
        schedule_id = schedule.get('id', '')
        created_at = schedule.get('created_at', '')
        if created_at:
            try:
                # datetime 객체인 경우 직접 사용, 문자열인 경우 파싱
                if isinstance(created_at, datetime):
                    date_obj = created_at
                else:
                    date_obj = datetime.strptime(str(created_at)[:10], '%Y-%m-%d')
                date_str = date_obj.strftime('%Y%m%d')
            except (ValueError, TypeError):
                date_str = datetime.now().strftime('%Y%m%d')
        else:
            date_str = datetime.now().strftime('%Y%m%d')

        # 견적서 유형에 따른 접미사
        type_suffix = {
            "first": "",
            "suspend": "_중단",
            "extend": "_연장"
        }
        suffix = type_suffix.get(self.estimate_type, "")

        self.estimate_no_input.setText(f"BFL_소비기한_{date_str}-{schedule_id}{suffix}")

        # 견적일자
        self.estimate_date_input.setText(f"{datetime.now().strftime('%Y년 %m월 %d일')}")

        # 수신 (업체명)
        client_name = schedule.get('client_name', '')
        self.receiver_input.setText(client_name)

        # 견적 명칭 (유형에 따라 다르게 표시)
        title_names = {
            "first": "소비기한설정시험의 건",
            "suspend": "소비기한설정시험 중단정산의 건",
            "extend": "소비기한설정시험 연장의 건"
        }
        self.title_value.setText(title_names.get(self.estimate_type, "소비기한설정시험의 건"))

        # 품목 테이블 업데이트
        self.update_items_table(schedule)

        # 금액 계산 및 표시
        self.calculate_and_display_totals(schedule)

        # Remark 업데이트
        self.update_remark(schedule)

    def update_items_table(self, schedule):
        """품목 테이블 업데이트"""
        self.items_table.setRowCount(1)

        # 식품유형
        food_type = schedule.get('food_type_name', '기타가공품')

        # 검사 항목 정보 구성
        test_period_days = schedule.get('test_period_days', 0) or 0
        test_period_months = schedule.get('test_period_months', 0) or 0
        test_period_years = schedule.get('test_period_years', 0) or 0

        # 소비기한 문자열
        period_parts = []
        if test_period_years > 0:
            period_parts.append(f"{test_period_years}년")
        if test_period_months > 0:
            period_parts.append(f"{test_period_months}개월")
        if test_period_days > 0:
            period_parts.append(f"{test_period_days}일")
        period_str = " ".join(period_parts) if period_parts else "0개월"

        # 보관조건
        storage_code = schedule.get('storage_condition', 'room_temp')
        storage_map = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }
        storage = storage_map.get(storage_code, storage_code)

        # 실험방법
        test_method = schedule.get('test_method', 'real')
        method_map = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_accel': '의뢰자요청(가속)',
            'custom_acceleration': '의뢰자요청(가속)'
        }
        method_str = method_map.get(test_method, '실측실험')

        # 시험기간 계산 (스케줄 관리에서 수정된 값 우선 사용)
        total_expiry_days = test_period_days + (test_period_months * 30) + (test_period_years * 365)

        # 실제 실험일수가 저장되어 있으면 사용 (날짜 수정 반영)
        actual_experiment_days = schedule.get('actual_experiment_days')
        if actual_experiment_days is not None and actual_experiment_days > 0:
            experiment_days = actual_experiment_days
        else:
            # 기본 계산 방식
            if test_method in ['acceleration', 'custom_accel', 'custom_acceleration']:
                experiment_days = total_expiry_days // 2 if total_expiry_days > 0 else 0
            else:
                experiment_days = int(total_expiry_days * 1.5)

        # 시험기간 문자열 생성 (년/월/일 형식)
        exp_years = experiment_days // 365
        exp_months = (experiment_days % 365) // 30
        exp_days_remaining = experiment_days % 30

        duration_parts = []
        if exp_years > 0: duration_parts.append(f"{exp_years}년")
        if exp_months > 0: duration_parts.append(f"{exp_months}개월")
        if exp_days_remaining > 0: duration_parts.append(f"{exp_days_remaining}일")
        test_duration = ' '.join(duration_parts) if duration_parts else f"{experiment_days}일"

        # 온도 구간 처리 (스케줄 관리와 동일한 방식)
        # 보관조건별 기본 온도 설정
        real_temps = {'room_temp': '15', 'warm': '25', 'cool': '10', 'freeze': '-18'}
        accel_temps = {
            'room_temp': ['15', '25', '35'],
            'warm': ['25', '35', '45'],
            'cool': ['5', '10', '15'],
            'freeze': ['-6', '-12', '-18']
        }

        custom_temps = schedule.get('custom_temperatures', '')
        if custom_temps:
            # 의뢰자 요청온도 사용
            temps = [t.strip().replace('℃', '') for t in custom_temps.split(',')]
        else:
            if test_method in ['acceleration', 'custom_accel', 'custom_acceleration']:
                # 가속실험: 3구간 온도
                temps = accel_temps.get(storage_code, ['25', '35', '45'])
            else:
                # 실측실험: 1구간 온도
                temps = [real_temps.get(storage_code, '15')]

        # 샘플링 횟수
        sampling_count = schedule.get('sampling_count', 6) or 6

        # 실험 주기 계산 (실험일수 / 샘플링 횟수)
        if experiment_days > 0 and sampling_count > 0:
            experiment_interval = experiment_days // sampling_count
        else:
            experiment_interval = 15  # 기본값

        # 검사항목 (스케줄에서 동적으로 가져오기)
        test_items_str = schedule.get('test_items', '')
        if test_items_str:
            test_items_list = [item.strip() for item in test_items_str.split(',') if item.strip()]
        else:
            test_items_list = ['관능평가', '세균수', '대장균(정량)', 'pH']

        # 식품유형 열 텍스트 (식품유형 위에 + 상세정보 아래)
        # 온도 문자열 생성
        if len(temps) == 1:
            temp_str = f"{temps[0]}℃"
        else:
            # 여러 온도는 슬래시로 구분하여 한 줄에 표시
            temp_str = " / ".join([f"{t}℃" for t in temps])

        # 견적 유형에 따라 표시 내용 변경
        if self.estimate_type == "suspend":
            # 중단 견적서: 완료 회차 표시
            completed_rounds = schedule.get('completed_rounds', 0)
            if completed_rounds is None or completed_rounds == 0:
                completed_rounds = max(1, sampling_count // 2)  # 기본값
            food_type_text = f"""{food_type}

소비기한 : {storage} {period_str}
시험기간 : {test_duration}
실험방법 : {method_str}
실험 온도: {temp_str}
※ 중단 정산
완료 회차: {completed_rounds}회 / 전체 {sampling_count}회
실험 주기: {experiment_interval}일"""
        elif self.estimate_type == "extend":
            # 연장 견적서: 연장 회차 표시
            extend_rounds = schedule.get('extend_rounds', 0)
            if extend_rounds is None or extend_rounds == 0:
                extend_rounds = 3  # 기본값
            food_type_text = f"""{food_type}

소비기한 : {storage} {period_str}
시험기간 : {test_duration}
실험방법 : {method_str}
실험 온도: {temp_str}
※ 연장 실험
연장 회차: {extend_rounds}회
실험 주기: {experiment_interval}일"""
        else:
            # 1차 견적서: 기존 내용
            food_type_text = f"""{food_type}

소비기한 : {storage} {period_str}
시험기간 : {test_duration}
실험방법 : {method_str}
실험 온도: {temp_str}
연장시험 : {'진행' if schedule.get('extension_test') else '미진행'}
실험 횟수: {sampling_count}회
실험 주기: {experiment_interval}일"""

        # 검사항목 목록 텍스트 (위에 배치)
        test_items_text = '\n'.join([f"{i+1})  {item}" for i, item in enumerate(test_items_list)])

        # 행 높이 동적 조정 (먼저 계산)
        base_height = 140
        item_height = 18
        temp_lines = len(temps) - 1 if len(temps) > 1 else 0
        row_height = base_height + max(len(test_items_list), temp_lines + 5) * item_height
        self.items_table.setRowHeight(0, row_height)

        # 테이블에 데이터 추가 - QWidget 컨테이너를 사용하여 상단 정렬
        # 셀 위젯 생성 헬퍼 함수
        def create_top_aligned_cell(text, align=Qt.AlignCenter, word_wrap=False):
            """상단 정렬된 셀 위젯 생성"""
            from PyQt5.QtWidgets import QVBoxLayout
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(5, 8, 5, 5)
            layout.setAlignment(Qt.AlignTop)

            label = QLabel(text)
            label.setAlignment(align)
            label.setStyleSheet("background-color: transparent;")
            if word_wrap:
                label.setWordWrap(True)
            layout.addWidget(label)
            layout.addStretch()  # 아래쪽에 여백 추가

            container.setStyleSheet("background-color: white;")
            return container

        # No. 열
        self.items_table.setCellWidget(0, 0, create_top_aligned_cell("1"))

        # 식품유형 열에 상세 정보 포함
        self.items_table.setCellWidget(0, 1, create_top_aligned_cell(food_type_text, Qt.AlignTop | Qt.AlignLeft, True))

        # 검사 항목 열에 검사항목만 표시
        self.items_table.setCellWidget(0, 2, create_top_aligned_cell(test_items_text, Qt.AlignTop | Qt.AlignLeft, True))

        # 금액 계산
        total_price = self.calculate_total_price(schedule)

        # 계 열
        self.items_table.setCellWidget(0, 3, create_top_aligned_cell(f"{total_price:,}", Qt.AlignTop | Qt.AlignRight))

        # 소계 열
        self.items_table.setCellWidget(0, 4, create_top_aligned_cell(f"{total_price:,} 원", Qt.AlignTop | Qt.AlignRight))

    def calculate_total_price(self, schedule, completed_rounds=None):
        """총 금액 계산 - 스케줄 관리에서 전달받은 비용 데이터 사용"""
        # 실험방법 확인
        test_method = schedule.get('test_method', 'real')
        sampling_count = schedule.get('sampling_count', 6) or 6

        # 온도 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 견적 유형에 따른 계산
        if self.estimate_type == "suspend":
            # 중단 견적: 완료된 회차만 계산
            if completed_rounds is not None:
                completed = completed_rounds
            else:
                completed = schedule.get('completed_rounds', 0)
                # 완료 회차가 없으면 기본값으로 전체 회차의 절반 사용
                if completed is None or completed == 0:
                    completed = max(1, sampling_count // 2)
            return self._calculate_suspend_price(schedule, completed, zone_count)
        elif self.estimate_type == "extend":
            # 연장 견적: 연장 비용만 계산
            return self._calculate_extend_price(schedule, zone_count)
        else:
            # 1차 견적: 전체 비용 계산
            return self._calculate_first_price(schedule, zone_count, sampling_count)

    def _calculate_first_price(self, schedule, zone_count, sampling_count):
        """1차 견적 금액 계산 - DB에 저장된 값 우선 사용

        O/X 상태 변경과 관계없이 모든 검사항목이 O인 것으로 가정한 원래 비용 계산
        1차 견적 전용 보고서/중간보고서 비용 사용 (first_report_cost, first_interim_cost)
        """
        # DB에 저장된 1차 견적 값이 있으면 사용 (최우선)
        saved_first_supply = schedule.get('first_supply_amount', 0) or 0
        if saved_first_supply > 0:
            return saved_first_supply

        # 저장된 값이 없으면 계산
        total = 0
        test_method = schedule.get('test_method', 'real')

        # cost_per_test (1회 기준 비용)가 있으면 사용하여 원래 전체 비용 계산
        cost_per_test = schedule.get('cost_per_test', 0) or 0
        if cost_per_test > 0:
            # 원래 전체 비용 = 1회기준 × 샘플링횟수 × 구간수
            total += cost_per_test * sampling_count * zone_count
        else:
            # cost_per_test가 없으면 test_items로 계산 (호환성 유지)
            test_items = schedule.get('test_items', '')
            if test_items:
                item_cost = Fee.calculate_total_fee(test_items)
                total += item_cost * sampling_count * zone_count

        # 1차 견적 전용 보고서 비용 (first_report_cost 우선 사용)
        report_cost = schedule.get('first_report_cost', 0) or schedule.get('report_cost', 0) or 0
        if report_cost == 0:
            # 중간보고서 여부 확인
            report_interim = schedule.get('report_interim', False)
            # 기본 보고서 비용: 가속=300,000원, 실측=200,000원, 중간보고서 있으면=200,000원
            if report_interim:
                report_cost = 200000
            elif test_method in ['acceleration', 'custom_acceleration']:
                report_cost = 300000
            else:
                report_cost = 200000
        total += report_cost

        # 1차 견적 전용 중간보고서 비용 (first_interim_cost 우선 사용)
        interim_report_cost = schedule.get('first_interim_cost', 0) or schedule.get('interim_report_cost', 0) or 0
        total += interim_report_cost

        return int(total)

    def _calculate_suspend_price(self, schedule, completed_rounds, zone_count):
        """중단 견적 금액 계산 - DB에 저장된 값 우선 사용

        상태가 '중단'이고 체크 설정이 O인 경우만 비용에 포함
        중단 견적 전용 보고서/중간보고서 비용 사용 (suspend_report_cost, suspend_interim_cost)
        """
        # DB에 저장된 중단 견적 값이 있으면 사용 (최우선)
        saved_suspend_supply = schedule.get('suspend_supply_amount', 0) or 0
        if saved_suspend_supply > 0:
            return saved_suspend_supply

        # 저장된 값이 없으면 계산
        total = 0
        test_method = schedule.get('test_method', 'real')

        # 스케줄 관리에서 계산된 중단 비용 정보 사용 (O로 체크된 항목만 포함됨)
        # 중단 견적은 suspend_rounds_cost 사용 (total_rounds_cost는 1차 견적용)
        suspend_rounds_cost = schedule.get('suspend_rounds_cost', 0) or 0
        if suspend_rounds_cost > 0:
            # O로 체크된 항목의 비용 × 구간수
            total += suspend_rounds_cost * zone_count
        else:
            # suspend_rounds_cost가 없으면 기존 방식으로 계산 (호환성 유지)
            test_items = schedule.get('test_items', '')
            if test_items:
                item_cost = Fee.calculate_total_fee(test_items)
                total += item_cost * completed_rounds * zone_count

        # 중단 견적 전용 보고서 비용 (suspend_report_cost 우선 사용)
        report_cost = schedule.get('suspend_report_cost', 0) or schedule.get('report_cost', 0) or 0
        if report_cost == 0:
            # 중간보고서 여부 확인
            report_interim = schedule.get('report_interim', False)
            # 기본 보고서 비용: 가속=300,000원, 실측=200,000원, 중간보고서 있으면=200,000원
            if report_interim:
                report_cost = 200000
            elif test_method in ['acceleration', 'custom_acceleration']:
                report_cost = 300000
            else:
                report_cost = 200000
        total += report_cost

        # 중단 견적 전용 중간보고서 비용 (suspend_interim_cost 우선 사용)
        interim_report_cost = schedule.get('suspend_interim_cost', 0) or schedule.get('interim_report_cost', 0) or 0
        total += interim_report_cost

        return int(total)

    def _calculate_extend_price(self, schedule, zone_count):
        """연장 견적 금액 계산 - DB에 저장된 값 우선 사용

        연장 견적 전용 보고서 비용 사용 (extend_report_cost)
        """
        # DB에 저장된 연장 견적 값이 있으면 사용 (최우선)
        saved_extend_supply = schedule.get('extend_supply_amount', 0) or 0
        if saved_extend_supply > 0:
            return saved_extend_supply

        # 저장된 값이 없으면 계산
        total = 0
        test_method = schedule.get('test_method', 'real')

        # 스케줄 관리에서 계산된 연장 회차 비용이 있으면 사용 (O/X 상태 반영됨)
        extend_rounds_cost = schedule.get('extend_rounds_cost', 0) or 0
        if extend_rounds_cost > 0:
            total += extend_rounds_cost * zone_count
        else:
            # 계산된 비용이 없으면 기존 방식으로 계산 (호환성 유지)
            extend_rounds = schedule.get('extend_rounds', 0)
            if extend_rounds is None or extend_rounds == 0:
                extend_rounds = 3  # 기본값

            # 검사항목 수수료 계산 (연장 회차)
            test_items = schedule.get('test_items', '')
            if test_items:
                item_cost = Fee.calculate_total_fee(test_items)
                total += item_cost * extend_rounds * zone_count

        # 연장 견적 전용 보고서 비용 (extend_report_cost 우선 사용)
        report_cost = schedule.get('extend_report_cost', 0) or schedule.get('report_cost', 0) or 0
        if report_cost == 0:
            # 중간보고서 여부 확인
            report_interim = schedule.get('report_interim', False)
            # 기본 보고서 비용: 가속=300,000원, 실측=200,000원, 중간보고서 있으면=200,000원
            if report_interim:
                report_cost = 200000
            elif test_method in ['acceleration', 'custom_acceleration']:
                report_cost = 300000
            else:
                report_cost = 200000
        total += report_cost

        return int(total)

    def calculate_and_display_totals(self, schedule):
        """금액 계산 및 표시"""
        subtotal = self.calculate_total_price(schedule)
        vat = int(subtotal * 0.1)
        total = subtotal + vat

        # 금액을 한글로 변환
        total_text = self.number_to_korean(total)

        self.total_text_label.setText(f"일금 {total_text} 원정")
        self.total_amount_label.setText(f"( ₩{total:,} )")
        self.subtotal_label.setText(f"{subtotal:,} 원")
        self.vat_label.setText(f"{vat:,} 원")

    def number_to_korean(self, num):
        """숫자를 한글로 변환"""
        units = ['', '만', '억', '조']
        nums = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
        small_units = ['', '십', '백', '천']

        if num == 0:
            return '영'

        result = ''
        unit_idx = 0

        while num > 0:
            part = num % 10000
            num //= 10000

            if part > 0:
                part_str = ''
                for i in range(4):
                    digit = part % 10
                    part //= 10
                    if digit > 0:
                        if digit == 1 and i > 0:
                            part_str = small_units[i] + part_str
                        else:
                            part_str = nums[digit] + small_units[i] + part_str

                result = part_str + units[unit_idx] + result

            unit_idx += 1

        return result

    def update_remark(self, schedule):
        """Remark 섹션 업데이트"""
        from datetime import datetime, timedelta

        # 저장된 Remark 내용이 있는지 확인
        field_name = {
            'first': 'remark_first',
            'suspend': 'remark_suspend',
            'extend': 'remark_extend'
        }.get(self.estimate_type, 'remark_first')

        saved_remark = schedule.get(field_name, '') or ''
        if saved_remark:
            # 저장된 내용이 있으면 그대로 사용
            self.remark_text.setPlainText(saved_remark)
            return

        sampling_count = schedule.get('sampling_count', 6) or 6
        test_method = schedule.get('test_method', 'real')

        # 온도 구간 수 결정
        if test_method in ['acceleration', 'custom_accel', 'custom_acceleration']:
            zone_count = 3
            zone_text = "3온도"
        else:
            zone_count = 1
            zone_text = "1온도"

        total_samples = sampling_count * zone_count

        # 연장실험 여부 확인 (연장×2)
        extension_test = schedule.get('extension_test', 0)
        if extension_test:
            total_samples = total_samples * 2

        # 포장단위 정보 가져오기
        packaging_weight = schedule.get('packaging_weight', 0) or 0
        packaging_unit = schedule.get('packaging_unit', 'g') or 'g'
        if packaging_weight > 0:
            packaging_text = f"{packaging_weight}{packaging_unit}"
        else:
            packaging_text = "100g"

        # 소비기한을 일수로 변환
        test_period_days = schedule.get('test_period_days', 0) or 0
        test_period_months = schedule.get('test_period_months', 0) or 0
        test_period_years = schedule.get('test_period_years', 0) or 0
        total_expiry_days = test_period_days + (test_period_months * 30) + (test_period_years * 365)

        # 실험기간 계산 (실측: 소비기한×1.5, 가속: 소비기한÷2)
        if test_method in ['real', 'custom_real']:
            total_experiment_days = int(total_expiry_days * 1.5)
        else:
            total_experiment_days = total_expiry_days // 2 if total_expiry_days > 0 else 0

        # 샘플링 간격 계산
        if total_experiment_days > 0 and sampling_count > 0:
            interval = total_experiment_days // sampling_count
        else:
            interval = 15  # 기본값

        # 중간보고서 실험일수 (6회차 기준)
        interim_experiment_days = interval * 6

        # 시작일과 예상 날짜 계산
        start_date_str = schedule.get('start_date', '')
        interim_expected_date = ""
        final_expected_date = ""

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                # 중간보고서 예상일 (실험 완료 + 분석시간 약 15일)
                interim_date = start_date + timedelta(days=interim_experiment_days + 15)
                interim_expected_date = interim_date.strftime('%Y-%m-%d')
                # 최종보고서 예상일 (실험 완료 + 분석시간 약 15일)
                final_date = start_date + timedelta(days=total_experiment_days + 15)
                final_expected_date = final_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass

        # 소비기한 개월 수 계산
        total_months = test_period_months + (test_period_years * 12)
        if test_period_days >= 15:
            total_months += 1

        # 검사 소요기간 문구 생성
        # 중간 보고서 날짜 및 회차 정보 가져오기 (스케쥴 관리에서)
        report1_date = schedule.get('report1_date', '') or ''
        report2_date = schedule.get('report2_date', '') or ''
        report3_date = schedule.get('report3_date', '') or ''
        interim1_round = schedule.get('interim1_round', 0) or 0
        interim2_round = schedule.get('interim2_round', 0) or 0
        interim3_round = schedule.get('interim3_round', 0) or 0
        report_interim = schedule.get('report_interim', False)

        # 회차별 제조후 일수 계산 함수
        def get_days_for_round(round_num):
            if round_num <= 0 or sampling_count <= 0:
                return 0
            if round_num == 1:
                return 0
            if round_num >= sampling_count:
                return total_experiment_days
            # 중간 회차: 균등 분배
            if sampling_count > 1:
                interval = total_experiment_days / (sampling_count - 1)
                return int(round((round_num - 1) * interval))
            return 0

        test_period_text = ""

        # 중간 보고서 날짜가 있는 경우 (스케쥴 관리에서 입력된 날짜 사용)
        has_report_dates = False

        # 중간 보고서 1 날짜가 있는 경우
        if report1_date and report1_date != '-':
            days_for_interim1 = get_days_for_round(interim1_round)
            test_period_text += f"→ 실험 기간 : {days_for_interim1}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. (중간 보고서 1 / {report1_date})\n"
            has_report_dates = True

        # 중간 보고서 2 날짜가 있는 경우
        if report2_date and report2_date != '-':
            days_for_interim2 = get_days_for_round(interim2_round)
            test_period_text += f"→ 실험 기간 : {days_for_interim2}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. (중간 보고서 2 / {report2_date})\n"
            has_report_dates = True

        # 중간 보고서 3 날짜가 있는 경우
        if report3_date and report3_date != '-':
            days_for_interim3 = get_days_for_round(interim3_round)
            test_period_text += f"→ 실험 기간 : {days_for_interim3}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. (중간 보고서 3 / {report3_date})\n"
            has_report_dates = True

        # 날짜가 없고 report_interim이 체크된 경우 기존 로직 사용
        if not has_report_dates and report_interim:
            interim_date_text = f" / {interim_expected_date}" if interim_expected_date else ""
            test_period_text += f"→ 실험 기간 : {interim_experiment_days}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. ({total_months}개월 중간 보고서{interim_date_text})\n"

        # 최종 보고서 라인
        final_date_text = f" / {final_expected_date}" if final_expected_date else ""
        test_period_text += f"→ 실험 기간 : {total_experiment_days}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. (최종 보고서{final_date_text})"

        # 견적 유형에 따른 Remark 생성
        if self.estimate_type == "suspend":
            # 중단 견적서 Remark
            completed_rounds = schedule.get('completed_rounds', 0)
            if completed_rounds is None or completed_rounds == 0:
                completed_rounds = max(1, sampling_count // 2)  # 기본값: 전체의 절반

            # 1차 견적 금액 계산 (부가세 포함)
            first_price = self._calculate_first_price(schedule, zone_count, sampling_count)
            first_price_with_vat = int(first_price * 1.1)  # 부가세 10% 포함

            # 중단 시 진행한 실험 비용 계산 (부가세 포함)
            suspend_price = self._calculate_suspend_price(schedule, completed_rounds, zone_count)
            suspend_price_with_vat = int(suspend_price * 1.1)  # 부가세 10% 포함

            # 잔여 금액 계산
            remaining_price = first_price_with_vat - suspend_price_with_vat

            # 로그인 사용자 정보
            user_name = ""
            user_phone = ""
            user_mobile = ""
            if self.current_user:
                user_name = self.current_user.get('name', '')
                user_phone = self.current_user.get('phone', '')
                user_mobile = self.current_user.get('mobile', '')

            remark_text = f"""※ 중단 정산 내역

→ 실험 중단 사유: 품질한계 도달 / 의뢰자 요청
→ 완료된 실험 회차: {completed_rounds}회 / 전체 {sampling_count}회 (온도 {zone_count}구간)
→ 정산 기준: 1차 견적 = {first_price_with_vat:,}원(부가세 포함) - {suspend_price_with_vat:,}원(중단 시 진행한 실험 비용) = {remaining_price:,}원(잔여)

※ 정산 안내
* 본 견적서는 실험 중단에 따른 정산 견적서입니다.
* 완료된 실험 회차까지의 비용만 청구됩니다.
* 이미 입금이 완료된 경우 환불 또는 다른 검사 비용으로 사용이 가능합니다.
* 추가 문의사항은 {user_name}, {user_phone}, {user_mobile} 연락 주시기 바랍니다.

※ 입금 계좌 안내
- 기업 은행 : 024-088021-01-017
- 우리 은행 : 1005-702-799176
- 농협 은행 : 301-0178-1722-11
★ 입금시 '대표자명' 또는 '업체명'으로 입금 부탁드립니다.
★ 업체명으로 입금 진행시, [농업회사법인 주식회]에서 잘리는 경우가 있습니다.
   이와 같은 경우, 입금 확인이 늦어질 수 있으니 업체명을 식별할 수 있도록 표시 부탁드립니다."""

        elif self.estimate_type == "extend":
            # 연장 견적서 Remark
            extend_rounds = schedule.get('extend_rounds', 0)
            if extend_rounds is None or extend_rounds == 0:
                extend_rounds = 3  # 기본값: 3회

            # 연장 실험 간격 계산
            extend_experiment_days = schedule.get('extend_experiment_days', 0)
            sampling_interval = schedule.get('sampling_interval', 15) or 15
            if extend_rounds > 0 and extend_experiment_days > 0:
                extend_interval = extend_experiment_days // extend_rounds
            else:
                extend_interval = sampling_interval

            remark_text = f"""※ 연장실험 안내

→ 연장 실험 회차: {extend_rounds}회 (온도 {zone_count}구간)
→ 연장 샘플링 간격: 약 {extend_interval}일

※ 연장실험 진행 절차
1. 본 견적서 확인 후 입금
2. 연장실험 진행 (기존 보관 검체 사용)
3. 최종 보고서 발행

* 연장실험은 기존 실험 데이터와 연계하여 진행됩니다.
* 기존 보관 중인 검체를 사용하여 연장 실험을 진행합니다.
* 연장실험 후 최종 보고서가 발행됩니다.

※ 입금 계좌 안내
- 기업 은행 : 024-088021-01-017
- 우리 은행 : 1005-702-799176
- 농협 은행 : 301-0178-1722-11
★ 입금시 '대표자명' 또는 '업체명'으로 입금 부탁드립니다.
★ 업체명으로 입금 진행시, [농업회사법인 주식회]에서 잘리는 경우가 있습니다.
   이와 같은 경우, 입금 확인이 늦어질 수 있으니 업체명을 식별할 수 있도록 표시 부탁드립니다."""

        else:
            # 1차 견적서 Remark (기존 내용)
            remark_text = f"""※ 검체량
→ 검체는 판매 또는 판매 예정인 제품과 동일하게 검사제품을 준비해주시기 바랍니다.
→ 검체량 : 온도 구간별({zone_text}) 총 {sampling_count}회씩 실험 = {total_samples}ea
    => 포장단위 {packaging_text} 이상 제품 기준 총 {total_samples}ea 이상 준비

※ 검사 소요기간
{test_period_text}
→ 실험스케쥴(구간 및 횟수)은 실험결과의 유의성에 따라 보고서 발행일 수가 변경될 수 있습니다.

* 예상 소비기한은 견적이며, 품질안전한계기간 미도달 시에도 실험연장 불가합니다.
* 견적 금액은 검사비용 외 보관비 및 보고서작성 비용 포함입니다.
* 지표 항목의 수정(추가)이나 삭제가 필요한 경우 사전 연락을 해주시고 문의사항은 연락 바랍니다.
* 온도 구간별 1회 시험을 하며, 반복 실험이 필요한 경우 연락 바랍니다.
* 소비기한 설정 실험은 입금 후 진행되며, 검사 중 품질한계 도달로 실험 중단 시, 중단 전까지의 비용 청구됩니다.

※ 입금 계좌 안내
- 기업 은행 : 024-088021-01-017
- 우리 은행 : 1005-702-799176
- 농협 은행 : 301-0178-1722-11
★ 입금시 '대표자명' 또는 '업체명'으로 입금 부탁드립니다.
★ 업체명으로 입금 진행시, [농업회사법인 주식회]에서 잘리는 경우가 있습니다.
   이와 같은 경우, 입금 확인이 늦어질 수 있으니 업체명을 식별할 수 있도록 표시 부탁드립니다."""

        self.remark_text.setPlainText(remark_text)

    def save_remark_content(self):
        """Remark 내용 저장"""
        if not self.current_schedule:
            QMessageBox.warning(self, "저장 실패", "먼저 스케줄을 선택해주세요.")
            return

        try:
            from database import get_connection

            schedule_id = self.current_schedule.get('id')
            if not schedule_id:
                QMessageBox.warning(self, "저장 실패", "스케줄 ID를 찾을 수 없습니다.")
                return

            # Remark 내용 가져오기
            remark_content = self.remark_text.toPlainText()

            # 견적서 유형에 따라 다른 필드에 저장
            field_name = {
                'first': 'remark_first',
                'suspend': 'remark_suspend',
                'extend': 'remark_extend'
            }.get(self.estimate_type, 'remark_first')

            # 데이터베이스 업데이트
            conn = get_connection()
            cursor = conn.cursor()

            # 컬럼이 없으면 추가
            cursor.execute("SHOW COLUMNS FROM schedules")
            columns = [col['Field'] for col in cursor.fetchall()]
            for col in ['remark_first', 'remark_suspend', 'remark_extend']:
                if col not in columns:
                    cursor.execute(f"ALTER TABLE schedules ADD COLUMN {col} TEXT")

            cursor.execute(f"""
                UPDATE schedules SET {field_name} = %s WHERE id = %s
            """, (remark_content, schedule_id))

            conn.commit()
            conn.close()

            # current_schedule도 업데이트하여 다시 로드할 때 반영되도록
            self.current_schedule[field_name] = remark_content

            QMessageBox.information(self, "저장 완료", "Remark 내용이 저장되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def reset_remark_content(self):
        """Remark 내용 초기화 - 저장된 내용 삭제 후 기본 템플릿 적용"""
        if not self.current_schedule:
            QMessageBox.warning(self, "초기화 실패", "먼저 스케줄을 선택해주세요.")
            return

        reply = QMessageBox.question(
            self, "Remark 초기화",
            "저장된 Remark 내용을 삭제하고 기본 템플릿으로 초기화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            from database import get_connection

            schedule_id = self.current_schedule.get('id')
            if not schedule_id:
                return

            # 견적서 유형에 따라 다른 필드 초기화
            field_name = {
                'first': 'remark_first',
                'suspend': 'remark_suspend',
                'extend': 'remark_extend'
            }.get(self.estimate_type, 'remark_first')

            # 데이터베이스에서 해당 필드 초기화
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE schedules SET {field_name} = NULL WHERE id = %s
            """, (schedule_id,))
            conn.commit()
            conn.close()

            # current_schedule에서도 삭제
            if field_name in self.current_schedule:
                self.current_schedule[field_name] = None

            # 새 템플릿으로 Remark 업데이트
            self.update_remark(self.current_schedule)

            QMessageBox.information(self, "초기화 완료", "Remark가 기본 템플릿으로 초기화되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"초기화 중 오류가 발생했습니다:\n{str(e)}")

    def print_estimate(self):
        """견적서 인쇄 - A4 사이즈 전체 활용"""
        from PyQt5.QtCore import QMarginsF
        from PyQt5.QtGui import QPainter, QPageLayout, QPageSize

        printer = QPrinter(QPrinter.HighResolution)

        # A4 사이즈 설정
        page_layout = QPageLayout(
            QPageSize(QPageSize.A4),
            QPageLayout.Portrait,
            QMarginsF(10, 10, 10, 10)  # 여백 설정 (mm)
        )
        printer.setPageLayout(page_layout)

        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            # 저장 버튼 숨기기
            self.save_btn_widget.setVisible(False)

            painter = QPainter()
            if painter.begin(printer):
                # 페이지 크기
                page_rect = printer.pageRect(QPrinter.DevicePixel)

                # 위젯의 실제 내용 크기 계산
                widget = self.estimate_container
                widget_width = widget.sizeHint().width() if widget.sizeHint().width() > 0 else widget.width()
                widget_height = widget.sizeHint().height() if widget.sizeHint().height() > 0 else widget.height()

                # A4 너비에 맞게 스케일 계산
                scale = page_rect.width() / widget_width

                # 세로가 넘치면 세로 기준으로 스케일 조정
                if widget_height * scale > page_rect.height():
                    scale = page_rect.height() / widget_height

                # 여유 공간 확보
                scale = scale * 0.95

                # 왼쪽 상단에서 시작 (중앙 정렬 제거)
                painter.scale(scale, scale)
                widget.render(painter)
                painter.end()

            # 저장 버튼 다시 표시
            self.save_btn_widget.setVisible(True)

    def save_as_pdf(self):
        """PDF로 저장"""
        import os
        from datetime import datetime
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtCore import QMarginsF
        from PyQt5.QtGui import QPainter, QPageLayout, QPageSize

        if not self.current_schedule:
            QMessageBox.warning(self, "알림", "저장할 견적서가 없습니다. 먼저 스케줄을 선택해주세요.")
            return

        # 설정에서 출력 경로 가져오기
        output_path = ""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'output_path'")
            result = cursor.fetchone()
            conn.close()
            if result and result['value']:
                output_path = result['value']
        except Exception as e:
            print(f"설정 로드 오류: {e}")

        # 파일명 생성: 업체명+식품유형+견적일자+보관조건+실험방법
        client_name = self.current_schedule.get('client_name', '업체명') or '업체명'
        food_type = self.current_schedule.get('food_type_name', '식품유형') or '식품유형'
        estimate_date = datetime.now().strftime('%Y%m%d')

        # 보관조건 변환
        storage_code = self.current_schedule.get('storage_condition', 'room_temp')
        storage_map = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }
        storage = storage_map.get(storage_code, storage_code)

        # 실험방법 변환
        test_method = self.current_schedule.get('test_method', 'real')
        method_map = {
            'real': '실측',
            'acceleration': '가속',
            'custom_real': '의뢰자요청_실측',
            'custom_accel': '의뢰자요청_가속',
            'custom_acceleration': '의뢰자요청_가속'
        }
        method_str = method_map.get(test_method, test_method)

        # 파일명에서 사용할 수 없는 문자 제거
        def sanitize_filename(name):
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '_')
            return name

        filename = f"{client_name}_{food_type}_{estimate_date}_{storage}_{method_str}.pdf"
        filename = sanitize_filename(filename)

        # 저장 경로 결정
        if output_path and os.path.isdir(output_path):
            # 설정된 폴더가 존재하면 사용
            file_path = os.path.join(output_path, filename)
            # 파일 덮어쓰기 확인
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, "파일 덮어쓰기",
                    f"파일이 이미 존재합니다:\n{file_path}\n\n덮어쓰시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    # 다른 이름으로 저장
                    file_path, _ = QFileDialog.getSaveFileName(
                        self, "PDF 저장", os.path.join(output_path, filename),
                        "PDF 파일 (*.pdf)"
                    )
                    if not file_path:
                        return
        else:
            # 설정된 폴더가 없으면 사용자에게 물어봄
            default_path = os.path.expanduser("~/Documents")
            if not os.path.exists(default_path):
                default_path = os.path.expanduser("~")

            file_path, _ = QFileDialog.getSaveFileName(
                self, "PDF 저장", os.path.join(default_path, filename),
                "PDF 파일 (*.pdf)"
            )
            if not file_path:
                return

        # PDF 생성
        try:
            # 저장 버튼 숨기기
            self.save_btn_widget.setVisible(False)

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setResolution(300)  # 300 DPI로 고해상도 설정

            # A4 사이즈 설정
            page_layout = QPageLayout(
                QPageSize(QPageSize.A4),
                QPageLayout.Portrait,
                QMarginsF(10, 10, 10, 10)  # 여백 설정 (mm)
            )
            printer.setPageLayout(page_layout)

            painter = QPainter()
            if painter.begin(printer):
                # 고품질 렌더링 설정
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.TextAntialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

                # 페이지 크기
                page_rect = printer.pageRect(QPrinter.DevicePixel)

                # 위젯의 실제 내용 크기 계산
                widget = self.estimate_container
                widget_width = widget.sizeHint().width() if widget.sizeHint().width() > 0 else widget.width()
                widget_height = widget.sizeHint().height() if widget.sizeHint().height() > 0 else widget.height()

                # A4 너비에 맞게 스케일 계산
                scale = page_rect.width() / widget_width

                # 세로가 넘치면 세로 기준으로 스케일 조정
                if widget_height * scale > page_rect.height():
                    scale = page_rect.height() / widget_height

                # 여유 공간 확보
                scale = scale * 0.95

                # 왼쪽 상단에서 시작
                painter.scale(scale, scale)
                widget.render(painter)
                painter.end()

                QMessageBox.information(self, "저장 완료", f"PDF가 저장되었습니다.\n\n{file_path}")
            else:
                QMessageBox.critical(self, "오류", "PDF 생성에 실패했습니다.")

            # 저장 버튼 다시 표시
            self.save_btn_widget.setVisible(True)

        except Exception as e:
            # 저장 버튼 다시 표시
            self.save_btn_widget.setVisible(True)
            QMessageBox.critical(self, "오류", f"PDF 저장 중 오류가 발생했습니다:\n{str(e)}")

    def save_as_excel(self):
        """엑셀로 저장"""
        QMessageBox.information(self, "알림", "엑셀 저장 기능은 추후 구현 예정입니다.")

    def create_email_panel(self):
        """이메일 전송 패널 생성"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 제목
        title_label = QLabel("이메일 전송")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(title_label)

        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        # 입력 필드 스타일
        input_style = """
            QLineEdit, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #1e90ff;
            }
        """

        # 수신자 (여러 명, 콤마로 구분)
        self.email_to_input = QLineEdit()
        self.email_to_input.setPlaceholderText("여러 명은 콤마(,)로 구분 (예: a@email.com, b@email.com)")
        self.email_to_input.setStyleSheet(input_style)
        form_layout.addRow("수신자:", self.email_to_input)

        # 참조 (여러 명, 콤마로 구분)
        self.email_cc_input = QLineEdit()
        self.email_cc_input.setPlaceholderText("여러 명은 콤마(,)로 구분 (선택사항)")
        self.email_cc_input.setStyleSheet(input_style)
        form_layout.addRow("참조(CC):", self.email_cc_input)

        # 제목
        self.email_subject_input = QLineEdit()
        self.email_subject_input.setStyleSheet(input_style)
        form_layout.addRow("제목:", self.email_subject_input)

        layout.addLayout(form_layout)

        # 본문
        body_label = QLabel("본문:")
        body_label.setStyleSheet("border: none;")
        layout.addWidget(body_label)

        self.email_body_input = QTextEdit()
        self.email_body_input.setStyleSheet(input_style)
        self.email_body_input.setMinimumHeight(150)
        layout.addWidget(self.email_body_input)

        # 첨부파일 표시
        attachment_layout = QHBoxLayout()
        attachment_label = QLabel("첨부파일:")
        attachment_label.setStyleSheet("border: none;")
        self.attachment_path_label = QLabel("견적서가 PDF로 자동 첨부됩니다")
        self.attachment_path_label.setStyleSheet("color: #666; border: none;")
        attachment_layout.addWidget(attachment_label)
        attachment_layout.addWidget(self.attachment_path_label)
        attachment_layout.addStretch()
        layout.addLayout(attachment_layout)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.email_preview_btn = QPushButton("미리보기 새로고침")
        self.email_preview_btn.clicked.connect(self.refresh_email_template)
        btn_layout.addWidget(self.email_preview_btn)

        self.email_send_btn = QPushButton("이메일 발송")
        self.email_send_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1873cc;
            }
        """)
        self.email_send_btn.clicked.connect(self.send_email)
        btn_layout.addWidget(self.email_send_btn)

        layout.addLayout(btn_layout)

        return panel

    def toggle_email_panel(self):
        """이메일 패널 표시/숨김 토글"""
        if self.email_panel.isVisible():
            self.email_panel.setVisible(False)
            self.email_toggle_btn.setText("이메일 전송 ▼")
        else:
            self.email_panel.setVisible(True)
            self.email_toggle_btn.setText("이메일 전송 ▲")
            # 이메일 템플릿 로드
            self.refresh_email_template()

    def refresh_email_template(self):
        """이메일 템플릿 새로고침"""
        if not self.current_schedule:
            self.email_subject_input.setText("[바이오푸드랩] 견적서 송부의 건")
            self.email_body_input.setPlainText("스케줄을 먼저 선택해주세요.")
            return

        # 설정에서 회사 정보 가져오기
        company_name = "(주)바이오푸드랩"
        company_phone = ""
        company_mobile = ""
        company_email = ""
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT `key`, value FROM settings")
            settings = cursor.fetchall()
            conn.close()
            settings_dict = {s['key']: s['value'] for s in settings}
            company_name = settings_dict.get('company_name', '(주)바이오푸드랩') or '(주)바이오푸드랩'
            company_phone = settings_dict.get('company_phone', '') or ''
            company_mobile = settings_dict.get('company_mobile', '') or ''
            company_email = settings_dict.get('company_email', '') or settings_dict.get('smtp_email', '') or ''
        except Exception as e:
            print(f"설정 로드 오류: {e}")

        # 동적 데이터 추출
        client_name = self.current_schedule.get('client_name', '') or ''
        food_type = self.current_schedule.get('food_type_name', '') or ''

        # 보관조건 변환
        storage_code = self.current_schedule.get('storage_condition', 'room_temp')
        storage_map = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }
        storage = storage_map.get(storage_code, storage_code)

        # 실험방법 변환
        test_method = self.current_schedule.get('test_method', 'real')
        method_map = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_accel': '의뢰자요청(가속)',
            'custom_acceleration': '의뢰자요청(가속)'
        }
        method_str = method_map.get(test_method, test_method)

        # 실험 횟수
        sampling_count = self.current_schedule.get('sampling_count', 6) or 6

        # 온도 구간 수
        if test_method in ['acceleration', 'custom_accel', 'custom_acceleration']:
            zone_count = 3
        else:
            zone_count = 1

        # 실험 주기 계산
        test_period_days = self.current_schedule.get('test_period_days', 0) or 0
        test_period_months = self.current_schedule.get('test_period_months', 0) or 0
        test_period_years = self.current_schedule.get('test_period_years', 0) or 0
        total_expiry_days = test_period_days + (test_period_months * 30) + (test_period_years * 365)

        if test_method in ['real', 'custom_real']:
            experiment_days = int(total_expiry_days * 1.5)
        else:
            experiment_days = total_expiry_days // 2 if total_expiry_days > 0 else 0

        if experiment_days > 0 and sampling_count > 0:
            experiment_interval = experiment_days // sampling_count
        else:
            experiment_interval = 15

        # 필요 시료량 계산
        total_samples = sampling_count * zone_count
        packaging_weight = self.current_schedule.get('packaging_weight', 0) or 0
        packaging_unit = self.current_schedule.get('packaging_unit', 'g') or 'g'
        if packaging_weight > 0:
            sample_text = f"포장단위 {packaging_weight}{packaging_unit} 이상 제품 기준 총 {total_samples}ea 이상"
        else:
            sample_text = f"총 {total_samples}ea 이상"

        # 총액 계산
        total_price = self.calculate_total_price(self.current_schedule)
        vat = int(total_price * 0.1)
        total_with_vat = total_price + vat

        # 제목 설정
        self.email_subject_input.setText(f"[바이오푸드랩] {client_name} 견적서 송부의 건")

        # 서명 정보 구성
        signature_lines = [company_name]
        if company_phone:
            signature_lines.append(f"Tel: {company_phone}")
        if company_mobile:
            signature_lines.append(f"Mobile: {company_mobile}")
        if company_email:
            signature_lines.append(f"Email: {company_email}")
        signature = '\n'.join(signature_lines)

        # 본문 템플릿
        body_template = f"""안녕하세요, {company_name}입니다.

{client_name} 귀하

요청하신 소비기한 설정시험 견적서를 송부드립니다.

■ 견적 정보
  - 식품유형: {food_type}
  - 보관조건: {storage}
  - 실험방법: {method_str}
  - 실험횟수: {sampling_count}회 (온도 {zone_count}구간)
  - 실험주기: {experiment_interval}일
  - 필요시료: {sample_text}
  - 견적금액: {total_with_vat:,}원 (VAT 포함)

첨부된 견적서를 확인해 주시기 바랍니다.
문의사항이 있으시면 언제든 연락 부탁드립니다.

감사합니다.

─────────────────────────
{signature}
─────────────────────────"""

        self.email_body_input.setPlainText(body_template)

    def send_email(self):
        """이메일 발송"""
        import os
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        from email.header import Header
        from datetime import datetime

        # 입력 검증
        to_emails = self.email_to_input.text().strip()
        if not to_emails:
            QMessageBox.warning(self, "입력 오류", "수신자 이메일을 입력해주세요.")
            return

        if not self.current_schedule:
            QMessageBox.warning(self, "오류", "견적서를 먼저 선택해주세요.")
            return

        # SMTP 설정 가져오기
        try:
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT `key`, value FROM settings")
            settings = cursor.fetchall()
            conn.close()

            settings_dict = {s['key']: s['value'] for s in settings}

            smtp_server = settings_dict.get('smtp_server', '')
            smtp_port = int(settings_dict.get('smtp_port', '587'))
            smtp_security = settings_dict.get('smtp_security', 'TLS')
            smtp_email = settings_dict.get('smtp_email', '')
            smtp_password = settings_dict.get('smtp_password', '')
            sender_name = settings_dict.get('smtp_sender_name', '(주)바이오푸드랩')
            output_path = settings_dict.get('output_path', '')

            if not smtp_server or not smtp_email or not smtp_password:
                QMessageBox.warning(self, "설정 오류",
                    "이메일 설정이 완료되지 않았습니다.\n설정 > 이메일 탭에서 SMTP 설정을 완료해주세요.")
                return

        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 로드 중 오류: {str(e)}")
            return

        # PDF 저장 (첨부용)
        pdf_path = self._save_pdf_for_email(output_path)
        if not pdf_path:
            return

        # 이메일 구성
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name} <{smtp_email}>"

            # 수신자 처리 (여러 명)
            to_list = [email.strip() for email in to_emails.split(',') if email.strip()]
            msg['To'] = ', '.join(to_list)

            # 참조 처리 (여러 명)
            cc_emails = self.email_cc_input.text().strip()
            cc_list = []
            if cc_emails:
                cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
                msg['Cc'] = ', '.join(cc_list)

            msg['Subject'] = self.email_subject_input.text()

            # 본문
            body = self.email_body_input.toPlainText()
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # PDF 첨부 (한글 파일명 인코딩 처리)
            with open(pdf_path, 'rb') as attachment:
                part = MIMEBase('application', 'pdf')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)

                # 한글 파일명을 위한 RFC 2231 인코딩
                filename = os.path.basename(pdf_path)
                encoded_filename = Header(filename, 'utf-8').encode()
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=('utf-8', '', filename)
                )
                part.add_header('Content-Type', 'application/pdf', name=encoded_filename)
                msg.attach(part)

            # SMTP 연결 및 발송
            all_recipients = to_list + cc_list

            if smtp_security == "SSL":
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                if smtp_security == "TLS":
                    server.starttls()

            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, all_recipients, msg.as_string())
            server.quit()

            # 이메일 발송 로그 저장
            try:
                from models.communications import EmailLog
                schedule_id = self.current_schedule.get('id')
                client_name = self.current_schedule.get('client_name', '')
                estimate_type = getattr(self, 'estimate_type', 'first')
                sent_by = self.current_user.get('id') if hasattr(self, 'current_user') and self.current_user else None

                EmailLog.save(
                    schedule_id=schedule_id,
                    estimate_type=estimate_type,
                    sender_email=smtp_email,
                    to_emails=', '.join(to_list),
                    cc_emails=', '.join(cc_list) if cc_list else None,
                    subject=self.email_subject_input.text(),
                    body=body,
                    attachment_name=os.path.basename(pdf_path),
                    sent_by=sent_by,
                    client_name=client_name
                )
            except Exception as log_err:
                print(f"이메일 로그 저장 오류: {log_err}")

            QMessageBox.information(self, "발송 완료",
                f"이메일이 성공적으로 발송되었습니다.\n\n"
                f"수신자: {', '.join(to_list)}\n"
                f"{'참조: ' + ', '.join(cc_list) if cc_list else ''}\n"
                f"첨부파일: {os.path.basename(pdf_path)}")

            # 첨부파일 경로 업데이트
            self.attachment_path_label.setText(f"첨부됨: {os.path.basename(pdf_path)}")

        except smtplib.SMTPAuthenticationError:
            QMessageBox.critical(self, "인증 오류",
                "SMTP 인증에 실패했습니다.\n이메일 또는 비밀번호를 확인해주세요.\n\n"
                "Gmail의 경우 '앱 비밀번호'를 사용해야 합니다.")
        except smtplib.SMTPException as e:
            QMessageBox.critical(self, "발송 오류", f"이메일 발송 중 오류가 발생했습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"오류가 발생했습니다:\n{str(e)}")

    def _save_pdf_for_email(self, output_path):
        """이메일 첨부용 PDF 저장"""
        import os
        from datetime import datetime
        from PyQt5.QtCore import QMarginsF
        from PyQt5.QtGui import QPainter, QPageLayout, QPageSize

        # 파일명 생성
        client_name = self.current_schedule.get('client_name', '업체명') or '업체명'
        food_type = self.current_schedule.get('food_type_name', '식품유형') or '식품유형'
        estimate_date = datetime.now().strftime('%Y%m%d')

        storage_code = self.current_schedule.get('storage_condition', 'room_temp')
        storage_map = {'room_temp': '상온', 'warm': '실온', 'cool': '냉장', 'freeze': '냉동'}
        storage = storage_map.get(storage_code, storage_code)

        test_method = self.current_schedule.get('test_method', 'real')
        method_map = {
            'real': '실측', 'acceleration': '가속',
            'custom_real': '의뢰자요청_실측', 'custom_accel': '의뢰자요청_가속',
            'custom_acceleration': '의뢰자요청_가속'
        }
        method_str = method_map.get(test_method, test_method)

        def sanitize_filename(name):
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '_')
            return name

        filename = f"{client_name}_{food_type}_{estimate_date}_{storage}_{method_str}.pdf"
        filename = sanitize_filename(filename)

        # 저장 경로 결정
        if output_path and os.path.isdir(output_path):
            file_path = os.path.join(output_path, filename)
        else:
            default_path = os.path.expanduser("~/Documents")
            if not os.path.exists(default_path):
                default_path = os.path.expanduser("~")
            file_path = os.path.join(default_path, filename)

        # PDF 생성
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setResolution(300)  # 300 DPI로 고해상도 설정

            page_layout = QPageLayout(
                QPageSize(QPageSize.A4),
                QPageLayout.Portrait,
                QMarginsF(10, 10, 10, 10)
            )
            printer.setPageLayout(page_layout)

            painter = QPainter()
            if painter.begin(printer):
                # 고품질 렌더링 설정
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.TextAntialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

                page_rect = printer.pageRect(QPrinter.DevicePixel)
                widget = self.estimate_container
                widget_width = widget.sizeHint().width() if widget.sizeHint().width() > 0 else widget.width()
                widget_height = widget.sizeHint().height() if widget.sizeHint().height() > 0 else widget.height()

                scale = page_rect.width() / widget_width
                if widget_height * scale > page_rect.height():
                    scale = page_rect.height() / widget_height
                scale = scale * 0.95

                painter.scale(scale, scale)
                widget.render(painter)
                painter.end()

                return file_path
            else:
                QMessageBox.critical(self, "오류", "PDF 생성에 실패했습니다.")
                return None

        except Exception as e:
            QMessageBox.critical(self, "오류", f"PDF 저장 중 오류: {str(e)}")
            return None

    def switch_estimate_type(self, estimate_type):
        """견적서 유형 전환 (1차, 중단, 연장)"""
        self.estimate_type = estimate_type

        # 버튼 스타일 업데이트 (비활성화된 버튼은 disabled 스타일 유지)
        self.first_estimate_btn.setStyleSheet(
            self.btn_active_style if estimate_type == "first" else self.btn_inactive_style
        )

        # 중단 버튼: 활성화된 경우에만 스타일 변경
        if self.suspend_estimate_btn.isEnabled():
            self.suspend_estimate_btn.setStyleSheet(
                self.btn_active_style if estimate_type == "suspend" else self.btn_inactive_style
            )

        # 연장 버튼: 활성화된 경우에만 스타일 변경
        if self.extend_estimate_btn.isEnabled():
            self.extend_estimate_btn.setStyleSheet(
                self.btn_active_style if estimate_type == "extend" else self.btn_inactive_style
            )

        # 현재 스케줄이 있으면 견적서 다시 로드
        if self.current_schedule:
            self.load_schedule_data(self.current_schedule)

    def get_estimate_type_name(self):
        """현재 견적서 유형 이름 반환"""
        type_names = {
            "first": "1차",
            "suspend": "중단",
            "extend": "연장"
        }
        return type_names.get(self.estimate_type, "1차")
