# Repository Guidelines

## 工作意见

本项目大版本号为 0，即允许破坏性变更。若旧接口或旧心智影响新功能实现，以经过确认的目标和设计为主。旧产物是经过认真设计后的成果，在与新功能不冲突时应作为参考。

## 项目结构与模块组织

本项目是面向 Wallpaper Engine 的调度增强用 Windows-only 桌面应用，含核心调度模块、系统托盘入口、本地 API 服务和前端界面。

- `app/`：提供应用入口、初始化、日志和版本记录。
- `configurations/` 提供用户配置、配置编译、配置持久化和 运行时配置
- `core/` 提供调度器核心模块。
- `server/` 提供本地 API 服务。
- `integrations/` 含 OpenWeatherMap、IP 查询的外部集成
- `ui/` 提供系统托盘包装、前端 WebView 窗口，附带国际化、图标资源和历史导出。
- `frontend/` 前端页面，现提供初始配置和运行时设置。
- `config/` 是本机真实运行配置目录，其中的 `profile.json`，可用于真实运行。
- `tests/` 放 pytest 测试。
- `docs/` 按规格生命周期管理，索引见 `docs/index.md`。

### 核心架构概述与阅读入口（`engine.schedule()`）

```
Sense:    ContextManager.sense()       # 获取原始上下文信息，并写入统一 Context 对象
Select:   Selector.select()            # 各 Policy 根据 Context 计算显著度，Selector 基于显著度、场景关联、匹配配置给出概率分布
Decide:   Controller.decide_action()   # 根据执行模式、场景概率、防打扰条件决定该 tick 行动
Execute:  Actuator.act()               # 根据 Decision 执行 Controller 决策，从场景概率得到目标 Playlist，并调用 WE CLI 进行实际切换
Commit:   SchedulerState.commit()      # 提交当前 tick。
```

`Engine.schedule()` 提供完整的调度流程：sense、select、decide、execute，并返回 `ScheduleResult`。`ProfileManager` 负责 Profile 加载、编译、持久化和应用队列；`app/main.py` 创建 `ProfileManager`，将同一实例交给 Bottle API、首次启动流程和 `Scheduler`。`Scheduler` 依赖注入的 `ProfileManager`，同时持有活动 `engine`，并编排生命周期、tick、暂停恢复、keep_alive、状态提交和 listener 通知。Profile 更新由 `ProfileManager` 入队，并且只由调度线程在两个 tick 之间应用到 Engine。`Actuator` 是纯执行器：接收 `Decision` 做 target selection + CLI 调用。

## 关键模块

以下对部分关键模块的职责做简要说明。

### configurations/

configurations 处理用户配置 `profile.json` 到运行时模型的编译、配置的持久化存储。

- `profile` 系列文件：定义 Profile Schema 、Store、Compiler。
- `runtime_models.py`：定义调度器的运行时配置 Schema。

### core/

`core/` 是调度器的核心模块，它定义绝大多数调度器运行逻辑。

1. `models`

定义运行时数据模型及契约。

- `scene.py`：定义场景集合 Scenes 和播单绑定 SceneBinding。
- `context.py`：定义调度器采集的上下文 Context 和对应的 ContextManager。
- `selection.py`：定义选择模型，即 Policy 和 Select 阶段的数据模型，定义上下文变量、语义项和显著度。
- `scheduling.py`：定义 Controller 和 Actuator 的数据模型，包括调度器动作、执行模式、时序状态和完整的 `ScheduleResult`。
- `trace.py`：定义 TickTrace，为 ScheduleResult 扩展时间、编号和暂停信息。

2. `policies/` 以及 `sensors`

各自定义 Policy 和 Sensor 的基类及具体实现。

3. `runtime/`

最核心的运行时模块，绝大部分业务逻辑都在这里实现。任何对于调度器业务逻辑的讨论、设计、开发和测试都必须在理解 `runtime/` 的基础上进行。具体而言，必须先阅读任务涉及的真实调用链、数据契约和数据流向。

