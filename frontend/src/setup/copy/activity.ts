const zh = {
  title: "识别当前活动",
  description: "根据前台应用与窗口标题区分工作、休闲。",
  recognitionHelp: "标题关键词优先于进程名。休闲指明确的娱乐活动；未命中规则时，本次活动不计为工作或休闲。",
  matchingTitle: "规则如何匹配",
  workTitle: "工作",
  leisureTitle: "休闲",
  processLabel: "进程名",
  titleKeywordLabel: "窗口标题关键词",
  processPlaceholder: "例如 Photoshop.exe",
  keywordPlaceholder: "例如 项目计划",
  add: "添加",
  empty: "暂未添加",
  importGroups: "导入应用组",
  importWork: "导入工作",
  importLeisure: "导入休闲",
  packLabels: { development: "开发人员工具", office: "办公工具", social: "社交", multimedia: "多媒体" },
  imported: (added: number, skipped: number) => `新增 ${added} 条规则，跳过 ${skipped} 条重复或冲突规则。`,
  conflictTitle: "存在冲突规则",
  conflictDescription: (values: string) => `这些项目同时出现在工作和休闲场景规则中：${values}`,
  matchingHelp:
    "进程名须完整匹配，忽略大小写和末尾的 .exe；窗口标题只需包含关键词，忽略大小写。例如，浏览器可归入工作，再用视频网站的标题关键词识别休闲。",
  pendingWarning: "输入框中有尚未添加的文字。请按回车或点“添加”，或者清空后再保存。",
};

const en = {
  title: "Recognize activity",
  description: "Identify work and leisure from foreground apps and window titles.",
  recognitionHelp:
    "Title keywords take priority over process names. Leisure means intentional entertainment; an unmatched observation counts as neither work nor leisure.",
  matchingTitle: "How rules match",
  workTitle: "Work",
  leisureTitle: "Leisure",
  processLabel: "Process names",
  titleKeywordLabel: "Window title keywords",
  processPlaceholder: "e.g. Photoshop.exe",
  keywordPlaceholder: "e.g. Project plan",
  add: "Add",
  empty: "Nothing added",
  importGroups: "Import app groups",
  importWork: "Import into work",
  importLeisure: "Import into leisure",
  packLabels: {
    development: "Developer tools",
    office: "Office tools",
    social: "Social",
    multimedia: "Multimedia",
  },
  imported: (added: number, skipped: number) =>
    `Added ${added} rules; skipped ${skipped} duplicates or conflicts.`,
  conflictTitle: "Conflicting rules",
  conflictDescription: (values: string) => `These items appear in both work and leisure: ${values}`,
  matchingHelp:
    "Process names match exactly, ignoring case and a trailing .exe. Window titles contain the keyword, ignoring case. For example, classify your browser as work and use video-site title keywords to recognize leisure.",
  pendingWarning:
    "Text is still waiting in an activity field. Press Enter or Add, or clear it before saving.",
};

export const ACTIVITY_COPY = { zh, en };
