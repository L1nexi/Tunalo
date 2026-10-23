import { expect, test } from "@playwright/test"
import { mockSetupApi } from "./support/profileApi"

test("经纬度估算失败说明原因，仍可手填坐标", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ status: 503, json: { error: "location_detection_unavailable", reason: "proxy_error" } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByText(/代理连接失败/)).toBeVisible()
  await expect(page.getByRole("button", { name: "打开地图查找坐标" })).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度" }).fill("39.9042")
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toHaveValue("39.9042")
})

test("经纬度估算不需要城市名称", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ json: { location: { latitude: 47.498253, longitude: 19.03978 } } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByRole("spinbutton", { name: "纬度" })).toHaveValue("47.498253")
  await expect(page.getByRole("spinbutton", { name: "经度" })).toHaveValue("19.03978")
  await page.getByRole("navigation").getByRole("button", { name: "查看配置草稿", exact: true }).click()
  await page.getByText("查看当前草稿全部设置").click()
  await expect(page.getByText("纬度 47.498253，经度 19.03978", { exact: true })).toBeVisible()
})

test("经纬度估算显示 IP 返回的城市，手动修改后清除提示", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.route("**/api/location-estimates", async (route) => {
    await route.fulfill({ json: { location: { city: "Budapest", latitude: 47.498253, longitude: 19.03978 } } })
  })
  await page.goto("/?locale=zh")
  await page.getByRole("button", { name: /天气服务/ }).click()
  await page.getByRole("button", { name: "估算经纬度" }).click()
  await expect(page.getByText("城市：Budapest，已填入预估经纬度。")).toBeVisible()
  await page.getByRole("spinbutton", { name: "纬度" }).fill("47.5")
  await expect(page.getByText("城市：Budapest，已填入预估经纬度。")).toHaveCount(0)
})

test("坐标越界或缺失时就近提示，不再等检查页", async ({ page }) => {
  await mockSetupApi(page, true)
  await page.goto("/?locale=zh")
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()

  await page.getByRole("spinbutton", { name: "纬度" }).fill("121.4737")
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toBeVisible()
  await expect(page.getByRole("button", { name: "保存并应用" })).toBeDisabled()

  // 切走再切回，编辑过的坐标仍就近提示，与保存禁用状态保持同步。
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "调度风格" }).click()
  await page.getByRole("navigation", { name: "设置项" }).getByRole("button", { name: "天气服务" }).click()
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toBeVisible()

  await page.getByRole("spinbutton", { name: "经度" }).fill("")
  await expect(page.getByText("请填写经度。")).toBeVisible()

  await page.getByRole("spinbutton", { name: "纬度" }).fill("31.2304")
  await expect(page.getByText("纬度必须在 -90 到 90 之间。")).toHaveCount(0)
})
