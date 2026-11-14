---
status: accepted
date: 2026-10-17
updated: 2026-11-14
---

# ADR-0005：按场景分布变化统一执行时机，拆分时序与防打扰职责

[ADR-0003](0003-scene-probability-budgets-and-preference-cascade.md) 让选择侧输出完整场景概率分布，[ADR-0004](0004-context-salience-and-observation-boundaries.md) 明确了构建显著度的观测边界。本次决定用当前分布与上次成功分布的距离计算等待阈值，统一场景跟随与日常轮换。Controller 持有并编排时序、防打扰两个模块；成功历史归时序模块，日志与历史记录消费调度结果。

## 背景

旧执行层按正概率场景集合是否相等区分 `SWITCH` 和 `CYCLE`，会丢掉选择机会变化的程度。例如 `{A: 0.99, B: 0.01}` 变成 `{A: 0.01, B: 0.99}`，倾向几乎反转，集合却没变；新增一个极小概率场景，又会被视为需要立即跟随的集合变化。

## 决策

### 从候选集合改为完整分布

改为缓存上次成功执行采用的完整分布。场景跟随与日常轮换共用 `APPLY`，分布变化越大，等待阈值越短；变化小时由基础轮换间隔控制。取消 `force_after` 及超时绕过空闲的行为，普通执行始终遵守同一套防打扰条件。

### 距离、参考尺度与等待阈值

设本 tick 的有效推荐分布为 \(P_t\)，上次成功执行采用的完整分布为 \(Q\)。这里保存的是抽样前的分布，包含所有候选的选择机会。分布距离采用全变差：

$$
d_t=\operatorname{TV}(P_t,Q)=\frac12\sum_{c\in\operatorname{supp}(P_t)\cup\operatorname{supp}(Q)}|P_t(c)-Q(c)|
$$

缺失场景的概率按零计。两个有效分布的距离在 \([0,1]\) 内，表示需要转移的概率质量。

设当前启用场景数为 \(N\)，场景 \(c\) 的关联变量集合为 \(V_c\)，采用配置结构的参考尺度：

$$
d_{\mathrm{ref}}=\frac{\sum_c|V_c|}{4N}
$$

令 \(C\) 为基础轮换间隔，\(t*{\mathrm{last}}\) 为上次成功执行时间，\(\Delta_t=t-t*{\mathrm{last}}\)。每 tick 重新计算：

$$
T(d_t)=
\begin{cases}
C,&d_t=0\\
\min\left(C,\;1\mathrm{s}\cdot\max\left(0,\left(\frac{2d_{\mathrm{ref}}}{d_t}\right)^5-1\right)\right),&d_t>0
\end{cases}
$$

幂次取 \(\gamma=5\)

| 当前变化                    | 等待阈值                |
| --------------------------- | ----------------------- |
| \(d_t=0\)                   | \(C\)                   |
| \(d*t=d*{\mathrm{ref}}\)    | \(\min(C,31\text{秒})\) |
| \(d*t\ge2d*{\mathrm{ref}}\) | 0                       |

### 记录侧消费已提交的结果

Engine 形成单轮 `ScheduleResult`，SchedulerState 提交时将它连同轮次、时间和暂停信息放入 `TickTrace`，Scheduler 再通过 tick listener 交给消费者。Trace 保留结果对象，消费者分别读取结果和提交信息，避免在两者上维护重复的属性入口。

三类记录各自回答不同的问题：运行日志记录程序运行、执行结果和异常；Event Log 持久化保存启动、暂停与动作结果等稀疏事件；Tick History 在内存中有界保留逐轮判断，供近期诊断和导出。

场景抽样与执行结果的日志由动作记录侧在提交后统一输出，使一次记录同时包含目标和执行结果。执行器保留命令超时、返回码和异常等底层诊断。这样，新增记录字段时可优先使用已有结果，调度模块继续负责形成判断和执行动作。

记录字段与接口见[日志与历史记录规格](../archived/done/LOGGING_AND_HISTORY_SPEC.md)；tick listener 沿用 [ADR-0006 的替代安排](0006-in-process-events-and-scheduler-consumption.md#弃用原因与替代安排)。
