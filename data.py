# -*- coding: utf-8 -*-
"""数据层：持久化存储、加载、默认值"""

import json
import os

from constants import (
    DEADLINE_COLORS_DEFAULT,
    DEADLINE_THRESHOLDS_DEFAULT,
    QUADS,
)

# ─── 数据路径 ──────────────────────────────────────────────────────────────────
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "quadrant_data.json")


def default_data():
    """返回带有所有默认值的应用数据结构。"""
    return {
        "font_size": 13,
        "geometry": None,
        "deadline_colors":    dict(DEADLINE_COLORS_DEFAULT),
        "deadline_thresholds": dict(DEADLINE_THRESHOLDS_DEFAULT),
        "tasks": {q["key"]: [] for q in QUADS},
    }


def load_data():
    """从 JSON 文件加载数据，带向后兼容迁移。"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)

            # 确保所有象限键存在
            for q in QUADS:
                if q["key"] not in d.get("tasks", {}):
                    d["tasks"][q["key"]] = []

            # 窗口几何（首次可能为 None）
            if "geometry" not in d:
                d["geometry"] = None

            # 截止日期颜色（向后兼容旧数据）
            if "deadline_colors" not in d:
                d["deadline_colors"] = dict(DEADLINE_COLORS_DEFAULT)

            # 截止日期阈值（向后兼容旧数据）
            if "deadline_thresholds" not in d:
                d["deadline_thresholds"] = dict(DEADLINE_THRESHOLDS_DEFAULT)

            return d
        except Exception:
            pass

    return default_data()


def save_data(d):
    """将数据字典写入 JSON 文件。"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"保存失败: {exc}")
