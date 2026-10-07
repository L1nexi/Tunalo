# 上下文感知壁纸调度

本上下文统一描述 Scheduler 如何根据用户处境形成壁纸语义，并控制 Wallpaper Engine 播单。这里只记录本项目中特有且容易混淆的概念。

## 调度

**Scheduler**:
持续推进 Tick、持有 Scheduler Memory，并协调完整调度生命周期的主体。Scheduler 是 Orchestrator 主体，不了解下层实现。
_可接受别名_: 调度器
_避免使用_: Engine

**Engine**:
绑定当前运行时配置、承载单个 Tick 调度管线的核心运行时对象。
_避免使用_: Scheduler

**Tick**:
Scheduler 的逻辑时间单位；它表示一个调度时间间隔。
_避免使用_: TickTrace、Action

## 语义

**Context**:
一个 Tick 中用于形成壁纸语义和控制判断的观测集合。

**Policy**:
当前观测与必要近期轨迹到各语义项有符号显著度的映射，表达支持或违和证据；它独立于用户偏好和场景目录。
_避免使用_: Blocker、Control Directive

**Tag Direction**:
Policy 当前倾向的各标签之间的相对比例，只表达语义方向，不表达总体影响大小。

**Salience**:
显著度，当前观测与必要近期轨迹对某个语义项的支持或违和程度。正向表示支持，零表示中性或不存在，负向表示反向；它独立于用户偏好与场景目录。
_避免使用_: Intensity

**Context Variable**:
承载一类上下文信息的粗变量，例如天气、活动、时段、季节。用户可以表达这些变量之间的响应偏好。
_可接受别名_: 上下文变量、粗变量

**Semantic Item**:
上下文变量下可以被支持或反向的具体语义，例如雨、工作、白天、夏季。Scene 可以关联一个或多个 Semantic Item。
_可接受别名_: 语义项
_避免使用_: Context Variable

**Preference Tier**:
具有同等偏好地位的上下文变量集合。多个层级按用户偏好程度排列，用于级联寻找可响应的上下文。
_可接受别名_: 偏好层级

**Intensity**:
强度，即被观测现象自身的强度，与信号归属是否清晰相互独立。
_避免使用_: Salience

**Response Style**:
用户对场景匹配更偏重背景氛围还是当前情境的偏好。它只改变各类 Context 对匹配结果的相对影响，不改变切换等待、阻塞或执行时机。
_可接受别名_: 响应风格
_避免使用_: Temporal Horizon、时间尺度偏好、调度风格、场景偏好、调度灵敏度、切换积极度

**Wandering**:
活动缺少持续的主导方向、注意力在不同方向间游移的内部语义，也近似容纳少量有方向但尚未被识别的活动。Wandering 不向用户开放为可关联的活动语义项。
_中文暂称_: 游移
_避免使用_: Idle、空闲

## 场景与播单

**Selector**:
根据上下文语义、用户偏好与可用场景关联形成完整场景选择概率分布的选择器。选择概率表示场景获得的选择机会，具体抽样属于执行侧。
_可接受别名_: 场景选择器
_避免使用_: Matcher

**Scene**:
产品预设的壁纸语义角色，由 SceneId 标识。Scene 承载匹配语义。
_可接受别名_: 场景
_避免使用_: Playlist

**Scenes**:
由零个、一个或多个 Scene 身份组成的语义候选集合，也是 Scheduler 在 matching、控制与跨 Tick 记忆中使用的场景领域值。
_可接受别名_: 场景集合、场景池
_避免使用_: Playlists

**Semantic Continuity**:
相邻 Tick 的 Scenes 在语义上的延续程度。共同 Scene 及其壁纸数量决定连续性强弱；不同 Scene 即使关联同一个 Playlist，也仍保持各自的语义身份。
_可接受别名_: 语义连续性
_避免使用_: Playlist Continuity、集合全等

**Scene Assignment**:
一个已启用 Scene 到一个具名 Wallpaper Engine Playlist 的关联，表达用户希望该场景呈现的画面。多个 Scene 可以关联同一个 Playlist；未建立关联的 Scene 不参与调度。
_可接受别名_: 场景关联
_避免使用_: Scene、Playlist

**FactualPlaylistStatus**:
从 Wallpaper Engine 得到的外部播单事实类别：`PLAYLIST`、`NO_PLAYLIST`、`UNKNOWN` 或 `AMBIGUOUS`。它是推导 Active Scenes 的依据之一，不等于 Scheduler 对当前语义状态的认知。
_避免使用_: Active Scenes

**Cached Scenes**:
lowering 前 Scenes 的跨 Tick Scheduler Memory，使 Scheduler 能从 Wallpaper Engine 暴露的单个 Playlist 恢复原来的场景集合身份。
_可接受别名_: cached\*scenes、Scheduler Memory
_避免使用_: Active Scenes、Current Playlist

**Active Scenes**:
当前 Tick 中 Scheduler 认为处于活跃状态的 Scenes，由外部播单事实与 Cached Scenes 共同推导。
_可接受别名_: active\*scenes
_避免使用_: Cached Scenes、FactualPlaylistStatus

**Scene Lowering**:
在执行边界从一个 Scenes 候选集合选出具体 Wallpaper Engine Playlist 的过程。每个候选 Scene 按其绑定 Playlist 的壁纸数量独立贡献选择权重，因此多个 Scene 绑定同一 Playlist 时会共同提高该 Playlist 的权重；lowering 不改变 Scenes 的语义身份。
_可接受别名_: lowering
_避免使用_: matching

**Playlist**:
系统与 Wallpaper Engine 交互边界上的单个具名播单，是外部观测结果或 lowering 目标。
_可接受别名_: 播单
_避免使用_: Scene、Scenes

## 诊断记录

**Tick History**:
近期、密集、仅在内存中有界保留的逐 Tick 调度记录，用于解释 Scheduler 的近期判断。
_避免使用_: Event Log

**Event Log**:
持久化保存启动、暂停、播单变化和执行失败等稀疏运行事件的记录，不包含每个 Tick 的完整过程。
_避免使用_: Tick History
