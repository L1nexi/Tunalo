# OpenWeather 当前天气 API 开发参考

核对日期：2026-10-05。本文整理 OpenWeatherMap（OWM）的 Current Weather Data 接口，供天气数据接入与语义构建时查阅。显著度曲线与场景选择算法另行讨论。

主要来源：[当前天气 API 官方文档](https://openweathermap.org/api/current?collection=current_forecast)。

## 1. 请求方式

```http
GET https://api.openweathermap.org/data/2.5/weather?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=metric&lang=zh_cn
```

占位符需要替换为实际经纬度和 API Key。建议按经纬度调用，显式指定 `units=metric`，省略 `mode` 以获得默认 JSON 响应。

| 参数 | 必需 | 含义与取值 |
| --- | --- | --- |
| `lat` | 是 | 纬度，数值 |
| `lon` | 是 | 经度，数值 |
| `appid` | 是 | API Key，字符串 |
| `units` | 否 | `standard`（默认）、`metric`、`imperial` |
| `lang` | 否 | 输出语言；`zh_cn` 为简体中文，`zh_tw` 为繁体中文 |
| `mode` | 否 | `xml` 或 `html`；不传时返回 JSON |

`lang` 翻译城市名与天气描述，数值单位由 `units` 决定。城市名、城市 ID、邮编形式的内置地理编码已被弃用；需要地点转换时，官方另提供 [Geocoding API](https://openweathermap.org/api/geocoding-api)。[请求与语言说明](https://openweathermap.org/api/current?collection=current_forecast)

## 2. JSON 响应字段

以下类型按官方 JSON 示例归纳；官方字段页并未给出完整的必填响应契约。单位列以 `units=metric` 为前提。[字段与单位说明](https://openweathermap.org/api/current?collection=current_forecast)

| 字段 | JSON 类型 | 含义与单位 |
| --- | --- | --- |
| `coord.lat`、`coord.lon` | 数值 | 响应地点的纬度、经度 |
| `weather` | 对象数组 | 天气现象列表，可能包含多个现象；第一项为主要天气 |
| `weather[].id` | 整数 | 天气现象代码 |
| `weather[].main` | 字符串 | 现象分组，例如 `Rain`、`Snow`、`Clouds` |
| `weather[].description` | 字符串 | 具体天气描述，受 `lang` 影响 |
| `weather[].icon` | 字符串 | 天气图标代码，例如 `10d`、`10n` |
| `main.temp` | 数值 | 气温，°C |
| `main.feels_like` | 数值 | 体感温度，°C |
| `main.temp_min`、`main.temp_max` | 数值，可选 | 同一时刻城市范围内的最低、最高气温，°C |
| `main.humidity` | 数值 | 相对湿度，% |
| `main.pressure`、`main.sea_level` | 数值 | 海平面气压，hPa |
| `main.grnd_level` | 数值 | 地面气压，hPa |
| `clouds.all` | 数值 | 云量，% |
| `visibility` | 数值 | 能见度，米；接口报告值上限为 10,000 米 |
| `wind.speed` | 数值 | 风速，米／秒 |
| `wind.deg` | 数值 | 气象风向，度，表示风从哪个方向吹来 |
| `wind.gust` | 数值，可能省略 | 阵风速度，米／秒 |
| `rain.1h` | 数值，可选 | 降雨，固定单位为毫米／小时（mm/h） |
| `snow.1h` | 数值，可选 | 降雪降水量，固定单位为毫米／小时（mm/h） |
| `dt` | 整数 | 数据计算时间，UTC Unix 时间戳，秒 |
| `timezone` | 整数 | 该地点相对于 UTC 的偏移，秒 |
| `sys.sunrise`、`sys.sunset` | 整数 | 日出、日落时间，UTC Unix 时间戳，秒 |
| `sys.country` | 字符串 | 国家代码 |
| `id`、`name` | 整数、字符串 | 城市 ID、城市名称 |
| `base`、`cod`、`sys.type`、`sys.id`、`sys.message` | 内部字段 | 官方标为内部参数；成功示例中的 `cod` 为数值 `200` |

### 需要留意的含义

- `weather` 是数组，不是单个对象；官方明确允许同时返回多个现象，并说明第一项是主要天气。[天气代码说明](https://openweathermap.org/api/weather-conditions)
- `temp_min` 与 `temp_max` **不是当天最低、最高温度**。它们描述当前时刻城市范围内的差异，许多地点的值会与 `temp` 相同，且官方明确标为可选。[当前温度极值说明](https://openweathermap.org/api/current?collection=current_forecast)
- `rain.1h` 与 `snow.1h` 的单位不随 `units` 改变。`snow.1h` 是降水字段，不能作为地面新增积雪深度使用。`units=standard` 时温度为开尔文，`imperial` 时为华氏度、风速为英里／小时。[单位说明](https://openweathermap.org/api/current?collection=current_forecast)
- `visibility=10000` 代表达到接口报告上限，无法区分实际能见度是 10 公里还是更远。`timezone` 是偏移秒数，不是时区名称，也不改变 `dt`、日出与日落时间戳本身的 UTC 含义。[时间与能见度字段](https://openweathermap.org/api/current?collection=current_forecast)

### 字段缺省

官方说明，响应只展示实际测得或计算的数据；测量时刻未发生的天气现象，其相关字段可能不返回。`rain.1h`、`snow.1h` 标注为“数据可用时提供”，`wind.gust` 在部分官方示例中也会省略。因此，正常天气响应中没有 `rain` 或 `snow` 是允许的，不等同于请求失败。[响应说明与示例](https://openweathermap.org/api/current?collection=current_forecast)

### 精简响应示例

以下为自制示意数据，展示 `metric` 请求下的结构与单位，不是实时观测，也不是完整字段列表。

```json
{
  "coord": { "lat": 31.23, "lon": 121.47 },
  "weather": [
    { "id": 501, "main": "Rain", "description": "中雨", "icon": "10d" }
  ],
  "main": { "temp": 22.0, "feels_like": 22.6, "humidity": 80, "pressure": 1010 },
  "clouds": { "all": 95 },
  "visibility": 6000,
  "wind": { "speed": 4.0, "deg": 120, "gust": 7.0 },
  "rain": { "1h": 3.0 },
  "dt": 1791187200,
  "timezone": 28800,
  "cod": 200
}
```

## 3. 天气代码与定量数据

代码用于识别现象类别；它不是显著度，也不是可以按数值大小线性排序的强度。[完整天气代码表](https://openweathermap.org/api/weather-conditions)

| 代码分组 | 含义 | 例子 |
| --- | --- | --- |
| `2xx` | 雷暴 | `202`：伴随强降雨的雷暴 |
| `3xx` | 毛毛雨 | `300`：轻微毛毛雨 |
| `5xx` | 雨 | `500`：小雨；`501`：中雨；`502`：强降雨 |
| `6xx` | 雪及雨雪混合 | `600`：小雪；`602`：大雪；`616`：雨夹雪 |
| `7xx` | 雾、烟霾、沙尘等现象 | `701`：薄雾；`741`：雾 |
| `800` | 晴朗 | 晴空 |
| `801`–`804` | 云 | 从少云到阴天 |

雨的分组还区分 `503`（更强降雨）、`504`（极强降雨）、`511`（冻雨）以及 `520`–`531` 的阵雨类别。降水也可能伴随雷暴或毛毛雨出现，不能只检查 `5xx` 就代表全部降水现象。[雨与雷暴代码](https://openweathermap.org/api/weather-conditions)

代码描述类别，`rain.1h` 则提供定量依据。例如 `0.3`、`3.0`、`12.0` 分别表示该字段的降雨量为 0.3、3.0、12.0 mm/h；这些数值只是单位示例，不定义本项目的小雨、中雨、大雨边界。云量、风速、阵风和体感温度也可独立读取。[当前天气数值字段](https://openweathermap.org/api/current?collection=current_forecast)

## 4. HTTP 错误

以下为官方 FAQ 列出的常见错误含义。[API 错误说明](https://openweathermap.org/faq)

| HTTP 状态 | 官方说明 |
| --- | --- |
| `401` | API Key 缺失、未激活、错误，或当前订阅无权访问所请求的产品 |
| `404` | 地点标识不正确，或 API 请求格式不正确 |
| `429` | 请求量超过套餐调用限制 |
| `500`、`502`、`503`、`504` | 服务端错误；官方建议联系支持并提供触发错误的请求示例 |

响应体中的 `cod` 在当前接口字段表中仅标为内部参数；错误响应中可能另有 `message` 描述原因。不要将其他 OpenWeather 产品的错误响应结构直接视为该接口的完整契约。[当前字段说明](https://openweathermap.org/api/current?collection=current_forecast)、[调用超额响应示例](https://openweathermap.org/appid)

## 5. 数据来源与免费套餐

当前天气由全球与区域气象模型、卫星、雷达和气象站等来源综合处理得到，不意味着请求位置有直接观测站，也不保证当地突发天气逐分钟进入响应。`dt` 是数据计算时间，应与客户端请求时间区分。[产品说明](https://openweathermap.org/api/current?collection=current_forecast)

截至 2026-10-05，官方价格表的 **Free** 列包含 Current Weather API，并列出：

| 项目 | Free 套餐 |
| --- | --- |
| 调用额度 | 60 次／分钟，1,000,000 次／月 |
| 天气数据更新 | 每 2 小时 |

以上是套餐资料的核对快照，后续以 [官方详细价格表](https://openweathermap.org/full-price) 为准。频繁请求不等于底层数据以相同频率更新；不要将其他付费套餐或 One Call API 的更新间隔套用到免费当前天气接口。
