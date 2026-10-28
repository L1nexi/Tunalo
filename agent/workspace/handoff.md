# 工作交接

更新时间：2026-10-28。
分支：`codex/frontend-adjustments`。
整理基线：`867a2d7`（已推送的 `origin/codex/frontend-adjustments`）；已丢弃的原事件历史截止 `0c1ef29`。
当前基线：`4e2d3e0`；本轮天气提醒改动未提交。

## 当前任务与状态

天气提醒已完成，定向 21 项和全量 365 项测试通过，规范轴与规格轴审阅均为零发现。WeatherSensor 的成功时间和来源指纹随 Trace 上浮，应用层 WeatherReminder 通过 tick listener 检查时长，由托盘呈现通知。

上一阶段的代码与文档已整理，回归通过。运行时优化已提交于 `e15af0c`，文档整理提交为 `4e2d3e0`。原八次未推送历史已移出当前分支，临时备份与事件讨论 stash 已清理。

## 保留与舍弃

| 原提交 | 整理结果 |
| --- | --- |
| `2aecb1b` | 保留天气待办的轻量通知范围，移除对 Event 管线实施的依赖 |
| `1b4c39a` | EventBus、共享发布入口、自动注册及对应测试不移植 |
| `bc20389` | 保留 JSONL 发生时间、月份选择、停止等待和入口收尾改进；调度回归改用 tick listener |
| `b3e9fea` | 保留协作流程、Agent 工作区约定和文档分工，职责描述与当前代码对齐 |
| `6f188d9` | 交接按当前任务重写，事件实施计划不移植；ADR-0006 作为弃用记录保留 |
| `896f55a` | 保留 ADR-0001 至 ADR-0005 的整理；ADR-0005 移除事件接线附录，ADR-0006 标明弃用原因 |
| `7fb01fa` | 随事件基础设施整体舍弃，当前没有订阅或退订接口 |
| `0c1ef29` | 保留状态封装、托盘初始化顺序、跨月日志回归及公开状态恢复测试，移除事件控制与订阅接线 |

## 当前接口与调用关系

- `Scheduler(profile_manager, event_logger)` 恢复 `pause()`、`resume()`、`apply_current_match_now()`、`add_tick_listener()` 和 `on_auto_resume`。
- `SchedulerState.pause(seconds)`、`resume() -> bool` 自行持久化；重复恢复返回 `False`。`commit(schedule) -> TickTrace` 合并元数据生成与状态提交，返回快照供 listener 使用。
- 历史存储通过 `tick_history.update` 接入；动作记录通过 `ActionEventWriter.on_tick` 接入，写入时传入原 `trace.ts`。
- `stop()` 等待正在执行的调度和 listener 完成，再保存状态和记录停止；循环使用 `stop_event.wait(1)`，停止信号可唤醒等待。
- 托盘图标、菜单和自动恢复回调在 Scheduler 启动前准备好。托盘控制通过直接方法调用完成，手动应用标记在状态锁内设置。
- 事件规格和开发指引退出当前分支；[ADR-0006](../../docs/adr/0006-in-process-events-and-scheduler-consumption.md) 保留原决策与弃用说明。

## 分支整理

- `codex/frontend-adjustments` 以 `867a2d7` 为共同基线，只保留两次整理提交；本轮检查时已与远端跟踪分支一致。
- 临时整理分支和本轮创建的三份备份分支均已删除，对应的事件讨论 stash 已丢弃；其余分支及两份原有 stash 保留。
- 本轮在两次整理提交之上实现天气提醒，当前改动保持未提交状态。

## 上一阶段验证

| 检查 | 结果 |
| --- | --- |
| `.\scripts\test.ps1 tests/core/runtime tests/core/test_scheduler_pipeline.py tests/app/test_event_logger.py tests/ui/test_tick_history.py tests/server/test_local_api.py -q` | 48 项通过，12.26 秒 |
| `.\scripts\test.ps1 -q` | 350 项通过，89.78 秒 |
| Ruff 自动修复、检查及格式检查 | 通过，89 个 Python 文件格式一致 |
| ADR 内容核对 | ADR-0001 至 ADR-0004 与原事件分支一致；ADR-0005 保留整理，移除事件接线附录 |
| 文档引用 | 11 份文档的 42 个本地引用中，41 个有效；ADR-0002 的 `PRODUCTIZATION_PHASE_PLAN.md` 链接在基线已失效，保留原文 |
| 事件依赖清理 | 源码与测试中无 `core.events`、`scheduler_events` 和批次分发调用 |
| `git diff --check` | 通过 |

状态恢复通过公开接口验证，调度回归保留真实 Engine、ProfileManager、历史存储和日志输出，只替换操作系统、网络与外部进程。测试按 tdd 样例维护，中文文档按 no-ai-slop-zh 检查。

## 天气提醒实现

行为与接口见[已完成规格](../../docs/archived/done/WEATHER_REMINDER_SPEC.md)。生产改动为六处：`core/models/context.py`、`core/sensors/weather.py`、新增 `app/weather_reminder.py`、`app/main.py`、`ui/tray.py` 和 `ui/i18n.py`。

- `WeatherData` 直接增加 `last_success_at` 和 `source_fingerprint`。Sensor 首次尚未成功时也返回带指纹的数据；成功时一次性替换天气值和完成时间，失败保留缓存。同来源迁移保留元数据，迟到请求只更新旧实例。
- `WeatherReminder(notify)` 提供 `on_tick(trace)`，按 Trace 时间检查两小时阈值、去重、成功重置和来源变化。首次一直失败时从首个 Trace 计时。
- 用户已确认来源切换按 tick 观察处理：观察到的 A→B→A 逐次重置，两个 tick 之间短暂切换按同一来源继续累计。
- 应用入口在 Scheduler 启动前注册 listener；托盘负责中英文通知，停止信号设置后跳过发送。中文为“自上次成功获取天气信息已经过了 {hours} 小时。可能是网络或者代理问题？”，小时数向下取整。
- WeatherPolicy、TimePolicy、历史输出和配置应用路径保持原代码。缓存照常参与调度，暂停期间继续检查；退出沿用原有流程。

## 本轮验证与后续

| 检查 | 结果 |
| --- | --- |
| 采集、提醒、通知与真实调度定向回归 | 21 项通过，7.01 秒 |
| `.\scripts\test.ps1 -q` | 365 项通过，76.11 秒 |
| Ruff 检查与格式检查 | 检查通过，92 个 Python 文件格式一致 |
| `git diff --check` | 通过 |
| 规范与规格两轴审阅 | 各零发现 |
| 异步测试请求清理补充后的采集回归 | 12 项通过，0.56 秒 |

测试通过公共接口验证采集、状态迁移、通知与调度结果，替换限于网络、时间和操作系统出口；真实调度回归验证新元数据随 Trace 上浮且旧 Trace 保持原值。测试均通过后台运行，遵守用户不要操作桌面的要求。

实现和验证已完成，当前保留本地差异供用户审阅。
