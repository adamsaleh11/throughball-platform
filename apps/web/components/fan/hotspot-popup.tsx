import type { Hotspot } from "@/lib/api/fan";
import { ConfidenceBadge } from "./confidence-badge";

type Props = {
  hotspot: Hotspot;
};

export function HotspotPopup({ hotspot }: Props) {
  const factors = Object.entries(hotspot.ranking_factors ?? {});
  const updatedAt = new Date(hotspot.updated_at).toLocaleString();

  return (
    <div className="min-w-[200px] space-y-2 p-1 font-mono text-sm">
      <div className="flex items-start justify-between gap-2">
        <span className="font-semibold leading-snug">{hotspot.area_label}</span>
        <ConfidenceBadge confidence={hotspot.confidence} />
      </div>

      <p className="text-xs text-muted-foreground">
        {hotspot.supporter_count} signals
      </p>

      <div>
        {factors.length > 0 ? (
          <ul className="space-y-0.5">
            {factors.map(([key, value]) => (
              <li key={key} className="flex gap-1 text-xs text-muted-foreground">
                <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                <span>{String(value)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">
            No additional evidence available.
          </p>
        )}
      </div>

      <p className="text-xs text-muted-foreground">Updated {updatedAt}</p>
    </div>
  );
}
