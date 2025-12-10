#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
자동 업데이트 모듈
GitHub Releases에서 최신 버전을 확인하고 업데이트를 수행합니다.
'''

import os
import sys
import subprocess
import tempfile
import threading
from packaging import version as pkg_version

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from version import VERSION, GITHUB_OWNER, GITHUB_REPO, APP_DISPLAY_NAME


class VersionChecker(QThread):
    """GitHub에서 최신 버전을 확인하는 스레드"""
    finished = pyqtSignal(dict)  # 결과 반환
    error = pyqtSignal(str)  # 에러 메시지

    def run(self):
        try:
            import requests

            # GitHub Releases API 호출
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # 릴리스 정보 추출
                latest_version = data.get('tag_name', '').lstrip('v')
                release_notes = data.get('body', '')

                # 다운로드 URL 찾기 (EXE 파일)
                download_url = None
                file_name = None
                file_size = 0

                for asset in data.get('assets', []):
                    # ZIP 파일 우선 (GitHub Actions에서 생성하는 형식)
                    if asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        file_name = asset['name']
                        file_size = asset['size']
                        break
                    # EXE 파일도 지원 (단일 파일 릴리스)
                    elif asset['name'].endswith('.exe') and not download_url:
                        download_url = asset['browser_download_url']
                        file_name = asset['name']
                        file_size = asset['size']

                self.finished.emit({
                    'success': True,
                    'latest_version': latest_version,
                    'current_version': VERSION,
                    'download_url': download_url,
                    'file_name': file_name,
                    'file_size': file_size,
                    'release_notes': release_notes,
                    'has_update': self._compare_versions(latest_version, VERSION)
                })
            elif response.status_code == 404:
                self.finished.emit({
                    'success': True,
                    'has_update': False,
                    'message': '릴리스가 없습니다.'
                })
            else:
                self.error.emit(f"GitHub API 오류: {response.status_code}")

        except ImportError:
            self.error.emit("requests 라이브러리가 설치되지 않았습니다.")
        except Exception as e:
            self.error.emit(f"버전 확인 중 오류: {str(e)}")

    def _compare_versions(self, latest, current):
        """버전 비교 (latest > current 이면 True)"""
        try:
            return pkg_version.parse(latest) > pkg_version.parse(current)
        except:
            # packaging 라이브러리가 없으면 단순 비교
            try:
                latest_parts = [int(x) for x in latest.split('.')]
                current_parts = [int(x) for x in current.split('.')]
                return latest_parts > current_parts
            except:
                return False


class DownloadThread(QThread):
    """파일 다운로드 스레드"""
    progress = pyqtSignal(int)  # 진행률 (0-100)
    finished = pyqtSignal(str)  # 다운로드된 파일 경로
    error = pyqtSignal(str)  # 에러 메시지

    def __init__(self, url, file_name):
        super().__init__()
        self.url = url
        self.file_name = file_name
        self.cancelled = False

    def run(self):
        try:
            import requests

            # 임시 폴더에 다운로드
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, self.file_name)

            response = requests.get(self.url, stream=True, timeout=60)
            total_size = int(response.headers.get('content-length', 0))

            downloaded = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        return

                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = int(downloaded / total_size * 100)
                        self.progress.emit(progress)

            self.finished.emit(file_path)

        except Exception as e:
            self.error.emit(f"다운로드 중 오류: {str(e)}")

    def cancel(self):
        self.cancelled = True


class UpdateDialog(QDialog):
    """업데이트 다이얼로그"""

    def __init__(self, parent=None, update_info=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_thread = None
        self.downloaded_file = None

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("업데이트 가능")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 제목
        title = QLabel(f"🎉 새 버전이 있습니다!")
        title.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title)

        # 버전 정보
        version_info = QLabel(
            f"현재 버전: {self.update_info['current_version']}\n"
            f"최신 버전: {self.update_info['latest_version']}"
        )
        version_info.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(version_info)

        # 릴리스 노트
        if self.update_info.get('release_notes'):
            notes_label = QLabel("변경 사항:")
            notes_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(notes_label)

            notes = QTextEdit()
            notes.setPlainText(self.update_info['release_notes'])
            notes.setReadOnly(True)
            notes.setMaximumHeight(150)
            layout.addWidget(notes)

        # 파일 크기
        if self.update_info.get('file_size'):
            size_mb = self.update_info['file_size'] / (1024 * 1024)
            size_label = QLabel(f"다운로드 크기: {size_mb:.1f} MB")
            size_label.setStyleSheet("color: #777;")
            layout.addWidget(size_label)

        # 진행 바 (처음엔 숨김)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555;")
        layout.addWidget(self.status_label)

        # 버튼
        btn_layout = QHBoxLayout()

        self.later_btn = QPushButton("나중에")
        self.later_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.later_btn)

        btn_layout.addStretch()

        self.update_btn = QPushButton("지금 업데이트")
        self.update_btn.setStyleSheet(
            "background-color: #3498db; color: white; "
            "padding: 8px 20px; font-weight: bold;"
        )
        self.update_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.update_btn)

        layout.addLayout(btn_layout)

    def start_download(self):
        """다운로드 시작"""
        if not self.update_info.get('download_url'):
            QMessageBox.warning(self, "오류", "다운로드 URL을 찾을 수 없습니다.")
            return

        self.update_btn.setEnabled(False)
        self.later_btn.setText("취소")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("다운로드 중...")

        self.download_thread = DownloadThread(
            self.update_info['download_url'],
            self.update_info['file_name']
        )
        self.download_thread.progress.connect(self.on_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_progress(self, value):
        """다운로드 진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"다운로드 중... {value}%")

    def on_download_finished(self, file_path):
        """다운로드 완료"""
        self.downloaded_file = file_path
        self.status_label.setText("다운로드 완료! 프로그램을 재시작합니다...")
        self.progress_bar.setValue(100)

        # 업데이트 실행
        self.apply_update()

    def on_download_error(self, error_msg):
        """다운로드 오류"""
        self.status_label.setText(f"오류: {error_msg}")
        self.update_btn.setEnabled(True)
        self.later_btn.setText("나중에")
        QMessageBox.critical(self, "다운로드 오류", error_msg)

    def apply_update(self):
        """업데이트 적용 (프로그램 교체 및 재시작)"""
        if not self.downloaded_file:
            return

        try:
            if getattr(sys, 'frozen', False):
                # EXE로 실행 중인 경우
                current_exe = sys.executable
                app_dir = os.path.dirname(current_exe)

                # ZIP 파일인 경우 압축 해제 후 복사
                if self.downloaded_file.endswith('.zip'):
                    import zipfile

                    # 임시 폴더에 압축 해제
                    extract_dir = os.path.join(tempfile.gettempdir(), "foodlab_update")
                    if os.path.exists(extract_dir):
                        import shutil
                        shutil.rmtree(extract_dir)

                    with zipfile.ZipFile(self.downloaded_file, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)

                    # PowerShell 스크립트로 폴더 전체 복사 (한글 경로 지원)
                    ps_script = os.path.join(tempfile.gettempdir(), "update.ps1")
                    with open(ps_script, 'w', encoding='utf-8-sig') as f:
                        f.write('Start-Sleep -Seconds 2\n')
                        f.write(f'Copy-Item -Path "{extract_dir}\\*" -Destination "{app_dir}" -Recurse -Force\n')
                        f.write(f'Start-Process -FilePath "{current_exe}"\n')
                        f.write(f'Remove-Item -Path "{extract_dir}" -Recurse -Force\n')
                        f.write(f'Remove-Item -Path "{ps_script}" -Force\n')
                else:
                    # 단일 EXE 파일인 경우
                    ps_script = os.path.join(tempfile.gettempdir(), "update.ps1")
                    with open(ps_script, 'w', encoding='utf-8-sig') as f:
                        f.write('Start-Sleep -Seconds 2\n')
                        f.write(f'Copy-Item -Path "{self.downloaded_file}" -Destination "{current_exe}" -Force\n')
                        f.write(f'Start-Process -FilePath "{current_exe}"\n')
                        f.write(f'Remove-Item -Path "{ps_script}" -Force\n')

                # PowerShell 스크립트 실행 후 종료
                subprocess.Popen(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                QMessageBox.information(
                    self, "업데이트",
                    "업데이트가 적용됩니다.\n프로그램이 자동으로 재시작됩니다."
                )

                # 앱 종료
                from PyQt5.QtWidgets import QApplication
                QApplication.quit()
            else:
                # 개발 모드 (스크립트로 실행 중)
                QMessageBox.information(
                    self, "업데이트 완료",
                    f"새 버전이 다운로드되었습니다:\n{self.downloaded_file}\n\n"
                    "개발 모드에서는 수동으로 교체해주세요."
                )
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"업데이트 적용 중 오류: {str(e)}")

    def reject(self):
        """다이얼로그 닫기"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait()
        super().reject()


class AutoUpdater:
    """자동 업데이트 관리자"""

    def __init__(self, parent=None):
        self.parent = parent
        self.checker = None

    def check_for_updates(self, silent=False):
        """업데이트 확인

        Args:
            silent: True면 업데이트가 없을 때 알림 없음
        """
        self.silent = silent
        self.checker = VersionChecker()
        self.checker.finished.connect(self._on_check_finished)
        self.checker.error.connect(self._on_check_error)
        self.checker.start()

    def _on_check_finished(self, result):
        """버전 확인 완료"""
        if result.get('success') and result.get('has_update'):
            # 새 버전이 있으면 업데이트 다이얼로그 표시
            dialog = UpdateDialog(self.parent, result)
            dialog.exec_()
        elif not self.silent:
            # 조용한 모드가 아니면 최신 버전임을 알림
            QMessageBox.information(
                self.parent, "업데이트 확인",
                f"현재 최신 버전({VERSION})을 사용 중입니다."
            )

    def _on_check_error(self, error_msg):
        """버전 확인 오류"""
        if not self.silent:
            QMessageBox.warning(
                self.parent, "업데이트 확인 실패",
                f"업데이트를 확인할 수 없습니다.\n{error_msg}"
            )


def check_for_updates_on_startup(parent=None):
    """프로그램 시작 시 업데이트 확인 (조용한 모드)"""
    updater = AutoUpdater(parent)
    updater.check_for_updates(silent=True)
    return updater  # 참조 유지를 위해 반환
