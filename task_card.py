# -*- coding: utf-8 -*-
"""TaskCard：可拖拽的任务卡片组件"""

from datetime import datetime, date

from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QFont, QCursor, QDrag, QFontMetrics, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy

from constants import (
    CARD_BG,
    CARD_BORDER,
    TEXT_DONE,
    TEXT_MAIN,
    get_font_family,
)

import os
import sys

if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(__file__)
_DELETE_ICON_PATH = os.path.join(_BASE_DIR, "source", "delete.svg")
_delete_icon_renderer = QSvgRenderer(_DELETE_ICON_PATH) if os.path.exists(_DELETE_ICON_PATH) else None


class TaskCard(QWidget):
    """可拖拽的任务卡片，支持 hover 动作条和 Qt 原生拖拽。"""

    MIME_TYPE = "application/x-quadrant-task"

    def __init__(
        self,
        task,
        quad_cfg,
        font_size,
        deadline_colors,
        deadline_thresholds,
        on_toggle,
        on_delete,
        on_edit,
        parent=None,
    ):
        super().__init__(parent)
        self.task = task
        self.quad_cfg = quad_cfg
        self.font_size = font_size
        self.deadline_colors = deadline_colors
        self.deadline_thresholds = deadline_thresholds
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_edit = on_edit

        self._dragging = False
        self._drag_start_pos = QPoint()
        self._hover = False
        self._target_quad = None          # 拖拽悬停目标象限
        self._show_actions = False        # hover 动作条
        self._action_hover_del = False
        self._painting = False

        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setAttribute(Qt.WA_Hover, True)
        self.setMinimumWidth(195)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

        # 300ms 延迟显示动作条
        self._action_timer = QTimer(self)
        self._action_timer.setSingleShot(True)
        self._action_timer.timeout.connect(self._show_action_bar)

    # ─── 公开 API ──────────────────────────────────────────────────────────────

    def task_id(self):
        return self.task["id"]

    def set_target_quad(self, quad_key):
        self._target_quad = quad_key
        self.update()

    def clear_target_quad(self):
        self._target_quad = None
        self.update()

    def update_font(self, font_size):
        self.font_size = font_size
        self.update()

    # ─── 颜色计算 ───────────────────────────────────────────────────────────────

    @staticmethod
    def deadline_color(dl, deadline_colors, deadline_thresholds):
        """根据剩余天数返回对应的截止日期颜色 QColor。"""
        try:
            d = datetime.strptime(dl, "%Y-%m-%d").date()
            diff = (d - date.today()).days
            if diff < 0:
                return QColor(deadline_colors.get("overdue", "#EF4444"))
            if diff == 0:
                return QColor(deadline_colors.get("today", "#F97316"))
            if diff <= deadline_thresholds.get("days3", 3):
                return QColor(deadline_colors.get("days3", "#EAB308"))
            if diff <= deadline_thresholds.get("days7", 7):
                return QColor(deadline_colors.get("days7", "#22C55E"))
            return QColor(deadline_colors.get("normal", "#3B82F6"))
        except Exception:
            return QColor(deadline_colors.get("none", "#94A3B8"))

    # ─── 绘制 ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ── 背景 ──
        if self._target_quad:
            painter.setBrush(QColor(CARD_BG))
            painter.setPen(QPen(QColor("#3B82F6"), 3))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        elif self._hover:
            painter.setBrush(QColor("#F8FAFC"))
            painter.setPen(QPen(QColor("#CBD5E1"), 1))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        else:
            painter.setBrush(QColor(CARD_BG))
            painter.setPen(QPen(QColor(CARD_BORDER), 1))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # ── 左侧色条 ──
        tag_rect = self.rect().adjusted(4, 6, -(self.width() - 9), -6)
        painter.setBrush(QColor(self.quad_cfg["tag_bg"]))
        painter.setPen(Qt.NoPen)
        painter.drawRect(tag_rect)

        # ── 复选框 ──
        chk_rect = self._chk_rect()
        checked = self.task.get("done", False)
        self._draw_checkbox(painter, chk_rect, checked)

        # ── 文字 ──
        font = QFont(get_font_family(), self.font_size)
        if checked:
            font.setStrikeOut(True)
        painter.setFont(font)
        text_color = QColor(TEXT_DONE) if checked else QColor(TEXT_MAIN)
        painter.setPen(text_color)

        # 日期宽度按字号精确计算（10字符 + 左右padding）
        fm = QFontMetrics(font)
        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12   # 12 = 左右各6px padding
        # 文字区域右边界 = card_right - dl_w - 4（即日期左边界 - 4px inset）
        text_right = self.width() - dl_w - 4
        text_w = text_right - chk_rect.right() - 4
        # 使用 boundingRect 获取 Qt 实际换行后的精确高度
        br_rect = QRect(0, 0, text_w, 1677216)
        br = fm.boundingRect(br_rect, Qt.AlignVCenter | Qt.TextWordWrap, self.task.get("text", ""))
        card_h = max(40, br.height() + 10)

        # 只有不在重绘中且高度差异大于1px时才更新高度
        if not self._painting and abs(self.height() - card_h) > 1:
            self._painting = True
            self.setFixedHeight(card_h)
            self._painting = False

        # 文字区域（使用实际卡片高度以保持垂直居中）
        text_rect = QRect(chk_rect.right() + 4, 0, text_w, max(card_h, self.height()))
        painter.drawText(
            text_rect.adjusted(4, 0, 0, 0),
            Qt.AlignVCenter | Qt.TextWordWrap,
            self.task.get("text", ""),
        )

        # ── 截止日期 ──
        dl = self.task.get("deadline", "")
        if dl:
            painter.setFont(QFont(get_font_family(), self.font_size - 2))
            painter.setPen(
                self.deadline_color(dl, self.deadline_colors, self.deadline_thresholds)
            )
            dl_rect = self.rect().adjusted(
                self.width() - dl_w, 0, -5, 0
            )
            painter.drawText(dl_rect, Qt.AlignVCenter | Qt.AlignRight, dl)

        # ── hover 动作条 ──
        if self._show_actions:
            bar_h = fm_dl.lineSpacing()
            bar_y = (self.height() - bar_h) // 2
            bg_rect = QRect(self.width() - 42, bar_y - 2, 36, bar_h + 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawRoundedRect(bg_rect, 6, 6)
            del_rect = self._del_btn_rect = QRect(
                self.width() - 38, bar_y,
                28, bar_h
            )
            self._draw_delete_icon(painter, del_rect, self._action_hover_del)

    def _draw_delete_icon(self, painter, rect, hovered):
        if _delete_icon_renderer:
            size = self.font_size * 2
            if size > rect.width():
                size = rect.width()
            x = rect.x() + (rect.width() - size) // 2
            y = rect.y() + (rect.height() - size) // 2
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            _delete_icon_renderer.render(p)
            p.end()
            painter.drawPixmap(x, y, pixmap)

    def _draw_checkbox(self, painter, rect, checked):
        from PySide6.QtCore import QRect
        box_rect = QRect(rect.x() + 4, (rect.height() - 14) // 2, 14, 14)
        painter.setPen(QPen(QColor("#CBD5E1"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(box_rect)
        if checked:
            painter.setPen(QPen(QColor("#3B82F6"), 2))
            painter.drawLine(box_rect.x() + 2, box_rect.y() + 7,  box_rect.x() + 5, box_rect.y() + 10)
            painter.drawLine(box_rect.x() + 5, box_rect.y() + 10, box_rect.x() + 12, box_rect.y() + 3)

    def _chk_rect(self):
        from PySide6.QtCore import QRect
        return QRect(18, 0, 22, self.height())

    # ─── 鼠标事件 ───────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()

            # 动作条按钮优先检测
            if self._show_actions:
                if getattr(self, "_del_btn_rect", None) and self._del_btn_rect.contains(pos):
                    self.on_delete(self.task["id"])
                    self._hide_action_bar()
                    return

            # 复选框区域
            if self._chk_rect().contains(pos):
                self.task["done"] = not self.task.get("done", False)
                self.on_toggle(self.task)
                self.update()
                return

            # 开始拖拽
            self._dragging = True
            self._drag_start_pos = pos
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        # 动作条 hover 检测
        if self._show_actions:
            pos = event.position().toPoint()
            del_h  = getattr(self, "_del_btn_rect", None) and self._del_btn_rect.contains(pos)
            if bool(del_h) != self._action_hover_del:
                self._action_hover_del  = bool(del_h)
                self.update()

        # 拖拽距离检测
        if event.buttons() & Qt.LeftButton and self._dragging:
            pos = event.position().toPoint()
            if (pos - self._drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                self._start_drag()

    def _start_drag(self):
        self._dragging = False
        self.setCursor(QCursor(Qt.OpenHandCursor))

        from PySide6.QtCore import QMimeData
        mime = QMimeData()
        task_id  = self.task["id"]
        src_quad = self.quad_cfg["key"]
        mime.setData(self.MIME_TYPE, f"{src_quad}:{task_id}".encode("utf-8"))

        pixmap = self._make_pixmap()
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.exec(Qt.MoveAction)

    def _make_pixmap(self):
        size = self.size()
        from PySide6.QtCore import QRect, QPoint
        pm = QPixmap(size * self.devicePixelRatio())
        pm.setDevicePixelRatio(self.devicePixelRatio())
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setOpacity(0.82)
        self.render(
            painter, QPoint(0, 0),
            QRect(QPoint(0, 0), size),
            QWidget.RenderFlag.DrawChildren,
        )
        painter.end()
        return pm

    def mouseReleaseEvent(self, _):
        self._dragging = False
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_edit(self.task)

    def enterEvent(self, event):
        self._hover = True
        self._action_timer.start(300)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._hide_action_bar()
        super().leaveEvent(event)

    def _show_action_bar(self):
        self._show_actions = True
        self.update()

    def _hide_action_bar(self):
        self._show_actions = False
        self._action_hover_del = False
        self._action_timer.stop()
        self.update()
        self.updateGeometry()

    def sizeHint(self):
        w = max(self.width(), 200)
        font = QFont(get_font_family(), self.font_size)
        fm = QFontMetrics(font)
        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12
        chk_right = 40
        text_w = w - dl_w - chk_right - 8
        br_rect = QRect(0, 0, text_w, 1677216)
        br = fm.boundingRect(br_rect, Qt.AlignVCenter | Qt.TextWordWrap, self.task.get("text", ""))
        h = max(40, br.height() + 10)
        return QSize(w, h)
