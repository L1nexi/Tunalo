# 工作交接

更新时间：2026-11-15。分支：`codex/frontend-adjustments`。本轮基线：`87972b3`。当前发布：`v0.12.0`（`8ecc865`）。

## 当前任务与状态

用户选择推进 TODO 中的日志与历史记录整理。本轮实现、验证与文档收尾完成，2026-11-15 审阅通过。实现见 `79a6717`，行为和接口见[日志与历史记录规格](../../docs/archived/done/LOGGING_AND_HISTORY_SPEC.md)，记录职责见 [ADR-0005](../../docs/adr/0005-distribution-driven-execution-and-control-boundaries.md#记录侧消费已提交的结果)。TODO 已转为 Completed，规格已归档，索引与引用同步更新。

多显示器与共同调度由用户后续先验证 Wallpaper Engine 行为、运行 POC。

## 已完成

- 删除 `TickTrace` 的五个转发属性。tick listener 仍统一接收完整 Trace，动作记录、天气提醒、历史映射和托盘从 `trace.schedule` 读取调度结果；轮次、时间和暂停信息由 Trace 提供。
- `EventLogger.write()` 和 `JsonlEventLogger.write()` 返回 `None`，删除进程内编号、月份与路径缓存。按事件发生时间构造月份文件路径，保留同一实例的写入锁和文件错误警告。
- 动作事件新增 `tick_id` 和 `mode`，失败事件补充 `selected_scene` 与 `target_playlist`。成功、失败与 NOOP／PAUSE 的记录范围有测试覆盖；失败后的活跃场景仍为上次成功场景池。
- `ActionEventWriter` 在提交后通过 `Tunalo.Actions` 输出包含执行结果的场景日志，成功为 INFO、失败为 WARNING。Actuator 移出执行前的抽样日志，执行器继续记录命令诊断。
- 历史 API 和 JSON 导出共用映射，在 `think.decision` 新增 `mode`。事件字段、历史输出和运行日志通过真实调度及公开读取接口验证。
- ADR-0005 补充记录职责，天气提醒规格同步新的属性路径，CHANGELOG 记录用户可见的诊断字段。文档索引删除了指向已不存在的 `brainstorming.md` 的旧入口。

## 本轮验证

```powershell
.\scripts\test.ps1 tests\app\test_event_logger.py tests\app\test_weather_reminder.py tests\core\runtime\test_scheduler.py tests\server\test_local_api.py tests\ui\test_tick_history.py tests\ui\test_weather_notification.py -q
```

结果：修改前基线 68 项通过，修改后 70 项通过。JSONL 并发测试检查 200 条记录完整落盘，文件错误测试使用真实文件系统验证警告和后续恢复。

- `.\scripts\test.ps1 -q`：409 项通过，98.22 秒。
- `.\.venv\Scripts\python.exe -m ruff check .`、`ruff format --check .` 均通过，97 个 Python 文件格式一致。
- 修改文档的相对链接与锚点检查通过，`git diff --check` 通过。

测试继续使用真实模块，替换限于网络、时钟、文件系统和操作系统出口；本轮未进行真实 Wallpaper Engine 或原生托盘的交互验收。

## 工作区与下一步

实现与测试已随 `79a6717` 提交。规格归档、TODO 完成状态、索引与引用更新随后续文档提交入库，工作区不再保留未提交改动。

此前天气迁移、天气规则收回集成侧及单实例保护已在当前提交历史中；本轮未修改这些功能。发布记录仍见 [v0.12.0 发布与界面验收](../../docs/archived/done/V0_12_0_RELEASE.md)。
