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


def run_cli():
    parser = argparse.ArgumentParser(description="四象限任务板 CLI")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    add_parser = subparsers.add_parser("add", help="添加任务")
    add_parser.add_argument("--quadrant", "-q", required=True, help="象限 (q1/q2/q3/q4)")
    add_parser.add_argument("--title", "-t", required=True, help="任务标题")
    add_parser.add_argument("--deadline", "-l", default="", help="截止日期 (YYYY-MM-DD)")

    list_parser = subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--quadrant", "-q", default="", help="象限 (q1/q2/q3/q4)")

    delete_parser = subparsers.add_parser("delete", help="删除任务")
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument("--id", "-i", help="任务ID")
    delete_group.add_argument("--all", "-a", action="store_true", help="删除所有任务")
    delete_parser.add_argument("--quadrant", "-q", default="", help="象限 (q1/q2/q3/q4)")

    edit_parser = subparsers.add_parser("edit", help="编辑任务")
    edit_parser.add_argument("--id", "-i", required=True, help="任务ID")
    edit_parser.add_argument("--title", "-t", default="", help="新标题")
    edit_parser.add_argument("--desc", "-d", default="", help="新描述")
    edit_parser.add_argument("--deadline", "-l", default="", help="新截止日期")
    edit_parser.add_argument("--done", choices=["true", "false"], help="完成状态")
    edit_parser.add_argument("--quadrant", "-q", default="", help="移动到新象限")

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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        sys.argv.pop(1)
        if len(sys.argv) > 1 and sys.argv[1] == "--help":
            sys.argv.pop(1)
            print("四象限任务板 CLI")
            print()
            print("用法: python main.py --cli <命令> [选项]")
            print()
            print("命令:")
            print("  add       添加任务")
            print("  list      列出任务")
            print("  delete    删除任务")
            print("  edit      编辑任务")
            print()
            print("输入 'python main.py --cli <命令> --help' 查看具体用法")
            sys.exit(0)
        run_cli()
        sys.exit(0)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from main_window import MainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()

    sys.exit(app.exec())
