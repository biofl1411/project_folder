#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
스케줄 관리 탭 - 스케줄 조회, 수정, 삭제, 상태 관리
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QMessageBox, QComboBox, QLineEdit, QDateEdit,
                             QDialog, QFormLayout, QTextEdit, QCheckBox, QGroupBox,
                             QFileDialog, QGridLayout, QSpinBox, QSplitter,
                             QScrollArea)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
import pandas as pd

from models.schedules import Schedule


class ScheduleManagementTab(QWidget):
    """스케줄 관리 탭"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule = None  # 현재 선택된 스케줄
        self.initUI()

    def initUI(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)

        # 스플리터로 상단/하단 분리
        splitter = QSplitter(Qt.Vertical)

        # ============ 상단 영역 (스크롤 가능) ============
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setSpacing(10)

        # 1. 소비기한 설정 실험 계획 (안) - 정보 요약 패널
        self.create_info_summary_panel(top_layout)

        # 2. 보관 온도 구간
        self.create_temperature_panel(top_layout)

        # 3. 메모 입력폼
        self.create_memo_panel(top_layout)

        splitter.addWidget(top_widget)

        # ============ 하단 영역 (스케줄 목록) ============
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # 스케줄 선택 영역
        self.create_schedule_selector(bottom_layout)

        splitter.addWidget(bottom_widget)

        # 스플리터 비율 설정 (상단 70%, 하단 30%)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)

    def create_info_summary_panel(self, parent_layout):
        """소비기한 설정 실험 계획 (안) - 정보 요약 패널"""
        group = QGroupBox("1. 소비기한 설정 실험 계획 (안)")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2980b9;
            }
        """)

        grid = QGridLayout(group)
        grid.setSpacing(5)

        # 스타일 정의
        label_style = "font-weight: bold; background-color: #ecf0f1; padding: 5px; border: 1px solid #bdc3c7;"
        value_style = "background-color: white; padding: 5px; border: 1px solid #bdc3c7; color: #2c3e50;"

        # 행 1: 회사명, 실험방법, 제품명
        row = 0
        grid.addWidget(self._create_label("회사명", label_style), row, 0)
        self.company_value = self._create_value_label("-", value_style)
        grid.addWidget(self.company_value, row, 1)

        grid.addWidget(self._create_label("실험방법", label_style), row, 2)
        self.test_method_value = self._create_value_label("-", value_style)
        grid.addWidget(self.test_method_value, row, 3)

        grid.addWidget(self._create_label("제품명", label_style), row, 4)
        self.product_value = self._create_value_label("-", value_style)
        grid.addWidget(self.product_value, row, 5)

        # 행 2: 소비기한, 보관조건, 식품유형
        row = 1
        grid.addWidget(self._create_label("소비기한", label_style), row, 0)
        self.expiry_value = self._create_value_label("-", value_style)
        grid.addWidget(self.expiry_value, row, 1)

        grid.addWidget(self._create_label("보관조건", label_style), row, 2)
        self.storage_value = self._create_value_label("-", value_style)
        grid.addWidget(self.storage_value, row, 3)

        grid.addWidget(self._create_label("식품유형", label_style), row, 4)
        self.food_type_value = self._create_value_label("-", value_style)
        grid.addWidget(self.food_type_value, row, 5)

        # 행 3: 설정기간, 중간보고서, 연장실험
        row = 2
        grid.addWidget(self._create_label("실험기간", label_style), row, 0)
        self.period_value = self._create_value_label("-", value_style)
        grid.addWidget(self.period_value, row, 1)

        grid.addWidget(self._create_label("중간보고서", label_style), row, 2)
        self.interim_report_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_report_value, row, 3)

        grid.addWidget(self._create_label("연장실험", label_style), row, 4)
        self.extension_value = self._create_value_label("-", value_style)
        grid.addWidget(self.extension_value, row, 5)

        # 행 4: 샘플링간격, 중간보고일, 마지막실험일
        row = 3
        grid.addWidget(self._create_label("샘플링횟수", label_style), row, 0)
        self.sampling_count_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_count_value, row, 1)

        grid.addWidget(self._create_label("샘플링간격", label_style), row, 2)
        self.sampling_interval_value = self._create_value_label("-", value_style)
        grid.addWidget(self.sampling_interval_value, row, 3)

        grid.addWidget(self._create_label("시작일", label_style), row, 4)
        self.start_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.start_date_value, row, 5)

        # 행 5: 중간보고일, 마지막실험일
        row = 4
        grid.addWidget(self._create_label("중간보고일", label_style), row, 0)
        self.interim_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.interim_date_value, row, 1)

        grid.addWidget(self._create_label("마지막실험일", label_style), row, 2)
        self.last_test_date_value = self._create_value_label("-", value_style)
        grid.addWidget(self.last_test_date_value, row, 3)

        grid.addWidget(self._create_label("상태", label_style), row, 4)
        self.status_value = self._create_value_label("-", value_style)
        grid.addWidget(self.status_value, row, 5)

        parent_layout.addWidget(group)

    def create_temperature_panel(self, parent_layout):
        """보관 온도 구간 패널"""
        group = QGroupBox("2. 보관 온도")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #27ae60;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #27ae60;
            }
        """)

        grid = QGridLayout(group)
        grid.setSpacing(5)

        label_style = "font-weight: bold; background-color: #d5f5e3; padding: 5px; border: 1px solid #27ae60;"
        value_style = "background-color: white; padding: 5px; border: 1px solid #27ae60; color: #27ae60; font-weight: bold;"

        # 헤더 행
        grid.addWidget(self._create_label("구분", label_style), 0, 0)
        grid.addWidget(self._create_label("1구간", label_style), 0, 1)
        grid.addWidget(self._create_label("2구간", label_style), 0, 2)
        grid.addWidget(self._create_label("3구간", label_style), 0, 3)

        # 온도 행
        grid.addWidget(self._create_label("온도", label_style), 1, 0)
        self.temp_zone1_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone1_value, 1, 1)
        self.temp_zone2_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone2_value, 1, 2)
        self.temp_zone3_value = self._create_value_label("-", value_style)
        grid.addWidget(self.temp_zone3_value, 1, 3)

        parent_layout.addWidget(group)

    def create_memo_panel(self, parent_layout):
        """메모 입력폼"""
        group = QGroupBox("3. 메모")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #9b59b6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #9b59b6;
            }
        """)

        layout = QVBoxLayout(group)

        # 메모 텍스트 에디터
        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("메모를 입력하세요...")
        self.memo_edit.setMaximumHeight(100)
        layout.addWidget(self.memo_edit)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_memo_btn = QPushButton("메모 저장")
        save_memo_btn.setAutoDefault(False)
        save_memo_btn.setDefault(False)
        save_memo_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 5px 15px;")
        save_memo_btn.clicked.connect(self.save_memo)
        btn_layout.addWidget(save_memo_btn)

        layout.addLayout(btn_layout)

        parent_layout.addWidget(group)

    def create_schedule_selector(self, parent_layout):
        """스케줄 선택 영역"""
        group = QGroupBox("스케줄 선택")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #34495e;
            }
        """)

        layout = QVBoxLayout(group)

        # 검색/필터 영역
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("업체명, 제품명 검색...")
        self.search_input.returnPressed.connect(self.search_schedules)
        filter_layout.addWidget(self.search_input)

        search_btn = QPushButton("검색")
        search_btn.setAutoDefault(False)
        search_btn.setDefault(False)
        search_btn.clicked.connect(self.search_schedules)
        filter_layout.addWidget(search_btn)

        refresh_btn = QPushButton("새로고침")
        refresh_btn.setAutoDefault(False)
        refresh_btn.setDefault(False)
        refresh_btn.clicked.connect(self.load_schedules)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # 스케줄 목록 테이블
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels([
            "ID", "업체명", "제품명", "실험방법", "시작일", "상태"
        ])

        # ID 열 숨김
        self.schedule_table.setColumnHidden(0, True)

        # 열 너비 설정
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.setMaximumHeight(200)

        # 선택 시 상단 패널 업데이트
        self.schedule_table.itemSelectionChanged.connect(self.on_schedule_selected)

        layout.addWidget(self.schedule_table)

        parent_layout.addWidget(group)

        # 초기 데이터 로드
        self.load_schedules()

    def _create_label(self, text, style):
        """스타일이 적용된 라벨 생성"""
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        return label

    def _create_value_label(self, text, style):
        """값 표시용 라벨 생성"""
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumWidth(100)
        return label

    def load_schedules(self):
        """스케줄 목록 로드"""
        try:
            schedules = Schedule.get_all()
            self.schedule_table.setRowCount(0)

            for row, schedule in enumerate(schedules):
                self.schedule_table.insertRow(row)

                # ID
                self.schedule_table.setItem(row, 0, QTableWidgetItem(str(schedule.get('id', ''))))

                # 업체명
                self.schedule_table.setItem(row, 1, QTableWidgetItem(schedule.get('client_name', '') or '-'))

                # 제품명
                self.schedule_table.setItem(row, 2, QTableWidgetItem(schedule.get('product_name', '') or '-'))

                # 실험방법
                test_method = schedule.get('test_method', '') or ''
                test_method_text = {
                    'real': '실측',
                    'acceleration': '가속',
                    'custom_real': '의뢰자(실측)',
                    'custom_acceleration': '의뢰자(가속)'
                }.get(test_method, test_method or '-')
                self.schedule_table.setItem(row, 3, QTableWidgetItem(test_method_text))

                # 시작일
                self.schedule_table.setItem(row, 4, QTableWidgetItem(schedule.get('start_date', '') or '-'))

                # 상태
                status = schedule.get('status', 'pending') or 'pending'
                status_text = {
                    'pending': '대기중',
                    'in_progress': '진행중',
                    'completed': '완료',
                    'cancelled': '취소'
                }.get(status, status)

                status_item = QTableWidgetItem(status_text)
                if status == 'in_progress':
                    status_item.setBackground(QColor('#FFF3E0'))
                elif status == 'completed':
                    status_item.setBackground(QColor('#E8F5E9'))
                elif status == 'cancelled':
                    status_item.setBackground(QColor('#FFEBEE'))

                self.schedule_table.setItem(row, 5, status_item)

            print(f"스케줄 {len(schedules)}개 로드 완료")

        except Exception as e:
            import traceback
            print(f"스케줄 로드 중 오류: {str(e)}")
            traceback.print_exc()

    def search_schedules(self):
        """스케줄 검색"""
        keyword = self.search_input.text().strip()
        if keyword:
            schedules = Schedule.search(keyword)
        else:
            schedules = Schedule.get_all()

        self.schedule_table.setRowCount(0)
        for row, schedule in enumerate(schedules):
            self.schedule_table.insertRow(row)
            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(schedule.get('id', ''))))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(schedule.get('client_name', '') or '-'))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(schedule.get('product_name', '') or '-'))

            test_method = schedule.get('test_method', '') or ''
            test_method_text = {
                'real': '실측',
                'acceleration': '가속',
                'custom_real': '의뢰자(실측)',
                'custom_acceleration': '의뢰자(가속)'
            }.get(test_method, test_method or '-')
            self.schedule_table.setItem(row, 3, QTableWidgetItem(test_method_text))

            self.schedule_table.setItem(row, 4, QTableWidgetItem(schedule.get('start_date', '') or '-'))

            status = schedule.get('status', 'pending') or 'pending'
            status_text = {'pending': '대기중', 'in_progress': '진행중', 'completed': '완료', 'cancelled': '취소'}.get(status, status)
            self.schedule_table.setItem(row, 5, QTableWidgetItem(status_text))

    def on_schedule_selected(self):
        """스케줄 선택 시 상단 패널 업데이트"""
        selected_rows = self.schedule_table.selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        schedule_id = self.schedule_table.item(row, 0).text()

        # 스케줄 상세 정보 가져오기
        schedule = Schedule.get_by_id(int(schedule_id))
        if schedule:
            self.current_schedule = schedule
            self.update_info_panel(schedule)

    def update_info_panel(self, schedule):
        """상단 정보 패널 업데이트"""
        # 1. 기본 정보
        self.company_value.setText(schedule.get('client_name', '-') or '-')
        self.product_value.setText(schedule.get('product_name', '-') or '-')

        # 실험방법
        test_method = schedule.get('test_method', '') or ''
        test_method_text = {
            'real': '실측실험',
            'acceleration': '가속실험',
            'custom_real': '의뢰자요청(실측)',
            'custom_acceleration': '의뢰자요청(가속)'
        }.get(test_method, '-')
        self.test_method_value.setText(test_method_text)

        # 소비기한 계산
        days = schedule.get('test_period_days', 0) or 0
        months = schedule.get('test_period_months', 0) or 0
        years = schedule.get('test_period_years', 0) or 0
        total_days = days + (months * 30) + (years * 365)

        expiry_parts = []
        if years > 0:
            expiry_parts.append(f"{years}년")
        if months > 0:
            expiry_parts.append(f"{months}개월")
        if days > 0:
            expiry_parts.append(f"{days}일")
        self.expiry_value.setText(' '.join(expiry_parts) if expiry_parts else '-')

        # 보관조건
        storage = schedule.get('storage_condition', '') or ''
        storage_text = {
            'room_temp': '상온',
            'warm': '실온',
            'cool': '냉장',
            'freeze': '냉동'
        }.get(storage, '-')
        self.storage_value.setText(storage_text)

        # 식품유형 (food_type_id로 조회 필요 - 일단 ID만 표시)
        food_type_id = schedule.get('food_type_id', '')
        self.food_type_value.setText(str(food_type_id) if food_type_id else '-')

        # 실험기간 계산 (실측: 소비기한 x 2, 가속: 소비기한 / 2)
        if test_method in ['real', 'custom_real']:
            experiment_days = total_days * 2
        else:
            experiment_days = total_days // 2 if total_days > 0 else 0

        exp_years = experiment_days // 365
        exp_months = (experiment_days % 365) // 30
        exp_days = experiment_days % 30
        period_parts = []
        if exp_years > 0:
            period_parts.append(f"{exp_years}년")
        if exp_months > 0:
            period_parts.append(f"{exp_months}개월")
        if exp_days > 0:
            period_parts.append(f"{exp_days}일")
        self.period_value.setText(' '.join(period_parts) if period_parts else '-')

        # 중간보고서
        interim = "요청" if schedule.get('report_interim') else "미요청"
        self.interim_report_value.setText(interim)

        # 연장실험
        extension = "진행" if schedule.get('extension_test') else "미진행"
        self.extension_value.setText(extension)

        # 샘플링 횟수
        sampling_count = schedule.get('sampling_count', 6) or 6
        self.sampling_count_value.setText(f"{sampling_count}회")

        # 샘플링 간격 계산
        if experiment_days > 0 and sampling_count > 0:
            interval = experiment_days // sampling_count
            self.sampling_interval_value.setText(f"{interval}일")
        else:
            self.sampling_interval_value.setText('-')

        # 시작일
        start_date = schedule.get('start_date', '-') or '-'
        self.start_date_value.setText(start_date)

        # 중간보고일 (6회차 시점)
        if start_date != '-' and experiment_days > 0 and sampling_count >= 6:
            try:
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                interval = experiment_days // sampling_count
                interim_date = start + timedelta(days=interval * 6)
                self.interim_date_value.setText(interim_date.strftime('%Y-%m-%d'))
            except:
                self.interim_date_value.setText('-')
        else:
            self.interim_date_value.setText('-')

        # 마지막 실험일
        if start_date != '-' and experiment_days > 0:
            try:
                from datetime import datetime, timedelta
                start = datetime.strptime(start_date, '%Y-%m-%d')
                last_date = start + timedelta(days=experiment_days)
                self.last_test_date_value.setText(last_date.strftime('%Y-%m-%d'))
            except:
                self.last_test_date_value.setText('-')
        else:
            self.last_test_date_value.setText('-')

        # 상태
        status = schedule.get('status', 'pending') or 'pending'
        status_text = {
            'pending': '대기중',
            'in_progress': '진행중',
            'completed': '완료',
            'cancelled': '취소'
        }.get(status, status)
        self.status_value.setText(status_text)

        # 2. 온도 구간 업데이트
        self.update_temperature_panel(schedule)

        # 3. 메모 로드
        memo = schedule.get('memo', '') or ''
        self.memo_edit.setText(memo)

    def update_temperature_panel(self, schedule):
        """온도 구간 패널 업데이트"""
        test_method = schedule.get('test_method', '') or ''
        storage = schedule.get('storage_condition', '') or ''
        custom_temps = schedule.get('custom_temperatures', '') or ''

        # 온도 정보
        # 실측실험 온도
        real_temps = {
            'room_temp': '15℃',
            'warm': '25℃',
            'cool': '10℃',
            'freeze': '-18℃'
        }

        # 가속실험 온도 (3구간)
        accel_temps = {
            'room_temp': ['15℃', '25℃', '35℃'],
            'warm': ['25℃', '35℃', '45℃'],
            'cool': ['5℃', '10℃', '15℃'],
            'freeze': ['-6℃', '-12℃', '-18℃']
        }

        # 초기화
        self.temp_zone1_value.setText('-')
        self.temp_zone2_value.setText('-')
        self.temp_zone3_value.setText('-')

        if test_method in ['real', 'custom_real']:
            # 실측: 1구간만
            if custom_temps:
                temps = custom_temps.split(',')
                self.temp_zone1_value.setText(temps[0] + '℃' if temps else '-')
                if len(temps) > 1:
                    self.temp_zone2_value.setText(temps[1] + '℃')
                if len(temps) > 2:
                    self.temp_zone3_value.setText(temps[2] + '℃')
            else:
                self.temp_zone1_value.setText(real_temps.get(storage, '-'))

        elif test_method in ['acceleration', 'custom_acceleration']:
            # 가속: 3구간
            if custom_temps:
                temps = custom_temps.split(',')
                self.temp_zone1_value.setText(temps[0] + '℃' if len(temps) > 0 else '-')
                self.temp_zone2_value.setText(temps[1] + '℃' if len(temps) > 1 else '-')
                self.temp_zone3_value.setText(temps[2] + '℃' if len(temps) > 2 else '-')
            else:
                temps = accel_temps.get(storage, ['-', '-', '-'])
                self.temp_zone1_value.setText(temps[0])
                self.temp_zone2_value.setText(temps[1])
                self.temp_zone3_value.setText(temps[2])

    def save_memo(self):
        """메모 저장"""
        if not self.current_schedule:
            QMessageBox.warning(self, "저장 실패", "먼저 스케줄을 선택하세요.")
            return

        memo = self.memo_edit.toPlainText()
        schedule_id = self.current_schedule.get('id')

        try:
            # 메모 저장 (Schedule 모델에 메서드 추가 필요)
            success = Schedule.update_memo(schedule_id, memo)
            if success:
                QMessageBox.information(self, "저장 완료", "메모가 저장되었습니다.")
            else:
                QMessageBox.warning(self, "저장 실패", "메모 저장에 실패했습니다.")
        except AttributeError:
            # update_memo 메서드가 없는 경우
            QMessageBox.warning(self, "저장 실패", "메모 저장 기능이 아직 구현되지 않았습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"메모 저장 중 오류가 발생했습니다:\n{str(e)}")
