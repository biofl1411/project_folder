#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
업체정보 관리 모델
'''

from database import get_connection

class Client:
    @staticmethod
    def get_all():
        """모든 업체 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY name")
        clients = cursor.fetchall()
        conn.close()
        return clients
    
    @staticmethod
    def get_by_id(client_id):
        """ID로 업체 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        conn.close()
        return client
    
    @staticmethod
    def create(name, ceo="", phone="", address="", contact_person="", mobile="", sales_rep=""):
        """새 업체 생성"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clients (name, ceo, phone, address, contact_person, mobile, sales_rep) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, ceo, phone, address, contact_person, mobile, sales_rep)
        )
        conn.commit()
        client_id = cursor.lastrowid
        conn.close()
        return client_id
    
    @staticmethod
    def update(client_id, name, ceo="", phone="", address="", contact_person="", mobile="", sales_rep=""):
        """업체 정보 수정"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clients SET name = ?, ceo = ?, phone = ?, address = ?, contact_person = ?, mobile = ?, sales_rep = ? WHERE id = ?",
            (name, ceo, phone, address, contact_person, mobile, sales_rep, client_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(client_id):
        """업체 삭제"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def search(keyword):
        """키워드로 업체 검색"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM clients 
            WHERE name LIKE ? OR contact_person LIKE ? OR ceo LIKE ?
            ORDER BY name
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        clients = cursor.fetchall()
        conn.close()
        return clients