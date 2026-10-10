# Docs Index

`docs/` 按规格生命周期管理，不按 `current` / `legacy` 二分。代码、测试、运行配置和正在推进的 active spec 才是当前实现依据；已完成规格进入归档后，保留为项目记忆和设计背景。进行中的设计讨论单独标明确认范围，未定案方案不直接作为实现契约。

## 生命周期

| 路径                   | 定位                                        | 管理规则                                                                                                                 |
| ---------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `docs/*.md`            | 当前规格、进行中的设计讨论、问题列表与开发指引 | 规格完成后移入 `archived/done/`；废弃后移入 `archived/deprecated/` 或 `archived/outdated/`。问题列表与开发指引持续更新。 |
| `half-finished/`       | 暂停的规格、研究记录、访谈和未来方向        | 想法仍有价值但不在当前实现路径上时保留在这里。                                                                           |
| `superpowers/`         | 本地 agent 工作过程记录                     | 作为 scratch / work-in-progress 使用，默认不推远端；有长期价值的完成记录归档到 `archived/done/superpowers/`。            |
| `archived/done/`       | 已完成规格和实施记录                        | 完成态历史记录。可以解释当前行为，但不作为持续维护的 current contract。                                                  |
| `archived/deprecated/` | 明确放弃的产品或架构路线                    | 只用于说明为什么不应按原路线继续。                                                                                       |
| `archived/outdated/`   | 已不匹配当前项目的大文档或旧入口            | 仅作历史背景，不作为实现依据。                                                                                           |
| `archived/reference/`  | 事实参考、POC、外部行为记录或推迟的架构备忘 | 可作为背景材料引用，不等同于 active task plan。                                                                          |

## 问题列表

| 文档                   | 作用                             |
| ---------------------- | -------------------------------- |
| `TODO.md`              | 后续小版本的体验与产品改进待办。 |
| `ACCEPTANCE_ISSUES.md` | 2026-09-23 桌面验收开放问题。    |
| [FRONTEND_UX_UI_REVIEW_2026-09-28.md](FRONTEND_UX_UI_REVIEW_2026-09-28.md) | 前端 UX、UI 与布局审查及桌面验收历史；2026-10-01 修复记录见第 6 节。新版场景偏好界面和 Profile 接入尚待设计，见 TODO。 |

## 开发指引

| 文档                     | 作用                                             |
| ------------------------ | ------------------------------------------------ |
| `DEVELOPMENT.md`         | 本地运行、检查、打包与实现入口。                 |
| `PRODUCT_POSITIONING.md` | 长期产品定位、目标用户与开发阶段的体验判断准则。 |

## Active Specs

| 文档                           | 作用                                                       | 状态   |
| ------------------------------ | ---------------------------------------------------------- | ------ |
| `PRODUCTIZATION_PHASE_PLAN.md` | 产品化阶段规划与既有配置、Tick History、setup 边界；场景模型的后续变更见 ADR。 | 界面接入待继续 |

## 场景选择模型阅读入口

