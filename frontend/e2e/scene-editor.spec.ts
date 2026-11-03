import { expect, test } from "@playwright/test"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"
import { mockPywebview } from "./support/pywebview"

test("仅场景弹窗有修改时，原生关闭先确认并保留草稿", async ({ page }) => {
  let closed = false
  await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "自定义场景", exact: true }).click()
  const editor = page.getByRole("dialog", { name: "自定义场景", exact: true })
  await editor.getByRole("textbox", { name: "场景名称" }).fill("待完成的冬季场景")
  await editor.getByRole("button", { name: "冬季", exact: true }).click()

  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  const confirmation = page.getByRole("alertdialog", { name: "放弃未保存的修改？" })
  await expect(confirmation).toBeVisible()
  expect(closed).toBe(false)
  await confirmation.getByRole("button", { name: "继续编辑", exact: true }).click()
  await expect(editor.getByRole("textbox", { name: "场景名称" })).toHaveValue("待完成的冬季场景")
  await expect(editor.getByRole("button", { name: "冬季", exact: true })).toHaveAttribute("aria-pressed", "true")
  await expect(editor.getByRole("button", { name: "冬季", exact: true })).toBeFocused()

  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  await confirmation.getByRole("button", { name: "放弃修改", exact: true }).click()
  await expect.poll(() => closed).toBe(true)
})

test("编辑场景时 Esc 确认只丢弃弹窗草稿，原生关闭也会保护编辑", async ({ page }) => {
  let closed = false
  await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  const edit = page.getByRole("button", { name: "编辑场景: 日间工作", exact: true })
  await edit.click()
  const editor = page.getByRole("dialog", { name: "编辑场景", exact: true })
  const name = editor.getByRole("textbox", { name: "场景名称" })
  await name.fill("待确认的编辑")
  await page.keyboard.press("Escape")
  const confirmation = page.getByRole("alertdialog", { name: "放弃场景编辑？", exact: true })
  await expect(confirmation).toContainText("本次场景编辑将丢失，其他设置修改会保留。")
  await confirmation.getByRole("button", { name: "继续编辑", exact: true }).click()
  await expect(name).toHaveValue("待确认的编辑")
  await expect(name).toBeFocused()
  await page.keyboard.press("Escape")
  await confirmation.getByRole("button", { name: "放弃修改", exact: true }).click()
  await expect(edit).toBeFocused()
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()

  await edit.click()
  await expect(name).toHaveValue("日间工作")
  await name.fill("另一份编辑")
  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  const windowConfirmation = page.getByRole("alertdialog", { name: "放弃未保存的修改？", exact: true })
  await expect(windowConfirmation).toBeVisible()
  expect(closed).toBe(false)
  await windowConfirmation.getByRole("button", { name: "继续编辑", exact: true }).click()
  await expect(name).toHaveValue("另一份编辑")
  await expect(name).toBeFocused()
  await editor.getByRole("button", { name: "取消", exact: true }).click()
  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  await expect.poll(() => closed).toBe(true)
})

test("主页面与弹窗同时修改时统一确认，放弃场景编辑保留其他设置", async ({ page }) => {
  let closed = false
  await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true })
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  const navigation = page.getByRole("navigation")
  await navigation.getByRole("button", { name: "调度风格", exact: true }).click()
  await page.getByRole("button", { name: "自定义防打扰设置", exact: true }).click()
  await page.getByRole("spinbutton", { name: "启动等待", exact: true }).fill("30")
  await navigation.getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "自定义场景", exact: true }).click()
  const editor = page.getByRole("dialog", { name: "自定义场景", exact: true })
  await editor.getByRole("textbox", { name: "场景名称" }).fill("临时场景")

  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  await expect(page.getByRole("alertdialog")).toHaveCount(1)
  const windowConfirmation = page.getByRole("alertdialog", { name: "放弃未保存的修改？", exact: true })
  await windowConfirmation.getByRole("button", { name: "继续编辑", exact: true }).click()
  expect(closed).toBe(false)
  await expect(editor.getByRole("textbox", { name: "场景名称" })).toHaveValue("临时场景")
  await page.keyboard.press("Escape")
  await page.getByRole("alertdialog", { name: "放弃场景编辑？", exact: true }).getByRole("button", { name: "放弃修改", exact: true }).click()
  await navigation.getByRole("button", { name: "调度风格", exact: true }).click()
  await expect(page.getByRole("spinbutton", { name: "启动等待", exact: true })).toHaveValue("30")
  const saved = await saveSettings(page)
  expect(saved.disturbance.startup_grace_seconds).toBe(30)
  expect(saved.scenes).toEqual(profile.scenes)
})

