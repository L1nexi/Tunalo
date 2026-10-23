import type { ActivityProfile } from "@/api/profile"
import { normalizeProcess, normalizeTitle } from "@/setup/profile/model"

interface AppRules {
  name: string
  nameEn?: string
  processes: string[]
  titleKeywords?: string[]
}

export interface ActivityRulePack {
  id: "development" | "office" | "social" | "multimedia"
  apps: AppRules[]
}

export const ACTIVITY_RULE_PACKS: ActivityRulePack[] = [
  {
    id: "development",
    apps: [
      { name: "VS Code", processes: ["code"], titleKeywords: ["Visual Studio Code"] },
      { name: "Cursor", processes: ["cursor"] },
      { name: "Windsurf", processes: ["windsurf"] },
      { name: "Visual Studio", processes: ["devenv"] },
      { name: "IntelliJ IDEA", processes: ["idea64"] },
      { name: "PyCharm", processes: ["pycharm64"] },
      { name: "WebStorm", processes: ["webstorm64"] },
      { name: "Android Studio", processes: ["studio64"] },
    ],
  },
  {
    id: "office",
    apps: [
      { name: "Word", processes: ["winword"] },
      { name: "Excel", processes: ["excel"] },
      { name: "PowerPoint", processes: ["powerpnt"] },
      { name: "OneNote", processes: ["onenote"] },
      { name: "WPS", processes: ["wps", "et", "wpp"] },
      { name: "Obsidian", processes: ["obsidian"] },
      { name: "Notion", processes: ["notion"], titleKeywords: ["Notion"] },
      { name: "腾讯文档", nameEn: "Tencent Docs", processes: [], titleKeywords: ["腾讯文档"] },
    ],
  },
  {
    id: "social",
    apps: [
      { name: "微信", nameEn: "WeChat", processes: ["wechat", "weixin"] },
      { name: "QQ", processes: ["qq"] },
      { name: "Telegram", processes: ["telegram"] },
      { name: "Discord", processes: ["discord"] },
      { name: "Slack", processes: ["slack"] },
      { name: "Teams", processes: ["ms-teams", "teams"] },
    ],
  },
  {
    id: "multimedia",
    apps: [
      { name: "VLC", processes: ["vlc"] },
      { name: "mpv", processes: ["mpv"] },
      { name: "PotPlayer", processes: ["potplayer", "potplayer64"] },
      { name: "Spotify", processes: ["spotify"] },
      { name: "网易云音乐", nameEn: "NetEase Cloud Music", processes: ["cloudmusic"] },
      { name: "QQ 音乐", nameEn: "QQ Music", processes: ["qqmusic"] },
      { name: "YouTube", processes: [], titleKeywords: ["YouTube"] },
      { name: "哔哩哔哩", nameEn: "bilibili", processes: [], titleKeywords: ["哔哩哔哩", "bilibili"] },
    ],
  },
]

export function importActivityRulePack(
  activity: ActivityProfile, pack: ActivityRulePack, target: "work" | "leisure",
): { activity: ActivityProfile; added: number; skipped: number } {
  const updated: ActivityProfile = {
    work_processes: [...activity.work_processes], leisure_processes: [...activity.leisure_processes],
    work_title_keywords: [...activity.work_title_keywords], leisure_title_keywords: [...activity.leisure_title_keywords],
  }
  let added = 0
  let skipped = 0
  const opposite = target === "work" ? "leisure" : "work"
  for (const kind of ["processes", "title_keywords"] as const) {
    const destination = updated[`${target}_${kind}`]
    const normalize = kind === "processes" ? normalizeProcess : normalizeTitle
    const existing = new Set([...destination, ...updated[`${opposite}_${kind}`]].map(normalize))
    const incoming = pack.apps.flatMap((app) => kind === "processes" ? app.processes : app.titleKeywords ?? [])
    for (const rule of incoming) {
      const key = normalize(rule)
      if (existing.has(key)) {
        skipped++
      } else {
        destination.push(rule)
        existing.add(key)
        added++
      }
    }
  }
  return { activity: updated, added, skipped }
}
