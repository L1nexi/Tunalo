# 天气更新超时提醒

状态：已实现，2026-10-28。当前验证结果见[工作交接](../../../agent/workspace/handoff.md)。

2026-11-10 随 Open-Meteo 接入修订来源定义；提醒阈值、失败缓存与恢复行为沿用原决策。

2026-11-21 修订休眠空档与提醒接口：相邻 Tick 间隔超过 60 秒时按进程未运行处理，这段时长不计入未更新计时；通知参数改为提醒阈值的小时常量，不再传入实际持续时长。

## 行为

天气连续两小时未成功更新时，通过系统托盘通知一次。成功获取天气后重置计时和已提醒状态，恢复时静默。首次一直失败时，从提醒器首次收到该来源的 Trace 开始计时。

来源由纬度和经度确定。同来源配置更新保留进度，换来源重新累计；地点显示名称不影响来源。来源变化按 tick 观察到的指纹处理，A→B→A 被逐次观察到时逐次重置，两个 tick 之间的短暂切换按同一来源继续累计。

提醒只负责通知，已有天气缓存照常参与调度。天气观测由 WeatherPolicy 解释，昼夜按地点在本地计算。暂停期间继续检查；休眠、长 tick 或调度异常后的检查在下一次提交时进行。相邻两次 Tick 的间隔超过 60 秒时，提醒器把这段间隔视为进程未运行，不计入未更新时长；间隔不超过 60 秒的 Tick 照常累计。

## 数据与接口

`WeatherData` 保留 `last_success_at: float | None = None` 和 `source_fingerprint: str = ""`。指纹为固定格式 JSON 数组 `[latitude, longitude]` 的 SHA-256 完整十六进制摘要，坐标使用运行时浮点值。进入 Trace 的来源信息使用指纹。

`WeatherSensor.collect() -> WeatherData` 首次尚未成功时也返回带指纹的数据，天气字段沿用默认值。请求成功完成时一次性替换完整数据，成功时间取完成时的 Unix 秒；失败保留缓存与成功时间。同来源通过现有状态迁移保留这些信息，旧请求迟到只更新旧实例。

`WeatherReminder(notify: Callable[[int], None])` 提供 `on_tick(trace: TickTrace) -> None`，阈值为 `WEATHER_REMINDER_AFTER_HOURS = 2` 小时，秒数常量 `WEATHER_REMINDER_AFTER_SECONDS` 由它派生。提醒器读取 `trace.schedule.context.weather`，用来源指纹和最近成功时间组成键，键变化时清零累计监测时长；相邻 Tick 间隔超过 `WEATHER_REMINDER_SUSPENSION_GAP_SECONDS = 60.0` 秒时不累计监测时长。达到阈值时先标记已提醒，再调用通知函数并传入 `WEATHER_REMINDER_AFTER_HOURS`。通知异常沿用 Scheduler 的 listener 异常处理。

应用入口在托盘创建后、Scheduler 启动前注册提醒器。`TrayIcon.notify_weather_unavailable(hours: int) -> None` 用传入的小时数格式化系统通知，已设置停止信号时跳过发送。退出沿用原有线程等待和状态保存流程。

上述显式组合沿用 [ADR-0006 的替代安排](../../adr/0006-in-process-events-and-scheduler-consumption.md#弃用原因与替代安排)。

## 文案

通知标题为 Tunalo，小时数取提醒阈值的小时常量。

- 中文：自上次成功获取天气信息已经过了 {hours} 小时。可能是网络或者代理问题？
- 英文：It has been {hours} hours since weather information was last retrieved successfully. Could it be a network or proxy issue?

## 验收

通过采集、状态导入导出、提醒器和托盘通知的公共接口验证：成功时间、失败缓存、来源迁移、迟到结果隔离、7199/7200 秒边界、通知去重、恢复重置、首次失败计时、暂停与停止；提醒器另验证休眠空档不计时、间隔不超过阈值的 Tick 照常累计，以及通知回调收到提醒阈值的小时常量。真实调度测试确认元数据随 Trace 上浮且旧 Trace 保持原值。替换限于网络、时间和操作系统出口，验证全部在后台进行。
