# -*- coding: utf-8 -*-
"""启动入口（直接运行: python main.py）"""

import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()

    sys.exit(app.exec())
