# -*- coding: utf-8 -*-
"""QuadrantPanel：可接受拖拽的象限面板"""

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtWidgets import QScrollArea

from constants import FONT_FAMILY
from task_card import TaskCard


class QuadrantPanel(QFrame):
    """单个象限区域：显示任务列表 + 接受拖拽放下。"""

    def __init__(self, cfg, data, app, parent=None):
        super().__init__(parent)
        self.cfg  = cfg
        self.data = data
        self.app  = app
        self.q_key = cfg["key"]
        self.show_done = False

        self._setup_ui()

    # ─── 公开 API ──────────────────────────────────────────────────────────────

    def render_tasks(self):
        """重新渲染任务卡片列表。"""
        # 清除现有卡片（保留 stretch item）
        while self.task_layout.count() > 1:
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks  = self.data["tasks"].get(self.q_key, [])
        fs     = self.data["font_size"]
        visible = [t for t in tasks if not t.get("done") or self.show_done]

        for task in visible:
            card = TaskCard(
                task=task,
                quad_cfg=self.cfg,
                font_size=fs,
                deadline_colors=self.data.get("deadline_colors", {}),
                deadline_thresholds=self.data.get("deadline_thresholds", {"days3": 3, "days7": 7, "normal": 999}),
                on_toggle=self._on_toggle,
                on_delete=self._on_delete,
                on_edit=self._on_edit,
            )
            self.task_layout.insertWidget(self.task_layout.count() - 1, card)
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self._update_count()

    def clear_done(self):
        self.data["tasks"][self.q_key] = [
            t for t in self.data["tasks"][self.q_key] if not t.get("done")
        ]
        self.app.save()
        self.render_tasks()

    def clear_all(self):
        self.data["tasks"][self.q_key] = []
        self.app.save()
        self.render_tasks()

    # ─── 内部事件处理器 ────────────────────────────────────────────────────────

    def _on_toggle(self, task):
        self.app._undo_stack.append({
            "type": "toggle",
            "q_key": self.q_key,
            "task_id": task["id"],
            "old_state": not task.get("done", False)
        })
        self.app._update_undo_icon()
        self.app.save()
        self.render_tasks()

    def _on_delete(self, task_id):
        task = next((t for t in self.data["tasks"][self.q_key] if t["id"] == task_id), None)
        if task:
            self.data["tasks"][self.q_key] = [
                t for t in self.data["tasks"][self.q_key] if t["id"] != task_id
            ]
            self.app._undo_stack.append({"type": "delete", "q_key": self.q_key, "task": task})
            self.app._update_undo_icon()
            self.app.save()
            self.render_tasks()
            self._update_count()

    def _on_edit(self, task):
        self.app._show_edit_dialog(task, self.q_key)

    def _update_count(self):
        total = sum(
            1 for t in self.data["tasks"].get(self.q_key, []) if not t.get("done")
        )
        self.count_label.setText(str(total))

    # ─── UI 构建 ───────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_header(layout)
        self._build_scroll_area(layout)
        self._apply_style()

    def _build_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(
            f"background:{self.cfg['header_bg']};"
            f"border-bottom:1px solid {self.cfg['border']};"
        )
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 4)

        title_row = QHBoxLayout()
        title_label = QLabel(self.cfg["title"])
        title_label.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        title_label.setStyleSheet(
            f"color:{self.cfg['header_fg']}; background:transparent; border:none;"
        )
        title_row.addWidget(title_label)

        self.count_label = QLabel()
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet(
            f"color:#FFFFFF; background:{self.cfg['header_fg']}; "
            f"font-size:14px; font-weight:bold; padding:0px 6px;"
        )
        self.count_label.setFixedHeight(20)
        title_row.addWidget(self.count_label)
        title_row.addStretch()
        h_layout.addLayout(title_row)

        parent_layout.addWidget(header)

    def _build_scroll_area(self, parent_layout):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            f'QScrollArea {{ background: {self.cfg["body_bg"]}; border: none; }}\n'
            "QScrollBar:vertical { background: transparent; width: 6px; }\n"
            "QScrollBar::handle { background: #CBD5E1; border-radius: 3px; }\n"
            "QScrollBar::add-line, QScrollBar::sub-line { height: 0; }"
        )

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(6, 6, 6, 6)
        self.task_layout.setSpacing(6)
        self.task_layout.addStretch()

        self.scroll.setWidget(self.task_container)
        self.scroll.viewport().installEventFilter(self)
        parent_layout.addWidget(self.scroll)

    def _apply_style(self):
        self.setStyleSheet(
            f"background:{self.cfg['body_bg']};"
            f"border:1px solid {self.cfg['border']};"
        )

    # ─── 拖拽事件 ──────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport() and event.type() == QEvent.Type.MouseButtonDblClick:
            self.app._show_add_dialog(self.cfg["title"])
            return True
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat(TaskCard.MIME_TYPE):
            try:
                raw = bytes(mime.data(TaskCard.MIME_TYPE)).decode("utf-8")
                src_key = raw.split(":")[0]
                if src_key != self.q_key:
                    self._set_highlight(True)
                    event.acceptProposedAction()
                    return
            except Exception:
                pass
        event.ignore()

    def dragLeaveEvent(self, event):
        self._set_highlight(False)

    def dropEvent(self, event):
        self._set_highlight(False)
        mime = event.mimeData()
        if mime.hasFormat(TaskCard.MIME_TYPE):
            try:
                raw = bytes(mime.data(TaskCard.MIME_TYPE)).decode("utf-8")
                src_key, task_id = raw.split(":")
                if src_key != self.q_key:
                    self.app._move_task(src_key, self.q_key, task_id)
                    event.acceptProposedAction()
                    return
            except Exception:
                pass
        event.ignore()

    def _set_highlight(self, on):
        self._highlighted = on
        if on:
            self.setStyleSheet(
                f"background:{self.cfg['body_bg']};"
                f"border:2px solid #3B82F6;"
            )
        else:
            self._apply_style()
        self.app._on_drag_target_changed(self.q_key if on else None)
