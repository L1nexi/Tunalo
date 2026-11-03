# 工作交接

更新时间：2026-11-03。
分支：`codex/frontend-adjustments`。
修复起点：`ab29206`（时间提示补全英文）。第 1 项已提交为 `7c0c3a5`。用户已授权按问题分批提交后续修复。

## 当前任务

按[外部 UI/UX 验收记录](../../docs/UI-UX-验收记录-2026-11-02.md)分批修复前六项问题。第 1 项场景弹窗草稿保护已通过验证和用户审阅。第 2 项已提交为 `eddedfb`，第 3 项失效播单计数随本次提交完成，第 4—6 项保持待修。

三项时间说明和帮助按钮名称的英文补全已进入基线。用户明确要求导航保持简洁，不显示“可跳过／沿用默认”；确有必要时，用 `*` 标明必选项。

## 第 3 项：失效播单计数

摘要、场景页和提交校验共用 `playlistBindingStatus(playlist, available)`，区分有效、未绑定和失效绑定。检查页接收当前可用播单，显示失效数量；零场景显示“尚未添加场景”。问题入口可跳到对应场景并聚焦播单选择器。

类型检查、生产构建和 8 项检查页及首次设置回归通过。其中新增 5 项，覆盖播单改名、删除、内容清空、零场景和英文提示。已在生产界面核对失效摘要及焦点定位，截图为 `tunalo-audit-fixes/unavailable-binding.png`。

## 第 2 项：选中状态辨识（已提交）

场景关联、预设分类、防打扰档位和语言选择统一使用主色实底表示选中，悬停继续使用浅灰底。移除语言控件覆盖选中底色的例外。组件参数、事件和交互逻辑保持原状。

修改 `frontend/src/components/ui/toggle/index.ts`、`toggle-group/ToggleGroupItem.vue` 及 `frontend/src/setup/workspace/SetupSidebar.vue`。类型检查、生产构建和 23 项相关浏览器测试通过。浅色选中态与弹窗背景对比度约 5.09:1，深色约 7.82:1；选中文字分别约 4.87:1、8.63:1。已检查悬停区别和键盘切换。截图见本次会话 `tunalo-audit-fixes/selection-light.png`、`selection-dark.png`。

## 第 1 项：场景关闭保护（已提交）

- 新建、编辑场景以及预设选择产生的临时修改，都参与窗口关闭判断。只修改弹窗时，原生关闭请求也先询问是否放弃。
- 按 Esc 时，有修改则确认放弃；选择“继续编辑”保留内容和焦点，选择“放弃修改”只清除弹窗编辑。显式“取消”直接清除本次编辑。
- 未编辑或已还原为原内容时直接关闭。关联标签的排列顺序变化按既有规范化比较处理。
- 主页面和弹窗同时修改时，窗口关闭使用同一个确认。放弃弹窗编辑仍保留主页面修改。
- 窗口确认框在打开时挂载，显示在场景弹窗之上；确认框和场景弹窗分别恢复到正确的输入位置或原操作按钮。

## 源码与接口

- `frontend/src/setup/profile/useProfileDraft.ts`：增加 `pendingSceneChanges`，并计入 `isDirty`。
- `frontend/src/setup/scenes/SceneDetailsForm.vue`、`ScenePresetForm.vue`：增加 `dirty(changed: boolean)` 事件，报告当前表单是否有临时修改。
- `frontend/src/setup/scenes/SceneEditor.vue`：汇总表单修改状态，处理 Esc 确认、取消和焦点恢复；卸载时清除临时标记。
- `frontend/src/setup/workspace/SetupConfirmations.vue`：修正窗口确认框的挂载顺序和焦点恢复。
- `frontend/src/setup/copy/scenes.ts`：增加中英文场景放弃确认文案。
- `frontend/e2e/scene-editor.spec.ts`：新增 7 项行为回归，包含真实浏览器关闭提示；原生关闭沿用现有桥接替身。

本批沿用现有 Profile、API 和原生关闭事件，后端及真实运行配置保持原状。

## 验证

| 检查 | 结果 |
| --- | --- |
| 原问题回归 | 修复前复现只编辑弹窗时绕过确认；修复后通过 |
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过 |
| `npm run test:e2e -- --reporter=line --workers=2` | 54 项通过，约 1.7 分钟 |
| 生产界面走查 | 1200×780 中文浅色、320×720 英文深色；确认框可操作、键盘焦点返回、窄窗口无横向溢出，无页面脚本错误 |
| `git diff --check` | 通过 |

默认 6 并发运行时，appearance、activity 各有一条原有用例超时。停止该次运行后，以 2 并发重跑，54 项全部通过。

截图和走查结果保存在本次 Codex 会话的 `tunalo-scene-draft-fix` 可视化目录，文件包括 `native-close-light.png`、`scene-discard-light.png`、`scene-discard-dark-320-en.png` 和 `results.json`。本地预览和走查浏览器均已关闭。

## 后续事项

真实 WebView2 标题栏关闭、Alt+F4 和 Windows DPI 缩放仍待实机联调；浏览器中的原生事件模拟覆盖前端处理器及桥接出口。

继续处理报告第 4 项检查页问题位置。第 5—6 项分别为必填字段就近反馈、优先级分区。每项独立验证和提交。

此前已验收的本地昼夜计算和天气提醒见[本地昼夜计算规格](../../docs/archived/done/LOCAL_SUN_TIMES_SPEC.md)、[天气提醒规格](../../docs/archived/done/WEATHER_REMINDER_SPEC.md)。
