# -*- coding: utf-8 -*-
"""MainWindow：主窗口与工具栏"""

import os
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import QByteArray, QRect, QSize, Qt, Slot
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QCheckBox, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QStyle, QVBoxLayout, QWidget, QMessageBox,
)

from constants import (
    BG_PAGE,
    BG_TOOLBAR,
    QUADS,
    TEXT_MAIN,
    TEXT_SUB,
    get_font_family,
    set_font_family as _set_font_family,
)
from data import load_data, save_data
from dialogs import AddTaskDialog, EditTaskDialog, SettingsDialog
from quadrant_panel import QuadrantPanel

if TYPE_CHECKING:
    from quadrant_panel import QuadrantPanel


class UndoAction:
    """撤销动作类型封装"""
    DELETE = "delete"
    TOGGLE = "toggle"
    EDIT = "edit"
    CLEAR_DONE = "clear_done"
    CLEAR_ALL = "clear_all"
    MOVE = "move"
    ADD = "add"


class MainWindow(QMainWindow):
    """四象限任务板主窗口"""

    def __init__(self) -> None:
        super().__init__()
        self.data = load_data()
        self._drag_target_key: Optional[str] = None
        self._undo_stack: List[Dict[str, Any]] = []
        self._is_initializing = True

        self.setWindowTitle("四象限任务板")
        self._set_window_icon()
        self.setMinimumSize(640, 600)
        self.setStyleSheet(f"background:{BG_PAGE};")

        saved_font = self.data.get("font_family", "Microsoft YaHei")
        _set_font_family(saved_font)

        geo = self.data.get("geometry")
        if geo:
            geom_bytes = QByteArray.fromBase64(geo.encode("ascii"))
            self.restoreGeometry(geom_bytes)
        else:
            self.resize(1280, 820)

        self.show_done_cb = QCheckBox()
        self.show_done_cb.setChecked(self.data.get("show_done", True))
        self.show_done_cb.stateChanged.connect(self._on_show_done_changed)
        self._build_toolbar()
        self._build_board()
        self._apply_show_done_state()
        self._update_show_done_icon()
        self._update_undo_icon()
        self._is_initializing = False

    def save(self) -> None:
        """保存数据到磁盘"""
        save_data(self.data)

    # ─── 撤销系统（公开接口，供 QuadrantPanel 调用）───────────────────────────

    def push_undo(self, action_type: str, **kwargs) -> None:
        """添加撤销动作到栈中（公开接口）"""
        action = {"type": action_type, **kwargs}
        self._undo_stack.append(action)
        self._update_undo_icon()

    def find_task(self, q_key: str, task_id: str) -> Optional[Dict[str, Any]]:
        """根据象限 key 和任务 ID 查找任务"""
        return next((t for t in self.data["tasks"].get(q_key, []) if t["id"] == task_id), None)

    @Slot()
    def _undo(self) -> None:
        """执行撤销操作"""
        if not self._undo_stack:
            return
        action = self._undo_stack.pop()
        action_type = action["type"]

        if action_type == UndoAction.DELETE:
            q_key = action["q_key"]
            task = action["task"]
            self.data["tasks"][q_key].append(task)
            self.panels[q_key].render_tasks()
            self.panels[q_key].update_count()
            self.save()

        elif action_type == UndoAction.TOGGLE:
            q_key = action["q_key"]
            task_id = action["task_id"]
            task = self.find_task(q_key, task_id)
            if task:
                task["done"] = action["old_state"]
                self.panels[q_key].render_tasks()
                self.panels[q_key].update_count()
                self.save()

        elif action_type == UndoAction.EDIT:
            q_key = action["q_key"]
            task_id = action["task_id"]
            task = self.find_task(q_key, task_id)
            if task:
                task["text"] = action["old_text"]
                task["deadline"] = action["old_deadline"]
                self.panels[q_key].render_tasks()
                self.save()

        elif action_type == UndoAction.CLEAR_DONE:
            q_key = action["q_key"]
            self.data["tasks"][q_key].extend(action["tasks"])
            self.panels[q_key].render_tasks()
            self.panels[q_key].update_count()
            self.save()

        elif action_type == UndoAction.CLEAR_ALL:
            for q_key, tasks in action["tasks"].items():
                self.data["tasks"][q_key].extend(tasks)
            for q_key in action["tasks"].keys():
                self.panels[q_key].render_tasks()
                self.panels[q_key].update_count()
            self.save()

        elif action_type == UndoAction.MOVE:
            task = action["task"]
            from_q_key = action["from_q_key"]
            to_q_key = action["to_q_key"]
            self.data["tasks"][to_q_key] = [t for t in self.data["tasks"][to_q_key] if t["id"] != task["id"]]
            self.data["tasks"][from_q_key].append(task)
            self.panels[from_q_key].render_tasks()
            self.panels[from_q_key].update_count()
            self.panels[to_q_key].render_tasks()
            self.panels[to_q_key].update_count()
            self.save()

        elif action_type == UndoAction.ADD:
            q_key = action["q_key"]
            task_id = action["task_id"]
            self.data["tasks"][q_key] = [t for t in self.data["tasks"][q_key] if t["id"] != task_id]
            self.panels[q_key].render_tasks()
            self.panels[q_key].update_count()
            self.save()

        self._update_undo_icon()

    def _update_undo_icon(self) -> None:
        """更新撤销按钮图标状态"""
        has_undo = len(self._undo_stack) > 0
        icon_file = "undo.svg" if has_undo else "undo2.svg"
        self._undo_wrapper._btn.setIcon(self._svg_icon(icon_file, 36))

    # ─── DPI 自适应工具方法 ────────────────────────────────────────────────────

    def _logical_to_physical(self, logical: int) -> int:
        """将逻辑像素转换为物理像素（考虑 DPI 缩放）"""
        return int(logical * self.devicePixelRatio())

    def _px(self, logical: int) -> int:
        """简化的物理像素转换"""
        return self._logical_to_physical(logical)

    # ─── 窗口图标 ──────────────────────────────────────────────────────────────

    def _set_window_icon(self) -> None:
        """设置窗口图标（支持 HiDPI）"""
        if getattr(sys, 'frozen', False):
            _base_dir = sys._MEIPASS
        else:
            _base_dir = os.path.dirname(__file__)
        icon_path = os.path.join(_base_dir, "source", "icon.svg")
        if os.path.exists(icon_path):
            renderer = QSvgRenderer(icon_path)

            icon = QIcon()

            # 1x 版本: 256x256, dpr=1.0
            pixmap_1x = QPixmap(256, 256)
            pixmap_1x.fill(Qt.transparent)
            p1 = QPainter(pixmap_1x)
            p1.setRenderHint(QPainter.Antialiasing)
            renderer.render(p1)
            p1.end()
            pixmap_1x.setDevicePixelRatio(1.0)
            icon.addPixmap(pixmap_1x, QIcon.Normal, QIcon.On)

            # 2x 版本: 512x512, dpr=2.0
            pixmap_2x = QPixmap(512, 512)
            pixmap_2x.fill(Qt.transparent)
            p2 = QPainter(pixmap_2x)
            p2.setRenderHint(QPainter.Antialiasing)
            renderer.render(p2)
            p2.end()
            pixmap_2x.setDevicePixelRatio(2.0)
            icon.addPixmap(pixmap_2x, QIcon.Normal, QIcon.On)

            self.setWindowIcon(icon)

    def _svg_icon(self, filename: str, logical_size: int = 20) -> QIcon:
        """从 SVG 文件加载图标（支持 HiDPI）

        Args:
            filename: SVG 文件名
            logical_size: 逻辑像素大小（不考虑 DPI 缩放）

        Returns:
            QIcon，根据 devicePixelRatio 自动适配
        """
        if getattr(sys, 'frozen', False):
            _base_dir = sys._MEIPASS
        else:
            _base_dir = os.path.dirname(__file__)
        path = os.path.join(_base_dir, "source", filename)
        if os.path.exists(path):
            renderer = QSvgRenderer(path)
            if renderer.isValid():
                icon = QIcon()

                # 1x 版本：dpr=1.0
                pixmap_1x = QPixmap(logical_size, logical_size)
                pixmap_1x.fill(Qt.transparent)
                p1 = QPainter(pixmap_1x)
                p1.setRenderHint(QPainter.Antialiasing)
                p1.setRenderHint(QPainter.SmoothPixmapTransform)
                renderer.render(p1, QRect(0, 0, logical_size, logical_size))
                p1.end()
                pixmap_1x.setDevicePixelRatio(1.0)
                icon.addPixmap(pixmap_1x, QIcon.Normal, QIcon.On)

                # 2x 版本：dpr=2.0（无论当前 DPI 是否为 2.0 都添加，确保清晰）
                pixmap_2x = QPixmap(logical_size * 2, logical_size * 2)
                pixmap_2x.fill(Qt.transparent)
                p2 = QPainter(pixmap_2x)
                p2.setRenderHint(QPainter.Antialiasing)
                p2.setRenderHint(QPainter.SmoothPixmapTransform)
                renderer.render(p2, QRect(0, 0, logical_size * 2, logical_size * 2))
                p2.end()
                pixmap_2x.setDevicePixelRatio(2.0)
                icon.addPixmap(pixmap_2x, QIcon.Normal, QIcon.On)

                # 如果当前 DPI 是其他值（如 1.5, 1.75），也添加对应版本
                scale = self.devicePixelRatio()
                if scale != 1.0 and scale != 2.0:
                    physical_size = int(logical_size * scale)
                    pixmap_scale = QPixmap(physical_size, physical_size)
                    pixmap_scale.fill(Qt.transparent)
                    p_scale = QPainter(pixmap_scale)
                    p_scale.setRenderHint(QPainter.Antialiasing)
                    p_scale.setRenderHint(QPainter.SmoothPixmapTransform)
                    renderer.render(p_scale, QRect(0, 0, physical_size, physical_size))
                    p_scale.end()
                    pixmap_scale.setDevicePixelRatio(scale)
                    icon.addPixmap(pixmap_scale, QIcon.Normal, QIcon.On)

                return icon
        return QIcon()

    # ─── 工具栏 ────────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        """构建工具栏"""
        toolbar = QWidget()
        toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(
            f"background:{BG_TOOLBAR}; border-bottom: 1px solid #E2E8F0;"
        )
        self.setMenuWidget(toolbar)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 0, 16, 0)

        layout.addLayout(self._build_title_section())
        layout.addStretch()
        layout.addLayout(self._build_font_controls())
        layout.addSpacing(10)

        self._undo_wrapper = self._create_toolbar_icon_btn(
            "undo.svg", "撤销", self._undo
        )
        layout.addWidget(self._undo_wrapper)

        self._show_done_wrapper = self._create_toolbar_toggle_btn(
            "fin.svg", "fin2.svg",
            "显示已完成",
            self.show_done_cb.isChecked(),
            lambda: self.show_done_cb.toggle()
        )
        self.show_done_cb.stateChanged.connect(self._update_show_done_icon)
        layout.addWidget(self._show_done_wrapper)

        layout.addWidget(self._create_toolbar_icon_btn("setting.svg", "设置", self._show_settings))
        layout.addWidget(self._create_toolbar_icon_btn("delfin.svg", "清空已完成", self._clear_done))
        layout.addWidget(self._create_toolbar_icon_btn("delall.svg", "清空全部", self._clear_all))
        layout.addWidget(self._create_toolbar_icon_btn("add.svg", "添加任务", self._show_add_dialog))

    def _build_title_section(self) -> QVBoxLayout:
        """构建标题区域"""
        title_col = QVBoxLayout()
        main_t = QLabel("四象限任务板")
        main_t.setFont(QFont(get_font_family(), 16, QFont.Bold))
        main_t.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; border:none;")
        title_col.addWidget(main_t)
        sub_t = QLabel("艾森豪威尔矩阵")
        sub_t.setFont(QFont(get_font_family(), 10))
        sub_t.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        title_col.addWidget(sub_t)
        return title_col

    def _create_toolbar_icon_btn(
        self,
        icon_file: str,
        label_text: str,
        callback,
    ) -> QWidget:
        """创建工具栏图标按钮（DPI 自适应）"""
        btn = QPushButton()
        # 使用固定的逻辑尺寸，setIconSize 接受的是逻辑像素
        logical_icon_size = 36
        btn.setIcon(self._svg_icon(icon_file, logical_icon_size))
        btn.setIconSize(QSize(self._px(36), self._px(36)))
        btn.setFixedSize(
            self._px(60),  # 逻辑 60px
            self._px(44)   # 逻辑 44px
        )
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        btn.clicked.connect(callback)

        wrapper = QWidget()
        vbox = QVBoxLayout(wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.addWidget(btn)
        lbl = QLabel(label_text)
        lbl.setFont(QFont(get_font_family(), 8))
        lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        lbl.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        lbl.setFixedHeight(14)
        vbox.addWidget(lbl)
        wrapper.setFixedSize(self._px(60), self._px(62))
        wrapper._btn = btn
        return wrapper

    def _create_toolbar_toggle_btn(
        self,
        icon_off: str,
        icon_on: str,
        label_text: str,
        is_on: bool,
        callback,
    ) -> QWidget:
        """创建工具栏切换图标按钮（DPI 自适应）"""
        btn = QPushButton()
        icon_file = icon_on if is_on else icon_off
        logical_icon_size = 36
        btn.setIcon(self._svg_icon(icon_file, logical_icon_size))
        btn.setIconSize(QSize(self._px(36), self._px(36)))
        btn.setFixedSize(
            self._px(60),
            self._px(44)
        )
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        btn.clicked.connect(callback)

        wrapper = QWidget()
        vbox = QVBoxLayout(wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.addWidget(btn)
        lbl = QLabel(label_text)
        lbl.setFont(QFont(get_font_family(), 8))
        lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        lbl.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        lbl.setFixedHeight(14)
        vbox.addWidget(lbl)
        wrapper.setFixedSize(self._px(60), self._px(62))
        wrapper._btn = btn
        return wrapper

    def _update_show_done_icon(self) -> None:
        """更新显示已完成按钮的图标"""
        if self._is_initializing:
            return
        is_on = self.show_done_cb.isChecked()
        icon_file = "fin2.svg" if is_on else "fin.svg"
        self._show_done_wrapper._btn.setIcon(self._svg_icon(icon_file, 36))

    @Slot(int)
    def _on_show_done_changed(self, state: int) -> None:
        """显示已完成复选框状态改变处理"""
        show = self.show_done_cb.isChecked()
        self.data["show_done"] = show
        for panel in self.panels.values():
            panel.show_done = show
            panel.render_tasks()
        self.save()
        self._update_show_done_icon()

    def _build_font_controls(self) -> QHBoxLayout:
        """构建字体大小控制组件（DPI 自适应）"""
        box = QHBoxLayout()

        minus = QPushButton("A−")
        minus.setFont(QFont(get_font_family(), 10))
        minus.setFixedSize(
            self._px(36),
            self._px(28)
        )
        minus.setCursor(Qt.PointingHandCursor)
        minus.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; border: none; border-radius: 4px; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        minus.clicked.connect(lambda: self._change_font(-1))
        box.addWidget(minus)

        self.font_label = QLabel(str(self.data["font_size"]))
        self.font_label.setFont(QFont(get_font_family(), 11, QFont.Bold))
        self.font_label.setAlignment(Qt.AlignCenter)
        self.font_label.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; border:none;")
        self.font_label.setFixedWidth(24)
        box.addWidget(self.font_label)

        plus = QPushButton("A＋")
        plus.setFont(QFont(get_font_family(), 10))
        plus.setFixedSize(
            self._px(36),
            self._px(28)
        )
        plus.setCursor(Qt.PointingHandCursor)
        plus.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; border: none; border-radius: 4px; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        plus.clicked.connect(lambda: self._change_font(1))
        box.addWidget(plus)

        return box

    def _apply_show_done_state(self) -> None:
        """应用显示已完成的初始状态"""
        show = self.show_done_cb.isChecked()
        for panel in self.panels.values():
            panel.show_done = show
            panel.render_tasks()

    def _change_font(self, delta: int) -> None:
        """调整字体大小"""
        size = max(10, min(24, self.data["font_size"] + delta))
        self.data["font_size"] = size
        self.font_label.setText(str(size))
        for panel in self.panels.values():
            panel.render_tasks()
        self.save()

    # ─── 四象限面板 ─────────────────────────────────────────────────────────────

    def _build_board(self) -> None:
        """构建四象限面板"""
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background:{BG_PAGE};")

        self._board_layout = QGridLayout(central)
        self._board_layout.setContentsMargins(16, 12, 16, 12)
        self._board_layout.setSpacing(8)
        self._board_layout.setColumnStretch(0, 1)
        self._board_layout.setColumnStretch(1, 1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        self.panels: Dict[str, "QuadrantPanel"] = {}
        for i, cfg in enumerate(QUADS):
            r, c = positions[i]
            panel = QuadrantPanel(cfg, self.data, self)
            panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self._board_layout.addWidget(panel, r, c)
            self.panels[cfg["key"]] = panel
            panel.render_tasks()

    # ─── 对话框 ────────────────────────────────────────────────────────────────

    def show_add_dialog(self, default_quad: Optional[str] = None) -> None:
        """显示添加任务对话框（公开接口）"""
        quad_titles = [q["title"] for q in QUADS]
        quad_keys = [q["key"] for q in QUADS]
        default = default_quad or quad_titles[0]
        dialog = AddTaskDialog(quad_keys, quad_titles, default,
                               self.data["font_size"], self)
        if dialog.exec() == AddTaskDialog.Accepted:
            result = dialog.get_result()
            if result:
                task, q_key = result
                self._add_task(q_key, task)

    # 别名，保持向后兼容
    _show_add_dialog = show_add_dialog

    def show_edit_dialog(self, task: Dict[str, Any], q_key: str) -> None:
        """显示编辑任务对话框（公开接口）"""
        quad_titles = [q["title"] for q in QUADS]
        quad_keys = [q["key"] for q in QUADS]
        old_text = task["text"]
        old_deadline = task.get("deadline", "")
        dialog = EditTaskDialog(task, quad_keys, quad_titles, q_key,
                                self.data["font_size"], self)
        if dialog.exec() == EditTaskDialog.Accepted:
            result = dialog.get_result()
            if result:
                new_text, new_dl, new_q_key = result
                if new_text != old_text or new_dl != old_deadline or new_q_key != q_key:
                    self.push_undo(
                        UndoAction.EDIT,
                        q_key=q_key,
                        task_id=task["id"],
                        old_text=old_text,
                        old_deadline=old_deadline
                    )
                task["text"] = new_text
                task["deadline"] = new_dl
                if new_q_key != q_key:
                    self.data["tasks"][q_key] = [
                        t for t in self.data["tasks"][q_key] if t["id"] != task["id"]
                    ]
                    if new_q_key not in self.data["tasks"]:
                        self.data["tasks"][new_q_key] = []
                    self.data["tasks"][new_q_key].append(task)
                self.save()
                for key in set([q_key, new_q_key]):
                    if key in self.panels:
                        self.panels[key].render_tasks()

    # 别名，保持向后兼容
    _show_edit_dialog = show_edit_dialog

    def _add_task(self, q_key: str, task: Dict[str, Any]) -> None:
        """添加任务到指定象限"""
        if q_key not in self.data["tasks"]:
            self.data["tasks"][q_key] = []
        self.data["tasks"][q_key].append(task)
        self.push_undo(UndoAction.ADD, q_key=q_key, task_id=task["id"])
        self.save()
        self.panels[q_key].render_tasks()

    def _show_edit_dialog(self, task: Dict[str, Any], q_key: str) -> None:
        """显示编辑任务对话框"""
        quad_titles = [q["title"] for q in QUADS]
        quad_keys = [q["key"] for q in QUADS]
        old_text = task["text"]
        old_deadline = task.get("deadline", "")
        dialog = EditTaskDialog(task, quad_keys, quad_titles, q_key,
                                self.data["font_size"], self)
        if dialog.exec() == EditTaskDialog.Accepted:
            result = dialog.get_result()
            if result:
                new_text, new_dl, new_q_key = result
                if new_text != old_text or new_dl != old_deadline or new_q_key != q_key:
                    self.push_undo(
                        UndoAction.EDIT,
                        q_key=q_key,
                        task_id=task["id"],
                        old_text=old_text,
                        old_deadline=old_deadline
                    )
                task["text"] = new_text
                task["deadline"] = new_dl
                if new_q_key != q_key:
                    self.data["tasks"][q_key] = [
                        t for t in self.data["tasks"][q_key] if t["id"] != task["id"]
                    ]
                    if new_q_key not in self.data["tasks"]:
                        self.data["tasks"][new_q_key] = []
                    self.data["tasks"][new_q_key].append(task)
                self.save()
                for key in set([q_key, new_q_key]):
                    if key in self.panels:
                        self.panels[key].render_tasks()

    def move_task(self, src_key: str, tgt_key: str, task_id: str) -> None:
        """移动任务从一个象限到另一个象限（公开接口）"""
        src_tasks = self.data["tasks"].get(src_key, [])
        task_data = None
        for t in src_tasks:
            if t["id"] == task_id:
                task_data = t
                break
        if not task_data:
            return

        self.push_undo(
            UndoAction.MOVE,
            task=task_data,
            from_q_key=src_key,
            to_q_key=tgt_key
        )
        self.data["tasks"][src_key] = [t for t in src_tasks if t["id"] != task_id]
        if tgt_key not in self.data["tasks"]:
            self.data["tasks"][tgt_key] = []
        self.data["tasks"][tgt_key].append(task_data)
        self.save()

        self.panels[src_key].render_tasks()
        self.panels[tgt_key].render_tasks()

    def on_drag_target_changed(self, quad_key: Optional[str]) -> None:
        """拖拽目标象限改变回调（公开接口）"""
        self._drag_target_key = quad_key

    @Slot()
    def _clear_done(self) -> None:
        """清空所有象限的已完成任务"""
        for panel in self.panels.values():
            done_tasks = [t for t in self.data["tasks"][panel.q_key] if t.get("done")]
            if done_tasks:
                self.push_undo(
                    UndoAction.CLEAR_DONE,
                    q_key=panel.q_key,
                    tasks=done_tasks
                )
            panel.clear_done()

    @Slot()
    def _clear_all(self) -> None:
        """清空所有象限的所有任务"""
        reply = QMessageBox.question(
            self, "清空全部",
            "确定要清除所有任务吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            all_tasks = {}
            for panel in self.panels.values():
                if self.data["tasks"][panel.q_key]:
                    all_tasks[panel.q_key] = list(self.data["tasks"][panel.q_key])
            if all_tasks:
                self.push_undo(UndoAction.CLEAR_ALL, tasks=all_tasks)
            for panel in self.panels.values():
                panel.clear_all()

    def _on_font_size_change(self, size: int) -> None:
        """设置对话框字体大小变化回调"""
        self.data["font_size"] = size
        self.font_label.setText(str(size))
        for panel in self.panels.values():
            panel.render_tasks()

    def _show_settings(self) -> None:
        """显示设置对话框"""
        dialog = SettingsDialog(
            self.data,
            self.data["font_size"],
            on_font_change=self._on_font_preview,
            on_font_size_change=self._on_font_size_change,
            parent=self
        )
        if dialog.exec() == SettingsDialog.Accepted:
            self.data["deadline_colors"] = dialog.get_colors()
            self.data["deadline_thresholds"] = dialog.get_thresholds()
            new_font = dialog.get_font_family()
            self.data["font_family"] = new_font
            _set_font_family(new_font)
            self.save()
            self._rebuild_ui()
            for panel in self.panels.values():
                panel.render_tasks()
        else:
            _set_font_family(self.data["font_family"])
            self._rebuild_ui()

    def _on_font_preview(self, font_family: str) -> None:
        """字体预览回调"""
        _set_font_family(font_family)
        self._rebuild_ui()
        for panel in self.panels.values():
            panel.render_tasks()

    def _rebuild_ui(self) -> None:
        """重新构建 UI 字体"""
        toolbar = self.menuWidget()
        if toolbar:
            self._update_widget_fonts(toolbar)

    def _update_widget_fonts(self, widget: QWidget) -> None:
        """递归更新 widget 及其子组件的字体（修复 if/elif bug）"""
        for child in widget.children():
            if isinstance(child, QLabel):
                cur = child.font()
                size = cur.pointSize()
                if size > 0:
                    child.setFont(QFont(get_font_family(), size, cur.weight(), cur.italic()))
            elif isinstance(child, QPushButton):
                cur = child.font()
                size = cur.pointSize()
                if size > 0:
                    child.setFont(QFont(get_font_family(), size, cur.weight(), cur.italic()))
            elif isinstance(child, QWidget):
                self._update_widget_fonts(child)

    # ─── 窗口事件 ──────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """窗口关闭时保存状态"""
        geom_bytes = self.saveGeometry()
        self.data["geometry"] = bytes(geom_bytes.toBase64()).decode("ascii")
        self.save()
        event.accept()