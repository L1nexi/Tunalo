# 上下文感知壁纸调度

本上下文统一描述 Scheduler 如何根据用户处境形成壁纸语义，并控制 Wallpaper Engine 播单。这里只记录本项目中特有且容易混淆的概念。

## 调度

**Scheduler**:
持续推进 Tick 并协调完整调度生命周期的主体。Scheduler 是 Orchestrator ，屏蔽具体实现。
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

**Salience**:
显著度，当前观测与必要近期轨迹对某个语义项的支持或违和程度。正向表示支持，零表示中性或不存在，负向表示反向；它独立于用户偏好与场景目录。
_避免使用_: Intensity

**Context Variable**:
承载一类上下文信息的粗变量，例如天气、活动、时段、季节。用户可以表达这些变量之间的响应偏好。
_可接受别名_: 上下文变量、粗变量

**Semantic Item**:
上下文变量下可以被支持或反向的具体语义，例如雨、工作（`work`）、娱乐（`leisure`）、白天、夏季。Scene 可以关联一个或多个 Semantic Item。
_可接受别名_: 语义项
_避免使用_: Context Variable

**Preference Tier**:
用户显式指定、具有同等偏好地位的上下文变量集合。多个层级按用户偏好程度排列，用于级联寻找可响应的上下文。
_可接受别名_: 偏好层级

**Variable Budget**:
显式偏好层中用于响应某个上下文变量的选择机会份额。它描述概率的来源；一个场景可以承接多个来源，因此来源预算不等于最终场景覆盖。
_可接受别名_: 变量预算、来源预算
_避免使用_: 场景概率、Policy 权重

**OTHER**:
未识别或未观察到明确方向的活动。它是活动轨迹中的零方向，不是场景可关联的语义项。
_可接受别名_: 游移
_避免使用_: Idle、空闲、娱乐

## 场景与播单

**Selector**:
根据上下文语义、用户偏好与可用场景关联形成完整场景选择概率分布的选择器。选择概率表示场景获得的选择机会，具体抽样属于执行侧。
_可接受别名_: 场景选择器
_避免使用_: Matcher

**Scene**:
产品预设的壁纸语义角色，由 SceneId 标识。Scene 承载匹配语义。
_可接受别名_: 场景
_避免使用_: Playlist

**Scene Semantic Association**:
Scene 与一个或多个语义项的关联，表达该场景适合响应的情境。它由产品定义，不描述绑定播单中的画面气质。
_可接受别名_: 场景语义关联、语义关联
_避免使用_: SceneBinding、播单标签

**Scenes**:
由零个、一个或多个 Scene 身份组成的候选集合，也是表达 Cached Scenes 与 Active Scenes 的场景领域值。
_可接受别名_: 场景集合、场景池
_避免使用_: Playlists

**Selection**:
当前上下文下各 Scene 的完整选择概率分布，以及本次选择所依据的显著度和来源。它表达选择机会，尚未抽取具体 Scene。
_可接受别名_: 场景选择结果
_避免使用_: Similarity、相似度、采样结果

**SceneBinding**:
一个已启用 Scene 与一个具名 Wallpaper Engine Playlist 的绑定，表达用户希望该场景呈现的画面。多个 Scene 可以绑定同一个 Playlist；未绑定的 Scene 不参与调度。
_可接受别名_: 场景播单绑定
_避免使用_: Scene、Playlist

**FactualPlaylistStatus**:
从 Wallpaper Engine 得到的外部播单事实类别：`PLAYLIST`、`NO_PLAYLIST`、`UNKNOWN` 或 `AMBIGUOUS`，用于判断是否需要恢复调度管理。
_避免使用_: Active Scenes

**Cached Distribution**:
上次成功执行所采用的完整场景选择分布，是衡量当前推荐变化的跨 Tick 参照。
_可接受别名_: 成功分布缓存、Scheduler Memory
_避免使用_: 上个 Tick 的分布、已抽中的场景

**Cached Scenes**:
Cached Distribution 中具有正选择概率的场景集合，表示最近成功执行所采用的场景池。
_可接受别名_: cached\*scenes
_避免使用_: Active Scenes、Current Playlist

**Active Scenes**:
当前 Tick 执行前，最近一次成功执行所采用的场景池快照。
_可接受别名_: active\*scenes
_避免使用_: Cached Scenes、FactualPlaylistStatus

**Scene Lowering**:
在执行边界按本次 Selection 的概率抽取一个 Scene，再找到其绑定的 Wallpaper Engine Playlist 的过程。同播单的不同 Scene 保留身份和概率，播单大小不改变选择机会。
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
