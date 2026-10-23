import { expect, test } from "@playwright/test"
import type { Profile } from "../src/api/profile"

import { mockSetupApi, profile, addPreset, saveSettings } from "./support/profileApi"

test("首次设置允许自由选择分类，并在检查页指出未完成设置", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh")

  const navigation = page.getByRole("navigation", { name: "设置项" })
  await expect(navigation).toBeVisible()
  await navigation.getByRole("button", { name: /天气服务/ }).click()
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toBeVisible()
  await expect(page.getByText("请填写纬度。", { exact: true })).toBeHidden()
  await expect(page.getByText("请填写经度。", { exact: true })).toBeHidden()
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

  await expect(page.getByText("添加你的第一个场景")).toBeVisible()
  await addPreset(page, "时间与活动", "日间工作")
  await expect(page.getByText(/多个场景可以共用一个播放列表/)).toBeVisible()
  await page.getByRole("button", { name: "日间工作: 播放列表" }).click()
  await expect(page.getByRole("option", { name: "CASUAL_ANIME" })).toBeVisible()
  await page.keyboard.press("Escape")
  await navigation.getByRole("button", { name: /查看配置草稿/ }).click()
  await expect(page.getByText("已绑定 0 个，待绑定 1 个")).toBeVisible()
  await expect(page.getByText("配置项缺失")).toBeVisible()
  await page.getByRole("alert").getByRole("button", { name: "场景绑定", exact: true }).click()
  await expect(page.getByText("至少添加一个场景，并为所有场景选择播放列表。")).toBeVisible()
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toHaveAttribute("aria-invalid", "true")
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toHaveAccessibleDescription("请为此场景选择播放列表。")
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toBeFocused()
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
  await expect(statusBlock.getByText("尚未验证 API Key")).toBeVisible()
  await expect(statusBlock.getByText(/连接天气服务失败/)).toBeVisible()
  await expect(page.getByText(/代理连接失败/)).toBeVisible()
})

test("无效的天气密钥显示字段错误", async ({ page }) => {
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
  await page.getByRole("navigation").getByRole("button", { name: "查看配置草稿", exact: true }).click()
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
  await expect(page.getByRole("status").filter({ hasText: "API Key 有效" })).toBeVisible()
  await expect(page.getByText(/^验证时间：/)).toBeVisible()
})

test("三个调度时间项通过问号说明，活动规则保留中立活动", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "自定义防打扰设置" }).click()

  for (const [label, hint] of [
    ["启动等待", "调度器启动至能够尝试切换的最短等待时间"],
    ["空闲等待", "停止操作多久后，允许壁纸切换"],
    ["基础轮换间隔", "从上次成功切换起计算"],
  ]) {
    await page.mouse.move(0, 0)
    await page.getByRole("button", { name: `${label}说明` }).hover()
    await expect(page.getByText(hint, { exact: false })).toBeVisible()
  }

  await navigation.getByRole("button", { name: "活动识别" }).click()
  await expect(page.getByText("标题关键词优先于进程名。休闲指明确的娱乐活动；未命中规则时，本次活动不计为工作或休闲。")).toBeVisible()
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
  const tested = page.waitForRequest((request) => new URL(request.url()).pathname === "/api/weather-key-validations" && request.method() === "POST")
  await page.getByRole("button", { name: "测试连接" }).click()
  expect((await tested).postDataJSON()).toEqual({ api_key: "another-key" })
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.getByText("API Key 有效")).toBeVisible()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(statusBlock.getByText("API Key 有效")).toBeVisible()
  await expect(statusBlock.getByText(/连接天气服务失败/)).toBeVisible()
  await expect(statusBlock.getByText(/连接超时/)).toBeVisible()

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
  // 保存成功只清提交侧反馈；天气测试的失败事实连同真实原因一并保留，不退化成泛化兜底文案。
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.getByText(/连接天气服务失败/)).toBeVisible()
  await expect(statusBlock.getByText(/连接超时/)).toBeVisible()
  await expect(page.getByText("操作失败。草稿仍然保留，请重试。")).toHaveCount(0)
})

