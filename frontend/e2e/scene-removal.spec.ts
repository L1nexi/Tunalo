import { expect, test } from "@playwright/test"
import type { Profile } from "../src/api/profile"
import { mockSetupApi, profile, saveSettings } from "./support/profileApi"

const twoSceneProfile: Profile = {
  ...profile,
  scenes: {
    ...profile.scenes,
    winter: { name: "冬季", playlist: "CASUAL_ANIME", associations: { season: ["winter"] } },
  },
}

test("移除再撤销保留原场景和绑定，不构成未保存修改", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh&test=1")
  await page.getByRole("navigation").getByRole("button", { name: "场景绑定", exact: true }).click()
  await page.getByRole("button", { name: "移除: 日间工作", exact: true }).click()
  await expect(page.getByRole("group", { name: "日间工作", exact: true })).toHaveCount(0)
  await page.getByRole("button", { name: "撤销", exact: true }).click()
  await expect(page.getByRole("button", { name: "日间工作: 播放列表" })).toContainText("CASUAL_ANIME")
  await expect(page.getByRole("button", { name: "保存并应用", exact: true })).toBeDisabled()
})

test("跨设置项撤销场景移除，同时保留其他设置的修改", async ({ page }) => {
  await mockSetupApi(page, true, twoSceneProfile)
  await page.goto("/?locale=zh&test=1")
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
  await page.goto("/?locale=zh&test=1")
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
