#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 관리 탭 - 스케줄 조회, 수정, 삭제, 상태 관리
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QMessageBox, QComboBox, QLineEdit, QDateEdit,
                             QDialog, QFormLayout, QTextEdit, QCheckBox, QGroupBox,
                             QFileDialog, QProgressDialog, QMenu, QAction)
from PyQt5.QtCore import Qt, QDate, QCoreApplication
from PyQt5.QtGui import QColor
import pandas as pd

from models.schedules import Schedule


class ScheduleManagementTab(QWidget):
    """스케줄 관리 탭"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_schedules()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 1. 상단 필터 영역
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")

        filter_layout = QHBoxLayout(filter_frame)

        # 검색 입력
        filter_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("업체명, 제품명 검색...")
        self.search_input.returnPressed.connect(self.apply_filter)
        filter_layout.addWidget(self.search_input)

        # 상태 필터
        filter_layout.addWidget(QLabel("상태:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["전체", "대기중", "진행중", "완료", "취소"])
        self.status_filter.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.status_filter)

        # 기간 필터
        filter_layout.addWidget(QLabel("기간:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("~"))

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addMonths(1))
        self.date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.date_to)

        # 필터 버튼
        filter_btn = QPushButton("검색")
        filter_btn.setAutoDefault(False)
        filter_btn.setDefault(False)
        filter_btn.clicked.connect(self.apply_filter)
        filter_layout.addWidget(filter_btn)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.setAutoDefault(False)
        reset_btn.setDefault(False)
        reset_btn.clicked.connect(self.reset_filter)
        filter_layout.addWidget(reset_btn)

        filter_layout.addStretch()

        layout.addWidget(filter_frame)

        # 2. 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")

        button_layout = QHBoxLayout(button_frame)

        # 전체 선택 체크박스
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.clicked.connect(self.select_all_rows)
        button_layout.addWidget(self.select_all_checkbox)

        # 새로고침 버튼
        refresh_btn = QPushButton("새로고침")
        refresh_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_btn.clicked.connect(self.load_schedules)
        button_layout.addWidget(refresh_btn)

        # 상세보기 버튼
        view_btn = QPushButton("상세보기")
        view_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        view_btn.clicked.connect(self.view_schedule_detail)
        button_layout.addWidget(view_btn)

        # 수정 버튼
        edit_btn = QPushButton("수정")
        edit_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_schedule)
        button_layout.addWidget(edit_btn)

        # 상태 변경 버튼
        status_btn = QPushButton("상태 변경")
        status_btn.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        status_btn.clicked.connect(self.change_status)
        button_layout.addWidget(status_btn)

        # 삭제 버튼
        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_schedule)
        button_layout.addWidget(delete_btn)

        # 엑셀 내보내기 버튼
        export_btn = QPushButton("엑셀 내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_to_excel)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()

        layout.addWidget(button_frame)

        # 3. 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(12)
        self.schedule_table.setHorizontalHeaderLabels([
            "선택", "ID", "업체명", "제품명", "실험방법", "보관조건",
            "시작일", "종료일", "샘플링", "보고서", "상태", "등록일"
        ])

        # 체크박스 열 너비 설정
        self.schedule_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.schedule_table.setColumnWidth(0, 50)

        # ID 열 숨김
        self.schedule_table.setColumnHidden(1, True)

        # 나머지 열 자동 조정
        for i in range(2, 12):
            self.schedule_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.doubleClicked.connect(self.view_schedule_detail)

        # 컨텍스트 메뉴 설정
        self.schedule_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedule_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.schedule_table)

        # 4. 하단 요약 정보
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.StyledPanel)
        summary_frame.setStyleSheet("background-color: #e8e8e8; border-radius: 5px;")
        summary_frame.setMaximumHeight(40)

        summary_layout = QHBoxLayout(summary_frame)

        self.total_label = QLabel("전체: 0건")
        self.pending_label = QLabel("대기중: 0건")
        self.progress_label = QLabel("진행중: 0건")
        self.completed_label = QLabel("완료: 0건")

        self.pending_label.setStyleSheet("color: #666;")
        self.progress_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.completed_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(QLabel("|"))
        summary_layout.addWidget(self.pending_label)
        summary_layout.addWidget(self.progress_label)
        summary_layout.addWidget(self.completed_label)
        summary_layout.addStretch()

        layout.addWidget(summary_frame)

    def load_schedules(self, schedules=None):
        """스케줄 목록 로드"""
        try:
            if schedules is None:
                schedules = Schedule.get_all()

            self.schedule_table.setRowCount(0)

            # 상태별 카운트
            status_counts = {'pending': 0, 'in_progress': 0, 'completed': 0, 'cancelled': 0}

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)

                # 체크박스
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.schedule_table.setCellWidget(row, 0, checkbox_widget)

                # ID (숨김)
                schedule_id = str(schedule.get('id', ''))
                self.schedule_table.setItem(row, 1, QTableWidgetItem(schedule_id))

                # 업체명
                client_name = schedule.get('client_name', '') or ''
                self.schedule_table.setItem(row, 2, QTableWidgetItem(client_name))

                # 제품명
                product_name = schedule.get('product_name', '') or schedule.get('title', '') or ''
                self.schedule_table.setItem(row, 3, QTableWidgetItem(product_name))

                # 실험방법
                test_method = schedule.get('test_method', '') or ''
                test_method_text = {
                    'real': '실측실험',
                    'acceleration': '가속실험',
                    'custom_real': '의뢰자요청(실측)',
                    'custom_acceleration': '의뢰자요청(가속)'
                }.get(test_method, test_method)
                self.schedule_table.setItem(row, 4, QTableWidgetItem(test_method_text))

                # 보관조건
                storage = schedule.get('storage_condition', '') or ''
                storage_text = {
                    'room_temp': '상온',
                    'warm': '실온',
                    'cool': '냉장',
                    'freeze': '냉동'
                }.get(storage, storage)
                self.schedule_table.setItem(row, 5, QTableWidgetItem(storage_text))

                # 시작일
                start_date = schedule.get('start_date', '') or ''
                self.schedule_table.setItem(row, 6, QTableWidgetItem(start_date))

                # 종료일
                end_date = schedule.get('end_date', '') or ''
                self.schedule_table.setItem(row, 7, QTableWidgetItem(end_date))

                # 샘플링 횟수
                sampling = str(schedule.get('sampling_count', 6) or 6)
                self.schedule_table.setItem(row, 8, QTableWidgetItem(f"{sampling}회"))

                # 보고서 종류
                reports = []
                if schedule.get('report_interim'):
                    reports.append('중간')
                if schedule.get('report_korean'):
                    reports.append('국문')
                if schedule.get('report_english'):
                    reports.append('영문')
                report_text = ', '.join(reports) if reports else '-'
                self.schedule_table.setItem(row, 9, QTableWidgetItem(report_text))

                # 상태
                status = schedule.get('status', 'pending') or 'pending'
                status_text = {
                    'pending': '대기중',
                    'in_progress': '진행중',
                    'completed': '완료',
                    'cancelled': '취소'
                }.get(status, status)

                status_item = QTableWidgetItem(status_text)
                if status == 'pending':
                    status_item.setBackground(QColor('#E0E0E0'))
                elif status == 'in_progress':
                    status_item.setBackground(QColor('#FFF3E0'))
                    status_item.setForeground(QColor('#E65100'))
                elif status == 'completed':
                    status_item.setBackground(QColor('#E8F5E9'))
                    status_item.setForeground(QColor('#2E7D32'))
                elif status == 'cancelled':
                    status_item.setBackground(QColor('#FFEBEE'))
                    status_item.setForeground(QColor('#C62828'))

                self.schedule_table.setItem(row, 10, status_item)

                # 등록일
                created_at = schedule.get('created_at', '') or ''
                if created_at and len(created_at) > 10:
                    created_at = created_at[:10]  # 날짜만 표시
                self.schedule_table.setItem(row, 11, QTableWidgetItem(created_at))

                # 상태 카운트
                if status in status_counts:
                    status_counts[status] += 1

            # 요약 정보 업데이트
            total = len(schedules)
            self.total_label.setText(f"전체: {total}건")
            self.pending_label.setText(f"대기중: {status_counts['pending']}건")
            self.progress_label.setText(f"진행중: {status_counts['in_progress']}건")
            self.completed_label.setText(f"완료: {status_counts['completed']}건")

            print(f"스케줄 {total}개 로드 완료")

        except Exception as e:
            import traceback
            print(f"스케줄 로드 중 오류: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"스케줄 목록을 불러오는 중 오류가 발생했습니다:\n{str(e)}")

    def apply_filter(self):
        """필터 적용"""
        try:
            keyword = self.search_input.text().strip()
            status_text = self.status_filter.currentText()
            date_from = self.date_from.date().toString('yyyy-MM-dd')
            date_to = self.date_to.date().toString('yyyy-MM-dd')

            # 상태 코드 변환
            status_map = {
                '전체': None,
                '대기중': 'pending',
                '진행중': 'in_progress',
                '완료': 'completed',
                '취소': 'cancelled'
            }
            status = status_map.get(status_text)

            # 필터링된 스케줄 가져오기
            schedules = Schedule.get_filtered(keyword, status, date_from, date_to)
            self.load_schedules(schedules)

        except AttributeError:
            # get_filtered 메서드가 없는 경우 기본 검색 사용
            keyword = self.search_input.text().strip()
            if keyword:
                schedules = Schedule.search(keyword)
            else:
                schedules = Schedule.get_all()
            self.load_schedules(schedules)
        except Exception as e:
            print(f"필터 적용 중 오류: {str(e)}")
            QMessageBox.warning(self, "경고", f"필터 적용 중 오류가 발생했습니다:\n{str(e)}")

    def reset_filter(self):
        """필터 초기화"""
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate().addMonths(1))
        self.load_schedules()

    def select_all_rows(self, checked):
        """모든 행 선택/해제"""
        for row in range(self.schedule_table.rowCount()):
            checkbox_widget = self.schedule_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)

    def get_selected_schedule_ids(self):
        """선택된 스케줄 ID 목록 반환"""
        selected_ids = []
        for row in range(self.schedule_table.rowCount()):
            checkbox_widget = self.schedule_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    id_item = self.schedule_table.item(row, 1)
                    if id_item:
                        selected_ids.append(int(id_item.text()))
        return selected_ids

    def view_schedule_detail(self):
        """스케줄 상세보기"""
        selected_ids = self.get_selected_schedule_ids()

        if not selected_ids:
            # 테이블에서 선택된 행 확인
            selected_rows = self.schedule_table.selectedIndexes()
            if selected_rows:
                row = selected_rows[0].row()
                id_item = self.schedule_table.item(row, 1)
                if id_item:
                    selected_ids = [int(id_item.text())]

        if not selected_ids:
            QMessageBox.warning(self, "선택 오류", "상세보기할 스케줄을 선택하세요.")
            return

        # 첫 번째 선택된 스케줄 상세보기
        schedule = Schedule.get_by_id(selected_ids[0])
        if schedule:
            dialog = ScheduleDetailDialog(self, schedule)
            dialog.exec_()

    def edit_schedule(self):
        """스케줄 수정"""
        selected_ids = self.get_selected_schedule_ids()

        if not selected_ids:
            QMessageBox.warning(self, "선택 오류", "수정할 스케줄을 선택하세요.")
            return

        if len(selected_ids) > 1:
            QMessageBox.warning(self, "선택 오류", "한 번에 하나의 스케줄만 수정할 수 있습니다.")
            return

        schedule = Schedule.get_by_id(selected_ids[0])
        if schedule:
            dialog = ScheduleEditDialog(self, schedule)
            if dialog.exec_():
                self.load_schedules()

    def change_status(self):
        """스케줄 상태 변경"""
        selected_ids = self.get_selected_schedule_ids()

        if not selected_ids:
            QMessageBox.warning(self, "선택 오류", "상태를 변경할 스케줄을 선택하세요.")
            return

        dialog = StatusChangeDialog(self)
        if dialog.exec_():
            new_status = dialog.selected_status
            success_count = 0

            for schedule_id in selected_ids:
                if Schedule.update_status(schedule_id, new_status):
                    success_count += 1

            if success_count > 0:
                QMessageBox.information(self, "상태 변경", f"{success_count}개의 스케줄 상태가 변경되었습니다.")
                self.load_schedules()
            else:
                QMessageBox.warning(self, "상태 변경 실패", "스케줄 상태 변경에 실패했습니다.")

    def delete_schedule(self):
        """스케줄 삭제"""
        selected_ids = self.get_selected_schedule_ids()

        if not selected_ids:
            QMessageBox.warning(self, "선택 오류", "삭제할 스케줄을 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "스케줄 삭제",
            f"선택한 {len(selected_ids)}개의 스케줄을 정말 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            for schedule_id in selected_ids:
                if Schedule.delete(schedule_id):
                    success_count += 1

            if success_count > 0:
                QMessageBox.information(self, "삭제 완료", f"{success_count}개의 스케줄이 삭제되었습니다.")
                self.load_schedules()
            else:
                QMessageBox.warning(self, "삭제 실패", "스케줄 삭제에 실패했습니다.")

    def export_to_excel(self):
        """엑셀 파일로 내보내기"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", "", "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'

        try:
            schedules = Schedule.get_all()

            if not schedules:
                QMessageBox.warning(self, "데이터 없음", "내보낼 스케줄 데이터가 없습니다.")
                return

            data = []
            for schedule in schedules:
                test_method = schedule.get('test_method', '') or ''
                test_method_text = {
                    'real': '실측실험',
                    'acceleration': '가속실험',
                    'custom_real': '의뢰자요청(실측)',
                    'custom_acceleration': '의뢰자요청(가속)'
                }.get(test_method, test_method)

                storage = schedule.get('storage_condition', '') or ''
                storage_text = {
                    'room_temp': '상온',
                    'warm': '실온',
                    'cool': '냉장',
                    'freeze': '냉동'
                }.get(storage, storage)

                status = schedule.get('status', 'pending') or 'pending'
                status_text = {
                    'pending': '대기중',
                    'in_progress': '진행중',
                    'completed': '완료',
                    'cancelled': '취소'
                }.get(status, status)

                data.append({
                    "업체명": schedule.get('client_name', ''),
                    "제품명": schedule.get('product_name', ''),
                    "실험방법": test_method_text,
                    "보관조건": storage_text,
                    "시작일": schedule.get('start_date', ''),
                    "종료일": schedule.get('end_date', ''),
                    "샘플링횟수": schedule.get('sampling_count', 6),
                    "상태": status_text,
                    "등록일": schedule.get('created_at', '')
                })

            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)

            QMessageBox.information(
                self, "내보내기 완료",
                f"스케줄 데이터가 엑셀 파일로 저장되었습니다.\n파일 위치: {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일로 내보내는 중 오류가 발생했습니다:\n{str(e)}")

    def show_context_menu(self, position):
        """컨텍스트 메뉴 표시"""
        menu = QMenu()

        view_action = QAction("상세보기", self)
        view_action.triggered.connect(self.view_schedule_detail)
        menu.addAction(view_action)

        edit_action = QAction("수정", self)
        edit_action.triggered.connect(self.edit_schedule)
        menu.addAction(edit_action)

        menu.addSeparator()

        status_menu = menu.addMenu("상태 변경")

        pending_action = QAction("대기중", self)
        pending_action.triggered.connect(lambda: self.quick_status_change('pending'))
        status_menu.addAction(pending_action)

        progress_action = QAction("진행중", self)
        progress_action.triggered.connect(lambda: self.quick_status_change('in_progress'))
        status_menu.addAction(progress_action)

        complete_action = QAction("완료", self)
        complete_action.triggered.connect(lambda: self.quick_status_change('completed'))
        status_menu.addAction(complete_action)

        cancel_action = QAction("취소", self)
        cancel_action.triggered.connect(lambda: self.quick_status_change('cancelled'))
        status_menu.addAction(cancel_action)

        menu.addSeparator()

        delete_action = QAction("삭제", self)
        delete_action.triggered.connect(self.delete_schedule)
        menu.addAction(delete_action)

        menu.exec_(self.schedule_table.mapToGlobal(position))

    def quick_status_change(self, status):
        """빠른 상태 변경"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        id_item = self.schedule_table.item(row, 1)
        if id_item:
            schedule_id = int(id_item.text())
            if Schedule.update_status(schedule_id, status):
                self.load_schedules()


class ScheduleDetailDialog(QDialog):
    """스케줄 상세보기 다이얼로그"""

    def __init__(self, parent=None, schedule=None):
        super().__init__(parent)
        self.schedule = schedule
        self.setWindowTitle("스케줄 상세보기")
        self.setMinimumSize(600, 500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 업체 정보
        client_group = QGroupBox("업체 정보")
        client_layout = QFormLayout(client_group)
        client_layout.addRow("업체명:", QLabel(self.schedule.get('client_name', '-')))
        layout.addWidget(client_group)

        # 제품 정보
        product_group = QGroupBox("제품 정보")
        product_layout = QFormLayout(product_group)
        product_layout.addRow("제품명:", QLabel(self.schedule.get('product_name', '-')))

        test_method = self.schedule.get('test_method', '')
        test_method_text = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_acceleration': '의뢰자요청(가속)'
        }.get(test_method, test_method or '-')
        product_layout.addRow("실험방법:", QLabel(test_method_text))

        storage = self.schedule.get('storage_condition', '')
        storage_text = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }.get(storage, storage or '-')
        product_layout.addRow("보관조건:", QLabel(storage_text))

        layout.addWidget(product_group)

        # 실험 정보
        test_group = QGroupBox("실험 정보")
        test_layout = QFormLayout(test_group)
        test_layout.addRow("시작일:", QLabel(self.schedule.get('start_date', '-')))
        test_layout.addRow("종료일:", QLabel(self.schedule.get('end_date', '-')))

        # 소비기한
        days = self.schedule.get('test_period_days', 0) or 0
        months = self.schedule.get('test_period_months', 0) or 0
        years = self.schedule.get('test_period_years', 0) or 0
        period_text = f"{years}년 {months}개월 {days}일" if (days or months or years) else "-"
        test_layout.addRow("소비기한:", QLabel(period_text))

        test_layout.addRow("샘플링 횟수:", QLabel(f"{self.schedule.get('sampling_count', 6)}회"))

        # 보고서 종류
        reports = []
        if self.schedule.get('report_interim'):
            reports.append('중간')
        if self.schedule.get('report_korean'):
            reports.append('국문')
        if self.schedule.get('report_english'):
            reports.append('영문')
        report_text = ', '.join(reports) if reports else '-'
        test_layout.addRow("보고서 종류:", QLabel(report_text))

        extension = "진행" if self.schedule.get('extension_test') else "미진행"
        test_layout.addRow("연장실험:", QLabel(extension))

        layout.addWidget(test_group)

        # 상태 정보
        status_group = QGroupBox("상태 정보")
        status_layout = QFormLayout(status_group)

        status = self.schedule.get('status', 'pending')
        status_text = {
            'pending': '대기중',
            'in_progress': '진행중',
            'completed': '완료',
            'cancelled': '취소'
        }.get(status, status)

        status_label = QLabel(status_text)
        if status == 'in_progress':
            status_label.setStyleSheet("color: #E65100; font-weight: bold;")
        elif status == 'completed':
            status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        elif status == 'cancelled':
            status_label.setStyleSheet("color: #C62828; font-weight: bold;")

        status_layout.addRow("현재 상태:", status_label)
        status_layout.addRow("등록일:", QLabel(self.schedule.get('created_at', '-')))

        layout.addWidget(status_group)

        # 닫기 버튼
        button_layout = QHBoxLayout()
        close_btn = QPushButton("닫기")
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)


class ScheduleEditDialog(QDialog):
    """스케줄 수정 다이얼로그"""

    def __init__(self, parent=None, schedule=None):
        super().__init__(parent)
        self.schedule = schedule
        self.setWindowTitle("스케줄 수정")
        self.setMinimumSize(500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # 제품명
        self.product_input = QLineEdit(self.schedule.get('product_name', ''))
        form_layout.addRow("제품명:", self.product_input)

        # 시작일
        self.start_date = QDateEdit()
        start = self.schedule.get('start_date', '')
        if start:
            self.start_date.setDate(QDate.fromString(start, 'yyyy-MM-dd'))
        else:
            self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("시작일:", self.start_date)

        # 종료일
        self.end_date = QDateEdit()
        end = self.schedule.get('end_date', '')
        if end:
            self.end_date.setDate(QDate.fromString(end, 'yyyy-MM-dd'))
        else:
            self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        form_layout.addRow("종료일:", self.end_date)

        # 상태
        self.status_combo = QComboBox()
        self.status_combo.addItems(["대기중", "진행중", "완료", "취소"])
        status = self.schedule.get('status', 'pending')
        status_index = {'pending': 0, 'in_progress': 1, 'completed': 2, 'cancelled': 3}.get(status, 0)
        self.status_combo.setCurrentIndex(status_index)
        form_layout.addRow("상태:", self.status_combo)

        layout.addLayout(form_layout)

        # 버튼
        button_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.save_schedule)

        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def save_schedule(self):
        """스케줄 저장"""
        try:
            schedule_id = self.schedule.get('id')

            # 상태 코드 변환
            status_map = {0: 'pending', 1: 'in_progress', 2: 'completed', 3: 'cancelled'}
            new_status = status_map.get(self.status_combo.currentIndex(), 'pending')

            # 상태 업데이트
            Schedule.update_status(schedule_id, new_status)

            QMessageBox.information(self, "저장 완료", "스케줄이 수정되었습니다.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"스케줄 수정 중 오류가 발생했습니다:\n{str(e)}")


class StatusChangeDialog(QDialog):
    """상태 변경 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("상태 변경")
        self.setMinimumWidth(300)
        self.selected_status = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("변경할 상태를 선택하세요:"))

        self.status_combo = QComboBox()
        self.status_combo.addItems(["대기중", "진행중", "완료", "취소"])
        layout.addWidget(self.status_combo)

        # 버튼
        button_layout = QHBoxLayout()
        confirm_btn = QPushButton("확인")
        confirm_btn.setAutoDefault(False)
        confirm_btn.setDefault(False)
        confirm_btn.clicked.connect(self.confirm_status)

        cancel_btn = QPushButton("취소")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def confirm_status(self):
        """상태 확인"""
        status_map = {0: 'pending', 1: 'in_progress', 2: 'completed', 3: 'cancelled'}
        self.selected_status = status_map.get(self.status_combo.currentIndex(), 'pending')
        self.accept()
