const MIN_RADIUS = 8;
const RADIUS_SCALE = 8;

export function hotspotRadius(supporterCount: number): number {
  return Math.max(MIN_RADIUS, Math.sqrt(Math.max(0, supporterCount)) * RADIUS_SCALE);
}

// Interpolates between light blue (#93c5fd, score=0) and deep indigo (#3730a3, score=100)
export function scoreColor(score: number): string {
  const t = Math.max(0, Math.min(100, score)) / 100;
  const r = Math.round(147 + (55 - 147) * t);
  const g = Math.round(197 + (48 - 197) * t);
  const b = Math.round(253 + (163 - 253) * t);
  return `rgb(${r},${g},${b})`;
}

export type ConfidenceLevel = "High" | "Medium" | "Low";

export function confidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 0.7) return "High";
  if (confidence >= 0.4) return "Medium";
  return "Low";
}

export const CONFIDENCE_STYLES: Record<
  ConfidenceLevel,
  { label: string; className: string }
> = {
  High: {
    label: "High",
    className: "bg-green-100 text-green-800 border-green-200",
  },
  Medium: {
    label: "Medium",
    className: "bg-amber-100 text-amber-800 border-amber-200",
  },
  Low: {
    label: "Low",
    className: "bg-red-100 text-red-800 border-red-200",
  },
};
