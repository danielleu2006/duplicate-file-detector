# TODO — Duplicate File Detector

---

## 当前优先级最高

- [ ] 在真实大文件夹上测试性能（1 万+ 文件）
- [ ] 确认 macOS / Linux GUI 正常运行（含缩略图 / ffmpeg 路径）

## 接下来可以做

- [ ] 感知哈希（pHash）支持 — 检测视觉相似的图片（即使字节不同）
- [ ] 硬链接去重 — 用硬链接替代重复文件（节省空间但保留路径）
- [ ] 独立的全屏预览面板 — 文本 / PDF 等（当前仅有列表 + 缩略图视图）
- [ ] 扫描进度文件计数 — Phase 1 也显示进度（当前只显示哈希进度）
- [ ] 递归深度限制 — `--max-depth` 选项
- [ ] 排除模式 — `--exclude` 支持通配符（如 `*.tmp`, `*.log`）
- [ ] 多路径扫描 — 同时扫描多个文件夹
- [ ] 增量扫描 — 记住已哈希的文件，仅扫描新增/修改的文件
- [ ] GUI 暗色主题 — 跟随 Daniel 其他项目的深色日志风格
- [ ] PyInstaller 打包 — 独立可执行文件分发
- [ ] 视频缩略图异步后台解码 — 避免大量视频阻塞 UI 线程

## 以后再做

- [ ] 拖放文件夹到 GUI 窗口
- [ ] 系统托盘集成
- [ ] 右键菜单集成（Windows 资源管理器）
- [ ] 扫描结果对比（两次扫描之间新增/消失的重复）
- [ ] 网络驱动器优化（缓存哈希结果）

## 已完成

- [x] CLI 扫描引擎（3 层策略：大小 → SHA-256 → 分组）
- [x] CLI 接口（argparse，`--json` / `--delete` / `--stage` / `--skip` 等）
- [x] Tkinter GUI（扫描设置、结果树、复选框、删除/移动/导出）
- [x] Keeper 启发式：`stem_suggests_copy` → **更短 basename** → mtime → 名字字典序
- [x] GUI **View**：List / Thumbnails / Grid / List + preview；设置持久化 `results_view_mode`
- [x] 滚轮滚动模式切换：`Smooth Scroll`（units / fast multi-units）并持久化 `smooth_scroll`
- [x] 大结果 Grid/Thumbnails 分批渲染（默认 80 组）+ `Load more`，避免长列表空白页
- [x] 缩略图预览（Pillow 可选）：图片 + ffmpeg 首帧视频（ffmpeg 在 PATH）
- [x] 依赖状态提示（GUI 底部显示 Pillow / FFmpeg 可用性）
- [x] 基于相对路径的统一勾选状态（列表与缩略图模式同步）
- [x] JSON 导出含 `copy_style_name`；CLI 报告标注 keeper / duplicate 原因
- [x] 删除操作（GUI + CLI，确认提示）
- [x] 移动到暂存目录（保留目录结构）
- [x] JSON 导出
- [x] 进度条 + 取消支持
- [x] 设置持久化（窗口位置、路径、选项、视图模式）
- [x] 默认跳过目录列表（.git, node_modules 等）
- [x] `--delete` / `--stage` 互斥校验
- [x] 代码审查修复（线程安全、stderr 等）
- [x] 完整用户手册（USER_MANUAL.md）
- [x] 项目笔记（PROJECT_NOTES.md）
- [x] TODO 追踪（本文件）
- [x] Bug：删除后重新扫描若无重复，Results 面板不刷新
- [x] Bug：取消扫描误报 “No duplicate files found!” → “Scan was cancelled”
