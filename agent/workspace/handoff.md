# 工作交接

更新时间：2026-11-03。
分支：`codex/frontend-adjustments`。
当前基线：`ab29206`（时间提示补全英文）。用户已批准第 1 项修复，并授权按问题分批提交后续修复。

## 当前任务

按[外部 UI/UX 验收记录](../../docs/UI-UX-验收记录-2026-11-02.md)分批修复前六项问题。第 1 项场景弹窗草稿保护已通过验证和用户审阅。下一批处理第 2 项选中状态辨识，第 3—6 项保持待修。

三项时间说明和帮助按钮名称的英文补全已进入基线。用户明确要求导航保持简洁，不显示“可跳过／沿用默认”；确有必要时，用 `*` 标明必选项。

## 本批行为

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

继续处理报告第 2 项选中状态辨识。第 3—6 项分别为失效播单计数、检查页问题位置、必填字段就近反馈、优先级分区。每项独立验证和提交。

此前已验收的本地昼夜计算和天气提醒见[本地昼夜计算规格](../../docs/archived/done/LOCAL_SUN_TIMES_SPEC.md)、[天气提醒规格](../../docs/archived/done/WEATHER_REMINDER_SPEC.md)。
