import { expect, test } from "@playwright/test"
import type { Page } from "@playwright/test"
import type { Profile } from "../src/api/profile"

const profile: Profile = {
  version: 1,
  setup_complete: true,
  wallpaper_engine_path: "C:\\Wallpaper Engine\\wallpaper64.exe",
  language: "zh",
  weather: {
    api_key: "saved-key",
    location: { name: "上海", latitude: 31.2304, longitude: 121.4737 },
  },
  scenes: { day_work: "CASUAL_ANIME" },
  matching: { response_style: "balanced" },
  disturbance: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 20,
    maximum_deferral_minutes: 60,
    cycle_interval_minutes: 15,
  },
  activity: {
    work_processes: [],
    leisure_processes: [],
    work_title_keywords: [],
    leisure_title_keywords: [],
  },
}

async function mockSetupApi(page: Page, hasProfile: boolean, settingsProfile: Profile = profile): Promise<void> {
  await page.route("**/api/profile", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill(hasProfile ? { json: { profile: settingsProfile } } : { status: 404, json: { error: "profile_not_found" } })
      return
    }
    await route.fulfill({ json: { status: "applied", profile: settingsProfile } })
  })
  await page.route("**/api/scenes", async (route) => {
    await route.fulfill({ json: { scenes: ["day_work", "day_leisure", "night_work", "night_leisure", "rain", "sunset"].map((id) => ({ id })) } })
  })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: { wallpaper_engine_path: profile.wallpaper_engine_path, playlists: [{ name: "CASUAL_ANIME", item_count: 60 }] } })
  })
}

test("首次设置允许自由选择分类，并在检查页指出未完成设置", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh")

  const navigation = page.getByRole("navigation", { name: "设置项" })
  await expect(navigation).toBeVisible()
  await expect(navigation.locator("button")).toHaveCount(6)
  await expect(navigation.getByRole("button", { name: /天气服务/ }).locator("[data-next-required]")).toBeVisible()
  await expect(page.getByText("1 / 7")).toHaveCount(0)
  await navigation.getByRole("button", { name: /天气服务/ }).click()
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toBeVisible()
  await expect(page.getByRole("textbox", { name: "城市名称" })).toHaveCount(0)
  await navigation.getByRole("button", { name: /Wallpaper Engine/ }).click()
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()
  await expect(page.getByText("Wallpaper Engine 中的播放列表名称")).toBeVisible()
  await expect(page.getByText("CASUAL_ANIME")).toBeVisible()
  await expect(page.getByText("60 张")).toBeVisible()
  await expect(page.getByText(/英文字母与数字/)).toBeVisible()

  await navigation.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key" }).fill("test-key")
  await navigation.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("spinbutton", { name: "纬度" }).fill("31.2304")
  await page.getByRole("spinbutton", { name: "经度" }).fill("121.4737")
  await navigation.getByRole("button", { name: /场景绑定/ }).click()

  for (const name of ["日间工作", "日间休闲", "夜间工作", "夜间休闲", "雨天"]) {
    await expect(page.getByRole("checkbox", { name })).toBeChecked()
  }
  await expect(page.getByText("添加其他场景")).toHaveCount(0)
  await expect(page.getByText(/多个场景可以共用一个播放列表/)).toBeVisible()
  await page.getByRole("button", { name: "日间工作: 播放列表" }).click()
  await expect(page.getByRole("option", { name: "CASUAL_ANIME" })).toBeVisible()
  await page.keyboard.press("Escape")
  await navigation.getByRole("button", { name: /查看配置草稿/ }).click()
  await expect(page.getByText("已绑定 0 个，待绑定 5 个")).toBeVisible()
  await expect(page.getByText("配置项缺失")).toBeVisible()
  await page.getByRole("alert").getByRole("button", { name: "场景绑定", exact: true }).click()
  await expect(page.getByText("至少启用并绑定一个场景。")).toBeVisible()
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toHaveAttribute("aria-invalid", "true")
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toHaveAttribute("aria-describedby", "scene-error-day_work")
  await expect(page.locator("#scene-error-day_work")).toContainText("请为此场景选择播放列表。")
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toBeFocused()
})

