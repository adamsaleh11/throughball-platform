import { cn } from "@/lib/utils";
import { confidenceLevel, CONFIDENCE_STYLES } from "@/lib/heatmap-utils";

type Props = {
  confidence: number;
};

export function ConfidenceBadge({ confidence }: Props) {
  const level = confidenceLevel(confidence);
  const { label, className } = CONFIDENCE_STYLES[level];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        className
      )}
    >
      {label}
    </span>
  );
}
