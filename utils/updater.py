#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
자동 업데이트 모듈
GitHub Releases를 통한 업데이트 확인 및 다운로드
'''

import os
import sys
import json
import tempfile
import subprocess
import threading

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from version import VERSION, GITHUB_OWNER, GITHUB_REPO, APP_NAME


class Updater:
    """자동 업데이트 관리 클래스"""

    def __init__(self):
        self.current_version = VERSION
        self.github_api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
        self.latest_version = None
        self.download_url = None
        self.release_notes = None

    def check_for_updates(self):
        """
        새 버전 확인
        Returns: (bool, str) - (업데이트 가능 여부, 최신 버전 또는 오류 메시지)
        """
        if not REQUESTS_AVAILABLE:
            return False, "requests 모듈이 설치되지 않았습니다."

        try:
            response = requests.get(
                self.github_api_url,
                headers={'Accept': 'application/vnd.github.v3+json'},
                timeout=10
            )

            if response.status_code == 404:
                return False, "릴리스가 없습니다."

            if response.status_code != 200:
                return False, f"GitHub API 오류: {response.status_code}"

            release_data = response.json()
            self.latest_version = release_data.get('tag_name', '').lstrip('v')
            self.release_notes = release_data.get('body', '')

            # 다운로드 URL 찾기 (Windows EXE 또는 ZIP)
            assets = release_data.get('assets', [])
            for asset in assets:
                name = asset.get('name', '').lower()
                if name.endswith('.zip') or name.endswith('.exe'):
                    self.download_url = asset.get('browser_download_url')
                    break

            # 버전 비교
            if self._compare_versions(self.latest_version, self.current_version) > 0:
                return True, self.latest_version
            else:
                return False, "최신 버전입니다."

        except requests.exceptions.Timeout:
            return False, "서버 연결 시간 초과"
        except requests.exceptions.ConnectionError:
            return False, "네트워크 연결 오류"
        except Exception as e:
            return False, f"업데이트 확인 오류: {str(e)}"

    def _compare_versions(self, version1, version2):
        """
        버전 비교
        Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
        """
        try:
            v1_parts = list(map(int, version1.split('.')))
            v2_parts = list(map(int, version2.split('.')))

            # 길이 맞추기
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)

            for i in range(3):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            return 0
        except:
            return 0

    def download_update(self, progress_callback=None):
        """
        업데이트 다운로드
        Args:
            progress_callback: 진행률 콜백 함수 (percent, downloaded, total)
        Returns: (bool, str) - (성공 여부, 파일 경로 또는 오류 메시지)
        """
        if not self.download_url:
            return False, "다운로드 URL이 없습니다."

        try:
            response = requests.get(self.download_url, stream=True, timeout=60)

            if response.status_code != 200:
                return False, f"다운로드 오류: {response.status_code}"

            # 임시 파일에 저장
            total_size = int(response.headers.get('content-length', 0))
            filename = self.download_url.split('/')[-1]
            temp_path = os.path.join(tempfile.gettempdir(), filename)

            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent, downloaded, total_size)

            return True, temp_path

        except Exception as e:
            return False, f"다운로드 오류: {str(e)}"

    def install_update(self, file_path):
        """
        업데이트 설치 (Windows용)
        """
        if not os.path.exists(file_path):
            return False, "파일을 찾을 수 없습니다."

        try:
            if file_path.endswith('.exe'):
                # 설치 프로그램 실행
                subprocess.Popen([file_path], shell=True)
            elif file_path.endswith('.zip'):
                # ZIP 파일 압축 해제 안내
                return True, f"다운로드 완료: {file_path}\n압축을 해제하고 기존 파일을 교체하세요."

            return True, "업데이트 설치를 시작합니다. 프로그램을 종료합니다."
        except Exception as e:
            return False, f"설치 오류: {str(e)}"

    def get_release_notes(self):
        """릴리스 노트 반환"""
        return self.release_notes or "릴리스 노트가 없습니다."


def check_update_async(callback):
    """
    비동기로 업데이트 확인
    Args:
        callback: 결과 콜백 함수 (has_update, version_or_message)
    """
    def _check():
        updater = Updater()
        result = updater.check_for_updates()
        callback(result[0], result[1], updater)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


if __name__ == "__main__":
    # 테스트
    updater = Updater()
    has_update, message = updater.check_for_updates()
    print(f"업데이트 확인: {has_update}, {message}")
    if has_update:
        print(f"릴리스 노트: {updater.get_release_notes()}")
