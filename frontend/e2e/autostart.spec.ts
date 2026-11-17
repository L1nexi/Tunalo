import { expect, test, type Page } from "@playwright/test"
import { mockSetupApi, profile } from "./support/profileApi"
import { mockPywebview } from "./support/pywebview"

async function openApplication(page: Page, locale: "zh" | "en" = "zh"): Promise<void> {
  await page.getByRole("navigation").getByRole("button", {
    name: locale === "zh" ? "应用设置" : "Application settings", exact: true,
  }).click()
}

test("开机启动独立即时保存，重开后回填并可关闭", async ({ page }, testInfo) => {
  let stored = false
  const profileWrites: string[] = []
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/profile" && request.method() !== "GET") profileWrites.push(request.method())
  })
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => stored,
    set: async (enabled) => { stored = enabled },
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await expect(page.getByRole("navigation").getByRole("button").first()).toHaveAccessibleName("应用设置")
  await openApplication(page)

  await expect(page.getByRole("heading", { name: "应用设置", exact: true })).toBeFocused()
  await expect(page.locator("footer").getByRole("button")).toHaveText(["关闭"])
  const toggle = page.getByRole("switch", { name: "开机启动", exact: true })
  await expect(toggle).toHaveAccessibleDescription("登录 Windows 时静默启动。")
  await toggle.click()
  await expect.poll(() => stored).toBe(true)
  await expect(toggle).toBeChecked()
  await page.screenshot({ path: testInfo.outputPath("application-settings.png") })

  await page.reload()
  await openApplication(page)
  await expect(toggle).toBeChecked()
  await toggle.click()
  await expect.poll(() => stored).toBe(false)
  expect(profileWrites).toEqual([])
})

test("首次设置也能打开应用设置页，开关与设置模式一致", async ({ page }, testInfo) => {
  let stored = false
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => stored,
    set: async (enabled) => { stored = enabled },
  })
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")
  await expect(page.getByRole("heading", { name: "连接 Wallpaper Engine" })).toBeVisible()

  const navigation = page.getByRole("navigation", { name: "设置项" })
  await expect(navigation.getByRole("button").first()).toHaveAccessibleName("应用设置")
  await openApplication(page)
  await expect(page.getByRole("heading", { name: "应用设置", exact: true })).toBeFocused()
  await expect(page.locator("footer").getByRole("button")).toHaveText(["取消", "查看配置草稿"])

  const toggle = page.getByRole("switch", { name: "开机启动", exact: true })
  await expect(toggle).toHaveAccessibleDescription("登录 Windows 时静默启动。")
  await toggle.click()
  await expect.poll(() => stored).toBe(true)
  await expect(toggle).toBeChecked()
  await page.waitForTimeout(200)
  await page.screenshot({ path: testInfo.outputPath("setup-application-settings.png") })

  await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await expect(page.getByRole("heading", { name: "查看配置草稿", exact: true })).toBeVisible()
})

test("从应用设置进入配置检查后，返回到实际来源页面", async ({ page }) => {
  await mockPywebview(page, async () => "auto", async () => {})
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "调度风格", exact: true }).click()
  await openApplication(page)
  await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await page.getByRole("button", { name: "返回设置", exact: true }).click()

  await expect(page.getByRole("heading", { name: "应用设置", exact: true })).toBeFocused()
  await expect(navigation.getByRole("button", { name: "应用设置", exact: true })).toHaveAttribute("aria-current", "page")
  await expect(navigation.locator('[aria-current="page"]')).toHaveCount(1)
  await expect(page.getByRole("switch", { name: "开机启动", exact: true })).toBeVisible()
  await expect(page.locator("footer").getByRole("button")).toHaveText(["关闭"])
})

test("浏览器环境显示桌面窗口说明，开关不可操作", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeDisabled()
  await expect(page.getByText("请在 Tunalo 桌面窗口中修改此设置。", { exact: true })).toBeVisible()
})

