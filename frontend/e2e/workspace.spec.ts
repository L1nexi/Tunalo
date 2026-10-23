import { expect, test } from "@playwright/test"
import { mockSetupApi } from "./support/profileApi"

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
