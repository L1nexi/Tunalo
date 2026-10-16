# 开发与验证

本项目仅支持 Windows。正式运行配置是 `config/profile.json`；本机已有配置不能作为测试样本覆盖或清空。

## 本地运行

在仓库根目录的 `.venv/` 中安装 Python 依赖：

```powershell
pip install -r requirements.txt
python main.py
```

单独联调设置前端时，先启动本地服务，再于另一个终端启动前端：

```powershell
python main.py --api-port 38417
```

```powershell
cd frontend
npm run dev
```

如需其他端口，请保持后端端口与前端的 `TUNALO_API_PORT` 一致。

## 检查与构建

```powershell
.\scripts\test.ps1 -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format . --check
```

在 `frontend/` 中运行：

```powershell
npm test
npm run test:e2e
npm run type-check
npm run build-only
```

设置页浏览器测试会启动独立的 Vite 服务，并在浏览器边界替代本地接口响应，不会读取或修改真实 `config/profile.json`。Windows 发布包由仓库根目录的 `scripts/build.bat` 构建；该脚本会清理既有的 `build/` 和 `dist/`。

## 实现入口

- `app/main.py`：托盘进程、首次设置和本地服务启动。
- `core/runtime/profile_manager.py`：配置读取、编译、保存和运行时应用。
- `core/runtime/selector.py`：Policy 求值、有符号显著度汇集，以及共用的确定性概率计算。
- `core/math_utils.py`：概率归一化、完整支持轴激活、时间衰减、相位映射与周期距离映射的纯数学函数。
- `server/`：本地接口与设置页静态资源。
- `frontend/`：首次设置和运行时设置界面。
- `config/profile.json`：用户配置；`data/`：运行状态与事件；`logs/scheduler.log`：运行日志。

需要排查天气或本地服务时，可临时设置 `TUNALO_LOG_LEVEL=DEBUG`。分享日志前请检查敏感内容。产品化规划、验收事项和后续改进见 [文档索引](index.md)。

## 场景选择模型

决策与取舍分别见 [ADR-0003：偏好级联与概率预算](adr/0003-scene-probability-budgets-and-preference-cascade.md)、[ADR-0004：显著度构建与观测边界](adr/0004-context-salience-and-observation-boundaries.md)。本文维护当前实现入口与可调整的内部取值，领域概念见 [CONTEXT.md](../CONTEXT.md)。

### Profile 与界面接入

Profile 使用版本 2，偏好字段为 `matching.preference_tiers`，空列表直接尽力选择；显式偏好穷尽后也直接尽力选择。旧响应风格已移除；旧格式走配置验证失败路径。实施不会自动迁移或覆盖本机配置。

`activity` 保留用户自定义规则：`work_processes`、`leisure_processes`、`work_title_keywords`、`leisure_title_keywords`。进程按名称精确匹配并统一可选的 `.exe` 后缀，标题按关键词包含匹配，两者都忽略大小写；同一个标准化目标不能同时归入工作与休闲。省略 `activity` 或设为 `null` 时使用内置默认规则；显式提供对象时完全使用其中的规则，空对象表示不识别活动。这三种状态在保存和重新加载后保持不变。

`ProfileCompiler` 处理用户 Profile 和内置规则，生成完整运行时配置。`runtime_models.py` 只定义运行时数据，不依赖 Profile 或活动规则表；直接构造 `ActivityPolicyConfig()` 得到空规则列表。

前端恢复到场景选择模型实施前的版本，保留活动规则编辑页面。目前前端仍使用原有 Profile 契约，尚未接入新版后端；待界面设计确认后再调整。

### 内部参数与规则入口

以下为 2026-10-13 的实现取值，不是用户设置，也不将所有初值固定成长期决策。调整参数继续满足 ADR 的感知锚点、分布性质与暴雨排序约束。

