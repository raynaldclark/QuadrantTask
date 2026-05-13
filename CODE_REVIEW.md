# 代码审查报告 · 四象限任务板 v1.3.4

> 审查时间：2026-05-13  
> 审查范围：全部 `.py` 源文件  
> 总代码量：~3200 行

---

## 一、代码健康度总览

| 指标 | 状态 |
|------|------|
| 编译通过 | 9/9 ✅ |
| 裸 `except` | 0 ✅ |
| TODO / FIXME | 0 ✅ |
| 类型注解覆盖率 | ~70%（数据层、主窗口完全覆盖） |
| 复杂函数（>80行） | 2 个 ⚠️ |
| 重复代码段 | 1 处 ⚠️ |

---

## 二、架构问题

### ⚠️ A. 巨无霸函数

**`dialogs.py` — `SettingsDialog.__init__`（182 行）**

问题：设置对话框的构造函数同时承担了布局构建、状态初始化、回调注册、网格配置五个职责，违反单一职责原则。

建议拆分：
```python
# 伪代码
class SettingsDialog(QDialog):
    def __init__(self, data, font_size, on_font_change, on_font_size_change, parent):
        super().__init__(parent)
        self._init_state(data)
        self._setup_window()
        self._build_ui()
        self._connect_signals()
```

**`quadrant_panel.py` — `_build_context_menu`（124 行）**

问题：右键菜单构建、字体按钮动态创建、action 状态判断全部混在一起。

建议拆分为 `_build_menu_actions()`、`_build_font_actions()`、`_refresh_menu_state()`。

---

### ⚠️ B. 状态管理脆性

**`main_window.py` — `_reload_data` 与 `_toggle_topmost` 的隐式契约**

当前代码：
- `_toggle_topmost` 写入 `data["is_topmost"]` 并 `save()`
- `_reload_data` 故意**跳过** `is_topmost` 的加载

两者之间存在隐式同步约定。如果未来有人维护 `_reload_data` 并补上 `is_topmost` 的读取，置顶功能会 silently broken。

建议：
```python
# _reload_data 中显式保留约定
def _reload_data(self):
    old_topmost = self._is_topmost  # 保留当前状态
    self.data = load_data()
    # is_topmost 由 _toggle_topmost 独占，不恢复
    self._is_topmost = old_topmost
    ...
```

---

### ⚠️ C. `_svg_icon` 静默失败

`_svg_icon` 在渲染器无效或文件不存在时返回空 `QIcon()`，不输出任何日志。图标消失时无法定位原因。

建议至少加 debug 日志：
```python
if not renderer.isValid():
    print(f"[WARN] SVG 渲染器无效: {path}")
    return QIcon()
```

---

## 三、重复代码

### `dropEvent` 逻辑重复

`quadrant_panel.py` 的 `dropEvent` 中，同象限移动和跨象限移动的 `DRAG_OFFSET` 计算逻辑完全一致（各8行），仅目标索引来源不同。

可提取为：
```python
def _get_drop_index(self, event_pos):
    viewport_y = event_pos.y()
    scroll_offset = self.scroll.verticalScrollBar().value()
    local_y = viewport_y + scroll_offset - DRAG_OFFSET
    return self._calculate_drop_index(local_y)
```

### 按钮样式字符串重复

`main_window.py` 中 `background: transparent; border: none;` 出现 4 次，可提取为类常量。

---

## 四、潜在 Bug

### 1. `_build_toolbar` 调用顺序依赖

`_update_top_icon` 调用时，`_topmost_wrapper` 已由 `_build_toolbar` 在同一调用链内创建，所以当前没问题。但如果未来重构把 `_update_top_icon` 提前到 `_build_toolbar` 之前，会触发 `AttributeError`。

建议在 `_update_top_icon` 末尾做 `return` 的守卫：
```python
def _update_top_icon(self):
    if not hasattr(self, '_topmost_wrapper') or self._topmost_wrapper is None:
        return
    ...
```

### 2. `_update_card_widths` 的递归调用风险

`_update_card_widths` 在 `render_tasks` 末尾用 `QTimer.singleShot(0, ...)` 调用；`eventFilter` 的 `Resize` 事件也调用它。如果连续多次 resize，可能堆积大量延迟调用。Qt 的单次延迟队列理论上会合并，但更安全的做法是：
```python
self._width_update_timer = QTimer(self)
self._width_update_timer.setSingleShot(True)
self._width_update_timer.start(50)  # 50ms 防抖
```

### 3. `data.py` — `cli_edit_task` 的 `desc` 字段

`cli_edit_task` 支持 `--desc` 参数，但数据模型中不存在 `desc` 字段（只有 `text`），且 `load_data` / `default_data` 中无此字段。编辑时写入 `desc` 会变成数据中的垃圾字段。

