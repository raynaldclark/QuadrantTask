# -*- coding: utf-8 -*-
"""对话框：AddTaskDialog / EditTaskDialog / SettingsDialog"""

import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QTextEdit, QLineEdit,
    QPushButton, QSpinBox, QColorDialog,
)

from constants import (
    BTN_PRIMARY_BG,
    BTN_PRIMARY_FG,
    FONT_FAMILY,
    TEXT_MAIN,
    TEXT_SUB,
    QUADS,
)


# ─── 通用 UI 工具 ─────────────────────────────────────────────────────────────

def _build_title_bar(title: str, parent: QDialog) -> QFrame:
    bar = QFrame(parent)
    bar.setStyleSheet(f"background:{BTN_PRIMARY_BG};")
    bar.setFixedHeight(44)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(16, 0, 12, 0)

    lbl = QLabel(title, bar)
    lbl.setFont(QFont(FONT_FAMILY, 15, QFont.Bold))
    lbl.setStyleSheet("color:#FFFFFF; background:transparent; border:none;")
    lay.addWidget(lbl)
    lay.addStretch()

    close_btn = QPushButton("✕", bar)
    close_btn.setStyleSheet(
        "QPushButton { background: transparent; color: #94A3B8; border: none; "
        "font-size: 16px; padding: 4px 8px; }"
        "QPushButton:hover { color: #FFFFFF; }"
    )
    close_btn.clicked.connect(parent.reject)
    lay.addWidget(close_btn)

    return bar


def _build_body(parent: QWidget) -> QWidget:
    body = QWidget(parent)
    body.setStyleSheet("background:#FFFFFF;")
    return body


# ─── AddTaskDialog ─────────────────────────────────────────────────────────────

