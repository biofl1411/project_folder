#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
버전 관리 모듈
'''

# 현재 버전 (Major.Minor.Patch)
VERSION = "1.0.10"

# GitHub 저장소 정보
GITHUB_OWNER = "biofl1411"
GITHUB_REPO = "project_folder"

# 앱 정보
APP_NAME = "FoodLabManager"
APP_DISPLAY_NAME = "식품 실험/분석 관리 시스템"

def get_version():
    """현재 버전 반환"""
    return VERSION

def get_version_tuple():
    """버전을 튜플로 반환 (비교용)"""
    return tuple(map(int, VERSION.split('.')))

def get_app_info():
    """앱 정보 반환"""
    return {
        'name': APP_NAME,
        'display_name': APP_DISPLAY_NAME,
        'version': VERSION,
        'github_owner': GITHUB_OWNER,
        'github_repo': GITHUB_REPO
    }
