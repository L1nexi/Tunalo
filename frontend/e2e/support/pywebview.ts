import type { Page } from "@playwright/test"

export type Theme = "auto" | "light" | "dark"

export async function mockPywebview(
  page: Page,
  getTheme: () => Promise<Theme>,
  setTheme: (theme: Theme) => Promise<void>,
  close = () => {},
  delayed = false,
  autostart = { get: async () => false, set: async (_enabled: boolean): Promise<void> => {} },
): Promise<void> {
  await page.exposeFunction("readAppearance", getTheme)
  await page.exposeFunction("writeAppearance", setTheme)
  await page.exposeFunction("closeSettings", close)
  await page.exposeFunction("readAutostart", autostart.get)
  await page.exposeFunction("writeAutostart", autostart.set)
  await page.addInitScript((delayed) => {
    const host = window as unknown as {
      readAppearance: () => Promise<Theme>
      writeAppearance: (theme: Theme) => Promise<void>
      closeSettings: () => Promise<void>
      readAutostart: () => Promise<boolean>
      writeAutostart: (enabled: boolean) => Promise<void>
    }
    function connect(): void {
      window.pywebview = { api: {
        get_theme: () => host.readAppearance(),
        set_theme: (theme) => host.writeAppearance(theme),
        get_autostart: () => host.readAutostart(),
        set_autostart: (enabled) => host.writeAutostart(enabled),
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