test("场景绑定按三组折叠分区展示卡片，未启用场景在组内灰显", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, scenes: { day_work: "CASUAL_ANIME" } })
  await page.route("**/api/scenes", async (route) => {
    await route.fulfill({ json: { scenes: [
      "day_work", "day_leisure", "night_work", "night_leisure",
      "spring", "summer", "autumn", "winter",
      "sunset", "rain",
    ].map((id) => ({ id })) } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()

  await expect(page.getByRole("button", { name: /季节氛围/ })).toBeVisible()
  await expect(page.getByRole("button", { name: /日常情境/ })).toBeVisible()
  await expect(page.getByRole("button", { name: /天气氛围/ })).toBeVisible()
  await expect(page.getByText("已启用 0/4", { exact: true })).toBeVisible()
  await expect(page.getByText("已启用 1/4", { exact: true })).toBeVisible()
  await expect(page.getByText("已启用 0/2", { exact: true })).toBeVisible()
  await expect(page.getByText("添加其他场景")).toHaveCount(0)
  await expect(page.getByRole("checkbox", { name: "黄昏" })).toBeVisible()
  await expect(page.getByRole("checkbox", { name: "雨天" })).toBeVisible()

  const groupHeaders = page.getByRole("button", { name: /^(季节氛围|日常情境|天气氛围)/ })
  await expect(groupHeaders).toHaveText([/^季节氛围/, /^日常情境/, /^天气氛围/])
  const sunsetCard = page.getByRole("checkbox", { name: "黄昏" }).locator("xpath=ancestor::*[@data-disabled]")
  await expect(sunsetCard).toHaveCSS("opacity", "0.6")
  const dayWorkCard = page.getByRole("checkbox", { name: "日间工作" }).locator("xpath=ancestor::*[contains(@class,'rounded-lg')][1]")
  await expect(dayWorkCard).not.toHaveCSS("opacity", "0.6")
})

test("勾选只激活场景卡，播单经卡内选择器显式绑定", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, scenes: {} })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()

  await page.getByRole("checkbox", { name: "雨天" }).click()
  const pickerTrigger = page.getByRole("button", { name: "雨天: 播放列表" })
  await expect(pickerTrigger).toContainText("选择播放列表")
  await expect(page.getByRole("option", { name: "CASUAL_ANIME" })).toHaveCount(0)

  await pickerTrigger.click()
  await expect(page.getByRole("option", { name: "CASUAL_ANIME" })).toBeVisible()
  await expect(page.getByRole("option", { name: /60/ })).toHaveCount(0)

  await page.getByRole("option", { name: "CASUAL_ANIME" }).click()
  await expect(pickerTrigger).toContainText("CASUAL_ANIME")
  await expect(pickerTrigger).not.toContainText("60")
  await expect(page.getByText("60 张壁纸", { exact: true })).toBeVisible()
  await expect(page.getByRole("option", { name: "CASUAL_ANIME" })).toHaveCount(0)
})

test("点击卡片主体可切换场景，卡内选择器不承担启停", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, scenes: {} })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()

  await page.getByText("下雨时参与匹配，雷雨时加分。").click()
  await expect(page.getByRole("checkbox", { name: "雨天" })).toBeChecked()

  await page.getByRole("button", { name: "雨天: 播放列表" }).click()
  await expect(page.getByRole("checkbox", { name: "雨天" })).toBeChecked()
  await page.keyboard.press("Escape")

  await page.getByText("下雨时参与匹配，雷雨时加分。").click()
  await expect(page.getByRole("checkbox", { name: "雨天" })).not.toBeChecked()
})

test("没有可用播放列表时，场景页可直接跳到 Wallpaper Engine", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: { wallpaper_engine_path: profile.wallpaper_engine_path, playlists: [] } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()
  await expect(page.getByText("场景绑定需要至少一个包含壁纸的播放列表。")).toBeVisible()
  await page.getByRole("button", { name: "连接 Wallpaper Engine" }).click()
  await expect(page.getByRole("heading", { name: "连接 Wallpaper Engine" })).toBeVisible()
})

