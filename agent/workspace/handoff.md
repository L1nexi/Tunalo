# 工作交接

更新时间：2026-11-17。分支：`dev`。当前基线：`0caeb35`（第一批后端）；第二批与导航重构已提交 `e06f810`；本轮「首次设置可达性」改动保留在工作区。任务起点为 `f8d852f`。

## 当前任务

实现 [TODO](../../docs/TODO.md) 的开机启动开关。用户已确认逻辑层方案，以及新增「应用设置」页的布局：导航入口位于列表首项，开关放在正文，修改即时生效，该页底栏只显示「关闭」。

两批实现完成后，用户实测只看到首次设置窗口，报告「开机启动按钮没生效」。排查确认开关本身正常，原因是导航只在设置模式插入「应用设置」，而本机没有 profile，窗口始终停在首次设置。用户评审后选择让首次设置也能进入该页（本轮改动，未提交）。

## 第一批已完成

- 新增 [app/autostart.py](../../src/app/autostart.py)。`build_autostart_command(executable, config_dir, script=None)` 生成绝对路径命令：发布版运行当前 exe，源码版运行同目录的 `pythonw.exe` 和入口脚本，并保留配置目录。
- `AutostartRegistration.is_enabled()/set_enabled()` 管理当前用户 `Software\Microsoft\Windows\CurrentVersion\Run` 下的 `Tunalo` 值。状态以命令是否匹配当前程序及配置目录为准；遇到旧路径时显示未启用，读取不会自动改写。启用时替换该值，关闭时允许启动项已不存在。布尔值与启动命令校验失败时保留已有注册项。
- [app/main.py](../../src/app/main.py) 将实际配置目录通过 `--config` 传给设置和首次配置窗口子进程；窗口入口构造启动项管理器并注入 `AppWindow`。
- [ui/webview.py](../../src/ui/webview.py) 的原生桥接增加 `get_autostart() -> bool`、`set_autostart(enabled: bool) -> None`。注册表访问失败继续抛出异常，供页面处理；开关不进入 Profile 的保存与应用流程。
- 新增 [tests/app/test_autostart.py](../../tests/app/test_autostart.py) 的 14 项测试，通过公开接口验证注册状态、旧路径替换、重复操作与无效输入；包含带空格路径的命令和实际 `pythonw.exe` 子进程启动。测试使用独立临时注册表分支，结束后删除，不写真实的 Windows 启动项。

配置格式与调度逻辑保持原有职责，启动项由原生桥接独立管理。

## 第二批已完成

- [ApplicationSettings.vue](../../frontend/src/setup/application/ApplicationSettings.vue) 提供一行「开机启动」设置，左侧为名称和说明，右侧为开关。导航入口位于列表首项，首次设置与设置模式都显示；[SetupFooter.vue](../../frontend/src/setup/workspace/SetupFooter.vue) 在设置模式的应用设置页只显示「关闭」，首次设置下保留「查看配置草稿」入口。页面切换保留原 Profile 草稿。
- [autostart.ts](../../frontend/src/autostart.ts) 管理窗口内的读取与保存状态。读写期间禁用开关，写入成功后更新显示；失败时保留原状态并提供重试。保存状态跨页面保留；原生桥接延迟就绪后会重新读取。浏览器环境说明需在桌面窗口中修改，不写入本地存储模拟开机启动。
- [useSetupWindow.ts](../../frontend/src/setup/workspace/useSetupWindow.ts) 关闭前等待启动项与外观写入完成，覆盖等待一项时又修改另一项的情况。放弃 Profile 草稿保留已经保存的开关状态。
- 新增 [Switch 组件](../../frontend/src/components/ui/switch/Switch.vue)，复用现有 Reka UI 2.10.5 和 `@/lib/utils`。安装器附带的外部字体与依赖升级已清除，包清单与全局样式没有变更。
- [workspace.ts](../../frontend/src/setup/copy/workspace.ts) 补齐中英文文案，[pywebview.d.ts](../../frontend/src/types/pywebview.d.ts) 声明两项原生接口；[页面测试](../../frontend/e2e/autostart.spec.ts) 覆盖新功能，测试桥接沿用原有调用方式并扩展开机启动接口。
- 中文开关说明按用户审阅意见改为「开机后静默启动托盘运行。」；对应页面测试同步更新。
- README 增加使用入口与移动程序后的操作说明，CHANGELOG 的 `[Unreleased]` 增加用户可见变化，TODO 标为实现完成并注明待审阅与待实测范围。

## 审阅后的导航重构

