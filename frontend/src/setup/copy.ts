import type { Locale, SceneId } from "@/api/profile";
import type { DisturbancePreset } from "@/setup/model";

const zh = {
  appName: "Tunalo",
  mode: { setup: "首次设置", settings: "设置" },
  loading: {
    title: "正在读取设置",
    description: "连接本地调度器并准备设置草稿。",
  },
  unavailable: {
    title: "无法连接到 Tunalo 服务",
    description: "请确认主程序仍在运行，然后重试。",
    retry: "重试",
  },
  steps: {
    wallpaper: { title: "Wallpaper Engine" },
    weather: { title: "天气服务" },
    location: { title: "天气位置" },
    scenes: { title: "场景绑定" },
    scheduling: { title: "调度风格" },
    activity: { title: "活动识别" },
    review: { title: "查看配置草稿" },
  },
  nav: {
    settingsDescription: "",
    discardTitle: "放弃未保存的修改？",
    discardSetupDescription: "当前设置草稿不会保存，首次设置将取消。",
    discardSettingsDescription: "当前运行设置不会改变，本次修改将丢失。",
    keepEditing: "继续编辑",
    discardChanges: "放弃修改",
    changed: "已修改",
    pending: "待填写",
    defaultReady: "可沿用默认",
    unsaved: "有未保存的修改",
    saved: "所有修改已保存",
    languageLabel: "语言",
    themeLabel: "外观",
    themeSystem: "跟随系统",
    themeLight: "浅色",
    themeDark: "深色",
    setupNavigation: "设置项",
    settingsNavigation: "设置项",
    reviewSetup: "查看配置草稿",
    reviewSettings: "查看配置草稿",
    backToSettings: "返回设置",
    current: "当前",
    complete: "完成",
    optional: "可跳过",
  },
  common: {
    back: "返回",
    next: "继续",
    cancel: "取消",
    close: "关闭",
    retry: "重试",
    required: "必填",
    needsAttention: "需要处理",
    optional: "可选",
    notSet: "未设置",
    custom: "自定义",
    show: "显示",
    hide: "隐藏",
    remove: "移除",
  },
  wallpaper: {
    title: "连接 Wallpaper Engine",
    description: "",
    pathLabel: "Wallpaper Engine 可执行文件",
    pathDescription:
      "选择 Wallpaper Engine 可执行文件，如 wallpaper64.exe。留空以尝试自动检测。",
    pathPlaceholder: "选择 Wallpaper Engine 可执行文件",
    choose: "选择文件",
    detect: "自动检测",
    scan: "扫描播放列表",
    scanning: "正在扫描",
    found: "文件路径有效",
    foundDescription: (count: number) => `找到 ${count} 个可用播放列表。`,
    scanResultsLabel: "播放列表及对应壁纸数量",
    playlistName: "Wallpaper Engine 中的播放列表名称",
    wallpaperCount: "壁纸数量",
    itemCount: (count: number) => `${count} 张`,
    englishNames:
      "为降低命令行调用时的兼容问题，建议播放列表名称优先使用英文字母与数字的组合。",
    emptyTitle: "未找到可用播放列表",
    emptyDescription:
      "请于 Wallpaper Engine 中创建至少一个包含壁纸的播放列表后重新尝试扫描。",
    zeroItem: "未找到壁纸",
    scanAgain: "重新扫描",
    manualHint: "如果自动检测失败，请手动选择 wallpaper64.exe。",
    scanRequired: "请扫描并确认至少一个可用播放列表。",
  },
  weather: {
    title: "连接天气服务",
    description:
      "Tunalo 使用 OpenWeatherMap 获取天气以及日出和日落信息。密钥仅保存于本地。",
    keyLabel: "OpenWeatherMap API Key",
    keyDescription: "保存天气设置时会联网校验 API Key 有效性。",
    keyPlaceholder: "粘贴 API Key",
    keyRequired: "请先填写 API Key。",
    getKey: "获取 API Key",
    guideTitle: "如何获取 API Key",
    guideSteps: [
      {
        title: "注册账号",
        action: "打开 OpenWeatherMap，注册账号并登录。已有账号可直接登录。",
        expected: "登录后点击个人头像，进入 API keys 页面。",
        fallback: "",
      },
      {
        title: "生成 API Key",
        action: "在 API keys 页面点击 Generate 生成 API Key。",
        expected: "确认新 Key 出现在账户的 Key 列表中。",
        fallback: "",
      },
      {
        title: "确认状态并粘贴",
        action: "确认该 Key 的 Status 为 Active，再粘贴 Key 到上方输入框。",
        expected: "使用“测试连接”确认 API Key 有效性以及网络连通性。",
        fallback: "",
      },
    ],
    validate: "测试连接",
    validating: "正在测试",
    keyValid: "API Key 有效",
    keyUntested: "尚未验证 API Key",
    testedAt: (date: string) => `验证时间：${date}`,
    connectionFailed: (reason: string) => `连接天气服务失败：${reason}`,
    validationMissing: "请先填写 API Key，再测试连接。",
    validationOnSubmit: "",
  },
  location: {
    title: "确认天气地点",
    setupDescription:
      "天气和日出日落只依据经纬度计算，无需填写城市名称。坐标仅保存在本机。",
    settingsDescription:
      "天气和日出日落只依据经纬度计算，无需填写城市名称。坐标仅保存在本机。",
    detect: "估算经纬度",
    detecting: "正在估算",
    detectHint: "根据公网 IP 估算城市级经纬度，结果可手动修正。",
    detected: (city: string | null) =>
      city ? `城市：${city}，已填入预估经纬度。` : "已填入预估经纬度，请核对。",
    detectionUnavailable:
      "无法连接到 ipapi.co。可在地图上查找地点坐标，再将纬度和经度分别填入下方。",
    manualHelp: "打开 OpenStreetMap，搜索所在地，在目标位置右键选择“显示地址”，从左侧复制纬度和经度；南纬和西经使用负数。",
    openMap: "打开地图查找坐标",
    latitudeLabel: "纬度",
    longitudeLabel: "经度",
    latitudePlaceholder: "-90 到 90",
    longitudePlaceholder: "-180 到 180",
    invalidLatitude: "纬度必须在 -90 到 90 之间。",
    invalidLongitude: "经度必须在 -180 到 180 之间。",
    requiredLatitude: "请填写纬度。",
    requiredLongitude: "请填写经度。",
  },
  scenes: {
    title: "绑定使用场景",
    description:
      "启用需要的内置场景，并为每个场景选择 Wallpaper Engine 播放列表。多个场景可以共用一个播放列表。",
    defaultHint: "",
    playlist: "播放列表",
    choosePlaylist: "选择播放列表",
    searchPlaylist: "搜索播放列表",
    noPlaylistMatch: "没有匹配的播放列表。",
    playlistCount: (count: number) => `${count} 张壁纸`,
    bindingRequired: "请为此场景选择播放列表。",
    unavailablePlaylist: "已选播放列表不在扫描结果中，请重新选择。",
    required: "至少启用并绑定一个场景。",
    unavailable: "场景绑定需要至少一个包含壁纸的播放列表。",
    groupSummary: (enabled: number, total: number) => `已启用 ${enabled}/${total}`,
    groups: { season: "季节氛围", context: "日常情境", weather: "天气氛围" },
    matchExplanation: "天气、时段、季节和活动会共同参与场景匹配；同时成立时由匹配结果决定候选场景，不按此处的列表顺序固定优先。",
  },
  preferences: {
    title: "调整调度风格",
    description: "",
    responseTitle: "响应风格",
    responseDescription:
      "决定匹配场景时更看重长期情境，还是当前天气与活动；不改变允许切换的时机。",
    responseExplanations: {
      background: "季节与时段相对更有影响；天气和活动仍参与匹配。",
      background_leaning: "与平衡档相比，长期情境的影响更大。",
      balanced: "长期情境与当前天气、活动共同参与匹配。",
      current_leaning: "与平衡档相比，当前天气和活动的影响更大。",
      current: "五档中最重视当前天气和活动；仍结合时段与季节。",
    },
    disturbanceTitle: "防打扰程度",
    disturbanceDescription: "调节调度器执行壁纸切换时的防打扰程度。",
    timingSummary: (startup: number | null, idle: number | null, deferral: number | null, cycle: number | null) =>
      `启动等待 ${startup ?? "—"} 秒；空闲等待 ${idle ?? "—"} 秒；场景切换最长延后 ${deferral ?? "—"} 分钟；同场景轮换最短间隔 ${cycle ?? "—"} 分钟。`,
    fineTune: "自定义防打扰设置",
    startupGrace: "启动等待",
    idleBeforeSwitch: "空闲等待",
    maximumDeferral: "最长延后",
    cycleInterval: "轮换间隔",
    seconds: "秒",
    minutes: "分钟",
    nonNegative: "请输入不小于 0 的整数。",
  },
  activity: {
    title: "识别当前活动",
    description: "确定调度器如何根据当前前台窗口信息判定当前活动状态。",
    workTitle: "工作场景规则",
    leisureTitle: "休闲场景规则",
    processLabel: "进程名",
    titleKeywordLabel: "窗口标题关键词",
    processPlaceholder: "例如 Photoshop.exe",
    keywordPlaceholder: "例如 项目计划",
    processHelp: "填写可执行文件名，例如 Photoshop.exe；按回车或点“添加”。",
    titleHelp: "填写窗口标题中会出现的文字，例如“项目计划”；按回车或点“添加”。",
    add: "添加",
    empty: "暂未添加",
    conflictTitle: "存在冲突规则",
    conflictDescription: (values: string) =>
      `这些项目同时出现在工作和休闲场景规则中：${values}`,
    matchingHelp: "进程名须完整匹配，忽略大小写和末尾的 .exe；窗口标题只需包含关键词，忽略大小写。两类规则都未命中时，不据此判断为工作或休闲。",
    pendingWarning: "输入框中有尚未添加的文字。请按回车或点“添加”，或者清空后再保存。",
  },
  review: {
    title: "查看配置草稿",
    description: "",
    missingTitle: "配置项缺失",
    missingDescription: "保存配置前需完成以下配置项。",
    wallpaper: "Wallpaper Engine 路径",
    weather: "本次草稿的天气测试",
    location: "经纬度",
    scenes: "场景绑定",
    response: "响应风格",
    disturbance: "防打扰程度",
    activity: "活动识别规则",
    weatherUntested: "当前草稿密钥尚未手动测试",
    weatherNote: "此结果仅针对当前草稿密钥的联网测试，不代表已运行配置的实时健康状态。",
    testedAt: (date: string) => `测试时间：${date}`,
    sceneCount: (bound: number, pending: number) => `已绑定 ${bound} 个，待绑定 ${pending} 个`,
    changesTitle: "本次修改",
    noChanges: "所有修改已保存。",
    currentDetails: "查看当前草稿全部设置",
    edit: "修改",
    disabled: "未启用",
    awaitingPlaylist: "待绑定播放列表",
    secretChanged: "已更改（内容不显示）",
    activityCount: (windows: number, processes: number) =>
      `窗口名规则 ${windows} 条，进程名规则 ${processes} 条`,
    coordinates: (latitude: number, longitude: number) =>
      `纬度 ${latitude}，经度 ${longitude}`,
    create: "完成设置",
    creating: "正在创建",
    save: "保存并应用",
    saving: "正在保存",
    success: "已保存并生效",
    setupSuccess: "设置已完成，正在启动调度器。",
  },
  errors: {
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
      wallpaper_engine_executable_not_found:
        "没有找到 Wallpaper Engine 可执行文件。请手动选择安装位置。",
      wallpaper_engine_config_not_found:
        "没有找到 Wallpaper Engine 配置文件。请先启动一次 Wallpaper Engine，然后重试。",
      wallpaper_engine_config_read_failed:
        "Wallpaper Engine 配置文件暂时无法读取。请关闭可能正在写入配置的窗口后重试。",
      unexpected_wallpaper_engine_config_format:
        "Wallpaper Engine 配置文件格式无法识别。",
    },
    issueCodes: {
      weather_api_key_invalid: "无效的 API Key。",
      weather_location_invalid:
        "OpenWeatherMap 无法使用这个地点，请检查经纬度。",
      weather_api_quota_exceeded:
        "API Key 已达到请求配额，请稍后重试或更换 Key。",
    },
    stages: {
      compile: "配置编译",
      prepare: "运行时准备",
      persist: "Profile 写入",
    },
  },
};

