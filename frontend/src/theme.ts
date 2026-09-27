import { useColorMode } from "@vueuse/core"

export const themeMode = useColorMode({
  storageKey: "tunalo-theme",
  emitAuto: true,
})
