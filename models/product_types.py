#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
식품 유형 관리 모델
내부망: DB 직접 연결
외부망: API 사용
'''

from connection_manager import is_internal_mode, connection_manager

def _get_api():
    """API 클라이언트 반환"""
    return connection_manager.get_api_client()

def _get_connection():
    """DB 연결 반환 (내부망 전용)"""
    from database import get_connection
    return get_connection()

class ProductType:
    @staticmethod
    def get_all():
        """모든 식품 유형 조회"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_types ORDER BY type_name")
            types = cursor.fetchall()
            conn.close()
            return types
        else:
            api = _get_api()
            return api.get_food_types()
    
    @staticmethod
    def get_by_name(type_name):
        """이름으로 식품 유형 조회"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_types WHERE type_name = %s", (type_name,))
            type_info = cursor.fetchone()
            conn.close()
            return dict(type_info) if type_info else None
        else:
            api = _get_api()
            return api.get_food_type_by_name(type_name)

    @staticmethod
    def get_by_id(type_id):
        """ID로 식품 유형 조회"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM food_types WHERE id = %s", (type_id,))
                type_info = cursor.fetchone()
                conn.close()
                return dict(type_info) if type_info else None
            else:
                api = _get_api()
                return api.get_food_type(type_id)
        except Exception as e:
            print(f"식품 유형 ID 조회 중 오류: {str(e)}")
            return None
    
    @staticmethod
    def get_test_items(type_name):
        """식품 유형의 검사 항목 조회"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT test_items FROM food_types WHERE type_name = %s", (type_name,))
            result = cursor.fetchone()
            conn.close()
            return result['test_items'] if result else ""
        else:
            api = _get_api()
            food_type = api.get_food_type_by_name(type_name)
            return food_type.get('test_items', '') if food_type else ""
    
    @staticmethod
    def create(type_name, category="", sterilization="", pasteurization="", appearance="", test_items=""):
        """새 식품 유형 생성"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO food_types (type_name, category, sterilization, pasteurization, appearance, test_items) VALUES (%s, %s, %s, %s, %s, %s)",
                (type_name, category, sterilization, pasteurization, appearance, test_items)
            )
            conn.commit()
            type_id = cursor.lastrowid
            conn.close()
            return type_id
        else:
            api = _get_api()
            return api.create_food_type(
                type_name=type_name,
                category=category,
                sterilization=sterilization,
                pasteurization=pasteurization,
                appearance=appearance,
                test_items=test_items
            )

    @staticmethod
    def update(type_id, type_name, category="", sterilization="", pasteurization="", appearance="", test_items=""):
        """식품 유형 정보 수정"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE food_types SET type_name = %s, category = %s, sterilization = %s, pasteurization = %s, appearance = %s, test_items = %s WHERE id = %s",
                (type_name, category, sterilization, pasteurization, appearance, test_items, type_id)
            )
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount > 0
        else:
            api = _get_api()
            return api.update_food_type(
                type_id,
                type_name=type_name,
                category=category,
                sterilization=sterilization,
                pasteurization=pasteurization,
                appearance=appearance,
                test_items=test_items
            )

    @staticmethod
    def delete(type_id):
        """식품 유형 삭제"""
        if is_internal_mode():
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM food_types WHERE id = %s", (type_id,))
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount > 0
        else:
            api = _get_api()
            return api.delete_food_type(type_id)
    
    @staticmethod
    def delete_all():
        """모든 식품 유형 삭제 (전체 초기화) - 내부망에서만 사용"""
        if not is_internal_mode():
            print("전체 삭제는 내부망에서만 가능합니다.")
            return 0

        try:
            conn = _get_connection()
            cursor = conn.cursor()

            # 삭제 전 행 수 확인
            cursor.execute("SELECT COUNT(*) as cnt FROM food_types")
            result = cursor.fetchone()
            count_before = result['cnt'] if result else 0

            # 테이블 데이터 삭제
            cursor.execute("DELETE FROM food_types")

            # 트랜잭션 커밋
            conn.commit()

            # 삭제 후 행 수 확인
            cursor.execute("SELECT COUNT(*) as cnt FROM food_types")
            result = cursor.fetchone()
            count_after = result['cnt'] if result else 0

            conn.close()

            # 실제 삭제된 행 수 계산
            deleted_count = count_before - count_after

            print(f"삭제 전: {count_before}, 삭제 후: {count_after}, 삭제된 행 수: {deleted_count}")

            return deleted_count
        except Exception as e:
            # 오류 발생 시 롤백
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            print(f"전체 삭제 중 오류 발생: {str(e)}")
            raise e

    @staticmethod
    def search(keyword):
        """식품 유형명이나 카테고리로 검색"""
        try:
            if is_internal_mode():
                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM food_types
                    WHERE type_name LIKE %s OR category LIKE %s
                    ORDER BY type_name
                """, (f"%{keyword}%", f"%{keyword}%"))
                food_types = cursor.fetchall()
                conn.close()
                return food_types
            else:
                api = _get_api()
                return api.search_food_types(keyword)
        except Exception as e:
            print(f"식품 유형 검색 중 오류: {str(e)}")
            return []