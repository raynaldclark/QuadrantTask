# -*- coding: utf-8 -*-
"""全局常量：象限定义、颜色、字体等"""

# ─── 字体 ────────────────────────────────────────────────────────────────────
_FONT_FAMILY = "Microsoft YaHei"

def get_font_family():
    return _FONT_FAMILY

def set_font_family(name):
    global _FONT_FAMILY
    _FONT_FAMILY = name

# ─── 页面 / 工具栏背景 ────────────────────────────────────────────────────────
BG_PAGE    = "#F1F5F9"
BG_TOOLBAR = "#FFFFFF"

# ─── 卡片 ────────────────────────────────────────────────────────────────────
CARD_BG     = "#FFFFFF"
CARD_BORDER = "#E5E7EB"

# ─── 文字颜色 ─────────────────────────────────────────────────────────────────
TEXT_MAIN = "#1E293B"
TEXT_SUB  = "#64748B"
TEXT_DONE = "#94A3B8"

# ─── 主按钮 ──────────────────────────────────────────────────────────────────
BTN_PRIMARY_BG = "#1E293B"
BTN_PRIMARY_FG = "#FFFFFF"

# ─── 截止日期颜色（默认值，可通过设置界面修改）───────────────────────────────
DEADLINE_COLORS_DEFAULT = {
    "overdue": "#EF4444",   # 过期（红色）
    "today":   "#F97316",   # 今天（橙色）
    "days3":   "#EAB308",   # 1-3天（黄色）
    "days7":   "#22C55E",   # 4-7天（绿色）
    "normal":  "#3B82F6",   # >7天（蓝色）
    "none":    "#94A3B8",   # 无日期（灰色）
}

# ─── 截止日期阈值（默认值，可通过设置界面修改）────────────────────────────────
DEADLINE_THRESHOLDS_DEFAULT = {
    "days3":  3,
    "days7":  7,
}

# ─── 截止日期阈值键的顺序（用于 SettingsDialog 渲染）─────────────────────────
DEADLINE_THRESHOLD_KEYS = ["days3", "days7"]

# ─── 象限定义 ─────────────────────────────────────────────────────────────────
QUADS = [
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