| 参数 | 当前值 | 实现入口 |
| --- | --- | --- |
| 正向边界、负向边界幅度 | 暂定 0.9、0.1；`s >= 0.9` 召回，`s <= -0.1` 排除 | `MatchingConfig` |
| 变量温度、场景温度 | 1.4、1.5；前者控制显式偏好层的来源预算，后者控制场景概率的探索程度 | `MatchingConfig` |
| 活动窗口、年龄尺度 | 600 槽、300 槽半权重点；600 槽及之后权重为零 | `ActivityPolicy.WINDOW_SIZE`、`ActivityPolicyConfig.age_scale` |
| 活动显著度 | 年龄加权净证据直接输出，不再套用幅度曲线 | `ActivityPolicy` |
| 季节、时段曲线参数 | 各自的 `activation_alpha` 均为 2，有限且大于 1，两者独立 | 对应 PolicyConfig |
| 时段相位映射参数 | `phase_gamma` 默认 2，有限且不小于 1；1 为线性映射 | `math_utils.mirrored_phase` 的函数参数 |
| 季节周期、四季峰值 | 365 日；80／172／265／355 | `SeasonPolicy`、`SeasonPolicyConfig` |
| 季节平台半宽、时段平台 | 本位与相对位置前后 7 日；时段无平台 | `SeasonPolicyConfig`、`TimePolicy` |
| 天气弱反向系数 | 0.25 | `WeatherPolicy` |

`salience_activation(x, alpha=2)` 使用对称幂函数覆盖完整的 [-1,1] 支持轴，保持零点和正负对称，两端平、中心陡。`periodic_salience` 将距各自峰值的最短周期距离归一到这条支持轴，平台只位于最支持与最不支持两端。季节采用实际年内日期，邻季峰值的输出接近零而不强制精确为零；时段保留真实昼夜锚点到虚拟时间的映射。完整轴上的 Hann 对照为 `sin(πx/2)`。

`mirrored_phase(u, phase_gamma=2, reverse=False)` 负责段内幂映射。TimePolicy 在黎明→白天、夕阳→夜晚时使用镜像 `1-(1-u)^gamma`，白天→夕阳、夜晚→黎明时使用 `u^gamma`；调用函数默认参数，再放入对应的六个虚拟小时区间，逐项计算周期显著度。镜像映射拓宽白天、夜晚的高显著区，收窄黎明、夕阳，保留峰值、零点、周期闭合和两对语义的取反关系。日出 06:00、日落 18:00、alpha=2、gamma=2 时，达到 0.9 的范围分别约为 7.33 小时与 2.50 小时。

天气、活动、时段显式同层时，变量温度需满足 `T_V < 1/ln(2)`，使雨显著度为 2、白天和工作各为 1、候选仅雨天与日间工作时，雨天概率更高。当前温度下约为 50.5284%／49.4716%，只是指定参数的算例；后续校准不要求保持这组精确数值。当前降雨标尺中，大雨为 2、暴雨为 4。

配置定义见 [runtime_models.py](../configurations/runtime_models.py)。十个 Scene 的直接语义关联集中在 [ProfileCompiler](../configurations/profile_compiler.py)：四个日间／夜间工作和娱乐场景分别关联时段与活动，四季、黄昏和雨天分别关联对应单项语义。雪、黎明等没有独立预设，不补回旧标签回退，也不由讨论中的复合例子自动扩充产品目录。

内置活动规则集中在 [activity_rules.py](../configurations/activity_rules.py)，天气正向强度和主分类回退集中在 [WeatherPolicy](../core/policies/weather.py)。这些表由实现维护，不在文档中复制另一份逐应用或逐代码配置；解释天气字段时参考 [OWM 开发参考](archived/reference/OPENWEATHER_CURRENT_API.md)。

### 运行时契约与历史记录

`core/models/selection.py` 集中语义词表、Salience、各 Policy 的求值与解释信息，以及 Selection。ContextVariable 和 SemanticItem 均为 StrEnum，序列化使用小写字符串值，活动语义项为 `work/leisure`。Policy、Selector 和配置编译直接使用这些选择契约。

`core/models/scheduling.py` 定义规划、控制和执行契约。`Engine.schedule()` 返回 ScheduleResult，保留本次 Context、Selection、ActPlan、Decision 和 ActionResult。其 target 表示执行后的有效场景：成功切换时为决策目标，其余情况沿用执行前场景。

`core/models/trace.py` 只定义 TickTrace，为 ScheduleResult 添加 tick 编号、时间和暂停信息。模型依赖方向为 trace → scheduling → selection。SchedulerState.commit 在成功执行后接收完整分布，分布变化时持久化；Cached Scenes 由其中的正概率场景推导。候选集合相同而概率不同，也会更新缓存。旧状态只有场景身份，不能还原原分布，因此按无成功分布缓存处理。

Tick History 继续保留最近 1200 次记录及现有 HTTP 读取、托盘导出、DTO 和脱敏规则。Policy 和控制器的解释字段完整保留，不改为调试日志。

