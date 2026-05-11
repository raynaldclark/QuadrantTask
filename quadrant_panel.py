# -*- coding: utf-8 -*-
"""QuadrantPanel：可接受拖拽的象限面板"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtCore import QEvent, QObject, Qt, Slot, QPoint, QTimer
from PySide6.QtGui import QFont, QAction, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QSizePolicy, QVBoxLayout, QWidget, QScrollArea,
    QPushButton, QWidgetAction
)

from constants import get_font_family
from task_card import TaskCard

if TYPE_CHECKING:
    from main_window import MainWindow


class QuadrantPanel(QFrame):
    """单个象限区域：显示任务列表 + 接受拖拽放下。"""

    def __init__(
        self,
        cfg: Dict[str, str],
        data: Dict[str, Any],
        main_window: "MainWindow",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.data = data
        self.main_window = main_window
        self.q_key = cfg["key"]
        self.show_done = False
        self._highlighted = False

        self._setup_ui()

    def render_tasks(self) -> None:
        """重新渲染任务卡片列表。"""
        while self.task_layout.count() > 1:
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self.data["tasks"].get(self.q_key, [])
        fs = self.data["font_size"]
        visible = [t for t in tasks if not t.get("done") or self.show_done]

        for task in visible:
            card = TaskCard(
                task=task,
                quad_cfg=self.cfg,
                font_size=fs,
                deadline_colors=self.data.get("deadline_colors", {}),
                deadline_thresholds=self.data.get("deadline_thresholds", {"urgent": 3, "short_term": 7, "medium_term": 14, "long_term": 999}),
                on_toggle=self._on_toggle,
                on_delete=self._on_delete,
                on_edit=self._on_edit,
            )
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            self.task_layout.insertWidget(self.task_layout.count() - 1, card)

        self.update_count()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._update_card_widths)

    def reload_tasks(self) -> None:
        """从外部重新加载数据后刷新任务列表"""
        self.render_tasks()

    def _update_card_widths(self) -> None:
        scroll_width = self.scroll.viewport().width()
        if scroll_width > 50:
            new_width = scroll_width - 12
            for i in range(self.task_layout.count() - 1):
                item = self.task_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), TaskCard):
                    w = item.widget()
                    w.setFixedSize(new_width, w.heightForWidth(new_width))
            self.task_layout.activate()
            self.task_container.updateGeometry()
            self.scroll.viewport().update()

    def clear_done(self) -> None:
        """清空已完成任务"""
        self.data["tasks"][self.q_key] = [
            t for t in self.data["tasks"][self.q_key] if not t.get("done")
        ]
        self.main_window.save()
        self.render_tasks()

    def clear_all(self) -> None:
        """清空所有任务"""
        self.data["tasks"][self.q_key] = []
        self.main_window.save()
        self.render_tasks()

    def update_count(self) -> None:
        """更新任务计数显示"""
        total = sum(
            1 for t in self.data["tasks"].get(self.q_key, []) if not t.get("done")
        )
        self.count_label.setText(str(total))

    @Slot()
    def _on_toggle(self, task: Dict[str, Any]) -> None:
        """任务完成状态切换处理（通过公开接口操作撤销）"""
        self.main_window.push_undo(
            "toggle",
            q_key=self.q_key,
            task_id=task["id"],
            old_state=not task.get("done", False)
        )
        self.main_window.save()
        self.render_tasks()

    @Slot()
    def _on_delete(self, task_id: str) -> None:
        """删除任务处理（通过公开接口操作撤销）"""
        task = self.main_window.find_task(self.q_key, task_id)
        if task:
            self.data["tasks"][self.q_key] = [
                t for t in self.data["tasks"][self.q_key] if t["id"] != task_id
            ]
            self.main_window.push_undo("delete", q_key=self.q_key, task=task)
            self.main_window.save()
            self.render_tasks()
            self.update_count()

    @Slot()
    def _on_edit(self, task: Dict[str, Any]) -> None:
        """编辑任务处理"""
        self.main_window.show_edit_dialog(task, self.q_key)

    def _setup_ui(self) -> None:
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_header(layout)
        self._build_scroll_area(layout)
        self._apply_style()

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
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
        title_label.setFont(QFont(get_font_family(), 14, QFont.Bold))
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

    def _build_scroll_area(self, parent_layout: QVBoxLayout) -> None:
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
        self._viewport_size = self.scroll.viewport().size()
        parent_layout.addWidget(self.scroll)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"background:{self.cfg['body_bg']};"
            f"border:1px solid {self.cfg['border']};"
        )

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self.scroll.viewport():
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.main_window.show_add_dialog(self.cfg["title"])
                return True
            elif event.type() == QEvent.Type.ContextMenu:
                self._show_context_menu(event.globalPos())
                return True
            elif event.type() == QEvent.Type.Resize:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self._update_card_widths)
                return False
        return super().eventFilter(obj, event)

    def _show_context_menu(self, global_pos: QPoint) -> None:
        """显示右键菜单，字体调整时保持菜单不消失"""
        menu = self._build_context_menu()

        def on_triggered(action):
            # QWidgetAction（字体按钮）触发后标记 reopen
            if isinstance(action, QWidgetAction):
                self._font_menu_reopen = True

        def on_about_to_hide():
            if getattr(self, '_font_menu_reopen', False):
                self._font_menu_reopen = False
                QTimer.singleShot(0, lambda: self._show_context_menu(global_pos))

        menu.triggered.connect(on_triggered)
        menu.aboutToHide.connect(on_about_to_hide)
        menu.popup(global_pos)

    def _build_context_menu(self) -> QMenu:
        """构建右键菜单（与工具栏功能一致）"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 28px 6px 12px;
                border-radius: 6px;
                color: #1E293B;
                font-size: 15px;
            }
            QMenu::item:selected {
                background: #F1F5F9;
            }
            QMenu::separator {
                height: 1px;
                background: #E2E8F0;
                margin: 6px 12px;
            }
        """)

        # 获取图标的辅助方法
        def get_icon(filename: str) -> QIcon:
            return self.main_window._svg_icon(filename, 32)

        # 1. 添加任务
        action_add = QAction(get_icon("add.svg"), "添加任务", self)
        action_add.triggered.connect(lambda: self.main_window.show_add_dialog(self.cfg["title"]))
        menu.addAction(action_add)

        menu.addSeparator()

        # 2. 撤销（根据撤销栈状态决定图标）
        has_undo = len(self.main_window._undo_stack) > 0
        undo_icon_file = "undo.svg" if has_undo else "undo2.svg"
        action_undo = QAction(get_icon(undo_icon_file), "撤销", self)
        action_undo.setEnabled(has_undo)
        action_undo.triggered.connect(self.main_window._undo)
        menu.addAction(action_undo)

        # 3. 显示已完成（切换状态）
        show_done = self.main_window.show_done_cb.isChecked()
        show_done_icon = "fin2.svg" if show_done else "fin.svg"
        action_show_done = QAction(get_icon(show_done_icon), "显示已完成" if show_done else "隐藏已完成", self)
        action_show_done.triggered.connect(self.main_window.show_done_cb.toggle)
        menu.addAction(action_show_done)

        menu.addSeparator()

        # 4. 清空已完成
        action_clear_done = QAction(get_icon("delfin.svg"), "清空已完成", self)
        action_clear_done.triggered.connect(self.main_window._clear_done)
        menu.addAction(action_clear_done)

        # 5. 清空全部
        action_clear_all = QAction(get_icon("delall.svg"), "清空全部", self)
        action_clear_all.triggered.connect(self.main_window._clear_all)
        menu.addAction(action_clear_all)

        menu.addSeparator()

        # 6. 字体大小调节（用 QWidgetAction 嵌入按钮，不触发菜单关闭）
        font_btns: list[QPushButton] = []

        def _refresh_font_btn_texts() -> None:
            """刷新所有字体按钮的显示字号"""
            new_size = self.main_window.data.get("font_size", 12)
            for b in font_btns:
                prefix = "A+" if b.text().startswith("A+") else "A-"
                b.setText(f"{prefix}  字体大小 ({new_size})")

        def make_font_btn(text, delta):
            btn = QPushButton(f"{text}  字体大小 ({self.main_window.data.get('font_size', 12)})")
            font_btns.append(btn)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none; border-radius: 4px;
                    color: #1E293B; font-size: 15px; text-align: left;
                    padding: 4px 8px;
                }
                QPushButton:hover { background: #F1F5F9; }
            """)
            btn.clicked.connect(lambda: (
                self.main_window._change_font(delta),
                _refresh_font_btn_texts(),
            ))
            return btn

        wa_up = QWidgetAction(menu)
        wa_up.setDefaultWidget(make_font_btn("A+", 1))
        menu.addAction(wa_up)

        wa_down = QWidgetAction(menu)
        wa_down.setDefaultWidget(make_font_btn("A-", -1))
        menu.addAction(wa_down)

        menu.addSeparator()

        # 8. 设置
        action_settings = QAction(get_icon("setting.svg"), "设置", self)
        action_settings.triggered.connect(self.main_window._show_settings)
        menu.addAction(action_settings)

        menu.addSeparator()

        # 9. 关闭程序
        action_close = QAction(get_icon("close.svg"), "关闭程序", self)
        action_close.triggered.connect(self.main_window.close)
        menu.addAction(action_close)

        return menu

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(TaskCard.MIME_TYPE):
            try:
                raw = bytes(mime.data(TaskCard.MIME_TYPE)).decode("utf-8")
                src_key, task_id = raw.split(":")
                self._drag_task_id = task_id
                self._src_key = src_key
                self._set_highlight(True)
                event.acceptProposedAction()
                return
            except Exception:
                pass
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(TaskCard.MIME_TYPE):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_highlight(False)

    def dropEvent(self, event) -> None:
        self._set_highlight(False)
        mime = event.mimeData()
        if mime.hasFormat(TaskCard.MIME_TYPE):
            try:
                raw = bytes(mime.data(TaskCard.MIME_TYPE)).decode("utf-8")
                src_key, task_id = raw.split(":")

                if src_key == self.q_key:
                    viewport_y = event.pos().y()
                    scroll_offset = self.scroll.verticalScrollBar().value()
                    DRAG_OFFSET = 60
                    local_y = viewport_y + scroll_offset - DRAG_OFFSET
                    drop_index = self._calculate_drop_index(local_y)
                    max_index = self.task_layout.count() - 1
                    drop_index = min(drop_index, max_index)
                    drop_index = max(drop_index, 0)
                    self.main_window.reorder_task(src_key, task_id, drop_index)
                else:
                    viewport_y = event.pos().y()
                    scroll_offset = self.scroll.verticalScrollBar().value()
                    DRAG_OFFSET = 60
                    local_y = viewport_y + scroll_offset - DRAG_OFFSET
                    drop_index = self._calculate_drop_index(local_y)
                    max_index = self.task_layout.count() - 1
                    drop_index = min(drop_index, max_index)
                    drop_index = max(drop_index, 0)
                    self.main_window.move_task_to_index(src_key, self.q_key, task_id, drop_index)
                event.acceptProposedAction()
                return
            except Exception:
                pass
        event.ignore()

    def _calculate_drop_index(self, y: int) -> int:
        index = 0
        count = self.task_layout.count()
        for i in range(count - 1):
            item = self.task_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                mid_y = widget.y() + widget.height() // 2
                if y > mid_y:
                    index = i + 1
        return index

    def _set_highlight(self, on: bool) -> None:
        self._highlighted = on
        if on:
            self.setStyleSheet(
                f"background:{self.cfg['body_bg']};"
                f"border:2px solid #3B82F6;"
            )
        else:
            self._apply_style()
        self.main_window.on_drag_target_changed(self.q_key if on else None)