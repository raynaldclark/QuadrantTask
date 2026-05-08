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
        print()
        print("=" * 60)
        print("ADD - 添加任务")
        print("=" * 60)
        print("用法: python main.py --cli add -q <象限> -t <标题> [-l <截止日期>]")
        print()
        print("  -q, --quadrant <象限>  必需。任务所属象限 (q1/q2/q3/q4)")
        print("                          q1: 紧急且重要")
        print("                          q2: 重要不紧急")
        print("                          q3: 紧急不重要")
        print("                          q4: 不紧急不重要")
        print("  -t, --title <标题>     必需。任务标题")
        print("  -l, --deadline <日期>  可选。截止日期，格式: YYYY-MM-DD")
        print()
        print("示例:")
        print("  python main.py --cli add -q q1 -t \"处理用户投诉\"")
        print("  python main.py --cli add -q q2 -t \"制定计划\" -l 2026-06-01")
        print()
        print("=" * 60)
        print("LIST - 列出任务")
        print("=" * 60)
        print("用法: python main.py --cli list [-q <象限>]")
        print()
        print("  -q, --quadrant <象限>  可选。只列出指定象限的任务")
        print()
        print("示例:")
        print("  python main.py --cli list           # 列出所有任务")
        print("  python main.py --cli list -q q1     # 只列出 q1 象限的任务")
        print()
        print("=" * 60)
        print("DELETE - 删除任务")
        print("=" * 60)
        print("用法: python main.py --cli delete -i <任务ID>")
        print("      python main.py --cli delete --all [-q <象限>]")
        print()
        print("  -i, --id <任务ID>     删除指定ID的任务（与 --all 互斥）")
        print("  -a, --all             删除所有任务（与 -i 互斥）")
        print("  -q, --quadrant <象限>  可选。配合 --all 使用，删除指定象限的任务")
        print()
        print("示例:")
        print("  python main.py --cli delete -i abc12345")
        print("  python main.py --cli delete --all")
        print("  python main.py --cli delete --all -q q1")
        print()
        print("=" * 60)
        print("EDIT - 编辑任务")
        print("=" * 60)
        print("用法: python main.py --cli edit -i <任务ID> [选项]")
        print()
        print("  -i, --id <任务ID>      必需。要编辑的任务ID")
        print("  -t, --title <标题>     可选。新的任务标题")
        print("  -l, --deadline <日期>  可选。新的截止日期，格式: YYYY-MM-DD")
        print("  -q, --quadrant <象限>  可选。移动任务到新象限")
        print("  --done <true|false>    可选。设置完成状态 (true=已完成, false=未完成)")
        print()
        print("示例:")
        print("  python main.py --cli edit -i abc12345 -t \"新标题\"")
        print("  python main.py --cli edit -i abc12345 --done true")
        print("  python main.py --cli edit -i abc12345 -q q2 --done false")
        sys.exit(0)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from main_window import MainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()

    sys.exit(app.exec())
