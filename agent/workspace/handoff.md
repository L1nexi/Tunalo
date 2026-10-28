# 工作交接

更新时间：2026-10-29。
分支：`codex/frontend-adjustments`。
当前基线：`5b38814`（天气不可用提醒）；本轮本地昼夜计算保持未提交。

## 当前任务与状态

本地昼夜计算已实现，全量 377 项测试、Ruff、前端类型检查和构建通过，待用户验收。用户已确认文件、接口与测试范围，并要求跳过与 OWM 的精度对照。

行为和接口见[本地昼夜计算规格](../../docs/LOCAL_SUN_TIMES_SPEC.md)，架构修订见 [ADR-0004](../../docs/adr/0004-context-salience-and-observation-boundaries.md#季节与时段平台和真实昼夜锚点)。TODO 保留在 In Progress，验收后再标记完成并归档规格。

天气不可用提醒已在当前基线中实现，继续依据天气采集的成功时间和来源指纹运行。

## 本轮实现

- 新增 `core/models/context.py` 中的不可变 `SunTimesData(sunrise, sunset)` 与 `Context.sun_times`，时间使用 UTC Unix 秒。
- 新增 `core/sensors/sun_times.py` 的 `SunTimesSensor(latitude, longitude)`，提供 `collect() -> SunTimesData | None` 和 `create(config)`。地点复用运行时配置中的现有经纬度，计算独立于天气密钥和请求结果。
- 按系统当地日期计算，缓存键为当地日期和 UTC 偏移；跨日、日期回拨或偏移变化时刷新。运行时配置替换创建新采集器，地点变更后重新计算。
- 极昼极夜等缺少完整日出日落时返回 `None`，TimePolicy 清除旧锚点并输出中性时段；既有曲线、昼夜中点与分钟粒度保持原样。
- 新采集器进入已有 Sensor 注册表，沿用 Engine 和 ContextManager 的组装、快照及配置替换流程。
- WeatherObservation、WeatherData 和 WeatherSensor 移除日出日落字段。Tick History 的日出日落从 `sense.weather` 移到 `sense.sunTimes`，包含 `available`、`sunrise`、`sunset`。
- 调参工具通过 `Context.sun_times` 提供固定锚点；前端天气和地点文案说明本地计算。Profile 格式和设置入口沿用现状。
- `requirements.txt` 增加 Astral。本机虚拟环境已安装 Astral 3.2 及其依赖 tzdata。

## 源码与测试入口

- 采集与数据：`src/core/sensors/sun_times.py`、`src/core/sensors/__init__.py`、`src/core/models/context.py`。
- 消费与输出：`src/core/policies/time.py`、`src/ui/tick_history.py`、`tools/tuning/harness.py`。
- 天气字段清理：`src/integrations/openweather.py`、`src/core/sensors/weather.py`。
- 行为测试：`tests/core/test_sun_times.py`、`tests/core/test_semantic_model.py`、`tests/core/test_weather.py`。
- 调度与导出测试：`tests/core/runtime/test_scheduler.py`、`tests/server/test_local_api.py`、`tests/ui/test_tick_history.py`。

测试使用公共接口，替换限于时间、网络、外部进程和操作系统出口。覆盖离线首次可用、当地日期边界、时区变化、地点替换、极昼极夜与恢复、天气缺失时的时段选择、暂停采集和历史输出；原时段曲线继续使用既有独立期望值。测试在后台运行。

## 本轮验证

| 检查 | 结果 |
| --- | --- |
| 采集、时段与天气定向测试 | 101 项通过，1.64 秒 |
| 调度、API 与导出定向测试 | 41 项通过，8.48 秒 |
| `.\scripts\test.ps1 -q` | 377 项通过，66.61 秒 |
| 加强旧快照断言后的调度回归 | 3 项通过，6.94 秒 |
| Ruff 自动修复、检查与格式化 | 通过，94 个 Python 文件格式一致 |
| `npm run build` | `type-check` 与 `build-only` 均通过；构建仍提示主包超过 500 kB |
| 文档引用 | 5 份文档的 23 个本地链接与锚点有效 |
| `git diff --check` | 通过 |

## 下一步

本批供用户审阅。验收通过后，将 TODO 标记完成、归档规格并更新索引。天气结果落盘仍是后续独立方向。
