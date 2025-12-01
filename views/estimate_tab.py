# views/estimate_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QGridLayout, QGroupBox, QTextEdit, QMessageBox,
    QLineEdit, QSizePolicy
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
        self.initUI()

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

        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.pdf_btn)
        button_layout.addWidget(self.excel_btn)
        button_layout.addStretch()

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

        main_layout.addWidget(scroll_area)

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

        # 회사명 (설정에서 불러옴)
        self.header_company_label = QLabel("(주) 바이오푸드랩")
        self.header_company_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.estimate_layout.addWidget(self.header_company_label)

        # 주소/연락처 (설정에서 불러옴)
        self.header_address_label = QLabel("")
        self.header_address_label.setStyleSheet("font-size: 10px; color: #666;")
        self.estimate_layout.addWidget(self.header_address_label)

        website_label = QLabel("http://www.biofl.co.kr")
        website_label.setStyleSheet("font-size: 10px; color: #1e90ff;")
        self.estimate_layout.addWidget(website_label)

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

        # 오른쪽 정보 (회사 정보 - 설정에서 불러옴)
        right_info_widget = QWidget()
        right_info_layout = QHBoxLayout(right_info_widget)
        right_info_layout.setContentsMargins(0, 0, 0, 0)
        right_info_layout.setSpacing(10)

        self.right_company_info = QLabel("")
        self.right_company_info.setStyleSheet("font-size: 11px;")

        # 직인 이미지
        self.stamp_label = QLabel("")
        self.stamp_label.setFixedSize(60, 60)
        self.stamp_label.setStyleSheet("border: none;")

        right_info_layout.addWidget(self.right_company_info)
        right_info_layout.addWidget(self.stamp_label)

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

        # 5. Remark 섹션 (스크롤 없이 전체 표시)
        remark_group = QGroupBox("※ Remark")
        remark_layout = QVBoxLayout(remark_group)

        self.remark_text = QLabel()
        self.remark_text.setWordWrap(True)
        self.remark_text.setStyleSheet("""
            QLabel {
                font-size: 11px;
                line-height: 1.4;
                padding: 5px;
            }
        """)
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
            cursor.execute("SELECT key, value FROM settings")
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

            # 로고 이미지 로드
            logo_path = settings_dict.get('logo_path', '')
            if logo_path and os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # 로고 크기 조정 (높이 60px 기준으로 비율 유지)
                    scaled_pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setStyleSheet("")  # 기존 텍스트 스타일 제거
            else:
                # 기본 텍스트 로고
                self.logo_label.setText("BFL")
                self.logo_label.setStyleSheet("""
                    font-size: 36px;
                    font-weight: bold;
                    color: #1e90ff;
                    font-family: Arial;
                """)

            # 직인 이미지 로드
            stamp_path = settings_dict.get('stamp_path', '')
            if stamp_path and os.path.exists(stamp_path):
                stamp_pixmap = QPixmap(stamp_path)
                if not stamp_pixmap.isNull():
                    # 직인 크기 조정 (60x60px)
                    scaled_stamp = stamp_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.stamp_label.setPixmap(scaled_stamp)
            else:
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

        # 회사 정보 로드
        self.load_company_info()

        # 견적번호
        schedule_id = schedule.get('id', '')
        created_at = schedule.get('created_at', '')
        if created_at:
            try:
                date_obj = datetime.strptime(created_at[:10], '%Y-%m-%d')
                date_str = date_obj.strftime('%Y%m%d')
            except:
                date_str = datetime.now().strftime('%Y%m%d')
        else:
            date_str = datetime.now().strftime('%Y%m%d')

        self.estimate_no_input.setText(f"BFL_소비기한_{date_str}-{schedule_id}")

        # 견적일자
        self.estimate_date_input.setText(f"{datetime.now().strftime('%Y년 %m월 %d일')}")

        # 수신 (업체명)
        client_name = schedule.get('client_name', '')
        self.receiver_input.setText(client_name)

        # 견적 명칭
        self.title_value.setText("소비기한설정시험의 건")

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

    def calculate_total_price(self, schedule):
        """총 금액 계산 - 스케줄 관리에서 전달받은 비용 데이터 사용"""
        # 스케줄 관리에서 계산된 비용 정보가 있으면 그대로 사용
        if schedule.get('total_rounds_cost') is not None and schedule.get('report_cost') is not None:
            total_rounds_cost = schedule.get('total_rounds_cost', 0) or 0
            report_cost = schedule.get('report_cost', 0) or 0
            interim_report_cost = schedule.get('interim_report_cost', 0) or 0

            # 가속 실험인 경우 온도 구간 수(3) 적용
            test_method = schedule.get('test_method', 'real')
            if test_method in ['acceleration', 'custom_acceleration', 'custom_accel']:
                zone_count = 3
            else:
                zone_count = 1

            total = (total_rounds_cost * zone_count) + report_cost + interim_report_cost
            return int(total)

        # 전달받은 비용 정보가 없으면 기존 방식으로 계산 (호환성 유지)
        total = 0

        # 실험방법 확인
        test_method = schedule.get('test_method', 'real')
        sampling_count = schedule.get('sampling_count', 6) or 6

        # 온도 구간 수 결정 (실측=1구간, 가속=3구간)
        if test_method in ['real', 'custom_real']:
            zone_count = 1
        else:
            zone_count = 3

        # 검사항목 수수료 계산
        test_items = schedule.get('test_items', '')
        if test_items:
            # 검사항목별 수수료 합계
            item_cost = Fee.calculate_total_fee(test_items)
            # 회차별 총계 × 구간수
            total += item_cost * sampling_count * zone_count

        # 보고서 비용 (실측: 200,000원, 가속: 300,000원)
        if test_method in ['real', 'custom_real']:
            report_cost = 200000
        else:
            report_cost = 300000
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
            except:
                pass

        # 소비기한 개월 수 계산
        total_months = test_period_months + (test_period_years * 12)
        if test_period_days >= 15:
            total_months += 1

        # 검사 소요기간 문구 생성
        report_interim = schedule.get('report_interim', False)

        test_period_text = ""
        # 중간보고서가 체크된 경우에만 중간보고서 라인 추가
        if report_interim:
            interim_date_text = f" / {interim_expected_date}" if interim_expected_date else ""
            test_period_text += f"→ 실험 기간 : {interim_experiment_days}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. ({total_months // 2}개월 중간 보고서{interim_date_text})\n"

        # 최종 보고서 라인
        final_date_text = f" / {final_expected_date}" if final_expected_date else ""
        test_period_text += f"→ 실험 기간 : {total_experiment_days}일 + 데이터 분석시간(약 7일~15일) 소요 예정입니다. (최종 보고서{final_date_text})"

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

* 소비기한 설정 실험은 입금 후 진행되며, 검사 중 품질한계 도달로 실험 중단 시, 중단 전까지의 비용 청구됩니다."""

        self.remark_text.setText(remark_text)

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
            cursor.execute("SELECT value FROM settings WHERE key = 'output_path'")
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
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)

            # A4 사이즈 설정
            page_layout = QPageLayout(
                QPageSize(QPageSize.A4),
                QPageLayout.Portrait,
                QMarginsF(10, 10, 10, 10)  # 여백 설정 (mm)
            )
            printer.setPageLayout(page_layout)

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

                # 왼쪽 상단에서 시작
                painter.scale(scale, scale)
                widget.render(painter)
                painter.end()

                QMessageBox.information(self, "저장 완료", f"PDF가 저장되었습니다.\n\n{file_path}")
            else:
                QMessageBox.critical(self, "오류", "PDF 생성에 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"PDF 저장 중 오류가 발생했습니다:\n{str(e)}")

    def save_as_excel(self):
        """엑셀로 저장"""
        QMessageBox.information(self, "알림", "엑셀 저장 기능은 추후 구현 예정입니다.")