test("原生桥接延迟就绪后读取开机启动状态", async ({ page }) => {
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, true, {
    get: async () => true, set: async () => {},
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeDisabled()
  await page.evaluate(() => window.dispatchEvent(new Event("test:bridge-ready")))
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeChecked()
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeEnabled()
})

test("读取期间禁用开关，完成后回填原生状态", async ({ page }) => {
  let finishRead!: (value: boolean) => void
  const reading = new Promise<boolean>((resolve) => { finishRead = resolve })
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => reading, set: async () => {},
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeDisabled()
  await expect(page.getByRole("status", { exact: false }).filter({ hasText: "正在读取开机启动设置…" })).toBeVisible()
  finishRead(true)
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeChecked()
})

test("读取失败后可以重试，不会把未知状态当成已关闭", async ({ page }) => {
  let attempts = 0
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => {
      if (++attempts === 1) throw new Error("read denied")
      return true
    },
    set: async () => {},
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  const error = page.getByRole("alert").filter({ hasText: "无法读取开机启动设置，请重试。" })
  await expect(error).toBeVisible()
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeDisabled()
  await error.getByRole("button", { name: "重试" }).click()
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeChecked()
  await expect(error).toHaveCount(0)
})

test("写入失败保留原状态，返回应用设置后仍能重试失败的选择", async ({ page }) => {
  let stored = false
  let attempts = 0
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => stored,
    set: async (enabled) => {
      if (++attempts === 1) throw new Error("write denied")
      stored = enabled
    },
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  const toggle = page.getByRole("switch", { name: "开机启动" })
  await toggle.click()
  await expect(page.getByRole("alert")).toContainText("开机启动设置未能保存，请重试。")
  await expect(toggle).not.toBeChecked()
  await page.getByRole("navigation").getByRole("button", { name: "Wallpaper Engine", exact: true }).click()
  await openApplication(page)
  await page.getByRole("alert").getByRole("button", { name: "重试" }).click()
  await expect.poll(() => stored).toBe(true)
  await expect(toggle).toBeChecked()
  await expect(page.getByRole("alert")).toHaveCount(0)
})

test("写入期间切换页面仍保留保存状态，不重复写入", async ({ page }) => {
  let finishSave!: () => void
  const saving = new Promise<void>((resolve) => { finishSave = resolve })
  let stored = false
  let writes = 0
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => stored,
    set: async (enabled) => { writes++; await saving; stored = enabled },
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await openApplication(page)
  const toggle = page.getByRole("switch", { name: "开机启动" })
  await toggle.click()
  await expect(toggle).toBeDisabled()
  await page.getByRole("navigation").getByRole("button", { name: "Wallpaper Engine", exact: true }).click()
  await openApplication(page)
  await expect(toggle).toBeDisabled()
  finishSave()
  await expect(toggle).toBeChecked()
  expect(writes).toBe(1)
})

test("切换应用设置保留草稿，放弃草稿仍保留开机启动选择", async ({ page }) => {
  let stored = false
  let closed = false
  await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true }, false, {
    get: async () => stored, set: async (enabled) => { stored = enabled },
  })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  const path = page.getByRole("textbox", { name: "Wallpaper Engine 可执行文件" })
  await path.fill("D:\\Other\\wallpaper64.exe")
  await openApplication(page)
  await page.getByRole("switch", { name: "开机启动" }).click()
  await expect.poll(() => stored).toBe(true)
  await page.getByRole("navigation").getByRole("button", { name: "Wallpaper Engine", exact: true }).click()
  await expect(path).toHaveValue("D:\\Other\\wallpaper64.exe")
  await openApplication(page)
  await page.getByRole("button", { name: "关闭", exact: true }).click()
  const dialog = page.getByRole("alertdialog", { name: "放弃未保存的修改？" })
  await dialog.getByRole("button", { name: "继续编辑" }).click()
  expect(closed).toBe(false)
  await page.getByRole("button", { name: "关闭", exact: true }).click()
  await dialog.getByRole("button", { name: "放弃修改" }).click()
  await expect.poll(() => closed).toBe(true)
  await page.reload()
  await expect(path).toHaveValue(profile.wallpaper_engine_path)
  await openApplication(page)
  await expect(page.getByRole("switch", { name: "开机启动" })).toBeChecked()
})

