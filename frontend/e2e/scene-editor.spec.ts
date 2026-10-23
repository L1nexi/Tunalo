import { expect, test } from "@playwright/test"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"

test("自定义场景保存同组多选，重开后名称、播单与关联一致", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
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
  await page.goto("/?locale=zh")
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
  await page.goto("/?locale=zh")
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
