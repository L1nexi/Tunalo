import { computed, inject, onMounted, provide, toRef } from "vue"
import type { InjectionKey } from "vue"

import type { Locale, Profile } from "@/api/profile"
import { describeScanError } from "@/setup/errorMessages"
import { usePlaylistScan } from "@/setup/wallpaper/usePlaylistScan"
import { useProfileDraft } from "@/setup/profile/useProfileDraft"
import { useProfileSubmission } from "@/setup/profile/useProfileSubmission"
import { useSetupFlow } from "@/setup/workflow/useSetupFlow"
import { useSetupWindow } from "./useSetupWindow"
import { useWeatherServices } from "@/setup/weather/useWeatherServices"

type Editor = ReturnType<typeof useProfileDraft>
type Flow = ReturnType<typeof useSetupFlow>
type Weather = ReturnType<typeof useWeatherServices>
type NativeWindow = ReturnType<typeof useSetupWindow>
type Submission = ReturnType<typeof useProfileSubmission>
type Scan = ReturnType<typeof useWorkspaceScan>

const editorKey: InjectionKey<Editor> = Symbol("setup-editor")
const flowKey: InjectionKey<Flow> = Symbol("setup-flow")
const weatherKey: InjectionKey<Weather> = Symbol("setup-weather")
const windowKey: InjectionKey<NativeWindow> = Symbol("setup-window")
const submissionKey: InjectionKey<Submission> = Symbol("setup-submission")
const scanKey: InjectionKey<Scan> = Symbol("setup-playlists")

/** 设置工作区创建共享会话，子视图按职责读取所需模块。 */
export function useSetupWorkspace(initialProfile: Profile | null, initialLocale: Locale) {
  const editor = useProfileDraft(initialProfile, initialLocale)
  const scan = usePlaylistScan(toRef(editor.draft, "wallpaper_engine_path"))
  const flow = useSetupFlow(editor, scan)
  const weather = useWeatherServices(
    toRef(editor.draft, "weather"),
    editor.locale,
    flow.clearWeatherFieldFeedback,
  )
  const nativeWindow = useSetupWindow(editor.isDirty)
  const submission = useProfileSubmission(editor, flow, weather, nativeWindow.closeWindow)
  const workspaceScan = useWorkspaceScan(editor, flow, scan, nativeWindow)

  provide(editorKey, editor)
  provide(flowKey, flow)
  provide(weatherKey, weather)
  provide(windowKey, nativeWindow)
  provide(submissionKey, submission)
  provide(scanKey, workspaceScan)

  onMounted(() => {
    void scan.scan().then(editor.acceptDetectedPath)
  })
  return { editor, flow, submission }
}

function useWorkspaceScan(
  editor: Editor,
  flow: Flow,
  scan: ReturnType<typeof usePlaylistScan>,
  nativeWindow: NativeWindow,
) {
  const detail = computed(() =>
    scan.error.value ? describeScanError(scan.error.value, editor.locale.value) : "",
  )

  async function rescan(): Promise<void> {
    flow.clearStepFeedback("wallpaper")
    await scan.scan()
  }

  async function chooseWallpaperEngine(): Promise<void> {
    const path = await nativeWindow.chooseWallpaperEngine()
    if (!path) return
    flow.updatePath(path)
    await scan.scan()
  }

  return { ...scan, detail, rescan, chooseWallpaperEngine }
}

export const useSetupEditor = (): Editor => inject(editorKey)!
export const useSetupFlowContext = (): Flow => inject(flowKey)!
export const useSetupWeather = (): Weather => inject(weatherKey)!
export const useSetupNativeWindow = (): NativeWindow => inject(windowKey)!
export const useSetupSubmission = (): Submission => inject(submissionKey)!
export const useSetupScan = (): Scan => inject(scanKey)!
