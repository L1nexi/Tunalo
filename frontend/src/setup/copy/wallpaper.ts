const zh = {
  title: "连接 Wallpaper Engine",
  description: "",
  pathLabel: "Wallpaper Engine 可执行文件",
  pathDescription: "选择 Wallpaper Engine 可执行文件，如 wallpaper64.exe。留空以尝试自动检测。",
  pathPlaceholder: "选择 Wallpaper Engine 可执行文件",
  choose: "选择文件",
  detect: "自动检测",
  scan: "扫描播放列表",
  scanning: "正在扫描",
  found: "文件路径有效",
  foundDescription: (count: number) => `找到 ${count} 个可用播放列表。`,
  scanResultsLabel: "播放列表及对应壁纸数量",
  playlistName: "Wallpaper Engine 中的播放列表名称",
  wallpaperCount: "壁纸数量",
  itemCount: (count: number) => `${count} 张`,
  englishNames: "为降低命令行调用时的兼容问题，建议播放列表名称优先使用英文字母与数字的组合。",
  emptyTitle: "未找到可用播放列表",
  emptyDescription: "请于 Wallpaper Engine 中创建至少一个包含壁纸的播放列表后重新尝试扫描。",
  zeroItem: "未找到壁纸",
  scanAgain: "重新扫描",
  manualHint: "如果自动检测失败，请手动选择 wallpaper64.exe。",
  scanRequired: "请扫描并确认至少一个可用播放列表。",
};

const en = {
  title: "Connect Wallpaper Engine",
  description:
    "Read Wallpaper Engine's local configuration first, so Scenes can only use playlists that actually exist.",
  pathLabel: "Wallpaper Engine executable",
  pathDescription:
    "Usually wallpaper64.exe inside the Steam installation. Leave blank to try automatic detection.",
  pathPlaceholder: "Auto-detect, or choose wallpaper64.exe",
  choose: "Choose file",
  detect: "Auto-detect",
  scan: "Scan playlists",
  scanning: "Scanning",
  found: "Connected",
  foundDescription: (count: number) => `Found ${count} usable playlists.`,
  scanResultsLabel: "Scanned playlists and wallpaper counts",
  playlistName: "Playlist name in Wallpaper Engine",
  wallpaperCount: "Wallpaper count",
  itemCount: (count: number) => `${count} wallpapers`,
  englishNames:
    "For command-line compatibility, prefer English letters and digits in playlist names. Existing non-English names can still be scanned; if switching fails, try renaming the playlist in English.",
  emptyTitle: "No usable playlists found",
  emptyDescription: "Create at least one Wallpaper Engine playlist containing a wallpaper, then scan again.",
  zeroItem: "No wallpapers",
  scanAgain: "Scan again",
  manualHint: "If automatic detection fails, choose wallpaper64.exe manually.",
  scanRequired: "Scan and confirm at least one usable playlist.",
};

export const WALLPAPER_COPY = { zh, en };
