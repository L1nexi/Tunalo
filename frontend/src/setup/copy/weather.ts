const zh = {
  title: "连接天气服务",
  description: "Tunalo 使用 OpenWeatherMap 获取天气，日出日落根据地点在本地计算。密钥仅保存于本地。",
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
};

const en = {
  title: "Connect weather",
  description:
    "Tunalo uses OpenWeatherMap for weather conditions and calculates sunrise and sunset locally from your location. The key stays in the local Profile.",
  keyLabel: "OpenWeatherMap API key",
  keyDescription: "Enter a valid Current Weather API key. Weather changes are checked online before saving.",
  keyPlaceholder: "Paste API key",
  keyRequired: "Enter an API key first.",
  getKey: "Get an API key",
  guideTitle: "How to get an API key",
  guideSteps: [
    {
      title: "Create an account",
      action: "Create an OpenWeatherMap account and sign in. If you already have one, sign in.",
      expected: "You can open the API keys page after signing in.",
      fallback: "If the site asks you to verify your email, follow its instructions first.",
    },
    {
      title: "Generate an API key",
      action: "Click Generate on the API keys page.",
      expected: "The new key appears in your account's key list.",
      fallback: "Use the Get an API key button here if you cannot find the page.",
    },
    {
      title: "Check status and paste",
      action: "Make sure the key's Status is Active, then copy the key itself into the field above.",
      expected: "Select Test connection and continue to location after it succeeds.",
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
};

export const WEATHER_COPY = { zh, en };

export const ZH_WEATHER_SAVE_PROMPT = {
  title: "API Key 连通性测试未通过，仍要保存吗？",
  description: "保存后，天气相关场景可能暂时无法响应。你可以稍后重新测试连接。",
} as const;