test("未编辑或还原场景修改后关闭不要求确认", async ({ page }) => {
  let closed = false
  await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true })
  await mockSetupApi(page, true, {
    ...profile,
    scenes: { day_work: { ...profile.scenes.day_work!, associations: { time: ["day", "night"], activity: ["work"] } } },
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  const edit = page.getByRole("button", { name: "编辑场景: 日间工作", exact: true })
  await edit.click()
  await expect(page.getByRole("dialog", { name: "编辑场景", exact: true })).toBeVisible()
  await page.keyboard.press("Escape")
  await expect(edit).toBeFocused()
  await expect(page.getByRole("alertdialog")).toHaveCount(0)

  await edit.click()
  const editor = page.getByRole("dialog", { name: "编辑场景", exact: true })
  const name = editor.getByRole("textbox", { name: "场景名称" })
  await name.fill("临时名称")
  await name.fill("日间工作")
  await editor.getByRole("button", { name: "日间", exact: true }).click()
  await editor.getByRole("button", { name: "日间", exact: true }).click()
  await page.keyboard.press("Escape")
  await expect(edit).toBeFocused()
  await expect(page.getByRole("alertdialog")).toHaveCount(0)
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()

  await edit.click()
  await expect(editor).toBeVisible()
  await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
  await expect.poll(() => closed).toBe(true)
})

for (const change of ["选中预设", "仅选择播单"] as const) {
  test(`预设弹窗${change}后关闭会保护草稿，取消后清除修改状态`, async ({ page }) => {
    let closed = false
    await mockPywebview(page, async () => "auto", async () => {}, () => { closed = true })
    await mockSetupApi(page, true)
    await page.goto("/?locale=zh")
    await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
    await page.getByRole("button", { name: "从预设添加", exact: true }).click()
    const editor = page.getByRole("dialog", { name: "挑选预设场景", exact: true })
    if (change === "选中预设") {
      await editor.getByRole("checkbox", { name: "冬季", exact: true }).check()
    } else {
      await editor.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true }).click()
      await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
      await expect(editor.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true })).toHaveAttribute("aria-expanded", "false")
      await expect(page.getByRole("option", { name: "CASUAL_ANIME", exact: true })).toHaveCount(0)
    }
    await page.keyboard.press("Escape")
    await page.getByRole("alertdialog", { name: "放弃场景编辑？", exact: true }).getByRole("button", { name: "继续编辑", exact: true }).click()
    await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
    const confirmation = page.getByRole("alertdialog", { name: "放弃未保存的修改？", exact: true })
    await expect(confirmation).toBeVisible()
    expect(closed).toBe(false)
    await confirmation.getByRole("button", { name: "继续编辑", exact: true }).click()
    if (change === "选中预设") {
      await expect(editor.getByRole("checkbox", { name: "冬季", exact: true })).toBeChecked()
    } else {
      await expect(editor.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true })).toContainText("CASUAL_ANIME")
    }
    await editor.getByRole("button", { name: "取消", exact: true }).click()
    await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
    await page.evaluate(() => window.dispatchEvent(new CustomEvent("tunalo:native-close-request")))
    await expect.poll(() => closed).toBe(true)
  })
}

test("浏览器关闭时也保护场景弹窗输入", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "自定义场景", exact: true }).click()
  const name = page.getByRole("dialog").getByRole("textbox", { name: "场景名称" })
  await name.fill("关闭前的草稿")
  const dialog = page.waitForEvent("dialog")
  await page.close({ runBeforeUnload: true })
  const confirmation = await dialog
  expect(confirmation.type()).toBe("beforeunload")
  await confirmation.dismiss()
  await expect(name).toHaveValue("关闭前的草稿")
})

