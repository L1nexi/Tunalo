import { expect, test } from "@playwright/test"
import type { Profile } from "../src/api/profile"
import { mockSetupApi } from "./support/profileApi"

test("清空密钥后失焦显示必填提示，切换页面保留反馈，补全后即时清除", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "天气服务", exact: true }).click()
  const key = page.getByRole("textbox", { name: "OpenWeatherMap API Key", exact: true })
  const required = page.getByText("请先填写 API Key。", { exact: true })
  await key.fill("")
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
  await expect(required).toHaveCount(0)
  await key.press("Tab")
  await expect(key).toHaveAccessibleDescription("请先填写 API Key。")
  await navigation.getByRole("button", { name: "场景绑定", exact: true }).click()
  await navigation.getByRole("button", { name: "天气服务", exact: true }).click()
  await expect(required).toBeVisible()
  await key.fill("another-key")
  await expect(required).toHaveCount(0)
  await expect(key).toHaveAttribute("aria-invalid", "false")
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeEnabled()
})

test("首次空白密钥保持安静，实际编辑并离开后才提示", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "天气服务", exact: true }).click()
  const key = page.getByRole("textbox", { name: "OpenWeatherMap API Key", exact: true })
  const required = page.getByText("请先填写 API Key。", { exact: true })
  await key.focus()
  await key.press("Tab")
  await expect(required).toHaveCount(0)
  await key.fill("temporary-key")
  await key.fill("")
  await expect(required).toHaveCount(0)
  await key.press("Tab")
  await expect(required).toBeVisible()
})

test("天气页测试 Key 时说明代理失败原因", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-key-validations", async (route) => {
    await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "proxy_error" } })
  })
  await page.goto("/?locale=zh&test=1")
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
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(page.getByText("无效的 API Key。", { exact: true })).toBeVisible()
  await expect(page.getByText(/连接天气服务失败/)).toHaveCount(0)
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
  await page.goto("/?locale=zh&test=1")
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
  await page.goto("/?locale=zh&test=1")
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
  await page.goto("/?locale=zh&test=1")
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
