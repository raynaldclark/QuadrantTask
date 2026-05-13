# -*- coding: utf-8 -*-
"""数据层：持久化存储、加载、默认值"""

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from constants import (
    DEADLINE_COLORS_DEFAULT,
    DEADLINE_THRESHOLDS_DEFAULT,
    QUADS,
)


# ─── 数据路径 ──────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "quadrant_data.json")


def default_data() -> Dict[str, Any]:
    """返回带有所有默认值的应用数据结构。"""
    return {
        "font_size": 13,
        "font_family": "Microsoft YaHei",
        "geometry": None,
        "deadline_colors": dict(DEADLINE_COLORS_DEFAULT),
        "deadline_thresholds": dict(DEADLINE_THRESHOLDS_DEFAULT),
        "tasks": {q["key"]: [] for q in QUADS},
    }


def load_data() -> Dict[str, Any]:
    """从 JSON 文件加载数据，带向后兼容迁移。"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)

            for q in QUADS:
                if q["key"] not in data.get("tasks", {}):
                    data["tasks"][q["key"]] = []

            if "geometry" not in data:
                data["geometry"] = None

            if "deadline_colors" not in data:
                data["deadline_colors"] = dict(DEADLINE_COLORS_DEFAULT)

            if "deadline_thresholds" not in data:
                data["deadline_thresholds"] = dict(DEADLINE_THRESHOLDS_DEFAULT)

            if "font_family" not in data:
                data["font_family"] = "Microsoft YaHei"

            if "is_topmost" not in data:
                data["is_topmost"] = False

            return data
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[WARN] 数据文件加载失败: {exc}，将使用默认数据")

    return default_data()


def save_data(data: Dict[str, Any]) -> None:
    """将数据字典写入 JSON 文件。"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"保存失败: {exc}")


# ─── CLI 操作函数 ─────────────────────────────────────────────────────────────

def cli_add_task(quadrant: str, title: str, deadline: str = "") -> Optional[str]:
    """添加任务，返回任务ID"""
    if quadrant not in [q["key"] for q in QUADS]:
        print(f"无效的象限: {quadrant}")
        return None
    if deadline:
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            print(f"无效的日期格式: {deadline}，请使用 YYYY-MM-DD")
            return None
    data = load_data()
    task = {
        "id": str(uuid.uuid4()),
        "text": title,
        "done": False,
        "deadline": deadline,
    }
    data["tasks"][quadrant].append(task)
    save_data(data)
    print(f"任务已添加: {task['id']}")
    return task["id"]


def cli_list_tasks(quadrant: str = "") -> List[Dict[str, Any]]:
    """列出任务，可指定象限"""
    data = load_data()
    if quadrant:
        if quadrant not in [q["key"] for q in QUADS]:
            print(f"无效的象限: {quadrant}")
            return []
        tasks = data["tasks"].get(quadrant, [])
    else:
        tasks = []
        for q_tasks in data["tasks"].values():
            tasks.extend(q_tasks)
    if not tasks:
        print("没有任务")
    else:
        for t in tasks:
            done_mark = "[x]" if t.get("done") else "[ ]"
            deadline_str = f" 截止:{t.get('deadline', '')}" if t.get('deadline') else ""
            print(f"[{t['id'][:8]}] {done_mark} {t.get('text', '')}{deadline_str}")
    return tasks


def cli_delete_task(task_id: str) -> bool:
    """删除指定ID的任务"""
    data = load_data()
    for q_key, tasks in data["tasks"].items():
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                data["tasks"][q_key].pop(i)
                save_data(data)
                print(f"任务已删除: {task_id}")
                return True
    print(f"未找到任务: {task_id}")
    return False


def cli_delete_all(quadrant: str = "") -> int:
    """删除所有任务或指定象限的任务"""
    data = load_data()
    if quadrant:
        if quadrant not in [q["key"] for q in QUADS]:
            print(f"无效的象限: {quadrant}")
            return 0
        count = len(data["tasks"].get(quadrant, []))
        data["tasks"][quadrant] = []
    else:
        count = sum(len(tasks) for tasks in data["tasks"].values())
        for q_key in data["tasks"]:
            data["tasks"][q_key] = []
    save_data(data)
    print(f"已删除 {count} 个任务")
    return count


def cli_edit_task(task_id: str, title: str = "", desc: str = "", deadline: str = "",
                  done: Optional[bool] = None, quadrant: str = "") -> bool:
    """编辑任务"""
    data = load_data()
    for q_key, tasks in data["tasks"].items():
        for task in tasks:
            if task["id"] == task_id:
                if title:
                    task["text"] = title
                if desc:
                    task["desc"] = desc
                if deadline is not None:
                    task["deadline"] = deadline
                if done is not None:
                    task["done"] = done
                if quadrant and quadrant in [q["key"] for q in QUADS]:
                    data["tasks"][q_key].remove(task)
                    data["tasks"][quadrant].append(task)
                save_data(data)
                print(f"任务已更新: {task_id}")
                return True
    print(f"未找到任务: {task_id}")
    return False