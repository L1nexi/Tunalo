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
- `server/`：本地接口与设置页静态资源。
- `frontend/`：首次设置和运行时设置界面。
- `config/profile.json`：用户配置；`data/`：运行状态与事件；`logs/scheduler.log`：运行日志。

需要排查天气或本地服务时，可临时设置 `TUNALO_LOG_LEVEL=DEBUG`。分享日志前请检查敏感内容。产品化规划、验收事项和后续改进见 [文档索引](index.md)。

## 场景选择模型

Profile 使用版本 2，偏好字段为 `matching.preference_tiers`，空列表表示中立回退。旧响应风格和用户活动规则已移除；旧格式走配置验证失败路径。实施不会自动迁移或覆盖本机配置。

Selector 的场景输入只有 SceneId 和等地位语义关联。`calculate_distribution(Salience, associations, MatchingConfig)` 是运行时与调参工具共用的纯概率入口；观测序列通过 `Selector.select(context)` 或真实 Policy 的 `evaluate(context)` 回放。活动轨迹每次新观测推进一槽，诊断读取不推进；状态热替换只传递分类后的方向。

```powershell
.\.venv\Scripts\python.exe tools/tuning/calibrate.py
.\.venv\Scripts\python.exe tools/tuning/scan.py --mode wx-act --out new-model-wx-act
```

前者导出三类显著度曲线及 1800 槽的完整场景分布；后者输出二维概览与 `distributions.json`。静态活动轴直接表示有符号显著度，不注入活动内部状态。工具只使用专用数据。
