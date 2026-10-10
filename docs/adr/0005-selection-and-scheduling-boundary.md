---
status: accepted
date: 2026-10-11
---

# 选择形成概率，调度决定时机，执行边界负责抽样

新模型改变了语义与概率，若仍沿用旧候选截断、连续性计算或按播单大小抽取，实际播放就会背离模型。决定明确选择、调度和历史记录的职责，只完成必要消费接入，保留已有免打扰门槛；不把本轮模型重构扩展为新的切换算法。

## 组合与状态所有权

沿用 Sensor、Policy、Engine 的组合，Matcher 更名为 Selector。`Engine.schedule()` 先 `ContextManager.sense()`，再 `Selector.select(context)`；Selector 持有并调用 Policy，汇集显著度并返回完整 Selection，不采集外部数据，也不抽取 Scene。不另拆 Observer 或统一语义管理类，语义构建与概率计算的逻辑边界已经足够清楚。

活动轨迹由 ActivityPolicy 持有，Selector 只代理状态导入导出。热替换接续分类后的轨迹，用新构建参数重新解释，不根据旧窗口重新分类，也不转换旧 EMA。Engine 先准备隔离的替换对象，Profile 持久化成功后才安装；准备或持久化失败不改变运行中的配置与轨迹。Sensor 与 TimePolicy 沿用重建生命周期，配置替换不迁移天气缓存或时段峰值。

共用纯入口 `calculate_distribution(Salience, associations, MatchingConfig)` 负责确定性概率计算，不推进活动历史。运行时与调参工具复用该入口，观测回放使用真实 Policy 或 `select(context)`，不复制一套调参算法，也不注入私有历史状态。通用数学函数集中在 `core/math_utils.py`，活动窗口、语义关系和参数选择仍归业务组件。

## 消费概率与提交状态

Controller 使用正概率 Scene 的身份集合：与当前活跃集合相同走轮换门槛，不同走切换门槛。删除旧连续性、集合相似度和衰减状态，但保留启动等待、空闲、CPU、全屏与轮换冷却，以及手动应用和恢复的既有门槛行为。

Decision 携带本次完整概率，Actuator 仅在真正执行切换或轮换时按它抽取 Scene，再查询绑定 Playlist。阻塞和暂停不抽样，同播单 Scene 不合并，不按壁纸数量加权，不取概率最大者。同一候选集合内概率改变时，下次允许轮换使用最新分布，不新增每 Tick 重抽、概率距离阈值或立刻切换。

无候选时保持已有播放或不动作，不为了执行补造候选。跨 Tick 缓存继续保存候选身份集合，只在成功切换且集合变化时持久化；执行失败不提交，不将缓存改成抽中的单个 Scene，也不持久化概率。这保留 Wallpaper Engine 暴露单个播单时恢复场景集合身份的既有语义。

## 类型与诊断边界

- `selection.py` 定义语义词表、显著度、Policy 求值与解释，以及 Selection。
- `scheduling.py` 定义规划、控制、执行和完整 ScheduleResult；它保留 Context、Selection、ActPlan、Decision、ActionResult。
- `trace.py` 只为 ScheduleResult 添加 Tick 编号、时间与暂停信息。TickTrace 不决定缓存提交，提交规则归 SchedulerState。

分层依赖为 `trace → scheduling → selection`。选择机会、调度决策与实际抽样结果分别记录，不能把旧 similarity 字段换名后继续表达另一种含义。

保留现有 Tick History 的有界内存、HTTP 读取、托盘导出、展示精度和脱敏范围，完整保留 Policy 与控制器解释；Event Log 继续记录稀疏运行事件，不替代 Tick History，也不持久化密集活动轨迹。不把已有历史导出改成调试日志。

## 配置与交付边界

Profile 是唯一用户配置入口，版本 2 用 `matching.preference_tiers` 替代旧响应风格；内部边界、温度、语义关联和曲线参数由产品维护。保留自定义活动识别规则，不将它们与内部数值调参混为一项。[ADR-0001](0001-productization-server-and-profile-editor.md) 的 ProfileStore、ProfileManager 单写者应用队列与调度安全点继续沿用。

项目处于 `0.x`，直接拒绝旧格式，不猜测旧风格对应的新层级，也不添加配置转换或算法兼容路径；正式本机 Profile 不由实施或测试自动覆盖。后端模型与配置契约已实现，但本轮前端改动已撤回，现有界面仍使用旧 Profile 契约。恢复自定义活动页面不等于新版偏好界面完成，模型验收与完整产品接入验收必须分别判断。

进一步设计切换稳定性、同集合概率变化如何响应，或者改动缓存含义，需要独立决策；本次保留旧门槛并不确认它们是最终调度模型。

当前实现与行为证据：[Engine](../../core/runtime/engine.py)、[Controller](../../core/runtime/controller.py)、[Actuator](../../core/runtime/actuator.py)、[SchedulerState](../../core/state/scheduler.py)、[选择管线测试](../../tests/test_selection_pipeline.py)、[Profile 应用测试](../../tests/test_profile_manager.py)。开发和接入状态见[开发指引](../DEVELOPMENT.md)。
