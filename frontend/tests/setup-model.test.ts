import { expect, test } from "vitest"

import {
  createProfileDraft,
  isNonNegativeInteger,
  parseNumberInput,
  profileFingerprint,
  validationIssueField,
} from "../src/setup/model.ts"
import { stepFingerprint, stepForIssue } from "../src/setup/flow.ts"

test("number input parsing preserves valid and invalid numeric edits", () => {
  expect(parseNumberInput("42")).toBe(42)
  expect(parseNumberInput("1.5")).toBe(1.5)
  expect(parseNumberInput("-1")).toBe(-1)
  expect(parseNumberInput("")).toBeNull()
})

test("disturbance values must be non-negative integers", () => {
  expect(isNonNegativeInteger(0)).toBe(true)
  expect(isNonNegativeInteger(42)).toBe(true)
  expect(isNonNegativeInteger(1.5)).toBe(false)
  expect(isNonNegativeInteger(-1)).toBe(false)
  expect(isNonNegativeInteger(null)).toBe(false)
})

test("server validation paths map to setup fields", () => {
  expect(validationIssueField(["weather", "api_key"])).toBe("weather.api_key")
  expect(validationIssueField(["weather", "location", "latitude"])).toBe("weather.location.latitude")
  expect(validationIssueField(["activity", "work_processes", 0])).toBe("activity")
  expect(validationIssueField(["scenes", "day_work"])).toBe("scenes")
})

test("server validation paths map to the owning setup step", () => {
  expect(stepForIssue(["wallpaper_engine_path"])).toBe("wallpaper")
  expect(stepForIssue(["weather", "api_key"])).toBe("weather")
  expect(stepForIssue(["weather", "location"])).toBe("weather")
  expect(stepForIssue(["scenes"])).toBe("scenes")
  expect(stepForIssue(["disturbance", "startup_grace_seconds"])).toBe("scheduling")
  expect(stepForIssue(["activity"])).toBe("activity")
})

test("scene fingerprints ignore map key order, so restoring a binding stays clean", () => {
  const base = createProfileDraft(null, "zh")
  const original = {
    ...base,
    scenes: { day_work: "CASUAL_ANIME", night_leisure: "NIGHT_CITY" },
  }
  const restored = {
    ...base,
    scenes: { night_leisure: "NIGHT_CITY", day_work: "CASUAL_ANIME" },
  }
  expect(profileFingerprint(restored)).toBe(profileFingerprint(original))
  expect(stepFingerprint(restored, "scenes")).toBe(
    stepFingerprint(original, "scenes"),
  )
})
