# v0.12.0 发布与界面验收记录

状态：2026-11-09 已发布。[GitHub Release](https://github.com/L1nexi/Tunalo/releases/tag/v0.12.0)，发布提交 `8ecc865`；发布结果记录提交为 `de27ce6`。产品变更见 [CHANGELOG](../../../CHANGELOG.md#0120---2026-11-09)。

## 版本与产物

应用版本为 `0.12.0`，配置格式仍为第 3 版 Profile。0.8.x 的 YAML 配置及第 1、2 版 Profile 不自动迁移；发布说明要求升级前备份旧配置，再通过首次设置重新配置。已有第 3 版 Profile 可继续使用。

发布附件为 `Tunalo-v0.12.0-windows-x64.zip` 和 `SHA256SUMS.txt`。压缩包大小为 28,448,441 字节，只包含 `Tunalo.exe`、README、CHANGELOG 和 `.env.example`，未包含个人配置、运行数据或日志。压缩包的 SHA-256 为：

```text
0e7e79725aec6a763438938e0caa28c3c18e4c8bb6b74c0a642f2d01c91302db
```

本次创建或补齐以下标签。CHANGELOG 的 25 个已发布版本均已有远程标签。

| tag | 提交 | 对应阶段 |
| --- | --- | --- |
| `v0.5.1` | `824789a` | Dashboard R1 完成及入口整理 |
| `v0.9.0` | `6210b12` | Profile 配置与统一设置工作区 |
| `v0.9.1` | `e135b31` | Tunalo 品牌与设置体验收尾 |
| `v0.10.0` | `ef4322f` | 场景选择与执行模型重建 |
| `v0.11.0` | `867a2d7` | 自定义场景与外观偏好保存 |
| `v0.12.0` | `8ecc865` | 感知补全与发布收尾 |

`v0.5.1` 位于 Dashboard R1 完成后的文档整理提交，下一提交开始加入 `v0.6.0` 的播放列表显示名功能。其余历史版本沿用此前确认的里程碑落点。发布提交已同步至 `main` 和 `codex/frontend-adjustments`。

## 前端修复与验证入口

| 修复 | 提交 | 源码或测试入口 |
| --- | --- | --- |
| 场景弹窗与窗口共用草稿保护，继续编辑时保留内容与焦点 | `7c0c3a5` | [scene-editor.spec.ts](../../../frontend/e2e/scene-editor.spec.ts) |
| 明确选中状态，区分未选中与悬停状态 | `eddedfb` | [ToggleGroupItem.vue](../../../frontend/src/components/ui/toggle-group/ToggleGroupItem.vue) |
| 统一有效、未绑定和失效播单的判断，检查页可定位具体场景 | `6cfa5ec`、`c81189e` | [review.spec.ts](../../../frontend/e2e/review.spec.ts) |
| 检查页前置待处理事项，天气密钥编辑后就近反馈，优先级与未分配情境分区 | `b14b436`、`620e984`、`210e2ee` | [review.spec.ts](../../../frontend/e2e/review.spec.ts)、[weather.spec.ts](../../../frontend/e2e/weather.spec.ts)、[preferences.spec.ts](../../../frontend/e2e/preferences.spec.ts) |
| 收紧场景与防打扰布局，统一展开控件；正文溢出时显示底栏分隔线 | `58b02b8` | [SetupWorkspace.vue](../../../frontend/src/setup/workspace/SetupWorkspace.vue) |
| 底栏取消／关闭使用描边按钮；预设分类间距统一为 8px，改用“时间 x 活动”，移除“季节与天气”四个预设 | `a31df16` | [scene-presets.spec.ts](../../../frontend/e2e/scene-presets.spec.ts)、[responsive.spec.ts](../../../frontend/e2e/responsive.spec.ts) |

移除预设后共保留五个分类、18 个模板。已有场景的加载与保存流程保持原状。场景表单继续支持跨组多选、同组多个语义项、批量绑定和键盘操作。

## 发布验证

| 检查 | 结果 |
| --- | --- |
| `.\scripts\test.ps1 -q` | 377 项通过，88.61 秒 |
| `npm run test:e2e -- --reporter=line --workers=2` | 界面调整阶段 65 项通过，2.0 分钟；发布阶段未修改界面源码 |
| `npm run type-check`、`npm run build-only` | 界面调整阶段和完整打包时均通过 |
| Ruff 检查与格式检查、`pip check`、`git diff --check` | 通过 |
| `.\scripts\build.bat --no-pause` | 完整构建通过，正常退出 |
| EXE 内容 | 版本为 `0.12.0`，架构为 Windows x64；前端资源和图标与本次构建逐项一致；运行库齐全，NumPy／Matplotlib 未打入包 |
| EXE 命令行启动 | 中文及空格目录下，`--help` 返回 0，未知参数返回 2 |
| 页面走查 | Edge，中英文与深浅主题，320、390、768、900、1200px；检查分类间距、多选、键盘切换和横向溢出 |
| 远程发布 | 正式 Release，已设为 Latest；说明正文、附件大小和摘要核对一致；登录下载及公开链接下载均与本地产物一致 |

前端测试使用公开页面操作和本地 API 测试数据。测试未读取或修改正式 Profile，也未执行真实壁纸切换。全部播单失效时的定位回归在 900×600 窗口创建 12 个场景，验证首屏外的目标场景进入视野，编辑按钮获得焦点。

本地发布产物与验证报告位于 `.pytest_tmp/release-v0.12.0/`，包括 `package-check.json`、`published-check.json` 和 `cli-smoke.json`。界面截图与测量数据位于 `C:\Users\L1nex\.codex\visualizations\2026\11\09\01a1c05a-ea44-7471-adf7-13b93ded0458\` 的 `before/`、`after/`。

## 后续事项

Windows 实机验收与构建依赖升级保留在 [TODO](../../TODO.md)。原生 WebView2、Windows DPI、真实天气联网和实际壁纸切换仍需实机验证。此前对构建依赖告警的分析只覆盖当时的依赖与浏览器产物，后续升级前应重新核对。
