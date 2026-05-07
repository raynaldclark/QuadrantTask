# -*- coding: utf-8 -*-
"""全局常量：象限定义、颜色、字体等"""

from dataclasses import dataclass
from typing import Dict, List


# ─── 字体 ────────────────────────────────────────────────────────────────────
@dataclass
class FontConfig:
    family: str = "Microsoft YaHei"
    size: int = 13

_font_config = FontConfig()


def get_font_family() -> str:
    return _font_config.family


def set_font_family(name: str) -> None:
    _font_config.family = name


def get_font_size() -> int:
    return _font_config.size


def set_font_size(size: int) -> None:
    _font_config.size = size


# ─── 页面 / 工具栏背景 ────────────────────────────────────────────────────────
BG_PAGE: str = "#F1F5F9"
BG_TOOLBAR: str = "#FFFFFF"

# ─── 卡片 ────────────────────────────────────────────────────────────────────
CARD_BG: str = "#FFFFFF"
CARD_BORDER: str = "#E5E7EB"

# ─── 文字颜色 ─────────────────────────────────────────────────────────────────
TEXT_MAIN: str = "#1E293B"
TEXT_SUB: str = "#64748B"
TEXT_DONE: str = "#94A3B8"

# ─── 主按钮 ──────────────────────────────────────────────────────────────────
BTN_PRIMARY_BG: str = "#1E293B"
BTN_PRIMARY_FG: str = "#FFFFFF"

# ─── 截止日期颜色（默认值，可通过设置界面修改）───────────────────────────────
DEADLINE_COLORS_DEFAULT: Dict[str, str] = {
    "overdue": "#EF4444",
    "today": "#F97316",
    "days3": "#EAB308",
    "days7": "#22C55E",
    "normal": "#3B82F6",
    "none": "#94A3B8",
}

# ─── 截止日期阈值（默认值，可通过设置界面修改）────────────────────────────────
DEADLINE_THRESHOLDS_DEFAULT: Dict[str, int] = {
    "days3": 3,
    "days7": 7,
}

# ─── 截止日期阈值键的顺序（用于 SettingsDialog 渲染）─────────────────────────
DEADLINE_THRESHOLD_KEYS: List[str] = ["days3", "days7"]

# ─── 象限定义 ─────────────────────────────────────────────────────────────────
@dataclass
class QuadrantConfig:
    key: str
    title: str
    subtitle: str
    header_bg: str
    header_fg: str
    body_bg: str
    border: str
    tag_bg: str


QUADS: List[Dict[str, str]] = [
    {
        "key": "q1",
        "title": "紧急且重要",
        "subtitle": "立即处理",
        "header_bg": "#FEE2E2",
        "header_fg": "#991B1B",
        "body_bg": "#FEF2F2",
        "border": "#FECACA",
        "tag_bg": "#FCA5A5",
    },
    {
        "key": "q2",
        "title": "重要不紧急",
        "subtitle": "规划执行",
        "header_bg": "#DBEAFE",
        "header_fg": "#1E40AF",
        "body_bg": "#EFF6FF",
        "border": "#BFDBFE",
        "tag_bg": "#93C5FD",
    },
    {
        "key": "q3",
        "title": "紧急不重要",
        "subtitle": "委托他人",
        "header_bg": "#FEF9C3",
        "header_fg": "#854D0E",
        "body_bg": "#FEFCE8",
        "border": "#FDE047",
        "tag_bg": "#FDE68A",
    },
    {
        "key": "q4",
        "title": "不紧急不重要",
        "subtitle": "考虑删减",
        "header_bg": "#F3F4F6",
        "header_fg": "#1F2937",
        "body_bg": "#F9FAFB",
        "border": "#E5E7EB",
        "tag_bg": "#D1D5DB",
    },
]


def get_quadrant_config(key: str) -> Dict[str, str]:
    """根据 key 获取象限配置"""
    for q in QUADS:
        if q["key"] == key:
            return q
    raise ValueError(f"Unknown quadrant key: {key}")