test("天气页测试 Key 时说明代理失败原因", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "proxy_error" } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await expect(page.getByText("如何获取 API Key")).toBeVisible()
  await page.getByText("如何获取 API Key").click()
  await expect(page.getByText(/Generate/)).toBeVisible()
  await expect(page.getByText("确认该 Key 的 Status 为 Active，再粘贴 Key 到上方输入框。")).toBeVisible()
  await page.getByRole("button", { name: "测试连接" }).click()
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.locator("p", { hasText: "尚未验证 API Key" })).toBeVisible()
  await expect(statusBlock.locator("p", { hasText: /连接天气服务失败/ })).toBeVisible()
  await expect(page.getByText(/代理连接失败/)).toBeVisible()
})

test("无效 Key 的提示不推测激活状态", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ status: 422, json: { error: "weather_validation_failed", issues: [{ path: ["weather", "api_key"], code: "weather_api_key_invalid", message: "weather_api_key_invalid" }] } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(page.getByText("无效的 API Key。", { exact: true })).toBeVisible()
  await expect(page.getByText(/连接天气服务失败/)).toHaveCount(0)
})

test("天气页测试当前草稿 Key 后显示成功", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ json: { status: "valid" } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key" }).fill("another-key")
  const keyTestRequest = page.waitForRequest((request) => request.url().endsWith("/api/weather-key-validations") && request.method() === "POST")
  await page.getByRole("button", { name: "测试连接" }).click()
  expect((await keyTestRequest).postDataJSON()).toEqual({ api_key: "another-key" })
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.locator("p", { hasText: "API Key 有效" })).toBeVisible()
  await expect(statusBlock.locator("p", { hasText: /验证时间：/ })).toBeVisible()
})

test("经纬度估算失败说明原因，仍可手填坐标", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ status: 503, json: { error: "location_detection_unavailable", reason: "proxy_error" } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByText(/代理连接失败/)).toBeVisible()
  await expect(page.getByRole("button", { name: "打开地图查找坐标" })).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度" }).fill("39.9042")
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toHaveValue("39.9042")
})

test("经纬度估算不需要城市名称", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ json: { location: { latitude: 47.498253, longitude: 19.03978 } } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toHaveValue("47.498253")
  await expect(page.getByRole("spinbutton", { name: "经度" })).toHaveValue("19.03978")
  await expect(page.getByRole("textbox", { name: "城市名称" })).toHaveCount(0)
  await page.getByRole("button", { name: "查看配置草稿" }).last().click()
  await page.getByText("查看当前草稿全部设置").click()
  await expect(page.getByText("纬度 47.498253，经度 19.03978", { exact: true })).toBeVisible()
})

test("经纬度估算显示 IP 返回的城市，手动修改后清除提示", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ json: { location: { city: "Budapest", latitude: 47.498253, longitude: 19.03978 } } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByText("城市：Budapest，已填入预估经纬度。")).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度" }).fill("47.5")
  await expect(page.getByText("城市：Budapest，已填入预估经纬度。")).toHaveCount(0)
})

test("保存成功提示出现在窗口顶部", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /调度风格/ }).click()
  await page.getByRole("button", { name: "当前优先" }).click()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /查看配置草稿/ }).click()
  const saveRequest = page.waitForRequest((request) => request.url().endsWith("/api/profile") && request.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  expect((await saveRequest).postDataJSON().scenes).toEqual({ day_work: "CASUAL_ANIME" })

  const notice = page.getByText("已保存并生效")
  await expect(notice).toBeVisible()
  const bounds = await notice.boundingBox()
  expect(bounds).not.toBeNull()
  expect(bounds!.y).toBeLessThan(200)
})

