# 工作交接

更新时间：2026-11-04。分支：`codex/frontend-adjustments`。本轮基线：`210e2ee`。修复起点：`ab29206`（时间提示补全英文）。

## 当前状态

本轮补齐代码审查发现的 P2：全部播单不可用时，检查页的失效绑定入口改为聚焦目标场景的编辑按钮，使首屏外的场景进入视野。有可用播单时仍聚焦播单选择器。用户已审阅通过，本次提交包含修复及两项回归。

[外部 UI/UX 验收记录](../../docs/UI-UX-验收记录-2026-11-02.md)中的六项问题均已修复。用户已审阅第 1 项，并授权自行按问题分批提交后续修复。

| 项目 | 提交 |
| --- | --- |
| 1. 场景草稿关闭保护 | `7c0c3a5` |
| 2. 选中状态辨识 | `eddedfb` |
| 3. 失效播单计数与定位 | `6cfa5ec` |
| 4. 检查页待处理事项前置 | `b14b436` |
| 5. 密钥必填字段就近反馈 | `620e984` |
| 6. 优先级与未分配区分开 | `210e2ee` |

三项时间说明和帮助按钮名称的英文补全已进入基线。导航继续保持简洁，不显示“可跳过／沿用默认”；确有必要时，用 `*` 标明必选项。

## 行为和源码入口

- 场景临时修改计入窗口关闭判断；Esc 对修改过的弹窗先确认，继续编辑保留内容和焦点，显式取消直接清除本次编辑。放弃弹窗编辑保留主页面修改。窗口确认框显示在场景弹窗之上，并正确恢复焦点。入口为 `frontend/src/setup/scenes/SceneEditor.vue`、两种场景表单、`profile/useProfileDraft.ts`、`workspace/SetupConfirmations.vue`。
- 场景关联、预设分类、防打扰档位和语言选择统一使用主色实底表示选中，悬停保持浅灰底。入口为 `frontend/src/components/ui/toggle/index.ts`、`toggle-group/ToggleGroupItem.vue`、`frontend/src/setup/workspace/SetupSidebar.vue`。
- 摘要、场景页和提交校验共用 `playlistBindingStatus(playlist, available)`，区分有效、未绑定和失效绑定。检查页接收当前可用播单，显示失效数量；零场景显示“尚未添加场景”。问题入口跳到对应场景，有可用播单时聚焦选择器，全部不可用时聚焦场景编辑按钮。入口为 `frontend/src/setup/profile/model/scenes.ts`、`review/summary.ts`、`ReviewStep.vue`、`workspace/SetupStepContent.vue` 和场景播单选择器。
- 已有问题列表移到检查页标题下，修正入口沿用原有校验和焦点行为，底部保持原有按钮布局。
- 密钥实际编辑并离开输入框后启用必填提示。首次空白表单及未经编辑的聚焦、离开保持安静。切换设置项保留反馈，补全密钥后即时清除。`WeatherKeyStep.vue` 增加 `blur` 事件，`useWeatherServices.ts` 提供 `apiKeyTouched` 与 `touchApiKey()`，由 `SetupWeatherContent.vue` 连接；联网测试反馈继续独立处理。
- 编号优先级连续排在上方，“添加层级”紧随其后；未指定情境独立放在下方，用留白及原有说明区分。层级重排使用调整后的索引，拖动、菜单、键盘操作和 Profile 中的偏好语义保持原状。入口为 `frontend/src/setup/scheduling/PreferenceTiersEditor.vue` 和 `copy/preferences.ts`。

后端、Profile 格式、原生关闭事件和真实运行配置保持原状。

## 验证

| 检查 | 结果 |
| --- | --- |
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过 |
| 本轮：`npm run test:e2e -- e2e/review.spec.ts --reporter=line --workers=2` | 8 项全部通过，29.5 秒 |
| 前轮：`npm run test:e2e -- --reporter=line --workers=2` | 63 项全部通过，59.7 秒 |
| `git diff --check` | 通过 |

本轮新增两项回归，分别覆盖全部播单删除、全部播单清空。在 900×600 视口中创建 12 个场景，点击最后一个场景的失效绑定入口，检查目标场景完整进入视野且编辑按钮获得焦点；选择器继续保持禁用。两个用例均先在修复前复现失败，再验证修复后通过。变更文件为 `frontend/src/setup/workspace/SetupStepContent.vue` 和 `frontend/e2e/review.spec.ts`。

前轮对关闭保护、失效播单计数、首屏入口、密钥失焦反馈和优先级顺序先用回归复现，再完成修复后的定向验证。新增回归共 16 项，覆盖弹窗和窗口关闭、浏览器关闭提示、播单改名及删除、内容清空、零场景、具体场景定位、检查页首屏入口、密钥失焦反馈、优先级顺序和层级重排。测试通过公开页面操作及外部 API、原生桥接替身观察行为。

选中态与相邻背景的对比度：浅色约 5.09:1，深色约 7.82:1；选中文字分别约 4.87:1、8.63:1。界面验证覆盖中英文、深浅主题、1200×780、900×600、800×520 和 320px 窄窗口，包含生产构建走查；检查键盘焦点、修正入口、无横向溢出及悬停区别。

验证使用 2 并发。此前默认 6 并发运行出现过原有用例超时，降低并发后全量通过。本地预览和走查浏览器均已关闭。

截图保存在本次 Codex 会话的 `tunalo-audit-fixes` 可视化目录：`selection-light.png`、`selection-dark.png`、`unavailable-binding.png`、`review-issues-first-800.png`、`api-key-required-zh.png`、`api-key-required-en.png`、`priorities-zh.png`、`priorities-en.png`。关闭保护的截图与事件结果见上一批的 `tunalo-scene-draft-fix` 目录。

## 待联调

真实 WebView2 标题栏关闭、Alt+F4 和 Windows DPI 缩放仍待实机联调；浏览器中的原生事件模拟已覆盖前端处理器及桥接出口。本轮验证使用模拟本地 API，未替代真实天气联网和实际壁纸切换验收。

此前已验收的本地昼夜计算和天气提醒见[本地昼夜计算规格](../../docs/archived/done/LOCAL_SUN_TIMES_SPEC.md)、[天气提醒规格](../../docs/archived/done/WEATHER_REMINDER_SPEC.md)。
