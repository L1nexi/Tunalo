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
- `core/math_utils.py`：概率归一化、幅度曲线、单点指数衰减与周期插值的纯数学函数。
- `server/`：本地接口与设置页静态资源。
- `frontend/`：首次设置和运行时设置界面。
- `config/profile.json`：用户配置；`data/`：运行状态与事件；`logs/scheduler.log`：运行日志。

需要排查天气或本地服务时，可临时设置 `TUNALO_LOG_LEVEL=DEBUG`。分享日志前请检查敏感内容。产品化规划、验收事项和后续改进见 [文档索引](index.md)。

## 场景选择模型

Profile 使用版本 2，偏好字段为 `matching.preference_tiers`，空列表表示中立回退。旧响应风格已移除；旧格式走配置验证失败路径。实施不会自动迁移或覆盖本机配置。

`activity` 保留用户自定义规则：`work_processes`、`leisure_processes`、`work_title_keywords`、`leisure_title_keywords`。进程按名称精确匹配并统一可选的 `.exe` 后缀，标题按关键词包含匹配，两者都忽略大小写；同一个标准化目标不能同时归入工作与休闲。省略 `activity` 或设为 `null` 时使用内置默认规则；显式提供对象时完全使用其中的规则，空对象表示不识别活动。这三种状态在保存和重新加载后保持不变。

`ProfileCompiler` 处理用户 Profile 和内置规则，生成完整运行时配置。`runtime_models.py` 只定义运行时数据，不依赖 Profile 或活动规则表；直接构造 `ActivityPolicyConfig()` 得到空规则列表。

前端恢复到场景选择模型实施前的版本，保留活动规则编辑页面。目前前端仍使用原有 Profile 契约，尚未接入新版后端；待界面设计确认后再调整。

### 运行时契约与历史记录

`core/models/selection.py` 集中语义词表、Salience、各 Policy 的求值与解释信息，以及 Selection。ContextVariable 和 SemanticItem 均为 StrEnum，序列化沿用原有小写字符串值。Policy、Selector 和配置编译直接使用这些选择契约。

`core/models/scheduling.py` 定义规划、控制和执行契约。`Engine.schedule()` 返回 ScheduleResult，保留本次 Context、Selection、ActPlan、Decision 和 ActionResult。其 target 表示执行后的有效场景：成功切换时为决策目标，其余情况沿用执行前场景。

`core/models/trace.py` 只定义 TickTrace，为 ScheduleResult 添加 tick 编号、时间和暂停信息。模型依赖方向为 trace → scheduling → selection。缓存更新规则由 SchedulerState.commit 掌握，仅成功切换且场景集合变化时持久化；TickTrace 不决定缓存提交。

Tick History 继续保留最近 1200 次记录及现有 HTTP 读取、托盘导出、DTO 和脱敏规则。Policy 和控制器的解释字段完整保留，不改为调试日志。

### 天气共同推导

天气按“晴朗／阴天／降水，降水内分雨雪”共享关系。代码表只给出正向依据，`WeatherPolicy` 统一推导支持与反向证据，不为四个语义项各写一张独立代码表。

记晴朗、阴天、雨、雪的正向依据为 `c`、`o`、`r`、`s`，公共降水强度 `p=max(r,s)`，弱反向系数 `a=0.25`。当前计算为：晴朗 `c-p-a*o`；阴天 `o-a*c-a*min(p,1)`；雨 `r-c-a*o`；雪 `s-c-a*o`。降水对晴朗的强反向随强度变化，对阴天的弱反向在降水强度超过 1 后保持为 -0.25。

800～804 的正向依据依次为晴朗 1、晴朗 0.75、晴朗／阴天各 0.25、阴天 0.75、阴天 1。它们是内部校准初值。示例：晴朗输出 `(1,-0.25,-1,-1)`，全阴输出 `(-0.25,1,-0.25,-0.25)`，大雨输出 `(-1,-0.25,1,0)`，暴雨输出 `(-2,-0.25,2,0)`；元组顺序为晴朗、阴天、雨、雪。

已知代码优先，即使推导结果全零也不按主分类重解释。未知代码时，`Clear`、`Clouds` 分别提供晴朗／阴天 1，`Rain`、`Drizzle`、`Snow` 沿用雨 0.5、雨 0.2、雪 0.75 的初值。没有观测或无法识别时保持全零；请求失败时继续解释 Sensor 的既有缓存。归档规则表中的雨雪正向强度仍沿用，晴朗／阴云全零的旧说明已由这里取代。

Selector 的场景输入只有 SceneId 和等地位语义关联。`calculate_distribution(Salience, associations, MatchingConfig)` 是运行时与调参工具共用的纯概率入口；它调用匹配流程中的 `salience_to_scene_scores(salience, associations)` 取得逐场景评分。观测序列通过 `Selector.select(context)` 或真实 Policy 的 `evaluate(context)` 回放。

活动轨迹保存工作、休闲、OTHER 类别，不用整数隐含方向。支持与反向关系由 ActivityPolicy 统一定义，分别汇总各语义项的证据后再应用幅度曲线。ActivityPolicy 组织 600 个年龄采样点，并选定指数衰减的尺度、底数和幂次；数学工具不提供业务窗口接口。每次新观测推进一槽，状态热替换复制分类观察，进程重启不恢复轨迹。

模型回归在既有公开入口验证：纯概率入口的独立 SPEC 算例与分布性质、真实 Policy 的观测序列、Profile 保存和编译，以及真实 Engine 的执行结果。不会为私有分类器、评分辅助函数或状态容器单开测试；测试替身仅用于 Windows、网络、时钟、随机源、文件系统和 Wallpaper Engine 执行边界。

```powershell
.\.venv\Scripts\python.exe tools/tuning/calibrate.py
.\.venv\Scripts\python.exe tools/tuning/scan.py --mode wx-act --out new-model-wx-act
```

前者导出三类显著度曲线及 1800 槽的完整场景分布；后者输出二维概览与 `distributions.json`。静态活动轴直接表示有符号显著度，不注入活动内部状态。工具只使用专用数据。
