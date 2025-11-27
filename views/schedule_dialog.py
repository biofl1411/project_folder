# schedule_dialog.py
from database import get_connection
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLineEdit, QPushButton, QTextEdit, QDateEdit,
    QComboBox, QLabel, QMessageBox, QWidget, QRadioButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QButtonGroup,
    QFrame, QApplication, QCheckBox
)
from PyQt5.QtCore import QDate, Qt, QTranslator, QEvent

# 온도 레이블 상수 정의
ROOM_TEMP_LABEL = "상온 (15℃)"
COOL_TEMP_LABEL = "냉장 (10℃)"
FREEZE_TEMP_LABEL = "냉동 (-18℃ 이하)"
WARM_TEMP_LABEL = "실온 (25℃)"
CUSTOM_TEMP_LABEL = "의뢰자 요청 온도"

ROOM_TEMP_ACCEL_LABEL = "상온 (15℃, 25℃, 35℃)"
WARM_TEMP_ACCEL_LABEL = "실온 (25℃, 35℃, 45℃)"
COOL_TEMP_ACCEL_LABEL = "냉장 (5℃, 10℃, 15℃)"
FREEZE_TEMP_ACCEL_LABEL = "냉동 (-6℃, -12℃, -18℃)"
CUSTOM_TEMP_ACCEL_LABEL = "의뢰자 요청 온도"

# 스케줄 생성 함수

def create_new_schedule(self):
    """새 스케줄 작성 다이얼로그 표시"""
    try:
        dialog = ScheduleCreateDialog(self)
        if dialog.exec_():
            self.load_schedules()
    except Exception as e:
        import traceback
        QMessageBox.critical(self, "오류", f"스케줄 생성 중 오류 발생:\n{e}\n{traceback.format_exc()}")


