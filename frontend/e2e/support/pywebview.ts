import type { Page } from "@playwright/test"

export type Theme = "auto" | "light" | "dark"

export async function mockPywebview(page: Page, getTheme: () => Promise<Theme>, setTheme: (theme: Theme) => Promise<void>, close = () => {}, delayed = false): Promise<void> {
  await page.exposeFunction("readAppearance", getTheme)
  await page.exposeFunction("writeAppearance", setTheme)
  await page.exposeFunction("closeSettings", close)
  await page.addInitScript((delayed) => {
    const host = window as unknown as {
      readAppearance: () => Promise<Theme>
      writeAppearance: (theme: Theme) => Promise<void>
      closeSettings: () => Promise<void>
    }
    function connect(): void {
      window.pywebview = { api: {
        get_theme: () => host.readAppearance(),
        set_theme: (theme) => host.writeAppearance(theme),
        close: () => host.closeSettings(),
        page_ready: async () => {},
        open_external: async () => {},
        choose_wallpaper_engine: async () => null,
      } }
      window.dispatchEvent(new Event("pywebviewready"))
    }
    if (delayed) window.addEventListener("test:bridge-ready", connect, { once: true })
    else connect()
  }, delayed)
}
