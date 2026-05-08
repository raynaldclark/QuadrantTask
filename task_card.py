# -*- coding: utf-8 -*-
"""TaskCard：可拖拽的任务卡片组件"""

import os
import sys
from datetime import date, datetime
from typing import Callable, Dict, Optional

from PySide6.QtCore import QMimeData, QPoint, QRect, QSize, Qt, Slot
from PySide6.QtGui import (
    QColor, QCursor, QDrag, QFont, QFontMetrics, QPainter, QPen, QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget, QLabel, QFrame

from constants import CARD_BG, CARD_BORDER, TEXT_DONE, TEXT_MAIN, get_font_family


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
        task: Dict[str, any],
        quad_cfg: Dict[str, str],
        font_size: int,
        deadline_colors: Dict[str, str],
        deadline_thresholds: Dict[str, int],
        on_toggle: Callable[[Dict[str, any]], None],
        on_delete: Callable[[str], None],
        on_edit: Callable[[Dict[str, any]], None],
        parent: Optional[QWidget] = None,
    ) -> None:
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
        self._target_quad: Optional[str] = None
        self._show_actions = False
        self._action_hover_del = False
        self._del_btn_rect: Optional[QRect] = None

        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setAttribute(Qt.WA_Hover, True)
        logical_min_width = max(195, self._logical_to_physical(195))
        self.setMinimumWidth(logical_min_width)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        from PySide6.QtCore import QTimer
        self._action_timer = QTimer(self)
        self._action_timer.setSingleShot(True)
        self._action_timer.timeout.connect(self._show_action_bar)

        self._text_label = QLabel(self)
        self._text_label.setTextFormat(Qt.PlainText)
        self._text_label.setWordWrap(True)
        self._text_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._text_label.setFrameShape(QFrame.NoFrame)
        self._text_label.setStyleSheet("QLabel { border: none; background: transparent; }")

    def _logical_to_physical(self, logical: int) -> int:
        """将逻辑像素转换为物理像素（考虑 DPI 缩放）"""
        return int(logical * self.devicePixelRatio())

    def _px(self, logical: int) -> int:
        """简化的物理像素转换"""
        return self._logical_to_physical(logical)

    def _update_text_label(self) -> None:
        checked = self.task.get("done", False)
        font = QFont(get_font_family(), self.font_size)
        if checked:
            font.setStrikeOut(True)
        self._text_label.setFont(font)
        self._text_label.setStyleSheet(
            f"QLabel {{ color: {'#94A3B8' if checked else '#1E293B'}; background: transparent; border: none; }}"
        )
        self._text_label.setText(self.task.get("text", ""))

        chk_right = self._checkbox_rect().right()
        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12
        text_right = self.width() - dl_w - 4
        text_w = text_right - chk_right + 2
        if text_w < 20:
            text_w = 20
        text_x = chk_right + 4
        self._text_label.setGeometry(text_x, 0, text_w, self.height())

    def task_id(self) -> str:
        return self.task["id"]

    def set_target_quad(self, quad_key: Optional[str]) -> None:
        self._target_quad = quad_key
        self.update()

    def clear_target_quad(self) -> None:
        self._target_quad = None
        self.update()

    def update_font(self, font_size: int) -> None:
        self.font_size = font_size
        self._update_text_label()
        self.update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_text_label()

    @staticmethod
    def deadline_color(
        dl: str,
        deadline_colors: Dict[str, str],
        deadline_thresholds: Dict[str, int],
    ) -> QColor:
        """根据剩余天数返回对应的截止日期颜色 QColor。"""
        try:
            d = datetime.strptime(dl, "%Y-%m-%d").date()
            diff = (d - date.today()).days
            if diff <= 0:
                return QColor(deadline_colors.get("overdue", "#EF4444"))
            if diff <= deadline_thresholds.get("urgent", 3):
                return QColor(deadline_colors.get("urgent", "#EAB308"))
            if diff <= deadline_thresholds.get("short_term", 7):
                return QColor(deadline_colors.get("short_term", "#22C55E"))
            if diff <= deadline_thresholds.get("medium_term", 14):
                return QColor(deadline_colors.get("medium_term", "#3B82F6"))
            return QColor(deadline_colors.get("long_term", "#8B5CF6"))
        except Exception:
            return QColor(deadline_colors.get("none", "#94A3B8"))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

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

        tag_rect = self.rect().adjusted(4, 6, -(self.width() - 9), -6)
        painter.setBrush(QColor(self.quad_cfg["tag_bg"]))
        painter.setPen(Qt.NoPen)
        painter.drawRect(tag_rect)

        chk_rect = self._checkbox_rect()
        checked = self.task.get("done", False)
        self._draw_checkbox(painter, chk_rect, checked)

        self._update_text_label()

        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12

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

    def _draw_delete_icon(self, painter: QPainter, rect: QRect, hovered: bool) -> None:
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

    def _draw_checkbox(self, painter: QPainter, rect: QRect, checked: bool) -> None:
        from PySide6.QtCore import QRect as QtRect
        box_rect = QtRect(rect.x() + 4, (rect.height() - 14) // 2, 14, 14)
        painter.setPen(QPen(QColor("#CBD5E1"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(box_rect)
        if checked:
            painter.setPen(QPen(QColor("#3B82F6"), 2))
            painter.drawLine(box_rect.x() + 2, box_rect.y() + 7, box_rect.x() + 5, box_rect.y() + 10)
            painter.drawLine(box_rect.x() + 5, box_rect.y() + 10, box_rect.x() + 12, box_rect.y() + 3)

    def _checkbox_rect(self) -> QRect:
        from PySide6.QtCore import QRect
        return QRect(18, 0, 22, self.height())

    @Slot()
    def _show_action_bar(self) -> None:
        self._show_actions = True
        self.update()

    @Slot()
    def _hide_action_bar(self) -> None:
        self._show_actions = False
        self._action_hover_del = False
        self._action_timer.stop()
        self.update()
        self.updateGeometry()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()

            if self._show_actions:
                if self._del_btn_rect is not None and self._del_btn_rect.contains(pos):
                    self.on_delete(self.task["id"])
                    self._hide_action_bar()
                    return

            if self._checkbox_rect().contains(pos):
                self.task["done"] = not self.task.get("done", False)
                self.on_toggle(self.task)
                self.update()
                return

            self._dragging = True
            self._drag_start_pos = pos
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event) -> None:
        if self._show_actions:
            pos = event.position().toPoint()
            del_hovered = self._del_btn_rect is not None and self._del_btn_rect.contains(pos)
            if bool(del_hovered) != self._action_hover_del:
                self._action_hover_del = bool(del_hovered)
                self.update()

        if event.buttons() & Qt.LeftButton and self._dragging:
            pos = event.position().toPoint()
            if (pos - self._drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                self._start_drag()

    def _start_drag(self) -> None:
        self._dragging = False
        self.setCursor(QCursor(Qt.OpenHandCursor))

        mime = QMimeData()
        task_id = self.task["id"]
        src_quad = self.quad_cfg["key"]
        mime.setData(self.MIME_TYPE, f"{src_quad}:{task_id}".encode("utf-8"))

        pixmap = self._make_pixmap()
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.exec(Qt.MoveAction)

    def _make_pixmap(self) -> QPixmap:
        size = self.size()
        from PySide6.QtCore import QRect as QtRect, QPoint as QtPoint
        pm = QPixmap(size * self.devicePixelRatio())
        pm.setDevicePixelRatio(self.devicePixelRatio())
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setOpacity(0.82)
        self.render(
            painter, QtPoint(0, 0),
            QtRect(QtPoint(0, 0), size),
            QWidget.RenderFlag.DrawChildren,
        )
        painter.end()
        return pm

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.on_edit(self.task)

    def enterEvent(self, event) -> None:
        self._hover = True
        self._action_timer.start(300)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._hide_action_bar()
        super().leaveEvent(event)

    def sizeHint(self) -> QSize:
        w = max(self.width(), 200)
        if w < 200:
            w = 200
        font = QFont(get_font_family(), self.font_size)
        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12
        chk_right = 40
        text_w = w - dl_w - chk_right - 8
        if text_w < 20:
            text_w = 20
        temp_label = QLabel(self.task.get("text", ""))
        temp_label.setFont(font)
        temp_label.setWordWrap(True)
        temp_label.setTextFormat(Qt.PlainText)
        temp_label.setFixedWidth(text_w)
        h = temp_label.sizeHint().height()
        if h <= 0:
            h = font.pixelSize() * 1.2
        h += 10
        return QSize(w, max(40, h))

    def heightForWidth(self, width: Optional[int] = None) -> int:
        if width is None:
            width = self.width()
        font = QFont(get_font_family(), self.font_size)
        fm_dl = QFontMetrics(QFont(get_font_family(), self.font_size - 2))
        dl_w = fm_dl.horizontalAdvance("2025-12-31") + 12
        chk_right = 40
        text_w = width - dl_w - chk_right - 8
        if text_w < 20:
            text_w = 20
        temp_label = QLabel(self.task.get("text", ""))
        temp_label.setFont(font)
        temp_label.setWordWrap(True)
        temp_label.setTextFormat(Qt.PlainText)
        temp_label.setFixedWidth(text_w)
        h = temp_label.sizeHint().height()
        if h <= 0:
            h = font.pixelSize() * 1.2
        h += 10
        return max(40, h)