const en: typeof zh = {
  appName: "Tunalo",
  mode: { setup: "First-time setup", settings: "Settings" },
  loading: {
    title: "Loading settings",
    description:
      "Connecting to the local scheduler and preparing a Profile draft.",
  },
  unavailable: {
    title: "Tunalo is unavailable",
    description:
      "Make sure the main application is still running, then try again.",
    retry: "Try again",
  },
  steps: {
    wallpaper: { title: "Wallpaper Engine" },
    weather: { title: "Weather service" },
    location: { title: "Location" },
    scenes: { title: "Scene assignments" },
    scheduling: { title: "Scheduling feel" },
    activity: { title: "Activity detection" },
    review: { title: "Review and finish" },
  },
  nav: {
    settingsDescription: "Changes stay in this draft until you save them.",
    discardTitle: "Discard unsaved changes?",
    discardSetupDescription: "This draft will not be saved and initial setup will be cancelled.",
    discardSettingsDescription: "The running settings will stay as they are. These edits will be lost.",
    keepEditing: "Keep editing",
    discardChanges: "Discard changes",
    changed: "Changed",
    pending: "Needs input",
    defaultReady: "Default ready",
    unsaved: "You have unsaved changes",
    saved: "All changes saved",
    languageLabel: "Language",
    themeLabel: "Appearance",
    themeSystem: "System",
    themeLight: "Light",
    themeDark: "Dark",
    setupNavigation: "Settings",
    settingsNavigation: "Settings",
    reviewSetup: "Review and finish",
    reviewSettings: "Review and save",
    backToSettings: "Back to settings",
    current: "Current",
    complete: "Complete",
    optional: "Optional",
  },
  common: {
    back: "Back",
    next: "Continue",
    cancel: "Cancel",
    close: "Close",
    retry: "Retry",
    required: "Required",
    needsAttention: "Needs attention",
    optional: "Optional",
    notSet: "Not set",
    custom: "Custom",
    show: "Show",
    hide: "Hide",
    remove: "Remove",
  },
  wallpaper: {
    title: "Connect Wallpaper Engine",
    description:
      "Read Wallpaper Engine's local configuration first, so Scenes can only use playlists that actually exist.",
    pathLabel: "Wallpaper Engine executable",
    pathDescription:
      "Usually wallpaper64.exe inside the Steam installation. Leave blank to try automatic detection.",
    pathPlaceholder: "Auto-detect, or choose wallpaper64.exe",
    choose: "Choose file",
    detect: "Auto-detect",
    scan: "Scan playlists",
    scanning: "Scanning",
    found: "Connected",
    foundDescription: (count: number) => `Found ${count} usable playlists.`,
    scanResultsLabel: "Scanned playlists and wallpaper counts",
    playlistName: "Playlist name in Wallpaper Engine",
    wallpaperCount: "Wallpaper count",
    itemCount: (count: number) => `${count} wallpapers`,
    englishNames:
      "For command-line compatibility, prefer English letters and digits in playlist names. Existing non-English names can still be scanned; if switching fails, try renaming the playlist in English.",
    emptyTitle: "No usable playlists found",
    emptyDescription:
      "Create at least one Wallpaper Engine playlist containing a wallpaper, then scan again.",
    zeroItem: "No wallpapers",
    scanAgain: "Scan again",
    manualHint:
      "If automatic detection fails, choose wallpaper64.exe manually.",
    scanRequired: "Scan and confirm at least one usable playlist.",
  },
  weather: {
    title: "Connect weather",
    description:
      "Tunalo uses OpenWeatherMap for conditions, sunrise, and sunset. The key stays in the local Profile.",
    keyLabel: "OpenWeatherMap API key",
    keyDescription:
      "Enter a valid Current Weather API key. Weather changes are checked online before saving.",
    keyPlaceholder: "Paste API key",
    keyRequired: "Enter an API key first.",
    getKey: "Get an API key",
    guideTitle: "How to get an API key",
    guideSteps: [
      {
        title: "Create an account",
        action:
          "Create an OpenWeatherMap account and sign in. If you already have one, sign in.",
        expected: "You can open the API keys page after signing in.",
        fallback:
          "If the site asks you to verify your email, follow its instructions first.",
      },
      {
        title: "Generate an API key",
        action: "Click Generate on the API keys page.",
        expected: "The new key appears in your account's key list.",
        fallback:
          "Use the Get an API key button here if you cannot find the page.",
      },
      {
        title: "Check status and paste",
        action:
          "Make sure the key's Status is Active, then copy the key itself into the field above.",
        expected:
          "Select Test connection and continue to location after it succeeds.",
        fallback:
          "If Active is not shown, check the key status in your account. For a failed test, check the copied key or follow the network guidance shown here.",
      },
    ],
    validate: "Test connection",
    validating: "Testing",
    keyValid: "API key is valid",
    keyUntested: "API key not verified yet",
    testedAt: (date: string) => `Verified at ${date}`,
    connectionFailed: (reason: string) => `Could not reach the weather service: ${reason}`,
    validationMissing: "Enter an API key before testing the connection.",
    validationOnSubmit:
      "This test checks the API key without saving your draft. Setup and weather changes also validate the key and location before saving.",
  },
  location: {
    title: "Confirm weather location",
    setupDescription:
      "Weather, sunrise, and sunset use only latitude and longitude. No city name is needed. Coordinates stay on this device.",
    settingsDescription:
      "Weather, sunrise, and sunset use only latitude and longitude. No city name is needed. Coordinates stay on this device.",
    detect: "Estimate coordinates",
    detecting: "Estimating",
    detectHint:
      "Estimate city-level coordinates from your public IP. You can correct the result manually.",
    detected: (city: string | null) =>
      city ? `City: ${city}. Estimated coordinates filled in.` : "Estimated coordinates filled in. Check that they are accurate.",
    detectionUnavailable:
      "Find your location on a map, then enter its latitude and longitude below, or retry after checking the issue.",
    manualHelp: "Open OpenStreetMap, search your location, right-click the point and choose Show address. Copy the latitude and longitude from the left panel; use negative values for south and west.",
    openMap: "Open map for coordinates",
    latitudeLabel: "Latitude",
    longitudeLabel: "Longitude",
    latitudePlaceholder: "-90 to 90",
    longitudePlaceholder: "-180 to 180",
    invalidLatitude: "Latitude must be between -90 and 90.",
    invalidLongitude: "Longitude must be between -180 and 180.",
    requiredLatitude: "Latitude is required.",
    requiredLongitude: "Longitude is required.",
  },
  scenes: {
    title: "Assign Scenes",
    description:
      "Enable built-in Scenes and choose a Wallpaper Engine playlist for each. Multiple Scenes may share a playlist.",
    defaultHint:
      "First-time setup preselects four everyday Scenes and Rain. Assign a playlist to each selected Scene; you can reuse one or turn off any Scene you do not need.",
    playlist: "Playlist",
    choosePlaylist: "Choose a playlist",
    searchPlaylist: "Search playlists",
    noPlaylistMatch: "No matching playlists.",
    playlistCount: (count: number) => `${count} wallpapers`,
    bindingRequired: "Choose a playlist for this Scene.",
    unavailablePlaylist:
      "The selected playlist is missing from the scan. Choose another.",
    required: "Enable and assign at least one Scene.",
    unavailable:
      "Scene assignments need at least one playlist containing wallpapers.",
    groupSummary: (enabled: number, total: number) => `${enabled}/${total} enabled`,
    groups: { season: "Seasonal atmosphere", context: "Everyday context", weather: "Weather atmosphere" },
    matchExplanation: "Weather, time, season, and activity all contribute to Scene matching. The list order does not set a fixed priority when several apply.",
  },
  preferences: {
    title: "Tune scheduling",
    description:
      "Response style sets what matters most. Interruption level controls when a switch is appropriate.",
    responseTitle: "Response style",
    responseDescription:
      "Choose what matters more when matching Scenes: longer-term context or current weather and activity. This does not change when switches are allowed.",
    responseExplanations: {
      background: "Season and time have relatively more influence; weather and activity still contribute.",
      background_leaning: "Longer-term context has more influence than in Balanced.",
      balanced: "Longer-term context, current weather, and activity all contribute.",
      current_leaning: "Current weather and activity have more influence than in Balanced.",
      current: "Current weather and activity have the most influence of the five choices; time and season still contribute.",
    },
    disturbanceTitle: "Interruption level",
    disturbanceDescription:
      "Choose a preset, or expand the exact timing values.",
    timingSummary: (startup: number | null, idle: number | null, deferral: number | null, cycle: number | null) =>
      `Startup wait ${startup ?? "—"} s; idle wait ${idle ?? "—"} s; maximum Scene deferral ${deferral ?? "—"} min; minimum same-Scene rotation ${cycle ?? "—"} min.`,
    fineTune: "Fine-tune timing",
    startupGrace: "Startup wait",
    idleBeforeSwitch: "Idle wait",
    maximumDeferral: "Maximum deferral",
    cycleInterval: "Rotation interval",
    seconds: "seconds",
    minutes: "minutes",
    nonNegative: "Enter a non-negative whole number.",
  },
  activity: {
    title: "Recognize activity",
    description:
      "This step is optional. Matching ignores letter case and the .exe suffix in process names.",
    workTitle: "Work",
    leisureTitle: "Leisure",
    processLabel: "Process names",
    titleKeywordLabel: "Window title keywords",
    processPlaceholder: "Enter a process and press Enter",
    keywordPlaceholder: "Enter a keyword and press Enter",
    processHelp: "Enter an executable name, such as Photoshop.exe, then press Enter or Add.",
    titleHelp: "Enter text found in a window title, such as Project plan, then press Enter or Add.",
    add: "Add",
    empty: "Nothing added",
    conflictTitle: "Conflicting rules",
    conflictDescription: (values: string) =>
      `These items appear in both work and leisure: ${values}`,
    matchingHelp: "Process names match exactly, ignoring case and a trailing .exe. Window titles contain the keyword, ignoring case. When no rule matches, activity does not identify work or leisure.",
    pendingWarning: "Text is still waiting in an activity field. Press Enter or Add, or clear it before saving.",
  },
  review: {
    title: "Review and save",
    description:
      "These settings remain a draft until you confirm and save the Profile.",
    missingTitle: "Needed before saving",
    missingDescription: "Complete these settings in any order.",
    wallpaper: "Wallpaper Engine path",
    weather: "Weather test for this draft",
    location: "Location",
    scenes: "Scene assignments",
    response: "Response style",
    disturbance: "Interruption level",
    activity: "Activity rules",
    weatherUntested: "This draft key has not been tested manually",
    weatherNote:
      "This online test checks the current draft key. It is not the live health of the running configuration; saving also validates the location.",
    testedAt: (date: string) => `Tested: ${date}`,
    sceneCount: (bound: number, pending: number) => `${bound} assigned, ${pending} awaiting playlists`,
    changesTitle: "Changes to apply",
    noChanges: "All changes saved.",
    currentDetails: "Review all draft settings",
    edit: "Edit",
    disabled: "Disabled",
    awaitingPlaylist: "Playlist needed",
    secretChanged: "Changed (value hidden)",
    activityCount: (windows: number, processes: number) =>
      `${windows} window rules, ${processes} process names`,
    coordinates: (latitude: number, longitude: number) =>
      `Latitude ${latitude}, longitude ${longitude}`,
    create: "Finish setup",
    creating: "Creating",
    save: "Save and apply",
    saving: "Saving",
    success: "Saved and applied",
    setupSuccess: "Setup is complete. Starting the scheduler.",
  },
  errors: {
    validation: "Complete the required fields on this page first.",
    pendingActivity: "Finish or clear the text waiting in an activity field.",
    fieldValidation:
      "The server found fields that need changes. Follow the messages below.",
    profileAlreadyExists:
      "A Profile already exists. Close this window and reopen Settings from the tray.",
    applyTimeout:
      "The scheduler did not finish applying the change. Your draft is still here; try again.",
    applyUnavailable:
      "The scheduler is not accepting configuration changes right now. Try again shortly.",
    weatherValidationUnavailable:
      "The weather check could not finish. Your draft is still here.",
    locationValidationUnavailable: "Automatic location detection failed.",
    networkReasons: {
      timeout:
        "The connection timed out. Check your network or proxy and try again.",
      proxy_error:
        "The proxy connection failed. Check the system proxy or try another network.",
      tls_error:
        "The secure connection failed. Check your network, proxy, and system clock.",
      connection_error:
        "A connection could not be established. Check your network or proxy.",
      request_error:
        "The network request failed. Check your connection and try again.",
      invalid_json: "The service returned unreadable data. Try again later.",
      invalid_response:
        "The service returned incomplete data. Try again later.",
      provider_error:
        "The location service rejected the lookup. Enter your location manually or try again later.",
    },
    httpRateLimited: "The service is limiting requests. Try again later.",
    httpForbidden:
      "The service denied the request. Check your network or proxy.",
    httpServerError: "The service is temporarily failing. Try again later.",
    httpOther: (status: number) =>
      `The service returned HTTP ${status}. Try again later.`,
    generic: "The operation failed. Your draft is still here; try again.",
    scanCodes: {
      wallpaper_engine_executable_not_found:
        "wallpaper64.exe was not found. Choose the installation manually.",
      wallpaper_engine_config_not_found:
        "Wallpaper Engine config.json was not found. Start Wallpaper Engine once, then try again.",
      wallpaper_engine_config_read_failed:
        "Wallpaper Engine configuration could not be read. Close anything writing it, then try again.",
      unexpected_wallpaper_engine_config_format:
        "The Wallpaper Engine configuration format was not recognized.",
    },
    issueCodes: {
      weather_api_key_invalid: "This API key is invalid.",
      weather_location_invalid:
        "OpenWeatherMap could not use this location. Check the coordinates.",
      weather_api_quota_exceeded:
        "This API key has reached its request quota. Try later or use another key.",
    },
    stages: {
      compile: "configuration compilation",
      prepare: "runtime preparation",
      persist: "Profile write",
    },
  },
};

