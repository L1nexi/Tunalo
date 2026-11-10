import { expect, test } from "@playwright/test"
import type { Profile } from "../src/api/profile"
import { mockSetupApi } from "./support/profileApi"

test("填写坐标即可测试天气，零度坐标也有效", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ json: { status: "valid" } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "天气服务", exact: true }).click()
  const testConnection = page.getByRole("button", { name: "测试连接", exact: true })
  await expect(testConnection).toBeDisabled()
  await expect(page.getByRole("button", { name: "天气数据来自 Open-Meteo", exact: true })).toBeVisible()
  await expect(page.getByLabel(/API Key/i)).toHaveCount(0)
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("0")
  await expect(testConnection).toBeDisabled()
  await page.getByRole("spinbutton", { name: "经度", exact: true }).fill("0")
  const tested = page.waitForRequest("**/api/weather-validations")
  await testConnection.click()
  expect((await tested).postDataJSON()).toEqual({ latitude: 0, longitude: 0 })
  await expect(page.getByRole("status").getByText("天气连接正常")).toBeVisible()
})

test("天气页测试连接时说明代理失败原因", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "proxy_error" } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "测试连接" }).click()
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.getByText("当前坐标尚未测试连接")).toBeVisible()
  await expect(statusBlock.getByText(/连接天气服务失败/)).toBeVisible()
  await expect(page.getByText(/代理连接失败/)).toBeVisible()
})

test("天气服务拒绝坐标时说明地点错误", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ status: 422, json: { error: "weather_validation_failed", issues: [{ path: ["weather", "location"], code: "weather_location_invalid", message: "weather_location_invalid" }] } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(page.getByText("Open-Meteo 无法使用这个地点，请检查经纬度。", { exact: true })).toBeVisible()
  await expect(page.getByText(/连接天气服务失败/)).toHaveCount(0)
})

test("已验证的当前坐标可直接保存，后续网络故障保留通过记录", async ({ page }) => {
  await mockSetupApi(page, true)
  let attempts = 0
  await page.route("**/api/weather-validations", async (route) => {
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
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("32")
  const tested = page.waitForRequest((request) => new URL(request.url()).pathname === "/api/weather-validations" && request.method() === "POST")
  await page.getByRole("button", { name: "测试连接" }).click()
  expect((await tested).postDataJSON()).toEqual({ latitude: 32, longitude: 121.4737 })
  const statusBlock = page.getByRole("status")
  await expect(statusBlock.getByText("天气连接正常")).toBeVisible()
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(statusBlock.getByText("天气连接正常")).toBeVisible()
  await expect(statusBlock.getByText(/连接天气服务失败/)).toBeVisible()
  await expect(statusBlock.getByText(/连接超时/)).toBeVisible()

  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  const saveRequest = page.waitForRequest((request) => request.url().includes("allow_unverified_weather=1") && request.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用" }).click()
  expect((await saveRequest).postDataJSON().weather).toEqual({ location: { latitude: 32, longitude: 121.4737 } })
  await expect(page.getByText("已保存并生效")).toBeVisible()
})

test("修改坐标后需要重新验证，保存时检查新坐标", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ json: { status: "valid" } })
  })
  await page.goto("/?locale=zh&test=1")
  const navigation = page.getByRole("navigation", { name: "设置项" })
  await navigation.getByRole("button", { name: "天气服务", exact: true }).click()
  await page.getByRole("button", { name: "测试连接", exact: true }).click()
  await expect(page.getByText("天气连接正常", { exact: true })).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("33")
  await expect(page.getByText("天气连接正常", { exact: true })).toHaveCount(0)
  await expect(page.getByText(/^验证时间：/)).toHaveCount(0)
  await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
  const saving = page.waitForRequest((request) => request.method() === "PUT")
  await page.getByRole("button", { name: "保存并应用", exact: true }).click()
  const saved = await saving
  expect(new URL(saved.url()).search).toBe("")
  expect(saved.postDataJSON().weather.location.latitude).toBe(33)
  await expect(page.getByText("已保存并生效")).toBeVisible()
})

