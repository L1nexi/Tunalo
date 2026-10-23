import { expect, test } from "@playwright/test"
import type { Page } from "@playwright/test"
import type { Profile } from "../src/api/profile"
import { mockSetupApi, profile, addPreset } from "./support/profileApi"

async function openSection(page: Page, name: string): Promise<void> {
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name }).click()
}

test("首次设置允许自由选择分类，并在检查页指出未完成设置", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")

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
  await page.goto("/?locale=zh&test=1")
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

test("首次设置提交第 3 版配置与空偏好、空活动规则", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()
  await openSection(page, "天气服务")
  await page.getByRole("textbox", { name: "OpenWeatherMap API Key", exact: true }).fill("test-key")
  await page.getByRole("spinbutton", { name: "纬度", exact: true }).fill("31")
  await page.getByRole("spinbutton", { name: "经度", exact: true }).fill("121")
  await openSection(page, "场景绑定")
  await addPreset(page, "时间与活动", "日间工作")
  await page.getByRole("button", { name: "日间工作: 播放列表", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await openSection(page, "查看配置草稿")
  const response = page.waitForResponse((item) => new URL(item.url()).pathname === "/api/profile" && item.request().method() === "POST")
  await page.getByRole("button", { name: "完成设置", exact: true }).click()
  const saved = (await response).request().postDataJSON()
  expect(saved.version).toBe(3)
  expect(saved.matching).toEqual({ preference_tiers: [] })
  expect(saved.activity).toEqual({ work_processes: [], leisure_processes: [], work_title_keywords: [], leisure_title_keywords: [] })
})
