#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 작성 탭
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                           QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QDate

# 순환 참조 방지를 위해 이 부분 제거
# from .schedule_dialog import ScheduleCreateDialog

class ScheduleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 상단 버튼 영역
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        button_layout = QHBoxLayout(button_frame)
        
        new_schedule_btn = QPushButton("새 스케줄 작성")
        new_schedule_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        new_schedule_btn.clicked.connect(self.create_new_schedule)
        
        view_btn = QPushButton("보기")
        view_btn.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        
        export_btn = QPushButton("내보내기")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        
        delete_btn = QPushButton("삭제")
        delete_btn.setIcon(self.style().standardIcon(self.style().SP_TrashIcon))
        
        button_layout.addWidget(new_schedule_btn)
        button_layout.addWidget(view_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # 2. 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels(["업체명", "샘플명", "시작일", "종료일", "상태"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.schedule_table)
        
        # 3. 안내 메시지
        info_label = QLabel("새 스케줄을 작성하려면 '새 스케줄 작성' 버튼을 클릭하세요.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray;")
        
        layout.addWidget(info_label)
        
        # 샘플 데이터 추가
        self.add_sample_data()
    
    def create_new_schedule(self):
        """새 스케줄 작성 다이얼로그 표시"""
        # 여기서 임포트 (지연 임포트)
        from .schedule_dialog import ScheduleCreateDialog
        
        dialog = ScheduleCreateDialog(self)
        result = dialog.exec_()
        
        if result:
            # 스케줄이 성공적으로 생성됨
            QMessageBox.information(self, "스케줄 생성", "새 스케줄이 성공적으로 생성되었습니다.")
            # 여기서 테이블 갱신 등 필요한 처리 수행
    
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