test("坐标越界或缺失时就近提示，不再等检查页", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()

  await page.getByRole("spinbutton", { name: "纬度" }).fill("121.4737")
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()

  // 切走再切回，编辑过的坐标仍就近提示，与保存禁用状态保持同步。
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toBeVisible()

  await page.getByRole("spinbutton", { name: "经度" }).fill("")
  await expect(page.getByText("请填写经度。")).toBeVisible()

  await page.getByRole("spinbutton", { name: "纬度" }).fill("31.2304")
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toHaveCount(0)
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

test("语言切换与主题选择可保留并跟随系统", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.emulateMedia({ colorScheme: "light" })
  await page.goto("/?locale=zh")

  await page.getByRole("group", { name: "语言" }).getByRole("button", { name: "English" }).click()
  await expect(page.getByRole("heading", { name: "Connect Wallpaper Engine" })).toBeVisible()
  await page.getByRole("group", { name: "Language" }).getByRole("button", { name: "中文" }).click()
  await expect(page.getByRole("heading", { name: "连接 Wallpaper Engine" })).toBeVisible()

  const background = () => page.getByRole("main").evaluate((element) => getComputedStyle(element).backgroundColor)
  const lightBackground = await background()
  await page.getByRole("combobox", { name: "外观: 跟随系统" }).click()
  await page.getByRole("option", { name: "深色", exact: true }).click()
  await expect.poll(background).not.toBe(lightBackground)
  const darkBackground = await background()

  await page.reload()
  await expect(page.getByRole("combobox", { name: "外观: 深色" })).toBeVisible()
  await expect.poll(background).toBe(darkBackground)

  await page.getByRole("combobox", { name: "外观: 深色" }).click()
  await page.getByRole("option", { name: "跟随系统", exact: true }).click()
  await expect.poll(background).toBe(lightBackground)
  await page.emulateMedia({ colorScheme: "dark" })
  await expect.poll(background).toBe(darkBackground)

  await page.getByRole("combobox", { name: "外观: 跟随系统" }).click()
  await page.getByRole("option", { name: "浅色", exact: true }).click()
  await expect.poll(background).toBe(lightBackground)
})

test("未添加的活动文字跨分类保留，保存前要求处理", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "活动识别" }).click()
  await page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("进程名", { exact: true }).fill("Photoshop.exe")
  await page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("窗口标题关键词", { exact: true }).fill("项目计划")
  await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await expect(page.getByText(/尚未添加的文字/)).toBeVisible()
  await navigation.getByRole("button", { name: /活动识别/ }).click()
  await expect(page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("进程名", { exact: true })).toHaveValue("Photoshop.exe")
  await page.getByRole("button", { name: "保存并应用" }).click()
  await expect(page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("进程名", { exact: true })).toHaveAttribute("aria-invalid", "true")
  await expect(page.getByText("请先处理尚未添加的活动规则文字。")).toBeVisible()
  await page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("进程名", { exact: true }).press("Enter")
  await expect(page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("窗口标题关键词", { exact: true })).toHaveAttribute("aria-invalid", "true")
  await page.getByRole("group", { name: "工作场景规则", exact: true }).getByLabel("窗口标题关键词", { exact: true }).press("Enter")
  const request = page.waitForRequest((item) => item.url().endsWith("/api/profile") && item.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  expect((await request).postDataJSON().activity.work_processes).toEqual(["Photoshop.exe"])
})

test("关闭确认说明修改后果，窄窗口可调整偏好", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.setViewportSize({ width: 900, height: 600 })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("button", { name: "添加层级" }).click()
  await page.getByRole("combobox", { name: "移动天气到", exact: true }).click()
  await page.getByRole("option", { name: "第 1 优先级", exact: true }).click()
  await page.getByRole("button", { name: "关闭" }).click()
  const dialog = page.getByRole("alertdialog", { name: "放弃未保存的修改？" })
  await expect(dialog).toContainText("当前运行设置不会改变，本次修改将丢失。")
  await expect(dialog.getByRole("button", { name: "继续编辑" })).toBeVisible()
  await expect(dialog.getByRole("button", { name: "放弃修改" })).toBeVisible()
})

test("首启自动探测回填的 Wallpaper Engine 路径不算未保存修改", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh")

  // 挂载扫描会自动探测并回填 Wallpaper Engine 路径；播放列表表格可见即回填已发生。
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()

  await page.getByRole("button", { name: "取消" }).click()
  await expect(page.getByRole("alertdialog", { name: "放弃未保存的修改？" })).toHaveCount(0)
})

test("回填后用户再编辑路径，关闭仍需确认", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh")
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()

  await page.getByRole("textbox", { name: "Wallpaper Engine 可执行文件" }).fill("D:\\Other\\wallpaper64.exe")
  await page.getByRole("button", { name: "取消" }).click()
  await expect(page.getByRole("alertdialog", { name: "放弃未保存的修改？" })).toBeVisible()
})

test("计时输入校验、检查页纠错跳转及修正后保存", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "调度风格", exact: true }).click()
  const timing = page.getByRole("button", { name: "自定义防打扰设置", exact: true })
  await timing.click()
  const startup = page.getByRole("spinbutton", { name: "启动等待", exact: true })
  for (const invalid of ["", "1.5", "-1"]) {
    await startup.fill(invalid)
    await expect(startup).toHaveAccessibleDescription("请输入不小于 0 的整数。")
    await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
  }
  await timing.click()
  await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await page.getByRole("alert").getByRole("button", { name: "调度风格", exact: true }).click()
  await expect(startup).toBeVisible()
  await expect(startup).toBeFocused()
  await startup.fill("0")
  expect((await saveSettings(page)).disturbance.startup_grace_seconds).toBe(0)
})
