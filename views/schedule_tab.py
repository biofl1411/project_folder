#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 작성 탭
'''
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QFrame, QMessageBox, QComboBox, QCheckBox, QLabel,
                           QApplication)
from PyQt5.QtCore import Qt, pyqtSignal

# ScheduleCreateDialog 클래스를 schedule_dialog.py에서 임포트
from .schedule_dialog import ScheduleCreateDialog

class ScheduleTab(QWidget):
    # 더블클릭 시 스케줄 ID를 전달하는 시그널
    schedule_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        button_layout = QHBoxLayout(button_frame)

        new_schedule_btn = QPushButton("새 스케줄 작성")
        new_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_schedule_btn.clicked.connect(self.create_new_schedule)

        edit_schedule_btn = QPushButton("수정하기")
        edit_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogContentsView))
        edit_schedule_btn.setStyleSheet("background-color: #3498db; color: white;")
        edit_schedule_btn.clicked.connect(self.edit_selected_schedule)

        delete_schedule_btn = QPushButton("선택 삭제")
        delete_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        delete_schedule_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        delete_schedule_btn.clicked.connect(self.delete_selected_schedule)

        button_layout.addWidget(new_schedule_btn)
        button_layout.addWidget(edit_schedule_btn)
        button_layout.addWidget(delete_schedule_btn)

        # 구분선
        button_layout.addSpacing(20)

        # 상태 변경 영역
        button_layout.addWidget(QLabel("상태 변경:"))

        self.status_combo = QComboBox()
        self.status_combo.addItems(["대기", "입고예정", "입고", "종료"])
        self.status_combo.setMinimumWidth(100)
        button_layout.addWidget(self.status_combo)

        change_status_btn = QPushButton("일괄 변경")
        change_status_btn.setStyleSheet("background-color: #27ae60; color: white;")
        change_status_btn.clicked.connect(self.change_selected_status)
        button_layout.addWidget(change_status_btn)

        button_layout.addStretch()

        layout.addWidget(button_frame)
        
        # 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels(["선택", "ID", "업체명", "샘플명", "시작일", "종료일", "상태"])
        self.schedule_table.setColumnHidden(1, True)  # ID 열 숨김
        self.schedule_table.setColumnWidth(0, 50)  # 선택 열 너비 고정
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 더블클릭 이벤트 연결
        self.schedule_table.doubleClicked.connect(self.on_double_click)

        layout.addWidget(self.schedule_table)
        
        # 초기 데이터 로드
        self.load_schedules()
    
    def load_schedules(self):
        """스케줄 목록 로드"""
        try:
            from models.schedules import Schedule

            schedules = Schedule.get_all()
            self.schedule_table.setRowCount(0)

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)

                # 체크박스 (선택 열)
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.schedule_table.setCellWidget(row, 0, checkbox_widget)

                # ID (숨김 열)
                schedule_id = schedule.get('id', '')
                self.schedule_table.setItem(row, 1, QTableWidgetItem(str(schedule_id)))

                # 업체명
                client_name = schedule.get('client_name', '') or ''
                self.schedule_table.setItem(row, 2, QTableWidgetItem(client_name))

                # 제품명/샘플명
                product_name = schedule.get('product_name', '') or schedule.get('title', '') or ''
                self.schedule_table.setItem(row, 3, QTableWidgetItem(product_name))

                # 시작일
                start_date = schedule.get('start_date', '') or ''
                self.schedule_table.setItem(row, 4, QTableWidgetItem(start_date))

                # 종료일
                end_date = schedule.get('end_date', '') or ''
                self.schedule_table.setItem(row, 5, QTableWidgetItem(end_date))

                # 상태 (새로운 상태값 매핑)
                status = schedule.get('status', 'pending') or 'pending'
                status_text = {
                    'pending': '대기',
                    'scheduled': '입고예정',
                    'received': '입고',
                    'completed': '종료',
                    # 기존 상태 호환
                    'in_progress': '입고',
                    'cancelled': '종료'
                }.get(status, status)

                status_item = QTableWidgetItem(status_text)
                if status in ['scheduled']:
                    status_item.setBackground(Qt.cyan)
                elif status in ['received', 'in_progress']:
                    status_item.setBackground(Qt.yellow)
                elif status in ['completed', 'cancelled']:
                    status_item.setBackground(Qt.green)

                self.schedule_table.setItem(row, 6, status_item)

            print(f"스케줄 {len(schedules)}개 로드 완료")
        except Exception as e:
            import traceback
            print(f"스케줄 로드 중 오류: {str(e)}")
            traceback.print_exc()

    def on_double_click(self, index):
        """더블클릭 시 스케줄 관리 탭으로 이동"""
        row = index.row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if schedule_id_item:
            schedule_id = int(schedule_id_item.text())
            self.schedule_double_clicked.emit(schedule_id)

    def delete_selected_schedule(self):
        """선택된 스케줄 삭제"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "삭제 실패", "삭제할 스케줄을 선택하세요.")
            return

        row = selected_rows[0].row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if not schedule_id_item:
            return

        schedule_id = int(schedule_id_item.text())
        client_name = self.schedule_table.item(row, 2).text()  # 업체명은 2번 열
        product_name = self.schedule_table.item(row, 3).text()  # 제품명은 3번 열

        reply = QMessageBox.question(
            self, '삭제 확인',
            f'다음 스케줄을 삭제하시겠습니까?\n\n업체: {client_name}\n제품: {product_name}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from models.schedules import Schedule
                success = Schedule.delete(schedule_id)
                if success:
                    QMessageBox.information(self, "삭제 완료", "스케줄이 삭제되었습니다.")
                    self.load_schedules()
                else:
                    QMessageBox.warning(self, "삭제 실패", "스케줄 삭제에 실패했습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"삭제 중 오류가 발생했습니다:\n{str(e)}")

    def create_new_schedule(self):
        """새 스케줄 작성 다이얼로그 표시"""
        try:
            print("스케줄 생성 시작")  # 디버깅 로그
            dialog = ScheduleCreateDialog(self)
            print("ScheduleCreateDialog 인스턴스 생성 성공")  # 디버깅 로그

            if dialog.exec_():
                print("다이얼로그 실행 성공")  # 디버깅 로그
                # 스케줄 저장 후 목록 새로고침
                self.load_schedules()
        except Exception as e:
            import traceback
            error_msg = f"스케줄 생성 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)  # 콘솔에 오류 출력
            QMessageBox.critical(self, "오류", error_msg)

    def edit_selected_schedule(self):
        """선택된 스케줄 수정 다이얼로그 표시"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "수정 실패", "수정할 스케줄을 선택하세요.")
            return

        row = selected_rows[0].row()
        schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
        if not schedule_id_item:
            return

        schedule_id = int(schedule_id_item.text())

        try:
            print(f"스케줄 수정 시작: ID {schedule_id}")
            dialog = ScheduleCreateDialog(self, schedule_id=schedule_id)

            if dialog.exec_():
                print("스케줄 수정 완료")
                self.load_schedules()
        except Exception as e:
            import traceback
            error_msg = f"스케줄 수정 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "오류", error_msg)

    def change_selected_status(self):
        """체크된 스케줄들의 상태를 일괄 변경"""
        try:
            from models.schedules import Schedule

            # 선택된 상태 가져오기
            selected_status_text = self.status_combo.currentText()
            status_map = {
                '대기': 'pending',
                '입고예정': 'scheduled',
                '입고': 'received',
                '종료': 'completed'
            }
            new_status = status_map.get(selected_status_text, 'pending')

            # 체크된 행 찾기
            checked_rows = []
            for row in range(self.schedule_table.rowCount()):
                checkbox_widget = self.schedule_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        checked_rows.append(row)

            if not checked_rows:
                QMessageBox.warning(self, "변경 실패", "변경할 스케줄을 체크하세요.")
                return

            # 확인 대화상자
            reply = QMessageBox.question(
                self, '상태 변경 확인',
                f'{len(checked_rows)}개의 스케줄 상태를 "{selected_status_text}"(으)로 변경하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success_count = 0
                for row in checked_rows:
                    schedule_id_item = self.schedule_table.item(row, 1)  # ID는 1번 열
                    if schedule_id_item:
                        schedule_id = int(schedule_id_item.text())
                        if Schedule.update_status(schedule_id, new_status):
                            success_count += 1

                QMessageBox.information(
                    self, "변경 완료",
                    f"{success_count}개의 스케줄 상태가 변경되었습니다."
                )
                self.load_schedules()

        except Exception as e:
            import traceback
            error_msg = f"상태 변경 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "오류", error_msg)

    def add_sample_data(self):
        """샘플 데이터 추가 (테스트용)"""
        sample_data = [
            {"client": "계림농장", "sample": "계란 샘플", "start": "2023-07-10", "end": "2023-07-30", "status": "진행중"},
            {"client": "거성씨푸드", "sample": "생선 샘플", "start": "2023-07-05", "end": "2023-07-25", "status": "완료"}
        ]
        
        self.schedule_table.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(data["client"]))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(data["sample"]))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(data["start"]))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(data["end"]))
            
            status_item = QTableWidgetItem(data["status"])
            if data["status"] == "진행중":
                status_item.setBackground(Qt.yellow)
            elif data["status"] == "완료":
                status_item.setBackground(Qt.green)
            
            self.schedule_table.setItem(row, 4, status_item)