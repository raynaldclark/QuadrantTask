# -*- coding: utf-8 -*-
"""MainWindow：主窗口与工具栏"""

import os
import sys

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QCheckBox, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from constants import (
    BG_PAGE,
    BG_TOOLBAR,
    BTN_PRIMARY_BG,
    BTN_PRIMARY_FG,
    FONT_FAMILY,
    QUADS,
    TEXT_MAIN,
    TEXT_SUB,
)
from data import load_data, save_data
from dialogs import AddTaskDialog, EditTaskDialog, SettingsDialog
from quadrant_panel import QuadrantPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = load_data()
        self._drag_target_key = None

        self.setWindowTitle("四象限任务板")
        self._set_window_icon()
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background:{BG_PAGE};")

        geo = self.data.get("geometry")
        if geo:
            geom_bytes = QByteArray.fromBase64(geo.encode("ascii"))
            self.restoreGeometry(geom_bytes)
        else:
            self.resize(1280, 820)

        self.show_done_cb = QCheckBox()
        self.show_done_cb.setChecked(self.data.get("show_done", True))
        self.show_done_cb.stateChanged.connect(self._toggle_show_done)
        self._build_toolbar()
        self._build_board()

    def _set_window_icon(self):
        if getattr(sys, 'frozen', False):
            _BASE_DIR = sys._MEIPASS
        else:
            _BASE_DIR = os.path.dirname(__file__)
        icon_path = os.path.join(_BASE_DIR, "source", "icon.svg")
        if os.path.exists(icon_path):
            renderer = QSvgRenderer(icon_path)
            pixmap = QPixmap(256, 256)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.setWindowIcon(QIcon(pixmap))

    def _svg_icon(self, filename, size=20):
        if getattr(sys, 'frozen', False):
            _BASE_DIR = sys._MEIPASS
        else:
            _BASE_DIR = os.path.dirname(__file__)
        path = os.path.join(_BASE_DIR, "source", filename)
        if os.path.exists(path):
            renderer = QSvgRenderer(path)
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        return QIcon()

    # ─── 公开 API ──────────────────────────────────────────────────────────────

    def save(self):
        save_data(self.data)

    # ─── 工具栏 ────────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        toolbar = QWidget()
        toolbar.setFixedHeight(64)
        toolbar.setStyleSheet(
            f"background:{BG_TOOLBAR}; border-bottom: 1px solid #E2E8F0;"
        )
        self.setMenuWidget(toolbar)

        t = QHBoxLayout(toolbar)
        t.setContentsMargins(16, 0, 16, 0)

        # 左侧标题区
        title_col = QVBoxLayout()
        main_t = QLabel("四象限任务板")
        main_t.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        main_t.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; border:none;")
        title_col.addWidget(main_t)
        sub_t = QLabel("艾森豪威尔矩阵")
        sub_t.setFont(QFont(FONT_FAMILY, 10))
        sub_t.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        title_col.addWidget(sub_t)
        t.addLayout(title_col)

        t.addStretch()

        # 字号 A− / A＋（无文字标签）
        t.addLayout(self._build_font_controls())

        t.addSpacing(16)

        # 显示已完成
        show_done_btn = QPushButton()
        show_done_btn.setIcon(self._svg_icon("fin.svg", 56))
        show_done_btn.setToolTip("显示已完成")
        show_done_btn.setFixedSize(40, 36)
        show_done_btn.setCursor(Qt.PointingHandCursor)
        show_done_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background: #F1F5F9; }}
        """)
        show_done_btn.clicked.connect(lambda: self.show_done_cb.toggle())
        t.addWidget(show_done_btn)

        t.addSpacing(8)

        # 设置按钮
        settings_btn = QPushButton()
        settings_btn.setIcon(self._svg_icon("setting.svg", 56))
        settings_btn.setToolTip("设置")
        settings_btn.setFixedSize(40, 36)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        settings_btn.clicked.connect(self._show_settings)
        t.addWidget(settings_btn)

        t.addSpacing(8)

        # 清空按钮
        clear_done_btn = QPushButton()
        clear_done_btn.setIcon(self._svg_icon("delfin.svg", 56))
        clear_done_btn.setToolTip("清空已完成")
        clear_done_btn.setFixedSize(40, 36)
        clear_done_btn.setCursor(Qt.PointingHandCursor)
        clear_done_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        clear_done_btn.clicked.connect(self._clear_done)
        t.addWidget(clear_done_btn)

        clear_all_btn = QPushButton()
        clear_all_btn.setIcon(self._svg_icon("delall.svg", 56))
        clear_all_btn.setToolTip("清空全部")
        clear_all_btn.setFixedSize(40, 36)
        clear_all_btn.setCursor(Qt.PointingHandCursor)
        clear_all_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; border-radius: 4px; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        clear_all_btn.clicked.connect(self._clear_all)
        t.addWidget(clear_all_btn)

        t.addSpacing(16)

        # 添加按钮
        add_btn = QPushButton()
        add_btn.setIcon(self._svg_icon("add.svg", 56))
        add_btn.setToolTip("添加任务")
        add_btn.setFixedSize(40, 36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {BTN_PRIMARY_BG}; border: none; border-radius: 4px; }}
            QPushButton:hover {{ background: #334155; }}
        """)
        add_btn.clicked.connect(self._show_add_dialog)
        t.addWidget(add_btn)

    def _build_font_controls(self):
        box = QHBoxLayout()

        minus = QPushButton("A−")
        minus.setFont(QFont(FONT_FAMILY, 10))
        minus.setFixedSize(36, 28)
        minus.setCursor(Qt.PointingHandCursor)
        minus.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; border: none; border-radius: 4px; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        minus.clicked.connect(lambda: self._change_font(-1))
        box.addWidget(minus)

        self.font_label = QLabel(str(self.data["font_size"]))
        self.font_label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.font_label.setAlignment(Qt.AlignCenter)
        self.font_label.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; border:none;")
        self.font_label.setFixedWidth(24)
        box.addWidget(self.font_label)

        plus = QPushButton("A＋")
        plus.setFont(QFont(FONT_FAMILY, 10))
        plus.setFixedSize(36, 28)
        plus.setCursor(Qt.PointingHandCursor)
        plus.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; border: none; border-radius: 4px; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        plus.clicked.connect(lambda: self._change_font(1))
        box.addWidget(plus)

        return box

    def _toolbar_btn(self, text, danger=False):
        if danger:
            btn = QPushButton(text)
            btn.setFont(QFont(FONT_FAMILY, 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: #FFF0F0; color: #DC2626;
                              border: 1px solid #FECACA; border-radius: 6px; padding: 5px 10px; }}
                QPushButton:hover {{ background: #FEE2E2; }}
            """)
        else:
            btn = QPushButton(text)
            btn.setFont(QFont(FONT_FAMILY, 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {TEXT_SUB};
                              border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px 10px; }}
                QPushButton:hover {{ background: #F1F5F9; color: {TEXT_MAIN}; }}
            """)
        return btn

    # ─── 四象限面板 ─────────────────────────────────────────────────────────────

    def _build_board(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background:{BG_PAGE};")

        self._board_layout = QGridLayout(central)
        self._board_layout.setContentsMargins(16, 12, 16, 12)
        self._board_layout.setSpacing(8)
        self._board_layout.setColumnStretch(0, 1)
        self._board_layout.setColumnStretch(1, 1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        self.panels = {}
        for i, cfg in enumerate(QUADS):
            r, c = positions[i]
            panel = QuadrantPanel(cfg, self.data, self)
            panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self._board_layout.addWidget(panel, r, c)
            self.panels[cfg["key"]] = panel
            panel.render_tasks()

    # ─── 对话框 ────────────────────────────────────────────────────────────────

    def _show_add_dialog(self, default_quad=None):
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

    def _add_task(self, q_key, task):
        if q_key not in self.data["tasks"]:
            self.data["tasks"][q_key] = []
        self.data["tasks"][q_key].append(task)
        self.save()
        self.panels[q_key].render_tasks()

    def _show_edit_dialog(self, task, q_key):
        quad_titles = [q["title"] for q in QUADS]
        quad_keys = [q["key"] for q in QUADS]
        dialog = EditTaskDialog(task, quad_keys, quad_titles, q_key,
                                self.data["font_size"], self)
        if dialog.exec() == EditTaskDialog.Accepted:
            result = dialog.get_result()
            if result:
                new_text, new_dl, new_q_key = result
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

    def _move_task(self, src_key, tgt_key, task_id):
        src_tasks = self.data["tasks"].get(src_key, [])
        task_data = None
        for t in src_tasks:
            if t["id"] == task_id:
                task_data = t
                break
        if not task_data:
            return

        self.data["tasks"][src_key] = [t for t in src_tasks if t["id"] != task_id]
        if tgt_key not in self.data["tasks"]:
            self.data["tasks"][tgt_key] = []
        self.data["tasks"][tgt_key].append(task_data)
        self.save()

        self.panels[src_key].render_tasks()
        self.panels[tgt_key].render_tasks()

    def _on_drag_target_changed(self, quad_key):
        self._drag_target_key = quad_key

    def _change_font(self, delta):
        size = max(10, min(24, self.data["font_size"] + delta))
        self.data["font_size"] = size
        self.font_label.setText(str(size))
        for p in self.panels.values():
            p.render_tasks()
        self.save()

    def _toggle_show_done(self):
        show = self.show_done_cb.isChecked()
        for p in self.panels.values():
            p.show_done = show
            p.render_tasks()

    def _clear_done(self):
        for p in self.panels.values():
            p.clear_done()

    def _clear_all(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "清空全部",
            "确定要清除所有任务吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for p in self.panels.values():
                p.clear_all()

    def _show_settings(self):
        dialog = SettingsDialog(self.data, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.data["deadline_colors"] = dialog.get_colors()
            self.data["deadline_thresholds"] = dialog.get_thresholds()
            self.save()
            for p in self.panels.values():
                p.render_tasks()

    # ─── 窗口事件 ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        geom_bytes = self.saveGeometry()
        self.data["geometry"] = bytes(geom_bytes.toBase64()).decode("ascii")
        self.save()
        event.accept()
