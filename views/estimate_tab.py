# views/estimate_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QGridLayout, QGroupBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
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

        # 스크롤 영역 (세로 스크롤만)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 좌우 스크롤 비활성화
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)     # 세로 스크롤만
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        # 견적서 컨테이너 (전체 너비 사용)
        self.estimate_container = QWidget()
        self.estimate_container.setStyleSheet("background-color: white;")

        self.estimate_layout = QVBoxLayout(self.estimate_container)
        self.estimate_layout.setContentsMargins(50, 30, 50, 30)
        self.estimate_layout.setSpacing(15)

        # 견적서 내용 생성
        self.create_estimate_content()

        scroll_area.setWidget(self.estimate_container)

        main_layout.addWidget(scroll_area)

    def create_estimate_content(self):
        """견적서 내용 생성"""
        # 1. 헤더 (로고 + 견적서 타이틀)
        header_layout = QHBoxLayout()

        # 로고
        logo_label = QLabel("BFL")
        logo_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #1e90ff;
            font-family: Arial;
        """)

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

        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.estimate_layout.addLayout(header_layout)

        # 회사명
        company_label = QLabel("(주) 바이오푸드랩")
        company_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.estimate_layout.addWidget(company_label)

        # 주소/연락처
        address_label = QLabel("#1411 Mario Tower, 28, Digital-ro 30 gil, Guro-gu, Seoul, Korea")
        address_label.setStyleSheet("font-size: 10px; color: #666;")
        self.estimate_layout.addWidget(address_label)

        website_label = QLabel("http://www.biofl.co.kr")
        website_label.setStyleSheet("font-size: 10px; color: #1e90ff;")
        self.estimate_layout.addWidget(website_label)

        # 구분선
        self.add_separator()

        # 2. 견적 정보 테이블
        info_frame = QFrame()
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(5)

        # 왼쪽 정보
        self.estimate_no_label = QLabel("견 적 번 호 :   BFL_소비기한_20250401-2")
        self.estimate_date_label = QLabel("견 적 일 자 :   2025년 04월 01일")
        self.receiver_label = QLabel("수       신 :   ")
        self.sender_label = QLabel("발       신 :   ㈜바이오푸드랩")

        # 오른쪽 정보 (회사 정보)
        right_info = QLabel("""(주)바이오푸드랩
대표이사 이 용 표
서울특별시 구로구 디지털로30길 28
1410호~1414호(구로동,마리오타워)