test("自定义场景保存同组多选，重开后名称、播单与关联一致", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "自定义场景", exact: true }).click()
  const dialog = page.getByRole("dialog")
  await dialog.getByRole("button", { name: "冬季", exact: true }).click()
  await dialog.getByRole("button", { name: "雨", exact: true }).click()
  await dialog.getByRole("button", { name: "雪", exact: true }).click()
  await expect(dialog.getByRole("textbox", { name: "场景名称" })).toHaveValue("冬季 · 雨或雪")
  await dialog.getByRole("textbox", { name: "场景名称" }).fill("我的冬日雨雪")
  await dialog.getByRole("button", { name: "播放列表", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await dialog.getByRole("button", { name: "稍后选择", exact: true }).click()
  await expect(dialog.getByRole("button", { name: "播放列表", exact: true })).toContainText("稍后逐个选择")
  await dialog.getByRole("button", { name: "添加场景", exact: true }).click()
  await expect(page.getByRole("button", { name: "我的冬日雨雪: 播放列表" })).toContainText("选择播放列表")
  await page.getByRole("button", { name: "我的冬日雨雪: 播放列表" }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  const saved = await saveSettings(page)
  const [id, scene] = Object.entries(saved.scenes).find(([, scene]) => scene.name === "我的冬日雨雪")!
  expect(scene.playlist).toBe("CASUAL_ANIME")
  expect(new Set(scene.associations.weather)).toEqual(new Set(["rain", "snow"]))
  expect(scene.associations.season).toEqual(["winter"])
  expect(saved.scenes.day_work).toEqual(profile.scenes.day_work)
  await page.reload()
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await expect(page.getByRole("button", { name: "我的冬日雨雪: 播放列表", exact: true })).toContainText("CASUAL_ANIME")
  await page.getByRole("button", { name: "编辑场景: 我的冬日雨雪" }).click()
  await dialog.getByRole("button", { name: "工作", exact: true }).click()
  await dialog.getByRole("button", { name: "娱乐", exact: true }).click()
  await dialog.getByRole("button", { name: "完成编辑", exact: true }).click()
  const changed = await saveSettings(page)
  expect(changed.scenes[id]).toEqual({
    name: "我的冬日雨雪",
    playlist: "CASUAL_ANIME",
    associations: {
      season: ["winter"],
      weather: expect.arrayContaining(["rain", "snow"]),
      activity: expect.arrayContaining(["work", "leisure"]),
    },
  })
  expect(changed.scenes[id]!.associations.weather).toHaveLength(2)
  expect(changed.scenes[id]!.associations.activity).toHaveLength(2)
})

test("编辑取消不改变草稿，空关联给出就近校验", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  const edit = page.getByRole("button", { name: "编辑场景: 日间工作", exact: true })
  await edit.click()
  const dialog = page.getByRole("dialog")
  await dialog.getByRole("textbox", { name: "场景名称" }).fill("临时修改")
  await dialog.getByRole("button", { name: "取消", exact: true }).click()
  await expect(edit).toBeFocused()
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
  await edit.click()
  await dialog.getByRole("button", { name: "日间", exact: true }).click()
  await dialog.getByRole("button", { name: "工作", exact: true }).click()
  await dialog.getByRole("button", { name: "完成编辑", exact: true }).click()
  await expect(dialog.getByText("至少选择一个关联标签。")).toBeVisible()
  await dialog.getByRole("button", { name: "日间", exact: true }).click()
  await dialog.getByRole("button", { name: "完成编辑", exact: true }).click()
  const saved = await saveSettings(page)
  expect(saved.scenes.day_work!.associations).toEqual({ time: ["day"] })
})

test("窄窗口可搜索长播单，重新打开选择器后恢复完整选项", async ({ page }) => {
  const longName = `LONG_${"WALLPAPER_".repeat(20)}`
  await page.setViewportSize({ width: 375, height: 812 })
  await mockSetupApi(page, true, { ...profile, scenes: { day_work: { ...profile.scenes.day_work!, playlist: longName } } })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: {
      wallpaper_engine_path: profile.wallpaper_engine_path,
      playlists: [{ name: longName, item_count: 60 }, { name: "RAIN", item_count: 20 }],
    } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  const picker = page.getByRole("button", { name: "日间工作: 播放列表", exact: true })
  await expect(picker).toContainText(longName)
  await picker.click()
  await expect(page.getByRole("option", { name: longName, exact: true })).toBeInViewport({ ratio: 1 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole("combobox", { name: "搜索播放列表", exact: true }).fill("RAIN")
  await expect(page.getByRole("option", { name: longName, exact: true })).toBeHidden()
  await page.getByRole("option", { name: "RAIN", exact: true }).click()
  await picker.click()
  await expect(page.getByRole("combobox", { name: "搜索播放列表" })).toBeEmpty()
  await expect(page.getByRole("option", { name: longName, exact: true })).toBeVisible()
  await page.keyboard.press("Escape")
  expect((await saveSettings(page)).scenes.day_work!.playlist).toBe("RAIN")
})
