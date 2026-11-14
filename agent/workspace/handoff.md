# 工作交接

更新时间：2026-11-16。分支：`dev`。本轮基线：`b3bc049`。当前发布：`v0.12.0`（`8ecc865`）。

## 当前状态

「标签发布流程」已实现，评审的 Standards / Spec 问题已收口。改动留在工作区，按用户要求未提交、未推送。

- 范围：pytest、Ruff、前端检查、e2e 和实际启动验证留在本地；GitHub Actions 只在 `v*` 标签构建发布包并创建 Release，不跑测试，也不做启动冒烟。
- `.github/workflows/release.yml`：`v*` 标签触发，标签过滤器排除带 `-` 的预发布标签；checkout → setup Python → 校验标签/`VERSION`/CHANGELOG → setup Node → 建 venv → `build.bat` → package → 从 `assets.txt` 读取附件 → `gh release create`。
- `scripts/release.py`：`validate`、`stage`、`package`。`stage` 把 `README.md`、`CHANGELOG.md`、`.env.example` 复制到 `dist`，白名单只在脚本定义；`package` 生成 zip、`SHA256SUMS.txt`、`release-notes.md`、`assets.txt`。发布说明只取 CHANGELOG 段落；CHANGELOG 标题兼容 `-` 与 `—`；下载指引、比较链接和仓库参数已移除。
- `scripts/build.bat`：前端构建前执行 `npm ci`；第 5 步调用 `release.py stage`，不再自己维护分发文件列表。
- `tests/scripts/test_release.py`：17 项，全部带类型注解；原 `tests/scripts/conftest.py` 已删除，`scripts` 路径统一由 `tests/conftest.py` 注入。
- `requirements-dev.txt` 增加 `pytest`、`ruff`；`docs/DEVELOPMENT.md` 增加发布前本地检查（含运行 `dist\Tunalo.exe` 验证设置窗口、托盘和 WE 连接）和标签发布步骤；`docs/index.md` 同步开发文档范围；`docs/TODO.md` 状态改为本地实现完成、待标签发布确认。
- 未修改应用、API、配置格式和 `CHANGELOG.md`。

## 验证

- 全量 pytest：424 项通过，158.38 秒（较上轮新增 2 项 `stage` 测试）。
- `pytest tests\scripts -q`：17 项通过。
- `python -m ruff check .`、`python -m ruff format --check .`：通过，123 个文件。
- `actionlint` 1.7.12：`release.yml` 通过。
- `.\scripts\build.bat --no-pause`：完整构建通过；`npm ci` 安装 480 个包；`stage` 复制 4 个分发文件到 `dist`。
- `release.py package --tag v0.12.0`：zip、`SHA256SUMS.txt`、`release-notes.md`、`assets.txt` 均生成；zip 只含 `Tunalo.exe`、README、CHANGELOG、`.env.example`；`assets.txt` 两行路径经 PowerShell 展开后顺序正确。
- e2e：本地 68 项通过（本轮未改前端）。
- `git diff --check`：通过。
- 尚未在 GitHub 上触发 Actions；`gh release create` 未真实执行。

## 后续工作

1. 审阅工作区改动；确认后提交并推送。
2. 下一次发版按 `docs/DEVELOPMENT.md` 执行：本地测试、Ruff、构建并运行 exe 验证，更新 `VERSION` 与 CHANGELOG，推送 `v*` 标签；首轮验证 `release.yml` 与 Release 附件。
3. 若之后确实需要把额外检查搬进 Actions，再按需增补，不默认扩张。
