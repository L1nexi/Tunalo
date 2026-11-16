# 应用内更新方案比较

研究日期：2026-11-17。归档状态：用户认为当前尚未到实施时机，应用内更新已暂缓，调查保留在暂停区。尚未实施或做实机 POC（用最小程序验证关键行为）。

用户已明确可以调整分发方式，优先更新可靠和长期易维护。下文保留调查时的方案建议，具体设计尚未确认；恢复时应重新核对项目现状和工具文档。

## 归档时的建议

推荐 **Velopack + GitHub Releases**，先验证它生成的免安装便携 ZIP，首版使用全量更新。应用侧使用官方 Python SDK（应用内调用的开发包），保留托盘和设置页自己的提示。通过验证后，再确定发布布局、用户数据迁移和首次升级方式。

Velopack 目前有官方 Python 接入、GitHub 更新源、检查、下载和应用更新接口，也能生成可更新的便携 ZIP。应用代码无需因此增加 C#；开发和 CI 环境要增加 .NET SDK 与 `vpk` 打包工具。这些能力分别见 [Python 指南](https://docs.velopack.io/getting-started/python)、[Python GithubSource](https://docs.velopack.io/reference/py/Sources/GithubSource) 和[打包产物说明](https://docs.velopack.io/packaging/overview)。

这次迁移会增加目录构建、数据迁移和发布格式调整的工作，但能让更新框架承担包下载、更新执行器和程序目录替换。后续仍需管理框架版本和发布配置。相比自行维护一个长期工作的 Windows 更新器，这些接入和维护工作更符合目前“可靠、易维护”的偏好。这个判断仍要由便携版 POC 验证；尤其要看现有宿主和窗口子进程能否正常退出，以及数据能否连续保留。

## 当前项目的约束

- [构建脚本](../../scripts/build.bat) 使用 PyInstaller `--onefile`，产物为 `Tunalo.exe`。
- [发布脚本](../../scripts/release.py) 生成 `Tunalo-v<版本>-windows-x64.zip` 与 `SHA256SUMS.txt`，ZIP 内含 exe、README、CHANGELOG 和 `.env.example`；当前没有安装器。
- [应用路径](../../src/app/context.py)、[启动入口](../../src/app/main.py)和[日志初始化](../../src/app/logging.py)以 exe 所在目录为默认根目录，`config/`、`data/`、`logs/` 和 `.env` 围绕该目录存放。`--config` 可指定外部配置位置。
- [TODO](../TODO.md) 要求启动后检查、托盘和设置页提示、手动检查、点击后下载校验并退出替换重启；离线和检查失败不影响正常使用。

“免安装”和“只有一个 exe”可以分别选择。Velopack 的便携 ZIP 能保留解压运行的使用方式，但会改变包内目录结构。

## 方案对照

