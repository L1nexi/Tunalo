# 工作交接

更新时间：2026-11-18。分支：`dev`。重构起点：`d4cdc48`。本轮页面规则重构已通过代码审查和用户确认，随本次提交收尾。

## 当前任务

开机启动功能引入了即时保存的「应用设置」页，但导航、正文和底栏分别维护 `application` 的特殊规则。本轮按用户确认的范围，把这些规则集中到页面描述，保持现有用户行为。

用户确认这是一般重构，无需新增 ADR。文档索引和 CHANGELOG 不变；改动包含 8 个前端源码文件、2 个页面测试文件、本交接记录及 [TODO](../../docs/TODO.md) 的状态更新。

## 本轮完成

- 新增 [workflow/pages.ts](../../frontend/src/setup/workflow/pages.ts)，提供 `PageId`、`PageDefinition` 和 `createSetupPages(locale, mode)`。页面顺序、导航标题、图标、正文标题和说明、宽度、Profile 步骤归属、反馈范围及底栏动作均在这里定义。
- [useSetupNavigation.ts](../../frontend/src/setup/workflow/useSetupNavigation.ts) 组合页面描述和 Profile 状态，提供 `currentPage` 与带图标的 `navigationItems`。`activePage`、`previousPage` 继续返回页面 ID；`navigateTo(id, focus)` 的签名和页面历史行为不变。删除旧的 `activeHeading`、`contentClass` 输出。
- [steps.ts](../../frontend/src/setup/workflow/steps.ts) 删除 `WIDE_STEPS`，保留 Profile 步骤、校验和字段归属；[useSetupFeedback.ts](../../frontend/src/setup/workflow/useSetupFeedback.ts) 仅调整 `PageId` 导入。
- [SetupSidebar.vue](../../frontend/src/setup/workspace/SetupSidebar.vue) 删除独立图标表；[SetupWorkspace.vue](../../frontend/src/setup/workspace/SetupWorkspace.vue) 从当前页面描述读取标题和说明。
- [SetupPageContent.vue](../../frontend/src/setup/workspace/SetupPageContent.vue) 根据页面描述决定宽度和 Profile 反馈是否显示。应用设置与其它页面处于同级内容选择分支。[SetupFooter.vue](../../frontend/src/setup/workspace/SetupFooter.vue) 根据页面描述渲染底栏动作，按钮禁用状态继续读取提交、校验和草稿状态。
- 导航和底栏不再判断 `application`。即时写入逻辑、原生桥接、窗口关闭等待、Profile 格式及后端均未改动。

## 测试与验证

新增测试继续通过设置窗口的用户操作验证行为，只在 HTTP 和原生桥接处沿用现有替身，不测试页面描述的内部字段。

- [autostart.spec.ts](../../frontend/e2e/autostart.spec.ts) 将返回来源页的用例扩展到首次设置和设置两种模式；新增 Profile 待处理反馈与应用设置互不影响、返回后保留草稿的用例。
- [workspace.spec.ts](../../frontend/e2e/workspace.spec.ts) 覆盖两种模式下三类页面的底栏组合、中英文切换及返回焦点。原自启测试中重复的底栏断言移到这里。
- `npm run type-check`：通过。
- 第一阶段运行 `npm run test:e2e -- e2e/autostart.spec.ts e2e/workspace.spec.ts e2e/review.spec.ts --reporter=line --workers=2`：原有 28 项通过。
- 全量运行 `npm run test:e2e -- --reporter=line --workers=2`：90 项通过，新增反馈隔离用例失败。该用例收窄了提示定位范围，并将同页提交的额外焦点断言改为检查字段无效状态，原因见[后续事项](#后续事项)。
- 修正后运行 `npm run test:e2e -- e2e/autostart.spec.ts --grep 'Profile 待处理反馈' --reporter=line --workers=1`：1 项通过。91 个用例均已有通过结果，修正后未重复运行全量。
- `npm run build-only`、`git diff --check`：通过。
- 已查看两种模式的中文应用设置截图，标题、导航、开关及底栏布局保持原样；320px 英文深色页面的键盘操作与无横向溢出检查由现有用例覆盖。

## 审查与收尾

- `code-review` 分别由独立审查者核对代码规范和需求符合度，两项均为 0 条发现。范围为 `d4cdc48` 至当前工作区，包含新增的 `pages.ts`。
- 审查期间复跑 `npm run type-check`、`git diff --check`，以及 `npm run test:e2e -- e2e/autostart.spec.ts e2e/workspace.spec.ts --grep '返回到实际来源页面|Profile 待处理反馈|三类页面' --reporter=line --workers=2`：检查通过，5 项用例全部通过。
- 已逐段对比 `focusContent()`、`navigateTo()` 和反馈模块的实现，与重构基线一致。
- 用户于 2026-11-18 确认通过，并要求收尾文档和提交。后续焦点问题已登记到 TODO，自启的 Windows 登录实测继续保留为待办。

## 后续事项

- 补测观察到同页校验的焦点时序问题：在活动页填写尚未添加的进程文字，直接点击「保存并应用」，提示和字段无效状态正常出现，但输入框未获得焦点。`focusContent()` 的 `nextTick()` 早于 `stepError` 更新；页面 ID 没有变化时，焦点处理可能先于错误渲染。相关焦点与反馈逻辑本轮未改，未将修复纳入本次重构。跨页返回与纠错焦点继续由现有导航用例覆盖。
- 尚未构建发布 exe，未执行 Windows 注销重登，也未核对系统设置或任务管理器另行禁用启动项后的表现。首次设置中开启自启但未完成配置时，下次登录会再次打开首次设置窗口，这一表现仍待确认。

## 自启实现基线

- `0caeb35`：自启后端及原生桥接，入口将真实配置目录传入窗口子进程。代码入口见 [app/autostart.py](../../src/app/autostart.py)、[app/main.py](../../src/app/main.py)、[ui/webview.py](../../src/ui/webview.py)。
- `e06f810`：应用设置页、独立即时保存、关闭前等待偏好写入，以及页面导航重构。
- `d4cdc48`：首次设置期间也可进入应用设置；该页保留「查看配置草稿」入口。上述三批均已提交，替代旧交接中「首次设置可达性未提交」的状态。
- 上一轮记录：后端常规测试 428 项通过，自启测试使用独立临时注册表分支；真实原生桥接已验证开启、重载回填和关闭。本轮未重跑 Python 测试或原生窗口验证。

应用内更新继续暂缓，调查保留在 [IN_APP_UPDATE_OPTIONS.md](../../docs/half-finished/IN_APP_UPDATE_OPTIONS.md)。
