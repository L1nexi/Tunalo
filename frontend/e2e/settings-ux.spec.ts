import { expect, test } from "@playwright/test"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"

test("直接用键盘创建优先级，移动后保留焦点并保存顺序", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "调度风格", exact: true }).click()
  await expect(page.getByText("不设置优先级时，Tunalo 会综合当前情境选择合适的场景。", { exact: true })).toBeVisible()

  const menu = page.getByRole("combobox", { name: "移动天气到", exact: true })
  await menu.focus()
  await menu.press("Enter")
  await page.getByRole("option", { name: "移到新优先级", exact: true }).press("Enter")
  await expect(page.getByRole("group", { name: "第 1 优先级", exact: true }).getByRole("button", { name: "拖动天气", exact: true })).toBeVisible()
  await expect(menu).toBeFocused()

  expect((await saveSettings(page)).matching.preference_tiers).toEqual([["weather"]])
})

test("中文输入法确认文字不会提前添加规则，移除后焦点回到输入框", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "活动识别", exact: true }).click()
  const group = page.getByRole("group", { name: "工作场景规则", exact: true })
  const input = group.getByRole("textbox", { name: "窗口标题关键词", exact: true })
  await input.fill("项目计划")
  await input.dispatchEvent("keydown", { key: "Enter", code: "Enter", isComposing: true })
  await expect(input).toHaveValue("项目计划")
  await expect(page.getByRole("button", { name: "移除: 项目计划", exact: true })).toHaveCount(0)
  await input.press("Enter")
  await expect(input).toBeEmpty()
  await group.getByText("项目计划", { exact: true }).click()
  const remove = group.getByRole("button", { name: "移除: 项目计划", exact: true })
  await expect(remove).toBeVisible()
  await remove.click()
  await expect(input).toBeFocused()
  await expect(remove).toHaveCount(0)
})

test("切换设置项时显示新页面顶部", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 650 })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "活动识别", exact: true }).click()
  await page.getByRole("button", { name: "规则如何匹配", exact: true }).click()
  const example = page.getByText(/例如，浏览器可归入工作/)
  await example.scrollIntoViewIfNeeded()
  await expect(example).toBeInViewport()
  await navigation.getByRole("button", { name: "场景绑定", exact: true }).click()
  await expect(page.getByRole("heading", { name: "管理使用场景", exact: true })).toBeInViewport()
  const addPresets = page.getByRole("button", { name: "从预设添加", exact: true })
  await expect(addPresets).toBeInViewport()

})

test("320px 英文浅色窗口可调整偏好并导入应用组", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 320, height: 720 })
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" })
  await mockSetupApi(page, true, {
    ...profile, language: "en",
    matching: { preference_tiers: [["weather"], ["activity", "time"], ["season"]] },
    activity: { ...profile.activity!, leisure_title_keywords: ["超长窗口标题测试".repeat(15)] },
  })
  await page.goto("/?locale=en")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "Scheduling feel", exact: true }).click()
  await page.getByRole("combobox", { name: "Move Weather to", exact: true }).click()
  const destination = page.getByRole("option", { name: "Priority 2", exact: true })
  await expect(destination).toBeInViewport()
  await destination.click()
  await navigation.getByRole("button", { name: "Activity detection", exact: true }).click()
  await page.getByRole("button", { name: "Import app groups", exact: true }).click()
  await page.getByRole("region", { name: "Office tools", exact: true }).getByRole("button", { name: "Import into work", exact: true }).click()
  await page.screenshot({ path: testInfo.outputPath("activity-narrow.png") })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  const save = page.getByRole("button", { name: "Save and apply", exact: true })
  await save.scrollIntoViewIfNeeded()
  await expect(save).toBeInViewport()
  const saved = await saveSettings(page, "en")
  expect(saved.matching.preference_tiers.map((tier) => new Set(tier))).toEqual([new Set(["activity", "time", "weather"]), new Set(["season"])])
  expect(saved.activity?.work_processes).toContain("winword")
})
