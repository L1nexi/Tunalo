import { expect, test } from "@playwright/test"
import type { SceneAssociations } from "../src/api/profile"
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
  await page.goto("/?locale=zh&test=1")
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

test("预设跨组选取并批量绑定，已有关联不会重复添加", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
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

test("没有可用播放列表时，场景页可直接跳到 Wallpaper Engine", async ({ page }) => {
  await mockSetupApi(page, false)
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: { wallpaper_engine_path: profile.wallpaper_engine_path, playlists: [] } })
  })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: /场景绑定/ }).click()
  await expect(page.getByText("场景绑定需要至少一个包含壁纸的播放列表。")).toBeVisible()
  await page.getByRole("button", { name: "连接 Wallpaper Engine" }).click()
  await expect(page.getByRole("heading", { name: "连接 Wallpaper Engine" })).toBeVisible()
})