test("检查页显示路径、测试状态、坐标及两类 Activity 规则数", async ({ page }) => {
  const configuredProfile: Profile = {
    ...profile,
    activity: {
      work_processes: ["code"],
      leisure_processes: ["steam"],
      work_title_keywords: ["IDE"],
      leisure_title_keywords: ["游戏"],
    },
  }
  await mockSetupApi(page, true, configuredProfile)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ json: { status: "valid" } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /查看配置草稿/ }).click()
  await page.getByText("查看当前草稿全部设置").click()

  await expect(page.getByText("Wallpaper Engine 路径")).toBeVisible()
  await expect(page.getByText(configuredProfile.wallpaper_engine_path)).toBeVisible()
  await expect(page.getByText("本次草稿的天气测试")).toBeVisible()
  await expect(page.getByText("当前草稿密钥尚未手动测试")).toBeVisible()
  await expect(page.getByText("纬度 31.2304，经度 121.4737")).toBeVisible()
  await expect(page.getByText("窗口名规则 2 条，进程名规则 2 条")).toBeVisible()

  await page.getByRole("button", { name: "测试连接" }).click()
  const weatherRow = page.locator("dd").filter({ has: page.getByRole("button", { name: "测试连接" }) })
  await expect(weatherRow.locator("p", { hasText: "API Key 有效" })).toBeVisible()
  await expect(weatherRow.locator("p", { hasText: /^验证时间：/ })).toBeVisible()
})

test("桌面布局使用宽屏空间，窄窗口没有外层纵向滚动", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: {
      wallpaper_engine_path: profile.wallpaper_engine_path,
      playlists: Array.from({ length: 11 }, (_, index) => ({ name: `PLAYLIST_${index + 1}`, item_count: index + 1 })),
    } })
  })
  await page.setViewportSize({ width: 2560, height: 1350 })
  await page.goto("/?locale=zh")
  await expect(page.getByRole("heading", { name: "连接 Wallpaper Engine" })).toHaveCount(1)
  const wideBounds = await page.locator("main > div").first().boundingBox()
  expect(wideBounds).not.toBeNull()
  expect(wideBounds!.width).toBeGreaterThan(1500)

  await page.setViewportSize({ width: 1100, height: 800 })
  const hasOuterScroll = await page.evaluate(() => document.documentElement.scrollHeight > window.innerHeight)
  expect(hasOuterScroll).toBe(false)
  await expect(page.getByRole("button", { name: "查看配置草稿" }).last()).toBeVisible()
})

test("侧栏收窄为 224px，表单页与场景页按内容类型限宽", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto("/?locale=zh")

  // 布局契约：aside 14rem = 224px；表单内容 47.5rem = 760px；宽步骤（场景）max-w-4xl = 896px。
  const aside = page.locator("aside")
  const asideWidth = await aside.boundingBox()
  expect(asideWidth).not.toBeNull()
  expect(Math.round(asideWidth!.width)).toBe(224)

  const stepContent = page.locator("#setup-step-content > div")
  const formWidth = await stepContent.boundingBox()
  expect(formWidth).not.toBeNull()
  expect(Math.round(formWidth!.width)).toBe(760)

  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()
  const sceneWidth = await stepContent.boundingBox()
  expect(sceneWidth).not.toBeNull()
  expect(Math.round(sceneWidth!.width)).toBe(896)
})

test("长播单名称不会让场景绑定横向溢出", async ({ page }) => {
  const longName = `LONG_PLAYLIST_${"WALLPAPER_".repeat(20)}`
  await mockSetupApi(page, true, { ...profile, scenes: { day_work: longName } })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: {
      wallpaper_engine_path: profile.wallpaper_engine_path,
      playlists: [{ name: longName, item_count: 60 }],
    } })
  })
  await page.setViewportSize({ width: 1200, height: 780 })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /场景绑定/ }).click()
  await expect(page.getByRole("heading", { name: "绑定使用场景" })).toBeVisible()

  const content = page.locator('[data-slot="card-content"]')
  const hasHorizontalOverflow = await content.evaluate((element) => element.scrollWidth > element.clientWidth)
  expect(hasHorizontalOverflow).toBe(false)
})

test("四个防打扰时间项通过问号说明，活动规则保留中立活动", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "自定义防打扰设置" }).click()

  for (const [label, hint] of [
    ["启动等待", "调度器启动至能够尝试切换的最短等待时间"],
    ["空闲等待", "停止操作多久后，允许壁纸切换"],
    ["最长延后", "距上次壁纸切换达到此时长后"],
    ["轮换间隔", "保持在同一场景时"],
  ]) {
    await page.mouse.move(0, 0)
    await page.getByRole("button", { name: `${label}说明` }).hover()
    await expect(page.getByText(hint, { exact: false })).toBeVisible()
  }

  await navigation.getByRole("button", { name: "活动识别" }).click()
  await expect(page.getByText("休闲指有意进行的娱乐活动。对于不具明确指向性活动，无需进行场景规则配置。")).toBeVisible()
})

