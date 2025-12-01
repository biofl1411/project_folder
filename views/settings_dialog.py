# views/settings_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QFormLayout, QLineEdit, QPushButton,
                            QLabel, QMessageBox, QSpinBox, QGroupBox, QCheckBox,
                            QComboBox)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumSize(550, 500)
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

        # 이메일 설정 탭
        email_tab = QWidget()
        self.setup_email_tab(email_tab)
        self.tab_widget.addTab(email_tab, "이메일")

        # 경로 설정 탭
        path_tab = QWidget()
        self.setup_path_tab(path_tab)
        self.tab_widget.addTab(path_tab, "파일 경로")

        # 스케줄 설정 탭
        schedule_tab = QWidget()
        self.setup_schedule_tab(schedule_tab)
        self.tab_widget.addTab(schedule_tab, "스케줄")

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

        # 고정값 스타일
        fixed_style = "background-color: #f0f0f0; color: #333;"

        self.company_name_input = QLineEdit()
        self.company_name_input.setText("(주)바이오푸드랩")
        self.company_name_input.setReadOnly(True)
        self.company_name_input.setStyleSheet(fixed_style)
        company_layout.addRow("회사명:", self.company_name_input)

        self.company_ceo_input = QLineEdit()
        self.company_ceo_input.setText("이용표")
        self.company_ceo_input.setReadOnly(True)
        self.company_ceo_input.setStyleSheet(fixed_style)
        company_layout.addRow("대표자:", self.company_ceo_input)

        self.company_manager_input = QLineEdit()
        company_layout.addRow("담당자:", self.company_manager_input)

        self.company_phone_input = QLineEdit()
        company_layout.addRow("연락처:", self.company_phone_input)

        self.company_mobile_input = QLineEdit()
        company_layout.addRow("핸드폰:", self.company_mobile_input)

        self.company_fax_input = QLineEdit()
        self.company_fax_input.setText("070-7410-1430")
        self.company_fax_input.setReadOnly(True)
        self.company_fax_input.setStyleSheet(fixed_style)
        company_layout.addRow("팩스:", self.company_fax_input)

        self.company_address_input = QLineEdit()
        self.company_address_input.setText("서울특별시 구로구 디지털로 30길 28, 마리오타워 1410~1414호")
        self.company_address_input.setReadOnly(True)
        self.company_address_input.setStyleSheet(fixed_style)
        company_layout.addRow("주소:", self.company_address_input)

        self.company_email_input = QLineEdit()
        self.company_email_input.setPlaceholderText("example@biofoodlab.co.kr")
        company_layout.addRow("이메일:", self.company_email_input)

        company_group.setLayout(company_layout)
        layout.addWidget(company_group)

        # 기본 설정 그룹
        default_group = QGroupBox("기본 설정")
        default_layout = QFormLayout()

        self.default_sampling_spin = QSpinBox()
        self.default_sampling_spin.setRange(1, 30)
        self.default_sampling_spin.setValue(13)  # 기본값 13회
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

    def setup_email_tab(self, tab):
        """이메일 설정 탭"""
        layout = QVBoxLayout(tab)

        # SMTP 서버 설정 그룹
        smtp_group = QGroupBox("SMTP 서버 설정")
        smtp_layout = QFormLayout()

        # SMTP 서버
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.gmail.com")
        smtp_layout.addRow("SMTP 서버:", self.smtp_server_input)

        # SMTP 포트
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        smtp_layout.addRow("포트:", self.smtp_port_spin)

        # 보안 연결
        self.smtp_security_combo = QComboBox()
        self.smtp_security_combo.addItems(["TLS", "SSL", "없음"])
        smtp_layout.addRow("보안:", self.smtp_security_combo)

        smtp_group.setLayout(smtp_layout)
        layout.addWidget(smtp_group)

        # 계정 설정 그룹
        account_group = QGroupBox("계정 설정")
        account_layout = QFormLayout()

        # 발신자 이메일
        self.smtp_email_input = QLineEdit()
        self.smtp_email_input.setPlaceholderText("sender@biofoodlab.co.kr")
        account_layout.addRow("발신 이메일:", self.smtp_email_input)

        # 비밀번호 (앱 비밀번호)
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        self.smtp_password_input.setPlaceholderText("앱 비밀번호 입력")
        account_layout.addRow("비밀번호:", self.smtp_password_input)

        # 발신자 이름
        self.smtp_sender_name_input = QLineEdit()
        self.smtp_sender_name_input.setText("(주)바이오푸드랩")
        account_layout.addRow("발신자 이름:", self.smtp_sender_name_input)

        account_group.setLayout(account_layout)
        layout.addWidget(account_group)

        # 테스트 버튼
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_email_btn = QPushButton("연결 테스트")
        self.test_email_btn.clicked.connect(self.test_email_connection)
        test_layout.addWidget(self.test_email_btn)
        layout.addLayout(test_layout)

        # 안내 문구
        info_label = QLabel("※ Gmail 사용 시 '앱 비밀번호'를 생성하여 입력하세요.\n"
                           "※ 네이버, 다음 등도 SMTP 설정 후 사용 가능합니다.")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)

        layout.addStretch()

    def test_email_connection(self):
        """이메일 연결 테스트"""
        try:
            import smtplib

            server = self.smtp_server_input.text().strip()
            port = self.smtp_port_spin.value()
            email = self.smtp_email_input.text().strip()
            password = self.smtp_password_input.text()
            security = self.smtp_security_combo.currentText()

            if not server or not email or not password:
                QMessageBox.warning(self, "입력 오류", "SMTP 서버, 이메일, 비밀번호를 모두 입력해주세요.")
                return

            # SMTP 연결 테스트
            if security == "SSL":
                smtp = smtplib.SMTP_SSL(server, port, timeout=10)
            else:
                smtp = smtplib.SMTP(server, port, timeout=10)
                if security == "TLS":
                    smtp.starttls()

            smtp.login(email, password)
            smtp.quit()

            QMessageBox.information(self, "연결 성공", "SMTP 서버에 성공적으로 연결되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "연결 실패", f"SMTP 연결에 실패했습니다.\n\n오류: {str(e)}")

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

        # 로고/직인 그룹
        image_group = QGroupBox("로고 및 직인 이미지")
        image_layout = QFormLayout()

        # 로고 파일
        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("로고 이미지 파일 경로")
        self.logo_path_input.setReadOnly(True)
        logo_btn = QPushButton("찾기")
        logo_btn.setFixedWidth(60)
        logo_btn.clicked.connect(lambda: self.browse_image('logo'))
        logo_clear_btn = QPushButton("삭제")
        logo_clear_btn.setFixedWidth(60)
        logo_clear_btn.clicked.connect(lambda: self.clear_image('logo'))
        logo_layout.addWidget(self.logo_path_input)
        logo_layout.addWidget(logo_btn)
        logo_layout.addWidget(logo_clear_btn)
        image_layout.addRow("회사 로고:", logo_layout)

        # 직인 파일
        stamp_layout = QHBoxLayout()
        self.stamp_path_input = QLineEdit()
        self.stamp_path_input.setPlaceholderText("직인 이미지 파일 경로")
        self.stamp_path_input.setReadOnly(True)
        stamp_btn = QPushButton("찾기")
        stamp_btn.setFixedWidth(60)
        stamp_btn.clicked.connect(lambda: self.browse_image('stamp'))
        stamp_clear_btn = QPushButton("삭제")
        stamp_clear_btn.setFixedWidth(60)
        stamp_clear_btn.clicked.connect(lambda: self.clear_image('stamp'))
        stamp_layout.addWidget(self.stamp_path_input)
        stamp_layout.addWidget(stamp_btn)
        stamp_layout.addWidget(stamp_clear_btn)
        image_layout.addRow("대표자 직인:", stamp_layout)

        # 안내 문구
        info_label = QLabel("※ 로고: 견적서 상단 'BFL' 위치에 표시됩니다.\n"
                           "※ 직인: 대표자 이름 옆에 표시됩니다.\n"
                           "※ 권장 형식: PNG (투명 배경), 크기: 로고 200x60px, 직인 80x80px")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        image_layout.addRow("", info_label)

        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        layout.addStretch()

    def browse_image(self, image_type):
        """이미지 파일 선택"""
        from PyQt5.QtWidgets import QFileDialog
        import shutil
        import os

        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 선택",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp);;모든 파일 (*.*)"
        )

        if file_path:
            # config 폴더에 복사
            config_dir = "config"
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            # 파일 이름 결정
            ext = os.path.splitext(file_path)[1]
            if image_type == 'logo':
                dest_name = f"company_logo{ext}"
                self.logo_path_input.setText(file_path)
            else:
                dest_name = f"company_stamp{ext}"
                self.stamp_path_input.setText(file_path)

            dest_path = os.path.join(config_dir, dest_name)

            try:
                shutil.copy2(file_path, dest_path)
                if image_type == 'logo':
                    self.logo_path_input.setText(dest_path)
                else:
                    self.stamp_path_input.setText(dest_path)
                QMessageBox.information(self, "완료", f"이미지가 저장되었습니다.\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"이미지 저장 실패: {str(e)}")

    def clear_image(self, image_type):
        """이미지 경로 삭제"""
        if image_type == 'logo':
            self.logo_path_input.clear()
        else:
            self.stamp_path_input.clear()

    def setup_schedule_tab(self, tab):
        """스케줄 설정 탭"""
        layout = QVBoxLayout(tab)

        # 중간보고서 설정 그룹
        interim_group = QGroupBox("중간보고서 날짜 설정")
        interim_layout = QFormLayout()

        # 설명 라벨
        description_label = QLabel(
            "중간보고일은 '3. 온도조건별 실험 스케줄'의 6회 실험일을 기준으로\n"
            "아래 설정한 일수를 더하여 자동 계산됩니다."
        )
        description_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        interim_layout.addRow(description_label)

        # 중간보고일 오프셋 설정
        offset_layout = QHBoxLayout()
        offset_label = QLabel("6회 실험일 +")
        self.interim_report_offset_spin = QSpinBox()
        self.interim_report_offset_spin.setRange(0, 90)
        self.interim_report_offset_spin.setValue(0)
        self.interim_report_offset_spin.setSuffix(" 일")
        self.interim_report_offset_spin.setMinimumWidth(100)
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.interim_report_offset_spin)
        offset_layout.addStretch()
        interim_layout.addRow("중간보고일 계산:", offset_layout)

        # 예시 설명
        example_label = QLabel(
            "예시: 6회 실험일이 2026-01-30이고 +15일로 설정하면\n"
            "      중간보고일은 2026-02-14로 자동 계산됩니다."
        )
        example_label.setStyleSheet("color: #27ae60; font-size: 10px; margin-top: 5px;")
        interim_layout.addRow(example_label)

        interim_group.setLayout(interim_layout)
        layout.addWidget(interim_group)

        # 안내 문구
        info_label = QLabel(
            "※ 이 설정은 스케줄 관리 탭의 중간보고일 자동 계산에 적용됩니다.\n"
            "※ 중간보고일은 스케줄 관리 탭에서 달력을 통해 직접 수정할 수도 있습니다."
        )
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)

        layout.addStretch()

    def load_settings(self):
        """데이터베이스에서 설정 불러오기"""
        try:
            from database import get_connection

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()

            settings_dict = {s['key']: s['value'] for s in settings}

            # 담당자: 로그인한 사용자 이름 가져오기
            try:
                cursor.execute("SELECT name FROM users ORDER BY last_login DESC LIMIT 1")
                user = cursor.fetchone()
                if user and user['name']:
                    self.company_manager_input.setText(user['name'])
                elif 'company_manager' in settings_dict:
                    self.company_manager_input.setText(settings_dict['company_manager'])
            except:
                if 'company_manager' in settings_dict:
                    self.company_manager_input.setText(settings_dict['company_manager'])

            conn.close()

            # 연락처, 핸드폰 (입력 가능 필드만 DB에서 로드)
            if 'company_phone' in settings_dict:
                self.company_phone_input.setText(settings_dict['company_phone'])
            if 'company_mobile' in settings_dict:
                self.company_mobile_input.setText(settings_dict['company_mobile'])

            # 기본 샘플링 횟수 (DB에 값이 없으면 기본값 13 사용)
            if 'default_sampling_count' in settings_dict:
                self.default_sampling_spin.setValue(int(settings_dict['default_sampling_count']))
            else:
                self.default_sampling_spin.setValue(13)

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

            # 회사 이메일
            if 'company_email' in settings_dict:
                self.company_email_input.setText(settings_dict['company_email'])

            # 이메일 설정
            if 'smtp_server' in settings_dict:
                self.smtp_server_input.setText(settings_dict['smtp_server'])
            if 'smtp_port' in settings_dict:
                self.smtp_port_spin.setValue(int(settings_dict['smtp_port']))
            if 'smtp_security' in settings_dict:
                index = self.smtp_security_combo.findText(settings_dict['smtp_security'])
                if index >= 0:
                    self.smtp_security_combo.setCurrentIndex(index)
            if 'smtp_email' in settings_dict:
                self.smtp_email_input.setText(settings_dict['smtp_email'])
            if 'smtp_password' in settings_dict:
                self.smtp_password_input.setText(settings_dict['smtp_password'])
            if 'smtp_sender_name' in settings_dict:
                self.smtp_sender_name_input.setText(settings_dict['smtp_sender_name'])

            # 로고/직인 경로
            if 'logo_path' in settings_dict:
                self.logo_path_input.setText(settings_dict['logo_path'])
            if 'stamp_path' in settings_dict:
                self.stamp_path_input.setText(settings_dict['stamp_path'])

            # 스케줄 설정
            if 'interim_report_offset' in settings_dict:
                try:
                    self.interim_report_offset_spin.setValue(int(settings_dict['interim_report_offset']))
                except:
                    self.interim_report_offset_spin.setValue(0)

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
                # 회사 정보
                ('company_name', self.company_name_input.text()),
                ('company_ceo', self.company_ceo_input.text()),
                ('company_manager', self.company_manager_input.text()),
                ('company_phone', self.company_phone_input.text()),
                ('company_mobile', self.company_mobile_input.text()),
                ('company_fax', self.company_fax_input.text()),
                ('company_address', self.company_address_input.text()),
                ('company_email', self.company_email_input.text()),
                # 기본 설정
                ('default_sampling_count', str(self.default_sampling_spin.value())),
                ('tax_rate', str(self.tax_rate_spin.value())),
                ('default_discount', str(self.default_discount_spin.value())),
                ('output_path', self.output_path_input.text()),
                ('template_path', self.template_path_input.text()),
                # 이메일 설정
                ('smtp_server', self.smtp_server_input.text()),
                ('smtp_port', str(self.smtp_port_spin.value())),
                ('smtp_security', self.smtp_security_combo.currentText()),
                ('smtp_email', self.smtp_email_input.text()),
                ('smtp_password', self.smtp_password_input.text()),
                ('smtp_sender_name', self.smtp_sender_name_input.text()),
                # 로고/직인 경로
                ('logo_path', self.logo_path_input.text()),
                ('stamp_path', self.stamp_path_input.text()),
                # 스케줄 설정
                ('interim_report_offset', str(self.interim_report_offset_spin.value()))
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
