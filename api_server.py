#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
FastAPI 서버
외부 클라이언트용 REST API 제공
'''

from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import secrets

# 기존 모델 import
from models.users import User, DEPARTMENTS, PERMISSION_LABELS, PERMISSION_BY_CATEGORY
from models.clients import Client
from models.schedules import Schedule
from models.fees import Fee
from models.product_types import ProductType
from models.schedule_attachments import ScheduleAttachment
from models.activity_log import ActivityLog, ACTION_TYPES
from models.communications import Message, EmailLog

# FastAPI 앱 생성
app = FastAPI(
    title="FoodLab API",
    description="식품 실험/분석 관련 견적 및 스케줄 관리 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 저장소 (간단한 토큰 기반 인증)
sessions = {}

# API 키 (환경변수로 관리 권장)
API_SECRET_KEY = "foodlab-api-secret-key-2024"


# ==================== Pydantic 모델 ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[Dict] = None
    message: Optional[str] = None

class ClientCreate(BaseModel):
    name: str
    ceo: Optional[str] = None
    business_no: Optional[str] = None
    category: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    sales_rep: Optional[str] = None
    toll_free: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    detail_address: Optional[str] = None
    notes: Optional[str] = None
    sales_business: Optional[str] = None
    sales_phone: Optional[str] = None
    sales_mobile: Optional[str] = None
    sales_address: Optional[str] = None
    mobile: Optional[str] = None

class ClientUpdate(ClientCreate):
    pass

class ScheduleCreate(BaseModel):
    client_id: int
    product_name: str
    food_type_id: Optional[int] = None
    test_method: Optional[str] = None
    storage_condition: Optional[str] = None
    start_date: Optional[str] = None
    expected_date: Optional[str] = None
    interim_report_date: Optional[str] = None
    test_period_days: int = 0
    test_period_months: int = 0
    test_period_years: int = 0
    sampling_count: int = 6
    report_interim: bool = False
    report_korean: bool = True
    report_english: bool = False
    extension_test: bool = False
    custom_temperatures: Optional[str] = None
    status: str = 'pending'
    packaging_weight: int = 0
    packaging_unit: str = 'g'
    estimate_date: Optional[str] = None

class ScheduleUpdate(BaseModel):
    data: Dict[str, Any]

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = 'user'
    department: str = ''
    permissions: Optional[Dict] = None
    email: str = ''
    phone: str = ''

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    permissions: Optional[Dict] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class FeeCreate(BaseModel):
    test_item: str
    food_category: str = ""
    price: float = 0
    description: str = ""
    display_order: int = 100
    sample_quantity: int = 0

class FeeUpdate(FeeCreate):
    pass

class ProductTypeCreate(BaseModel):
    type_name: str
    category: str = ""
    sterilization: str = ""
    pasteurization: str = ""
    appearance: str = ""
    test_items: str = ""

class ProductTypeUpdate(ProductTypeCreate):
    pass

class ActivityLogCreate(BaseModel):
    user_id: int
    username: str
    user_name: str
    department: Optional[str] = None
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    details: Optional[str] = None

class ActivityLogFilter(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    action_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    target_type: Optional[str] = None

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str
    message_type: str = 'chat'
    subject: Optional[str] = None

class EmailLogCreate(BaseModel):
    schedule_id: Optional[int] = None
    estimate_type: Optional[str] = None
    sender_email: str
    to_emails: str
    cc_emails: Optional[str] = None
    subject: str
    body: str
    attachment_name: Optional[str] = None
    sent_by: Optional[int] = None
    client_name: Optional[str] = None

class EmailLogStatusUpdate(BaseModel):
    status: Optional[str] = None
    received: Optional[str] = None
    received_at: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None


# ==================== 인증 ====================

def verify_token(authorization: str = Header(None)):
    """토큰 검증"""
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")

    token = authorization.replace("Bearer ", "")
    if token not in sessions:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    return sessions[token]


# ==================== 인증 API ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인"""
    user = User.authenticate(request.username, request.password)

    if user:
        # 토큰 생성
        token = secrets.token_urlsafe(32)
        sessions[token] = user

        return LoginResponse(
            success=True,
            token=token,
            user=user
        )
    else:
        return LoginResponse(
            success=False,
            message="아이디 또는 비밀번호가 올바르지 않습니다"
        )

@app.post("/api/auth/logout")
async def logout(user: dict = Depends(verify_token), authorization: str = Header(None)):
    """로그아웃"""
    token = authorization.replace("Bearer ", "")
    if token in sessions:
        del sessions[token]
    return {"success": True, "message": "로그아웃되었습니다"}

@app.get("/api/auth/me")
async def get_current_user(user: dict = Depends(verify_token)):
    """현재 로그인 사용자 정보"""
    return {"success": True, "data": user}


# ==================== Users API ====================

@app.get("/api/users")
async def get_users(user: dict = Depends(verify_token)):
    """모든 사용자 조회"""
    users = User.get_all()
    return {"success": True, "data": users}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, user: dict = Depends(verify_token)):
    """ID로 사용자 조회"""
    user_data = User.get_by_id(user_id)
    if user_data:
        return {"success": True, "data": user_data}
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

@app.post("/api/users")
async def create_user(request: UserCreate, user: dict = Depends(verify_token)):
    """새 사용자 생성"""
    user_id = User.create(
        username=request.username,
        password=request.password,
        name=request.name,
        role=request.role,
        department=request.department,
        permissions=request.permissions,
        email=request.email,
        phone=request.phone
    )
    if user_id:
        return {"success": True, "data": {"id": user_id}}
    raise HTTPException(status_code=400, detail="사용자 생성에 실패했습니다")

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, request: UserUpdate, user: dict = Depends(verify_token)):
    """사용자 정보 수정"""
    success = User.update(
        user_id=user_id,
        name=request.name,
        department=request.department,
        permissions=request.permissions,
        email=request.email,
        phone=request.phone
    )
    return {"success": success}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, user: dict = Depends(verify_token)):
    """사용자 삭제"""
    success = User.delete(user_id)
    return {"success": success}

@app.post("/api/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: int, activate: bool = True, user: dict = Depends(verify_token)):
    """사용자 활성화/비활성화"""
    success = User.toggle_active(user_id, activate)
    return {"success": success}

@app.post("/api/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, user: dict = Depends(verify_token)):
    """비밀번호 초기화"""
    success = User.reset_password(user_id)
    return {"success": success}

@app.post("/api/users/{user_id}/change-password")
async def change_user_password(user_id: int, new_password: str, user: dict = Depends(verify_token)):
    """비밀번호 변경"""
    success = User.update_password(user_id, new_password)
    return {"success": success}

@app.post("/api/users/{user_id}/verify-password")
async def verify_user_password(user_id: int, password: str, user: dict = Depends(verify_token)):
    """비밀번호 확인"""
    success = User.verify_password(user_id, password)
    return {"success": success}

@app.post("/api/users/{user_id}/toggle-view-all")
async def toggle_user_view_all(user_id: int, can_view: bool = True, user: dict = Depends(verify_token)):
    """사용자 열람권한 토글"""
    success = User.toggle_view_all(user_id, can_view)
    return {"success": success}

@app.get("/api/users/{user_id}/active-status")
async def get_user_active_status(user_id: int, user: dict = Depends(verify_token)):
    """사용자 활성화 상태 조회"""
    status = User.get_active_status(user_id)
    return {"success": True, "data": status}

@app.get("/api/users/{user_id}/view-all-status")
async def get_user_view_all_status(user_id: int, user: dict = Depends(verify_token)):
    """사용자 열람권한 상태 조회"""
    status = User.get_view_all_status(user_id)
    return {"success": True, "data": status}

@app.get("/api/users/constants/departments")
async def get_departments():
    """부서 목록 조회"""
    return {"success": True, "data": DEPARTMENTS}

@app.get("/api/users/constants/permissions")
async def get_permissions():
    """권한 목록 조회"""
    return {"success": True, "data": {
        "labels": PERMISSION_LABELS,
        "by_category": PERMISSION_BY_CATEGORY
    }}


# ==================== Clients API ====================

@app.get("/api/clients")
async def get_clients(
    page: int = 1,
    per_page: int = 100,
    search_keyword: Optional[str] = None,
    search_field: Optional[str] = None,
    sales_rep_filter: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """업체 목록 조회 (페이지네이션)"""
    result = Client.get_paginated(
        page=page,
        per_page=per_page,
        search_keyword=search_keyword,
        search_field=search_field,
        sales_rep_filter=sales_rep_filter
    )
    return {"success": True, "data": result}

@app.get("/api/clients/all")
async def get_all_clients(user: dict = Depends(verify_token)):
    """모든 업체 조회"""
    clients = Client.get_all()
    return {"success": True, "data": clients}

@app.get("/api/clients/count")
async def get_clients_count(user: dict = Depends(verify_token)):
    """업체 수 조회"""
    count = Client.get_total_count()
    return {"success": True, "data": count}

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int, user: dict = Depends(verify_token)):
    """ID로 업체 조회"""
    client = Client.get_by_id(client_id)
    if client:
        return {"success": True, "data": client}
    raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다")

@app.post("/api/clients")
async def create_client(request: ClientCreate, user: dict = Depends(verify_token)):
    """새 업체 생성"""
    client_id = Client.create(**request.dict())
    if client_id:
        return {"success": True, "data": {"id": client_id}}
    raise HTTPException(status_code=400, detail="업체 생성에 실패했습니다")

@app.put("/api/clients/{client_id}")
async def update_client(client_id: int, request: ClientUpdate, user: dict = Depends(verify_token)):
    """업체 정보 수정"""
    success = Client.update(client_id=client_id, **request.dict())
    return {"success": success}

@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: int, user: dict = Depends(verify_token)):
    """업체 삭제"""
    success = Client.delete(client_id)
    return {"success": success}

@app.get("/api/clients/search/{keyword}")
async def search_clients(keyword: str, user: dict = Depends(verify_token)):
    """업체 검색"""
    clients = Client.search(keyword)
    return {"success": True, "data": clients}


# ==================== Schedules API ====================

@app.get("/api/schedules")
async def get_schedules(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """스케줄 목록 조회 (필터링)"""
    if keyword or status or date_from or date_to:
        schedules = Schedule.get_filtered(
            keyword=keyword,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
    else:
        schedules = Schedule.get_all()
    return {"success": True, "data": schedules}

@app.get("/api/schedules/{schedule_id}")
async def get_schedule(schedule_id: int, user: dict = Depends(verify_token)):
    """ID로 스케줄 조회"""
    schedule = Schedule.get_by_id(schedule_id)
    if schedule:
        return {"success": True, "data": schedule}
    raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")

@app.post("/api/schedules")
async def create_schedule(request: ScheduleCreate, user: dict = Depends(verify_token)):
    """새 스케줄 생성"""
    schedule_id = Schedule.create(
        client_id=request.client_id,
        product_name=request.product_name,
        food_type_id=request.food_type_id,
        test_method=request.test_method,
        storage_condition=request.storage_condition,
        test_start_date=request.start_date,
        expected_date=request.expected_date,
        interim_report_date=request.interim_report_date,
        test_period_days=request.test_period_days,
        test_period_months=request.test_period_months,
        test_period_years=request.test_period_years,
        sampling_count=request.sampling_count,
        report_interim=request.report_interim,
        report_korean=request.report_korean,
        report_english=request.report_english,
        extension_test=request.extension_test,
        custom_temperatures=request.custom_temperatures,
        status=request.status,
        packaging_weight=request.packaging_weight,
        packaging_unit=request.packaging_unit,
        estimate_date=request.estimate_date
    )
    if schedule_id:
        return {"success": True, "data": {"id": schedule_id}}
    raise HTTPException(status_code=400, detail="스케줄 생성에 실패했습니다")

@app.put("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, request: ScheduleUpdate, user: dict = Depends(verify_token)):
    """스케줄 정보 수정"""
    success = Schedule.update(schedule_id, request.data)
    return {"success": success}

@app.patch("/api/schedules/{schedule_id}/status")
async def update_schedule_status(schedule_id: int, status: str, user: dict = Depends(verify_token)):
    """스케줄 상태 변경"""
    success = Schedule.update_status(schedule_id, status)
    return {"success": success}

@app.patch("/api/schedules/{schedule_id}/memo")
async def update_schedule_memo(schedule_id: int, memo: str, user: dict = Depends(verify_token)):
    """스케줄 메모 수정"""
    success = Schedule.update_memo(schedule_id, memo)
    return {"success": success}

@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, user: dict = Depends(verify_token)):
    """스케줄 삭제"""
    success = Schedule.delete(schedule_id)
    return {"success": success}

@app.get("/api/schedules/search/{keyword}")
async def search_schedules(keyword: str, user: dict = Depends(verify_token)):
    """스케줄 검색"""
    schedules = Schedule.search(keyword)
    return {"success": True, "data": schedules}


# ==================== Fees API ====================

@app.get("/api/fees")
async def get_fees(user: dict = Depends(verify_token)):
    """모든 수수료 조회"""
    fees = Fee.get_all()
    # dict 변환
    fees_list = [dict(fee) for fee in fees] if fees else []
    return {"success": True, "data": fees_list}

@app.get("/api/fees/{test_item}")
async def get_fee_by_item(test_item: str, user: dict = Depends(verify_token)):
    """검사 항목으로 수수료 조회"""
    fee = Fee.get_by_item(test_item)
    if fee:
        return {"success": True, "data": dict(fee)}
    raise HTTPException(status_code=404, detail="수수료를 찾을 수 없습니다")

@app.post("/api/fees")
async def create_fee(request: FeeCreate, user: dict = Depends(verify_token)):
    """새 수수료 생성"""
    fee_id = Fee.create(
        test_item=request.test_item,
        food_category=request.food_category,
        price=request.price,
        description=request.description,
        display_order=request.display_order,
        sample_quantity=request.sample_quantity
    )
    if fee_id:
        return {"success": True, "data": {"id": fee_id}}
    raise HTTPException(status_code=400, detail="수수료 생성에 실패했습니다")

@app.put("/api/fees/{fee_id}")
async def update_fee(fee_id: int, request: FeeUpdate, user: dict = Depends(verify_token)):
    """수수료 정보 수정"""
    success = Fee.update(
        fee_id=fee_id,
        test_item=request.test_item,
        food_category=request.food_category,
        price=request.price,
        description=request.description,
        display_order=request.display_order,
        sample_quantity=request.sample_quantity
    )
    return {"success": success}

@app.delete("/api/fees/{fee_id}")
async def delete_fee(fee_id: int, user: dict = Depends(verify_token)):
    """수수료 삭제"""
    success = Fee.delete(fee_id)
    return {"success": success}

@app.post("/api/fees/calculate")
async def calculate_fee(test_items: List[str], user: dict = Depends(verify_token)):
    """수수료 계산"""
    total = Fee.calculate_total_fee(test_items)
    return {"success": True, "data": total}


# ==================== Product Types API ====================

@app.get("/api/food-types")
async def get_food_types(user: dict = Depends(verify_token)):
    """모든 식품 유형 조회"""
    types = ProductType.get_all()
    types_list = [dict(t) for t in types] if types else []
    return {"success": True, "data": types_list}

@app.get("/api/food-types/{type_id}")
async def get_food_type(type_id: int, user: dict = Depends(verify_token)):
    """ID로 식품 유형 조회"""
    food_type = ProductType.get_by_id(type_id)
    if food_type:
        return {"success": True, "data": food_type}
    raise HTTPException(status_code=404, detail="식품 유형을 찾을 수 없습니다")

@app.get("/api/food-types/name/{type_name}")
async def get_food_type_by_name(type_name: str, user: dict = Depends(verify_token)):
    """이름으로 식품 유형 조회"""
    food_type = ProductType.get_by_name(type_name)
    if food_type:
        return {"success": True, "data": food_type}
    raise HTTPException(status_code=404, detail="식품 유형을 찾을 수 없습니다")

@app.post("/api/food-types")
async def create_food_type(request: ProductTypeCreate, user: dict = Depends(verify_token)):
    """새 식품 유형 생성"""
    type_id = ProductType.create(
        type_name=request.type_name,
        category=request.category,
        sterilization=request.sterilization,
        pasteurization=request.pasteurization,
        appearance=request.appearance,
        test_items=request.test_items
    )
    if type_id:
        return {"success": True, "data": {"id": type_id}}
    raise HTTPException(status_code=400, detail="식품 유형 생성에 실패했습니다")

@app.put("/api/food-types/{type_id}")
async def update_food_type(type_id: int, request: ProductTypeUpdate, user: dict = Depends(verify_token)):
    """식품 유형 정보 수정"""
    success = ProductType.update(
        type_id=type_id,
        type_name=request.type_name,
        category=request.category,
        sterilization=request.sterilization,
        pasteurization=request.pasteurization,
        appearance=request.appearance,
        test_items=request.test_items
    )
    return {"success": success}

@app.delete("/api/food-types/{type_id}")
async def delete_food_type(type_id: int, user: dict = Depends(verify_token)):
    """식품 유형 삭제"""
    success = ProductType.delete(type_id)
    return {"success": success}

@app.get("/api/food-types/search/{keyword}")
async def search_food_types(keyword: str, user: dict = Depends(verify_token)):
    """식품 유형 검색"""
    types = ProductType.search(keyword)
    types_list = [dict(t) for t in types] if types else []
    return {"success": True, "data": types_list}


# ==================== Schedule Attachments API ====================

@app.get("/api/schedules/{schedule_id}/attachments")
async def get_schedule_attachments(schedule_id: int, user: dict = Depends(verify_token)):
    """스케줄 첨부파일 목록"""
    attachments = ScheduleAttachment.get_by_schedule(schedule_id)
    attachments_list = [dict(a) for a in attachments] if attachments else []
    return {"success": True, "data": attachments_list}


@app.post("/api/schedules/{schedule_id}/attachments")
async def upload_attachment(schedule_id: int, file: UploadFile = File(...), user: dict = Depends(verify_token)):
    """첨부파일 업로드"""
    import tempfile
    import shutil

    try:
        # 임시 파일에 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # ScheduleAttachment.add() 사용
        success, message, attachment_id = ScheduleAttachment.add(schedule_id, tmp_path)

        # 임시 파일 삭제
        try:
            os.unlink(tmp_path)
        except:
            pass

        if success:
            return {"success": True, "message": message, "attachment_id": attachment_id}
        else:
            return {"success": False, "message": message}

    except Exception as e:
        return {"success": False, "message": f"업로드 오류: {str(e)}"}


@app.get("/api/attachments/{attachment_id}")
async def get_attachment(attachment_id: int, user: dict = Depends(verify_token)):
    """첨부파일 정보 조회"""
    attachment = ScheduleAttachment.get_by_id(attachment_id)
    if attachment:
        return {"success": True, "data": dict(attachment)}
    return {"success": False, "message": "첨부파일을 찾을 수 없습니다."}


@app.get("/api/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: int, user: dict = Depends(verify_token)):
    """첨부파일 다운로드"""
    from fastapi.responses import FileResponse

    file_path = ScheduleAttachment.get_file_path(attachment_id)
    if file_path and os.path.exists(file_path):
        attachment = ScheduleAttachment.get_by_id(attachment_id)
        filename = attachment['file_name'] if attachment else os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    return {"success": False, "message": "파일을 찾을 수 없습니다."}


@app.delete("/api/attachments/{attachment_id}")
async def delete_attachment(attachment_id: int, user: dict = Depends(verify_token)):
    """첨부파일 삭제"""
    success, message = ScheduleAttachment.delete(attachment_id)
    return {"success": success, "message": message}


# ==================== Activity Logs API ====================

@app.post("/api/activity-logs")
async def create_activity_log(request: ActivityLogCreate, user: dict = Depends(verify_token)):
    """활동 로그 생성"""
    try:
        # ACTION_TYPES에서 action_name 가져오기
        action_name = ACTION_TYPES.get(request.action_type, request.action_type)

        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO activity_logs
            (user_id, username, user_name, department, action_type, action_name,
             target_type, target_id, target_name, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            request.user_id,
            request.username,
            request.user_name,
            request.department or '',
            request.action_type,
            action_name,
            request.target_type,
            request.target_id,
            request.target_name,
            request.details
        ))

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {"success": True, "data": {"id": log_id}}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/activity-logs")
async def get_activity_logs(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    action_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    user: dict = Depends(verify_token)
):
    """활동 로그 목록 조회 (필터링)"""
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if username:
        filters['username'] = username
    if action_type:
        filters['action_type'] = action_type
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if target_type:
        filters['target_type'] = target_type

    logs = ActivityLog.get_all(limit=limit, offset=offset, filters=filters if filters else None)
    return {"success": True, "data": logs}

@app.get("/api/activity-logs/user/{target_user_id}")
async def get_user_activity_logs(
    target_user_id: int,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(verify_token)
):
    """특정 사용자의 활동 로그 조회"""
    logs = ActivityLog.get_by_user(target_user_id, limit=limit, offset=offset)
    return {"success": True, "data": logs}

@app.get("/api/activity-logs/summary")
async def get_activity_logs_summary(user: dict = Depends(verify_token)):
    """사용자별 활동 요약"""
    summary = ActivityLog.get_user_summary()
    return {"success": True, "data": summary}

@app.get("/api/activity-logs/count")
async def get_activity_logs_count(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    action_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """활동 로그 개수 조회"""
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if username:
        filters['username'] = username
    if action_type:
        filters['action_type'] = action_type
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to

    count = ActivityLog.get_count(filters if filters else None)
    return {"success": True, "data": count}

@app.get("/api/activity-logs/action-types")
async def get_action_types(user: dict = Depends(verify_token)):
    """활동 유형 목록"""
    return {"success": True, "data": ACTION_TYPES}


# ==================== Messages API ====================

@app.post("/api/messages")
async def send_message(request: MessageCreate, user: dict = Depends(verify_token)):
    """메시지 전송"""
    message_id = Message.send(
        sender_id=request.sender_id,
        receiver_id=request.receiver_id,
        content=request.content,
        message_type=request.message_type,
        subject=request.subject
    )
    if message_id:
        return {"success": True, "data": {"id": message_id}}
    return {"success": False, "message": "메시지 전송 실패"}

@app.get("/api/messages/conversation")
async def get_conversation(
    user1_id: int,
    user2_id: int,
    limit: int = 100,
    user: dict = Depends(verify_token)
):
    """두 사용자 간 대화 내역 조회"""
    messages = Message.get_conversation(user1_id, user2_id, limit)
    return {"success": True, "data": messages}

@app.get("/api/messages/partners/{target_user_id}")
async def get_chat_partners(target_user_id: int, user: dict = Depends(verify_token)):
    """대화 상대 목록 조회"""
    partners = Message.get_chat_partners(target_user_id)
    return {"success": True, "data": partners}

@app.post("/api/messages/{message_id}/read")
async def mark_message_read(message_id: int, target_user_id: int, user: dict = Depends(verify_token)):
    """메시지 읽음 처리"""
    success = Message.mark_as_read(message_id, target_user_id)
    return {"success": success}

@app.post("/api/messages/conversation/read")
async def mark_conversation_read(target_user_id: int, partner_id: int, user: dict = Depends(verify_token)):
    """대화 전체 읽음 처리"""
    count = Message.mark_conversation_as_read(target_user_id, partner_id)
    return {"success": True, "data": count}

@app.get("/api/messages/unread-count/{target_user_id}")
async def get_unread_count(target_user_id: int, user: dict = Depends(verify_token)):
    """읽지 않은 메시지 수"""
    count = Message.get_unread_count(target_user_id)
    return {"success": True, "data": count}

@app.get("/api/messages/unread-by-partner/{target_user_id}")
async def get_unread_by_partner(target_user_id: int, user: dict = Depends(verify_token)):
    """상대별 읽지 않은 메시지 수"""
    unread = Message.get_unread_by_partner(target_user_id)
    return {"success": True, "data": unread}

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: int, target_user_id: int, user: dict = Depends(verify_token)):
    """메시지 삭제"""
    success = Message.delete_message(message_id, target_user_id)
    return {"success": success}

@app.delete("/api/messages/conversation/{partner_id}")
async def delete_conversation(partner_id: int, target_user_id: int, user: dict = Depends(verify_token)):
    """대화 전체 삭제"""
    count = Message.delete_conversation(target_user_id, partner_id)
    return {"success": True, "data": count}


# ==================== Email Logs API ====================

@app.post("/api/email-logs")
async def create_email_log(request: EmailLogCreate, user: dict = Depends(verify_token)):
    """이메일 로그 저장"""
    log_id = EmailLog.save(
        schedule_id=request.schedule_id,
        estimate_type=request.estimate_type,
        sender_email=request.sender_email,
        to_emails=request.to_emails,
        cc_emails=request.cc_emails,
        subject=request.subject,
        body=request.body,
        attachment_name=request.attachment_name,
        sent_by=request.sent_by,
        client_name=request.client_name
    )
    if log_id:
        return {"success": True, "data": {"id": log_id}}
    return {"success": False, "message": "이메일 로그 저장 실패"}

@app.get("/api/email-logs")
async def get_email_logs(
    limit: int = 100,
    sent_by: Optional[int] = None,
    user: dict = Depends(verify_token)
):
    """이메일 로그 목록 조회"""
    logs = EmailLog.get_all(limit=limit, sent_by=sent_by)
    return {"success": True, "data": logs}

@app.get("/api/email-logs/{log_id}")
async def get_email_log(log_id: int, user: dict = Depends(verify_token)):
    """이메일 로그 상세 조회"""
    log = EmailLog.get_by_id(log_id)
    if log:
        return {"success": True, "data": log}
    return {"success": False, "message": "이메일 로그를 찾을 수 없습니다"}

@app.get("/api/email-logs/schedule/{schedule_id}")
async def get_email_logs_by_schedule(schedule_id: int, user: dict = Depends(verify_token)):
    """스케줄별 이메일 로그 조회"""
    logs = EmailLog.get_by_schedule(schedule_id)
    return {"success": True, "data": logs}

@app.get("/api/email-logs/search")
async def search_email_logs(
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    sent_by: Optional[int] = None,
    user: dict = Depends(verify_token)
):
    """이메일 로그 검색"""
    logs = EmailLog.search(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        sent_by=sent_by
    )
    return {"success": True, "data": logs}

@app.delete("/api/email-logs/{log_id}")
async def delete_email_log(log_id: int, target_user_id: Optional[int] = None, user: dict = Depends(verify_token)):
    """이메일 로그 삭제"""
    success = EmailLog.delete(log_id, target_user_id)
    return {"success": success}

@app.put("/api/email-logs/{log_id}/status")
async def update_email_log_status(log_id: int, request: EmailLogStatusUpdate, user: dict = Depends(verify_token)):
    """이메일 로그 상태 업데이트"""
    success = EmailLog.update_status(
        log_id,
        status=request.status,
        received=request.received,
        received_at=request.received_at
    )
    return {"success": success}


# ==================== Settings API ====================

@app.get("/api/settings")
async def get_settings(user: dict = Depends(verify_token)):
    """설정 목록 조회"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT `key`, value FROM settings")
        settings = cursor.fetchall()
        conn.close()
        settings_dict = {s['key']: s['value'] for s in settings}
        return {"success": True, "data": settings_dict}
    except Exception as e:
        return {"success": False, "error": str(e), "data": {}}

@app.get("/api/settings/{key}")
async def get_setting(key: str, user: dict = Depends(verify_token)):
    """특정 설정 조회"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"success": True, "data": result['value']}
        return {"success": False, "data": None, "message": "설정을 찾을 수 없습니다"}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


@app.put("/api/settings/{key}")
async def update_setting(key: str, value: str, user: dict = Depends(verify_token)):
    """설정 업데이트"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        # 먼저 업데이트 시도
        cursor.execute("""
            UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
            WHERE `key` = %s
        """, (value, key))

        # 업데이트된 행이 없으면 새로 추가
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO settings (`key`, value) VALUES (%s, %s)
            """, (key, value))

        conn.commit()
        conn.close()
        return {"success": True, "message": "설정이 저장되었습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/settings/batch")
async def update_settings_batch(settings: Dict[str, str], user: dict = Depends(verify_token)):
    """여러 설정 일괄 업데이트"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        for key, value in settings.items():
            cursor.execute("""
                UPDATE settings SET value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE `key` = %s
            """, (value, key))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO settings (`key`, value) VALUES (%s, %s)
                """, (key, value))

        conn.commit()
        conn.close()
        return {"success": True, "message": f"{len(settings)}개 설정이 저장되었습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== User Settings API ====================

@app.get("/api/user-settings/{user_id}")
async def get_user_settings(user_id: int, user: dict = Depends(verify_token)):
    """사용자별 설정 조회"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT `key`, value FROM user_settings WHERE user_id = %s", (user_id,))
        settings = cursor.fetchall()
        conn.close()
        settings_dict = {s['key']: s['value'] for s in settings}
        return {"success": True, "data": settings_dict}
    except Exception as e:
        return {"success": False, "error": str(e), "data": {}}


@app.get("/api/user-settings/{user_id}/{key}")
async def get_user_setting(user_id: int, key: str, user: dict = Depends(verify_token)):
    """사용자별 특정 설정 조회"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_settings WHERE user_id = %s AND `key` = %s", (user_id, key))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"success": True, "data": result['value']}
        return {"success": False, "data": None, "message": "설정을 찾을 수 없습니다"}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


@app.put("/api/user-settings/{user_id}/{key}")
async def update_user_setting(user_id: int, key: str, value: str, user: dict = Depends(verify_token)):
    """사용자별 설정 업데이트"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        # 먼저 업데이트 시도
        cursor.execute("""
            UPDATE user_settings SET value = %s
            WHERE user_id = %s AND `key` = %s
        """, (value, user_id, key))

        # 업데이트된 행이 없으면 새로 추가
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO user_settings (user_id, `key`, value) VALUES (%s, %s, %s)
            """, (user_id, key, value))

        conn.commit()
        conn.close()
        return {"success": True, "message": "설정이 저장되었습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/user-settings/{user_id}/batch")
async def update_user_settings_batch(user_id: int, settings: Dict[str, str], user: dict = Depends(verify_token)):
    """사용자별 여러 설정 일괄 업데이트"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        for key, value in settings.items():
            cursor.execute("""
                UPDATE user_settings SET value = %s
                WHERE user_id = %s AND `key` = %s
            """, (value, user_id, key))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, `key`, value) VALUES (%s, %s, %s)
                """, (user_id, key, value))

        conn.commit()
        conn.close()
        return {"success": True, "message": f"{len(settings)}개 설정이 저장되었습니다"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok", "message": "API 서버가 정상 작동중입니다"}


@app.get("/api/debug/db-config")
async def get_db_config():
    """데이터베이스 설정 확인 (진단용)"""
    from database import load_db_config
    config = load_db_config()
    # 보안을 위해 비밀번호는 마스킹
    return {
        "host": config.get("host"),
        "port": config.get("port"),
        "database": config.get("database"),
        "user": config.get("user"),
        "charset": config.get("charset")
    }


@app.get("/api/debug/db-stats")
async def get_db_stats():
    """데이터베이스 통계 확인 (진단용)"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        stats = {}

        # 각 테이블의 레코드 수 확인
        tables = ['clients', 'schedules', 'users', 'fees', 'food_types']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                result = cursor.fetchone()
                stats[table] = result['cnt'] if result else 0
            except:
                stats[table] = "error"

        conn.close()
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 서버 실행 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("FoodLab API 서버 시작")
    print("=" * 50)
    print("접속 주소: http://0.0.0.0:8000")
    print("API 문서: http://0.0.0.0:8000/docs")
    print("=" * 50)

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
