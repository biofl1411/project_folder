#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
식품 유형 관리 모델
'''

from database import get_connection

class ProductType:
    @staticmethod
    def get_all():
        """모든 식품 유형 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM food_types ORDER BY type_name")
        types = cursor.fetchall()
        conn.close()
        return types
    
    @staticmethod
    def get_by_name(type_name):
        """이름으로 식품 유형 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM food_types WHERE type_name = %s", (type_name,))
        type_info = cursor.fetchone()
        conn.close()
        return dict(type_info) if type_info else None

    @staticmethod
    def get_by_id(type_id):
        """ID로 식품 유형 조회"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_types WHERE id = %s", (type_id,))
            type_info = cursor.fetchone()
            conn.close()
            return dict(type_info) if type_info else None
        except Exception as e:
            print(f"식품 유형 ID 조회 중 오류: {str(e)}")
            return None
    
    @staticmethod
    def get_test_items(type_name):
        """식품 유형의 검사 항목 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT test_items FROM food_types WHERE type_name = %s", (type_name,))
        result = cursor.fetchone()
        conn.close()
        return result['test_items'] if result else ""
    
    @staticmethod
    def create(type_name, category="", sterilization="", pasteurization="", appearance="", test_items=""):
        """새 식품 유형 생성"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO food_types (type_name, category, sterilization, pasteurization, appearance, test_items) VALUES (%s, %s, %s, %s, %s, %s)",
            (type_name, category, sterilization, pasteurization, appearance, test_items)
        )
        conn.commit()
        type_id = cursor.lastrowid
        conn.close()
        return type_id

    @staticmethod
    def update(type_id, type_name, category="", sterilization="", pasteurization="", appearance="", test_items=""):
        """식품 유형 정보 수정"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE food_types SET type_name = %s, category = %s, sterilization = %s, pasteurization = %s, appearance = %s, test_items = %s WHERE id = %s",
            (type_name, category, sterilization, pasteurization, appearance, test_items, type_id)
        )
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount > 0

    @staticmethod
    def delete(type_id):
        """식품 유형 삭제"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM food_types WHERE id = %s", (type_id,))
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount > 0
    
    @staticmethod
    def delete_all():
        """모든 식품 유형 삭제 (전체 초기화)"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 삭제 전 행 수 확인
            cursor.execute("SELECT COUNT(*) FROM food_types")
            count_before = cursor.fetchone()[0]
            
            # 트랜잭션 시작
            conn.execute("BEGIN TRANSACTION")
            
            # 테이블 데이터 삭제
            cursor.execute("DELETE FROM food_types")
            
            # 자동 증가 ID 초기화 (SQLite 기준)
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='food_types'")
            
            # 트랜잭션 커밋
            conn.commit()
            
            # 삭제 후 행 수 확인
            cursor.execute("SELECT COUNT(*) FROM food_types")
            count_after = cursor.fetchone()[0]
            
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
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM food_types
                WHERE type_name LIKE %s OR category LIKE %s
                ORDER BY type_name
            """, (f"%{keyword}%", f"%{keyword}%"))
            food_types = cursor.fetchall()
            conn.close()
            
            return food_types
        except Exception as e:
            print(f"식품 유형 검색 중 오류: {str(e)}")
            return []