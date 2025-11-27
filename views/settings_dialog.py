# views/settings_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QFormLayout, QLineEdit, QPushButton,
                            QLabel, QMessageBox, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumSize(500, 400)
        self.initUI()
        self.load_settings()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 탭 위젯
        self.tab_widget = QTabWidget()

        # 일반 설정 탭
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "일반")

        # 부가세 설정 탭
        tax_tab = QWidget()
        self.setup_tax_tab(tax_tab)
        self.tab_widget.addTab(tax_tab, "부가세/할인")

        # 경로 설정 탭
        path_tab = QWidget()
        self.setup_path_tab(path_tab)
        self.tab_widget.addTab(path_tab, "파일 경로")

        layout.addWidget(self.tab_widget)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def setup_general_tab(self, tab):
        """일반 설정 탭"""
        layout = QVBoxLayout(tab)

        # 회사 정보 그룹
        company_group = QGroupBox("회사 정보")
        company_layout = QFormLayout()

        self.company_name_input = QLineEdit()
        company_layout.addRow("회사명:", self.company_name_input)

        self.company_phone_input = QLineEdit()
        company_layout.addRow("연락처:", self.company_phone_input)

        self.company_address_input = QLineEdit()
        company_layout.addRow("주소:", self.company_address_input)

        company_group.setLayout(company_layout)
        layout.addWidget(company_group)

        # 기본 설정 그룹
        default_group = QGroupBox("기본 설정")
        default_layout = QFormLayout()

        self.default_sampling_spin = QSpinBox()
        self.default_sampling_spin.setRange(1, 30)
        self.default_sampling_spin.setValue(6)
        default_layout.addRow("기본 샘플링 횟수:", self.default_sampling_spin)

        default_group.setLayout(default_layout)
        layout.addWidget(default_group)

        layout.addStretch()

    def setup_tax_tab(self, tab):
        """부가세/할인 설정 탭"""
        layout = QVBoxLayout(tab)

        # 부가세 그룹
        tax_group = QGroupBox("부가세 설정")
        tax_layout = QFormLayout()

        self.tax_rate_spin = QSpinBox()
        self.tax_rate_spin.setRange(0, 100)
        self.tax_rate_spin.setValue(10)
        self.tax_rate_spin.setSuffix(" %")
        tax_layout.addRow("부가세율:", self.tax_rate_spin)

        tax_group.setLayout(tax_layout)
        layout.addWidget(tax_group)

        # 할인 그룹
        discount_group = QGroupBox("할인 설정")
        discount_layout = QFormLayout()

        self.default_discount_spin = QSpinBox()
        self.default_discount_spin.setRange(0, 100)
        self.default_discount_spin.setValue(0)
        self.default_discount_spin.setSuffix(" %")
        discount_layout.addRow("기본 할인율:", self.default_discount_spin)

        discount_group.setLayout(discount_layout)
        layout.addWidget(discount_group)

        layout.addStretch()

    def setup_path_tab(self, tab):
        """파일 경로 설정 탭"""
        layout = QVBoxLayout(tab)

        # 경로 그룹
        path_group = QGroupBox("파일 저장 경로")
        path_layout = QFormLayout()

        self.output_path_input = QLineEdit()
        self.output_path_input.setText("output")
        path_layout.addRow("출력 파일 경로:", self.output_path_input)

        self.template_path_input = QLineEdit()
        self.template_path_input.setText("templates")
        path_layout.addRow("템플릿 경로:", self.template_path_input)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        layout.addStretch()

    def load_settings(self):
        """데이터베이스에서 설정 불러오기"""
        try:
            from database import get_connection

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()
            conn.close()

            settings_dict = {s['key']: s['value'] for s in settings}

            # 부가세율
            if 'tax_rate' in settings_dict:
                self.tax_rate_spin.setValue(int(settings_dict['tax_rate']))

            # 기본 할인율
            if 'default_discount' in settings_dict:
                self.default_discount_spin.setValue(int(settings_dict['default_discount']))

            # 출력 경로
            if 'output_path' in settings_dict:
                self.output_path_input.setText(settings_dict['output_path'])

            # 템플릿 경로
            if 'template_path' in settings_dict:
                self.template_path_input.setText(settings_dict['template_path'])

        except Exception as e:
            print(f"설정 로드 중 오류: {str(e)}")

    def save_settings(self):
        """설정 저장"""
        try:
            from database import get_connection

            conn = get_connection()
            cursor = conn.cursor()

            # 설정 값 업데이트
            settings = [
                ('tax_rate', str(self.tax_rate_spin.value())),
                ('default_discount', str(self.default_discount_spin.value())),
                ('output_path', self.output_path_input.text()),
                ('template_path', self.template_path_input.text())
            ]

            for key, value in settings:
                cursor.execute("""
                    UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                """, (value, key))

                # 없으면 새로 추가
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO settings (key, value) VALUES (?, ?)
                    """, (key, value))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
            self.accept()

        except Exception as e:
            print(f"설정 저장 중 오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