test("已验证的当前 API Key 可直接保存，后续网络故障不抹去通过记录", async ({ page }) => {
  await mockSetupApi(page, true)
  let attempts = 0
  await page.route("**/api/weather-key-validations", async (route) => {
    attempts += 1
    await route.fulfill(attempts === 1
      ? { json: { status: "valid" } }
      : { status: 503, json: { error: "weather_validation_unavailable", reason: "timeout" } })
  })
  await page.route("**/api/profile?allow_unverified_weather=1", async (route) => {
    const updated = route.request().postDataJSON() as Profile
    await route.fulfill({ json: { status: "applied", profile: updated } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key" }).fill("another-key")
  await page.getByRole("button", { name: "测试连接" }).click()
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.locator("p", { hasText: "API Key 有效" })).toBeVisible()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(statusBlock.locator("p", { hasText: "API Key 有效" })).toBeVisible()
  await expect(statusBlock.locator("p", { hasText: /连接天气服务失败/ })).toBeVisible()
  await expect(statusBlock.locator("p", { hasText: /连接超时/ })).toBeVisible()

  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  const saveRequest = page.waitForRequest((request) => request.url().includes("allow_unverified_weather=1") && request.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  expect((await saveRequest).postDataJSON().weather.api_key).toBe("another-key")
  await expect(page.getByText("已保存并生效")).toBeVisible()
})

test("天气服务暂不可用时可确认保存当前草稿", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "timeout" } })
  })
  await page.route("**/api/profile?allow_unverified_weather=1", async (route) => {
    const updated = route.request().postDataJSON() as Profile
    await route.fulfill({ json: { status: "applied", profile: updated } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key" }).fill("another-key")
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(page.getByText(/连接超时/)).toBeVisible()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  await page.getByRole("button", { name: "保存并应用" }).click()
  const confirmation = page.getByRole("alertdialog", { name: "API Key 连通性测试未通过，仍要保存吗？" })
  await expect(confirmation).toBeVisible()
  const saveRequest = page.waitForRequest((request) => request.url().includes("allow_unverified_weather=1") && request.method() === "PUT")
  await confirmation.getByRole("button", { name: "保存并应用" }).click()
  expect((await saveRequest).postDataJSON().weather.api_key).toBe("another-key")
  await expect(page.getByText("已保存并生效")).toBeVisible()
})

test("保存时才遇到天气连接故障，也可确认继续保存", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/profile**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fallback()
    } else if (route.request().url().includes("allow_unverified_weather=1")) {
      await route.fulfill({ json: { status: "applied", profile: route.request().postDataJSON() } })
    } else {
      await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "timeout" } })
    }
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key" }).fill("another-key")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  await page.getByRole("button", { name: "保存并应用" }).click()
  const confirmation = page.getByRole("alertdialog", { name: "API Key 连通性测试未通过，仍要保存吗？" })
  await expect(confirmation).toBeVisible()
  await expect(confirmation).toContainText("连接超时")
  await confirmation.getByRole("button", { name: "保存并应用" }).click()
  await expect(page.getByText("已保存并生效")).toBeVisible()
})

