# 本地昼夜计算

状态：已实现，待用户验收，2026-10-29。架构选择见 [ADR-0004](adr/0004-context-salience-and-observation-boundaries.md#季节与时段平台和真实昼夜锚点)。

## 行为

使用已配置地点的经纬度和系统当地日期，通过 Astral 在本地计算日出日落。启动后的首次采集即可得到当天结果；天气服务的密钥、请求进度与请求结果不影响计算。地点仍取现有 `weather.location`，Profile 格式和设置入口沿用现状。

日期与时区沿用计算机的当地时间。结果保留在内存中，以当地日期和 UTC 偏移为缓存键；跨日、日期回拨或偏移变化后重新计算。配置替换会创建新采集器，新地点重新计算。重启后直接计算当天结果。

极昼极夜等当天缺少完整日出日落的情况返回无数据。TimePolicy 清除旧锚点，四个时段的显著度归零；恢复到有完整日出日落的日期后，重新参与判断。

TimePolicy 继续使用既有的晨间、白天、黄昏、夜晚曲线、昼夜中点和分钟粒度。天气持续失败提醒继续依据天气采集的成功时间运行。

## 数据与接口

| 位置 | 契约 |
| --- | --- |
| `core.models.context.SunTimesData` | 包含 `sunrise: int` 和 `sunset: int`，均为 UTC Unix 秒；数据不可变。 |
| `Context.sun_times` | 类型为 `SunTimesData \| None`，随每个 Tick 的观测快照进入 Trace。 |
| `SunTimesSensor(latitude, longitude)` | 使用给定经纬度计算；`collect() -> SunTimesData \| None` 返回本地日期的结果。 |
| `SunTimesSensor.create(config)` | 从运行时配置读取现有坐标；缺少任一坐标时返回 `None`。 |
| `TimePolicy.evaluate(context)` | 从 `context.sun_times` 读取锚点，返回既有 `TimeEvaluation`。 |

新 Sensor 通过已有注册表和 Engine 组装。`WeatherObservation`、`WeatherData` 与 WeatherSensor 移除日出日落字段，天气请求仅解析气象观测。

Tick History 的 `sense.sunTimes` 包含 `available`、`sunrise`、`sunset`。无数据时 `available` 为 `false`，两个时间为 `null`。原 `sense.weather` 仅保留天气可用性、代码和主分类。调参工具的固定日出日落通过 `Context.sun_times` 提供。

## 验收

通过采集、时段策略、场景选择、真实调度和历史导出的公共接口验证，时间、网络和操作系统出口可用测试替代：

- 离线首次采集可用，配置中只有坐标时也能计算。
- 同一日期结果稳定，跨日、日期回拨、UTC 偏移和地点变更后结果更新；日期边界按当地时间处理。
- 极昼极夜返回无数据并清除旧锚点，普通日期恢复。
- 天气缺失时仍可按时段选场景，既有曲线、对称性与概率行为保留原期望值。
- 暂停时继续采集，运行时替换地点后采用新结果，旧快照保持原值。
- API 和 JSON 导出分别记录天气与本地日出日落。

本批按用户要求跳过与 OWM 的精度对照。检查使用项目测试脚本、Ruff、前端类型检查和构建，结果记录在[工作交接](../agent/workspace/handoff.md)。
