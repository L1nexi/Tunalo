import { expect, test } from "@playwright/test"
import type { Profile, SceneAssociations } from "../src/api/profile"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"

test("单变量和双变量预设按组添加，保存完整的名称与语义关联", async ({ page }) => {
  const groups: Array<{ name: string; scenes: Record<string, SceneAssociations> }> = [
    { name: "季节", scenes: {
      春季: { season: ["spring"] }, 夏季: { season: ["summer"] },
      秋季: { season: ["autumn"] }, 冬季: { season: ["winter"] },
    } },
    { name: "时间", scenes: {
      清晨: { time: ["dawn"] }, 日间: { time: ["day"] },
      黄昏: { time: ["sunset"] }, 夜晚: { time: ["night"] },
    } },
    { name: "活动", scenes: { 工作: { activity: ["work"] }, 娱乐: { activity: ["leisure"] } } },
    { name: "天气", scenes: {
      晴空: { weather: ["clear"] }, 多云: { weather: ["cloudy"] },
      雨天: { weather: ["rain"] }, 雪天: { weather: ["snow"] },
    } },
    { name: "时间与活动", scenes: {
      日间工作: { time: ["day"], activity: ["work"] },
      日间休闲: { time: ["day"], activity: ["leisure"] },
      夜间工作: { time: ["night"], activity: ["work"] },
      夜间休闲: { time: ["night"], activity: ["leisure"] },
    } },
    { name: "季节与天气", scenes: {
      冬日晴天: { season: ["winter"], weather: ["clear"] },
      冬日雨雪: { season: ["winter"], weather: expect.arrayContaining(["rain", "snow"]) },
      夏日晴朗: { season: ["summer"], weather: ["clear"] },
      夏日雨天: { season: ["summer"], weather: ["rain"] },
    } },
  ]
  await mockSetupApi(page, true, { ...profile, scenes: {} })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "从预设添加", exact: true }).click()
  const dialog = page.getByRole("dialog")
  for (const [section, names] of [
    ["单变量场景", ["季节", "时间", "活动", "天气"]],
    ["双变量场景", ["时间与活动", "季节与天气"]],
  ] as const) {
    const categories = dialog.getByRole("group", { name: section, exact: true })
    for (const name of names) {
      await expect(categories.getByRole("button", { name, exact: true })).toBeVisible()
    }
  }
  for (const group of groups) {
    await dialog.getByRole("button", { name: group.name, exact: true }).click()
    for (const name of Object.keys(group.scenes)) {
      await expect(dialog.getByRole("checkbox", { name, exact: true })).toBeVisible()
    }
    await dialog.getByRole("button", { name: "选择本组", exact: true }).click()
  }
  await dialog.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await dialog.getByRole("button", { name: "添加 22 个场景", exact: true }).click()
  const saved = await saveSettings(page)
  expect(Object.values(saved.scenes)).toHaveLength(22)
  expect(Object.fromEntries(Object.values(saved.scenes).map((scene) => [scene.name, scene.associations])))
    .toEqual(Object.assign({}, ...groups.map((group) => group.scenes)))
  expect(Object.values(saved.scenes).find((scene) => scene.name === "冬日雨雪")!.associations.weather).toHaveLength(2)
  expect(Object.values(saved.scenes).every((scene) => scene.playlist === "CASUAL_ANIME")).toBe(true)
})

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

test("预设跨组选取并批量绑定，已有关联不会重复添加", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "从预设添加", exact: true }).click()
  const dialog = page.getByRole("dialog")
  await dialog.getByRole("button", { name: "季节", exact: true }).click()
  await dialog.getByRole("button", { name: "选择本组", exact: true }).click()
  await dialog.getByRole("button", { name: "时间与活动", exact: true }).click()
  await expect(dialog.getByRole("checkbox", { name: "日间工作", exact: true })).toBeDisabled()
  await dialog.getByRole("button", { name: "季节与天气", exact: true }).click()
  await dialog.getByRole("checkbox", { name: "冬日雨雪", exact: true }).check()
  await dialog.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await dialog.getByRole("button", { name: "稍后选择", exact: true }).click()
  await expect(dialog.getByRole("button", { name: "为本次添加的场景绑定播单", exact: true })).toContainText("稍后逐个选择")
  await dialog.getByRole("button", { name: "添加 5 个场景", exact: true }).click()
  await expect(page.getByRole("button", { name: "冬日雨雪: 播放列表", exact: true })).toContainText("选择播放列表")
  await page.getByRole("checkbox", { name: "选择全部场景", exact: true }).check()
  await page.getByRole("button", { name: "批量绑定", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await page.getByRole("button", { name: "绑定播单", exact: true }).click()
  const saved = await saveSettings(page)
  expect(Object.keys(saved.scenes)).toHaveLength(6)
  expect(Object.values(saved.scenes).every((scene) => scene.playlist === "CASUAL_ANIME")).toBe(true)
  await page.getByRole("textbox", { name: "搜索场景或播单" }).fill("雨或雪")
  await expect(page.getByRole("group", { name: "冬日雨雪", exact: true })).toBeVisible()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toHaveCount(0)
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

test("移除再撤销保留原场景和绑定，不构成未保存修改", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "移除: 日间工作", exact: true }).click()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toHaveCount(0)
  await page.getByRole("button", { name: "撤销", exact: true }).click()
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toContainText("CASUAL_ANIME")
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
})

