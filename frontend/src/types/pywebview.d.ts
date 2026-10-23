export {}

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_theme(): Promise<"auto" | "light" | "dark">
        set_theme(theme: "auto" | "light" | "dark"): Promise<void>
        choose_wallpaper_engine(): Promise<string | null>
        close(): Promise<void>
        open_external(url: string): Promise<void>
        page_ready(): Promise<void>
      }
    }
  }
}