for (const outcome of ["成功", "失败"] as const) {
  test(`旧坐标的测试${outcome}迟到时保持新坐标未验证`, async ({ page }) => {
    await mockSetupApi(page, true)
    let release: () => void = () => {}
    const pending = new Promise<void>((resolve) => { release = resolve })
    await page.route("**/api/weather-validations", async (route) => {
      await pending
      await route.fulfill(outcome === "成功"
        ? { json: { status: "valid" } }
        : { status: 503, json: { error: "weather_validation_unavailable", reason: "timeout" } })
    })
    await page.goto("/?locale=zh&test=1")
    const navigation = page.getByRole("navigation", { name: "设置项" })
    await navigation.getByRole("button", { name: "天气服务", exact: true }).click()
    const testing = page.waitForRequest("**/api/weather-validations")
    await page.getByRole("button", { name: "测试连接", exact: true }).click()
    await testing
    await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("34")
    release()
    await expect(page.getByRole("button", { name: "测试连接", exact: true })).toBeEnabled()
    await expect(page.getByText("天气连接正常", { exact: true })).toHaveCount(0)
    await expect(page.getByText(/连接超时/)).toHaveCount(0)
    await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
    await page.getByText("查看当前草稿全部设置").click()
    await expect(page.getByText("当前坐标尚未手动测试连接", { exact: true })).toBeVisible()
    const saving = page.waitForRequest((request) => request.method() === "PUT")
    await page.getByRole("button", { name: "保存并应用", exact: true }).click()
    expect(new URL((await saving).url()).search).toBe("")
    await expect(page.getByText("已保存并生效")).toBeVisible()
  })
}

test("请求配额耗尽时可确认保存，并在坐标变更后清除旧错误", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ status: 422, json: {
      error: "weather_validation_failed",
      issues: [{ path: ["weather"], code: "weather_api_quota_exceeded", message: "weather_api_quota_exceeded" }],
    } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "天气服务", exact: true }).click()
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("32")
  await page.getByRole("button", { name: "测试连接", exact: true }).click()
  await expect(page.getByText("天气服务的请求额度已用完，请稍后重试。", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "保存并应用", exact: true }).click()
  const confirmation = page.getByRole("alertdialog", { name: "天气连接测试未通过，仍要保存吗？" })
  await expect(confirmation).toBeVisible()
  await confirmation.getByRole("button", { name: "保存并应用", exact: true }).click()
  await expect(page.getByText("已保存并生效")).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("33")
  await expect(page.getByText("天气服务的请求额度已用完，请稍后重试。", { exact: true })).toHaveCount(0)
})

test("天气服务暂不可用时可确认保存当前草稿", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/weather-validations", async (route) => {
    await route.fulfill({ status: 503, json: { error: "weather_validation_unavailable", reason: "timeout" } })
  })
  await page.route("**/api/profile?allow_unverified_weather=1", async (route) => {
    const updated = route.request().postDataJSON() as Profile
    await route.fulfill({ json: { status: "applied", profile: updated } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("32")
  await page.getByRole("button", { name: "测试连接" }).click()
  await expect(page.getByText(/连接超时/)).toBeVisible()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  await page.getByRole("button", { name: "保存并应用" }).click()
  const confirmation = page.getByRole("alertdialog", { name: "天气连接测试未通过，仍要保存吗？" })
  await expect(confirmation).toBeVisible()
  const saveRequest = page.waitForRequest((request) => request.url().includes("allow_unverified_weather=1") && request.method() === "PUT")
  await confirmation.getByRole("button", { name: "保存并应用" }).click()
  expect((await saveRequest).postDataJSON().weather).toEqual({ location: { latitude: 32, longitude: 121.4737 } })
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
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("32")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "查看配置草稿" }).click()
  await page.getByRole("button", { name: "保存并应用" }).click()
  const confirmation = page.getByRole("alertdialog", { name: "天气连接测试未通过，仍要保存吗？" })
  await expect(confirmation).toBeVisible()
  await expect(confirmation).toContainText("连接超时")
  await confirmation.getByRole("button", { name: "保存并应用" }).click()
  await expect(page.getByText("已保存并生效")).toBeVisible()
})
