import { useColorMode } from "@vueuse/core"
import { watch } from "vue"
import { toast } from "vue-sonner"

const browserTest = new URLSearchParams(window.location.search).get("test") === "1"

export const { store: themeMode } = useColorMode({
  storageKey: browserTest ? "tunalo-theme" : null,
})

let pendingSave: Promise<void> = Promise.resolve()

export function reportThemeError(action: "load" | "save"): void {
  const zh = document.documentElement.lang.startsWith("zh")
  const messages = zh
    ? { load: "无法读取外观偏好，暂用系统外观。", save: "外观偏好未能保存，请重试。" }
    : { load: "Couldn't load appearance. Using the system theme.", save: "Couldn't save appearance. Please try again." }
  toast.error(messages[action])
}

export async function initializeTheme(): Promise<void> {
  if (browserTest) return
  if (!window.pywebview?.api) {
    await new Promise<void>((resolve) => window.addEventListener("pywebviewready", () => resolve(), { once: true }))
  }
  const api = window.pywebview!.api
  try {
    themeMode.value = await api.get_theme()
  } finally {
    watch(themeMode, (theme) => {
      pendingSave = pendingSave.then(() => api.set_theme(theme)).catch(() => reportThemeError("save"))
    }, { flush: "sync" })
  }
}

export async function flushThemePreference(): Promise<void> {
  let saving: Promise<void>
  do {
    saving = pendingSave
    await saving
  } while (saving !== pendingSave)
}
