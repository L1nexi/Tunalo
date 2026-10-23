import type { Locale } from "@/api/profile";
import type { DisturbancePreset } from "@/setup/profile/model";

const zh = {
  title: "调整调度风格",
  description: "",
  responseTitle: "情境偏好",
  responseDescription: "拖动情境或使用旁边的下拉菜单调整。越靠上越优先，同层并列。",
  noPriorityHelp: "不设置优先级时，Tunalo 会综合当前情境选择合适的场景。",
  cascadeHelp:
    "从上往下寻找明显的情境和可用场景；找到后优先响应这一层，否则继续下一层。都未命中时，综合当前情境选择。",
  unassignedHelp: "仍参与场景判断，但不指定响应顺序。",
  allAssigned: "所有情境均已设置优先级。",
  moveToNewLayer: "移到新优先级",
  unassigned: "未指定优先级",
  addLayer: "添加层级",
  layer: (number: number) => `第 ${number} 优先级`,
  dropHere: "将情境移到这里；空层不会保存。",
  dragVariable: (name: string) => `拖动${name}`,
  moveVariable: (name: string) => `移动${name}到`,
  moved: (name: string, destination: string) => `${name}已移到${destination}`,
  moveLayerUp: (number: number) => `上移第 ${number} 优先级`,
  moveLayerDown: (number: number) => `下移第 ${number} 优先级`,
  removeLayer: (number: number) => `删除第 ${number} 优先级`,
  layerMoved: (before: number, after: number) => `第 ${before} 优先级已移到第 ${after} 位`,
  layerRemoved: "已删除层级，其中的情境已放回未指定优先级。",
  invalidPreferences: "请检查情境偏好，每项情境只能出现一次。",
  disturbanceTitle: "防打扰程度",
  disturbanceDescription: "调节调度器执行壁纸切换时的防打扰程度。",
  timingSummary: (startup: number | null, idle: number | null, cycle: number | null) =>
    `启动等待 ${startup ?? "—"} 秒；空闲等待 ${idle ?? "—"} 秒；基础轮换间隔 ${cycle ?? "—"} 分钟，推荐变化较大时会提前切换。`,
  fineTune: "自定义防打扰设置",
  startupGrace: "启动等待",
  idleBeforeSwitch: "空闲等待",
  cycleInterval: "基础轮换间隔",
  seconds: "秒",
  minutes: "分钟",
  nonNegative: "请输入不小于 0 的整数。",
};

const en = {
  title: "Tune scheduling",
  description: "Choose context priorities and interruption settings.",
  responseTitle: "Context preferences",
  responseDescription:
    "Drag contexts or use their menus. Higher levels come first; contexts in one level share priority.",
  noPriorityHelp: "Without explicit priorities, Tunalo uses the current context to choose suitable scenes.",
  cascadeHelp:
    "Tunalo responds to the first level with a clear context and available scenes. If none qualifies, it uses the overall context to choose.",
  unassignedHelp: "Still considered when choosing scenes, without an explicit response order.",
  allAssigned: "All contexts have an explicit priority.",
  moveToNewLayer: "Move to a new priority",
  unassigned: "No explicit priority",
  addLayer: "Add priority level",
  layer: (number: number) => `Priority ${number}`,
  dropHere: "Move a context here. Empty levels are not saved.",
  dragVariable: (name: string) => `Drag ${name}`,
  moveVariable: (name: string) => `Move ${name} to`,
  moved: (name: string, destination: string) => `${name} moved to ${destination}`,
  moveLayerUp: (number: number) => `Move priority ${number} up`,
  moveLayerDown: (number: number) => `Move priority ${number} down`,
  removeLayer: (number: number) => `Remove priority ${number}`,
  layerMoved: (before: number, after: number) => `Priority ${before} moved to position ${after}`,
  layerRemoved: "Priority level removed. Its contexts now have no explicit priority.",
  invalidPreferences: "Check context preferences. Each context can appear only once.",
  disturbanceTitle: "Interruption level",
  disturbanceDescription: "Choose a preset, or expand the exact timing values.",
  timingSummary: (startup: number | null, idle: number | null, cycle: number | null) =>
    `Startup wait ${startup ?? "—"} s; idle wait ${idle ?? "—"} s; baseline rotation interval ${cycle ?? "—"} min, shortened when recommendations change substantially.`,
  fineTune: "Fine-tune timing",
  startupGrace: "Startup wait",
  idleBeforeSwitch: "Idle wait",
  cycleInterval: "Baseline rotation interval",
  seconds: "seconds",
  minutes: "minutes",
  nonNegative: "Enter a non-negative whole number.",
};

export const PREFERENCES_COPY = { zh, en };

export const ZH_TIMING_HINTS = {
  startupGrace: "调度器启动至能够尝试切换的最短等待时间，更高的启动等待时间通常可以增加壁纸选择的稳定性。",
  idleBeforeSwitch:
    "停止操作多久后，允许壁纸切换。更短的空闲等待时间通常可以带来更及时的壁纸响应，但也会增加切换次数。",
  cycleInterval:
    "从上次成功切换起计算。推荐变化很小时按此间隔轮换，变化较大时提前切换；切换仍需通过空闲、全屏和负载检查。",
} as const;

export const DISTURBANCE_LABELS: Record<Locale, Record<DisturbancePreset, string>> = {
  zh: {
    eager: "积极",
    responsive: "灵敏",
    balanced: "平衡",
    quiet: "安静",
    minimal: "最少打扰",
  },
  en: {
    eager: "Eager",
    responsive: "Responsive",
    balanced: "Balanced",
    quiet: "Quiet",
    minimal: "Minimal",
  },
};
