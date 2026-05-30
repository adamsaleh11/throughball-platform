import { hostCities } from "@/lib/reference-data";

export const CITY_DASHBOARD_STORAGE_KEY = "throughball:last-city-dashboard-city";
export const DEFAULT_CITY_ID = hostCities[0].id;

export function isKnownHostCity(cityId: string): boolean {
  return hostCities.some((city) => city.id === cityId);
}

export function resolveDashboardCityId(
  profileCityId?: string | null,
  storedCityId?: string | null
): string {
  if (profileCityId && isKnownHostCity(profileCityId)) return profileCityId;
  if (storedCityId && isKnownHostCity(storedCityId)) return storedCityId;
  return DEFAULT_CITY_ID;
}

export function cityVisualClass(cityId: string): string {
  const index = Math.abs(hashString(cityId)) % 4;
  return [
    "from-emerald-900 via-zinc-900 to-stone-700",
    "from-sky-950 via-zinc-900 to-emerald-800",
    "from-rose-950 via-zinc-900 to-amber-800",
    "from-zinc-950 via-slate-800 to-teal-800",
  ][index];
}

function hashString(input: string): number {
  return input.split("").reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) | 0, 0);
}

export type TonightWindow = {
  startsAfter: string;
  startsBefore: string;
};

export function buildCityTonightWindow(timezone: string, now = new Date()): TonightWindow | null {
  if (!isValidTimezone(timezone)) return null;

  const cityDate = localDateParts(now, timezone);
  const start = zonedLocalTimeToUtc(
    cityDate.year,
    cityDate.month,
    cityDate.day,
    18,
    0,
    timezone
  );
  const nextDay = new Date(Date.UTC(cityDate.year, cityDate.month - 1, cityDate.day + 1));
  const nextCityDate = localDateParts(nextDay, "UTC");
  const end = zonedLocalTimeToUtc(
    nextCityDate.year,
    nextCityDate.month,
    nextCityDate.day,
    6,
    0,
    timezone
  );

  return {
    startsAfter: start.toISOString(),
    startsBefore: end.toISOString(),
  };
}

function isValidTimezone(timezone: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: timezone }).format(new Date());
    return true;
  } catch {
    return false;
  }
}

function localDateParts(date: Date, timezone: string): { year: number; month: number; day: number } {
  const parts = new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    month: "2-digit",
    timeZone: timezone,
    year: "numeric",
  }).formatToParts(date);

  return {
    year: Number(parts.find((part) => part.type === "year")?.value),
    month: Number(parts.find((part) => part.type === "month")?.value),
    day: Number(parts.find((part) => part.type === "day")?.value),
  };
}

function zonedLocalTimeToUtc(
  year: number,
  month: number,
  day: number,
  hour: number,
  minute: number,
  timezone: string
): Date {
  const assumedUtc = new Date(Date.UTC(year, month - 1, day, hour, minute));
  const offsetMs = timezoneOffsetMs(assumedUtc, timezone);
  return new Date(assumedUtc.getTime() - offsetMs);
}

function timezoneOffsetMs(date: Date, timezone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    hour: "2-digit",
    hour12: false,
    minute: "2-digit",
    month: "2-digit",
    second: "2-digit",
    timeZone: timezone,
    year: "numeric",
  }).formatToParts(date);

  const getPart = (type: string) => Number(parts.find((part) => part.type === type)?.value);
  const asUtc = Date.UTC(
    getPart("year"),
    getPart("month") - 1,
    getPart("day"),
    getPart("hour") === 24 ? 0 : getPart("hour"),
    getPart("minute"),
    getPart("second")
  );

  return asUtc - date.getTime();
}
