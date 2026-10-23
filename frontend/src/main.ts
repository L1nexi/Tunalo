import { createApp, nextTick } from "vue"

import App from "./App.vue"
import "./style.css"
import { initializeTheme, reportThemeError } from "./theme"
import "vue-sonner/style.css"

async function mount(): Promise<void> {
  let themeLoadFailed = false
  try {
    await initializeTheme()
  } catch {
    themeLoadFailed = true
  }
  createApp(App).mount("#app")
  if (themeLoadFailed) {
    await nextTick()
    reportThemeError("load")
  }
}

void mount()
