import { expect, test } from "@playwright/test"
import { mockSetupApi, profile } from "./support/profileApi"

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

  const saved = page.waitForRequest((request) => request.method() === "PUT" && new URL(request.url()).pathname === "/api/profile")
  await page.getByRole("button", { name: "保存并应用", exact: true }).click()
  expect((await saved).postDataJSON().matching.preference_tiers).toEqual([["weather"]])
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

test("切换设置项从顶部开始，黄昏属于时段分组", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 650 })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "活动识别", exact: true }).click()
  await page.getByRole("button", { name: "规则如何匹配", exact: true }).click()
  await page.getByText(/例如，浏览器可归入工作/).scrollIntoViewIfNeeded()
  expect(await page.locator("#setup-step-content").evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
  await navigation.getByRole("button", { name: "场景绑定", exact: true }).click()
  expect(await page.locator("#setup-step-content").evaluate((element) => element.scrollTop)).toBe(0)
  await page.getByRole("button", { name: /时段氛围/ }).click()
  await expect(page.getByRole("checkbox", { name: "黄昏", exact: true })).toBeHidden()
  await expect(page.getByRole("checkbox", { name: "雨天", exact: true })).toBeVisible()
  await page.getByRole("button", { name: /时段氛围/ }).click()
  await expect(page.getByRole("checkbox", { name: "黄昏", exact: true })).toBeVisible()
})

for (const viewport of [
  { width: 1280, height: 900, locale: "zh", theme: "light" },
  { width: 900, height: 650, locale: "zh", theme: "dark" },
  { width: 375, height: 812, locale: "zh", theme: "light" },
  { width: 375, height: 812, locale: "en", theme: "dark" },
  { width: 320, height: 720, locale: "en", theme: "light" },
] as const) {
  test(`设置在 ${viewport.width}px ${viewport.locale} ${viewport.theme} 下可读可操作`, async ({ page }, testInfo) => {
    await page.setViewportSize(viewport)
    await page.emulateMedia({ colorScheme: viewport.theme, reducedMotion: "reduce" })
    await mockSetupApi(page, true, {
      ...profile,
      language: viewport.locale,
      matching: { preference_tiers: [["weather"], ["activity", "time"], ["season"]] },
      activity: { ...profile.activity!, work_processes: ["Photoshop.exe"], leisure_title_keywords: ["超长窗口标题测试".repeat(15)] },
    })
    await page.goto(`/?locale=${viewport.locale}`)
    const navigation = page.getByRole("navigation")
    const zh = viewport.locale === "zh"
    await navigation.getByRole("button", { name: zh ? "调度风格" : "Scheduling feel", exact: true }).click()
    await page.getByRole("combobox", { name: zh ? "移动天气到" : "Move Weather to", exact: true }).click()
    const destination = page.getByRole("option", { name: zh ? "第 2 优先级" : "Priority 2", exact: true })
    await expect(destination).toBeInViewport()
    await destination.click()
    await page.getByRole("combobox", { name: zh ? "移动天气到" : "Move Weather to", exact: true }).click()
    await page.getByRole("option", { name: zh ? "第 1 优先级" : "Priority 1", exact: true }).click()
    await expect(page.getByRole("button", { name: zh ? "保存并应用" : "Save and apply", exact: true })).toBeDisabled()
    await page.getByRole("heading", { level: 1 }).scrollIntoViewIfNeeded()
    await page.screenshot({ path: testInfo.outputPath("preferences.png"), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    await navigation.getByRole("button", { name: zh ? "活动识别" : "Activity detection", exact: true }).click()
    await page.getByRole("button", { name: zh ? "导入应用组" : "Import app groups", exact: true }).click()
    const pack = page.getByRole("region", { name: zh ? "办公工具" : "Office tools", exact: true })
    await pack.getByRole("button", { name: zh ? "导入工作" : "Import into work", exact: true }).click()
    await page.getByRole("button", { name: zh ? "导入应用组" : "Import app groups", exact: true }).click()
    await page.getByRole("heading", { level: 1 }).scrollIntoViewIfNeeded()
    await page.screenshot({ path: testInfo.outputPath("activity.png"), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    const footer = page.locator('[data-slot="card-footer"]')
    expect(await footer.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true)
    const save = page.getByRole("button", { name: zh ? "保存并应用" : "Save and apply", exact: true })
    await expect(save).toBeEnabled()
    await save.click()
    await expect(save).toBeDisabled()
  })
}