### 执行时序与防打扰

Controller 持有并编排 TimingControl 与 DisturbanceControl，Engine 继续通过 Controller 决策。前者管理启动等待和切换阈值，后者只检查空闲、CPU 和全屏。运行时配置分别为 `timing` 与 `disturbance`；Profile 中删除 `maximum_deferral_minutes`，其余三个用户计时字段保留原位置。旧 Profile 若仍含删除的字段，会验证失败；本机配置不自动迁移。

成功分布缓存统一命名为 `cached_scenes_probabilities`。ActPlan 只保存执行模式与完整缓存分布，`active_scenes` 是从正概率场景派生的 property。`plan_actuation` 根据 WE 状态、手动请求和暂停确定模式，调用方通过 `Controller.decide_action(plan, context, selection)` 决策。外部播单状态只影响模式，成功分布仍是时序比较的参照。

设本 tick 推荐分布为 P，上次成功执行所采用的分布为 Q，启用场景数为 N，场景 c 的去重语义关联集合为 A_c：

$$
d=\frac12\sum_c|P(c)-Q(c)|,\qquad d_{\mathrm{ref}}=\frac{\sum_c|A_c|}{4N}
$$

Profile 至少启用一个场景，每个场景的语义关联集合非空，因此参考尺度为正。首次没有 Q 时直接取 d=1。没有安全场景时不执行，也不以空分布覆盖 Q。

令 C 为基础轮换间隔，x=d/d_ref。每 tick 重算等待阈值：

$$
T(d)=\begin{cases}
C,&x=0\\
\min\left(C,\max\left(0,\left(\frac2x\right)^5-1\right)\mathrm{s}\right),&x>0
\end{cases}
$$

变化达到 d_ref 时阈值为 min(C,31 秒)，达到 2d_ref 时为零。启动等待结束、通过防打扰检查，且距上次成功执行已满 T(d) 时执行。变化出现时不会另开计时；例如上次成功执行已过两分钟，此时阈值变为 31 秒，本 tick 就满足时序条件。采集和选择在启动等待及阻挡期间持续进行，每次使用最新分布，不积压待执行意图。

普通轮换与场景响应统一为 `APPLY`，不再根据候选集合是否相等区分动作，也不再超时绕过空闲。执行时仍由 Actuator 按最新推荐分布抽取场景并应用播单。只有成功执行才推进成功时间和 Q；失败、阻挡和无候选均保留原参照。手动、恢复和暂停沿用原有特殊路径。配置替换保留成功时间、启动等待截止时间和缓存，参考尺度按新配置重算。

Tick History 的 `controller.timing` 记录距离、参考尺度、阈值、已过时间和剩余等待，`controller.disturbance` 记录防打扰条件。成功事件统一为 `scenes_applied`。[时序行为测试](../tests/test_runtime_behavior.py) 从 Controller.decide_action 观察结果。

### 天气共同推导

天气按“晴朗／阴天／降水，降水内分雨雪”共享关系。代码表只给出正向依据，`WeatherPolicy` 统一推导支持与反向证据，不为四个语义项各写一张独立代码表。

记晴朗、阴天、雨、雪的正向依据为 `c`、`o`、`r`、`s`，公共降水强度 `p=max(r,s)`，弱反向系数 `a=0.25`。当前计算为：晴朗 `c-p-a*o`；阴天 `o-a*c-a*min(p,1)`；雨 `r-c-a*o`；雪 `s-c-a*o`。降水对晴朗的强反向随强度变化，对阴天的弱反向在降水强度超过 1 后保持为 -0.25。

降雨锚点为小雨 0.75、中雨 1、大雨 2、暴雨 4。毛毛雨、阵雨、冻雨和混合降水的雨强随这些锚点重新校准；中间取值按锚点间插值确定，雪的正向标尺沿用当前值。

雷暴由雨景承接，雨显著度表达用户对雨景情境的感知，不只表达雨量。轻雷暴（210）取 2，普通雷暴（211）、不规则雷暴（221）取 3，强雷暴（212）取 4。伴随小雨、普通降雨或毛毛雨的雷暴（200、201、230～232）仍取 3，伴随强降雨的雷暴（202）取 4；不因雨量较小而削弱雷暴本身的显著度。

