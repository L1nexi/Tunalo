# 工作交接

更新时间：2026-11-09。分支：`codex/frontend-adjustments`。当前发布：`v0.12.0`，发布提交：`8ecc865`。

## 当前状态

[`v0.12.0`](https://github.com/L1nexi/Tunalo/releases/tag/v0.12.0) 已正式发布并设为 Latest。应用版本更新为 `0.12.0`，CHANGELOG 按 2026-11-09 定稿，比较链接改用对应标签。发布提交已同步至 `main` 和 `codex/frontend-adjustments`。

本轮补齐以下五个历史标签，并创建当前发布标签；CHANGELOG 中的 25 个已发布版本现均有远程标签。

| tag | 对应提交 |
| --- | --- |
| `v0.5.1` | `824789a` |
| `v0.9.0` | `6210b12` |
| `v0.9.1` | `e135b31` |
| `v0.10.0` | `ef4322f` |
| `v0.11.0` | `867a2d7` |
| `v0.12.0` | `8ecc865` |

`v0.5.1` 落在 Dashboard R1 完成及入口整理之后，下一提交开始添加 `v0.6.0` 的播放列表显示名功能。其余四个历史版本沿用此前确认的落点。

发布附件为 `Tunalo-v0.12.0-windows-x64.zip`（28,448,441 字节）和 `SHA256SUMS.txt`。压缩包只包含 `Tunalo.exe`、README、CHANGELOG 和 `.env.example`；未包含个人配置、数据或日志。发布说明补充了旧 YAML 与第 1、2 版 Profile 需要备份并重新配置的升级说明。

本轮验证：后端 377 项通过（88.61 秒），Ruff 检查与格式检查通过，完整打包通过并重新执行前端类型检查和构建。前端 65 项页面测试沿用本会话界面调整阶段的通过结果，发布阶段未修改界面源码。

EXE 内版本、Windows x64 架构、前端资源和图标逐项核对通过，NumPy／Matplotlib 未打入包。中文及空格目录下，`--help` 返回 0，未知参数返回 2。GitHub 发布状态、Latest 标记、说明正文、附件大小及 SHA-256 均已核对；登录下载和公开链接下载的压缩包都与本地产物一致。

产物与发布验证记录位于 `.pytest_tmp/release-v0.12.0/`，其中 `package-check.json` 记录压缩包信息，`published-check.json` 记录远程附件及标签核对结果。原生 WebView2、Windows DPI、真实天气联网和 Wallpaper Engine 切换仍待后续实机验收。

## 本轮界面调整（已提交 `a31df16`）

用户已审阅并提交截图中的三处界面调整及相关测试。

- `SetupFooter.vue`：取消／关闭按钮改用现有 `outline` 变体。
- `ScenePresetForm.vue`：五个预设分类合为一个 `ToggleGroup`，同行间隔统一为 8px，窄窗口自动换行；保留跨组多选和键盘操作。
- `scenes/presets.ts`、`copy/scenes.ts`、`copy/scene-labels.ts`：改用“时间 x 活动”／“Time x activity”，移除“季节与天气”分类、四个预设及闲置文案。当前共 18 个预设；已有场景的加载和保存流程保持原状。
- 同步调整 `e2e/scene-presets.spec.ts`、`e2e/setup.spec.ts`、`e2e/responsive.spec.ts` 中受影响的现有用例。

验证通过：`npm run type-check`、`npm run build-only`、`npm run test:e2e -- --reporter=line --workers=2`（65 项，2.0 分钟）、`git diff --check`。Impeccable detector 和样式源码检查均无发现。

生产构建在 Edge 中检查中英文、深浅主题及 320、390、768、900、1200px 窗口，分类间距、跨组选择、键盘切换和横向溢出检查通过。截图、测量数据和临时走查脚本位于 `C:\Users\L1nex\.codex\visualizations\2026\11\09\01a1c05a-ea44-7471-adf7-13b93ded0458\` 的 `before/`、`after/`。

该阶段验证浏览器内的生产构建，后续已随 `v0.12.0` 重新打包 EXE。

## 前轮发布工程与 CHANGELOG（2026-11-06）

以下为前轮记录；发布准备已于 `9e203ce` 提交，本轮开始时工作区干净。

本轮按用户确认的五个开发阶段重写 CHANGELOG，并保留此前 UI 打磨和 README 写作之外的发布工程修复。改动留在工作区，待用户审阅。

- `scripts/build.bat` 补齐 CHANGELOG，构建前检查发布附带文件；依赖安装、前端构建、清理、打包或文件复制失败时返回非零退出码。新增 `--no-pause`，便于命令行验证。
- 打包时显式排除调参专用的 NumPy 和 Matplotlib。首轮产物实际收进 138 个 NumPy 模块；排除后 EXE 从 39,538,894 字节降至 28,838,875 字节，减少约 27%。
- `CHANGELOG.md` 补记 `v0.9.0`、`v0.9.1`、`v0.10.0`、`v0.11.0` 四个阶段，分别记录配置产品化、Tunalo 品牌与交互收尾、调度模型重建、自定义场景。六文件 YAML 到 Profile 第 1 版、第 1 版到第 2 版、第 2 版到第 3 版的变化分别写入对应版本的 Breaking Changes。当前感知和发布收尾保留在 Unreleased，预留 `v0.12.0`。
- 已重新生成 `dist/Tunalo.exe`。发布目录仅含 EXE、README、CHANGELOG 和 `.env.example`；内嵌前端和图标与当前构建逐文件一致，WebView2 及 Python.NET 的运行库齐全，未收进个人配置、运行数据或日志。README 沿用现有文件，待用户定稿后重新打包。

已确认的 tag 落点如下；本轮仅写文档，应用版本仍为 `0.9.0`，历史 tag 待创建。

| tag | 对应提交 | 阶段结束日期（作者日期） |
| --- | --- | --- |
| `v0.9.0` | `6210b12` | 2026-09-25 |
| `v0.9.1` | `e135b31` | 2026-10-02 |
| `v0.10.0` | `ef4322f` | 2026-10-19 |
| `v0.11.0` | `867a2d7` | 2026-10-24 |
| `v0.12.0` | UI、README 与打包收尾全部提交后的 commit；当前基线为 `58b02b8` | 待定 |

CHANGELOG 的新版本比较链接使用对应提交范围，Unreleased 从 `867a2d7` 起计算。`v0.8.3` 及更早记录保持原样。

本轮文档检查通过：五段比较范围连续覆盖 `v0.8.3` 后的 110 个提交，无遗漏或重叠；四个历史版本的日期与对应提交一致，旧版本正文和比较链接逐字保留。已同步 `dist/CHANGELOG.md`，发布目录内容检查与 `git diff --check` 通过。结果见 `.pytest_tmp/changelog-rewrite-check.json`。

以下为此前发布工程阶段的验证结果：

| 发布工程检查 | 结果 |
| --- | --- |
| `.\scripts\test.ps1 -q` | 377 项通过，250.69 秒 |
| `npm run test:e2e -- --reporter=line --workers=2` | 65 项通过，2.9 分钟 |
| `npm run type-check`、`npm run build-only` | 通过 |
| Ruff 检查、格式检查、`pip check` | 通过 |
| `.\scripts\build.bat --no-pause` | 完整构建通过，正常退出 |
| EXE 内容检查 | 前端、图标、运行库和附带文件通过，NumPy／Matplotlib 均未打包 |
| EXE 命令行启动 | 在含中文和空格的独立目录中，`--help` 返回 0，未知参数返回 2；未启动窗口 |
| `git diff --check` | 通过 |

临时验证脚本和结果在 `.pytest_tmp/verify_release.py`、`.pytest_tmp/release-artifact-check.json`、`.pytest_tmp/release-cli-smoke.json`、`.pytest_tmp/release-npm-audit.json` 和 `.pytest_tmp/release-bundle-check.json`。

`npm audit --omit=dev` 报告 27 项依赖告警，其中 1 项严重、14 项高危、11 项中危、1 项低危，来源涉及组件生成器和构建工具等。通过附带源码映射的独立构建核对 345 个浏览器脚本源文件，未发现这些告警包进入产物；构建环境中的依赖升级仍待处理。本轮未修改依赖版本或锁文件。

用户要求不使用 computer use，已停止原生窗口操作并清理该独立目录启动的测试进程。原生关闭保护、外观持久化、Windows DPI、真实天气联网和 Wallpaper Engine 切换仍待手动验收。测试未读取或修改本机正式 Profile，也未执行壁纸切换。

## 上一轮 UI 调整（已提交 `58b02b8`）

已完成用户指定的《Tunalo 前端 UI 风格审查交接》五项修复。

- `SceneBindingRow.vue` 将同行布局起点从 1024px 提前到 768px，名称列上限为 18rem；行间增加细分隔线，更窄窗口收紧纵向间距。相同六场景下，1200×780 的名称至播单间距从 524px 降到 216px，900×600 的行高从 125.5px 降到 78.5px。
- `SetupSidebar.vue` 用暮紫图标标出当前页，保留原灰底和悬停效果。
- `SchedulingStep.vue` 将防打扰档位收成共用浅底的分段按钮，宽度从 760px 收至 504px。窄窗继续使用下拉框。`SceneDetailsForm.vue` 为多选项使用现有 `outline` 变体，保留选中实底。
- `WeatherKeyStep.vue` 的帮助入口改用现有 Collapsible 与按钮；天气帮助和自定义防打扰设置均沿用活动页的箭头、展开旋转和图文间距。
- `SetupWorkspace.vue` 通过现有 VueUse `useResizeObserver` 观察正文及视口尺寸，向 `SetupFooter.vue` 传入 `scrollable: boolean`。底栏仅在正文溢出时显示顶部分隔线，透明边框预留相同高度。已验证切换页面、搜索缩短列表、恢复列表和调整窗口大小。

本轮仅修改上述七个前端组件及本交接。保持现有配色、字体、配置格式和保存流程。

| 本轮检查 | 结果 |
| --- | --- |
| `npm run type-check` | 通过 |
| `npm run build-only` | 通过 |
| `npm run test:e2e -- --reporter=line --workers=2` | 65 项全部通过，2.1 分钟 |
| `git diff --check` | 通过 |
| 样式源码检查、Impeccable detector | 0 项发现 |
| 生产构建页面走查 | Edge，1200×780、900×600，中文深浅主题；英文另查 900、390、320px；页面和控制台正常 |

走查通过页面操作和外部 API 测试数据验证，检查展开按钮的键盘操作、多选状态、底栏分隔线及横向溢出。沿用现有行为测试，本轮未新增持久化测试。Browser 插件未提供，使用仓库现有 Playwright 和 Edge。

截图、临时走查脚本和测量结果位于 `C:\Users\L1nex\.codex\visualizations\2026\11\05\01a1aca0-c2e2-7252-91bd-b46ca139e24a\ui-style-fixes\`，包含 `before/`、`after/`、`inspect-scenes/`。日期路径沿用会话目录，实际验证日期为 11 月 6 日。Inspector 在 1440、768、390px 检查得到 0 FAIL、1 WARN；WARN 为宽窗右侧留白，名称与播单集中排列符合本轮收窄要求。暮紫按项目既有品牌色保留。

原生 WebView2 和 Windows DPI 缩放仍待实机复核。

## 此前已验收的修复（截至 2026-11-04）

前轮基线为 `210e2ee`，全部播单失效时的场景定位修复已提交为 `c81189e`。

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

### 行为和源码入口

- 场景临时修改计入窗口关闭判断；Esc 对修改过的弹窗先确认，继续编辑保留内容和焦点，显式取消直接清除本次编辑。放弃弹窗编辑保留主页面修改。窗口确认框显示在场景弹窗之上，并正确恢复焦点。入口为 `frontend/src/setup/scenes/SceneEditor.vue`、两种场景表单、`profile/useProfileDraft.ts`、`workspace/SetupConfirmations.vue`。
- 场景关联、预设分类、防打扰档位和语言选择统一使用主色实底表示选中，悬停保持浅灰底。入口为 `frontend/src/components/ui/toggle/index.ts`、`toggle-group/ToggleGroupItem.vue`、`frontend/src/setup/workspace/SetupSidebar.vue`。
- 摘要、场景页和提交校验共用 `playlistBindingStatus(playlist, available)`，区分有效、未绑定和失效绑定。检查页接收当前可用播单，显示失效数量；零场景显示“尚未添加场景”。问题入口跳到对应场景，有可用播单时聚焦选择器，全部不可用时聚焦场景编辑按钮。入口为 `frontend/src/setup/profile/model/scenes.ts`、`review/summary.ts`、`ReviewStep.vue`、`workspace/SetupStepContent.vue` 和场景播单选择器。
- 已有问题列表移到检查页标题下，修正入口沿用原有校验和焦点行为，底部保持原有按钮布局。
- 密钥实际编辑并离开输入框后启用必填提示。首次空白表单及未经编辑的聚焦、离开保持安静。切换设置项保留反馈，补全密钥后即时清除。`WeatherKeyStep.vue` 增加 `blur` 事件，`useWeatherServices.ts` 提供 `apiKeyTouched` 与 `touchApiKey()`，由 `SetupWeatherContent.vue` 连接；联网测试反馈继续独立处理。
- 编号优先级连续排在上方，“添加层级”紧随其后；未指定情境独立放在下方，用留白及原有说明区分。层级重排使用调整后的索引，拖动、菜单、键盘操作和 Profile 中的偏好语义保持原状。入口为 `frontend/src/setup/scheduling/PreferenceTiersEditor.vue` 和 `copy/preferences.ts`。

后端、Profile 格式、原生关闭事件和真实运行配置保持原状。

### 前轮验证

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

### 待联调

真实 WebView2 标题栏关闭、Alt+F4 和 Windows DPI 缩放仍待实机联调；浏览器中的原生事件模拟已覆盖前端处理器及桥接出口。本轮验证使用模拟本地 API，未替代真实天气联网和实际壁纸切换验收。

此前已验收的本地昼夜计算和天气提醒见[本地昼夜计算规格](../../docs/archived/done/LOCAL_SUN_TIMES_SPEC.md)、[天气提醒规格](../../docs/archived/done/WEATHER_REMINDER_SPEC.md)。
