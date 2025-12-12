#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
API 클라이언트
서버 API와 통신하는 모듈
기존 database.py의 get_connection() 대신 사용
'''

import requests
import json
import os

# API 서버 설정
API_BASE_URL = "http://192.168.0.96:8000"  # 내부망
API_EXTERNAL_URL = "http://14.7.14.31:8000"  # 외부망 (포트포워딩 필요)

# 설정 파일 경로
CONFIG_PATH = 'config/api_config.json'


class ApiClient:
    """API 클라이언트 클래스"""

    _instance = None
    _token = None
    _user = None
    _base_url = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """설정 파일 로드"""
        import sys
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        config_file = os.path.join(base_path, CONFIG_PATH)

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self._base_url = config.get('api_url', API_BASE_URL)
        else:
            # 기본값: 내부망 시도, 실패시 외부망
            self._base_url = API_BASE_URL

    def _get_headers(self):
        """요청 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(self, method, endpoint, data=None, params=None):
        """API 요청 실행"""
        url = f"{self._base_url}{endpoint}"
        # 타임아웃 설정: (연결 타임아웃, 읽기 타임아웃)
        timeout = (2, 5)  # 연결 2초, 읽기 5초

        try:
            if method == "GET":
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=self._get_headers(), json=data, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, headers=self._get_headers(), json=data, timeout=timeout)
            elif method == "PATCH":
                response = requests.patch(url, headers=self._get_headers(), json=data, params=params, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=self._get_headers(), timeout=timeout)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

            if response.status_code == 401:
                # 인증 실패
                self._token = None
                self._user = None
                raise Exception("인증이 만료되었습니다. 다시 로그인해주세요.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError as e:
            # 내부망 실패시 외부망 시도
            if self._base_url == API_BASE_URL:
                self._base_url = API_EXTERNAL_URL
                return self._request(method, endpoint, data, params)
            raise Exception(f"서버에 연결할 수 없습니다: {str(e)}")

        except requests.exceptions.Timeout:
            raise Exception("서버 응답 시간이 초과되었습니다. (60초)")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API 요청 오류: {str(e)}")

    # ==================== 인증 ====================

    def login(self, username, password):
        """로그인"""
        result = self._request("POST", "/api/auth/login", {
            "username": username,
            "password": password
        })

        if result.get("success"):
            self._token = result.get("token")
            self._user = result.get("user")
            return self._user
        return None

    def logout(self):
        """로그아웃"""
        try:
            self._request("POST", "/api/auth/logout")
        except:
            pass
        finally:
            self._token = None
            self._user = None

    def get_current_user(self):
        """현재 로그인 사용자"""
        return self._user

    def is_logged_in(self):
        """로그인 상태 확인"""
        return self._token is not None

    # ==================== Users ====================

    def get_users(self):
        """모든 사용자 조회"""
        result = self._request("GET", "/api/users")
        return result.get("data", [])

    def get_user(self, user_id):
        """ID로 사용자 조회"""
        result = self._request("GET", f"/api/users/{user_id}")
        return result.get("data")

    def create_user(self, **kwargs):
        """사용자 생성"""
        result = self._request("POST", "/api/users", kwargs)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def update_user(self, user_id, **kwargs):
        """사용자 수정"""
        result = self._request("PUT", f"/api/users/{user_id}", kwargs)
        return result.get("success", False)

    def delete_user(self, user_id):
        """사용자 삭제"""
        result = self._request("DELETE", f"/api/users/{user_id}")
        return result.get("success", False)

    def toggle_user_active(self, user_id, activate=True):
        """사용자 활성화/비활성화"""
        result = self._request("POST", f"/api/users/{user_id}/toggle-active", params={"activate": activate})
        return result.get("success", False)

    def reset_user_password(self, user_id):
        """비밀번호 초기화"""
        result = self._request("POST", f"/api/users/{user_id}/reset-password")
        return result.get("success", False)

    def get_departments(self):
        """부서 목록"""
        result = self._request("GET", "/api/users/constants/departments")
        return result.get("data", [])

    def get_permissions(self):
        """권한 목록"""
        result = self._request("GET", "/api/users/constants/permissions")
        return result.get("data", {})

    # ==================== Clients ====================

    def get_clients(self, page=1, per_page=100, search_keyword=None, search_field=None, sales_rep_filter=None):
        """업체 목록 조회 (페이지네이션)"""
        params = {"page": page, "per_page": per_page}
        if search_keyword:
            params["search_keyword"] = search_keyword
        if search_field:
            params["search_field"] = search_field
        if sales_rep_filter:
            params["sales_rep_filter"] = sales_rep_filter

        result = self._request("GET", "/api/clients", params=params)
        return result.get("data", {})

    def get_all_clients(self):
        """모든 업체 조회"""
        result = self._request("GET", "/api/clients/all")
        return result.get("data", [])

    def get_clients_count(self):
        """업체 수 조회"""
        result = self._request("GET", "/api/clients/count")
        return result.get("data", 0)

    def get_client(self, client_id):
        """ID로 업체 조회"""
        result = self._request("GET", f"/api/clients/{client_id}")
        return result.get("data")

    def create_client(self, **kwargs):
        """업체 생성"""
        result = self._request("POST", "/api/clients", kwargs)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def update_client(self, client_id, **kwargs):
        """업체 수정"""
        result = self._request("PUT", f"/api/clients/{client_id}", kwargs)
        return result.get("success", False)

    def delete_client(self, client_id):
        """업체 삭제"""
        result = self._request("DELETE", f"/api/clients/{client_id}")
        return result.get("success", False)

    def search_clients(self, keyword):
        """업체 검색"""
        result = self._request("GET", f"/api/clients/search/{keyword}")
        return result.get("data", [])

    # ==================== Schedules ====================

    def get_schedules(self, keyword=None, status=None, date_from=None, date_to=None):
        """스케줄 목록 조회"""
        params = {}
        if keyword:
            params["keyword"] = keyword
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        result = self._request("GET", "/api/schedules", params=params)
        return result.get("data", [])

    def get_schedule(self, schedule_id):
        """ID로 스케줄 조회"""
        result = self._request("GET", f"/api/schedules/{schedule_id}")
        return result.get("data")

    def create_schedule(self, **kwargs):
        """스케줄 생성"""
        result = self._request("POST", "/api/schedules", kwargs)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def update_schedule(self, schedule_id, data):
        """스케줄 수정"""
        result = self._request("PUT", f"/api/schedules/{schedule_id}", {"data": data})
        return result.get("success", False)

    def update_schedule_status(self, schedule_id, status):
        """스케줄 상태 변경"""
        result = self._request("PATCH", f"/api/schedules/{schedule_id}/status", params={"status": status})
        return result.get("success", False)

    def update_schedule_memo(self, schedule_id, memo):
        """스케줄 메모 수정"""
        result = self._request("PATCH", f"/api/schedules/{schedule_id}/memo", params={"memo": memo})
        return result.get("success", False)

    def delete_schedule(self, schedule_id):
        """스케줄 삭제"""
        result = self._request("DELETE", f"/api/schedules/{schedule_id}")
        return result.get("success", False)

    def search_schedules(self, keyword):
        """스케줄 검색"""
        result = self._request("GET", f"/api/schedules/search/{keyword}")
        return result.get("data", [])

    # ==================== Fees ====================

    def get_fees(self):
        """모든 수수료 조회"""
        result = self._request("GET", "/api/fees")
        return result.get("data", [])

    def get_fee_by_item(self, test_item):
        """검사 항목으로 수수료 조회"""
        result = self._request("GET", f"/api/fees/{test_item}")
        return result.get("data")

    def create_fee(self, **kwargs):
        """수수료 생성"""
        result = self._request("POST", "/api/fees", kwargs)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def update_fee(self, fee_id, **kwargs):
        """수수료 수정"""
        result = self._request("PUT", f"/api/fees/{fee_id}", kwargs)
        return result.get("success", False)

    def delete_fee(self, fee_id):
        """수수료 삭제"""
        result = self._request("DELETE", f"/api/fees/{fee_id}")
        return result.get("success", False)

    def calculate_fee(self, test_items):
        """수수료 계산"""
        result = self._request("POST", "/api/fees/calculate", test_items)
        return result.get("data", 0)

    # ==================== Food Types ====================

    def get_food_types(self):
        """모든 식품 유형 조회"""
        result = self._request("GET", "/api/food-types")
        return result.get("data", [])

    def get_food_type(self, type_id):
        """ID로 식품 유형 조회"""
        result = self._request("GET", f"/api/food-types/{type_id}")
        return result.get("data")

    def get_food_type_by_name(self, type_name):
        """이름으로 식품 유형 조회"""
        result = self._request("GET", f"/api/food-types/name/{type_name}")
        return result.get("data")

    def create_food_type(self, **kwargs):
        """식품 유형 생성"""
        result = self._request("POST", "/api/food-types", kwargs)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def update_food_type(self, type_id, **kwargs):
        """식품 유형 수정"""
        result = self._request("PUT", f"/api/food-types/{type_id}", kwargs)
        return result.get("success", False)

    def delete_food_type(self, type_id):
        """식품 유형 삭제"""
        result = self._request("DELETE", f"/api/food-types/{type_id}")
        return result.get("success", False)

    def search_food_types(self, keyword):
        """식품 유형 검색"""
        result = self._request("GET", f"/api/food-types/search/{keyword}")
        return result.get("data", [])

    # ==================== Schedule Attachments ====================

    def get_schedule_attachments(self, schedule_id):
        """스케줄 첨부파일 목록"""
        result = self._request("GET", f"/api/schedules/{schedule_id}/attachments")
        return result.get("data", [])

    def upload_attachment(self, schedule_id, file_path):
        """첨부파일 업로드"""
        import os
        if not os.path.exists(file_path):
            return False, "파일을 찾을 수 없습니다.", None
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f)}
                response = requests.post(
                    f"{self.base_url}/api/schedules/{schedule_id}/attachments",
                    files=files,
                    timeout=self.timeout
                )
            if response.status_code == 200:
                data = response.json()
                return True, "파일이 업로드되었습니다.", data.get("attachment_id")
            else:
                return False, f"업로드 실패: {response.status_code}", None
        except Exception as e:
            return False, f"업로드 오류: {str(e)}", None

    def delete_attachment(self, attachment_id):
        """첨부파일 삭제"""
        result = self._request("DELETE", f"/api/attachments/{attachment_id}")
        if result.get("success"):
            return True, "첨부파일이 삭제되었습니다."
        return False, result.get("message", "삭제 실패")

    # ==================== Settings ====================

    def get_settings(self):
        """모든 설정 조회"""
        result = self._request("GET", "/api/settings")
        return result.get("data", {})

    def get_setting(self, key):
        """특정 설정 조회"""
        result = self._request("GET", f"/api/settings/{key}")
        return result.get("data")

    # ==================== Health Check ====================

    def health_check(self):
        """서버 상태 확인"""
        try:
            result = self._request("GET", "/api/health")
            return result.get("status") == "ok"
        except:
            return False


# 싱글톤 인스턴스
api = ApiClient()


# ==================== 기존 코드 호환용 래퍼 ====================

def get_api_client():
    """API 클라이언트 인스턴스 반환"""
    return api