for (const closeMethod of ["button", "native"] as const) {
  test(`${closeMethod} 关闭等待启动项写入完成`, async ({ page }) => {
    let finishSave!: () => void
    const saving = new Promise<void>((resolve) => { finishSave = resolve })
    const events: string[] = []
    await mockPywebview(page, async () => "auto", async () => {}, () => { events.push("closed") }, false, {
      get: async () => false,
      set: async () => { await saving; events.push("saved") },
    })
    await mockSetupApi(page, true)
    await page.goto("/?locale=zh&test=1")
    await openApplication(page)
    await page.getByRole("switch", { name: "开机启动" }).click()
    await expect(page.getByRole("switch", { name: "开机启动" })).toBeDisabled()
    if (closeMethod === "button") await page.getByRole("button", { name: "关闭", exact: true }).click()
    else await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
    expect(events).toEqual([])
    finishSave()
    await expect.poll(() => events).toEqual(["saved", "closed"])
  })
}

for (const first of ["appearance", "autostart"] as const) {
  test(`关闭等待 ${first} 时修改另一项偏好，也会等待两项保存`, async ({ page }) => {
    let finishTheme!: () => void
    let finishAutostart!: () => void
    const themeSaving = new Promise<void>((resolve) => { finishTheme = resolve })
    const startupSaving = new Promise<void>((resolve) => { finishAutostart = resolve })
    const started: string[] = []
    const events: string[] = []
    await mockPywebview(page, async () => "auto", async () => {
      started.push("appearance"); await themeSaving; events.push("appearance")
    }, () => { events.push("closed") }, false, {
      get: async () => false,
      set: async () => { started.push("autostart"); await startupSaving; events.push("autostart") },
    })
    await mockSetupApi(page, true)
    await page.goto("/?locale=zh")
    await openApplication(page)
    const changeTheme = async () => {
      await page.getByRole("combobox", { name: /^外观:/ }).click()
      await page.getByRole("option", { name: "深色", exact: true }).click()
    }
    const changeStartup = async () => { await page.getByRole("switch", { name: "开机启动" }).click() }
    await (first === "appearance" ? changeTheme() : changeStartup())
    await expect.poll(() => started).toContain(first)
    await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
    await (first === "appearance" ? changeStartup() : changeTheme())
    await expect.poll(() => started).toHaveLength(2)
    if (first === "appearance") finishTheme()
    else finishAutostart()
    await expect.poll(() => events).toEqual([first])
    if (first === "appearance") finishAutostart()
    else finishTheme()
    await expect.poll(() => events).toHaveLength(3)
    expect(events.at(-1)).toBe("closed")
  })
}

test("320px 英文深色页面无横向溢出，键盘可以切换开关", async ({ page }, testInfo) => {
  let stored = false
  await page.setViewportSize({ width: 320, height: 720 })
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" })
  await mockPywebview(page, async () => "auto", async () => {}, () => {}, false, {
    get: async () => stored, set: async (enabled) => { stored = enabled },
  })
  await mockSetupApi(page, true, { ...profile, language: "en" })
  await page.goto("/?locale=en&test=1")
  await openApplication(page, "en")
  const toggle = page.getByRole("switch", { name: "Launch at sign-in" })
  await expect(toggle).toBeEnabled()
  await toggle.focus()
  await toggle.press("Space")
  await expect.poll(() => stored).toBe(true)
  await expect(toggle).toBeChecked()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: testInfo.outputPath("application-settings-narrow-dark.png") })
})
