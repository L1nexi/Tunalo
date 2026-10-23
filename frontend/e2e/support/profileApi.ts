import { expect, type Page } from "@playwright/test"
import type { Profile } from "../../src/api/profile"

export const profile: Profile = {
  version: 3,
  setup_complete: true,
  wallpaper_engine_path: "C:\\Wallpaper Engine\\wallpaper64.exe",
  language: "zh",
  weather: {
    api_key: "saved-key",
    location: { name: "上海", latitude: 31.2304, longitude: 121.4737 },
  },
  scenes: { day_work: { name: "日间工作", playlist: "CASUAL_ANIME", associations: { time: ["day"], activity: ["work"] } } },
  matching: { preference_tiers: [] },
  disturbance: {
    startup_grace_seconds: 15,
    idle_before_switch_seconds: 20,
    cycle_interval_minutes: 15,
  },
  activity: {
    work_processes: [],
    leisure_processes: [],
    work_title_keywords: [],
    leisure_title_keywords: [],
  },
}

export async function mockSetupApi(page: Page, hasProfile: boolean, settingsProfile: Profile = profile): Promise<void> {
  let committed = structuredClone(settingsProfile)
  let exists = hasProfile
  await page.route(/\/api\/profile(?:\?.*)?$/, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill(exists ? { json: { profile: committed } } : { status: 404, json: { error: "profile_not_found" } })
      return
    }
    committed = route.request().postDataJSON() as Profile
    exists = true
    await route.fulfill({ json: { status: route.request().method() === "POST" ? "created" : "applied", profile: committed } })
  })
  await page.route("**/api/wallpaper-engine/playlist-scans", async (route) => {
    await route.fulfill({ json: { wallpaper_engine_path: profile.wallpaper_engine_path, playlists: [{ name: "CASUAL_ANIME", item_count: 60 }] } })
  })
}


export async function saveSettings(page: Page, locale: "zh" | "en" = "zh"): Promise<Profile> {
  const response = page.waitForResponse(
    (response) => response.request().method() === "PUT" && new URL(response.url()).pathname === "/api/profile",
  )
  const button = page.getByRole("button", { name: locale === "zh" ? "保存并应用" : "Save and apply", exact: true })
  await button.click()
  const saved = await response
  expect(saved.ok()).toBe(true)
  await expect(button).toBeDisabled()
  return saved.request().postDataJSON() as Profile
}

export async function addPreset(page: Page, group: string, name: string): Promise<void> {
  await page.getByRole("button", { name: "从预设添加", exact: true }).click()
  const dialog = page.getByRole("dialog")
  await dialog.getByRole("button", { name: group, exact: true }).click()
  await dialog.getByRole("checkbox", { name, exact: true }).check()
  await dialog.getByRole("button", { name: "添加 1 个场景", exact: true }).click()
}
