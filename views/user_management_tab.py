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
from PyQt5.QtGui import QColor, QFont

from models.users import (User, DEPARTMENTS, PERMISSION_LABELS, DEFAULT_PASSWORD,
                         PERMISSION_CATEGORIES, PERMISSION_BY_CATEGORY,
                         get_default_permissions)


class UserManagementTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.selected_user_id = None
        self.permission_checkboxes = {}
        self.category_checkboxes = {}  # 카테고리 전체선택 체크박스
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
        info_layout.addRow("부서:", self.department_combo)

        # 초기 비밀번호 안내
        pwd_label = QLabel(f"초기 비밀번호: {DEFAULT_PASSWORD}")
        pwd_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addRow("", pwd_label)

        right_layout.addWidget(info_group)

        # 권한 설정 그룹
        perm_group = QGroupBox("권한 설정")
        perm_layout = QVBoxLayout(perm_group)

        # 전체 선택/해제 버튼
        all_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(lambda: self.toggle_all_permissions(True))
        all_btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("전체 해제")
        deselect_all_btn.clicked.connect(lambda: self.toggle_all_permissions(False))
        all_btn_layout.addWidget(deselect_all_btn)
        perm_layout.addLayout(all_btn_layout)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        perm_widget = QWidget()
        perm_main_layout = QVBoxLayout(perm_widget)
        perm_main_layout.setSpacing(10)

        # 카테고리별 권한 그룹 생성
        for cat_key, cat_name in PERMISSION_CATEGORIES.items():
            cat_group = QGroupBox(cat_name)
            cat_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            cat_layout = QVBoxLayout(cat_group)

            # 카테고리 전체 선택 체크박스
            cat_header = QHBoxLayout()
            cat_all_checkbox = QCheckBox("전체")
            cat_all_checkbox.setStyleSheet("font-weight: bold; color: #2196F3;")
            cat_all_checkbox.stateChanged.connect(
                lambda state, ck=cat_key: self.toggle_category_permissions(ck, state == Qt.Checked)
            )
            self.category_checkboxes[cat_key] = cat_all_checkbox
            cat_header.addWidget(cat_all_checkbox)
            cat_header.addStretch()
            cat_layout.addLayout(cat_header)

            # 권한 체크박스들
            perm_keys = PERMISSION_BY_CATEGORY.get(cat_key, [])
            perm_grid = QGridLayout()
            perm_grid.setSpacing(5)

            row = 0
            col = 0
            for perm_key in perm_keys:
                perm_label = PERMISSION_LABELS.get(perm_key, perm_key)

                checkbox = QCheckBox(perm_label)
                checkbox.setStyleSheet("""
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
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
                checkbox.stateChanged.connect(
                    lambda state, ck=cat_key: self.update_category_checkbox(ck)
                )

                self.permission_checkboxes[perm_key] = checkbox
                perm_grid.addWidget(checkbox, row, col)

                col += 1
                if col >= 2:  # 2열로 배치
                    col = 0
                    row += 1

            cat_layout.addLayout(perm_grid)
            perm_main_layout.addWidget(cat_group)

        perm_main_layout.addStretch()
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

    def toggle_all_permissions(self, checked):
        """모든 권한 전체 선택/해제"""
        for checkbox in self.permission_checkboxes.values():
            checkbox.setChecked(checked)

    def toggle_category_permissions(self, category_key, checked):
        """카테고리별 권한 전체 선택/해제"""
        perm_keys = PERMISSION_BY_CATEGORY.get(category_key, [])
        for perm_key in perm_keys:
            if perm_key in self.permission_checkboxes:
                self.permission_checkboxes[perm_key].setChecked(checked)

    def update_category_checkbox(self, category_key):
        """카테고리 내 개별 체크박스 상태에 따라 전체 체크박스 업데이트"""
        perm_keys = PERMISSION_BY_CATEGORY.get(category_key, [])
        all_checked = all(
            self.permission_checkboxes.get(pk, QCheckBox()).isChecked()
            for pk in perm_keys
        )

        if category_key in self.category_checkboxes:
            # 시그널 순환 방지
            self.category_checkboxes[category_key].blockSignals(True)
            self.category_checkboxes[category_key].setChecked(all_checked)
            self.category_checkboxes[category_key].blockSignals(False)

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

            # 카테고리 체크박스 업데이트
            for cat_key in PERMISSION_CATEGORIES.keys():
                self.update_category_checkbox(cat_key)

    def clear_form(self):
        """입력 폼 초기화"""
        self.selected_user_id = None
        self.name_input.clear()
        self.username_input.clear()
        self.username_input.setEnabled(True)
        self.department_combo.setCurrentIndex(0)

        # 권한 체크박스 초기화 (모두 해제)
        for checkbox in self.permission_checkboxes.values():
            checkbox.setChecked(False)

        # 카테고리 체크박스 업데이트
        for cat_key in PERMISSION_CATEGORIES.keys():
            self.update_category_checkbox(cat_key)

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
