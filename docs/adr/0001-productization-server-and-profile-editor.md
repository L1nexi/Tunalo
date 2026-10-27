---
status: partially-deprecated
date: 2026-09-23
---

# ADR-0001：配置编辑的本地服务端与桌面边界

## 状态

部分过时。2026-10-27 复核确认两项失效条款：后端提供内置场景目录、首次创建必须校验天气。当前场景预设由前端管理，天气校验允许用户选择跳过。下文保留原决策。

## 背景

首次配置和运行时设置需要共享配置编辑能力。原有 HTTP 服务位于 `ui/`，接口沿用首次引导的 `setup` 命名；设置窗口的进程状态和聚焦策略散落在应用入口。需要划清 HTTP、桌面表现与配置应用的职责。

## 决策

1. **独立本地服务端。** 在 Python 源码根下设置 `server/`：`host.py` 接收已构造的应用，管理端口、线程与启停；`app.py` 组合 Bottle 应用；`routes/` 处理请求校验与 HTTP 错误翻译；`spa.py` 提供静态资源和页面回退。`ui/` 负责托盘、WebView 等桌面表现。

2. **共享资源接口。** Profile 是单例 REST 资源：`GET /api/profile` 读取，`POST /api/profile` 创建，`PUT /api/profile` 完整替换并等待应用结果，与前端整份提交的方式一致。辅助资源包括场景目录 `/api/scenes`（已过时）、播单扫描 `/api/wallpaper-engine/playlist-scans` 和地点估算 `/api/location-estimates`。API 按资源命名，页面保留 `/setup/`。前后端随同一发布包升级。

3. **统一配置所有权。** `app/main.py` 将同一个 `ProfileManager` 交给 HTTP API、首次启动流程和 Scheduler。`ProfileManager` 管理配置读取、编译、持久化与应用队列；HTTP 路由通过它操作配置，调度线程在两个 Tick 之间处理更新。依赖方向为 `app → server → configurations/core/integrations`。

4. **集中外部集成。** 用户主动请求时，通过 `ipapi.co` 估算城市级地点，返回值供用户编辑，也可手动输入。Profile 保存最终确认的地点。界面说明外部服务可见请求来源 IP。首次创建通过 OpenWeatherMap 校验凭据和坐标（强制校验已过时），后续在天气设置变化时重新校验。`integrations/` 负责外部请求、解析和异常；天气校验与 WeatherSensor 共用适配器，路由负责翻译 HTTP 响应。

5. **由控制器管理设置窗口。** `SettingsWindowController.show()` 持有窗口子进程状态：首次打开时创建，活动时聚焦，退出后重建；聚焦失败时记录警告并保留已有进程。应用入口注入进程创建和 Windows 聚焦能力，托盘发出显示设置的意图。

## 考虑的替代方案

- **`backend/server/` 或 `service/`。** `server/` 与现有 Python 包并列，直接表达 HTTP 边界；整体迁入 `backend/` 会扩大迁移范围，`service/` 则与 ProfileManager 的职责重叠。
- **手动输入、浏览器或 Windows 精确定位、城市搜索、离线 IP 数据库。** 公网 IP 估算便于接入 WebView 表单，省去系统权限申请和本地数据库维护。后续改善定位时，优先增加基于 OpenWeather Geocoding 的城市搜索与候选选择。
- **入口闭包或通用窗口管理框架。** 闭包会将窗口状态和策略留在应用入口，通用框架则为单一窗口增加抽象成本，因此采用具体控制器。

## 后果

- 首次配置和运行时设置共享 API，HTTP、外部协议与桌面表现各有维护边界。
- 资源接口替换产生破坏性变更，需要同步修改前端与测试；HTTP 层承担请求校验和异常翻译的维护成本。
- 网络、VPN 或代理可能造成 IP 定位偏差，用户需要能修正结果。

## 相关文档

- [开发与验证](../DEVELOPMENT.md)：当前实现入口与验证方式。
- [领域术语](../../CONTEXT.md)：调度与场景概念。
