const zh = {
  title: "连接天气服务",
  description: "",
  keyLabel: "OpenWeatherMap API Key",
  keyPlaceholder: "粘贴 API Key",
  keyRequired: "请先填写 API Key。",
  getKey: "获取 API Key",
  guideTitle: "如何获取 API Key",
  guideSteps: [
    {
      title: "注册账号",
      action: "打开 OpenWeatherMap，注册账号并登录。已有账号可直接登录。",
    },
    {
      title: "生成 API Key",
      action: "在 API keys 页面点击 Generate 生成 API Key。",
    },
    {
      title: "确认状态并粘贴",
      action: "确认该 Key 的 Status 为 Active，再粘贴 Key 到上方输入框。",
    },
  ],
  validate: "测试连接",
  validating: "正在测试",
  keyValid: "API Key 有效",
  keyUntested: "尚未验证 API Key",
  testedAt: (date: string) => `验证时间：${date}`,
  connectionFailed: (reason: string) => `连接天气服务失败：${reason}`,
  validationMissing: "请先填写 API Key，再测试连接。",
};

const en = {
  title: "Connect weather",
  description: "",
  keyLabel: "OpenWeatherMap API key",
  keyPlaceholder: "Paste API key",
  keyRequired: "Enter an API key first.",
  getKey: "Get an API key",
  guideTitle: "How to get an API key",
  guideSteps: [
    {
      title: "Create an account",
      action: "Create an OpenWeatherMap account and sign in. If you already have one, sign in.",
    },
    {
      title: "Generate an API key",
      action: "Click Generate on the API keys page.",
    },
    {
      title: "Check status and paste",
      action: "Make sure the key's Status is Active, then copy the key itself into the field above.",
    },
  ],
  validate: "Test connection",
  validating: "Testing",
  keyValid: "API key is valid",
  keyUntested: "API key not verified yet",
  testedAt: (date: string) => `Verified at ${date}`,
  connectionFailed: (reason: string) => `Could not reach the weather service: ${reason}`,
  validationMissing: "Enter an API key before testing the connection.",
};

export const WEATHER_COPY = { zh, en };

export const ZH_WEATHER_SAVE_PROMPT = {
  title: "API Key 连通性测试未通过，仍要保存吗？",
  description: "保存后，天气相关场景可能暂时无法响应。你可以稍后重新测试连接。",
} as const;