TEL: (070) 7410-1400
FAX: (070) 7410-1430""")
        right_info.setStyleSheet("font-size: 11px;")

        info_layout.addWidget(self.estimate_no_label, 0, 0)
        info_layout.addWidget(right_info, 0, 1, 4, 1, Qt.AlignRight)
        info_layout.addWidget(self.estimate_date_label, 1, 0)
        info_layout.addWidget(self.receiver_label, 2, 0)
        info_layout.addWidget(self.sender_label, 3, 0)

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
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.items_table.setColumnWidth(0, 40)
        self.items_table.setColumnWidth(1, 100)
        self.items_table.setColumnWidth(3, 80)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setMinimumHeight(200)
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                gridline-color: #ccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 5px;
                font-weight: bold;
            }
        """)

        self.estimate_layout.addWidget(self.items_table)

        # 5. Remark 섹션
        remark_group = QGroupBox("※ Remark")
        remark_layout = QVBoxLayout(remark_group)

        self.remark_text = QTextEdit()
        self.remark_text.setReadOnly(True)
        self.remark_text.setMinimumHeight(150)
        self.remark_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-size: 11px;
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

    def load_schedule_data(self, schedule):
        """스케줄 데이터로 견적서 로드"""
        self.current_schedule = schedule
        if not schedule:
            return

        from datetime import datetime

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

        self.estimate_no_label.setText(f"견 적 번 호 :   BFL_소비기한_{date_str}-{schedule_id}")

        # 견적일자
        self.estimate_date_label.setText(f"견 적 일 자 :   {datetime.now().strftime('%Y년 %m월 %d일')}")

        # 수신 (업체명)
        client_name = schedule.get('client_name', '')
        self.receiver_label.setText(f"수       신 :   {client_name}")

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
        storage = schedule.get('storage_condition', '상온')

        # 실험방법
        test_method = schedule.get('test_method', 'real')
        method_map = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_accel': '의뢰자요청(가속)'
        }
        method_str = method_map.get(test_method, '실측실험')

        # 보고서 종류
        report_parts = []
        if schedule.get('report_interim'):
            report_parts.append("중간보고서")
        if schedule.get('report_korean'):
            report_parts.append("국문")
        if schedule.get('report_english'):
            report_parts.append("영문")

        # 검사항목 (식품유형에서 가져오기)
        test_items = schedule.get('test_items', '관능평가, 세균수, 대장균군')

        # 검사항목 정보 텍스트
        info_text = f"""소비기한: {storage} {period_str}
    ({', '.join(report_parts) if report_parts else '국문'})
실험방법: {method_str}
실험온도: {schedule.get('custom_temperatures', '5,10,15 ℃')}

1)  관능평가
2)  세균수
3)  대장균군
4)  pH"""

        # 테이블에 데이터 추가
        self.items_table.setItem(0, 0, QTableWidgetItem("1."))
        self.items_table.setItem(0, 1, QTableWidgetItem(food_type))

        info_item = QTableWidgetItem(info_text)
        self.items_table.setItem(0, 2, info_item)
        self.items_table.setRowHeight(0, 150)

        # 금액 계산
        total_price = self.calculate_total_price(schedule)
        self.items_table.setItem(0, 3, QTableWidgetItem(f"{total_price:,}"))
        self.items_table.setItem(0, 4, QTableWidgetItem(f"{total_price:,} 원"))

    def calculate_total_price(self, schedule):
        """총 금액 계산"""
        total = 0

        # 검사항목 수수료
        test_items = schedule.get('test_items', '')
        if test_items:
            total += Fee.calculate_total_fee(test_items)

        # 실험방법 수수료
        test_method = schedule.get('test_method', 'real')
        if test_method == 'acceleration':
            # 가속실험 추가 비용
            accel_fee = Fee.get_by_item('가속')
            if accel_fee:
                total += accel_fee['price']
        else:
            real_fee = Fee.get_by_item('실측')
            if real_fee:
                total += real_fee['price']

        # 보고서 수수료
        if schedule.get('report_interim'):
            interim_fee = Fee.get_by_item('중간보고서')
            if interim_fee:
                total += interim_fee['price']

        if schedule.get('report_korean'):
            korean_fee = Fee.get_by_item('완료보고서')
            if korean_fee:
                total += korean_fee['price']

        if schedule.get('report_english'):
            english_fee = Fee.get_by_item('영문')
            if english_fee:
                total += english_fee['price']

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
        sampling_count = schedule.get('sampling_count', 6) or 6
        test_method = schedule.get('test_method', 'real')

        if test_method in ['acceleration', 'custom_accel']:
            zone_count = 3
            zone_text = "3온도"
        else:
            zone_count = 1
            zone_text = "1온도"

        total_samples = sampling_count * zone_count

        remark_text = f"""※ 검체량
→ 검체는 판매 또는 판매 예정인 제품과 동일하게 검사제품을 준비해주시기 바랍니다.
→ 검체량 : 온도구간별({zone_text}) 총 {sampling_count}회씩 실험 = {total_samples}ea
    = > 포장단위 100g 이상 제품 기준 총 {total_samples}ea 이상 준비

※ 검사 소요기간
→ 실험기간 : 48일 + 데이터 분석시간 (약 7일~15일), 소요예정입니다. (3개월 중간보고서)
→ 실험기간 : 90일 + 데이터 분석시간 (약 7일~15일), 소요예정입니다. (6개월 보고서)
약 8~12일에 온도별({zone_text}) 1회씩 실험- 실험스케줄(구간 및 횟수)은 실험결과의 유의성에 따라 변경될 수 있습니다.

※ 제시해 주신 예상소비기한 설정 실험에 대한 견적이며 품질안전한계기간 도달하지 않더라도 실험연장은 불가합니다.
※ 지표항목으로 수정하고 싶으신 항목이 있으시면 연락바랍니다.
※ 견적 금액은 검사비용 외 보관비 및 보고서작성 비용 포함입니다.
※ 실험스케줄 관련 문의사항있으시면 연락바랍니다.
※ 소비기한 검사 중 품질한계 도달로 실험 중단시 중단건까지의 실험발생된 비용만 청구됩니다.
※ 소비기한설정실험은 입금 후 진행됩니다"""

        self.remark_text.setText(remark_text)

    def print_estimate(self):
        """견적서 인쇄"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.estimate_container.render(printer)

    def save_as_pdf(self):
        """PDF로 저장"""
        QMessageBox.information(self, "알림", "PDF 저장 기능은 추후 구현 예정입니다.")

    def save_as_excel(self):
        """엑셀로 저장"""
        QMessageBox.information(self, "알림", "엑셀 저장 기능은 추후 구현 예정입니다.")
