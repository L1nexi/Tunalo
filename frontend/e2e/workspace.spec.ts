import { expect, test } from "@playwright/test"
import { mockSetupApi } from "./support/profileApi"

for (const scenario of [
  {
    mode: "首次设置", hasProfile: false,
    editorButtons: ["取消", "查看配置草稿"],
    reviewButtons: ["返回设置", "完成设置"],
    applicationButtons: ["取消", "查看配置草稿"],
    englishEditorButtons: ["Cancel", "Review and finish"],
    englishReviewButtons: ["Back to settings", "Finish setup"],
    englishApplicationButtons: ["Cancel", "Review and finish"],
    englishReviewTitle: "Review and finish",
    englishSubmit: "Finish setup",
  },
  {
    mode: "设置", hasProfile: true,
    editorButtons: ["关闭", "查看配置草稿", "保存并应用"],
    reviewButtons: ["返回设置", "保存并应用"],
    applicationButtons: ["关闭"],
    englishEditorButtons: ["Close", "Review and save", "Save and apply"],
    englishReviewButtons: ["Back to settings", "Save and apply"],
    englishApplicationButtons: ["Close"],
    englishReviewTitle: "Review and save",
    englishSubmit: "Save and apply",
  },
] as const) {
  test(`${scenario.mode}中三类页面的底栏动作随语言切换更新`, async ({ page }) => {
    await mockSetupApi(page, scenario.hasProfile)
    await page.goto("/?locale=zh&test=1")
    await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()
    const navigation = page.getByRole("navigation")
    const footer = page.locator("footer")
    await expect(footer.getByRole("button")).toHaveText([...scenario.editorButtons])

    await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
    await expect(footer.getByRole("button")).toHaveText([...scenario.reviewButtons])
    await expect(footer.getByRole("button", { name: scenario.hasProfile ? "保存并应用" : "完成设置", exact: true })).toBeDisabled()

    await navigation.getByRole("button", { name: "应用设置", exact: true }).click()
    await expect(footer.getByRole("button")).toHaveText([...scenario.applicationButtons])
    await expect(navigation.getByRole("button", { name: "应用设置", exact: true })).not.toHaveAttribute("aria-describedby")
    await page.getByRole("group", { name: "语言", exact: true }).getByRole("button", { name: "English", exact: true }).click()
    await expect(page.getByRole("heading", { name: "Application settings", exact: true })).toBeVisible()
    await expect(page.getByText("Changes on this page take effect immediately.", { exact: true })).toBeVisible()
    await expect(navigation.getByRole("button").first()).toHaveAccessibleName("Application settings")
    await expect(footer.getByRole("button")).toHaveText([...scenario.englishApplicationButtons])

    await navigation.getByRole("button", { name: "Wallpaper Engine", exact: true }).click()
    await expect(page.getByRole("heading", { name: "Connect Wallpaper Engine", exact: true })).toBeFocused()
    await expect(footer.getByRole("button")).toHaveText([...scenario.englishEditorButtons])
    await footer.getByRole("button", { name: scenario.englishReviewTitle, exact: true }).click()
    await expect(page.getByRole("heading", { name: scenario.englishReviewTitle, exact: true })).toBeFocused()
    await expect(footer.getByRole("button")).toHaveText([...scenario.englishReviewButtons])
    const submitButton = footer.getByRole("button", { name: scenario.englishSubmit, exact: true })
    if (scenario.hasProfile) await expect(submitButton).toBeEnabled()
    else await expect(submitButton).toBeDisabled()
    await footer.getByRole("button", { name: "Back to settings", exact: true }).click()
    await expect(page.getByRole("heading", { name: "Connect Wallpaper Engine", exact: true })).toBeFocused()
  })
}

test("语言切换与主题选择可保留并跟随系统", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.emulateMedia({ colorScheme: "light" })
  await page.goto("/?locale=zh&test=1")

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

test("关闭确认说明修改后果，窄窗口可调整偏好", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.setViewportSize({ width: 900, height: 600 })
  await page.goto("/?locale=zh&test=1")
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

test("切换设置项时显示新页面顶部", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 650 })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
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

test("首启自动探测回填的 Wallpaper Engine 路径不算未保存修改", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")

  // 挂载扫描会自动探测并回填 Wallpaper Engine 路径；播放列表表格可见即回填已发生。
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()

  await page.getByRole("button", { name: "取消" }).click()
  await expect(page.getByRole("alertdialog", { name: "放弃未保存的修改？" })).toHaveCount(0)
})

test("回填后用户再编辑路径，关闭仍需确认", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()

  await page.getByRole("textbox", { name: "Wallpaper Engine 可执行文件" }).fill("D:\\Other\\wallpaper64.exe")
  await page.getByRole("button", { name: "取消" }).click()
  await expect(page.getByRole("alertdialog", { name: "放弃未保存的修改？" })).toBeVisible()
})
