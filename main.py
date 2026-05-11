# -*- coding: utf-8 -*-
"""启动入口（直接运行: python main.py）"""

import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from data import (
    cli_add_task,
    cli_list_tasks,
    cli_delete_task,
    cli_delete_all,
    cli_edit_task,
)


if __name__ == "__main__":
    is_cli = len(sys.argv) > 1 and sys.argv[1] == "--cli"
    if is_cli:
        sys.argv.pop(1)
        print("四象限任务板 CLI")
        print()

    parser = argparse.ArgumentParser(
        description="四象限任务板 CLI - 命令行任务管理工具",
        epilog="象限说明: q1=紧急且重要, q2=重要不紧急, q3=紧急不重要, q4=不紧急不重要",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    add_parser = subparsers.add_parser(
        "add",
        help="添加新任务到指定象限",
        description="创建新任务，需要指定所属象限和标题，可选添加截止日期",
    )
    add_parser.add_argument("--quadrant", "-q", required=True, help="象限 (q1/q2/q3/q4)，必填")
    add_parser.add_argument("--title", "-t", required=True, help="任务标题，必填")
    add_parser.add_argument("--deadline", "-l", default="", help="截止日期，格式: YYYY-MM-DD，可选")

    list_parser = subparsers.add_parser(
        "list",
        help="列出任务",
        description="查看任务列表，可按象限筛选",
    )
    list_parser.add_argument("--quadrant", "-q", default="", help="象限 (q1/q2/q3/q4)，可选，不指定则列出全部")

    delete_parser = subparsers.add_parser(
        "delete",
        help="删除任务",
        description="删除单个或批量删除任务",
    )
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument("--id", "-i", help="任务ID，删除指定任务")
    delete_group.add_argument("--all", "-a", action="store_true", help="删除所有任务")
    delete_parser.add_argument("--quadrant", "-q", default="", help="象限 (q1/q2/q3/q4)，配合 --all 使用")

    edit_parser = subparsers.add_parser(
        "edit",
        help="编辑任务",
        description="修改任务属性：标题、截止日期、象限、完成状态",
    )
    edit_parser.add_argument("--id", "-i", required=True, help="任务ID，必填")
    edit_parser.add_argument("--title", "-t", default="", help="新标题")
    edit_parser.add_argument("--desc", "-d", default="", help="新描述")
    edit_parser.add_argument("--deadline", "-l", default=None, help="新截止日期，格式: YYYY-MM-DD")
    edit_parser.add_argument("--done", choices=["true", "false"], help="完成状态: true=已完成, false=未完成")
    edit_parser.add_argument("--quadrant", "-q", default="", help="移动任务到新象限")

    args = parser.parse_args()

    if args.command == "add":
        cli_add_task(args.quadrant, args.title, args.deadline)
    elif args.command == "list":
        cli_list_tasks(args.quadrant)
    elif args.command == "delete":
        if args.all:
            cli_delete_all(args.quadrant)
        else:
            cli_delete_task(args.id)
    elif args.command == "edit":
        done = None
        if args.done is not None:
            done = args.done == "true"
        cli_edit_task(args.id, args.title, args.desc, args.deadline, done, args.quadrant)
    else:
        parser.print_help()

    if not is_cli:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from main_window import MainWindow

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        win = MainWindow()
        win.show()

        sys.exit(app.exec())