- `profile_manager.py`：提供 `ProfileManager`，统一管理 Profile 初次读取、编译、持久化、应用队列。
- `selector.py`：提供 `Selector`，负责推动 Policy 计算显著度并计算场景概率分布。
- `controller.py`：提供 `Controller`，根据执行模式、场景概率、防打扰约束确定本 tick 的 Decision。
- `timing.py`：由 Controller 持有，根据前后两次场景分布的差异度、轮换冷却间隔进行择时评估。
- `disturbance.py`：由 Controller 持有，根据空闲、CPU 和全屏状态评估防打扰条件。
- `actuator.py`：将高层决策 Decision 转换为实际 WE CLI 调用
- `executor.py`： WE CLI 封装，内置 keep_alive 保活
- `engine.py`：持有上述子模块，编排为完整的单次调度流水线。提供原子化配置变更接口，提供 WE 保活的便利方法。
- `scheduler.py`：持有 `Engine` 、 `ProfileManager` 和 `SchedulerState`。其中，`Engine` 管理具体调度逻辑，并提供初始化和配置变更接口；`ProfileManager` 用于管理 Profile；`SchedulerState` 用于管理调度器状态。`Scheduler` 协调三大组件，定义生命周期方法、运行时锁、主循环，暂停恢复、tick 结束时的 hook。

1. `state/`

负责调度器运行时状态和持久化输出的管理

- `scheduler.py`：定义调度器的运行时状态，提供状态流转方法。
- `persisted.py`：定义需跨进程持久化的调度器状态。
- `tick_history.py`：定义最近窗口的 tick 历史，用于导出分析。
- `action_events.py`：按事件类型记录并导出调度器动作。

### server/

- `app.py`： Bottle 应用组合根与健康检查、Tick History 路由
- `routes/profile.py|profile_support.py`：业务逻辑路由

## 构建、测试与本地开发常用命令

- 本项目使用虚拟环境进行开发和构建，目录为根目录的 `.venv/`

- 开发与构建命令：

```bash
pip install -r requirements.txt # 构建依赖
pip install -r requirements-dev.txt # tools 以及 tests 依赖
python main.py # 运行 Tunalo
```

- 测试命令

pytest 配置以 `pytest.ini` 为准。测试命令须通过 `.\scripts\test.ps1` 运行。该脚本对 pytest 模块进行包装。它为每次运行分配独立唯一目录以支持多 `pytest` 并行测试，并在测试完毕后自动清理残留。使用方法与 pytest 相同。

```shell
.\scripts\test.ps1 tests/test_foo.py -q # 运行单个测试文件
.\scripts\test.ps1 -q # 运行所有测试
```

- Windows 打包命令

```bash
.\scripts\build.bat
```

脚本会启动虚拟环境、安装依赖并完成资源打包。

- 指定端口方便前端联调：

```bash
python main.py --api-port 38417
cd frontend
npm run dev
```

如需其他端口，保持后端端口与前端 `TUNALO_API_PORT=<port>` 一致；默认端口是 `38417`。

- 编码规范要求：

所有 Python 文件修改完毕后，应用 Ruff 格式化

```powershell
python -m ruff check . --fix
python -m ruff format .
```

- 前端开发构建命令：

```bash
npm run type-check
npm run build-only
```

前端工作后应运行 `npm run type-check` 和 `npm run build-only`。

## 编码风格与命名约定

Python 代码使用完整类型注解。模块、类、函数职责清晰，函数名、变量名自解释。非必要不使用注释，但对会抛出异常的函数必须用 docstring 说明异常类型和触发条件。

产品界面使用 `frontend/` 的 shadcn-vue 组件和语义 token，保持 Vite `base: './'`、URL query locale 和 pywebview 本地加载；引入路由时使用 hash router。

## 补充材料

- `CONTEXT.md`：领域术语，用于校准用词规范