export const COPY = { zh, en } satisfies Record<Locale, typeof zh>;

export const ZH_TIMING_HINTS = {
  startupGrace:
    "调度器启动至能够尝试切换的最短等待时间，更高的启动等待时间通常可以增加壁纸选择的稳定性。",
  idleBeforeSwitch:
    "停止操作多久后，允许壁纸切换。更短的空闲等待时间通常可以带来更及时的壁纸响应，但也会增加切换次数。",
  maximumDeferral: "距上次壁纸切换达到此时长后，场景切换可不再等待空闲时机。",
  cycleInterval:
    "保持在同一场景时，在当前场景对应的播放列表内进行壁纸轮播时允许的最短间隔。",
} as const;

export const ZH_ACTIVITY_NOTE =
  "休闲指有意进行的娱乐活动。对于不具明确指向性活动，无需进行场景规则配置。";

export const ZH_WEATHER_SAVE_PROMPT = {
  title: "API Key 连通性测试未通过，仍要保存吗？",
  description: "保存后，天气相关场景可能暂时无法响应。你可以稍后重新测试连接。",
} as const;

export const SCENE_LABELS: Record<Locale, Record<SceneId, string>> = {
  zh: {
    day_work: "日间工作",
    day_leisure: "日间休闲",
    night_work: "夜间工作",
    night_leisure: "夜间休闲",
    spring: "春季",
    summer: "夏季",
    autumn: "秋季",
    winter: "冬季",
    sunset: "黄昏",
    rain: "雨天",
  },
  en: {
    day_work: "Day work",
    day_leisure: "Day leisure",
    night_work: "Night work",
    night_leisure: "Night leisure",
    spring: "Spring",
    summer: "Summer",
    autumn: "Autumn",
    winter: "Winter",
    sunset: "Sunset",
    rain: "Rain",
  },
};

