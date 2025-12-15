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
import time

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

    def _request(self, method, endpoint, data=None, params=None, retry_count=3):
        """
        API 요청 실행 (재시도 및 타임아웃 개선)

        Args:
            method: HTTP 메서드 (GET, POST, PUT, PATCH, DELETE)
            endpoint: API 엔드포인트
            data: 요청 바디 데이터
            params: 쿼리 파라미터
            retry_count: 재시도 횟수 (기본 3회)
        """
        url = f"{self._base_url}{endpoint}"
        # 타임아웃 설정: (연결 타임아웃, 읽기 타임아웃)
        # 외부망에서 큰 데이터(수수료 목록 등) 로드 시 충분한 시간 확보
        timeout = (5, 30)  # 연결 5초, 읽기 30초

        last_exception = None

        for attempt in range(retry_count):
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
                    return self._request(method, endpoint, data, params, retry_count)
                last_exception = e
                # 재시도 전 대기 (지수 백오프: 1초, 2초, 4초)
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    print(f"[API] 연결 실패, {wait_time}초 후 재시도... ({attempt + 1}/{retry_count})")
                    time.sleep(wait_time)
                    continue

            except requests.exceptions.Timeout as e:
                last_exception = e
                # 타임아웃 시 재시도
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    print(f"[API] 타임아웃, {wait_time}초 후 재시도... ({attempt + 1}/{retry_count})")
                    time.sleep(wait_time)
                    continue

            except requests.exceptions.RequestException as e:
                last_exception = e
                # 기타 요청 오류는 재시도 안함
                break

        # 모든 재시도 실패
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise Exception(f"서버 응답 시간이 초과되었습니다. (재시도 {retry_count}회 실패)")
        elif isinstance(last_exception, requests.exceptions.ConnectionError):
            raise Exception(f"서버에 연결할 수 없습니다: {str(last_exception)}")
        else:
            raise Exception(f"API 요청 오류: {str(last_exception)}")

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

    def change_user_password(self, user_id, new_password):
        """비밀번호 변경"""
        result = self._request("POST", f"/api/users/{user_id}/change-password",
                              params={"new_password": new_password})
        return result.get("success", False)

    def verify_user_password(self, user_id, password):
        """비밀번호 확인"""
        result = self._request("POST", f"/api/users/{user_id}/verify-password",
                              params={"password": password})
        return result.get("success", False)

    def toggle_user_view_all(self, user_id, can_view=True):
        """사용자 열람권한 토글"""
        result = self._request("POST", f"/api/users/{user_id}/toggle-view-all",
                              params={"can_view": can_view})
        return result.get("success", False)

    def get_user_active_status(self, user_id):
        """사용자 활성화 상태 조회"""
        result = self._request("GET", f"/api/users/{user_id}/active-status")
        return result.get("data", 0)

    def get_user_view_all_status(self, user_id):
        """사용자 열람권한 상태 조회"""
        result = self._request("GET", f"/api/users/{user_id}/view-all-status")
        return result.get("data", 0)

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
                    f"{self._base_url}/api/schedules/{schedule_id}/attachments",
                    headers=self._get_headers(),
                    files=files,
                    timeout=(5, 30)
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

    def get_attachment(self, attachment_id):
        """첨부파일 정보 조회"""
        result = self._request("GET", f"/api/attachments/{attachment_id}")
        if result.get("success"):
            return result.get("data")
        return None

    def download_attachment(self, attachment_id, save_path=None):
        """첨부파일 다운로드

        Args:
            attachment_id: 첨부파일 ID
            save_path: 저장할 경로 (없으면 임시 파일에 저장)

        Returns:
            (success, file_path or error_message)
        """
        import tempfile

        try:
            response = requests.get(
                f"{self._base_url}/api/attachments/{attachment_id}/download",
                headers=self._get_headers(),
                timeout=(5, 60),  # 다운로드는 더 긴 타임아웃
                stream=True
            )

            if response.status_code == 200:
                # Content-Disposition 헤더에서 파일명 추출
                content_disp = response.headers.get('content-disposition', '')
                filename = None
                if 'filename=' in content_disp:
                    import re
                    match = re.search(r'filename[*]?=(?:UTF-8\'\')?([^;\n]+)', content_disp)
                    if match:
                        filename = match.group(1).strip('"\'')

                # 저장 경로 결정
                if save_path:
                    file_path = save_path
                else:
                    suffix = os.path.splitext(filename)[1] if filename else ''
                    fd, file_path = tempfile.mkstemp(suffix=suffix)
                    os.close(fd)

                # 파일 저장
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return True, file_path
            else:
                return False, f"다운로드 실패: {response.status_code}"

        except Exception as e:
            return False, f"다운로드 오류: {str(e)}"

    # ==================== Settings ====================

    def get_settings(self):
        """모든 설정 조회"""
        result = self._request("GET", "/api/settings")
        return result.get("data", {})

    def get_setting(self, key):
        """특정 설정 조회"""
        result = self._request("GET", f"/api/settings/{key}")
        return result.get("data")

    def update_setting(self, key, value):
        """설정 업데이트"""
        result = self._request("PUT", f"/api/settings/{key}", params={"value": value})
        return result.get("success", False)

    def update_settings_batch(self, settings_dict):
        """여러 설정 일괄 업데이트"""
        result = self._request("POST", "/api/settings/batch", settings_dict)
        return result.get("success", False)

    # ==================== User Settings ====================

    def get_user_settings(self, user_id):
        """사용자별 설정 조회"""
        result = self._request("GET", f"/api/user-settings/{user_id}")
        return result.get("data", {})

    def get_user_setting(self, user_id, key):
        """사용자별 특정 설정 조회"""
        result = self._request("GET", f"/api/user-settings/{user_id}/{key}")
        return result.get("data")

    def update_user_setting(self, user_id, key, value):
        """사용자별 설정 업데이트"""
        result = self._request("PUT", f"/api/user-settings/{user_id}/{key}", params={"value": value})
        return result.get("success", False)

    def update_user_settings_batch(self, user_id, settings_dict):
        """사용자별 여러 설정 일괄 업데이트"""
        result = self._request("POST", f"/api/user-settings/{user_id}/batch", settings_dict)
        return result.get("success", False)

    # ==================== Activity Logs ====================

    def create_activity_log(self, user_id, username, user_name, action_type,
                           department=None, target_type=None, target_id=None,
                           target_name=None, details=None):
        """활동 로그 생성"""
        try:
            result = self._request("POST", "/api/activity-logs", {
                "user_id": user_id,
                "username": username,
                "user_name": user_name,
                "department": department or "",
                "action_type": action_type,
                "target_type": target_type,
                "target_id": target_id,
                "target_name": target_name,
                "details": details
            })
            if result.get("success"):
                return result.get("data", {}).get("id")
            return None
        except Exception as e:
            print(f"활동 로그 API 기록 실패: {str(e)}")
            return None

    def get_activity_logs(self, user_id=None, username=None, action_type=None,
                         date_from=None, date_to=None, target_type=None,
                         limit=500, offset=0):
        """활동 로그 목록 조회"""
        params = {"limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id
        if username:
            params["username"] = username
        if action_type:
            params["action_type"] = action_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if target_type:
            params["target_type"] = target_type

        result = self._request("GET", "/api/activity-logs", params=params)
        return result.get("data", [])

    def get_user_activity_logs(self, user_id, limit=100, offset=0):
        """특정 사용자의 활동 로그 조회"""
        result = self._request("GET", f"/api/activity-logs/user/{user_id}",
                              params={"limit": limit, "offset": offset})
        return result.get("data", [])

    def get_activity_logs_summary(self):
        """사용자별 활동 요약"""
        result = self._request("GET", "/api/activity-logs/summary")
        return result.get("data", [])

    def get_activity_logs_count(self, user_id=None, username=None, action_type=None,
                                date_from=None, date_to=None):
        """활동 로그 개수 조회"""
        params = {}
        if user_id:
            params["user_id"] = user_id
        if username:
            params["username"] = username
        if action_type:
            params["action_type"] = action_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        result = self._request("GET", "/api/activity-logs/count", params=params)
        return result.get("data", 0)

    def get_action_types(self):
        """활동 유형 목록"""
        result = self._request("GET", "/api/activity-logs/action-types")
        return result.get("data", {})

    # ==================== Messages ====================

    def send_message(self, sender_id, receiver_id, content, message_type='chat', subject=None):
        """메시지 전송"""
        result = self._request("POST", "/api/messages", {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "message_type": message_type,
            "subject": subject
        })
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def get_conversation(self, user1_id, user2_id, limit=100):
        """두 사용자 간 대화 내역 조회"""
        result = self._request("GET", "/api/messages/conversation",
                              params={"user1_id": user1_id, "user2_id": user2_id, "limit": limit})
        return result.get("data", [])

    def get_chat_partners(self, user_id):
        """대화 상대 목록 조회"""
        result = self._request("GET", f"/api/messages/partners/{user_id}")
        return result.get("data", [])

    def mark_message_read(self, message_id, user_id):
        """메시지 읽음 처리"""
        result = self._request("POST", f"/api/messages/{message_id}/read",
                              params={"target_user_id": user_id})
        return result.get("success", False)

    def mark_conversation_read(self, user_id, partner_id):
        """대화 전체 읽음 처리"""
        result = self._request("POST", "/api/messages/conversation/read",
                              params={"target_user_id": user_id, "partner_id": partner_id})
        return result.get("data", 0)

    def get_unread_count(self, user_id):
        """읽지 않은 메시지 수"""
        result = self._request("GET", f"/api/messages/unread-count/{user_id}")
        return result.get("data", 0)

    def get_unread_by_partner(self, user_id):
        """상대별 읽지 않은 메시지 수"""
        result = self._request("GET", f"/api/messages/unread-by-partner/{user_id}")
        return result.get("data", {})

    def delete_message(self, message_id, user_id):
        """메시지 삭제"""
        result = self._request("DELETE", f"/api/messages/{message_id}",
                              params={"target_user_id": user_id})
        return result.get("success", False)

    def delete_conversation(self, user_id, partner_id):
        """대화 전체 삭제"""
        result = self._request("DELETE", f"/api/messages/conversation/{partner_id}",
                              params={"target_user_id": user_id})
        return result.get("data", 0)

    # ==================== Email Logs ====================

    def save_email_log(self, schedule_id, estimate_type, sender_email, to_emails, cc_emails,
                      subject, body, attachment_name, sent_by=None, client_name=None):
        """이메일 로그 저장"""
        result = self._request("POST", "/api/email-logs", {
            "schedule_id": schedule_id,
            "estimate_type": estimate_type,
            "sender_email": sender_email,
            "to_emails": to_emails,
            "cc_emails": cc_emails,
            "subject": subject,
            "body": body,
            "attachment_name": attachment_name,
            "sent_by": sent_by,
            "client_name": client_name
        })
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None

    def get_email_logs(self, limit=100, sent_by=None):
        """이메일 로그 목록 조회"""
        params = {"limit": limit}
        if sent_by:
            params["sent_by"] = sent_by
        result = self._request("GET", "/api/email-logs", params=params)
        return result.get("data", [])

    def get_email_log(self, log_id):
        """이메일 로그 상세 조회"""
        result = self._request("GET", f"/api/email-logs/{log_id}")
        return result.get("data")

    def get_email_logs_by_schedule(self, schedule_id):
        """스케줄별 이메일 로그 조회"""
        result = self._request("GET", f"/api/email-logs/schedule/{schedule_id}")
        return result.get("data", [])

    def search_email_logs(self, keyword=None, start_date=None, end_date=None, limit=100, sent_by=None):
        """이메일 로그 검색"""
        params = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if sent_by:
            params["sent_by"] = sent_by
        result = self._request("GET", "/api/email-logs/search", params=params)
        return result.get("data", [])

    def delete_email_log(self, log_id, user_id=None):
        """이메일 로그 삭제"""
        params = {}
        if user_id:
            params["target_user_id"] = user_id
        result = self._request("DELETE", f"/api/email-logs/{log_id}", params=params)
        return result.get("success", False)

    def update_email_log_status(self, log_id, status=None, received=None, received_at=None):
        """이메일 로그 상태 업데이트"""
        result = self._request("PUT", f"/api/email-logs/{log_id}/status", {
            "status": status,
            "received": received,
            "received_at": received_at
        })
        return result.get("success", False)

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
