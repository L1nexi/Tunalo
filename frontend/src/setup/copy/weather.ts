const zh = {
  title: "连接天气服务",
  description: "",
  validate: "测试连接",
  validating: "正在测试",
  connectionValid: "天气连接正常",
  connectionUntested: "当前坐标尚未测试连接",
  testedAt: (date: string) => `验证时间：${date}`,
  connectionFailed: (reason: string) => `连接天气服务失败：${reason}`,
  validationMissing: "请先填写有效的经纬度，再测试连接。",
  attribution: "天气数据来自 Open-Meteo",
};

const en = {
  title: "Connect weather",
  description: "",
  validate: "Test connection",
  validating: "Testing",
  connectionValid: "Weather connection is working",
  connectionUntested: "Connection not tested for these coordinates",
  testedAt: (date: string) => `Verified at ${date}`,
  connectionFailed: (reason: string) => `Could not reach the weather service: ${reason}`,
  validationMissing: "Enter valid coordinates before testing the connection.",
  attribution: "Weather data by Open-Meteo",
};

export const WEATHER_COPY = { zh, en };

export const ZH_WEATHER_SAVE_PROMPT = {
  title: "天气连接测试未通过，仍要保存吗？",
  description: "保存后，天气相关场景可能暂时无法响应。你可以稍后重新测试连接。",
} as const;
