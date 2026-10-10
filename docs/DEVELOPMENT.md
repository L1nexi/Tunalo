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
- `core/math_utils.py`：softmax、S 形曲线与周期插值的共用数学工具。
- `server/`：本地接口与设置页静态资源。
- `frontend/`：首次设置和运行时设置界面。
- `config/profile.json`：用户配置；`data/`：运行状态与事件；`logs/scheduler.log`：运行日志。

需要排查天气或本地服务时，可临时设置 `TUNALO_LOG_LEVEL=DEBUG`。分享日志前请检查敏感内容。产品化规划、验收事项和后续改进见 [文档索引](index.md)。

## 场景选择模型

Profile 使用版本 2，偏好字段为 `matching.preference_tiers`，空列表表示中立回退。旧响应风格已移除；旧格式走配置验证失败路径。实施不会自动迁移或覆盖本机配置。

`activity` 保留用户自定义规则：`work_processes`、`leisure_processes`、`work_title_keywords`、`leisure_title_keywords`。进程按名称精确匹配并统一可选的 `.exe` 后缀，标题按关键词包含匹配，两者都忽略大小写；同一个标准化目标不能同时归入工作与休闲。省略 `activity` 或设为 `null` 时使用内置默认规则；显式提供对象时完全使用其中的规则，空对象表示不识别活动。这三种状态在保存和重新加载后保持不变。

`ProfileCompiler` 处理用户 Profile 和内置规则，生成完整运行时配置。`runtime_models.py` 只定义运行时数据，不依赖 Profile 或活动规则表；直接构造 `ActivityPolicyConfig()` 得到空规则列表。

前端恢复到场景选择模型实施前的版本，保留活动规则编辑页面。目前前端仍使用原有 Profile 契约，尚未接入新版后端；待界面设计确认后再调整。`trace` 与 `semantics` 的职责及类型归属调整留到后续提交，本轮不改诊断实现。

Selector 的场景输入只有 SceneId 和等地位语义关联。`calculate_distribution(Salience, associations, MatchingConfig)` 是运行时与调参工具共用的纯概率入口；观测序列通过 `Selector.select(context)` 或真实 Policy 的 `evaluate(context)` 回放。活动轨迹每次新观测推进一槽，诊断读取不推进；状态热替换只传递分类后的方向。

```powershell
.\.venv\Scripts\python.exe tools/tuning/calibrate.py
.\.venv\Scripts\python.exe tools/tuning/scan.py --mode wx-act --out new-model-wx-act
```

前者导出三类显著度曲线及 1800 槽的完整场景分布；后者输出二维概览与 `distributions.json`。静态活动轴直接表示有符号显著度，不注入活动内部状态。工具只使用专用数据。
