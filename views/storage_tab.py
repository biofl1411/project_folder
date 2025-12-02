#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
보관구 현황 탭 - 소비기한 설정 실험 보관 현황
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QFrame, QGridLayout, QGroupBox,
                           QScrollArea, QMessageBox, QDialog, QFormLayout,
                           QLineEdit, QComboBox, QSpinBox, QTextEdit,
                           QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from models.storage import Storage, STORAGE_LOCATIONS, DEFAULT_TEMPERATURES


class StorageUnitWidget(QFrame):
    """개별 보관구 위젯"""

    def __init__(self, storage_data, can_edit=False, parent=None):
        super().__init__(parent)
        self.storage_data = storage_data
        self.can_edit = can_edit
        self.parent_tab = parent
        self.initUI()

    def initUI(self):
        """UI 초기화"""
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # 온도 표시
        temp = self.storage_data.get('temperature', '')
        temp_label = QLabel(temp)
        temp_label.setAlignment(Qt.AlignCenter)
        temp_label.setStyleSheet(self.get_temp_style(temp))
        temp_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(temp_label)

        # 사용량 / 용량
        capacity = self.storage_data.get('capacity', 100)
        usage = self.storage_data.get('current_usage', 0)

        # 프로그레스 바
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(capacity)
        progress.setValue(usage)
        progress.setTextVisible(False)
        progress.setFixedHeight(15)

        # 사용률에 따른 색상
        usage_percent = (usage / capacity * 100) if capacity > 0 else 0
        if usage_percent >= 90:
            progress_color = "#e74c3c"  # 빨강
        elif usage_percent >= 70:
            progress_color = "#f39c12"  # 주황
        else:
            progress_color = "#27ae60"  # 초록

        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(progress)

        # 용량 텍스트
        usage_label = QLabel(f"{usage} / {capacity}")
        usage_label.setAlignment(Qt.AlignCenter)
        usage_label.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(usage_label)

        # 잔여량
        remaining = capacity - usage
        remaining_label = QLabel(f"잔여: {remaining}")
        remaining_label.setAlignment(Qt.AlignCenter)
        remaining_label.setStyleSheet(f"font-size: 10px; color: {progress_color}; font-weight: bold;")
        layout.addWidget(remaining_label)

        # 메모 표시 (? 아이콘)
        notes = self.storage_data.get('notes', '')
        help_label = QLabel("?")
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setFixedSize(18, 18)
        help_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #3498db;
                border-radius: 9px;
                font-size: 11px;
                font-weight: bold;
            }
            QLabel:hover {
                background-color: #2980b9;
            }
        """)
        if notes:
            help_label.setToolTip(notes)
        else:
            help_label.setToolTip("메모 없음")

        # ? 아이콘 중앙 정렬을 위한 컨테이너
        help_container = QWidget()
        help_layout = QHBoxLayout(help_container)
        help_layout.setContentsMargins(0, 0, 0, 0)
        help_layout.addStretch()
        help_layout.addWidget(help_label)
        help_layout.addStretch()
        layout.addWidget(help_container)

        # 수정 버튼 (권한 있는 경우만)
        if self.can_edit:
            edit_btn = QPushButton("수정")
            edit_btn.setFixedHeight(25)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            edit_btn.clicked.connect(self.edit_storage)
            layout.addWidget(edit_btn)

        # 전체 스타일
        self.setStyleSheet("""
            StorageUnitWidget {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
            }
            StorageUnitWidget:hover {
                border-color: #3498db;
            }
        """)

        self.setFixedSize(120, 200 if self.can_edit else 170)

    def get_temp_style(self, temp):
        """온도에 따른 스타일 반환"""
        try:
            temp_value = int(temp.replace('°C', '').replace(' ', ''))
            if temp_value <= -10:
                return "color: #2980b9; background-color: #d6eaf8; padding: 5px; border-radius: 5px;"
            elif temp_value <= 0:
                return "color: #1abc9c; background-color: #d1f2eb; padding: 5px; border-radius: 5px;"
            elif temp_value <= 15:
                return "color: #27ae60; background-color: #d5f5e3; padding: 5px; border-radius: 5px;"
            elif temp_value <= 30:
                return "color: #f39c12; background-color: #fef9e7; padding: 5px; border-radius: 5px;"
            else:
                return "color: #e74c3c; background-color: #fdedec; padding: 5px; border-radius: 5px;"
        except (ValueError, TypeError):
            return "color: #333; background-color: #eee; padding: 5px; border-radius: 5px;"

    def edit_storage(self):
        """보관구 수정 다이얼로그"""
        if self.parent_tab:
            self.parent_tab.show_edit_dialog(self.storage_data)


class StorageEditDialog(QDialog):
    """보관구 수정 다이얼로그"""

    def __init__(self, storage_data, current_user, parent=None):
        super().__init__(parent)
        self.storage_data = storage_data
        self.current_user = current_user
        self.setWindowTitle("보관구 수정")
        self.setMinimumWidth(400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 위치
        self.location_combo = QComboBox()
        self.location_combo.addItems(STORAGE_LOCATIONS)
        self.location_combo.setEditable(True)
        current_location = self.storage_data.get('location', '')
        index = self.location_combo.findText(current_location)
        if index >= 0:
            self.location_combo.setCurrentIndex(index)
        else:
            self.location_combo.setCurrentText(current_location)
        form.addRow("위치:", self.location_combo)

        # 온도
        self.temp_combo = QComboBox()
        self.temp_combo.addItems(DEFAULT_TEMPERATURES)
        self.temp_combo.setEditable(True)
        current_temp = self.storage_data.get('temperature', '')
        index = self.temp_combo.findText(current_temp)
        if index >= 0:
            self.temp_combo.setCurrentIndex(index)
        else:
            self.temp_combo.setCurrentText(current_temp)
        form.addRow("온도:", self.temp_combo)

        # 용량
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 10000)
        self.capacity_spin.setValue(self.storage_data.get('capacity', 100))
        form.addRow("총 용량:", self.capacity_spin)

        # 현재 사용량
        self.usage_spin = QSpinBox()
        self.usage_spin.setRange(0, 10000)
        self.usage_spin.setValue(self.storage_data.get('current_usage', 0))
        form.addRow("현재 사용량:", self.usage_spin)

        # 변경 사유
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("사용량 변경 시 사유 입력")
        self.reason_input.returnPressed.connect(self.save)  # Enter 키로 저장
        form.addRow("변경 사유:", self.reason_input)

        # 메모
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("메모 (선택사항)")
        self.notes_input.setText(self.storage_data.get('notes', ''))
        self.notes_input.setMaximumHeight(80)
        form.addRow("메모:", self.notes_input)

        layout.addLayout(form)

        # 버튼
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton("저장")
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white;")
        self.save_btn.clicked.connect(self.save)
        self.save_btn.setDefault(True)  # 기본 버튼으로 설정 (Enter 키)
        self.save_btn.setAutoDefault(True)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def save(self):
        """저장"""
        storage_id = self.storage_data.get('id')
        if not storage_id:
            QMessageBox.warning(self, "오류", "보관구 ID가 없습니다.")
            return

        location = self.location_combo.currentText()
        temperature = self.temp_combo.currentText()
        capacity = self.capacity_spin.value()
        new_usage = self.usage_spin.value()
        notes = self.notes_input.toPlainText()
        reason = self.reason_input.text()

        if new_usage > capacity:
            QMessageBox.warning(self, "오류", "사용량이 용량을 초과할 수 없습니다.")
            return

        # 기본 정보 업데이트
        Storage.update(storage_id, location=location, temperature=temperature,
                      capacity=capacity, notes=notes)

        # 사용량이 변경된 경우 로그 기록
        old_usage = self.storage_data.get('current_usage', 0)
        if new_usage != old_usage:
            changed_by = self.current_user.get('name', '') if self.current_user else ''
            Storage.update_usage(storage_id, new_usage, changed_by, reason)

        self.accept()


class StorageTab(QWidget):
    """보관구 현황 탭"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.initUI()
        self.load_storage_data()

    def set_current_user(self, user):
        """현재 사용자 설정"""
        self.current_user = user
        self.load_storage_data()

    def can_edit_storage(self):
        """보관구 수정 권한 확인"""
        if not self.current_user:
            return False

        # 관리자는 항상 수정 가능
        if self.current_user.get('role') == 'admin':
            return True

        # storage_edit 권한 확인
        from models.users import User
        return User.has_permission(self.current_user, 'storage_edit')

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 상단 헤더
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #34495e; border-radius: 5px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("보관구 현황")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 새로고침 버튼
        refresh_btn = QPushButton("새로고침")
        refresh_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px 15px;")
        refresh_btn.clicked.connect(self.load_storage_data)
        header_layout.addWidget(refresh_btn)

        # 보관구 추가 버튼
        self.add_btn = QPushButton("+ 보관구 추가")
        self.add_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 15px;")
        self.add_btn.clicked.connect(self.add_storage)
        header_layout.addWidget(self.add_btn)

        layout.addWidget(header_frame)

        # 온도별 요약
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("background-color: #ecf0f1; border-radius: 5px; padding: 10px;")
        self.summary_layout = QHBoxLayout(self.summary_frame)
        layout.addWidget(self.summary_frame)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def load_storage_data(self):
        """보관구 데이터 로드"""
        # 기본 데이터 초기화
        Storage.initialize_default_storage()

        # 기존 위젯 제거
        self.clear_layout(self.content_layout)
        self.clear_layout(self.summary_layout)

        can_edit = self.can_edit_storage()

        # 추가 버튼 활성화/비활성화
        self.add_btn.setEnabled(can_edit)
        self.add_btn.setVisible(can_edit)

        # 온도별 요약 표시
        self.load_summary()

        # 위치별 보관구 표시
        locations = Storage.get_locations()

        for location in locations:
            units = Storage.get_by_location(location)
            if not units:
                continue

            # 위치 그룹박스
            group = QGroupBox(f"- {location} -")
            group.setStyleSheet("""
                QGroupBox {
                    font-size: 14px;
                    font-weight: bold;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    margin-top: 15px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 20px;
                    padding: 0 10px;
                    color: #2980b9;
                }
            """)

            group_layout = QHBoxLayout(group)
            group_layout.setSpacing(15)
            group_layout.setContentsMargins(15, 20, 15, 15)

            for unit in units:
                widget = StorageUnitWidget(unit, can_edit, self)
                group_layout.addWidget(widget)

            group_layout.addStretch()
            self.content_layout.addWidget(group)

        self.content_layout.addStretch()

    def load_summary(self):
        """온도별 요약 로드"""
        summary = Storage.get_summary_by_temperature()

        summary_title = QLabel("온도별 현황: ")
        summary_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.summary_layout.addWidget(summary_title)

        for s in summary:
            temp = s.get('temperature', '')
            count = s.get('unit_count', 0)
            total_cap = s.get('total_capacity', 0)
            total_use = s.get('total_usage', 0)
            remaining = total_cap - total_use

            label = QLabel(f"{temp}: {count}대 (잔여 {remaining}/{total_cap})")
            label.setStyleSheet("""
                background-color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 11px;
            """)
            self.summary_layout.addWidget(label)

        self.summary_layout.addStretch()

    def show_edit_dialog(self, storage_data):
        """수정 다이얼로그 표시"""
        dialog = StorageEditDialog(storage_data, self.current_user, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_storage_data()

    def add_storage(self):
        """새 보관구 추가"""
        if not self.can_edit_storage():
            QMessageBox.warning(self, "권한 없음", "보관구를 추가할 권한이 없습니다.")
            return

        # 빈 데이터로 수정 다이얼로그 열기
        new_storage = {
            'id': None,
            'location': STORAGE_LOCATIONS[0] if STORAGE_LOCATIONS else '',
            'temperature': '25°C',
            'capacity': 100,
            'current_usage': 0,
            'notes': ''
        }

        dialog = StorageEditDialog(new_storage, self.current_user, self)
        dialog.setWindowTitle("새 보관구 추가")

        # save 메서드 오버라이드
        def save_new():
            location = dialog.location_combo.currentText()
            temperature = dialog.temp_combo.currentText()
            capacity = dialog.capacity_spin.value()
            usage = dialog.usage_spin.value()
            notes = dialog.notes_input.toPlainText()

            if usage > capacity:
                QMessageBox.warning(dialog, "오류", "사용량이 용량을 초과할 수 없습니다.")
                return

            storage_id = Storage.create(location, temperature, capacity, usage, notes)
            if storage_id:
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "오류", "보관구 추가에 실패했습니다.")

        # 저장 버튼 연결 변경
        for btn in dialog.findChildren(QPushButton):
            if btn.text() == "저장":
                try:
                    btn.clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                btn.clicked.connect(save_new)
                break

        if dialog.exec_() == QDialog.Accepted:
            self.load_storage_data()

    def clear_layout(self, layout):
        """레이아웃 내 위젯 제거"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
