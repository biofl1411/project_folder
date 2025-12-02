#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
사용자 관리 탭 - 관리자 전용
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QMessageBox, QComboBox, QGroupBox,
                           QFormLayout, QCheckBox, QScrollArea, QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from models.users import (User, DEPARTMENTS, DEFAULT_PERMISSIONS,
                         PERMISSION_LABELS, DEFAULT_PASSWORD)


class UserManagementTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.selected_user_id = None
        self.permission_checkboxes = {}
        self.initUI()
        self.load_users()

    def set_current_user(self, user):
        """현재 로그인한 사용자 설정"""
        self.current_user = user

    def initUI(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # 왼쪽: 사용자 목록
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 사용자 목록 라벨
        list_label = QLabel("사용자 목록")
        list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(list_label)

        # 사용자 테이블
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(['ID', '아이디', '이름', '부서', '마지막 로그인'])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SingleSelection)
        self.user_table.itemSelectionChanged.connect(self.on_user_selected)
        self.user_table.setColumnHidden(0, True)  # ID 컬럼 숨김
        left_layout.addWidget(self.user_table)

        # 버튼 영역
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_users)
        btn_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("삭제")
        delete_btn.setStyleSheet("background-color: #f44336; color: white;")
        delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(delete_btn)

        reset_pwd_btn = QPushButton("비밀번호 초기화")
        reset_pwd_btn.clicked.connect(self.reset_password)
        btn_layout.addWidget(reset_pwd_btn)

        left_layout.addLayout(btn_layout)

        layout.addWidget(left_widget, 1)

        # 오른쪽: 사용자 추가/수정
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 사용자 정보 입력 그룹
        info_group = QGroupBox("사용자 정보")
        info_layout = QFormLayout(info_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("사용자 이름")
        info_layout.addRow("이름:", self.name_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("로그인 아이디")
        info_layout.addRow("아이디:", self.username_input)

        self.department_combo = QComboBox()
        self.department_combo.addItems([d for d in DEPARTMENTS if d != '관리자'])
        self.department_combo.currentTextChanged.connect(self.on_department_changed)
        info_layout.addRow("부서:", self.department_combo)

        # 초기 비밀번호 안내
        pwd_label = QLabel(f"초기 비밀번호: {DEFAULT_PASSWORD}")
        pwd_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addRow("", pwd_label)

        right_layout.addWidget(info_group)

        # 권한 설정 그룹
        perm_group = QGroupBox("권한 설정 (O: 권한 있음, X: 권한 없음)")
        perm_layout = QVBoxLayout(perm_group)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        perm_widget = QWidget()
        perm_grid = QGridLayout(perm_widget)
        perm_grid.setSpacing(5)

        row = 0
        for perm_key, perm_label in PERMISSION_LABELS.items():
            label = QLabel(perm_label)
            checkbox = QCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #ffcccc;
                    border: 1px solid #999;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #ccffcc;
                    border: 1px solid #999;
                    border-radius: 3px;
                }
            """)

            # O/X 표시 라벨
            status_label = QLabel("X")
            status_label.setStyleSheet("color: red; font-weight: bold;")
            status_label.setFixedWidth(20)

            checkbox.stateChanged.connect(
                lambda state, lbl=status_label: self.update_permission_label(state, lbl)
            )

            self.permission_checkboxes[perm_key] = checkbox

            perm_grid.addWidget(label, row, 0)
            perm_grid.addWidget(checkbox, row, 1)
            perm_grid.addWidget(status_label, row, 2)
            row += 1

        perm_grid.setRowStretch(row, 1)
        scroll.setWidget(perm_widget)
        perm_layout.addWidget(scroll)

        right_layout.addWidget(perm_group)

        # 저장 버튼
        save_btn_layout = QHBoxLayout()

        clear_btn = QPushButton("새 사용자")
        clear_btn.clicked.connect(self.clear_form)
        save_btn_layout.addWidget(clear_btn)

        save_btn = QPushButton("저장")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_user)
        save_btn_layout.addWidget(save_btn)

        right_layout.addLayout(save_btn_layout)

        layout.addWidget(right_widget, 1)

    def update_permission_label(self, state, label):
        """체크박스 상태에 따라 O/X 라벨 업데이트"""
        if state == Qt.Checked:
            label.setText("O")
            label.setStyleSheet("color: green; font-weight: bold;")
        else:
            label.setText("X")
            label.setStyleSheet("color: red; font-weight: bold;")

    def load_users(self):
        """사용자 목록 로드"""
        self.user_table.setRowCount(0)
        users = User.get_all()

        for user in users:
            # admin 계정은 목록에서 제외 (수정/삭제 방지)
            if user.get('username') == 'admin':
                continue

            row = self.user_table.rowCount()
            self.user_table.insertRow(row)

            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
            self.user_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
            self.user_table.setItem(row, 2, QTableWidgetItem(user.get('name', '')))
            self.user_table.setItem(row, 3, QTableWidgetItem(user.get('department', '')))
            self.user_table.setItem(row, 4, QTableWidgetItem(user.get('last_login', '') or ''))

    def on_user_selected(self):
        """사용자 선택 시"""
        selected = self.user_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        self.selected_user_id = user_id

        user = User.get_by_id(user_id)
        if user:
            self.name_input.setText(user.get('name', ''))
            self.username_input.setText(user.get('username', ''))
            self.username_input.setEnabled(False)  # 아이디는 수정 불가

            department = user.get('department', '')
            index = self.department_combo.findText(department)
            if index >= 0:
                self.department_combo.setCurrentIndex(index)

            # 권한 체크박스 설정
            permissions = user.get('permissions', {})
            for perm_key, checkbox in self.permission_checkboxes.items():
                checkbox.setChecked(permissions.get(perm_key, False))

    def on_department_changed(self, department):
        """부서 변경 시 기본 권한 설정"""
        if self.selected_user_id:
            # 기존 사용자 수정 시에는 자동 변경하지 않음
            return

        # 새 사용자 추가 시에만 기본 권한 적용
        if department in DEFAULT_PERMISSIONS:
            default_perms = DEFAULT_PERMISSIONS[department]
            for perm_key, checkbox in self.permission_checkboxes.items():
                checkbox.setChecked(default_perms.get(perm_key, False))

    def clear_form(self):
        """입력 폼 초기화"""
        self.selected_user_id = None
        self.name_input.clear()
        self.username_input.clear()
        self.username_input.setEnabled(True)
        self.department_combo.setCurrentIndex(0)

        # 권한 체크박스 초기화
        for checkbox in self.permission_checkboxes.values():
            checkbox.setChecked(False)

        # 부서 변경 이벤트 트리거
        self.on_department_changed(self.department_combo.currentText())

        self.user_table.clearSelection()

    def save_user(self):
        """사용자 저장"""
        name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        department = self.department_combo.currentText()

        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력하세요.")
            return

        if not username:
            QMessageBox.warning(self, "입력 오류", "아이디를 입력하세요.")
            return

        # 권한 수집
        permissions = {}
        for perm_key, checkbox in self.permission_checkboxes.items():
            permissions[perm_key] = checkbox.isChecked()

        if self.selected_user_id:
            # 기존 사용자 수정
            success = User.update(
                self.selected_user_id,
                name=name,
                department=department,
                permissions=permissions
            )
            if success:
                QMessageBox.information(self, "성공", "사용자 정보가 수정되었습니다.")
                self.load_users()
            else:
                QMessageBox.critical(self, "오류", "사용자 수정에 실패했습니다.")
        else:
            # 새 사용자 추가
            user_id = User.create(
                username=username,
                password=DEFAULT_PASSWORD,
                name=name,
                role='user',
                department=department,
                permissions=permissions
            )
            if user_id:
                QMessageBox.information(self, "성공",
                    f"사용자가 추가되었습니다.\n초기 비밀번호: {DEFAULT_PASSWORD}")
                self.clear_form()
                self.load_users()
            else:
                QMessageBox.critical(self, "오류", "사용자 추가에 실패했습니다.\n(아이디 중복 확인)")

    def delete_user(self):
        """사용자 삭제"""
        if not self.selected_user_id:
            QMessageBox.warning(self, "선택 오류", "삭제할 사용자를 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "삭제 확인",
            "선택한 사용자를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if User.delete(self.selected_user_id):
                QMessageBox.information(self, "성공", "사용자가 삭제되었습니다.")
                self.clear_form()
                self.load_users()
            else:
                QMessageBox.critical(self, "오류", "사용자 삭제에 실패했습니다.")

    def reset_password(self):
        """비밀번호 초기화"""
        if not self.selected_user_id:
            QMessageBox.warning(self, "선택 오류", "비밀번호를 초기화할 사용자를 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "비밀번호 초기화",
            f"선택한 사용자의 비밀번호를 초기화하시겠습니까?\n새 비밀번호: {DEFAULT_PASSWORD}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if User.reset_password(self.selected_user_id):
                QMessageBox.information(self, "성공",
                    f"비밀번호가 초기화되었습니다.\n새 비밀번호: {DEFAULT_PASSWORD}")
            else:
                QMessageBox.critical(self, "오류", "비밀번호 초기화에 실패했습니다.")