已确认决策与取舍由 ADR-0002～0005 承接；领域词表见根目录 [CONTEXT.md](../CONTEXT.md)，当前参数、代码和验证入口见[开发指引](DEVELOPMENT.md#场景选择模型)。模型与后端消费已实现，前端仍使用旧 Profile 契约，具体界面、长期校准及后续语义探索见 [TODO](TODO.md)。

2026-10-11 已清理本轮讨论总览、分项讨论、实施规格、计划、初值表、初步验收及开放问题等中间文档；未决事项已迁入 TODO。需要追溯原始讨论或实施过程时使用 Git 历史，不从旧过程记录推定当前能力。

## Architecture Decisions

| 文档                                                   | 作用                                                                | 状态     |
| ------------------------------------------------------ | ------------------------------------------------------------------- | -------- |
| `adr/0001-productization-server-and-profile-editor.md` | 产品化本地服务端、REST Profile 接口、城市定位与设置窗口的架构交接。 | Accepted |
| [ADR-0002](adr/0002-scene-model-rethink-and-neutral-baseline.md) | 旧匹配心智的溯源、整体模型重审与中立随机基准。 | Accepted |
| [ADR-0003](adr/0003-scene-probability-budgets-and-preference-cascade.md) | 偏好级联、正向召回与负向排除、变量预算、条件场景概率及尽力选择。 | Accepted |
| [ADR-0004](adr/0004-context-salience-and-observation-boundaries.md) | 有符号显著度、有限活动轨迹、季节与时段锚点、天气共同推导及观测边界。 | Accepted |
| [ADR-0005](adr/0005-selection-and-scheduling-boundary.md) | 选择与调度分工、执行时抽样、状态所有权、类型职责、诊断及配置接入边界。 | Accepted |

## Half-Finished

| 文档                                                    | 作用                                          |
| ------------------------------------------------------- | --------------------------------------------- |
| `half-finished/ROADMAP.md`                              | 旧未来方向记录；文档自身已标注废弃。          |
| `half-finished/WALLPAPER_AWARE_CYCLE_SPEC.md`           | Wallpaper-aware cycle 的产品级设计。          |
| `half-finished/WALLPAPER_AWARE_CYCLE_IMPL_SPEC.md`      | Wallpaper-aware cycle 的实现规格。            |
| `half-finished/WALLPAPER_AWARE_CYCLE_IMPL_BRIEF.md`     | Wallpaper-aware cycle 的短版实现说明。        |
| `half-finished/WALLPAPER_AWARE_SCHEDULING_INTERVIEW.md` | Wallpaper-aware scheduling 的访谈和研究记录。 |
| `half-finished/WALLPAPER_CLUSTER_CALIBRATION.md`        | Wallpaper 聚类与用户校准的早期方向记录。      |

## Archived: Done

| 领域                           | 文档                                                                                                                                                                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Configuration                  | `archived/done/doc_configuration/CONFIGURATION_SPEC.md`, `archived/done/doc_configuration/CONFIGURATION_PHASE_PLAN.md`                                                                               |
| Diagnostics                    | `archived/done/doc_dashboard/DASHBOARD_ANALYSIS_SPEC.md`, `archived/done/doc_dashboard/DASHBOARD_ANALYSIS_IMPLEMENTATION_SPEC.md`, `archived/done/doc_dashboard/DASHBOARD_TIMELINE_ECHARTS_GUIDE.md` |
| Playlist matching              | `archived/done/doc_playlist_pool/R8_PLAYLIST_POOL_SPEC.md`                                                                                                                                           |
| History                        | `archived/done/HISTORY_SYSTEM_SPEC.md`                                                                                                                                                               |
| Product direction              | `archived/done/PRODUCT_DIRECTION.md`                                                                                                                                                                 |
| Wallpaper Engine factual state | `archived/done/WE_FACTUAL_PLAYLIST_RECOVERY_SPEC.md`                                                                                                                                                 |
| Agent work records             | `archived/done/superpowers/`                                                                                                                                                                         |

## Archived: Deprecated

这些是已经冻结且不应作为主线恢复的设计路线：

- `archived/deprecated/CONFIG_EDITOR_SPEC.md`
- `archived/deprecated/CONFIG_EDITOR_IMPLEMENTATION_SPEC.md`
- `archived/deprecated/CONFIG_EDITOR_R5_SPEC.md`
- `archived/deprecated/HISTORY_SPEC.md`

## Archived: Outdated

- `archived/outdated/README_DEV.md`

## Archived: Reference

这些文档记录背景事实、POC 和推迟的架构方向：

- [OPENWEATHER_CURRENT_API.md](archived/reference/OPENWEATHER_CURRENT_API.md)：OWM 当前天气接口的请求参数、响应字段、天气代码与数据口径。
- `archived/reference/WE_CLI.md`
- `archived/reference/WE_CLI_POC.md`
- `archived/reference/SEMANTIC-REFACTOR-SPEC.md`
- `archived/reference/config.json`

## 维护规则

- `README.md` 面向用户和发布包读者；实现规格、产品规格和研究记录放在 `docs/`。
- 不新建 `current/` 桶。规格完成后应进入 `archived/done/`，即使对应实现仍然是当前行为。
- active spec 完成后，移动到 `archived/done/` 并同步更新本索引。
- 已完成实现的决策与理由整理为 ADR 后，可清理重复的讨论和实施中间文档；保留代码与行为验证入口，将尚未完成的工作迁入 TODO，并同步清除旧引用。
- 路线明确放弃后，移动到 `archived/deprecated/`；如果文档内缺少状态说明，补一段短说明。
- 大型旧文档不再匹配当前代码时，移动到 `archived/outdated/`。
