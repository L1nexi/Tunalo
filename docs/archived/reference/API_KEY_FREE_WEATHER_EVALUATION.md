# 免 API Key 天气服务评估

评估日期：2026-11-09。方案范围更新：2026-11-10。用户已确认完全转向 Open-Meteo，删除 OpenWeatherMap 集成及密钥配置，直接采用破坏性变更，不提供旧格式转换。改动面已确认，替换已实施，验证结果见工作交接；下文其他供应商资料保留为选型依据。

## 结论

已决定完全转向 **Open-Meteo**，用户确认地点后即可获取天气，省去注册、激活和填写密钥的步骤。它提供按经纬度查询的当前天气接口，数据能支持 Tunalo 的晴朗、阴天、雨、雪四项语义。免费服务适用于非商业用途；若产品未来收费或加入广告，需要重新评估服务方案。[功能说明](https://open-meteo.com/en/features)、[使用条款](https://open-meteo.com/en/terms)

后续体验验证仍需观察两项问题：实际使用网络的持续访问情况，以及预报推算的当前天气能否满足壁纸响应体验。MET Norway 的规则与来源较明确，可作为备选；7Timer 的时间步长较粗；wttr.in 的托管额度和数据使用依据还需补充。下文的推荐顺序是工程判断。

## 评估时的 Tunalo 需求

以下记录替换前 `de27ce6` 的代码行为，作为选型背景；替换后的接口与标尺见 [Open-Meteo 集成](../../../src/integrations/openmeteo.py) 和 [WeatherPolicy](../../../src/core/policies/weather.py)。

- [WeatherPolicy](../../../src/core/policies/weather.py) 使用 OpenWeatherMap（OWM）天气代码及主分类，构建晴朗、阴天、雨、雪的显著度，即对相应场景的支持或违和程度。雨雪区分强弱，雷暴由雨语义承接，部分 OWM 代码可同时支持雨雪。当前没有独立的雾、霾、风或温度语义。
- [WeatherSensor](../../../src/core/sensors/weather.py) 每 600 秒异步获取一次；失败保留内存缓存。[WeatherReminder](../../../src/app/weather_reminder.py) 在两小时没有成功获取后提醒一次，继续使用缓存。
- [SunTimesSensor](../../../src/core/sensors/sun_times.py) 已按地点和当地日期在本地计算日出日落。天气选型只需满足气象数据需求，地点仍供两类采集共同使用。
- [Profile](../../../src/configurations/profile.py) 当前为 v3，要求非空 `weather.api_key`，并拒绝多余字段。前端的[草稿](../../../frontend/src/setup/profile/model/draft.ts)、[步骤校验](../../../frontend/src/setup/workflow/steps.ts)、[连接测试](../../../frontend/src/setup/weather/useWeatherServices.ts)及[提交](../../../frontend/src/setup/profile/useProfileSubmission.ts)都依赖这个字段。

## Open-Meteo

### 数据与时间含义

免费端点为 `https://api.open-meteo.com/v1/forecast`，无需注册密钥。本次实现只请求 `current=weather_code`。调研探测额外请求了 `cloud_cover`，并核查自动返回的 `current.time` 和 `current.interval`；这些字段没有纳入本次运行时数据。[接口文档](https://open-meteo.com/en/docs)

`current` 是天气预报模型在当前时刻的估计。官方以 15 分钟为时间步长；中国等缺少原生 15 分钟模型覆盖的地区使用小时数据插值。插值是在相邻预报时点之间估算中间值。大部分全球模型每六小时更新一次，具体频率随模型而变。[数据来源与更新说明](https://open-meteo.com/en/features)

它覆盖中国，按地点自动选择适用模型。本次使用默认 `best_match`；官方中国气象局（CMA）模型专页在本次核查时提示上游开放数据服务过载、下载不稳定，因此固定 CMA 模型会增加当前已知的数据更新风险。[模型选择](https://open-meteo.com/en/features)、[CMA 当前公告](https://open-meteo.com/en/docs/cma-api)

其 WMO 天气代码可映射现有四项语义。WMO 是世界气象组织，此处指接口使用的天气现象编码。[代码表](https://open-meteo.com/en/docs#weather-variable-documentation)

| 代码 | 接口含义 | 对 Tunalo 的适配方向 |
| --- | --- | --- |
| `0 / 1 / 2 / 3` | 晴、大部晴、局部多云、阴 | 保留晴阴过渡，重新核对分级 |
| `51–57` 中列出的代码 | 毛毛雨、冻毛毛雨 | 雨，区分强弱 |
| `61 / 63 / 65 / 66 / 67 / 80 / 81 / 82` | 雨、冻雨、阵雨 | 雨，区分强弱 |
| `71 / 73 / 75 / 77 / 85 / 86` | 雪、雪粒、阵雪 | 雪，区分强弱 |
| `95 / 96 / 97 / 99` | 雷暴及部分冰雹情形 | 由雨承接强支持，按现象重新校准 |
| `45 / 48` | 雾、雾凇 | 可沿用现有雾类全零的处理 |

现有小雨／中雨／大雨／暴雨显著度为 `0.75 / 1 / 2 / 4`。两家代码的分级与现象粒度不同，映射后的强度需要用场景选择结果验证。Open-Meteo 的代码表也缺少 OWM 那样明确的混合雨雪代码；如果要保留同时支持雨雪的能力，需要再评估 `rain`、`showers`、`snowfall`，并核对时间区间和单位。已确认本次只按天气码解释，更多字段留待后续评估。

### 使用条件与调用量

免费服务限非商业用途，允许无订阅、无广告的个人或非营利应用，以及自愿捐赠。条款列出每分钟少于 600 次、每小时少于 5,000 次、每天少于 10,000 次，定价页另列每月 300,000 次；服务没有可用性保证。限额按 IP 和应用施加，应用发行后的总用量如何归集，仍需向提供方核实。[使用条款](https://open-meteo.com/en/terms)、[配额与可用性](https://open-meteo.com/en/pricing)

按单地点、全天运行计算：本次保留十分钟间隔，每天 144 次，30 天约 4,320 次，另加启动和连接测试。若提供方将整个应用合并按每日 10,000 次计，约 69 个常开客户端就接近该额度；这是配额归集方式尚未明确时的条件测算。

数据采用要求署名的 CC BY 4.0 许可，需链接 Open-Meteo、链接许可，并说明天气数据被转换用于场景判断。官方要求在展示天气数据的位置附近提供来源链接；可在天气设置状态及相关诊断视图中提供。服务端源码采用 AGPLv3，客户端调用接口与部署服务端涉及不同的许可材料。[数据与源码许可](https://open-meteo.com/en/licence)

### 本机访问结果

2026-11-09 23:22（北京时间），用公开的北京示例坐标 `39.9, 116.4` 请求上述两个字段，未读取用户真实配置。

| 请求方式 | 成功次数 | 三次耗时 |
| --- | --- | --- |
| 显式关闭 requests 的环境代理读取 | 3/3，均 HTTP 200 | 2.964、4.162、0.285 秒 |
| 沿用当前进程代理环境 | 3/3，均 HTTP 200 | 1.626、0.363、0.409 秒 |

环境存在代理变量，测试未记录其内容，也未加载项目 `.env`。六次响应均为有效 JSON，返回 `weather_code=0`、`cloud_cover=0`、`interval=900`。这些结果确认本机当前两种请求路径可用；多运营商、跨时段访问和雨雪天气的表现仍待采样。关闭环境代理读取的请求也可能经过系统级网络转发。

## 其他候选服务

### MET Norway Locationforecast

Locationforecast 按经纬度返回全球预报，提供 JSON。接入使用标明应用名称和有效联系地址的 `User-Agent` 请求头，无需用户填写密钥。中国属于其全球区域，采用欧洲中期天气预报中心（ECMWF）约 9 km 的模型数据。`instant` 中有云量等时点字段，天气类别 `symbol_code` 和降水量则属于未来一段时间的汇总；适配时要区分预报时段和当前观测。[接口文档](https://api.met.no/weatherapi/locationforecast/2.0/documentation)、[数据模型](https://api.met.no/doc/locationforecast/datamodel)

截至本次核查，官方接口文档要求非北欧地区的相同请求至少间隔 3 小时，数据每 6 小时更新。还需遵守响应的 `Expires`，随后使用 `If-Modified-Since`。这是当前产品的访问要求；本次未验证服务端是否对 3 小时间隔实施自动限流。中国等地区不适合直接沿用高频获取“当前天气”的方式。[更新间隔](https://api.met.no/weatherapi/locationforecast/2.0/documentation#update-intervals)、[使用条款](https://api.met.no/doc/TermsOfService)

其数据许可为 CC BY 4.0 / NLOD 2.0，需标注 MET Norway 来源、链接许可并说明数据改动；CC BY 4.0 允许商用。20 次/秒限制针对整个应用所有安装的合计流量。服务没有可用性保证，缺失合规标识、过量请求可能收到 403/429。[许可说明](https://api.met.no/doc/License)、[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)、[使用条款](https://api.met.no/doc/TermsOfService)

对 Tunalo 的判断：可以覆盖晴、阴、雨、雪，并有降水信息；若采用，需要缓存整段预报并按有效时刻取值，同时调整对“多久没有成功更新”的判断。建议作为备选研究，首轮接入成本高于直接提供 `current` 的候选。这里是基于数据形式与请求限制的工程判断。未验证中国网络长期可达性。

### wttr.in

托管服务示例无需认证，`format=j1` 提供 JSON，`current_condition` 含 `weatherCode`、云量、降水量和观测时间；天气码采用 WorldWeatherOnline 的枚举，与 Tunalo 目前 OWM 代码不同。数据字段足以表达四项天气语义及一定强弱信息。[官方 README](https://github.com/chubin/wttr.in#json-output)

所核查的 README 未给出托管服务固定调用额度、观测更新承诺或数据再分发许可。仓库 Apache-2.0 是程序源码许可；上游天气接口、数据许可和托管额度需要另行核实。README 的自建示例有 45 分钟原始天气缓存，并依赖托管 wttr.in 或需要密钥的 WorldWeatherOnline；该缓存示例不能作为线上服务更新承诺。[官方 README 与自建说明](https://github.com/chubin/wttr.in#installation)、[源码许可](https://github.com/chubin/wttr.in/blob/master/LICENSE)

对 Tunalo 的判断：可用于功能验证；本次缺少足以支撑默认生产集成的配额与数据使用依据。未验证中国网络长期可达性。

### 7Timer!

7Timer 提供无需注册密钥的经纬度 JSON/XML 接口。官网现链接到维护者的 GitHub Wiki；新版文档写明全球约 10 km 网格，CIVIL 是 3 小时步长的预报，含云量、天气类别、降水类型与强度等级，可以映射晴、阴、雨、雪。[官网接口说明](https://www.7timer.info/doc.php?lang=en)、[当前官方 Wiki](https://github.com/Yeqzids/7timer-issues/wiki/Wiki)

许可资料有新旧差异：旧 `doc.php` 写非商用，新 Wiki 的 Usage 则明确允许免费或付费软件使用数据，并按现状提供。官网 News 已说明文档迁到 Wiki，应优先采用现行 Wiki，并保留这项差异的核查记录。当前 Wiki 没有列出强制署名文本或固定调用配额。[现行 Usage](https://github.com/Yeqzids/7timer-issues/wiki/Wiki#usage)、[迁移公告](https://github.com/Yeqzids/7timer-issues/wiki/News)

旧官网介绍每天更新 4 次，当前 Wiki 未给出更新承诺，因此这里只记录为历史说明。服务自 2021 年公告支持 HTTPS；新 Wiki 仍留有 HTTP 示例，实际集成应使用 HTTPS。其预报时步较粗，是否适合降雨开始、停止时切换壁纸需要体验验证。[旧官网介绍](https://www.7timer.info/doc.php?lang=en)、[HTTPS 公告](https://github.com/Yeqzids/7timer-issues/wiki/News)

对 Tunalo 的判断：数据和免密钥条件基本满足，当前使用说明也允许付费软件，但时步与更新承诺较弱，适合作为次级候选。本次未验证中国网络长期可达性。

## 候选比较

| 服务 | 四项天气与强弱信息 | 访问与更新要求 | 本次判断 |
| --- | --- | --- | --- |
| Open-Meteo | 当前天气码覆盖四项及强弱；混合雨雪需补充评估 | 中国的 15 分钟时步来自小时数据插值；免费限非商业用途并按 IP 和应用限流 | 优先验证；短时本机访问成功 |
| MET Norway | 有天气类别、云量和分时段降水量 | 中国等非北欧地区同请求至少 3 小时；数据每 6 小时更新；遵守缓存头 | 数据来源和规则明确，需预报缓存及时间语义适配 |
| wttr.in | `current_condition` 字段较全，需转换 WWO 天气码 | 托管配额、更新承诺与数据许可尚缺直接依据 | 适合验证，暂不作为默认集成 |
| 7Timer | CIVIL 有天气类别、云量、降水类型和强度等级 | 3 小时预报步长；当前文档没有更新承诺或固定配额 | 次级候选，需验证刷新与降雨响应体验 |

MET Norway、wttr.in 和 7Timer 的核查仅涉及一手文档和源码，未向三家服务发送天气数据请求。Open-Meteo 的访问结果见上文。

## 已确认的接入范围

采用单一 Open-Meteo 来源。保留额外提供方需要维护两套协议、配置、界面状态和测试；目前没有两家服务的长期质量比较数据，也没有需要保留 OWM 的已知用户场景，因此本次直接替换。

| 范围 | 实施内容 |
| --- | --- |
| 外部请求 | 新增 `integrations/openmeteo.py`，删除 `openweather.py`；采集与连接测试共用请求、解析和异常分类 |
| 数据及策略 | `WeatherObservation.code`、`WeatherData.code` 使用 WMO 代码；`None` 表示未获取，0 表示晴天；按 ADR-0004 保留雨、雪和雷暴标尺 |
| 采集与提醒 | 保留每 600 秒获取、10 秒采集超时、失败缓存和两小时提醒；来源指纹改为坐标，同来源更新和迟到请求隔离沿用原契约 |
| 配置及持久化 | 删除密钥，Profile 升为 v4；通过既有版本错误拒绝旧格式，不做转换 |
| 本地接口与设置 | `POST /api/weather-validations` 接受当前坐标；删除密钥输入和申请指引，保留测试结果、错误详情和确认后跳过验证保存；坐标变化使验证失效 |
| 诊断及文档 | Tick History 和调参工具使用新代码；同步 README、ADR-0001/0004 和天气提醒规格，补来源署名 |

本次保留既有缓存行为。数据适用时刻、缓存过期、重试退避和定量雨雪信息留作独立改进。`current.time` 是预报适用时刻，与模型初始化时间不同；若后续处理旧数据，需要分别核对两者。[模型更新时间说明](https://open-meteo.com/en/docs/model-updates)

设置流程为“估算或填写地点 → 测试连接 → 继续设置”，IP 估算和手动坐标沿用现有入口。天气请求向 Open-Meteo 发送坐标，服务也可见出口 IP；本次没有增加城市搜索或提供方切换。

验收覆盖晴阴过渡、毛毛雨、强降雨、雷暴、雪、未知代码和无数据时的语义，以及首次保存、修改地点、配置热更新、失败缓存、旧请求迟到、v4 读写和旧版拒绝。自动化验证结果见[工作交接](../../../agent/workspace/handoff.md)。

长期访问情况仍待观察，可在目标 Windows 网络中连续采样 48 小时，分别统计代理和直连的成功率、延迟与限流；这是后续体验验证建议。本次调研完成六次只读探测，实施后又用新集成对公开北京示例坐标请求一次，返回有效晴天码 0。