建议：要么在 `TaskCard` 和 `_update_text_label` 中读取 `desc`，要么从 CLI 中移除 `--desc`。

### 4. `dialogs.py` 版本字符串硬编码

`SettingsDialog` 底部的版本号 `"版本 1.2.4"` 已过时（当前 v1.3.4），每次发版都可能忘记更新。

建议：
```python
from importlib.metadata import version, PackageNotFoundError
try:
    __ver__ = version("quadranttask")  # 或从 __init__ 导入
except PackageNotFoundError:
    __ver__ = "dev"
```

---

## 五、可增加的功能

### 🔥 高优先级

| 功能 | 理由 | 工作量 |
|------|------|--------|
| **任务搜索 / 过滤** | 当前只能滚动浏览，超过20个任务查找困难 | 中 |
| **键盘快捷键** | Ctrl+Z 撤销、Ctrl+N 新建、Delete 删除等基本操作无需鼠标 | 小 |
| **截止日期排序** | 按紧急程度排序能快速聚焦 | 小 |
| **任务标签 / 分类** | 当前只有四象限，细粒度不够 | 大 |
| **数据备份 / 导出** | JSON 文件误删或损坏无恢复路径 | 中 |
| **打开数据目录按钮** | 用户找不到 `quadrant_data.json` 在哪 | 小 |

### 🟡 中优先级

| 功能 | 理由 |
|------|------|
| 深色模式 | 长期使用疲劳，护眼需求 |
| 任务统计面板 | 完成率、象限分布可视化 |
| 截止日期倒计时 Widget | 任务卡片上显示"还有 X 天" |
| 任务完成 Streak 追踪 | 提升持续使用动力 |
| 托盘最小化 | 后台常驻，不占任务栏 |
| 多语言支持 | 目前只有中文，英文用户无法使用 |
| CSV / Excel 导出 | 二次处理或汇报 |
| 任务优先级颜色标签 | 补充截止日期颜色之外的视觉维度 |

### 🟢 低优先级 / 长期

| 功能 | 理由 |
|------|------|
| 任务备注 / 富文本描述 | 当前只有标题 |
| 子任务 / 依赖关系 | 复杂项目需要 |
| 日历视图 | 截止日期一览 |
| 云同步 | 多设备协同 |
| 插件系统 | 扩展性 |
| PWA / 网页版 | 跨平台 |

---

## 六、代码质量改进建议

| 优先级 | 改动 | 理由 |
|--------|------|------|
| 🔴 立即 | 提取 `DRAG_OFFSET` 为类常量 | 2 处重复，维护时容易不一致 |
| 🔴 立即 | `dialogs.py:703` 版本号改为动态读取 | 每次发版必定出错 |
| 🟠 近期 | 拆分 `SettingsDialog.__init__` | 182 行难以维护 |
| 🟠 近期 | 拆分 `_build_context_menu` | 124 行职责不清晰 |
| 🟡 中期 | `_svg_icon` 添加失败日志 | 图标消失无法定位 |
| 🟡 中期 | `_reload_data` 显式注释保留 `_is_topmost` | 防止未来维护者踩坑 |
| 🟢 长期 | 为按钮样式提取 `STYLE_*` 常量 | 统一维护颜色主题 |

---

## 七、数据模型建议

当前 `quadrant_data.json` 结构：

```json
{
  "font_size": 13,
  "font_family": "Microsoft YaHei",
  "geometry": null,
  "deadline_colors": { ... },
  "deadline_thresholds": { ... },
  "show_done": true,
  "is_topmost": false,
  "tasks": { "q1": [...], "q2": [...], ... }
}
```

**建议增加：**
```json
{
  "version": "1.3.4",          // ← 新增：方便数据迁移
  "tasks": {
    "q1": [{
      "id": "...",
      "text": "标题",
      "done": false,
      "deadline": "2026-05-20",
      "tags": ["工作", "紧急"],  // ← 新增：标签
      "note": "备注内容",        // ← 新增：备注（可选）
      "priority": "high"        // ← 新增：优先级
    }]
  }
}
```

---

## 八、稳定性改进

| 场景 | 当前风险 | 建议 |
|------|---------|------|
| 删除 `quadrant_data.json` 后重启 | 使用默认数据，用户数据全丢 | 启动时检测，若文件不存在则备份为 `.bak` |
| 文件被其他程序占用 | `save_data` 捕获异常只打印，不重试 | 捕获 `PermissionError` 后弹框提示 |
| 拖拽超大文本内容 | 文本作为 `setData` MIME 传输无长度限制 | 添加最大长度限制 |
| 高 DPI 缩放 | `_logical_to_physical` 直接 `int()` 可能精度丢失 | 用 `round()` 替代 `int()` |

---

*报告生成完毕。*