export const SCENE_DESCRIPTIONS: Record<Locale, Record<SceneId, string>> = {
  zh: {
    day_work: "白天、当前活动为工作时参与匹配。",
    day_leisure: "白天、当前活动为休闲时参与匹配。",
    night_work: "夜间、当前活动为工作时参与匹配。",
    night_leisure: "夜间、当前活动为休闲时参与匹配。",
    spring: "春季白天更契合，晴好天气加分。",
    summer: "夏季白天更契合，晴好天气加分。",
    autumn: "秋季整体契合，黄昏时加分。",
    winter: "冬季整体契合，黄昏与下雪时加分。",
    sunset: "黄昏时分的氛围场景。",
    rain: "下雨时参与匹配，雷雨时加分。",
  },
  en: {
    day_work: "Matches on daytime while working.",
    day_leisure: "Matches on daytime during leisure.",
    night_work: "Matches at night while working.",
    night_leisure: "Matches at night during leisure.",
    spring: "Fits spring days; clear weather adds weight.",
    summer: "Fits summer days; clear weather adds weight.",
    autumn: "Fits autumn; sunset hours add weight.",
    winter: "Fits winter; sunset and snow add weight.",
    sunset: "An atmosphere scene for sunset hours.",
    rain: "Matches while raining; storms add weight.",
  },
};

export const RESPONSE_STYLE_LABELS: Record<
  Locale,
  Record<import("@/api/profile").ResponseStyle, string>
> = {
  zh: {
    background: "背景优先",
    background_leaning: "偏向背景",
    balanced: "平衡",
    current_leaning: "偏向当前",
    current: "当前优先",
  },
  en: {
    background: "Background first",
    background_leaning: "Lean background",
    balanced: "Balanced",
    current_leaning: "Lean current",
    current: "Current first",
  },
};

export const DISTURBANCE_LABELS: Record<
  Locale,
  Record<DisturbancePreset, string>
> = {
  zh: {
    eager: "积极",
    responsive: "灵敏",
    balanced: "平衡",
    quiet: "安静",
    minimal: "最少打扰",
  },
  en: {
    eager: "Eager",
    responsive: "Responsive",
    balanced: "Balanced",
    quiet: "Quiet",
    minimal: "Minimal",
  },
};