- `useStepNavigation.ts` 改为 [useSetupNavigation.ts](../../frontend/src/setup/workflow/useSetupNavigation.ts)，用 `PageId = StepId | "application"` 统一页面选择。对外提供只读的 `activePage` 与 `previousPage`，通过 `navigateTo(id, focus)` 统一处理页面切换、滚动和焦点。Profile 的校验与缺失项仍只使用 `StepId`。
- [SetupSidebar.vue](../../frontend/src/setup/workspace/SetupSidebar.vue) 直接从现有设置会话取得导航列表和当前页面，点击后调用统一导航。删除专门的应用设置导航事件，以及用 `undefined` 表示应用设置选中的做法。
- [SetupWorkspace.vue](../../frontend/src/setup/workspace/SetupWorkspace.vue) 只创建会话并组织布局，删除 `applicationOpen`、`showStep()` 和 `showApplication()`，不再转发侧栏事件或决定显示哪类页面。
- `SetupStepContent.vue` 改为 [SetupPageContent.vue](../../frontend/src/setup/workspace/SetupPageContent.vue)，与底栏共同读取 `activePage`。底栏不再接收应用设置标志；[useSetupFeedback.ts](../../frontend/src/setup/workflow/useSetupFeedback.ts) 的校验跳转也通过统一导航，消除直接改写页面状态和重复调用焦点处理。
- 页面历史记录实际来源。从应用设置进入配置检查后，「返回设置」回到应用设置；新增公开页面测试，并在 CHANGELOG 记录这处可见变化。

## 首次设置可达性调整

- [useSetupNavigation.ts](../../frontend/src/setup/workflow/useSetupNavigation.ts) 的导航列表在两种模式都从「应用设置」开始，`navigateTo` 不再拦截首次设置下的应用设置页。开关不参与 Profile 校验，导航项也不显示步骤状态。
- [SetupFooter.vue](../../frontend/src/setup/workspace/SetupFooter.vue) 在首次设置的应用设置页保留右侧「查看配置草稿」：该页原本只剩「取消」，进去后没有回到流程的入口。
- [ApplicationSettings.vue](../../frontend/src/setup/application/ApplicationSettings.vue) 不接收 `mode`，开关说明在两种模式统一为「登录 Windows 时静默启动。」；组件只负责写入与反馈，页面是否出现由导航决定。
- [workspace.ts](../../frontend/src/setup/copy/workspace.ts) 增加中英文说明；页面测试改为覆盖首次设置下的入口、底栏按钮、说明行与开关写入；CHANGELOG、README、TODO 同步。

## 验证

- 第一批 `.\scripts\test.ps1 -q`：428 项通过，14 项调参工具测试按脚本默认规则排除。相关 Python 文件的 Ruff 检查与格式检查通过，`main.py --help` 正常退出。第二批未修改 Python。
- 导航重构后在 `frontend/` 执行 `npm run test:e2e -- --reporter=line --workers=2`：87 项全部通过，包含 15 项开机启动及导航测试，以及原有页面回归。
- `npm run type-check`、`npm run build-only` 通过。
- 用户调整中文说明后，重跑对应页面用例（`autostart.spec.ts --grep 开机启动独立即时保存`）：1 项通过；重新构建前端通过。
- Impeccable 对导航重构修改的四个 Vue 界面文件运行 `detect --json`，结果为空。
- 已查看 1280px 中文浅色页面与 320px 英文深色页面的浏览器截图；窄屏无横向溢出，键盘可切换开关。原生窗口测得标题 24px、说明 14px、设置行宽 760px，沿用项目的 Windows 字体。
- 使用构建后的前端及真实 `AppWindow`、原生桥接和临时注册表分支，验证开启、页面重载后回填、再次关闭，以及无效输入产生 Promise 拒绝。另用超长启动命令验证写入失败后页面提示并保留关闭状态。两次验证均未写入真实 Windows 启动项。
- 导航重构后，用最新构建再次通过原生窗口验证开启、重载回填与再次关闭。退出时 WebView 临时缓存清理遇到文件占用，后续清理被环境自动审批拦截，临时缓存保留在系统临时目录。
- 首次设置可达性调整后：`npm run test:e2e -- --reporter=line --workers=2` 87 项通过；`npm run type-check`、`npm run build-only` 通过；页面截图确认首次设置下导航首项为「应用设置」，底栏为「取消」与「查看配置草稿」，开关说明与设置模式一致。
- `git diff --check` 通过。

## 待审阅与待实测

- 等待用户审阅本轮首次设置可达性调整的工作区改动，并决定是否提交。
- 尚未构建发布 exe，未执行 Windows 注销重登，也未核对系统设置或任务管理器另行禁用启动项后的表现。首次设置期间开启且未完成设置时，登录会再次打开首次设置窗口，这一表现待用户确认。

应用内更新继续暂缓，调查保留在 [IN_APP_UPDATE_OPTIONS.md](../../docs/half-finished/IN_APP_UPDATE_OPTIONS.md)，尚未确定实施方案。上一轮天气连接提示已在基线提交 `f8d852f` 中。
