# Docs Index

`docs/` 按规格生命周期管理。代码、测试、运行配置和正在推进的活跃规格为一手依据；已完成规格进入归档后，保留为项目记忆和设计背景。进行中的设计讨论单独标明确认范围。

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

| 文档                     | 作用                                             |
| ------------------------ | ------------------------------------------------ |
| `DEVELOPMENT.md`         | 本地运行、检查、打包与实现入口。                 |
| `PRODUCT_POSITIONING.md` | 长期产品定位、目标用户与开发阶段的体验判断准则。 |

## Active Specs

| 文档                           | 作用                                                                           | 状态           |
| ------------------------------ | ------------------------------------------------------------------------------ | -------------- |
| `PRODUCTIZATION_PHASE_PLAN.md` | 产品化阶段规划与既有配置、Tick History、setup 边界；场景模型的后续变更见 ADR。 | 界面接入待继续 |

## Architecture Decisions

| 文档                                                                     | 作用                                                                 | 状态     |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------- |
| `adr/0001-productization-server-and-profile-editor.md`                   | 产品化本地服务端、REST Profile 接口、城市定位与设置窗口的架构交接。  | Accepted |
| [ADR-0002](adr/0002-scene-model-rethink-and-neutral-baseline.md)         | 旧匹配心智的溯源、整体模型重审与中立随机基准。                       | Accepted |
| [ADR-0003](adr/0003-scene-probability-budgets-and-preference-cascade.md) | 偏好级联、正向召回与负向排除、变量预算、条件场景概率及尽力选择。     | Accepted |
| [ADR-0004](adr/0004-context-salience-and-observation-boundaries.md)      | 有符号显著度、有限活动轨迹、季节与时段锚点、天气共同推导及观测边界。 | Accepted |

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
