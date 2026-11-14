# 开发与验证

本项目仅支持 Windows，使用仓库根目录的 `.venv/` 进行开发和构建。

## 环境与依赖

```powershell
pip install -r requirements.txt      # 运行依赖
pip install -r requirements-dev.txt  # 工具与测试依赖
```

## 本地运行

```powershell
python main.py
```

单独联调设置前端时，先启动本地服务，再在另一个终端启动前端：

```powershell
python main.py --api-port 38417
```

```powershell
cd frontend
npm run dev
```

如需其他端口，保持后端端口与前端 `TUNALO_API_PORT` 一致；默认端口是 `38417`。

## 测试

pytest 配置以 `pytest.ini` 为准。测试须通过 `.\scripts\test.ps1` 运行；脚本为每次运行分配独立目录以支持并行测试，结束后自动清理，其余参数继续传给 pytest：

```shell
.\scripts\test.ps1 tests/core/test_selection_model.py -q  # 运行单个测试文件
.\scripts\test.ps1 -q                                      # 运行常规测试
.\scripts\test.ps1 -Tuning -q                              # 只运行调参工具集成测试
.\scripts\test.ps1 -All -q                                 # 运行全部测试
```

调参工具的扫描与绘图测试要遍历完整网格并生成热图，单独运行约 80 秒，因此常规测试默认跳过；指定测试路径时按路径运行。改动 `tools/tuning/` 或场景概率输出后，加 `-Tuning` 验证。

<<<<<<< HEAD
前端界面测试在 `frontend/` 中运行，使用本机 Edge：

```powershell
cd frontend
npm ci
npm run test:e2e -- --reporter=line --workers=2
```

=======

> > > > > > > 015ddb3 (test: 调参工具集成测试默认跳过)

## 打包

```powershell
.\scripts\build.bat
```

脚本会启动虚拟环境、安装依赖并完成资源打包，产物在 `dist\Tunalo.exe`。

## 持续交付

开发阶段的 pytest、Ruff、前端检查与构建在本地完成。GitHub Actions 只在推送 `v*` 标签时构建 Windows 发布包并创建 Release；Runner 上不运行 Wallpaper Engine，实际启动和壁纸切换仍在本机验证。

发布前在本机运行：

```powershell
.\scripts\test.ps1 -q
python -m ruff check .
python -m ruff format --check .
.\scripts\build.bat --no-pause
```

构建后运行 `dist\Tunalo.exe`，确认设置窗口、托盘和 Wallpaper Engine 连接正常。

## 发布

1. 更新 `src/app/version.py` 的 `VERSION`。
2. 在 `CHANGELOG.md` 顶部把 `[Unreleased]` 内容整理为 `## [x.y.z] - YYYY-MM-DD` 段落，分隔符用短横线或破折号均可。
3. 提交后创建并推送标签：

   ```powershell
   git tag vx.y.z
   git push origin vx.y.z
   ```

4. 标签触发 [release.yml](../.github/workflows/release.yml)：校验标签、`VERSION` 与 CHANGELOG 段落一致，构建 `dist\Tunalo.exe`，生成 `Tunalo-vx.y.z-windows-x64.zip`、`SHA256SUMS.txt` 与发布说明，最后创建 Release。

标签必须匹配 `v<major>.<minor>.<patch>`；不支持预发布标签（如 `v0.13.0-rc.1`，不会触发发布）。构建或版本校验失败时不会创建 Release。

本地验证发布包：

```powershell
.\scripts\build.bat --no-pause
python scripts\release.py package --tag vx.y.z
```

产物位于 `dist\release\`。

## 代码风格

所有 Python 文件修改完后，应用 Ruff 格式化：

```powershell
python -m ruff check . --fix
python -m ruff format .
```

前端工作在 `frontend/` 中完成，提交前运行：

```powershell
npm run type-check
npm run build-only
```
