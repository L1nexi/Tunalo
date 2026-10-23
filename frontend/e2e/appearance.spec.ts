import { expect, test, type Page } from "@playwright/test"
import { mockSetupApi } from "./support/profileApi"
import { mockPywebview, type Theme } from "./support/pywebview"

async function chooseTheme(page: Page, label: string) {
  await page.getByRole("combobox", { name: /^外观:/ }).click()
  await page.getByRole("option", { name: label, exact: true }).click()
}

function colorScheme(page: Page): Promise<string> {
  return page.locator("html").evaluate((element) => getComputedStyle(element).colorScheme)
}

test("原生外观独立保存，重开后保留选择，跟随系统不覆盖偏好", async ({ page }) => {
  let stored: Theme = "dark"
  const writes: Theme[] = []
  await mockPywebview(page, async () => stored, async (theme) => { stored = theme; writes.push(theme) })
  await mockSetupApi(page, true)
  await page.emulateMedia({ colorScheme: "light" })
  await page.goto("/?locale=zh")
  await expect.poll(() => colorScheme(page)).toBe("dark")
  await expect(page.getByRole("combobox", { name: "外观: 深色" })).toBeVisible()
  expect(writes).toEqual([])
  await chooseTheme(page, "浅色")
  await expect.poll(() => stored).toBe("light")
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
  await page.reload()
  await expect(page.getByRole("combobox", { name: "外观: 浅色" })).toBeVisible()
  await chooseTheme(page, "跟随系统")
  await expect.poll(() => stored).toBe("auto")
  await page.emulateMedia({ colorScheme: "dark" })
  await expect.poll(() => colorScheme(page)).toBe("dark")
  await page.reload()
  await expect(page.getByRole("combobox", { name: "外观: 跟随系统" })).toBeVisible()
  await page.emulateMedia({ colorScheme: "light" })
  await expect.poll(() => colorScheme(page)).toBe("light")
  expect(writes).toEqual(["light", "auto"])
})

test("关闭等待期间继续切换外观，也会保存最后选择再退出", async ({ page }) => {
  let releaseDark!: () => void
  let releaseLight!: () => void
  const darkSaving = new Promise<void>((resolve) => { releaseDark = resolve })
  const lightSaving = new Promise<void>((resolve) => { releaseLight = resolve })
  const started: Theme[] = []
  const events: string[] = []
  await mockPywebview(page, async () => "auto", async (theme) => {
    started.push(theme)
    await (theme === "dark" ? darkSaving : lightSaving)
    events.push(`saved:${theme}`)
  }, () => { events.push("closed") })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await chooseTheme(page, "深色")
  await expect.poll(() => started).toEqual(["dark"])
  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  await chooseTheme(page, "浅色")
  expect(events).toEqual([])
  expect(started).toEqual(["dark"])
  releaseDark()
  await expect.poll(() => started).toEqual(["dark", "light"])
  expect(events).toEqual(["saved:dark"])
  releaseLight()
  await expect.poll(() => events).toEqual(["saved:dark", "saved:light", "closed"])
})

test("外观读写失败有提示，仍可重新选择并保存", async ({ page }) => {
  let attempts = 0
  const saved: Theme[] = []
  await mockPywebview(page, async () => { throw new Error("read failed") }, async (theme) => {
    attempts++
    if (attempts === 1) throw new Error("write failed")
    saved.push(theme)
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await expect(page.getByText("无法读取外观偏好，暂用系统外观。", { exact: true })).toBeVisible()
  await chooseTheme(page, "深色")
  await expect(page.getByText("外观偏好未能保存，请重试。", { exact: true })).toBeVisible()
  await chooseTheme(page, "浅色")
  await expect.poll(() => saved).toEqual(["light"])
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
})

test("桥接稍后就绪时仍从原生偏好回填外观", async ({ page }) => {
  const saved: Theme[] = []
  await mockPywebview(page, async () => "dark", async (theme) => { saved.push(theme) }, () => {}, true)
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.evaluate(() => window.dispatchEvent(new Event("test:bridge-ready")))
  await expect(page.getByRole("combobox", { name: "外观: 深色" })).toBeVisible()
  await expect.poll(() => colorScheme(page)).toBe("dark")
  expect(saved).toEqual([])
})

test("放弃 Profile 草稿仍等待外观保存，保留编辑时不关闭窗口", async ({ page }) => {
  let releaseSave!: () => void
  const saving = new Promise<void>((resolve) => { releaseSave = resolve })
  let closed = false
  let stored: Theme = "auto"
  await mockPywebview(page, async () => stored, async (theme) => {
    await saving
    stored = theme
  }, () => { closed = true })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("textbox", { name: "Wallpaper Engine 可执行文件" }).fill("D:\\Other\\wallpaper64.exe")
  await chooseTheme(page, "深色")
  await page.getByRole("button", { name: "关闭", exact: true }).click()
  const dialog = page.getByRole("alertdialog", { name: "放弃未保存的修改？" })
  await dialog.getByRole("button", { name: "继续编辑" }).click()
  expect(closed).toBe(false)
  await page.getByRole("button", { name: "关闭", exact: true }).click()
  await dialog.getByRole("button", { name: "放弃修改" }).click()
  expect(closed).toBe(false)
  releaseSave()
  await expect.poll(() => closed).toBe(true)
  expect(stored).toBe("dark")
  await page.reload()
  await expect(page.getByRole("textbox", { name: "Wallpaper Engine 可执行文件" })).toHaveValue("C:\\Wallpaper Engine\\wallpaper64.exe")
  await expect(page.getByRole("combobox", { name: "外观: 深色" })).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
})
