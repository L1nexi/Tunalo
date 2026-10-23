import { onBeforeUnmount, onMounted, ref } from "vue"
import type { Ref } from "vue"

/** 原生桥接、关闭请求和浏览器离开保护随设置窗口一起注册与释放。 */
export function useSetupWindow(isDirty: Readonly<Ref<boolean>>) {
  const hasNativeBridge = ref(Boolean(window.pywebview?.api))
  const closeDialogOpen = ref(false)

  function handleBeforeUnload(event: BeforeUnloadEvent): void {
    if (!isDirty.value) return
    event.preventDefault()
  }

  function updateNativeBridgeAvailability(): void {
    hasNativeBridge.value = Boolean(window.pywebview?.api)
    if (window.pywebview?.api) void window.pywebview.api.page_ready()
  }

  function requestClose(): void {
    if (isDirty.value) {
      closeDialogOpen.value = true
      return
    }
    void closeWindow()
  }

  async function closeWindow(): Promise<void> {
    if (window.pywebview?.api) await window.pywebview.api.close()
  }

  async function chooseWallpaperEngine(): Promise<string | null> {
    return window.pywebview?.api ? await window.pywebview.api.choose_wallpaper_engine() : null
  }

  async function openExternal(url: string): Promise<void> {
    if (window.pywebview?.api) {
      await window.pywebview.api.open_external(url)
      return
    }
    window.open(url, "_blank", "noopener,noreferrer")
  }

  onMounted(() => {
    window.addEventListener("beforeunload", handleBeforeUnload)
    window.addEventListener("pywebviewready", updateNativeBridgeAvailability)
    // ui/webview.py 用同名事件转发被守卫拦截的原生 × / Alt+F4。
    window.addEventListener("tunalo:native-close-request", requestClose)
    updateNativeBridgeAvailability()
  })

  onBeforeUnmount(() => {
    window.removeEventListener("beforeunload", handleBeforeUnload)
    window.removeEventListener("pywebviewready", updateNativeBridgeAvailability)
    window.removeEventListener("tunalo:native-close-request", requestClose)
  })

  return { hasNativeBridge, closeDialogOpen, requestClose, closeWindow, chooseWallpaperEngine, openExternal }
}
