# Docs Index

`docs/` 按规格生命周期管理。代码、测试、运行配置和正在推进的活跃规格为一手依据。已完成规格进入归档后，保留为项目记忆和设计背景。进行中的设计讨论单独标明确认范围。

## 文档分工

| 文档                               | 内容                                                                       |
| ---------------------------------- | -------------------------------------------------------------------------- |
| 规格                               | 预期行为、边界条件与验收标准。                                             |
| ADR（`adr/`）                      | 模块边界、依赖方向、方案取舍及理由；修订既有决策时注明对应条款。           |
| [Agent 工作区](../agent/README.md) | 当前任务的进度同步、未决问题与 [工作交接](../agent/workspace/handoff.md)。 |

行为和验收变化时更新规格，架构决策变化时更新或新增 ADR。任务推进时，工作区引用相关文档并更新当前状态。

## 架构方案

调整模块划分、职责或依赖方向前，先说明模块职责、依赖方向和关键数据流，并列出涉及的关键接口。

ADR 记录已确定的架构选择及其理由。接口签名、执行步骤与接线细节写入规格或开发指引，由 ADR 引用。

## 生命周期

| 路径                  | 定位                                           | 管理规则                                                                                                                 |
| --------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `docs/*.md`           | 当前规格、进行中的设计讨论、问题列表与开发指引 | 规格完成后移入 `archived/done/`；废弃后移入 `archived/deprecated/` 或 `archived/outdated/`。问题列表与开发指引持续更新。 |
| `half-finished/`      | 暂停的规格、研究记录、访谈和未来方向           | 想法仍有价值但不在当前实现路径上时保留在这里。                                                                           |
| `archived/done/`      | 已完成规格和实施记录                           | 完成态历史记录。                                                                                                         |
| `archived/reference/` | 事实参考、POC、外部行为记录                    | 作为参考材料按需引用。                                                                                                   |

## 问题列表

| 文档      | 作用                             |
| --------- | -------------------------------- |
| `TODO.md` | 后续小版本的体验与产品改进待办。 |

## 开发指引

| 文档                                                                 | 作用                                             |
| -------------------------------------------------------------------- | ------------------------------------------------ |
| `DEVELOPMENT.md`                                                     | 本地运行、检查、打包与实现入口。                 |
| `PRODUCT_POSITIONING.md`                                             | 长期产品定位、目标用户与开发阶段的体验判断准则。 |
| [brainstorming.md](brainstorming.md)                                 | 功能构思的判断原则与常见失误。                   |

## Active Specs

当前暂无活跃规格，天气提醒的待实施范围见 [TODO](TODO.md)。

## Architecture Decisions

| 文档                                                                         | 作用                                                                 | 状态     |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------- | -------- |
| [ADR-0001](adr/0001-productization-server-and-profile-editor.md)             | 配置编辑的本地服务端、Profile 所有权、外部集成与桌面窗口边界。       | 部分过时 |
| [ADR-0002](adr/0002-scene-model-rethink-and-neutral-baseline.md)             | 旧匹配心智的溯源、整体模型重审与中立随机基准。                       | Accepted |
| [ADR-0003](adr/0003-scene-probability-budgets-and-preference-cascade.md)     | 同组最大值聚合、偏好级联、召回与排除、变量预算、场景概率及尽力选择。 | Accepted |
| [ADR-0004](adr/0004-context-salience-and-observation-boundaries.md)          | 有符号显著度、有限活动轨迹、季节与时段锚点、天气共同推导及观测边界。 | Accepted |
| [ADR-0005](adr/0005-distribution-driven-execution-and-control-boundaries.md) | 分布距离驱动的执行时机、时序与防打扰职责、成功历史和记录边界。       | Accepted |
| [ADR-0006](adr/0006-in-process-events-and-scheduler-consumption.md)          | 原进程内事件管线的决策与弃用原因；现采用显式接口与 tick listener。    | 已弃用 |

## Archived: Reference

这些文档记录背景事实、POC 和推迟的架构方向：

- [OPENWEATHER_CURRENT_API.md](archived/reference/OPENWEATHER_CURRENT_API.md)：OWM 当前天气接口的请求参数、响应字段、天气代码与数据口径。
- [WE_CLI.md](archived/reference/WE_CLI.md)：WE CLI 官方文档快照
- [WE_CLI_POC.md](archived/reference/WE_CLI_POC.md)：WE CLI 实机 POC 验证结果
- [config.json](archived/reference/config.json)：WE 官方配置文件 schema 参考

## 维护规则

- `README.md` 面向用户和发布包读者；实现规格、产品规格和研究记录放在 `docs/`。
- 活跃规格完成后，移动到 `archived/done/` 并同步更新本索引。
- 已完成实现的决策进行文档整理后，可清理重复的讨论和实施中间文档；保留代码与行为验证入口，将尚未完成的工作迁入 TODO，并同步清除旧引用。
