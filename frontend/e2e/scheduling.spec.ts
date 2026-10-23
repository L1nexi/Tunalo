import { expect, test } from "@playwright/test"
import type { Page } from "@playwright/test"
import type { Profile } from "../src/api/profile"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"

async function openSection(page: Page, name: string): Promise<void> {
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name }).click()
}

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

test("仅修改计时仍保留已有偏好和自定义活动规则", async ({ page }) => {
  const configured: Profile = {
    ...profile, matching: { preference_tiers: [["weather", "activity"], ["season"]] },
    activity: { work_processes: ["custom.exe"], leisure_processes: [], work_title_keywords: ["项目计划"], leisure_title_keywords: ["电影"] },
  }
  await mockSetupApi(page, true, configured)
  await page.goto("/?locale=zh")
  await openSection(page, "调度风格")
  await page.getByRole("button", { name: "自定义防打扰设置", exact: true }).click()
  await page.getByRole("spinbutton", { name: "启动等待", exact: true }).fill("30")
  await openSection(page, "查看配置草稿")
  await expect(page.getByText("15 秒 → 30 秒", { exact: true })).toBeVisible()
  const saved = await saveSettings(page)
  expect(saved.matching.preference_tiers.map((tier) => new Set(tier))).toEqual([new Set(["weather", "activity"]), new Set(["season"])])
  expect(saved.activity).toEqual({ work_processes: ["custom.exe"], leisure_processes: [], work_title_keywords: ["项目计划"], leisure_title_keywords: ["电影"] })
  await page.reload()
  await openSection(page, "活动识别")
  await expect(page.getByRole("button", { name: "移除: custom.exe", exact: true })).toBeVisible()
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
