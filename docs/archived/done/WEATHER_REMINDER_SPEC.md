# 天气更新超时提醒

状态：已实现，2026-10-28。当前验证结果见[工作交接](../../../agent/workspace/handoff.md)。

## 行为

天气连续两小时未成功更新时，通过系统托盘通知一次。成功获取天气后重置计时和已提醒状态，恢复时静默。首次一直失败时，从提醒器首次收到该来源的 Trace 开始计时。

来源由 API key、纬度和经度确定。同来源配置更新保留进度，换来源重新累计；地点显示名称不影响来源。来源变化按 tick 观察到的指纹处理，A→B→A 被逐次观察到时逐次重置，两个 tick 之间的短暂切换按同一来源继续累计。

提醒只负责通知，已有天气缓存照常参与调度。WeatherPolicy、TimePolicy、历史输出和配置应用路径保持原有实现。暂停期间继续检查；休眠、长 tick 或调度异常后的检查在下一次提交时进行。

## 数据与接口

`WeatherData` 增加 `last_success_at: float | None = None` 和 `source_fingerprint: str = ""`。指纹为固定格式 JSON 数组 `[api_key, latitude, longitude]` 的 SHA-256 完整十六进制摘要，坐标使用运行时浮点值。进入 Trace 的来源信息使用指纹。

`WeatherSensor.collect() -> WeatherData` 首次尚未成功时也返回带指纹的数据，天气字段沿用默认值。请求成功完成时一次性替换完整数据，成功时间取完成时的 Unix 秒；失败保留缓存与成功时间。同来源通过现有状态迁移保留这些信息，旧请求迟到只更新旧实例。

`WeatherReminder(notify: Callable[[float], None])` 提供 `on_tick(trace: TickTrace) -> None`，阈值为 `2 * 60 * 60` 秒。提醒器读取 `trace.context.weather`，用 `trace.ts` 计算持续时长。达到阈值时先标记已提醒，再向通知函数传入持续秒数；通知异常沿用 Scheduler 的 listener 异常处理。

应用入口在托盘创建后、Scheduler 启动前注册提醒器。`TrayIcon.notify_weather_unavailable(elapsed_seconds: float) -> None` 发送系统通知，已设置停止信号时跳过发送。退出沿用原有线程等待和状态保存流程。

上述显式组合沿用 [ADR-0006 的替代安排](../../adr/0006-in-process-events-and-scheduler-consumption.md#弃用原因与替代安排)。

## 文案

通知标题为 Tunalo，持续小时数向下取整。

- 中文：自上次成功获取天气信息已经过了 {hours} 小时。可能是网络或者代理问题？
- 英文：It has been {hours} hours since weather information was last retrieved successfully. Could it be a network or proxy issue?

## 验收

通过采集、状态导入导出、提醒器和托盘通知的公共接口验证：成功时间、失败缓存、来源迁移、迟到结果隔离、7199/7200 秒边界、通知去重、恢复重置、首次失败计时、暂停与停止。真实调度测试确认元数据随 Trace 上浮且旧 Trace 保持原值。替换限于网络、时间和操作系统出口，验证全部在后台进行。
