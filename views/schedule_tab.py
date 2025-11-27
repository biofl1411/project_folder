#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 작성 탭
'''
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QFrame, QMessageBox)
from PyQt5.QtCore import Qt

# ScheduleCreateDialog 클래스를 schedule_dialog.py에서 임포트
from .schedule_dialog import ScheduleCreateDialog

class ScheduleTab(QWidget):
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
        
        button_layout.addWidget(new_schedule_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels(["업체명", "샘플명", "시작일", "종료일", "상태"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.schedule_table)
        
        # 초기 데이터 로드
        self.load_schedules()
    
    def load_schedules(self):
        """스케줄 목록 로드"""
        # 여기에 데이터베이스에서 스케줄 로드 코드 구현
        pass
    
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