| 方案 | 已有能力 | Tunalo 仍需承担 | 迁移与维护判断 |
| --- | --- | --- | --- |
| Velopack + GitHub Releases | Python SDK、版本源、下载、应用更新和重启；安装器与便携 ZIP；可选差分包 | 自己的提示界面、检查时机、正常退出、数据布局与首次迁移、配置备份策略 | 推荐。接受目录构建和新发布格式后，可减少自写更新执行代码。[官方 Python 接入](https://docs.velopack.io/getting-started/python)、[打包](https://docs.velopack.io/packaging/overview) |
| Inno Setup + GitHub Releases | 创建安装器、安装和卸载、文件替换、运行程序检测、签名接入 | 应用持续检查新版本、下载和校验安装器、更新提示；安装脚本及数据迁移 | 适合明确需要安装向导和自定义安装规则时采用。只为本次更新需求引入，仍要自己写较多更新逻辑。[功能](https://jrsoftware.org/inno-setup)、[CloseApplications](https://jrsoftware.org/inno-setup/documentation/topic_setup_closeapplications.htm) |
| Windows MSIX + App Installer | Windows 管理应用包安装与更新；可按启动检查、后台检查或提示策略配置 | MSIX 打包、签名与证书信任、App Installer 文件、数据路径迁移；自己的设置页状态与按钮接入 | 平台承担更多部署工作，但分发和运行布局变化较大。当前优先级低于 Velopack。[自动更新](https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview)、[包签名](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview) |
| WinSparkle + 安装器 | DLL 提供版本 feed 检查、原生提示、下载和更新物签名验证，随后交给安装器 | Python 的 C API 绑定、feed 发布、安装器；若保留直接替换 exe，还要自己处理替换 | 适合愿意采用其原生更新窗口、并已有安装器的程序。Tunalo 仍要做两种界面接入和安装逻辑。[接入](https://winsparkle.org/guides/integrating-winsparkle/)、[发布](https://winsparkle.org/guides/publishing-updates/) |
| Python 自写检查 + 独立辅助进程 | 可以沿用现有 ZIP 和单 exe，所有行为都由项目控制 | 检查、下载、验证、解包、等待退出、替换失败恢复、重启和更新器自身维护 | 保留现布局的直接方案。当前用户已允许迁移，省下的打包改动不足以抵消长期维护更新执行器的责任。下文列出边界。 |

这些是适合本项目比较的几类方案，本文没有用下载量或市场份额给它们排序。

## Velopack 的接入边界

### Python 接入与独立更新器

官方 Python 包提供 `App().run()` 和 `UpdateManager`。启动时应先运行 Velopack 初始化，再执行正常应用启动，因为安装或更新过程中会用特殊参数调用应用，并要求它快速退出。Python API 支持分别检查、下载、应用更新，也有带重启参数的方法，适合将操作接到 Tunalo 自己的按钮上。[Python 指南](https://docs.velopack.io/getting-started/python)、[Python UpdateManager](https://docs.velopack.io/reference/py/UpdateManager)、[生命周期调用](https://docs.velopack.io/integrating/hooks)

`Update.exe` 是 Velopack 管理包和应用更新的执行器。公开 CLI 包含 `apply`、`start`、`patch` 和 `uninstall`，其中 `apply` 可等待指定进程退出并接受待应用的包。它采用 Velopack 的包与目录布局；直接拿一个 `Update.exe` 并不能让现有任意 ZIP 自动获得完整更新能力。[Update.exe CLI](https://docs.velopack.io/reference/cli/content/update-windows)

官方 Python 指南明确要求 PyInstaller 使用 `--onedir`，并写明 `--onefile` 不兼容。接入时应按官方目录构建方式验证。`vpk` 在构建端需要 .NET SDK，这不等于用户电脑需要为了 Python 应用安装 .NET。[Python 打包要求](https://docs.velopack.io/getting-started/python)

### 便携 ZIP 与用户数据

`vpk pack` 会生成便携 ZIP、Setup、全量 `.nupkg` 更新包和 `releases.<channel>.json` 版本索引；可选生成差分包。便携 ZIP 用于免安装运行和更新，后续更新读取版本索引和更新包，现有普通 ZIP 加 SHA256 文件需要调整发布流程。[产物](https://docs.velopack.io/packaging/overview)、[分发与版本索引](https://docs.velopack.io/distributing/overview)

Windows 的标准结构包含根目录入口、`Update.exe` 和 `current/` 程序目录，实际应用文件位于 `current/`。更新会完整替换 `current/`，所以目前把可变数据放在实际 exe 旁的做法必须改动。官方建议更新后仍要保留的数据放到 `current/` 外；安装型应用若要求卸载后也保留数据，可放 `%AppData%\{packId}`。[Windows 布局](https://docs.velopack.io/packaging/operating-systems/windows)、[保留文件和设置](https://docs.velopack.io/integrating/preserved-files)

对 Tunalo 的初步布局建议是把便携版的 `config/`、`data/`、`logs/` 和 `.env` 放在便携包根目录，使它们随用户移动整个文件夹；程序资源留在 `current/`。这是本项目的设计提议，便携 ZIP 的实际产物布局、入口名称和运行时路径取得方式要在 POC 中确认。采用安装型分发时，应单独确定 AppData 数据目录。

### 失败处理、差分与签名

官方 Windows 文档说明：程序目录被占用时，更新器会尝试结束其中的进程；仍被占用时查找其他占用者，提示用户结束或取消；无法识别占用者时提示错误并启动旧版。这能省去一部分文件锁处理，但 Tunalo 仍应先正常关闭调度器、窗口和其他子进程，避免由更新器强制结束。[Windows 更新行为](https://docs.velopack.io/packaging/operating-systems/windows)

Velopack 能生成和选择差分更新包，差分即只传输前后版本变化的内容。首版可关闭差分，先验证全量更新。差分传输和新版本健康检测后自动退回旧版是不同能力；本研究只核实了前述特定文件锁失败时启动旧版的行为，没有把通用健康检测和自动回退计入收益。[差分说明](https://docs.velopack.io/packaging/deltas)

Windows 代码签名是发布者用证书为程序证明身份和完整性的机制。Velopack 在 Windows 上建议签名，但基础使用不强制；正式分发时应按所用版本的打包工具配置签名，让应用、Setup 和 Update 等生成物都得到处理。签名需要另外管理证书或签名服务，也不能承诺用户完全看不到 SmartScreen 提示。[Windows 要求](https://docs.velopack.io/packaging/operating-systems/windows)、[签名接入](https://docs.velopack.io/packaging/signing)

## 其他方案的关键限制

Inno Setup 负责安装执行，可以关闭占用待更新文件的应用、替换文件、安装后运行程序，也支持不提权的当前用户安装。它的下载能力是在 Setup 运行期间下载文件。应用常驻时何时检查 GitHub、展示哪个版本、何时下载安装器，仍需要应用或另一个更新库负责。这是按其功能边界作出的集成判断。[CloseApplications](https://jrsoftware.org/inno-setup/documentation/topic_setup_closeapplications.htm)、[当前用户安装](https://jrsoftware.org/inno-setup/documentation/topic_setup_privilegesrequired.htm)、[Files 下载和校验](https://jrsoftware.org/inno-setup/documentation/topic_filessection.htm)、[安装器签名](https://jrsoftware.org/inno-setup/documentation/topic_setup_signtool.htm)

MSIX 将程序安装到受保护的位置，程序文件不能按当前方式直接写入；数据要与程序包分开。App Installer 能承担包更新检查和部署，但需要新增 `.appinstaller` 和包清单，并选择更新策略。直接分发的 MSIX 包必须签名，签名还必须得到设备信任；开发用自签名证书不等于普通用户可以直接安装。由此带来的数据迁移和分发要求，是本次没有把它列为首选的原因。[运行目录和数据](https://learn.microsoft.com/en-us/windows/msix/msix-containerization-overview)、[自动更新配置](https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview)、[签名与信任](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview)

WinSparkle 对外提供 C API。Python 可以通过标准库 `ctypes` 调用 DLL；这需要维护函数签名和回调线程处理，属于本项目的集成工作。版本信息来自 appcast，即包含版本和下载地址的 RSS 文件；官方流程使用 HTTPS feed，并对下载的更新文件做 EdDSA 签名验证。这里签名的是更新文件，不能直接称作“feed 已签名”。其常见流程下载并运行 MSI、Inno Setup 或 NSIS 安装器；也可接管下载物的处理，但接管后如何替换现有 exe 仍要自己写。[C API 接入](https://winsparkle.org/guides/integrating-winsparkle/)、[Python ctypes](https://docs.python.org/3/library/ctypes.html)、[更新签名](https://winsparkle.org/guides/getting-started/)、[feed 与安装器](https://winsparkle.org/guides/publishing-updates/)、[自定义安装回调](https://winsparkle.org/c-api/callbacks/)

## 自写 Python 更新器要维护的内容

如果继续使用普通 ZIP 和单 exe，最小可行方式是由主程序检查和下载，再启动独立辅助进程，等待旧程序退出后替换并重启。维护范围至少包括：

1. 选择稳定版与正确架构的附件；为离线、代理、限流和部分下载设置超时、缓存与退避。
2. 在临时位置下载和校验，限制解包路径，只更新明确的程序文件，保留配置、日志与其他用户文件。
3. 确认所有使用旧 exe 的进程都已退出，处理重复更新、权限不足、杀毒软件占用和重启参数。
4. 在替换中断或失败后恢复可运行状态，保留诊断信息；另行设计新版本启动失败时的恢复机制和配置兼容策略。
5. 管理辅助进程的分发、临时文件清理和自身更新。打包后的程序不能假设用户另有 Python 环境。

GitHub 最新 Release 接口支持公开资源的匿名读取，附件有下载 URL，摘要字段可能为空；匿名 REST 请求按 IP 限流。因此，自写方案需要自己处理这些规则。Velopack 有 GitHub 源，也仍需 Tunalo 选择检查时机和失败后的产品表现。[最新 Release](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)、[附件字段](https://docs.github.com/en/rest/releases/assets)、[请求限流](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)、[Velopack Python GithubSource](https://docs.velopack.io/reference/py/Sources/GithubSource)

当前 SHA256 文件可以用于检查下载物是否与发布摘要一致；若包和摘要都来自同一发布账户，它没有增加独立的发布者身份验证。选择 Velopack、Inno Setup 或自写方案后，都应明确区分下载完整性校验、更新文件签名和 Windows 代码签名。

PyInstaller 对“通过自身 exe 启动一个要在原进程退出后继续运行的新进程”还有环境重置要求；从 6.9 起，相关重启场景需要设置 `PYINSTALLER_RESET_ENVIRONMENT=1`。这是继续维护单文件辅助进程方案时要纳入的打包约束。[PyInstaller 重启说明](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#using-sys-executable-to-spawn-subprocesses-that-outlive-the-application-process-implementing-application-restart)

Python 还有 `tufup` 备选。它建立在 `python-tuf` 上，采用带签名的 TUF 元数据、压缩包和可选补丁发布仓库，并有自己的 Windows 安装脚本；应用界面和进程退出仍归应用负责。采用它需要再学习 TUF 的更新信任模型和发布密钥管理，本次没有展开为首选。[tufup 官方仓库](https://github.com/dennisvang/tufup)

## 净维护成本与验证范围

采用 Velopack 后，Tunalo 仍要开发托盘和设置页交互、后台检查调度、正常退出流程，以及用户配置备份与迁移。这些工作本来就是本 TODO 的产品需求，不能全部计为框架节省的工作。

主要节省的是自行维护更新执行器的责任：安装更新包、程序目录切换、更新器分发及一部分 Windows 文件锁处理。新增成本是目录构建、Velopack 初始化、数据目录迁移、`vpk` 和 SDK 版本管理、GitHub 发布产物调整，以及已有用户首次迁移的引导。用户接受分发调整后，建议承担这些迁移成本。

本文核实了官方支持和公开行为，尚未验证 Tunalo 的实际兼容性，也没有根据“有 Python SDK”推断其集成已经成熟。官网可能比稳定版本文档更新更快；正式实现应固定 SDK 和 `vpk` 版本，用同一版本做验证。

恢复研究时，可先用两个连续版本做 POC，集中验证四件事：

- 便携 ZIP 解压后直接运行，跨版本全量更新后配置、历史、日志和 `.env` 都保留。
- 托盘宿主与 `--window` 子进程正常退出，更新成功后恢复必要启动参数；更新不产生重复实例。
- 离线、限流、取消下载、损坏更新物、目录不可写和文件占用时，现有程序保持可用，并能再次尝试。
- 更新只在预定的用户操作后应用；首次从现有单 exe 分发迁入新目录时，有明确的数据位置和恢复办法。

POC 若能通过，就按 Velopack 制定实现规格；若便携模式有不可接受的限制，再比较它的当前用户安装器与自写辅助进程。