class FoodTypeSelectionDialog(QDialog):
    """식품 유형을 검색 및 선택하는 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("식품 유형 선택")
        self.resize(400, 500)

        # 검색 입력 필드 및 버튼
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("검색어 입력...")
        self.search_button = QPushButton("검색", self)
        self.search_button.setAutoDefault(False)
        self.search_button.setDefault(False)

        # 테이블 위젯 설정
        self.food_type_table = QTableWidget(self)
        self.food_type_table.setColumnCount(7)
        self.food_type_table.setHorizontalHeaderLabels([
            "ID", "식품 유형명", "카테고리", "살균여부",
            "멸균여부", "성상", "검사항목"
        ])
        self.food_type_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.food_type_table.setSelectionMode(QTableWidget.SingleSelection)
        self.food_type_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 테이블 더블클릭 시그널 연결
        self.food_type_table.doubleClicked.connect(self.accept_selection)

        # 선택/취소 버튼
        self.select_button = QPushButton("선택", self)
        self.select_button.setAutoDefault(False)
        self.select_button.setDefault(False)
        self.cancel_button = QPushButton("취소", self)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)

        # 레이아웃 구성
        main_layout = QVBoxLayout(self)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:", self))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.food_type_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # 시그널 연결
        self.search_button.clicked.connect(self.search_food_types)
        self.select_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
        
        # 엔터 키 이벤트 추가
        self.search_input.returnPressed.connect(self.search_food_types)

        # 초기 식품 유형 목록 로드
        self.load_food_types()
        
        # 검색어 초기화
        self.search_text = ""

    def load_food_types(self):
        """데이터베이스에서 모든 식품 유형 불러오기"""
        try:
            from models.product_types import ProductType
            
            # 데이터베이스에서 모든 식품 유형 불러오기
            food_types = ProductType.get_all()
            
            self.display_food_types(food_types)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"식품 유형을 불러오는 중 오류 발생: {str(e)}")
    
    def search_food_types(self):
        """검색어로 식품 유형 검색"""
        search_text = self.search_input.text().strip()
        self.search_text = search_text  # 검색어 저장
        
        if not search_text:
            self.load_food_types()  # 검색어가 비어있으면 전체 목록 표시
            return
        
        try:
            from models.product_types import ProductType
            food_types = ProductType.search(search_text)
            self.display_food_types(food_types)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"식품 유형 검색 중 오류 발생: {str(e)}")
    
    def display_food_types(self, food_types):
        """식품 유형 목록을 테이블에 표시"""
        self.food_type_table.setRowCount(0)  # 테이블 초기화
        
        try:
            # 데이터 추가
            for row_index, food_type in enumerate(food_types):
                self.food_type_table.insertRow(row_index)
                
                # 기본 필드
                food_type_id = ""
                food_type_name = ""
                category = ""
                sterilization = ""
                pasteurization = ""
                appearance = ""
                test_items = ""
                
                # 데이터베이스 결과 형식에 따라 조정
                if isinstance(food_type, dict):
                    # 딕셔너리인 경우
                    food_type_id = str(food_type.get('id', ''))
                    food_type_name = food_type.get('type_name', '')
                    category = food_type.get('category', '')
                    sterilization = food_type.get('sterilization', '')
                    pasteurization = food_type.get('pasteurization', '')
                    appearance = food_type.get('appearance', '')
                    test_items = food_type.get('test_items', '')
                elif hasattr(food_type, 'keys'):  # sqlite3.Row 객체 확인
                    # sqlite3.Row 객체인 경우
                    try:
                        food_type_id = str(food_type['id'])
                        food_type_name = food_type['type_name']
                        if 'category' in food_type.keys(): category = food_type['category']
                        if 'sterilization' in food_type.keys(): sterilization = food_type['sterilization']
                        if 'pasteurization' in food_type.keys(): pasteurization = food_type['pasteurization']
                        if 'appearance' in food_type.keys(): appearance = food_type['appearance']
                        if 'test_items' in food_type.keys(): test_items = food_type['test_items']
                    except Exception as e:
                        print(f"sqlite3.Row 처리 중 오류: {str(e)}")
                else:
                    # 튜플인 경우
                    try:
                        food_type_id = str(food_type[0])
                        food_type_name = str(food_type[1])
                        if len(food_type) > 2: category = str(food_type[2])
                        if len(food_type) > 3: sterilization = str(food_type[3])
                        if len(food_type) > 4: pasteurization = str(food_type[4])
                        if len(food_type) > 5: appearance = str(food_type[5])
                        if len(food_type) > 6: test_items = str(food_type[6])
                    except Exception as e:
                        print(f"튜플 처리 중 오류: {str(e)}")
                
                # 테이블에 데이터 설정
                self.food_type_table.setItem(row_index, 0, QTableWidgetItem(food_type_id))
                self.food_type_table.setItem(row_index, 1, QTableWidgetItem(food_type_name))
                self.food_type_table.setItem(row_index, 2, QTableWidgetItem(category))
                self.food_type_table.setItem(row_index, 3, QTableWidgetItem(sterilization))
                self.food_type_table.setItem(row_index, 4, QTableWidgetItem(pasteurization))
                self.food_type_table.setItem(row_index, 5, QTableWidgetItem(appearance))
                self.food_type_table.setItem(row_index, 6, QTableWidgetItem(test_items))
            
            # 컬럼 너비 조정
            self.food_type_table.resizeColumnsToContents()
            
            # 데이터가 없는 경우 메시지 표시
            if self.food_type_table.rowCount() == 0:
                QMessageBox.information(self, "알림", "검색 결과가 없습니다.")
                
        except Exception as e:
            import traceback
            error_msg = f"식품 유형 표시 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)
    
    def accept_selection(self):
        """선택한 항목을 저장하고 다이얼로그 수락"""
        selected_indexes = self.food_type_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "경고", "식품 유형을 선택해주세요.")
            return
        
        # 선택된 행 정보 가져오기
        row = selected_indexes[0].row()
        food_type_id = self.food_type_table.item(row, 0).text()
        food_type_name = self.food_type_table.item(row, 1).text()
        category = self.food_type_table.item(row, 2).text() if self.food_type_table.item(row, 2) else ""
        sterilization = self.food_type_table.item(row, 3).text() if self.food_type_table.item(row, 3) else ""
        pasteurization = self.food_type_table.item(row, 4).text() if self.food_type_table.item(row, 4) else ""
        appearance = self.food_type_table.item(row, 5).text() if self.food_type_table.item(row, 5) else ""
        test_items = self.food_type_table.item(row, 6).text() if self.food_type_table.item(row, 6) else ""
        
        # 선택된 식품 유형 저장 (모든 정보를 포함)
        self.selected_food_type = {
            'id': food_type_id, 
            'type_name': food_type_name,
            'category': category,
            'sterilization': sterilization,
            'pasteurization': pasteurization,
            'appearance': appearance,
            'test_items': test_items
        }
        
        self.accept()

class ScheduleCreateDialog(QDialog):
    """스케줄 생성 다이얼로그 - 제품 정보 자동 채우기 기능 개선"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("스케줄 작성")
        self.resize(600, 700)
        
        # 온도 상수 정의 - 인스턴스 변수로 추가
        # 실측실험 온도
        self.ROOM_TEMP_LABEL = "상온 (15℃)"
        self.COOL_TEMP_LABEL = "냉장 (10℃)"
        self.FREEZE_TEMP_LABEL = "냉동 (-18℃ 이하)"
        self.WARM_TEMP_LABEL = "실온 (25℃)"
        self.CUSTOM_TEMP_LABEL = "의뢰자 요청 온도"

        # 가속실험 온도
        self.ROOM_TEMP_ACCEL_LABEL = "상온 (15℃, 25℃, 35℃)"
        self.WARM_TEMP_ACCEL_LABEL = "실온 (25℃, 35℃, 45℃)"
        self.COOL_TEMP_ACCEL_LABEL = "냉장 (5℃, 10℃, 15℃)"
        self.FREEZE_TEMP_ACCEL_LABEL = "냉동 (-6℃, -12℃, -18℃)"
        self.CUSTOM_TEMP_ACCEL_LABEL = "의뢰자 요청 온도"
        
        # 한국어 번역기 설정
        self.translator = QTranslator()
        self.translator.load('ko_KR', ':/translations/')
        QApplication.instance().installTranslator(self.translator)
        
        # 레이아웃 설정
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 업체 정보 영역 수정
        client_group = QGroupBox("업체 정보")
        client_layout = QFormLayout()
        client_group.setLayout(client_layout)

        # 업체명 입력 및 검색
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("업체명 검색...")
        self.client_search_btn = QPushButton("검색")
        self.client_search_btn.setAutoDefault(False)  # 엔터 키 자동 실행 방지
        self.client_search_btn.setDefault(False)
        self.client_detail_btn = QPushButton("신규 등록")
        self.client_detail_btn.setAutoDefault(False)
        self.client_detail_btn.setDefault(False)

        client_search_layout = QHBoxLayout()
        client_search_layout.addWidget(self.client_input)
        client_search_layout.addWidget(self.client_search_btn)
        client_search_layout.addWidget(self.client_detail_btn)
        client_layout.addRow("업체명:", client_search_layout)

        # 업체 정보 표시 - 새로운 필드 추가
        self.client_ceo_label = QLabel("- ")  # 대표자 정보
        client_layout.addRow("대표자:", self.client_ceo_label)

        self.client_name_label = QLabel("- ")  # 담당명
        client_layout.addRow("담당명:", self.client_name_label)

        self.client_contact_label = QLabel("- ")  # 담당자
        client_layout.addRow("담당자:", self.client_contact_label)

        self.client_phone_label = QLabel("- ")  # 연락처
        client_layout.addRow("연락처:", self.client_phone_label)

        self.client_sales_label = QLabel("- ")  # 영업담당자 정보
        client_layout.addRow("영업담당자:", self.client_sales_label)

        self.main_layout.addWidget(client_group)
            
        # 실험 정보 영역
        test_group = QGroupBox("실험 정보")
        test_layout = QFormLayout()
        test_group.setLayout(test_layout)
        
        # 실험 방법 라디오 버튼 - 4가지 옵션으로 확장
        test_method_layout = QHBoxLayout()
        self.test_method_real = QRadioButton("실측실험")
        self.test_method_acceleration = QRadioButton("가속실험")
        self.test_method_custom_real = QRadioButton("의뢰자 요청(실측)")
        self.test_method_custom_accel = QRadioButton("의뢰자 요청(가속)")
        
        # 라디오 버튼 그룹화
        self.test_method_group = QButtonGroup()
        self.test_method_group.addButton(self.test_method_real)
        self.test_method_group.addButton(self.test_method_acceleration)
        self.test_method_group.addButton(self.test_method_custom_real)
        self.test_method_group.addButton(self.test_method_custom_accel)
        
        # 기본값 설정
        self.test_method_real.setChecked(True)
        
        test_method_layout.addWidget(self.test_method_real)
        test_method_layout.addWidget(self.test_method_acceleration)
        test_method_layout.addWidget(self.test_method_custom_real)
        test_method_layout.addWidget(self.test_method_custom_accel)
        test_layout.addRow("실험방법(필수):", test_method_layout)
        
        # 보관 조건 라디오 버튼
        storage_layout = QHBoxLayout()
        self.storage_room_temp = QRadioButton("상온")
        self.storage_warm = QRadioButton("실온")
        self.storage_cool = QRadioButton("냉장")
        self.storage_freeze = QRadioButton("냉동")
        
        # 라디오 버튼 그룹화
        self.storage_group = QButtonGroup()
        self.storage_group.addButton(self.storage_room_temp)
        self.storage_group.addButton(self.storage_warm)
        self.storage_group.addButton(self.storage_cool)
        self.storage_group.addButton(self.storage_freeze)
        
        # 기본값 설정
        self.storage_room_temp.setChecked(True)
        
        storage_layout.addWidget(self.storage_room_temp)
        storage_layout.addWidget(self.storage_warm)
        storage_layout.addWidget(self.storage_cool)
        storage_layout.addWidget(self.storage_freeze)
        test_layout.addRow("보관조건(필수):", storage_layout)
        
        # 보관 온도 (읽기 전용)
        self.storage_temp_label = QLabel(self.ROOM_TEMP_LABEL)
        self.storage_temp_label.setStyleSheet("color: blue; font-weight: bold;")
        test_layout.addRow("실험 온도:", self.storage_temp_label)
        
        # 의뢰 예상일
        self.expected_date = QDateEdit()
        self.expected_date.setDate(QDate.currentDate())
        self.expected_date.setCalendarPopup(True)
        test_layout.addRow("의뢰 예상일(필수):", self.expected_date)
        
        # 실험 시작일
        self.test_start_date = QDateEdit()
        self.test_start_date.setDate(QDate.currentDate())
        self.test_start_date.setCalendarPopup(True)
        test_layout.addRow("실험 시작일(필수):", self.test_start_date)
        
        # "설정 기간" 라벨을 "소비기한"으로 변경하고 UI 구성
        period_layout = QHBoxLayout()
                
        # 일 선택
        days_layout = QHBoxLayout()
        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 365)
        self.days_spin.setValue(0)
        days_layout.addWidget(self.days_spin)
        days_layout.addWidget(QLabel("일"))
                
        # 월 선택
        months_layout = QHBoxLayout()
        self.months_spin = QSpinBox()
        self.months_spin.setRange(0, 60)
        self.months_spin.setValue(0)
        months_layout.addWidget(self.months_spin)
        months_layout.addWidget(QLabel("개월"))
                
        # 년 선택
        years_layout = QHBoxLayout()
        self.years_spin = QSpinBox()
        self.years_spin.setRange(0, 10)
        self.years_spin.setValue(0)
        years_layout.addWidget(self.years_spin)
        years_layout.addWidget(QLabel("년"))
                
        # 각 기간 입력을 레이아웃에 추가
        period_layout.addLayout(days_layout)
        period_layout.addLayout(months_layout)
        period_layout.addLayout(years_layout)
        period_layout.addStretch()
                
        test_layout.addRow("소비기한:", period_layout)

        # 실험기간 표시용 레이블 추가
        self.experiment_period_label = QLabel("0일 0개월 0년")
        self.experiment_period_label.setStyleSheet("color: blue; font-weight: bold;")
        test_layout.addRow("실험기간:", self.experiment_period_label)
        
        # 실험기간 표시용 레이블 추가하는 코드 이후에 추가할 부분:

        # 보고서 종류 체크박스 그룹 추가
        report_type_frame = QFrame()
        report_type_layout = QHBoxLayout(report_type_frame)
        report_type_layout.setContentsMargins(0, 0, 0, 0)

        # 세 가지 체크박스 생성
        self.report_type_interim = QCheckBox("중간")
        self.report_type_korean = QCheckBox("국문")
        self.report_type_english = QCheckBox("영문")

        # 기본값으로 국문 체크
        self.report_type_korean.setChecked(True)

        # 레이아웃에 체크박스 추가
        report_type_layout.addWidget(self.report_type_interim)
        report_type_layout.addWidget(self.report_type_korean)
        report_type_layout.addWidget(self.report_type_english)
        report_type_layout.addStretch()

        # 폼 레이아웃에 추가
        test_layout.addRow("보고서 종류:", report_type_frame)
        
        # 샘플링 횟수 설정
        sampling_layout = QHBoxLayout()
        
        # 기본값 체크박스
        self.default_sampling_check = QCheckBox("기본값 사용 (6회)")
        self.default_sampling_check.setChecked(True)
        
        # 사용자 정의 입력
        self.sampling_spin = QSpinBox()
        self.sampling_spin.setRange(1, 30)
        self.sampling_spin.setValue(6)
        self.sampling_spin.setEnabled(False)  # 처음에는 비활성화
        
        sampling_layout.addWidget(self.default_sampling_check)
        sampling_layout.addWidget(self.sampling_spin)
        sampling_layout.addWidget(QLabel("회"))
        sampling_layout.addStretch()
        
        test_layout.addRow("샘플링 횟수:", sampling_layout)
         
        # 연장실험 옵션 레이아웃
        extension_layout = QHBoxLayout()

        # 연장실험 체크박스 생성
        self.extension_check = QCheckBox("진행")
        self.extension_check.setChecked(False)  # 기본값은 체크 해제 (미진행)

        # 미진행 레이블 (체크박스 상태에 따라 표시)
        self.extension_status_label = QLabel("미진행")
        self.extension_status_label.setStyleSheet("color: gray;")

        # 레이아웃에 위젯 추가
        extension_layout.addWidget(self.extension_check)
        extension_layout.addWidget(self.extension_status_label)
        extension_layout.addStretch()

        # 폼 레이아웃에 추가
        test_layout.addRow("연장실험:", extension_layout)

        # 체크박스 상태 변경 시 레이블 업데이트를 위한 함수 연결
        self.extension_check.stateChanged.connect(self.update_extension_status)
        
        # 실험 정보 영역 추가
        self.main_layout.addWidget(test_group)
        
        # 제품 정보 영역 수정
        product_group = QGroupBox("제품 정보")
        product_layout = QFormLayout()
        product_group.setLayout(product_layout)

        # 제품명
        self.product_name_input = QLineEdit()
        product_layout.addRow("제품명:", self.product_name_input)

        # 식품 유형 콤보박스와 선택 버튼
        food_type_layout = QHBoxLayout()
        self.food_type_combo = QComboBox()
        self.food_type_combo.setEditable(True)
        self.food_type_combo.setPlaceholderText("식품유형 입력 또는 검색")

        # 식품 유형 선택 버튼 추가
        self.food_type_select_btn = QPushButton("검색")
        self.food_type_select_btn.setAutoDefault(False)
        self.food_type_select_btn.setDefault(False)
        food_type_layout.addWidget(self.food_type_combo)
        food_type_layout.addWidget(self.food_type_select_btn)
        product_layout.addRow("식품유형:", food_type_layout)

        # 성상
        self.appearance_input = QLineEdit()
        product_layout.addRow("성상:", self.appearance_input)

        # 단서조항_1
        self.sterilization_input = QLineEdit()
        product_layout.addRow("단서조항_1:", self.sterilization_input)

        # 단서조항_2
        self.pasteurization_input = QLineEdit()
        product_layout.addRow("단서조항_2:", self.pasteurization_input)

        # 검사 항목
        self.test_items_layout = QHBoxLayout()
        self.test_items_label = QLabel("관능평가, 대장균(정량), 세균수, 총아플라톡신")
        self.test_items_label.setStyleSheet("color: blue; text-decoration: underline;")
        test_items_links = QPushButton("항목링크")
        self.test_items_layout.addWidget(self.test_items_label)
        self.test_items_layout.addWidget(test_items_links)
        product_layout.addRow("검사항목:", self.test_items_layout)

        # 제품 정보 그룹을 메인 레이아웃에 추가
        self.main_layout.addWidget(product_group)
        
        # 버튼 영역 - 버튼 객체를 먼저 생성하고 할당
        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton("미리보기")
        self.preview_btn.setAutoDefault(False)
        self.preview_btn.setDefault(False)
        self.save_btn = QPushButton("저장")
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setDefault(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addLayout(button_layout)
        
        # 필요한 변수 초기화
        self.selected_client_id = None
        self.selected_food_type_id = None
                    
        # 모든 시그널 연결
        self.connect_signals()
        
    def update_start_date(self, date):
        """의뢰 예상일이 변경되면 실험 시작일도 동일하게 변경"""
        self.test_start_date.setDate(date)
        
    def toggle_sampling_input(self, state):
        """샘플링 기본값 사용 여부에 따라 입력 필드 활성화/비활성화"""
        self.sampling_spin.setEnabled(not state)
        if state:
            self.sampling_spin.setValue(6)  # 기본값으로 복원

    def connect_signals(self):
        """모든 시그널 연결을 한 곳에서 처리"""
        # 클라이언트 관련
        self.client_search_btn.clicked.connect(self.search_client)
        self.client_detail_btn.clicked.connect(self.add_new_client)
        
        # 식품 유형 관련
        self.food_type_combo.currentIndexChanged.connect(self.update_food_type_info)
        self.food_type_select_btn.clicked.connect(self.select_food_type)
        self.food_type_combo.lineEdit().returnPressed.connect(self.select_food_type)
        
        # 소비기한 관련
        self.days_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "days"))
        self.months_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "months"))
        self.years_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "years"))
        
        # 실험 방법 관련 - 실험기간 업데이트 연결
        self.test_method_real.toggled.connect(self.update_test_method)
        self.test_method_acceleration.toggled.connect(self.update_test_method)
        self.test_method_custom_real.toggled.connect(self.update_test_method)
        self.test_method_custom_accel.toggled.connect(self.update_test_method)
            
        # 설정 기간 관련
        self.days_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "days"))
        self.months_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "months"))
        self.years_spin.valueChanged.connect(lambda value: self.period_value_changed(value, "years"))
        
        # 보관 조건 관련
        self.storage_room_temp.toggled.connect(self.update_storage_temp)
        self.storage_cool.toggled.connect(self.update_storage_temp)
        self.storage_freeze.toggled.connect(self.update_storage_temp)
        self.storage_warm.toggled.connect(self.update_storage_temp)
        
        # 날짜 관련
        self.expected_date.dateChanged.connect(self.update_start_date)
        
        # 샘플링 관련
        self.default_sampling_check.stateChanged.connect(self.toggle_sampling_input)
        
        # 버튼 관련
        self.preview_btn.clicked.connect(self.preview_schedule)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def select_food_type(self):
        """식품 유형 선택 다이얼로그 표시 및 선택 정보 자동 채우기"""
        try:
            print("식품 유형 선택 시작")
            
            # 현재 입력된 검색어 가져오기
            search_text = self.food_type_combo.currentText().strip()
            
            # FoodTypeSelectionDialog 생성
            dialog = FoodTypeSelectionDialog(self)
            
            # 검색어 설정 - 대화상자가 생성된 후에 설정
            if search_text:
                dialog.search_input.setText(search_text)
                # 즉시 검색 실행
                dialog.search_food_types()
            
            # 다이얼로그 실행
            if dialog.exec_():
                # 선택된 식품 유형 정보 가져오기
                selected_food_type = dialog.selected_food_type
                print(f"선택된 식품 유형: {selected_food_type}")
                
                # 식품 유형 정보 자동 채우기
                self.fill_food_type_info(selected_food_type)
        except Exception as e:
            import traceback
            error_msg = f"식품 유형 선택 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)

    def fill_food_type_info(self, food_type_data):
        """선택된 식품 유형 정보로 폼 필드 채우기"""
        try:
            if isinstance(food_type_data, dict):
                # 식품 유형 콤보박스에 이름 설정
                self.food_type_combo.setCurrentText(food_type_data.get('type_name', ''))
                
                # 식품 유형 ID 저장
                self.selected_food_type_id = food_type_data.get('id', '')
                
                # 각 필드에 정보 채우기
                self.sterilization_input.setText(food_type_data.get('sterilization', ''))
                self.pasteurization_input.setText(food_type_data.get('pasteurization', ''))
                self.appearance_input.setText(food_type_data.get('appearance', ''))
                self.test_items_label.setText(food_type_data.get('test_items', ''))
                
                print(f"식품 유형 정보 채우기 완료: {food_type_data.get('type_name', '')}")
            else:
                print(f"식품 유형 데이터 형식 오류: {type(food_type_data)}")
        except Exception as e:
            print(f"식품 유형 정보 채우기 중 오류 발생: {str(e)}")

    def update_food_type_info(self):
        """콤보박스에서 선택된 식품 유형에 따른 정보 업데이트"""
        try:
            food_type_name = self.food_type_combo.currentText().strip()
            if not food_type_name:
                return
            
            # 입력된 텍스트로 식품 유형 검색
            from models.product_types import ProductType
            
            # 정확히 일치하는 항목 먼저 확인
            food_type = ProductType.get_by_name(food_type_name)
            
            # 정확히 일치하는 항목이 없으면 부분 일치 검색
            if not food_type:
                food_types = ProductType.search(food_type_name)
                if food_types:
                    if len(food_types) == 1:
                        # 검색 결과가 하나면 자동 선택
                        food_type = food_types[0]
                        self.fill_food_type_info(food_type)
                    else:
                        # 검색 결과가 여러 개면 선택 다이얼로그 표시 (선택 사항)
                        # 여기서는 자동으로 다이얼로그를 띄우지 않고 사용자가 검색 버튼을 클릭하도록 함
                        return
                else:
                    print(f"'{food_type_name}' 일치하는 식품 유형이 없습니다.")
                    return
            else:
                # 일치하는 항목을 찾았으면 정보 채우기
                self.fill_food_type_info(food_type)
                
        except Exception as e:
            print(f"식품 유형 정보 업데이트 중 오류 발생: {str(e)}")
            
   # ScheduleCreateDialog 클래스 내부의 search_client 함수 수정
    # search_client 및 add_new_client 함수 수정
    def search_client(self):
        """업체 검색 다이얼로그 표시"""
        try:
            print("업체 검색 시작")  # 로그 기록
            
            # 안전하게 ClientSearchDialog 클래스 존재 여부 확인
            try:
                # 상대 경로 임포트 시도
                from .client_dialog import ClientSearchDialog
                dialog_exists = True
                print("ClientSearchDialog 클래스 임포트 성공")
            except (ImportError, ModuleNotFoundError):
                dialog_exists = False
                print("ClientSearchDialog 클래스를 찾을 수 없음 - 임시 모드 사용")
            
            if dialog_exists:
                # 실제 다이얼로그 사용
                dialog = ClientSearchDialog(self)
                if dialog.exec_():
                    # 선택된 업체 정보 가져오기
                    client_id, client_data = dialog.selected_client
                    
                    # 업체 정보 설정
                    self.selected_client_id = client_id
                    self.client_input.setText(client_data.get('name', ''))
                    self.client_name_label.setText(client_data.get('manager_name', '-'))
                    self.client_contact_label.setText(client_data.get('contact_person', '-'))
                    self.client_phone_label.setText(client_data.get('phone', '-'))
                    
                    print(f"업체 검색 완료: {client_data.get('name', '')}")
            else:
                # 임시 구현
                QMessageBox.information(self, "업체 검색", "업체 검색 기능은 아직 구현 중입니다.")
                
                # 임시 데이터로 필드 채우기
                self.client_input.setText("테스트 업체")
                self.client_name_label.setText("홍길동")
                self.client_contact_label.setText("담당자명")
                self.client_phone_label.setText("010-1234-5678")
                self.selected_client_id = 1  # 임시 ID
                print("임시 업체 데이터 설정 완료")
        except Exception as e:
            import traceback
            error_msg = f"업체 검색 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)

    # ScheduleCreateDialog 클래스 내부의 add_new_client 함수 수정
    def add_new_client(self):
        """새 업체 등록 다이얼로그 표시"""
        try:
            print("업체 등록 시작")  # 로그 기록
            
            # 안전하게 ClientDialog 클래스 존재 여부 확인
            try:
                # 상대 경로 임포트 시도
                from .client_dialog import ClientDialog
                dialog_exists = True
                print("ClientDialog 클래스 임포트 성공")
            except (ImportError, ModuleNotFoundError):
                dialog_exists = False
                print("ClientDialog 클래스를 찾을 수 없음 - 임시 모드 사용")
            
            if dialog_exists:
                # 실제 다이얼로그 사용
                dialog = ClientDialog(self)
                if dialog.exec_():
                    # 신규 등록된 업체 정보 가져오기
                    client_id = dialog.client_id
                    client_data = dialog.client_data
                    
                    # 업체 정보 설정
                    self.selected_client_id = client_id
                    self.client_input.setText(client_data.get('name', ''))
                    self.client_name_label.setText(client_data.get('manager_name', '-'))
                    self.client_contact_label.setText(client_data.get('contact_person', '-'))
                    self.client_phone_label.setText(client_data.get('phone', '-'))
                    
                    print(f"새 업체 등록 완료: {client_data.get('name', '')}")
            else:
                # 임시 구현
                QMessageBox.information(self, "업체 등록", "업체 등록 기능은 아직 구현 중입니다.")
                
                # 임시 데이터로 필드 채우기
                self.client_input.setText("신규 업체")
                self.client_name_label.setText("새담당자")
                self.client_contact_label.setText("새연락처담당")
                self.client_phone_label.setText("010-9876-5432")
                self.selected_client_id = 2  # 임시 ID
                print("임시 신규 업체 데이터 설정 완료")
        except Exception as e:
            import traceback
            error_msg = f"업체 등록 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)
      
    def update_storage_temp(self):
        """보관 조건에 따라 온도 표시 업데이트"""
        try:
            # 로그 기록
            self.log_message("INFO", "보관 조건 업데이트 시작")

            # 실측실험 또는 의뢰자 요청(실측) 선택 시
            if self.test_method_real.isChecked() or self.test_method_custom_real.isChecked():
                if self.storage_room_temp.isChecked():
                    self.storage_temp_label.setText(self.ROOM_TEMP_LABEL)
                    self.log_message("INFO", f"실측실험 - 상온 선택: {self.ROOM_TEMP_LABEL}")
                elif self.storage_cool.isChecked():
                    self.storage_temp_label.setText(self.COOL_TEMP_LABEL)
                    self.log_message("INFO", f"실측실험 - 냉장 선택: {self.COOL_TEMP_LABEL}")
                elif self.storage_freeze.isChecked():
                    self.storage_temp_label.setText(self.FREEZE_TEMP_LABEL)
                    self.log_message("INFO", f"실측실험 - 냉동 선택: {self.FREEZE_TEMP_LABEL}")
                elif self.storage_warm.isChecked():
                    self.storage_temp_label.setText(self.WARM_TEMP_LABEL)
                    self.log_message("INFO", f"실측실험 - 실온 선택: {self.WARM_TEMP_LABEL}")

            # 가속실험 또는 의뢰자 요청(가속) 선택 시
            else:
                if self.storage_room_temp.isChecked():
                    self.storage_temp_label.setText(self.ROOM_TEMP_ACCEL_LABEL)
                    self.log_message("INFO", f"가속실험 - 상온 선택: {self.ROOM_TEMP_ACCEL_LABEL}")
                elif self.storage_cool.isChecked():
                    self.storage_temp_label.setText(self.COOL_TEMP_ACCEL_LABEL)
                    self.log_message("INFO", f"가속실험 - 냉장 선택: {self.COOL_TEMP_ACCEL_LABEL}")
                elif self.storage_freeze.isChecked():
                    self.storage_temp_label.setText(self.FREEZE_TEMP_ACCEL_LABEL)
                    self.log_message("INFO", f"가속실험 - 냉동 선택: {self.FREEZE_TEMP_ACCEL_LABEL}")
                elif self.storage_warm.isChecked():
                    self.storage_temp_label.setText(self.WARM_TEMP_ACCEL_LABEL)
                    self.log_message("INFO", f"가속실험 - 실온 선택: {self.WARM_TEMP_ACCEL_LABEL}")
        except Exception as e:
            import traceback
            error_msg = f"보관 조건 업데이트 중 오류 발생: {str(e)}"
            self.log_message("ERROR", f"{error_msg}\n{traceback.format_exc()}")
            print(error_msg)
    
    def update_test_method(self):
        """실험 방법에 따라 온도 표시 및 실험기간 업데이트"""
        try:
            print("실험 방법 변경 감지")
            
            # 기존 온도 입력 필드 모두 제거
            self.clear_custom_temp_inputs()
            
            # 의뢰자 요청 옵션 처리
            if self.test_method_custom_real.isChecked():
                self.storage_temp_label.setText(self.CUSTOM_TEMP_LABEL)
                self.create_custom_temp_inputs(is_acceleration=False)
                print("의뢰자 요청(실측) 선택 - 온도 입력창 2개 생성")
                
            elif self.test_method_custom_accel.isChecked():
                self.storage_temp_label.setText(self.CUSTOM_TEMP_ACCEL_LABEL)
                self.create_custom_temp_inputs(is_acceleration=True)
                print("의뢰자 요청(가속) 선택 - 온도 입력창 3개 생성")
                
            else:
                # 일반 실험 방법의 경우 보관 조건에 맞게 온도 업데이트
                self.update_storage_temp()
                print("일반 실험 방법 선택 - 기본 온도 표시")
            
            # 실험기간 업데이트
            self.update_experiment_period()
                
        except Exception as e:
            import traceback
            error_msg = f"실험 방법 업데이트 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)
            
    def update_experiment_period(self):
        """소비기한을 기반으로 실험기간 계산 및 업데이트"""
        try:
            # 소비기한 값 가져오기
            days = self.days_spin.value()
            months = self.months_spin.value()
            years = self.years_spin.value()
            
            # 소비기한을 총 일수로 계산 (근사값)
            total_days = days + (months * 30) + (years * 365)
            
            # 실험 방법에 따라 실험기간 계산
            experiment_days = 0
            if self.test_method_real.isChecked() or self.test_method_custom_real.isChecked():
                # 실측실험: 소비기한의 2배
                experiment_days = total_days * 2
            elif self.test_method_acceleration.isChecked() or self.test_method_custom_accel.isChecked():
                # 가속실험: 소비기한의 1/2
                experiment_days = total_days // 2
            
            # 실험기간을 년, 월, 일로 변환
            exp_years = experiment_days // 365
            exp_days_remainder = experiment_days % 365
            exp_months = exp_days_remainder // 30
            exp_days = exp_days_remainder % 30
            
            # 실험기간 라벨 업데이트
            period_text = ""
            if exp_years > 0:
                period_text += f"{exp_years}년 "
            if exp_months > 0:
                period_text += f"{exp_months}개월 "
            if exp_days > 0:
                period_text += f"{exp_days}일"
            
            if not period_text:
                period_text = "0일"
            
            self.experiment_period_label.setText(period_text.strip())
            print(f"실험기간 업데이트: {period_text.strip()}")
            
        except Exception as e:
            print(f"실험기간 업데이트 중 오류 발생: {str(e)}")
            
    def show_custom_temp_inputs(self, is_acceleration=False):
        """의뢰자 요청 온도 입력창 표시"""
        try:
            print("온도 입력창 생성 시작")
            
            # 기존에 추가된 "요청 온도:" 행을 찾아 제거
            test_group = None
            for i in range(self.main_layout.count()):
                item = self.main_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox) and item.widget().title() == "실험 정보":
                    test_group = item.widget()
                    test_layout = test_group.layout()
                    
                    # QFormLayout에서 "요청 온도:" 라벨을 찾아 제거
                    if test_layout:
                        for row in range(test_layout.rowCount()):
                            label_item = test_layout.itemAt(row, QFormLayout.LabelRole)
                            if label_item and label_item.widget():
                                label_widget = label_item.widget()
                                if isinstance(label_widget, QLabel) and label_widget.text() == "요청 온도:":
                                    # 필드 항목 가져오기
                                    field_item = test_layout.itemAt(row, QFormLayout.FieldRole)
                                    if field_item and field_item.widget():
                                        field_widget = field_item.widget()
                                        # 위젯 제거 및 삭제
                                        test_layout.removeRow(row)
                                        field_widget.setParent(None)
                                        field_widget.deleteLater()
                                        label_widget.setParent(None)
                                        label_widget.deleteLater()
                                        print("기존 '요청 온도:' 행 제거 완료")
                                        break
                    break
            
            # 기존 입력창이 있다면 제거
            if hasattr(self, 'custom_temp_frame'):
                self.custom_temp_frame.setParent(None)
                self.custom_temp_frame.deleteLater()
                print("기존 온도 입력창 제거")
            
            # 새 입력창 생성
            self.custom_temp_frame = QFrame()
            temp_layout = QVBoxLayout(self.custom_temp_frame)
            
            # 가속실험인 경우 3개 온도 입력, 실측실험인 경우 2개 온도 입력
            temp_count = 3 if is_acceleration else 2
            self.temp_inputs = []
            
            for i in range(temp_count):
                temp_input_layout = QHBoxLayout()
                temp_input = QLineEdit()
                temp_input.setPlaceholderText(f"온도 {i+1} (℃)")
                self.temp_inputs.append(temp_input)
                
                temp_input_layout.addWidget(QLabel(f"온도 {i+1}:"))
                temp_input_layout.addWidget(temp_input)
                temp_input_layout.addWidget(QLabel("℃"))
                temp_input_layout.addStretch()
                
                temp_layout.addLayout(temp_input_layout)
            
            # 실험 정보 그룹을 이미 찾았으니 바로 추가
            if test_group and test_layout:
                self.custom_temp_frame.setLayout(temp_layout)
                test_layout.addRow("요청 온도:", self.custom_temp_frame)
                print(f"온도 입력창 {temp_count}개 생성 완료")
            else:
                print("실험 정보 그룹을 찾을 수 없음")
                QMessageBox.warning(self, "경고", "온도 입력창을 추가할 위치를 찾을 수 없습니다.")
                
        except Exception as e:
            import traceback
            error_msg = f"온도 입력창 생성 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)
            
    def period_value_changed(self, value, period_type):
        """소비기한 값이 변경되었을 때 처리"""
        try:
            # 소비기한 메시지 구성
            days = self.days_spin.value()
            months = self.months_spin.value()
            years = self.years_spin.value()
            
            # 실험기간 계산 및 업데이트
            self.update_experiment_period()
            
            # 값이 변경되면 로그 기록
            message = f"소비기한 변경: {days}일 {months}개월 {years}년"
            print(message)  # 로그 기록
            
        except Exception as e:
            print(f"소비기한 값 변경 처리 중 오류 발생: {str(e)}")  # 로그 기록
    
    def update_food_type_info(self):
        """식품 유형에 따른 정보 업데이트"""
        try:
            food_type_name = self.food_type_combo.currentText().strip()
            if not food_type_name:
                return
            
            from models.product_types import ProductType
            # 식품 유형 정보 가져오기
            food_type = ProductType.get_by_name(food_type_name)
            
            if food_type:
                # 식품 유형 정보 설정
                if isinstance(food_type, dict):
                    # 딕셔너리인 경우
                    self.sterilization_input.setText(food_type.get('sterilization', ''))
                    self.pasteurization_input.setText(food_type.get('pasteurization', ''))
                    self.appearance_input.setText(food_type.get('appearance', ''))
                    self.test_items_label.setText(food_type.get('test_items', ''))
                else:
                    # sqlite3.Row 객체인 경우
                    try:
                        # 컬럼 이름으로 접근 시도
                        self.sterilization_input.setText(food_type['sterilization'] if 'sterilization' in food_type.keys() else '')
                        self.pasteurization_input.setText(food_type['pasteurization'] if 'pasteurization' in food_type.keys() else '')
                        self.appearance_input.setText(food_type['appearance'] if 'appearance' in food_type.keys() else '')
                        self.test_items_label.setText(food_type['test_items'] if 'test_items' in food_type.keys() else '')
                    except (IndexError, KeyError):
                        # 인덱스로 접근 (컬럼 순서에 따라 조정 필요)
                        self.sterilization_input.setText(str(food_type[3]) if len(food_type) > 3 else '')
                        self.pasteurization_input.setText(str(food_type[4]) if len(food_type) > 4 else '')
                        self.appearance_input.setText(str(food_type[5]) if len(food_type) > 5 else '')
                        self.test_items_label.setText(str(food_type[6]) if len(food_type) > 6 else '')
        except Exception as e:
            import traceback
            error_msg = f"식품 유형 정보 업데이트 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.warning(self, "경고", error_msg)
            
    # 여기에 log_message 함수 추가
    # ScheduleCreateDialog 클래스 내부에 log_message 함수 추가
    def log_message(self, category, message):
        """로그 메시지를 출력하는 함수"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{category}] {message}")
        
        # 선택적으로 파일에 로그 기록
        try:
            with open('app_log.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"[{timestamp}] [{category}] {message}\n")
        except Exception as e:
            print(f"[{timestamp}] [ERROR] 로그 파일 쓰기 실패: {str(e)}")
    
    def select_food_type(self):
        """식품 유형 선택 다이얼로그 표시"""
        try:
            print("식품 유형 선택 시작")
            
            # 현재 입력된 검색어 가져오기
            search_text = self.food_type_combo.currentText().strip()
            
            # FoodTypeSelectionDialog 생성
            dialog = FoodTypeSelectionDialog(self)
            
            # 검색어 설정 - 대화상자가 생성된 후에 설정
            dialog.search_text = search_text
            if hasattr(dialog, 'search_input'):
                dialog.search_input.setText(search_text)
            
            # 다이얼로그 실행
            if dialog.exec_():
                # 선택된 식품 유형 정보 가져오기
                selected_food_type = dialog.selected_food_type
                print(f"선택된 식품 유형: {selected_food_type}")
                
                # 식품 유형 정보 설정
                if isinstance(selected_food_type, dict):
                    # 딕셔너리인 경우
                    self.food_type_combo.setCurrentText(selected_food_type['type_name'])
                    self.selected_food_type_id = selected_food_type['id']
                    
                    # 추가 정보 설정
                    self.sterilization_input.setText(selected_food_type.get('sterilization', ''))
                    self.pasteurization_input.setText(selected_food_type.get('pasteurization', ''))
                    self.appearance_input.setText(selected_food_type.get('appearance', ''))
                    self.test_items_label.setText(selected_food_type.get('test_items', ''))
                    
                    print(f"식품 유형 정보 설정 완료: {selected_food_type['type_name']}")
                else:
                    # 튜플인 경우 (이전 형식 호환)
                    food_type_id, food_type_name = selected_food_type
                    self.food_type_combo.setCurrentText(food_type_name)
                    self.selected_food_type_id = food_type_id
                    
                    # 식품 유형 정보 업데이트
                    self.update_food_type_info()
                    print(f"식품 유형 정보 설정 완료 (이전 형식): {food_type_name}")
        except Exception as e:
            import traceback
            error_msg = f"식품 유형 선택 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)

    def update_food_type_info(self):
        """식품 유형에 따른 정보 업데이트"""
        try:
            food_type_name = self.food_type_combo.currentText().strip()
            if not food_type_name:
                return
            
            # 입력된 텍스트로 식품 유형 검색
            from models.product_types import ProductType
            
            # 정확히 일치하는 항목 먼저 확인
            food_type = ProductType.get_by_name(food_type_name)
            
            # 정확히 일치하는 항목이 없으면 부분 일치 검색
            if not food_type:
                food_types = ProductType.search(food_type_name)
                if food_types:
                    if len(food_types) == 1:
                        # 검색 결과가 하나면 자동 선택
                        food_type = food_types[0]
                        self.food_type_combo.setCurrentText(food_type['type_name'])
                        self.selected_food_type_id = food_type['id']
                    else:
                        # 검색 결과가 여러 개면 선택 다이얼로그 표시
                        self.select_food_type()
                        return
                else:
                    print(f"'{food_type_name}' 일치하는 식품 유형이 없습니다.")
                    return
            
            # 식품 유형 정보 설정
            self.selected_food_type_id = food_type['id']
            self.sterilization_input.setText(food_type.get('sterilization', ''))
            self.pasteurization_input.setText(food_type.get('pasteurization', ''))
            self.appearance_input.setText(food_type.get('appearance', ''))
            self.test_items_label.setText(food_type.get('test_items', ''))
            
            print(f"식품 유형 정보 업데이트 완료: {food_type_name}")
        except Exception as e:
            print(f"식품 유형 정보 업데이트 중 오류 발생: {str(e)}")
     
    def accept(self):
        """다이얼로그 수락 (저장 버튼 클릭)"""
        try:
            print("스케줄 저장 시작")  # 로그 기록

            # 필수 입력 확인
            if not self.selected_client_id:
                QMessageBox.warning(self, "입력 오류", "업체를 선택해주세요.")
                return

            if not self.product_name_input.text().strip():
                QMessageBox.warning(self, "입력 오류", "제품명을 입력해주세요.")
                return

            # 의뢰자 요청 온도인 경우 온도 값 수집
            custom_temperatures = None
            if (self.test_method_custom_real.isChecked() or self.test_method_custom_accel.isChecked()) and hasattr(self, 'temp_inputs'):
                temperatures = []
                for temp_input in self.temp_inputs:
                    temp_value = temp_input.text().strip()
                    if temp_value:
                        temperatures.append(temp_value)
                custom_temperatures = ','.join(temperatures) if temperatures else None

            # 데이터베이스에 저장
            from models.schedules import Schedule

            schedule_id = Schedule.create(
                client_id=self.selected_client_id,
                product_name=self.product_name_input.text().strip(),
                food_type_id=self.selected_food_type_id,
                test_method=self.get_test_method(),
                storage_condition=self.get_storage_condition(),
                test_start_date=self.test_start_date.date().toString('yyyy-MM-dd'),
                test_period_days=self.days_spin.value(),
                test_period_months=self.months_spin.value(),
                test_period_years=self.years_spin.value(),
                sampling_count=6 if self.default_sampling_check.isChecked() else self.sampling_spin.value(),
                report_interim=self.report_type_interim.isChecked(),
                report_korean=self.report_type_korean.isChecked(),
                report_english=self.report_type_english.isChecked(),
                extension_test=self.extension_check.isChecked(),
                custom_temperatures=custom_temperatures
            )

            if schedule_id:
                # 설정 기간 메시지 구성
                period_msg = ""
                days = self.days_spin.value()
                months = self.months_spin.value()
                years = self.years_spin.value()

                if days > 0:
                    period_msg += f"{days}일 "
                if months > 0:
                    period_msg += f"{months}개월 "
                if years > 0:
                    period_msg += f"{years}년"

                if period_msg:
                    period_msg = f"소비기한: {period_msg.strip()}"

                save_msg = f"스케줄이 저장되었습니다.\n\n{period_msg}"
                QMessageBox.information(self, "저장 완료", save_msg)
                print(f"스케줄 저장 완료: ID {schedule_id}")

                # 다이얼로그 닫기
                super().accept()
            else:
                QMessageBox.critical(self, "저장 실패", "스케줄을 저장하지 못했습니다.")

        except Exception as e:
            import traceback
            error_msg = f"스케줄 저장 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "오류", error_msg)
    
    def preview_schedule(self):
        """스케줄 미리보기 기능"""
        try:
            print("스케줄 미리보기 시작")  # 로그 기록
            
            # 기본 정보 수집
            product_name = self.product_name_input.text()
            test_method = '가속실험' if self.test_method_acceleration.isChecked() else '실측실험'
            storage_condition = self.storage_temp_label.text()
            test_period = f"{self.days_spin.value()}일 {self.months_spin.value()}개월 {self.years_spin.value()}년"
            sampling_count = 6 if self.default_sampling_check.isChecked() else self.sampling_spin.value()
            
            # 보고서 종류 정보 수집
            report_types = []
            if self.report_type_interim.isChecked():
                report_types.append("중간")
            if self.report_type_korean.isChecked():
                report_types.append("국문")
            if self.report_type_english.isChecked():
                report_types.append("영문")
            report_type_text = ", ".join(report_types) if report_types else "없음"
            
            # 연장실험 상태
            extension_status = "진행" if self.extension_check.isChecked() else "미진행"
            
            # 미리보기 메시지 구성
            preview_msg = f"""
    === 스케줄 미리보기 ===
    제품명: {product_name}
    실험방법: {test_method}
    보관조건: {storage_condition}
    소비기한: {test_period}
    샘플링 횟수: {sampling_count}회
    보고서 종류: {report_type_text}
    연장실험: {extension_status}
            """
            
            # 미리보기 메시지 표시
            QMessageBox.information(self, "스케줄 미리보기", preview_msg)
            print("스케줄 미리보기 완료")  # 로그 기록
        except Exception as e:
            import traceback
            error_msg = f"스케줄 미리보기 중 오류 발생: {str(e)}"
            print(error_msg)  # 로그 기록
            QMessageBox.critical(self, "오류", error_msg)
            
    def update_extension_status(self, state):
        """연장실험 체크박스 상태에 따라 레이블 업데이트"""
        if state == Qt.Checked:
            self.extension_status_label.setText("진행")
            self.extension_status_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.extension_status_label.setText("미진행")
            self.extension_status_label.setStyleSheet("color: gray;")
        
        print(f"연장실험 상태 변경: {'진행' if state == Qt.Checked else '미진행'}")
                    
    def get_test_method(self):
        """현재 선택된 실험 방법 반환"""
        if self.test_method_real.isChecked():
            return "real"
        elif self.test_method_acceleration.isChecked():
            return "acceleration"
        elif self.test_method_custom_real.isChecked():
            return "custom_real"
        elif self.test_method_custom_accel.isChecked():
            return "custom_acceleration"
        return ""

    def get_storage_condition(self):
        """현재 선택된 보관 조건 반환"""
        if self.storage_room_temp.isChecked():
            return "room_temp"
        elif self.storage_warm.isChecked():
            return "warm"
        elif self.storage_cool.isChecked():
            return "cool"
        elif self.storage_freeze.isChecked():
            return "freeze"
        return ""

    def clear_custom_temp_inputs(self):
        """모든 온도 입력 필드를 제거합니다."""
        try:
            print("모든 온도 입력 필드 제거 시작")
            
            # 실험 정보 그룹 찾기
            test_group = None
            for i in range(self.main_layout.count()):
                item = self.main_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox) and item.widget().title() == "실험 정보":
                    test_group = item.widget()
                    break
            
            if not test_group:
                print("실험 정보 그룹을 찾을 수 없음")
                return
                
            # 레이아웃에서 모든 "요청 온도:" 항목 제거
            test_layout = test_group.layout()
            if not test_layout or not isinstance(test_layout, QFormLayout):
                print("적절한 레이아웃을 찾을 수 없음")
                return
                
            # 레이아웃에서 모든 행을 확인하며 "요청 온도:" 라벨이 있는 행을 찾아 제거
            rows_to_remove = []
            for row in range(test_layout.rowCount()):
                label_item = test_layout.itemAt(row, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    label = label_item.widget()
                    if isinstance(label, QLabel) and "요청 온도" in label.text():
                        rows_to_remove.append(row)
            
            # 높은 인덱스부터 제거 (낮은 인덱스부터 제거하면 인덱스가 변경됨)
            for row in sorted(rows_to_remove, reverse=True):
                # 해당 행의 모든 위젯 제거
                label_item = test_layout.itemAt(row, QFormLayout.LabelRole)
                field_item = test_layout.itemAt(row, QFormLayout.FieldRole)
                
                if label_item and label_item.widget():
                    widget = label_item.widget()
                    test_layout.removeItem(label_item)
                    widget.setParent(None)
                    widget.deleteLater()
                    
                if field_item and field_item.widget():
                    widget = field_item.widget()
                    test_layout.removeItem(field_item)
                    widget.setParent(None)
                    widget.deleteLater()
                    
                # 행 자체를 제거
                test_layout.takeRow(row)
                
            print(f"{len(rows_to_remove)}개의 '요청 온도:' 행 제거 완료")
            
            # 클래스 속성으로 저장된 프레임도 제거
            if hasattr(self, 'custom_temp_frame'):
                self.custom_temp_frame.setParent(None)
                self.custom_temp_frame.deleteLater()
                delattr(self, 'custom_temp_frame')
                print("custom_temp_frame 제거 완료")
                
            # temp_inputs 변수도 초기화
            if hasattr(self, 'temp_inputs'):
                delattr(self, 'temp_inputs')
                
        except Exception as e:
            import traceback
            error_msg = f"온도 입력 필드 제거 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            
    def create_custom_temp_inputs(self, is_acceleration=False):
        """새로운 온도 입력 필드를 생성합니다."""
        try:
            print("새 온도 입력 필드 생성 시작")
            
            # 입력 필드 개수 결정
            temp_count = 3 if is_acceleration else 2
            
            # 실험 정보 그룹 찾기
            test_group = None
            for i in range(self.main_layout.count()):
                item = self.main_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox) and item.widget().title() == "실험 정보":
                    test_group = item.widget()
                    break
                    
            if not test_group:
                print("실험 정보 그룹을 찾을 수 없음")
                return
                
            test_layout = test_group.layout()
            if not test_layout or not isinstance(test_layout, QFormLayout):
                print("적절한 레이아웃을 찾을 수 없음")
                return
                
            # 새 컨테이너 프레임 생성
            self.custom_temp_frame = QFrame()
            self.custom_temp_frame.setFrameShape(QFrame.StyledPanel)
            temp_layout = QVBoxLayout(self.custom_temp_frame)
            temp_layout.setContentsMargins(0, 0, 0, 0)
            
            self.temp_inputs = []
            
            # 온도 입력 필드 생성
            for i in range(temp_count):
                row_layout = QHBoxLayout()
                label = QLabel(f"온도 {i+1}:")
                input_field = QLineEdit()
                input_field.setPlaceholderText(f"온도 {i+1} (℃)")
                unit_label = QLabel("℃")
                
                row_layout.addWidget(label)
                row_layout.addWidget(input_field)
                row_layout.addWidget(unit_label)
                row_layout.addStretch()
                
                self.temp_inputs.append(input_field)
                temp_layout.addLayout(row_layout)
                
            # 레이아웃에 추가
            test_layout.addRow("요청 온도:", self.custom_temp_frame)
            print(f"{temp_count}개의 온도 입력 필드 생성 완료")
            
        except Exception as e:
            import traceback
            error_msg = f"온도 입력 필드 생성 중 오류 발생: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
    
    def delete_food_type(food_type_id):
        """식품 유형 삭제"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 삭제 전 로깅
            print(f"식품 유형 삭제 시작: ID {food_type_id}")
            
            # 데이터 삭제 쿼리 실행
            cursor.execute("DELETE FROM food_types WHERE id = ?", (food_type_id,))
            
            # 영향 받은 행 수 확인
            rows_affected = cursor.rowcount
            print(f"삭제된 행 수: {rows_affected}")
            
            # 변경사항 커밋
            conn.commit()
            conn.close()
            
            return True, f"{rows_affected}개의 항목이 삭제되었습니다."
        except Exception as e:
            print(f"식품 유형 삭제 중 오류 발생: {str(e)}")
            # 롤백 시도
            try:
                conn.rollback()
            except:
                pass
            finally:
                conn.close()
            return False, f"삭제 중 오류 발생: {str(e)}"        
    