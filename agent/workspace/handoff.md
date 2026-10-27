# 工作交接

更新时间：2026-10-28。
分支：`codex/frontend-adjustments`。
整理基线：`867a2d7`（已推送的 `origin/codex/frontend-adjustments`）；已丢弃的原事件历史截止 `0c1ef29`。
运行时保留提交：`e15af0c`；文档整理随本次更新提交。

## 当前任务与状态

用户决定放弃通用 Event 管线，保留未推送提交中的独立改进。已从已推送基线选择性移植并恢复直接控制接口和 tick listener，本轮将整理结果接回 `codex/frontend-adjustments`。天气提醒采用状态观测方案，留待下一步实施。

代码与文档已整理，回归通过。运行时优化已提交于 `e15af0c`，文档单独提交，方便审阅。原八次未推送历史已移出当前分支，临时备份与事件讨论 stash 已清理，整理结果保持本地。

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

- `codex/frontend-adjustments` 以 `867a2d7` 为共同基线，只保留两次整理提交，比远端领先两次提交。
- 临时整理分支和本轮创建的三份备份分支均已删除，对应的事件讨论 stash 已丢弃；其余分支及两份原有 stash 保留。
- 本轮只调整分支引用和本交接，运行代码与全量 350 项通过时的版本一致，未推送远端。

## 验证

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

## 下一步：天气提醒

已确认 WeatherSensor 维护最后成功更新时间，经采集快照进入 Trace；应用层 WeatherReminder 注册为 tick listener，判断超时、去重并调用托盘通知。提醒器读取采集状态，采样间隔留在 Sensor 内部。

同来源配置更新保留状态，换来源重新累计，A→B→A 也重新累计；旧采集器迟到的结果只影响旧实例。退出不等待天气请求，停止期间不再提醒。首次启用尚未成功时的计时起点与通知时长取整仍需明确。

后续在 `codex/frontend-adjustments` 审阅保留改进，再实施天气提醒。用户要求不要操作桌面，后续继续使用后台文件与测试验证。
