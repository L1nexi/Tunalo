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

pytest 配置以 `pytest.ini` 为准。测试须通过 `.\scripts\test.ps1` 运行；脚本为每次运行分配独立目录以支持并行测试，结束后自动清理。用法与 pytest 相同：

```shell
.\scripts\test.ps1 tests/core/test_selection_model.py -q  # 运行单个测试文件
.\scripts\test.ps1 -q                                      # 运行所有测试
```

## 打包

```powershell
.\scripts\build.bat
```

脚本会启动虚拟环境、安装依赖并完成资源打包，产物在 `dist\Tunalo.exe`。

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
