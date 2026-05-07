# -*- coding: utf-8 -*-
"""启动入口（直接运行: python main.py）"""

import os
import sys

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()

    sys.exit(app.exec())
