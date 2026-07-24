import taigaAhead from "../assets/taiga-status/taiga-status-ahead.webp";
import taigaBehind from "../assets/taiga-status/taiga-status-behind.webp";
import taigaOnSchedule from "../assets/taiga-status/taiga-status-on-schedule.webp";

export type ScheduleStatus = "ahead" | "on_schedule" | "behind" | "unknown";

export type MissionProgress = {
  completed: number | null;
  total: number;
  percentage: number | null;
  scheduleStatus: ScheduleStatus;
  label: string;
  message: string;
  imageSrc: string | null;
  imageAlt: string;
};

const totalWeeks = 28;

export const scheduleStatusLabels: Record<ScheduleStatus, string> = {
  ahead: "予定より先行",
  on_schedule: "予定どおり",
  behind: "予定より遅れ",
  unknown: "判定不可",
};

export const scheduleStatusMessages: Record<ScheduleStatus, string> = {
  ahead: "予定より先行しています",
  on_schedule: "予定どおり進んでいます",
  behind: "予定より遅れています",
  unknown: "進捗状況を判定できません",
};

const statusImages: Record<Exclude<ScheduleStatus, "unknown">, { src: string; alt: string }> = {
  ahead: { src: taigaAhead, alt: "予定より先行している状態" },
  on_schedule: { src: taigaOnSchedule, alt: "予定どおり進んでいる状態" },
  behind: { src: taigaBehind, alt: "予定より遅れている状態" },
};

export function calculateMissionProgress(
  completedWeeks?: number | null,
  options: { totalWeeks?: number } = {},
): MissionProgress {
  const missionTotal = options.totalWeeks ?? totalWeeks;
  if (
    completedWeeks === null ||
    completedWeeks === undefined ||
    Number.isNaN(completedWeeks) ||
    !Number.isFinite(completedWeeks) ||
    missionTotal <= 0
  ) {
    return {
      completed: null,
      total: Math.max(missionTotal, 0),
      percentage: null,
      scheduleStatus: "unknown",
      label: scheduleStatusLabels.unknown,
      message: scheduleStatusMessages.unknown,
      imageSrc: null,
      imageAlt: "",
    };
  }

  const completed = Math.min(Math.max(Math.round(completedWeeks), 0), missionTotal);
  const percentage = Math.round((completed / missionTotal) * 100);
  const scheduleStatus = resolveScheduleStatus(completed);
  const image = statusImages[scheduleStatus];

  return {
    completed,
    total: missionTotal,
    percentage,
    scheduleStatus,
    label: scheduleStatusLabels[scheduleStatus],
    message: scheduleStatusMessages[scheduleStatus],
    imageSrc: image.src,
    imageAlt: image.alt,
  };
}

function resolveScheduleStatus(completedWeeks: number): Exclude<ScheduleStatus, "unknown"> {
  if (completedWeeks >= 20) {
    return "ahead";
  }
  if (completedWeeks >= 1) {
    return "on_schedule";
  }
  return "behind";
}
