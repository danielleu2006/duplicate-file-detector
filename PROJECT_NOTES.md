# Project Notes — Duplicate File Detector

## 项目概述

重复文件检测器（Duplicate File Detector）— Python + Tkinter 跨平台工具

- 快速检测文件夹中的重复文件
- 支持 GUI（Tkinter）和 CLI 双界面
- 纯 Python，无外部依赖

## 技术栈

- Python 3.10+（使用 `set[str]` 类型提示和 `Path.is_relative_to()`）
- Tkinter + ttk（跨平台 GUI，标准库）
- hashlib（SHA-256 哈希，标准库）
- threading（GUI 后台扫描线程）
- JSON（设置持久化）

## 架构

```
dedup.py              ← 核心扫描引擎 + CLI 接口
dedup_gui.py          ← Tkinter GUI（入口点）
settings.py           ← JSON 设置持久化（~/.dedup/settings.json）
```

### 模块职责

- **dedup.py**：3 层比较策略（文件大小 → SHA-256 哈希 → 分组报告）、CLI 接口（argparse）、删除/移动操作、JSON 报告生成、`log_callback` / `progress_callback` / `cancel_event` 参数支持 GUI 集成
- **dedup_gui.py**：Tkinter GUI、扫描设置面板、结果树视图（复选框选择）、删除/移动/导出操作、进度条、取消支持、工作线程（线程安全：主线程捕获 Tk 变量后传给工作线程）、设置持久化
- **settings.py**：`~/.dedup/settings.json` 读写、默认值回退、窗口位置记忆

## 已决定的事情

- 使用 3 层比较策略（大小 → 哈希 → 分组），先排除大小不同的文件再哈希
- 使用 SHA-256（而非 MD5），碰撞概率可忽略不计，无需逐字节验证
- 保留最旧文件（按修改时间），删除/移动其余副本
- 空文件（0 字节）始终跳过，避免误报
- GUI 使用工作线程 + `root.after()` 更新 UI，保证线程安全
- `--delete` 和 `--stage` 互斥，CLI 和 GUI 均做校验
- GUI 删除操作需要确认提示（messagebox.askyesno）
- 设置存储在 `~/.dedup/settings.json`（而非平台特定目录，简化实现）
- 不做感知哈希（pHash），仅做精确字节级重复检测

## 不要做的事情

- 不做感知哈希 / 图像相似度检测（超出范围，考虑未来扩展）
- 不做多根目录同时扫描（当前仅支持单个扫描根目录，跨子文件夹重复检测已支持）
- 不做文件内容逐字节对比（SHA-256 碰撞概率可忽略，无需额外验证）
- 不做实时文件监视 / 文件系统监听
- 不做网络驱动器扫描优化
- 不做文件去重（硬链接 / 符号链接替代），仅检测 + 删除/移动

## 风险 / 注意事项

- 大文件夹（10 万+文件）首次扫描可能较慢，哈希阶段受磁盘 I/O 限制
- 符号链接循环可能导致无限递归（`--follow-symlinks` 时需谨慎）
- Windows 上文件可能被锁定（`PermissionError`），已做 try/except 处理
- Tkinter 不是线程安全的，GUI 代码严格遵守"主线程读 Tk 变量"规则

## 文件清单

- `dedup.py` — 核心扫描引擎 + CLI 接口
- `dedup_gui.py` — Tkinter GUI
- `settings.py` — JSON 设置持久化
- `README.md` — 快速入门
- `USER_MANUAL.md` — 完整用户手册（11 章节：概述、安装、快速开始、GUI 指南、CLI 参考、原理、重复处理、设置、跳过目录、排错、架构）
- `PROJECT_NOTES.md` — 本文件
- `TODO.md` — 待办事项

## 变更日志

### 2025-07（初始版本）

- 做了什么：创建重复文件检测工具（CLI + GUI）
- 功能：3 层扫描策略、SHA-256 哈希、复选框树视图、删除/移动操作、JSON 导出、进度条、取消支持、设置持久化
- 技术决定：纯 Python 无外部依赖；Tkinter GUI；`log_callback` / `progress_callback` / `cancel_event` 参数实现 GUI 集成而不重复逻辑

### 2025-07（Bug 修复 #1）

- 修复：删除文件后重新扫描，若无重复文件，Duplicate Results 面板不会刷新（旧结果残留）
- 原因：`_on_scan_complete` 在 `duplicates` 为空时直接显示 messagebox，但未清除 treeview 中的旧数据
- 修复方法：在无重复分支中添加 tree 清除、`_selected_items` 清空、`_update_action_buttons()` 调用
- 备注：跨子文件夹重复检测已确认正常工作（`os.walk` 递归扫描所有子目录），但暂不支持多根目录扫描