800～804 的正向依据依次为晴朗 1、晴朗 0.75、晴朗／阴天各 0.25、阴天 0.75、阴天 1。它们是内部校准初值。示例：晴朗输出 `(1,-0.25,-1,-1)`，全阴输出 `(-0.25,1,-0.25,-0.25)`，大雨输出 `(-2,-0.25,2,0)`，暴雨输出 `(-4,-0.25,4,0)`；元组顺序为晴朗、阴天、雨、雪。

已知代码优先，即使推导结果全零也不按主分类重解释。未知代码时，`Clear`、`Clouds` 分别提供晴朗／阴天 1，`Rain`、`Drizzle`、`Snow` 使用雨 1、雨 0.6、雪 0.75 的初值，`Thunderstorm` 使用雨 3。没有观测或无法识别时保持全零；请求失败时继续解释 Sensor 的既有缓存。雨雪的正向强度及中间代码取值以 WeatherPolicy 为准，不把早期晴朗／阴云全零处理恢复为当前行为。

### 概率计算、回放与行为验证

Selector 的场景输入只有 SceneId 和等地位语义关联。`calculate_distribution(Salience, associations, MatchingConfig)` 是运行时与调参工具共用的纯概率入口；它调用匹配流程中的 `salience_to_scene_scores(salience, associations)` 取得逐场景评分。观测序列通过 `Selector.select(context)` 或真实 Policy 的 `evaluate(context)` 回放。

活动轨迹保存工作（`work`）、娱乐（`leisure`）、游移（`other`）类别，不用整数隐含方向。支持与反向关系由 ActivityPolicy 统一定义，分别加权汇总各语义项的证据，取净值并按完整窗口分母归一后直接输出。ActivityPolicy 组织 600 个年龄采样点，调用 `time_decaying_activation(age, scale=age_scale)`；该函数以默认 alpha=2 激活 `max(1-age/scale,-1)`，再将输出平移到 [0,1]。不新增活动 alpha 参数，数学工具不提供业务窗口接口。每次新观测推进一槽，状态热替换复制分类观察，进程重启不恢复轨迹。

模型回归在既有公开入口验证：ADR 中的约束实例与分布性质、真实 Policy 的观测序列、Profile 保存和编译，以及 Controller 的决策结果。测试替身仅用于 Windows、网络、时钟、随机源、文件系统和 Wallpaper Engine 执行边界。

| 行为证据 | 入口 |
| --- | --- |
| 无偏好分布、简单与复合场景、显式预算、级联、排除、尽力选择与边界 | [test_selection_model.py](../tests/test_selection_model.py) |
| 完整支持轴、有限衰减终点、周期最短距离和峰值平台 | [test_math_utils.py](../tests/test_math_utils.py) |
| 活动窗口、季节平台、真实昼夜锚点及天气支持与反向关系 | [test_semantic_model.py](../tests/test_semantic_model.py) |
| 偏好编译、播单名称与大小无关、自定义活动规则及保存回填 | [test_profile_compiler.py](../tests/test_profile_compiler.py) |
| 分布变化时序、启动等待、防打扰和配置替换后的时间保留 | [test_runtime_behavior.py](../tests/test_runtime_behavior.py) |
| Profile 初始化、首次创建及应用时机 | [test_profile_manager.py](../tests/test_profile_manager.py) |
| 单语义项 suite 的无偏好分布、二项复合竞争与排除、固定轴的标准组合 | [test_tuning.py](../tests/test_tuning.py) |

确定性测试与曲线验证不能代替真实 Windows、天气网络和 Wallpaper Engine 验收，也不代表长期主观体验校准完成。模型与后端消费的验收不覆盖当前尚未接入的新版设置界面；后续事项见 [TODO](TODO.md)。

```powershell
.\.venv\Scripts\python.exe tools/tuning/calibrate.py --alpha 2 --out tools/tuning/runs/model-calibration-power-alpha2
.\.venv\Scripts\python.exe tools/tuning/scan.py --suite single --alpha 2 --out single-power-alpha2
.\.venv\Scripts\python.exe tools/tuning/scan.py --suite pairs --alpha 2 --out pairs-power-alpha2
.\.venv\Scripts\python.exe tools/tuning/scan.py --suite single --curve hann --out single-hann-full-axis
.\.venv\Scripts\python.exe tools/tuning/scan.py --suite pair-wx-act --alpha 2 --out weather-activity-pair
.\.venv\Scripts\python.exe tools/tuning/scan.py --suite product --mode wx-act --out product-wx-act
```

