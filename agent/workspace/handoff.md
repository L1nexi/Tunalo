# 工作交接

更新时间：2026-11-10。分支：`codex/frontend-adjustments`。本轮基线：`de27ce6`。当前发布：`v0.12.0`（`8ecc865`）。

## 当前状态

[`v0.12.0`](https://github.com/L1nexi/Tunalo/releases/tag/v0.12.0) 已发布；发布提交、历史标签、界面修复与验证结果见[发布与界面验收记录](../../docs/archived/done/V0_12_0_RELEASE.md)。

Open-Meteo 替换已实现并完成自动化验证，改动留在工作区，待用户审阅。用户已确认采用单一 Open-Meteo 来源、删除 OpenWeatherMap 和密钥，直接破坏性变更，不提供旧格式转换。

- 新增 `src/integrations/openmeteo.py`，删除旧集成；采集与连接测试共用 `current.weather_code` 请求和解析。
- 按 [ADR-0004](../../docs/adr/0004-context-salience-and-observation-boundaries.md) 保留降雨 0.75／1／2／4、雪 0.25／0.75／1.5 和普通／强雷暴 3／4 的标尺，使用 WMO 代码。移除 OWM 主分类回退；本次按单一现象解释，未增加混合雨雪推断。
- `WeatherData.code` 用 None 表示缺失、0 表示晴天；同步 Sensor、策略详情、Tick History 和调参数据。来源指纹只含坐标，保留 600 秒采集、10 秒采集超时、失败缓存、两小时提醒和独立昼夜计算。
- Profile 升为 v4，移除 `weather.api_key`；旧版本通过现有版本错误拒绝读取。真实 `config/profile.json` 未读取或修改。
- 连接测试改为 `POST /api/weather-validations`，接收当前坐标。前端删除密钥和申请指引，坐标变化使验证失效，旧坐标迟到的成功或失败均不更新当前状态；保留网络失败与配额耗尽时确认保存的入口。
- README、CHANGELOG、开发指引、ADR-0001/0004、提醒规格、索引和 TODO 已同步。选型与范围见[评估记录](../../docs/archived/reference/API_KEY_FREE_WEATHER_EVALUATION.md)。

工作区保留此前整理的发布与界面验收记录、文档索引和待办改动；本轮没有提交、打标签或发布。

## 验证

- `.\scripts\test.ps1 -q`：387 项通过。首轮发现旧用例将“无密钥”等同于“没有天气采集器”，已改为通过 Engine 验证天气离线时暂停调度仍能计算并替换本地昼夜，随后全量复验通过。
- `npm run test:e2e -- --workers=2`：68 项通过。随后天气页细节整理后的 10 项天气测试再次通过。
- `npm run build`：类型检查和生产构建通过。
- `.\.venv\Scripts\python.exe -m ruff check .`、`ruff format . --check`：通过。
- `git diff --check` 和文档本地链接检查通过。
- 新集成对公开北京示例坐标 `39.9, 116.4` 的一次真实请求成功，返回 `code=0`，晴天显著度正确。

## 后续工作

本轮改动待用户审阅，通过后再将天气服务任务移入 Completed。缓存过期、重试退避和更多天气字段留作后续独立改进。

实机验收和依赖升级仍见 [TODO](../../docs/TODO.md)。沿用用户此前不使用桌面自动操作的要求；本轮未进行原生窗口操作。真实网络长期表现及天气场景体验仍需后续观察。
