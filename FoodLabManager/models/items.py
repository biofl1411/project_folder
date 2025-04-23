#item.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
실험 항목 관리 모델
'''

# 상대 경로 임포트 대신 절대 경로 임포트 사용
from database import get_connection

class Item:
    @staticmethod
    def get_all():
        """모든 항목 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items ORDER BY category, name")
        items = cursor.fetchall()
        conn.close()
        return items
    
    @staticmethod
    def get_by_id(item_id):
        """ID로 항목 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        conn.close()
        return item
    
    @staticmethod
    def create(name, category, description=""):
        """새 항목 생성"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (name, category, description) VALUES (?, ?, ?)",
            (name, category, description)
        )
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id
    
    @staticmethod
    def update(item_id, name, category, description=""):
        """항목 수정"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET name = ?, category = ?, description = ? WHERE id = ?",
            (name, category, description, item_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(item_id):
        """항목 삭제"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_by_category(category):
        """카테고리별 항목 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE category = ? ORDER BY name", (category,))
        items = cursor.fetchall()
        conn.close()
        return items
    
    @staticmethod
    def get_categories():
        """모든 카테고리 목록 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category")
        categories = [row['category'] for row in cursor.fetchall()]
        conn.close()
        return categories