class AddTaskDialog(QDialog):
    def __init__(self, quad_keys, quad_titles, default_quad, font_size, parent=None):
        super().__init__(parent)
        self.fs = font_size
        self._result = None
        self._quad_keys = quad_keys
        self._quad_titles = quad_titles
        self._selected_key = quad_keys[quad_titles.index(default_quad)] if default_quad in quad_titles else quad_keys[0]

        self.setWindowTitle("添加任务")
        self.setModal(True)
        self.setFixedSize(460, 420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(_build_title_bar("添加新任务", self))

        body = _build_body(self)
        b = QVBoxLayout(body)
        b.setContentsMargins(20, 16, 20, 16)
        outer.addWidget(body)

        # 任务内容
        b.addWidget(QLabel("任务内容 *"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("输入任务描述...")
        self.text_edit.setFont(QFont(FONT_FAMILY, self.fs))
        self.text_edit.setFixedHeight(72)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{ border: 1px solid #CBD5E1; border-radius: 6px;
                        padding: 8px; font-size: {self.fs}px; color: {TEXT_MAIN};
                        background: #FFFFFF; }}
        """)
        b.addWidget(self.text_edit)

        # 象限选择
        b.addWidget(QLabel("象限"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self._quad_cards = {}
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, cfg in enumerate(QUADS):
            r, c = positions[i]
            card = self._build_quad_card(cfg)
            grid.addWidget(card, r, c)
            self._quad_cards[cfg["key"]] = card
        self._update_quad_cards()
        b.addLayout(grid)

        # 截止日期
        b.addWidget(QLabel("截止日期（可选）"))
        self.dl_edit = QLineEdit()
        self.dl_edit.setPlaceholderText("YYYY-MM-DD")
        self.dl_edit.setFont(QFont(FONT_FAMILY, self.fs - 1))
        self.dl_edit.setStyleSheet(f"""
            QLineEdit {{ border: 1px solid #CBD5E1; border-radius: 6px;
                        padding: 8px 12px; font-size: {self.fs - 1}px; color: {TEXT_MAIN}; }}
        """)
        b.addWidget(self.dl_edit)
        b.addStretch()

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._add_ok_cancel(b, btn_row, "添加", self._on_ok)
        b.addLayout(btn_row)

    def _add_ok_cancel(self, parent_layout, btn_row, ok_text, ok_handler):
        cancel = QPushButton("取消")
        cancel.setFont(QFont(FONT_FAMILY, self.fs))
        cancel.setFixedSize(90, 36)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{ background: #F1F5F9; color: {TEXT_SUB};
                          border: 1px solid #E2E8F0; border-radius: 6px; }}
            QPushButton:hover {{ background: #E2E8F0; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton(ok_text)
        ok.setFont(QFont(FONT_FAMILY, self.fs, QFont.Bold))
        ok.setFixedSize(90, 36)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet(f"""
            QPushButton {{ background: {BTN_PRIMARY_BG}; color: {BTN_PRIMARY_FG};
                          border: none; border-radius: 6px; }}
            QPushButton:hover {{ background: #334155; }}
        """)
        ok.setDefault(False)
        ok.setAutoDefault(False)
        ok.clicked.connect(ok_handler)
        btn_row.addWidget(ok)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            return
        super().keyPressEvent(event)

    def _on_ok(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{ border: 2px solid #EF4444; border-radius: 6px;
                            padding: 8px; font-size: {self.fs}px; color: {TEXT_MAIN};
                            background: #FFFFFF; }}
            """)
            return

        dl = self.dl_edit.text().strip()
        if dl == "YYYY-MM-DD":
            dl = ""

        self._result = (
            {"id": str(uuid.uuid4()), "text": text, "done": False, "deadline": dl},
            self._selected_key,
        )
        self.accept()

    def get_result(self):
        return self._result

    def _build_quad_card(self, cfg):
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedHeight(52)
        card._cfg = cfg
        card._sel_lbl = None
        self._update_card_style(card, False)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)
        tag = QFrame()
        tag.setFixedSize(6, 36)
        tag.setStyleSheet(f"background:{cfg['tag_bg']}; border-radius: 3px;")
        lay.addWidget(tag)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(cfg["title"])
        title_lbl.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        title_lbl.setStyleSheet(f"color:{cfg['header_fg']}; background:transparent; border:none;")
        text_col.addWidget(title_lbl)
        sub_lbl = QLabel(cfg["subtitle"])
        sub_lbl.setFont(QFont(FONT_FAMILY, 10))
        sub_lbl.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        text_col.addWidget(sub_lbl)
        lay.addLayout(text_col)
        lay.addStretch()
        sel_lbl = QLabel("✓")
        sel_lbl.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        sel_lbl.setStyleSheet("color:#3B82F6; background:transparent; border:none;")
        sel_lbl.setFixedWidth(24)
        sel_lbl.setVisible(False)
        lay.addWidget(sel_lbl)
        card._sel_lbl = sel_lbl
        card.mousePressEvent = lambda _, k=cfg["key"]: self._select_quad(k)
        return card

    def _update_card_style(self, card, selected):
        cfg = card._cfg
        border_color = "#3B82F6" if selected else cfg["border"]
        card.setStyleSheet(
            f"background:{cfg['body_bg']}; border: 2px solid {border_color}; "
            f"border-radius: 6px;"
        )

    def _select_quad(self, key):
        self._selected_key = key
        self._update_quad_cards()

    def _update_quad_cards(self):
        for key, card in self._quad_cards.items():
            is_sel = key == self._selected_key
            self._update_card_style(card, is_sel)
            card._sel_lbl.setVisible(is_sel)


# ─── EditTaskDialog ───────────────────────────────────────────────────────────

class EditTaskDialog(QDialog):
    def __init__(self, task, quad_keys, quad_titles, current_quad, font_size, parent=None):
        super().__init__(parent)
        self.fs = font_size
        self._result = None
        self._quad_keys = quad_keys
        self._quad_titles = quad_titles
        self._selected_key = current_quad

        self.setWindowTitle("修改任务")
        self.setModal(True)
        self.setFixedSize(460, 420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(_build_title_bar("修改任务", self))

        body = _build_body(self)
        b = QVBoxLayout(body)
        b.setContentsMargins(20, 16, 20, 16)
        outer.addWidget(body)

        # 任务内容
        b.addWidget(QLabel("任务内容 *"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("输入任务描述...")
        self.text_edit.setFont(QFont(FONT_FAMILY, self.fs))
        self.text_edit.setFixedHeight(72)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{ border: 1px solid #CBD5E1; border-radius: 6px;
                        padding: 8px; font-size: {self.fs}px; color: {TEXT_MAIN};
                        background: #FFFFFF; }}
        """)
        self.text_edit.setPlainText(task.get("text", ""))
        b.addWidget(self.text_edit)

        # 象限选择
        b.addWidget(QLabel("象限"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self._quad_cards = {}
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, cfg in enumerate(QUADS):
            r, c = positions[i]
            card = self._build_quad_card(cfg)
            grid.addWidget(card, r, c)
            self._quad_cards[cfg["key"]] = card
        self._update_quad_cards()
        b.addLayout(grid)

        # 截止日期
        b.addWidget(QLabel("截止日期（可选）"))
        self.dl_edit = QLineEdit()
        self.dl_edit.setPlaceholderText("YYYY-MM-DD")
        self.dl_edit.setFont(QFont(FONT_FAMILY, self.fs - 1))
        self.dl_edit.setStyleSheet(f"""
            QLineEdit {{ border: 1px solid #CBD5E1; border-radius: 6px;
                        padding: 8px 12px; font-size: {self.fs - 1}px; color: {TEXT_MAIN}; }}
        """)
        self.dl_edit.setText(task.get("deadline", ""))
        b.addWidget(self.dl_edit)
        b.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._add_ok_cancel(b, btn_row, "保存", self._on_ok)
        b.addLayout(btn_row)

    def _add_ok_cancel(self, parent_layout, btn_row, ok_text, ok_handler):
        cancel = QPushButton("取消")
        cancel.setFont(QFont(FONT_FAMILY, self.fs))
        cancel.setFixedSize(90, 36)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{ background: #F1F5F9; color: {TEXT_SUB};
                          border: 1px solid #E2E8F0; border-radius: 6px; }}
            QPushButton:hover {{ background: #E2E8F0; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton(ok_text)
        ok.setFont(QFont(FONT_FAMILY, self.fs, QFont.Bold))
        ok.setFixedSize(90, 36)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet(f"""
            QPushButton {{ background: {BTN_PRIMARY_BG}; color: {BTN_PRIMARY_FG};
                          border: none; border-radius: 6px; }}
            QPushButton:hover {{ background: #334155; }}
        """)
        ok.setDefault(False)
        ok.setAutoDefault(False)
        ok.clicked.connect(ok_handler)
        btn_row.addWidget(ok)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            return
        super().keyPressEvent(event)

    def _on_ok(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{ border: 2px solid #EF4444; border-radius: 6px;
                            padding: 8px; font-size: {self.fs}px; color: {TEXT_MAIN};
                            background: #FFFFFF; }}
            """)
            return

        dl = self.dl_edit.text().strip()
        if dl == "YYYY-MM-DD":
            dl = ""

        self._result = (text, dl, self._selected_key)
        self.accept()

    def get_result(self):
        return self._result

    def _build_quad_card(self, cfg):
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedHeight(52)
        card._cfg = cfg
        card._sel_lbl = None
        self._update_card_style(card, False)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)
        tag = QFrame()
        tag.setFixedSize(6, 36)
        tag.setStyleSheet(f"background:{cfg['tag_bg']}; border-radius: 3px;")
        lay.addWidget(tag)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(cfg["title"])
        title_lbl.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        title_lbl.setStyleSheet(f"color:{cfg['header_fg']}; background:transparent; border:none;")
        text_col.addWidget(title_lbl)
        sub_lbl = QLabel(cfg["subtitle"])
        sub_lbl.setFont(QFont(FONT_FAMILY, 10))
        sub_lbl.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        text_col.addWidget(sub_lbl)
        lay.addLayout(text_col)
        lay.addStretch()
        sel_lbl = QLabel("✓")
        sel_lbl.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        sel_lbl.setStyleSheet("color:#3B82F6; background:transparent; border:none;")
        sel_lbl.setFixedWidth(24)
        sel_lbl.setVisible(False)
        lay.addWidget(sel_lbl)
        card._sel_lbl = sel_lbl
        card.mousePressEvent = lambda _, k=cfg["key"]: self._select_quad(k)
        return card

    def _update_card_style(self, card, selected):
        cfg = card._cfg
        border_color = "#3B82F6" if selected else cfg["border"]
        card.setStyleSheet(
            f"background:{cfg['body_bg']}; border: 2px solid {border_color}; "
            f"border-radius: 6px;"
        )

    def _select_quad(self, key):
        self._selected_key = key
        self._update_quad_cards()

    def _update_quad_cards(self):
        for key, card in self._quad_cards.items():
            is_sel = key == self._selected_key
            self._update_card_style(card, is_sel)
            card._sel_lbl.setVisible(is_sel)


# ─── SettingsDialog ────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._colors = dict(data.get("deadline_colors", {}))
        self._thresholds = dict(
            data.get("deadline_thresholds", {"days3": 3, "days7": 7})
        )

        self.setWindowTitle("设置")
        self.setModal(True)
        self.setFixedSize(440, 420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(_build_title_bar("设置", self))

        body = _build_body(self)
        b = QVBoxLayout(body)
        b.setContentsMargins(20, 16, 20, 16)
        outer.addWidget(body)

        # 小标题
        h = QLabel("截止日期颜色与阈值规则")
        h.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        h.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; margin-bottom: 8px;")
        b.addWidget(h)

        self._spin_widgets = {}
        self._label_widgets = {}
        self._color_widgets = {}

        # 用 GridLayout 三列对齐：名称 | 阈值/提示 | 颜色
        from PySide6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 0)   # 名称列固定
        grid.setColumnStretch(1, 1)   # 阈值/提示列可伸缩
        grid.setColumnStretch(2, 0)   # 颜色列向左贴靠

        row_idx = 0

        # 固定项（无 spin）
        for key, label_text, hint, color_key in [
            ("overdue", "已过期", "< 0天", "overdue"),
            ("today",   "今天",   "= 0天", "today"),
        ]:
            self._add_fixed_row_to_grid(grid, row_idx, key, label_text, hint, color_key)
            row_idx += 1

        # 可配置项（有 spin）：即将到期、近期、正常
        for key, label_text, default_val in [
            ("days3",  "即将到期", 3),
            ("days7",  "近期",     7),
        ]:
            self._add_config_row_to_grid(grid, row_idx, key, label_text, default_val)
            row_idx += 1

        # 固定项（无 spin）：正常、无日期
        self._add_fixed_row_to_grid(grid, row_idx, "normal", "正常", "更长时间", "normal")
        row_idx += 1
        self._add_fixed_row_to_grid(grid, row_idx, "none", "无日期", "—", "none")
        row_idx += 1

        b.addLayout(grid)

        b.addStretch()

        # 确定 / 取消
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("取消")
        cancel.setFont(QFont(FONT_FAMILY, 11))
        cancel.setFixedSize(90, 32)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{ background: #F1F5F9; color: {TEXT_SUB};
                          border: 1px solid #E2E8F0; border-radius: 6px; }}
            QPushButton:hover {{ background: #E2E8F0; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton("确定")
        ok.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        ok.setFixedSize(90, 32)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet(f"""
            QPushButton {{ background: {BTN_PRIMARY_BG}; color: {BTN_PRIMARY_FG};
                          border: none; border-radius: 6px; }}
            QPushButton:hover {{ background: #334155; }}
        """)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)
        b.addLayout(btn_row)

    # ─── 行构建 ────────────────────────────────────────────────────────────────

    def _add_fixed_row_to_grid(self, grid, row, key, label_text, hint, color_key):
        col = QLabel(label_text)
        col.setFont(QFont(FONT_FAMILY, 11))
        col.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent;")
        col.setFixedWidth(90)
        grid.addWidget(col, row, 0)

        hint_lbl = QLabel(hint)
        hint_lbl.setFont(QFont(FONT_FAMILY, 10))
        hint_lbl.setStyleSheet("color:#94A3B8; background:transparent;")
        hint_lbl.setFixedWidth(70)
        grid.addWidget(hint_lbl, row, 1)

        color_btn = self._make_color_btn(color_key)
        grid.addWidget(color_btn, row, 2)
        self._color_widgets[color_key] = color_btn

    def _add_config_row_to_grid(self, grid, row, key, label_text, default_val):
        dyn_lbl = QLabel(label_text)
        dyn_lbl.setFont(QFont(FONT_FAMILY, 11))
        dyn_lbl.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent;")
        dyn_lbl.setFixedWidth(90)
        self._label_widgets[key] = dyn_lbl
        grid.addWidget(dyn_lbl, row, 0)

        spin = QSpinBox()
        spin.setFixedSize(70, 26)
        spin.setFont(QFont(FONT_FAMILY, 11))
        spin.setMinimum(1)
        spin.setMaximum(999)
        spin.setValue(self._thresholds.get(key, default_val))
        spin.setStyleSheet(f"""
            QSpinBox {{ border: 1px solid #CBD5E1; border-radius: 4px;
                       padding: 2px 6px; color: {TEXT_MAIN}; background: #FFFFFF; }}
        """)
        spin.valueChanged.connect(
            lambda val, k=key, lbl=dyn_lbl, txt=label_text, sp=spin:
                self._on_threshold_change(k, lbl, txt, sp)
        )
        self._spin_widgets[key] = spin

        suffix = QLabel("天")
        suffix.setFont(QFont(FONT_FAMILY, 11))
        suffix.setStyleSheet(f"color:{TEXT_SUB}; background:transparent;")

        # spin + 后缀放在一个子 HBox 中，再整体加入 grid 第 1 列
        mid = QHBoxLayout()
        mid.setSpacing(4)
        mid.addWidget(spin)
        mid.addWidget(suffix)
        grid.addLayout(mid, row, 1)

        color_btn = self._make_color_btn(key)
        grid.addWidget(color_btn, row, 2)
        self._color_widgets[key] = color_btn

        self._on_threshold_change(key, dyn_lbl, label_text, spin)

    def _on_threshold_change(self, key, lbl, base_text, spin):
        lbl.setText(f"{base_text}")

    def _make_color_btn(self, key) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(90, 26)
        btn.setCursor(Qt.PointingHandCursor)
        hex_color = self._colors.get(key, "#94A3B8")
        self._apply_btn_style(btn, hex_color)
        # 用默认参数捕获 key，避免 lambda 循环陷阱
        btn.clicked.connect(
            lambda _, k=key, b=btn: self._pick_color(k, b)
        )
        return btn

    def _apply_btn_style(self, btn, hex_color):
        btn.setStyleSheet(
            f"QPushButton {{ background: {hex_color}; border: 1px solid #CBD5E1; "
            f"border-radius: 4px; color: #FFFFFF; font-size: 11px; "
            f"font-family: 'Microsoft YaHei'; }}"
            f"QPushButton:hover {{ border-color: #94A3B8; }}"
        )

    def _pick_color(self, key, btn):
        color = QColorDialog.getColor(
            initial=QColor(self._colors.get(key, "#94A3B8")),
            parent=self,
        )
        if color.isValid():
            hex_color = color.name()
            self._colors[key] = hex_color
            self._apply_btn_style(btn, hex_color)

    def get_colors(self) -> dict:
        return dict(self._colors)

    def get_thresholds(self) -> dict:
        return {key: spin.value() for key, spin in self._spin_widgets.items()}
