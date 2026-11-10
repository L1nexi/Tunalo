# 工作交接

更新时间：2026-11-11。分支：`codex/frontend-adjustments`。本轮基线：`2539017`。当前发布：`v0.12.0`（`8ecc865`）。

## 当前状态

[`v0.12.0`](https://github.com/L1nexi/Tunalo/releases/tag/v0.12.0) 已发布；发布提交、历史标签、界面修复与验证结果见[发布与界面验收记录](../../docs/archived/done/V0_12_0_RELEASE.md)。

Open-Meteo 替换与天气类型层重构已实现并完成自动化验证，改动留在工作区，待用户审阅。用户已确认采用单一 Open-Meteo 来源、删除 OpenWeatherMap 和密钥，直接破坏性变更，不提供旧格式转换。

- 新增 `src/integrations/openmeteo.py`，删除旧集成；采集与连接测试共用 `current.weather_code` 请求和解析。
- Open-Meteo 集成负责把 WMO 天气码归类为 `WeatherType`，`WeatherData.type` 使用 `None` 表示尚未获取、`clear` 表示有效晴天、`unknown` 表示无法归类的有效观测。`WeatherPolicy` 只消费天气类型，不再认识来源代码。
- 按 [ADR-0004](../../docs/adr/0004-context-salience-and-observation-boundaries.md) 保留降雨 0.75／1／2／4、雪 0.25／0.75／1.5 和普通／强雷暴 3／4 的标尺，逐天气类型取值。移除 OWM 主分类回退；本次按单一现象解释，未增加混合雨雪推断。
- 同步 Sensor、策略详情、Tick History 和调参数据：`sense.weather` 为 `{available, type}`，详情为 `{weatherType, available, mapped}`，调参工具直接使用天气类型预设。来源指纹只含坐标，保留 600 秒采集、10 秒采集超时、失败缓存、两小时提醒和独立昼夜计算。
- Profile 升为 v4，移除 `weather.api_key`；旧版本通过现有版本错误拒绝读取。真实 `config/profile.json` 未读取或修改。
- 连接测试改为 `POST /api/weather-validations`，接收当前坐标。前端删除密钥和申请指引，坐标变化使验证失效，旧坐标迟到的成功或失败均不更新当前状态；保留网络失败与配额耗尽时确认保存的入口。
- README、CHANGELOG、ADR-0001/0004、提醒规格、索引和 TODO 已同步。选型与范围见[评估记录](../../docs/archived/reference/API_KEY_FREE_WEATHER_EVALUATION.md)。
- 删除 `docs/DEVELOPMENT.md`：其内容维护价值不足且结构混乱，相关入口改为 ADR、代码、测试和 README；索引、ADR 与评估记录中的引用已清理。

工作区保留此前整理的发布与界面验收记录、文档索引和待办改动；本轮没有提交、打标签或发布。

2026-11-11 另完成一轮文档重构：`docs/DEVELOPMENT.md` 重建为常青开发文档，只保留本地运行、测试、打包与代码风格；AGENTS.md 移除命令章节，新增变更记录规则；`docs/index.md` 登记开发文档及其生命周期。本轮同样未提交。

## 验证

- `.\scripts\test.ps1 -q`：404 项通过。覆盖天气代码归类、天气类型到四项显著度的推导、未知类型中性、Tick History 新字段和调度器缓存。
- `.\.venv\Scripts\python.exe -m ruff check src tests`、`ruff format --check`（改动文件）：通过。
- 前端未改动，此前 `npm run test:e2e -- --workers=2` 的 68 项与 `npm run build` 结果继续适用于设置流程。
- `git diff --check` 通过；本次改动涉及的文档相对链接检查通过，删除 `docs/DEVELOPMENT.md` 后无残留引用。
- 新集成对公开北京示例坐标 `39.9, 116.4` 的一次真实请求成功，返回 `code=0`；归类后为 `clear`，晴天显著度正确。

## 后续工作

本轮改动待用户审阅，通过后再将天气服务任务移入 Completed。缓存过期、重试退避和更多天气字段留作后续独立改进。

实机验收和依赖升级仍见 [TODO](../../docs/TODO.md)。沿用用户此前不使用桌面自动操作的要求；本轮未进行原生窗口操作。真实网络长期表现及天气场景体验仍需后续观察。