test("语言与外观位于侧栏底部，主题选择可保留并跟随系统", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.emulateMedia({ colorScheme: "light" })
  await page.goto("/?locale=zh")

  const navigation = page.getByRole("navigation", { name: "设置项" })
  const language = page.getByRole("group", { name: "语言" })
  const navBounds = await navigation.boundingBox()
  const languageBounds = await language.boundingBox()
  expect(navBounds).not.toBeNull()
  expect(languageBounds).not.toBeNull()
  expect(languageBounds!.y).toBeGreaterThan(navBounds!.y + navBounds!.height)
  await language.getByRole("button", { name: "English" }).click()
  await expect(page.getByRole("heading", { name: "Connect Wallpaper Engine" })).toBeVisible()
  await page.getByRole("group", { name: "Language" }).getByRole("button", { name: "中文" }).click()

  const theme = page.getByRole("combobox", { name: "外观: 跟随系统" })
  await expect(theme).toBeVisible()
  const triggerBounds = await theme.boundingBox()
  const iconBounds = await theme.locator("svg").first().boundingBox()
  expect(triggerBounds).not.toBeNull()
  expect(iconBounds).not.toBeNull()
  expect(Math.abs(iconBounds!.x + iconBounds!.width / 2 - triggerBounds!.x - triggerBounds!.width / 2)).toBeLessThan(1)
  await expect(page.locator("html")).not.toHaveClass(/dark/)
  const lightBackground = await page.locator("body").evaluate((body) => getComputedStyle(body).backgroundColor)

  await theme.click()
  await page.getByRole("option", { name: "深色" }).click()
  await expect(page.locator("html")).toHaveClass(/dark/)
  const darkBackground = await page.locator("body").evaluate((body) => getComputedStyle(body).backgroundColor)
  expect(darkBackground).not.toBe(lightBackground)
  await page.reload()
  await expect(page.getByRole("combobox", { name: "外观: 深色" })).toBeVisible()
  await expect(page.locator("html")).toHaveClass(/dark/)

  await page.getByRole("combobox", { name: "外观: 深色" }).click()
  await page.getByRole("option", { name: "跟随系统" }).click()
  await expect(page.locator("html")).not.toHaveClass(/dark/)
  await page.emulateMedia({ colorScheme: "dark" })
  await expect(page.locator("html")).toHaveClass(/dark/)

  await page.getByRole("combobox", { name: "外观: 跟随系统" }).click()
  await page.getByRole("option", { name: "浅色" }).click()
  await expect(page.locator("html")).not.toHaveClass(/dark/)
})

test("保存期间锁定编辑，返回的配置与本次提交一致", async ({ page }) => {
  await mockSetupApi(page, true)
  let release!: () => void
  const gate = new Promise<void>((resolve) => { release = resolve })
  await page.route("**/api/profile", async (route) => {
    if (route.request().method() === "GET") return route.fallback()
    await gate
    await route.fulfill({ json: { status: "applied", profile: route.request().postDataJSON() } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "当前优先" }).click()
  const request = page.waitForRequest((item) => item.url().endsWith("/api/profile") && item.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  try {
    expect((await request).postDataJSON().matching.response_style).toBe("current")
    await expect(page.getByRole("button", { name: "正在保存" })).toBeVisible()
    expect(await page.locator("nav").evaluate((element) => element.hasAttribute("inert"))).toBe(true)
    expect(await page.locator("#setup-step-content").evaluate((element) => element.hasAttribute("inert"))).toBe(true)
  } finally {
    release()
  }
  await expect(page.getByText("已保存并生效")).toBeVisible()
  await expect(page.getByRole("button", { name: "当前优先" })).toHaveAttribute("aria-pressed", "true")
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()
})

test("未添加的活动文字跨分类保留，保存前要求处理", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "活动识别" }).click()
  await page.locator("#work-processes").fill("Photoshop.exe")
  await page.locator("#work-title-keywords").fill("项目计划")
  await navigation.getByRole("button", { name: "调度风格" }).click()
  await navigation.getByRole("button", { name: /活动识别/ }).click()
  await expect(page.locator("#work-processes")).toHaveValue("Photoshop.exe")
  await page.getByRole("button", { name: "保存并应用" }).click()
  await expect(page.locator("#work-processes")).toHaveAttribute("aria-invalid", "true")
  await expect(page.getByText("请先处理尚未添加的活动规则文字。")).toBeVisible()
  await page.locator("#work-processes").press("Enter")
  await expect(page.locator("#work-title-keywords")).toHaveAttribute("aria-invalid", "true")
  await page.locator("#work-title-keywords").press("Enter")
  const request = page.waitForRequest((item) => item.url().endsWith("/api/profile") && item.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  expect((await request).postDataJSON().activity.work_processes).toEqual(["Photoshop.exe"])
})

test("重新启用恢复上次绑定且不弹选择器，首次启用不默认绑定", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, scenes: { day_work: "CASUAL_ANIME", rain: "RAIN" } })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: { wallpaper_engine_path: profile.wallpaper_engine_path, playlists: [
      { name: "CASUAL_ANIME", item_count: 60 },
      { name: "RAIN", item_count: 20 },
    ] } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()

  await page.getByRole("checkbox", { name: "雨天" }).click()
  await page.getByRole("checkbox", { name: "雨天" }).click()
  await expect(page.getByRole("option", { name: "RAIN" })).toHaveCount(0)
  await expect(page.getByRole("button", { name: "雨天: 播放列表" })).toContainText("RAIN")
  await expect(page.getByText("20 张壁纸", { exact: true })).toBeVisible()

  await page.getByRole("checkbox", { name: "日间休闲" }).click()
  await expect(page.getByRole("button", { name: "日间休闲: 播放列表" })).toContainText("选择播放列表")
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()
})

