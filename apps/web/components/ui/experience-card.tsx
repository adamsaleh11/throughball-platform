import { cn } from "@/lib/utils";

interface ExperienceCardProps {
  id: string;
  title: string;
  description: string;
  selected: boolean;
  onToggle: (id: string) => void;
}

export function ExperienceCard({ id, title, description, selected, onToggle }: ExperienceCardProps) {
  return (
    <button
      aria-pressed={selected}
      className={cn(
        "flex flex-col gap-2 rounded-lg border-2 p-4 text-left transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        selected
          ? "border-primary bg-primary/5"
          : "border-border bg-background hover:border-primary/40 hover:bg-muted/50"
      )}
      onClick={() => onToggle(id)}
      type="button"
    >
      <span className="text-sm font-semibold leading-snug">{title}</span>
      <span className="text-xs leading-snug text-muted-foreground">{description}</span>
    </button>
  );
}
