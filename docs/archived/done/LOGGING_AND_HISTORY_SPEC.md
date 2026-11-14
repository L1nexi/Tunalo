# 日志与历史记录整理

状态：已实现，2026-11-15 用户审阅通过。基线 `87972b3`。

## 目标与范围

保留现有三类记录，简化它们取得调度结果的方式，并补上解释执行结果所需的字段。

| 记录 | 回答的问题 | 保留方式 |
| --- | --- | --- |
| 运行日志 | 程序在哪里出错，本次执行是否成功 | `logs/scheduler.log`，沿用现有滚动文件 |
| Event Log | 何时启动、暂停、恢复，以及尝试应用了哪些场景 | `data/events-YYYY-MM.jsonl`，沿用按发生时间分月保存 |
| Tick History | 最近每轮为什么选择、等待或执行 | 内存保留最近 1200 轮，通过现有 API 和托盘导出读取 |

本轮沿用 [ADR-0005](../../adr/0005-distribution-driven-execution-and-control-boundaries.md) 的记录侧消费调度结果，以及 [ADR-0006 的替代安排](../../adr/0006-in-process-events-and-scheduler-consumption.md#弃用原因与替代安排)。调度流程和 tick listener 的交付顺序保持现状。

## 修改背景

- 原 `TickTrace` 已持有 `ScheduleResult`，又用五个属性逐一转发其中的数据。记录器、天气提醒和托盘依赖这组转发属性。
- 原 `JsonlEventLogger.write()` 返回进程内编号，编号未写入文件，生产代码也未读取；写入器为它维护计数和失败回滚。
- 原 `actuation_failed` 没有保存当时已选中的场景和目标播单。成功和失败事件都缺少对应的 tick 编号及执行模式。
- 原 Tick History 未输出已有的执行模式，难以从记录中区分普通调度、手动应用、恢复和暂停。
- 原运行日志中的场景抽样信息由 Actuator 在执行前输出，缺少同一条记录中的执行结果。

## 行为

1. tick listener 的接口继续为 `Callable[[TickTrace], None]`。`TickTrace` 保留轮次、时间、暂停信息和 `schedule`，删除五个转发属性。回调内部通过 `schedule = trace.schedule` 读取本轮结果，通过 `trace.tick_id`、`trace.ts` 等字段读取提交信息。`TickHistoryStore.update(trace)` 继续存储完整 Trace；读取结果字段的变化发生在历史映射函数中。这项简化只减少属性入口，数据传递仍为 `ScheduleResult → TickTrace → listener`。
2. Event Log 保留既有事件类型和字段。两类动作事件新增 `tick_id` 和 `mode`；失败事件另补 `selected_scene` 和 `target_playlist`，值来自当次 `ActionResult`。NOOP 与 PAUSE 轮次只进入 Tick History。
3. Tick History 在 `think.decision` 中新增 `mode`，取值为 `normal`、`manual`、`recovery` 或 `pause`。API 与 JSON 导出继续共用映射。
4. 场景抽样与执行结果的运行日志由 `ActionEventWriter` 在收到已提交结果后统一输出，使用 `Tunalo.Actions` logger，包含轮次、模式、执行结果、选中场景、目标播单和概率。成功使用 INFO，失败使用 WARNING。执行器继续记录命令超时、返回码及异常。
5. JSONL 写入继续保证同一实例的并发记录完整，按事件发生时间选择月份；文件写入失败继续报告警告。删除编号返回值及相关状态，直接按发生时间构造文件路径。

## 文件、类与接口

| 文件 | 类或函数 | 修改 |
| --- | --- | --- |
| `src/core/models/trace.py` | `TickTrace` | 删除 `context`、`selection`、`decision`、`action`、`target` 转发属性；构造字段不变 |
| `src/core/models/event.py` | `EventLogger.write(event_type, data, *, ts)` | 返回类型由 `int` 改为 `None` |
| `src/app/event_logger.py` | `JsonlEventLogger.write(...) -> None` | 删除编号及月份缓存；保留锁和文件错误处理 |
| `src/core/state/action_events.py` | `ActionEventWriter.on_tick(trace: TickTrace) -> None` | 回调内从 `trace.schedule` 读取调度结果，从 Trace 读取轮次和时间，补事件字段并输出执行结果日志 |
| `src/core/runtime/actuator.py` | `Actuator.act(decision) -> ActionResult` | 移出执行前的场景抽样日志；执行逻辑不变 |
| `src/ui/tick_history.py` | `ActionDecisionDto`、`map_tick_snapshot(trace: TickTrace) -> TickSnapshotDto` | 新增 `mode: DecisionMode`；映射时从 `trace.schedule` 读取结果，从 Trace 读取轮次、时间和暂停信息 |
| `src/app/weather_reminder.py` | `WeatherReminder.on_tick(trace: TickTrace) -> None` | 天气读取改为 `trace.schedule.context.weather`，持续时间仍使用 `trace.ts` |
| `src/ui/tray.py` | `TrayIcon` 的场景状态读取 | 改为读取 `trace.schedule`，显示行为不变 |
| `tests/app/test_event_logger.py` | 写入器行为测试 | 用真实落盘结果验证并发和写入失败后的恢复，删除编号断言，补完整类型注解 |
| `tests/core/runtime/test_scheduler.py` | 调度器行为测试 | 适配属性访问，并检查已提交动作的记录内容和结果日志 |
| `tests/server/test_local_api.py`、`tests/ui/test_tick_history.py` | 历史 API 与导出测试 | 覆盖模式字段及失败前后场景的含义 |

文档同步范围：在 ADR-0005 补充三类记录的职责，在 CHANGELOG 记录新增的诊断信息，工作交接保留验证结果。审阅通过后规格归档至本目录，TODO 转为 Completed。

## 测试入口

沿用真实模块，替换限于网络、时钟、文件系统和操作系统出口。

| 公共接口 | 检验内容 | 范围之外 |
| --- | --- | --- |
| `Scheduler.start()/stop()` 与 tick listener | 已提交的成功／失败结果进入事件文件与历史；停止等待当前记录完成 | WE 实机行为 |
| `JsonlEventLogger.write()` 与产出的 JSONL 文件 | 发生时间、跨月写入、并发完整性、文件错误后的继续写入 | 多进程写入同一文件 |
| `GET /api/tick-history` 与 `export_tick_history()` | 执行模式、场景身份、失败时保留原活跃场景、导出契约 | 原生托盘交互 |

验证结果见[工作交接](../../../agent/workspace/handoff.md)。
