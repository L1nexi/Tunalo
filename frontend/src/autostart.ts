import { computed, onBeforeUnmount, onMounted, readonly, ref } from "vue"

type AutostartStatus = "unavailable" | "loading" | "ready" | "saving" | "load-error" | "save-error"

const enabled = ref(false)
const status = ref<AutostartStatus>("unavailable")
let pendingRead: Promise<void> | null = null
let pendingSave: Promise<void> | null = null
let failedTarget: boolean | undefined

export const autostartSaving = computed(() => status.value === "saving")

function loadPreference(): Promise<void> {
  if (pendingSave) return pendingSave
  if (pendingRead) return pendingRead
  const api = window.pywebview?.api
  if (!api) {
    status.value = "unavailable"
    return Promise.resolve()
  }

  status.value = "loading"
  pendingRead = api.get_autostart()
    .then((value) => {
      enabled.value = value
      status.value = "ready"
    })
    .catch(() => { status.value = "load-error" })
    .finally(() => { pendingRead = null })
  return pendingRead
}

function setEnabled(value: boolean): Promise<void> {
  const api = window.pywebview?.api
  if (!api || (status.value !== "ready" && status.value !== "save-error")) return Promise.resolve()

  status.value = "saving"
  pendingSave = api.set_autostart(value)
    .then(() => {
      enabled.value = value
      failedTarget = undefined
      status.value = "ready"
    })
    .catch(() => {
      failedTarget = value
      status.value = "save-error"
    })
    .finally(() => { pendingSave = null })
  return pendingSave
}

export function useAutostart() {
  const canChange = computed(() => status.value === "ready" || status.value === "save-error")
  const busy = computed(() => status.value === "loading" || status.value === "saving")

  function retry(): Promise<void> {
    return status.value === "save-error" && failedTarget !== undefined
      ? setEnabled(failedTarget)
      : loadPreference()
  }

  function onBridgeReady(): void {
    void loadPreference()
  }

  onMounted(() => {
    window.addEventListener("pywebviewready", onBridgeReady)
    if (status.value !== "save-error") void loadPreference()
  })
  onBeforeUnmount(() => window.removeEventListener("pywebviewready", onBridgeReady))

  return { enabled: readonly(enabled), status: readonly(status), canChange, busy, setEnabled, retry }
}

export async function flushAutostartPreference(): Promise<void> {
  while (pendingSave) await pendingSave
}
