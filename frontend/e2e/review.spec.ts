import { expect, test } from "@playwright/test"
import { mockSetupApi, profile } from "./support/profileApi"

test("首次检查配置时待处理项和修正入口位于首屏", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 600 })
  await mockSetupApi(page, false)
  await page.goto("/?locale=zh&test=1")
  await expect(page.getByRole("table", { name: "播放列表及对应壁纸数量" })).toBeVisible()
  await page.getByRole("navigation").getByRole("button", { name: "查看配置草稿", exact: true }).click()
  const issues = page.getByRole("alert")
  await expect(issues).toContainText("配置项缺失")
  await expect(issues).toBeInViewport({ ratio: 1 })
  await expect(issues.getByRole("button", { name: "场景绑定", exact: true })).toBeInViewport()
  await expect(page.getByRole("button", { name: "完成设置", exact: true })).toBeDisabled()
  await issues.getByRole("button", { name: "天气服务", exact: true }).click()
  await expect(page.getByRole("textbox", { name: "OpenWeatherMap API Key", exact: true })).toBeFocused()
})

for (const scanChange of ["改名", "删除", "清空"] as const) {
  test(`播单${scanChange}后检查页区分失效绑定，并定位到对应场景`, async ({ page }) => {
    await mockSetupApi(page, true, {
      ...profile,
      scenes: {
        valid: { ...profile.scenes.day_work!, name: "有效场景", playlist: "AVAILABLE" },
        missing: { ...profile.scenes.day_work!, name: "失效场景" },
        unbound: { ...profile.scenes.day_work!, name: "待选场景", playlist: "" },
      },
    })
    await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
      await route.fulfill({ json: {
        wallpaper_engine_path: profile.wallpaper_engine_path,
        playlists: [
          { name: "AVAILABLE", item_count: 10 },
          ...(scanChange === "改名" ? [{ name: "RENAMED", item_count: 60 }] : []),
          ...(scanChange === "清空" ? [{ name: "CASUAL_ANIME", item_count: 0 }] : []),
        ],
      } })
    })
    await page.goto("/?locale=zh&test=1")
    const navigation = page.getByRole("navigation")
    await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
    await page.getByText("查看当前草稿全部设置", { exact: true }).click()
    await expect(page.getByText("已绑定 1 个，待绑定 1 个，1 个绑定失效")).toBeVisible()
    await page.getByRole("button", { name: "失效场景: 绑定失效", exact: true }).click()
    const picker = page.getByRole("button", { name: "失效场景: 播放列表", exact: true })
    await expect(picker).toBeFocused()
    await expect(picker).toHaveAccessibleDescription("已选播放列表不在扫描结果中，请重新选择。")
    await picker.click()
    await page.getByRole("option", { name: "AVAILABLE", exact: true }).click()
    await navigation.getByRole("button", { name: "查看配置草稿", exact: true }).click()
    await page.getByText("查看当前草稿全部设置", { exact: true }).click()
    await expect(page.getByText("已绑定 2 个，待绑定 1 个")).toBeVisible()
  })
}

for (const scanChange of ["删除", "清空"] as const) {
  test(`全部播单${scanChange}后仍能定位到首屏外的失效场景`, async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 600 })
    await mockSetupApi(page, true, {
      ...profile,
      scenes: Object.fromEntries(Array.from({ length: 12 }, (_, index) => [
        `scene_${index}`,
        { ...profile.scenes.day_work!, name: `测试场景${index}` },
      ])),
    })
    await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
      await route.fulfill({ json: {
        wallpaper_engine_path: profile.wallpaper_engine_path,
        playlists: scanChange === "删除" ? [] : [{ name: "CASUAL_ANIME", item_count: 0 }],
      } })
    })
    await page.goto("/?locale=zh&test=1")
    await page.getByRole("navigation").getByRole("button", { name: "查看配置草稿", exact: true }).click()
    await page.getByText("查看当前草稿全部设置", { exact: true }).click()
    await page.getByRole("button", { name: "测试场景11: 绑定失效", exact: true }).click()

    const scene = page.getByRole("group", { name: "测试场景11", exact: true })
    await expect(scene.getByRole("button", { name: "测试场景11: 播放列表", exact: true })).toBeDisabled()
    await expect(scene).toBeInViewport({ ratio: 1 })
    await expect(scene.getByRole("button", { name: "编辑场景: 测试场景11", exact: true })).toBeFocused()
  })
}

test("零场景时检查页明确提示尚未添加场景", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, scenes: {} })
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await page.getByText("查看当前草稿全部设置", { exact: true }).click()
  await expect(page.getByText("尚未添加场景", { exact: true })).toBeVisible()
})

test("英文检查页说明失效绑定，并可定位修正", async ({ page }) => {
  await mockSetupApi(page, true, { ...profile, language: "en" })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: {
      wallpaper_engine_path: profile.wallpaper_engine_path,
      playlists: [{ name: "AVAILABLE", item_count: 10 }],
    } })
  })
  await page.goto("/?locale=en&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "Review and save", exact: true }).click()
  await page.getByText("Review all draft settings", { exact: true }).click()
  await expect(page.getByText("0 assigned, 0 awaiting playlists, 1 unavailable binding")).toBeVisible()
  await page.getByRole("button", { name: "日间工作: Unavailable binding", exact: true }).click()
  await expect(page.getByRole("button", { name: "日间工作: Playlist", exact: true })).toBeFocused()
})
