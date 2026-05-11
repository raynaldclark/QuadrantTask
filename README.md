# 四象限任务板

基于 PySide6 的四象限时间管理工具，将任务按照重要性和紧急性分为四个象限进行管理。

![四象限任务板](https://img.shields.io/badge/version-v1.3.3-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-orange)

![预览](preview.jpg)

## 功能特性

- **四象限管理**：将任务按重要/紧急程度分配到四个象限
- **拖拽排序**：任务卡片支持拖拽调整顺序
- **撤销/重做**：支持多步撤销和重做操作
- **截止日期**：支持为任务设置截止日期，自动以颜色标识剩余时间
- **显示/隐藏已完成**：可切换已完成任务是否显示
- **字体调节**：支持调节界面字体大小
- **HiDPI 支持**：完美适配各种分辨率屏幕
- **CLI 支持**：可通过命令行进行任务的增删改查操作

## CLI 命令

```bash
# 添加任务（默认未完成）
python main.py --cli add -q q1 -t "任务标题" -l 2026-05-10

# 列出任务（可指定象限）
python main.py --cli list
python main.py --cli list -q q1

# 删除任务
python main.py --cli delete -i <task_id>
python main.py --cli delete --all        # 删除所有
python main.py --cli delete --all -q q1 # 删除指定象限

# 编辑任务
python main.py --cli edit -i <task_id> -t "新标题"
python main.py --cli edit -i <task_id> --done true
python main.py --cli edit -i <task_id> -q q2 --done false

# 查看帮助
python main.py --cli --help
python main.py --cli add --help
```

象限说明：`q1` 紧急且重要，`q2` 重要不紧急，`q3` 紧急不重要，`q4` 不紧急不重要。

> CLI 与 GUI 数据实时同步，关闭 GUI 前请确保已完成编辑。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 数据存储

运行时数据保存在 `quadrant_data.json`，包含字段：
- `font_size` - 全局字体大小
- `geometry` - 窗口位置与尺寸
- `deadline_colors` - 截止日期颜色配置
- `deadline_thresholds` - 截止日期颜色阈值
- `tasks` - 各象限任务列表

## 版本

v1.3.3

### v1.3.3 右键菜单功能

- 为每个象限面板添加右键菜单，菜单包含工具栏所有功能（图标+文字）
- 右键菜单选项：撤销、显示已完成/隐藏已完成、清空已完成、清空全部、添加任务、设置、关闭程序
- 撤销按钮根据撤销栈状态动态切换图标（undo.svg / undo2.svg）并启用/禁用
- 显示已完成按钮根据当前状态动态切换图标和文字
- 右键菜单样式优化：图标尺寸、文字大小、间距、圆角全面放大，更易点击

### v1.3.2 Bug 修复和性能优化

#### 拖拽排序修复
- 修复拖拽排序边界问题：非最后一个任务现在可以正常移动到最后位置
- 修复 `_calculate_drop_index` 的 `max_index` 计算（`count()-2` → `count()-1`）
- 修复 `reorder_task` 边界检查，允许 `new_index == len(tasks)`

#### 数据持久化修复
- 修复 `data.py` `cli_edit_task`：移动任务时截止日期不再被覆盖
- 修复 `data.py` `load_data`：异常处理改进，不再静默吞掉错误
- 修复 `data.py` `cli_add_task`：添加日期格式验证，拒绝无效日期
- 修复 `data.py` `cli_edit_task`：deadline 默认值从空字符串改为 `None`

#### 界面优化
- 修复 `task_card.py`：移除 `paintEvent` 中的 `_update_text_label()` 调用，提升渲染性能
- 修复 `task_card.py`：`deadline_color` 添加空截止日期检查，避免解析错误
- 修复 `quadrant_panel.py`：`clear_all` 添加撤销支持
- 简化 `main_window.py` `_snap_to_edges` 重复循环逻辑（52 行 → 22 行）
- 修复 `main_window.py`：删除重复的 `_show_edit_dialog` 方法定义

#### CLI 改进
- 修复 `main.py` CLI 执行逻辑，移除无效的 `run_cli()` 函数
- 修复 `--cli` 标志处理，确保 CLI 命令正确执行
- 新增 `requirements.txt` 明确指定 PySide6 依赖

### v1.3.1 窗口边缘吸附功能

- 拖拽窗口靠近屏幕边缘时自动吸附
- 支持多屏幕环境，自动识别窗口所在屏幕
- 吸附时考虑 Windows 任务栏高度，窗口不会遮挡任务栏
- 支持标题栏拖拽和主界面拖拽两种方式

### v1.3.0

### v1.3.0 GUI界面美化和任务卡片拖拽功能优化

#### 窗口界面重构
- 采用无边框窗口设计，自定义标题栏实现 Windows 原生风格
- 标题栏支持最小化、最大化、还原、关闭按钮（SVG 图标）
- 窗口仅允许从底部、底角、右侧边缘调整大小
- 鼠标悬停标题栏时自动高亮窗口控制按钮
- 工具栏背景设为纯白色，移除底部边框

#### 任务卡片拖拽排序
- 支持同象限内任务卡片拖拽重排序
- 支持跨象限任务卡片移动
- 拖拽时显示蓝色高亮边框指示目标位置
- 优化拖拽坐标计算，精确到卡片中点对比
- 向上拖拽越过卡片中点时触发排序
- 向下拖拽越过卡片中点以下时触发排序
- 修复文件监听器重复触发导致数据重置的问题

#### 设置对话框优化
- 标题栏采用第二象限配色（#DBEAFE 背景，#1E40AF 文字）
- 确定/取消按钮添加 2px #BFDBFE 边框
- 对话框底部添加版本信息和开发者标识

### v1.2.4 任务卡片文本显示优化

- 重构任务卡片文本渲染，使用 QLabel 替代手动绘制
- 修复中文文字换行后卡片高度计算不准确的问题
- 优化文字宽度设置，提升长文本显示效果
- CLI 帮助信息详细化，增加命令描述和使用说明

### v1.2.3 CLI 支持

- 新增 CLI 命令：add、list、delete、edit
- delete 支持 `--all` 参数删除全部任务
- edit 支持修改标题、截止日期、象限、完成状态
- GUI 添加文件监听，CLI 修改数据后界面自动刷新
- 打开 GUI 状态下，CLI 和 GUI 数据实时同步

### v1.2.2 设置界面优化

#### 设置界面重构
- 标题栏与主体区域无缝衔接，主体区域外圈添加 1px 黑色边框
- 去除主体区域内部元素的独立边框
- 日期 spinbox 改为纯数字输入框
- 截止日期配置区域结构重组为 6 行：已过期、即将到期、近期、中期、远期、无日期
- 日期阈值键名重命名（`urgent`/`short_term`/`medium_term`/`long_term`）更清晰

#### 字体设置预览
- 设置界面添加字体大小调节按钮（与主界面同步）
- 实时预览字体变化效果
- 取消时自动恢复原始设置

#### 架构改进
- 设置对话框支持 `font_size` 和 `on_font_size_change` 回调参数
- `SettingsDialog` 初始化时从外部传入 `font_size`，保持与主界面字体一致

### v1.2.1 HiDPI 图标修复

- 改用环境变量 `QT_ENABLE_HIGHDPI_SCALING` 和 `QT_SCALE_FACTOR_ROUNDING_POLICY` 启用 HiDPI 支持，替代已弃用的 `AA_EnableHighDpiScaling` 属性
- 图标始终添加 1x 和 2x 两个分辨率版本，Qt 根据当前 DPI 自动选择最合适的版本
- 修复切换图标时只显示左上四分之一的问题
- 支持所有 DPI 缩放比例：100%、125%、150%、175%、200%、225% 等

### v1.2.0 更新内容

#### 代码重构
- **类型提示**：全项目添加 Python Type Hinting，提升 IDE 支持
- **命名规范**：遵循 PEP 8，变量/函数名更具语义
- **撤销系统解耦**：QuadrantPanel 通过公开接口（`push_undo`/`find_task`）操作撤销，消除直接访问内部属性
- **信号槽优化**：所有槽函数添加 `@Slot()` 装饰器，提升性能
- **if/elif 修复**：修复 `_update_widget_fonts` 中的逻辑 bug

#### DPI 自适应
- 所有硬编码像素值改为 DPI 自适应
- 新增 `_px()` / `_logical_to_physical()` 方法自动适配高分辨率屏幕
- 支持 4K 显示器等 HiDPI 设备

#### 架构改进
- 引入 `UndoAction` 类封装动作类型常量，消除字符串硬编码
- 使用 `TYPE_CHECKING` 避免循环导入
- 公共方法添加 Docstrings 文档
- 提取公共函数 `_build_title_section()`、`_create_toolbar_icon_btn()` 减少重复代码
