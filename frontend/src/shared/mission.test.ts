import { describe, expect, it } from "vitest";

import { calculateMissionProgress } from "./mission";

describe("Mission Progress", () => {
  it("calculates accessible schedule status variants", () => {
    expect(calculateMissionProgress(24)).toMatchObject({
      completed: 24,
      percentage: 86,
      scheduleStatus: "ahead",
      label: "予定より先行",
      imageAlt: "予定より先行している状態",
    });
    expect(calculateMissionProgress(7)).toMatchObject({
      percentage: 25,
      scheduleStatus: "on_schedule",
      label: "予定どおり",
    });
    expect(calculateMissionProgress(0)).toMatchObject({
      percentage: 0,
      scheduleStatus: "behind",
      label: "予定より遅れ",
    });
  });

  it("handles boundaries and missing authoritative data", () => {
    expect(calculateMissionProgress(100)).toMatchObject({ completed: 28, percentage: 100 });
    expect(calculateMissionProgress(-4)).toMatchObject({ completed: 0, percentage: 0 });
    expect(calculateMissionProgress(undefined)).toMatchObject({
      completed: null,
      percentage: null,
      scheduleStatus: "unknown",
      imageSrc: null,
    });
  });
});