`calibrate.py` 导出三类显著度曲线、1800 槽的完整场景分布及 `parameters.json`。`scan.py` 默认扫描单语义项 suite，可通过 `--suite product` 使用产品场景。两个工具的 `--alpha` 都只控制 Time、Season；Activity 的年龄权重仍使用默认 alpha=2。`--curve current` 使用默认生产激活曲线；`--curve hann` 在独立调参进程中替换完整支持轴的激活函数，沿用真实 Policy 的峰值、平台和概率计算，Hann 不使用 alpha。

单语义项 suite 有 13 个场景：春、夏、秋、冬；晴朗、阴天、雨；黎明、白天、黄昏、夜晚；工作、娱乐。每个场景只关联对应的一个语义项。调参场景有自己的标识，产品场景仍由 ProfileCompiler 定义；共享概率入口按输入关联计算。偏好默认为空。

二项复合按两个粗变量分为六套。每套保留全部 13 个单项基线，再加入两个变量间的全部组合；每个复合场景关联两个等地位语义项，例如 `rain_work` 关联雨与工作。

| suite | 复合变量 | 新增场景 | 默认扫描 |
| --- | --- | ---: | --- |
| `pair-wx-doy` | 季节×天气 | 12 | `wx-doy` |
| `pair-hour-doy` | 季节×时间 | 16 | `hour-doy` |
| `pair-act-doy` | 季节×活动 | 8 | `act-doy` |
| `pair-wx-hour` | 天气×时间 | 12 | `wx-hour` |
| `pair-wx-act` | 天气×活动 | 6 | `wx-act` |
| `pair-act-hour` | 时间×活动 | 8 | `act-hour` |

`--suite pairs` 顺序扫描六套，分别输出到对应 suite 目录。二项 suite 默认只扫描自己的两条轴；显式 `--mode` 可覆盖默认范围。标准扫描共生成 146 张图。各套使用相同基线，便于观察复合场景进入后如何承接和分配概率。

六种扫描模式使用同一组固定轴取点。扫描两条轴时，剩余两条轴各取四点，按笛卡尔积组成 16 个子图，统一排成 4×4。

| 固定轴 | 峰值态、偏向过渡态、中间态、另一峰值态 |
| --- | --- |
| 时间 | 白天峰 12:00、偏白天 13:30、白天／黄昏中点 15:00、黄昏峰 18:00 |
| 季节 | 春峰 80、偏春 103、春夏中点 126、夏峰 172；日期按当前季节峰值推导 |
| 活动 | 工作 1、偏工作 0.75、中等工作证据 0.5、中性 0 |
| 天气 | 无天气、小雨 500、中雨 501、大雨 502 |

季节中点指日期中点，实际显著度由选定曲线决定。活动 0 表示无明确工作或娱乐方向，不单独建立空闲场景。扫描步长沿用时间 0.5 小时、日期 4 日、活动 0.05；天气扫描轴补齐小雨与暴雨。

输出按 suite、再按扫描模式建目录。每个模式包含各场景的概率热图和一张 `winner-map.png`。概率图共用 `0–100%` 色标，胜者图展示每格概率最大的场景；并列时沿用 suite 的场景顺序，无正概率场景时标为 `no winner`。完整概率及 suite、曲线、场景关联、固定点和采样参数写入 suite 目录的 `distributions.json`。`--alpha` 调整 Time、Season 的激活函数并写入运行参数，校准工具也支持；相位映射沿用数学函数默认值。静态活动轴直接表示有符号显著度，不注入活动内部状态。工具只使用专用数据。

胜者图按场景语义配色：工作为蓝色、娱乐为粉紫色；春季新绿、夏季日光金、秋季落叶赭、冬季冰蓝；晴朗为天蓝、阴天为灰色、雨景为灰蓝；黎明浅桃、白天金黄、黄昏珊瑚橙、夜晚靛蓝。二项场景混合两项语义色并略微压暗，以区分单项基线；日间／夜间工作与娱乐复用产品对应场景的配色，日间浅、夜间深。图例只展示当前 suite，颜色定义集中在 `heatmaps.py` 的 `SCENE_COLORS`。

```text
tools/tuning/runs/<run-name>/
└── single/
    ├── distributions.json
    ├── cur-act-doy/
    │   ├── work.png
    │   ├── day.png
    │   ├── rain.png
    │   ├── winner-map.png
    │   └── ...
    ├── cur-wx-hour/
    │   └── ...
    └── cur-hour-doy/
        └── ...
```
