# 工作交接

更新时间：2026-11-17。分支：`dev`。本轮基线：`f8d852f`。开始时工作区干净。

## 当前任务

实现 [TODO](../../docs/TODO.md) 的开机启动开关。用户已确认逻辑层方案，以及新增「应用设置」页的布局：导航入口位于列表首项，开关放在正文，修改即时生效，该页底栏只显示「关闭」。

按用户确认的两批工作区审阅推进，不自动提交。第一批已完成，停在第一个审阅检查点；前端尚未开始。用户审阅第一批后再接页面。

## 第一批已完成

- 新增 [app/autostart.py](../../src/app/autostart.py)。`build_autostart_command(executable, config_dir, script=None)` 生成绝对路径命令：发布版运行当前 exe，源码版运行同目录的 `pythonw.exe` 和入口脚本，并保留配置目录。
- `AutostartRegistration.is_enabled()/set_enabled()` 管理当前用户 `Software\Microsoft\Windows\CurrentVersion\Run` 下的 `Tunalo` 值。状态以命令是否匹配当前程序及配置目录为准；遇到旧路径时显示未启用，读取不会自动改写。启用时替换该值，关闭时允许启动项已不存在。布尔值与启动命令校验失败时保留已有注册项。
- [app/main.py](../../src/app/main.py) 将实际配置目录通过 `--config` 传给设置和首次配置窗口子进程；窗口入口构造启动项管理器并注入 `AppWindow`。
- [ui/webview.py](../../src/ui/webview.py) 的原生桥接增加 `get_autostart() -> bool`、`set_autostart(enabled: bool) -> None`。注册表访问失败继续抛出异常，供页面处理；开关不进入 Profile 的保存与应用流程。
- 新增 [tests/app/test_autostart.py](../../tests/app/test_autostart.py) 的 14 项测试，通过公开接口验证注册状态、旧路径替换、重复操作与无效输入；包含带空格路径的命令和实际 `pythonw.exe` 子进程启动。测试使用独立临时注册表分支，结束后删除，不写真实的 Windows 启动项。

本轮未修改配置格式或调度逻辑。上述改动及本交接记录保留在工作区，尚未提交。

## 验证

- `.\scripts\test.ps1 -q`：428 项通过，14 项调参工具测试按脚本默认规则排除。
- `.venv\Scripts\python.exe -m ruff check src/app/autostart.py src/app/main.py src/ui/webview.py tests/app/test_autostart.py` 通过；同一组文件的 `ruff format --check` 通过。
- `.venv\Scripts\python.exe main.py --help` 正常退出，公开命令行参数保持兼容。
- `git diff --check` 通过。
- 尚未通过原生 WebView 调用新桥接，也未构建发布 exe 或执行 Windows 注销重登验收。

## 第二批已确认范围

- 新增 `frontend/src/setup/application/ApplicationSettings.vue` 和 `frontend/src/autostart.ts`。沿用现有字体与语义颜色，设置行左侧为名称和说明，右侧为开关；处理读取、切换、失败重试和桥接延迟就绪。
- 修改 `SetupSidebar.vue`、`SetupWorkspace.vue` 和 `SetupFooter.vue`，接入独立的应用设置页。仅在设置模式显示，不加入首次配置步骤或 Profile 校验。
- 修改 `useSetupWindow.ts`、`frontend/src/types/pywebview.d.ts` 和 `frontend/src/setup/copy/workspace.ts`，接入桥接类型与中英文文案，关闭前等待启动项写入完成。放弃 Profile 草稿仍保留已写入的开关状态。
- 新增 shadcn-vue `Switch` 组件及导出文件；若安装器修改 `frontend/package.json`、`frontend/package-lock.json`，只纳入该组件所需改动。
- 新增 `frontend/e2e/autostart.spec.ts`，扩展 `frontend/e2e/support/pywebview.ts`；验证即时保存、读写失败重试、重开回填、关闭等待，以及页面切换后保留原草稿。
- 更新 CHANGELOG 的 `[Unreleased]`、README、TODO 和本交接；执行相关前端回归、类型检查与构建，检查渲染后的页面，再进入第二个工作区审阅检查点。

原生验收需核对 Windows 启动项显示、系统侧另行禁用后的表现及登录后静默进托盘。实际注销重登的验证结果单独标明。

应用内更新继续暂缓，调查保留在 [IN_APP_UPDATE_OPTIONS.md](../../docs/half-finished/IN_APP_UPDATE_OPTIONS.md)，尚未确定实施方案。上一轮天气连接提示已在基线提交 `f8d852f` 中。