const twoSceneProfile: Profile = {
  ...profile,
  scenes: {
    ...profile.scenes,
    winter: { name: "冬季", playlist: "CASUAL_ANIME", associations: { season: ["winter"] } },
  },
}

test("跨设置项撤销场景移除，同时保留其他设置的修改", async ({ page }) => {
  await mockSetupApi(page, true, twoSceneProfile)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "移除: 日间工作", exact: true }).click()
  await page.getByRole("button", { name: "移除: 冬季", exact: true }).click()
  await page.getByRole("navigation").getByRole("button", { name: "调度风格", exact: true }).click()
  await page.getByRole("button", { name: "积极", exact: true }).click()
  await page.getByRole("alert").filter({ hasText: "冬季" }).hover()
  await page.getByRole("alert").filter({ hasText: "日间工作" }).getByRole("button", { name: "撤销", exact: true }).click()
  await page.getByRole("alert").filter({ hasText: "冬季" }).getByRole("button", { name: "撤销", exact: true }).click()
  await page.getByRole("navigation").getByRole("button", { name: /^场景绑定/ }).click()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toBeVisible()
  const saved = await saveSettings(page)
  expect(saved.scenes).toEqual(twoSceneProfile.scenes)
  expect(saved.disturbance).toEqual({
    startup_grace_seconds: 5, idle_before_switch_seconds: 10, cycle_interval_minutes: 5,
  })
})

test("保存期间禁用撤销，响应后仍可恢复并再次保存", async ({ page }) => {
  await mockSetupApi(page, true, twoSceneProfile)
  let releaseResponse!: () => void
  const responseGate = new Promise<void>((resolve) => { releaseResponse = resolve })
  let firstRequest = true
  await page.route(/\/api\/profile(?:\?.*)?$/, async (route) => {
    if (route.request().method() !== "PUT" || !firstRequest) {
      await route.fallback()
      return
    }
    firstRequest = false
    await responseGate
    await route.fallback()
  })
  await page.goto("/?locale=zh")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "移除: 日间工作", exact: true }).click()
  const submitted = page.waitForRequest((request) => request.method() === "PUT" && new URL(request.url()).pathname === "/api/profile")
  await page.getByRole("button", { name: "保存并应用", exact: true }).click()
  const firstSaved = (await submitted).postDataJSON() as Profile
  expect(Object.keys(firstSaved.scenes)).toEqual(["winter"])
  const undo = page.getByRole("button", { name: "撤销", exact: true })
  await expect(undo).toBeDisabled()
  await page.waitForTimeout(5_200)
  await expect(undo).toBeDisabled()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toBeHidden()
  const firstResponse = page.waitForResponse(
    (response) => response.request().method() === "PUT" && new URL(response.url()).pathname === "/api/profile",
  )
  releaseResponse()
  expect((await firstResponse).ok()).toBe(true)
  await expect(page.getByText("所有修改已保存", { exact: true })).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
  await expect(undo).toBeEnabled()
  await undo.click()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toBeVisible()
  expect((await saveSettings(page)).scenes).toEqual(twoSceneProfile.scenes)
  await page.reload()
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
})

test("320px 英文深色窗口中可完成预设和自定义场景编辑", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 320, height: 720 })
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" })
  await mockSetupApi(page, true, { ...profile, language: "en" })
  await page.goto("/?locale=en")
  await page.getByRole("navigation").getByRole("button", { name: "Scene assignments", exact: true }).click()
  await page.getByRole("button", { name: "Add presets", exact: true }).click()
  const dialog = page.getByRole("dialog")
  await expect(dialog).toBeInViewport({ ratio: 1 })
  await dialog.getByRole("button", { name: "Season and weather", exact: true }).click()
  await dialog.getByRole("checkbox", { name: "Rainy summer", exact: true }).check()
  await dialog.getByRole("button", { name: "Playlist for these scenes", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await page.screenshot({ path: testInfo.outputPath("presets-narrow.png") })
  const addPreset = dialog.getByRole("button", { name: "Add 1 scene", exact: true })
  await expect(addPreset).toBeInViewport()
  await addPreset.click()
  await page.getByRole("button", { name: "Custom scene", exact: true }).click()
  await dialog.getByRole("textbox", { name: "Scene name", exact: true }).fill("Winter rain or snow")
  for (const name of ["Winter", "Rain", "Snow"]) await dialog.getByRole("button", { name, exact: true }).click()
  await dialog.getByRole("button", { name: "Playlist", exact: true }).click()
  await page.getByRole("option", { name: "CASUAL_ANIME", exact: true }).click()
  await page.screenshot({ path: testInfo.outputPath("editor-narrow.png") })
  await expect(dialog).toBeInViewport({ ratio: 1 })
  const addScene = dialog.getByRole("button", { name: "Add scene", exact: true })
  await expect(addScene).toBeInViewport()
  await addScene.click()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await saveSettings(page, "en")
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