test("日常设置直接保存并列出具体修改，未修改时禁用保存", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/profile", async (route) => {
    if (route.request().method() === "GET") return route.fallback()
    await route.fulfill({ json: { status: "applied", profile: route.request().postDataJSON() } })
  })
  await page.goto("/?locale=zh")
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "当前优先" }).click()
  await expect(page.getByText("有未保存的修改")).toBeVisible()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  await expect(page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" })).toHaveAttribute("aria-current", "page")
  await expect(page.getByText("平衡 → 当前优先")).toBeVisible()
  await page.getByRole("button", { name: "保存并应用" }).click()
  await expect(page.getByText("所有修改已保存。", { exact: true })).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()
})

test("关闭确认说明修改后果，窄窗口档位仍可选择", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.setViewportSize({ width: 900, height: 600 })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await expect(page.getByRole("combobox", { name: "响应风格" })).toBeVisible()
  await page.getByRole("combobox", { name: "响应风格" }).click()
  await page.getByRole("option", { name: "当前优先" }).click()
  await page.getByRole("button", { name: "关闭" }).click()
  const dialog = page.getByRole("alertdialog", { name: "放弃未保存的修改？" })
  await expect(dialog).toContainText("当前运行设置不会改变，本次修改将丢失。")
  await expect(dialog.getByRole("button", { name: "继续编辑" })).toBeVisible()
  await expect(dialog.getByRole("button", { name: "放弃修改" })).toBeVisible()
})

test("无效时间输入与错误说明关联", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "自定义防打扰设置" }).click()
  const startup = page.getByRole("spinbutton", { name: "启动等待" })
  await startup.fill("-1")
  await expect(startup).toHaveAttribute("aria-invalid", "true")
  await expect(startup).toHaveAttribute("aria-describedby", "timing-error-startup_grace_seconds")
  await expect(page.locator("#timing-error-startup_grace_seconds")).toContainText("请输入不小于 0 的整数")
})

test("选择器内搜索过滤播单，重开后搜索词已清空", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: {
      wallpaper_engine_path: profile.wallpaper_engine_path,
      playlists: [
        { name: "CASUAL_ANIME", item_count: 60 },
        ...Array.from({ length: 8 }, (_, index) => ({ name: `OTHER_${index}`, item_count: 2 })),
        { name: "RAIN", item_count: 20 },
      ],
    } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()

  await page.getByRole("button", { name: "日间工作: 播放列表" }).click()
  await page.getByRole("combobox", { name: "搜索播放列表" }).fill("RAIN")
  await expect(page.getByRole("option", { name: "RAIN" })).toBeVisible()
  await expect(page.getByRole("option", { name: "OTHER_0" })).toHaveCount(0)
  await page.getByRole("option", { name: "RAIN" }).click()
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toContainText("RAIN")

  await page.getByRole("button", { name: "日间工作: 播放列表" }).click()
  await expect(page.getByRole("combobox", { name: "搜索播放列表" })).toHaveValue("")
  await expect(page.getByRole("option", { name: "OTHER_0" })).toBeVisible()
})
