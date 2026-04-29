# Project Notes — Duplicate File Detector

## 项目概述

重复文件检测器（Duplicate File Detector）— Python + Tkinter 跨平台工具

- 快速检测文件夹中的重复文件
- 支持 **GUI**（Tkinter）和 **CLI**
- 核心扫描：**仅标准库**（`dedup.py`：hashlib、os.walk 等）
- GUI 缩略图 / 视频首帧：**可选** 安装 **Pillow**、系统 **PATH** 上的 **ffmpeg**

## 技术栈

- Python 3.10+（`set[str]`、`Path.is_relative_to()`）
- Tkinter + ttk（GUI）
- hashlib（SHA-256）
- threading（GUI 后台扫描）
- JSON（`~/.dedup/settings.json`）
- **可选：** Pillow（图片缩略图）、ffmpeg（视频首帧 PNG pipe）

## 架构

```
dedup.py              ← 核心扫描引擎 + CLI（sort_paths_for_keep、报告、删除/移动）
dedup_gui.py          ← Tkinter GUI（多视图、缩略图、勾选同步）
settings.py           ← JSON 设置持久化（含 results_view_mode）
```

### 模块职责

- **dedup.py**：三层策略（大小 → SHA-256 → 分组）、`stem_suggests_copy`、`sort_paths_for_keep`、CLI、`json_report`（含 `copy_style_name`）、`log_callback` / `progress_callback` / `cancel_event` 供 GUI
- **dedup_gui.py**：扫描设置、**View**（List / Thumbnails / Grid / List + preview）、树视图与缩略图、**\_selected_rel_paths** 勾选、删除/移动/导出、底部依赖状态（Pillow/FFmpeg）、工作线程 + `root.after()` 更新 UI
- **settings.py**：`~/.dedup/settings.json`（路径、选项、`results_view_mode`、窗口几何）

## 已决定的事情

- 使用 3 层比较策略（大小 → 哈希 → 分组），空文件（0 字节）跳过
- SHA-256；keeper：**非 `(n)`/`-n` 副本样式 stem** → **更短 basename** → 更旧 mtime → 名字字典序
- GUI 工作线程不直接读 Tk 变量（主线程捕获后传入）
- `--delete` 与 `--stage` 互斥
- 设置存 `~/.dedup/settings.json`
- 不做感知哈希（pHash），仅精确字节级重复

## 不要做的事情

- 不做感知哈希 / 图像相似度（未来可扩展）
- 不做多根目录同时扫描（单根递归）
- 不做实时目录监听
- 不做硬链接替代去重（仅检测 + 删除/移动）

## 风险 / 注意事项

- 大目录哈希阶段 I/O 密集
- `--follow-symlinks` 注意 symlink 环
- Windows 文件锁定 → 已 try/except
- 大量视频首帧：当前同步调用 ffmpeg，可能拖慢 UI（见 TODO）

## 文件清单

- `dedup.py`、`dedup_gui.py`、`settings.py`
- `README.md`、`USER_MANUAL.md`、`PROJECT_NOTES.md`、`TODO.md`

## 变更日志

### 2026-04（GUI 视图与预览）

- **View**：List / Thumbnails / Grid / **List + preview**（选中组可视化对比）
- 缩略图：Pillow 打开图片；ffmpeg 管道输出 PNG 首帧用于常见视频扩展名
- 勾选集使用相对路径字符串集合，列表与缩略图模式一致

### 2026-04（Keeper 规则）

- 同哈希组内：**非副本样式 stem** → **更短 basename** → **mtime** → **字典序**
- CLI / GUI / JSON 对齐；GUI **Note** 列：`copy-style name`、`longer name` 等

### 2025-07（初始版本）

- CLI + GUI；三层扫描、SHA-256、树视图、暂存/删除、JSON、进度、取消、设置持久化

### 2025-07（Bug 修复 #1）

- 无重复扫描结果时清空 treeview（避免旧数据残留）
- 备注：原笔记中的 `_selected_items` 已改为路径集合 **`_selected_rel_paths`**

### 2025-07（Bug 修复 #2）

- 取消扫描显示 **Scan was cancelled**，不误报无重复
