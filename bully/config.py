# -*- coding: utf-8 -*-
"""路徑、檔名與圖表樣式設定"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get('TIGPS_DIR', ROOT / 'data'))    # 可用環境變數 TIGPS_DIR 指到別的資料夾
RESULTS_DIR = ROOT / 'results'
FIG_DIR = ROOT / 'figures'

# TIGPS 原始檔(放在 DATA_DIR 底下任何子資料夾皆可,程式會自動尋找)
FILES = {
    'w1_student': 'TIGPSw1_s.dta',    # 2023 第一波 學生
    'w1_parent': 'TIGPSw1_p.dta',     # 2023 第一波 照顧者
    'w1_teacher': 'TIGPSw1_t.dta',    # 2023 第一波 導師
    'w2_student': 'TIGPSw2_s.dta',    # 2024 第二波 學生
}


def find(key):
    """在 DATA_DIR 裡遞迴尋找檔案"""
    name = FILES[key]
    hits = sorted(DATA_DIR.rglob(name))
    if not hits:
        raise FileNotFoundError(f'找不到 {name}。請依 data/README.md 把 TIGPS 檔案放進 {DATA_DIR}')
    return hits[0]


# 圖表顏色
INK, INK2, MUTED, GRID, SURF = '#1b1f24', '#50565d', '#858a8f', '#e3e5df', '#fcfcfb'
RED, GREY, BLUE = '#c2452d', '#858a8f', '#2a78d6'
ROLE_COLORS = {'無涉入': '#8fb8a8', '純受害': '#5b8fc9', '純加害': '#e0a33a', '加害受害': '#c2452d'}
FONTS = ['Microsoft JhengHei', 'Noto Sans TC', 'Noto Sans CJK TC', 'PingFang TC', 'Heiti TC']
