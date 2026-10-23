const zh = {
  validation: "请完成当前配置项的全部必填内容。",
  pendingActivity: "请先处理尚未添加的活动规则文字。",
  fieldValidation: "配置存在无效字段，请按下方提示修正。",
  profileAlreadyExists: "配置已存在。请关闭窗口后从托盘重新打开设置。",
  applyTimeout: "调度器暂时没有完成应用，请重试。",
  applyUnavailable: "配置修改不可用，请稍后重试。",
  weatherValidationUnavailable: "天气服务可用性测试未通过。",
  locationValidationUnavailable: "自动定位服务不可用。",
  networkReasons: {
    timeout: "连接超时，请检查网络或代理后重试。",
    proxy_error: "代理连接失败，请检查系统代理设置或改用可用的网络。",
    tls_error: "安全连接失败，请检查网络、代理和系统时间。",
    connection_error: "无法建立连接，请检查网络或代理后重试。",
    request_error: "网络请求失败，请检查网络后重试。",
    invalid_json: "服务返回了无法解析的数据，请稍后重试。",
    invalid_response: "服务返回的数据不完整，请稍后重试。",
    provider_error: "定位服务拒绝了此次查询，请手工填写地点或稍后重试。",
  },
  httpRateLimited: "服务限制了请求频率，请稍后重试。",
  httpForbidden: "服务拒绝了请求，请检查当前网络或代理。",
  httpServerError: "服务端暂时出错，请稍后重试。",
  httpOther: (status: number) => `服务返回 HTTP ${status}，请稍后重试。`,
  generic: "操作失败。草稿仍然保留，请重试。",
  scanCodes: {
    wallpaper_engine_executable_not_found: "没有找到 Wallpaper Engine 可执行文件。请手动选择安装位置。",
    wallpaper_engine_config_not_found:
      "没有找到 Wallpaper Engine 配置文件。请先启动一次 Wallpaper Engine，然后重试。",
    wallpaper_engine_config_read_failed:
      "Wallpaper Engine 配置文件暂时无法读取。请关闭可能正在写入配置的窗口后重试。",
    unexpected_wallpaper_engine_config_format: "Wallpaper Engine 配置文件格式无法识别。",
  },
  issueCodes: {
    weather_api_key_invalid: "无效的 API Key。",
    weather_location_invalid: "OpenWeatherMap 无法使用这个地点，请检查经纬度。",
    weather_api_quota_exceeded: "API Key 已达到请求配额，请稍后重试或更换 Key。",
  },
  stages: {
    compile: "配置编译",
    prepare: "运行时准备",
    persist: "Profile 写入",
  },
};

const en = {
  validation: "Complete the required fields on this page first.",
  pendingActivity: "Finish or clear the text waiting in an activity field.",
  fieldValidation: "The server found fields that need changes. Follow the messages below.",
  profileAlreadyExists: "A Profile already exists. Close this window and reopen Settings from the tray.",
  applyTimeout: "The scheduler did not finish applying the change. Your draft is still here; try again.",
  applyUnavailable: "The scheduler is not accepting configuration changes right now. Try again shortly.",
  weatherValidationUnavailable: "The weather check could not finish. Your draft is still here.",
  locationValidationUnavailable: "Automatic location detection failed.",
  networkReasons: {
    timeout: "The connection timed out. Check your network or proxy and try again.",
    proxy_error: "The proxy connection failed. Check the system proxy or try another network.",
    tls_error: "The secure connection failed. Check your network, proxy, and system clock.",
    connection_error: "A connection could not be established. Check your network or proxy.",
    request_error: "The network request failed. Check your connection and try again.",
    invalid_json: "The service returned unreadable data. Try again later.",
    invalid_response: "The service returned incomplete data. Try again later.",
    provider_error:
      "The location service rejected the lookup. Enter your location manually or try again later.",
  },
  httpRateLimited: "The service is limiting requests. Try again later.",
  httpForbidden: "The service denied the request. Check your network or proxy.",
  httpServerError: "The service is temporarily failing. Try again later.",
  httpOther: (status: number) => `The service returned HTTP ${status}. Try again later.`,
  generic: "The operation failed. Your draft is still here; try again.",
  scanCodes: {
    wallpaper_engine_executable_not_found: "wallpaper64.exe was not found. Choose the installation manually.",
    wallpaper_engine_config_not_found:
      "Wallpaper Engine config.json was not found. Start Wallpaper Engine once, then try again.",
    wallpaper_engine_config_read_failed:
      "Wallpaper Engine configuration could not be read. Close anything writing it, then try again.",
    unexpected_wallpaper_engine_config_format:
      "The Wallpaper Engine configuration format was not recognized.",
  },
  issueCodes: {
    weather_api_key_invalid: "This API key is invalid.",
    weather_location_invalid: "OpenWeatherMap could not use this location. Check the coordinates.",
    weather_api_quota_exceeded: "This API key has reached its request quota. Try later or use another key.",
  },
  stages: {
    compile: "configuration compilation",
    prepare: "runtime preparation",
    persist: "Profile write",
  },
};

export const ERRORS_COPY = { zh, en };
