"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Bot,
  CalendarClock,
  ChevronLeft,
  Clock3,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  fetchMatch,
  fetchMatchEvents,
  fetchMatchMomentum,
  fetchMatchStats,
  type MatchDetail,
  type MatchEvent,
  type MatchMomentum,
  type MatchStat,
} from "@/lib/api/matches";
import { cn } from "@/lib/utils";

type MatchDashboardProps = {
  matchId: string;
};

export type Scoreline = {
  home: number;
  away: number;
  complete: boolean;
};

const queryOptions = {
  retry: false,
  refetchOnWindowFocus: false,
  refetchInterval: false,
  staleTime: Infinity,
} as const;

const statRows: Array<{
  label: string;
  value: keyof Pick<
    MatchStat,
    "goals" | "possession_pct" | "shots" | "shots_on_target" | "passes" | "corners" | "fouls"
  >;
  suffix?: string;
}> = [
  { label: "Goals", value: "goals" },
  { label: "Possession", value: "possession_pct", suffix: "%" },
  { label: "Shots", value: "shots" },
  { label: "On target", value: "shots_on_target" },
  { label: "Passes", value: "passes" },
  { label: "Corners", value: "corners" },
  { label: "Fouls", value: "fouls" },
];

export function deriveScoreline(match: MatchDetail, stats: MatchStat[]): Scoreline {
  const home = stats.find((stat) => stat.team_id === match.home_team.team_id);
  const away = stats.find((stat) => stat.team_id === match.away_team.team_id);

  return {
    home: home?.goals ?? 0,
    away: away?.goals ?? 0,
    complete: Boolean(home && away),
  };
}

export function MatchDashboard({ matchId }: MatchDashboardProps) {
  const matchQuery = useQuery({
    queryKey: ["match", matchId, "detail"],
    queryFn: () => fetchMatch(matchId),
    enabled: Boolean(matchId),
    ...queryOptions,
  });

  const statsQuery = useQuery({
    queryKey: ["match", matchId, "stats"],
    queryFn: () => fetchMatchStats(matchId),
    enabled: Boolean(matchId) && matchQuery.isSuccess,
    ...queryOptions,
  });

  const eventsQuery = useQuery({
    queryKey: ["match", matchId, "events"],
    queryFn: () => fetchMatchEvents(matchId),
    enabled: Boolean(matchId) && matchQuery.isSuccess,
    ...queryOptions,
  });

  const momentumQuery = useQuery({
    queryKey: ["match", matchId, "momentum"],
    queryFn: () => fetchMatchMomentum(matchId),
    enabled: Boolean(matchId) && matchQuery.isSuccess,
    ...queryOptions,
  });

  const isRefreshing =
    matchQuery.isFetching || statsQuery.isFetching || eventsQuery.isFetching || momentumQuery.isFetching;

  async function refreshDashboard() {
    await Promise.all([
      matchQuery.refetch(),
      statsQuery.refetch(),
      eventsQuery.refetch(),
      momentumQuery.refetch(),
    ]);
  }

  if (matchQuery.isLoading) {
    return <DashboardShell title="Match Intelligence" rightSlot={<SkeletonButton />} />;
  }

  if (matchQuery.isError || !matchQuery.data) {
    return (
      <DashboardShell title="Match Intelligence">
        <div className="mx-auto flex max-w-xl flex-col items-center justify-center rounded-md border border-border p-8 text-center">
          <ShieldAlert className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
          <h2 className="mt-4 text-lg font-semibold">Match unavailable</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            This match could not be loaded. Check the match link or try again.
          </p>
          <Button className="mt-5 gap-2" onClick={() => matchQuery.refetch()} variant="secondary">
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </div>
      </DashboardShell>
    );
  }

  const match = matchQuery.data.match;
  const stats = statsQuery.data?.stats ?? [];
  const events = eventsQuery.data?.events ?? [];
  const momentum = momentumQuery.data?.momentum ?? [];
  const scoreline = deriveScoreline(match, stats);

  return (
    <DashboardShell
      title="Match Intelligence"
      rightSlot={
        <Button
          className="h-9 gap-1.5 px-3 text-sm"
          disabled={isRefreshing}
          onClick={refreshDashboard}
          variant="secondary"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin")} aria-hidden="true" />
          Refresh
        </Button>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,0.9fr)]">
        <div className="space-y-4">
          <MatchHeader match={match} scoreline={scoreline} />
          <StatsPanel
            error={statsQuery.isError}
            homeTeamId={match.home_team.team_id}
            awayTeamId={match.away_team.team_id}
            stats={stats}
            onRetry={() => statsQuery.refetch()}
          />
          <MomentumPanel error={momentumQuery.isError} momentum={momentum} onRetry={() => momentumQuery.refetch()} />
        </div>
        <div className="space-y-4">
          <AiAnalystPanel />
          <EventTimeline error={eventsQuery.isError} events={events} onRetry={() => eventsQuery.refetch()} />
        </div>
      </div>
    </DashboardShell>
  );
}

function DashboardShell({
  children,
  rightSlot,
  title,
}: {
  children?: ReactNode;
  rightSlot?: ReactNode;
  title: string;
}) {
  return (
    <main className="min-h-screen bg-background px-4 py-5 md:px-6 md:py-7">
      <section className="mx-auto max-w-7xl space-y-5">
        <header className="flex flex-wrap items-center gap-3 border-b border-border pb-4">
          <Link href="/app" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </Link>
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold md:text-lg">{title}</h1>
            <p className="text-xs text-muted-foreground">Seeded match data</p>
          </div>
          {rightSlot}
        </header>
        {children}
      </section>
    </main>
  );
}

function SkeletonButton() {
  return <div className="h-9 w-24 rounded-md bg-muted" aria-hidden="true" />;
}

function MatchHeader({ match, scoreline }: { match: MatchDetail; scoreline: Scoreline }) {
  return (
    <section className="rounded-md border border-border p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs uppercase text-muted-foreground">{formatStage(match.stage)}</p>
          <h2 className="mt-1 text-xl font-semibold md:text-2xl">
            {match.home_team.name} vs {match.away_team.name}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1">
              <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
              {formatDateTime(match.starts_at)}
            </span>
            <span className="rounded-md border border-border px-2 py-1">
              {match.city.name}
              {match.city.stadium_name ? `, ${match.city.stadium_name}` : ""}
            </span>
            <span className="rounded-md border border-border px-2 py-1">{formatStage(match.status)}</span>
          </div>
        </div>
        <div className="w-full rounded-md bg-muted p-4 sm:w-auto sm:min-w-64">
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
            <TeamScore name={match.home_team.name} score={scoreline.home} />
            <span className="text-sm text-muted-foreground">-</span>
            <TeamScore name={match.away_team.name} score={scoreline.away} />
          </div>
          <p className="mt-3 text-center text-xs text-muted-foreground">
            {scoreline.complete ? "Score from match stats" : "Score awaiting complete stats"}
          </p>
        </div>
      </div>
      {match.tags.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {match.tags.map((tag) => (
            <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs text-primary" key={tag}>
              {tag}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TeamScore({ name, score }: { name: string; score: number }) {
  return (
    <div className="min-w-0">
      <p className="truncate text-sm font-medium">{name}</p>
      <p className="mt-1 text-3xl font-semibold">{score}</p>
    </div>
  );
}

function StatsPanel({
  awayTeamId,
  error,
  homeTeamId,
  onRetry,
  stats,
}: {
  awayTeamId: string;
  error: boolean;
  homeTeamId: string;
  onRetry: () => void;
  stats: MatchStat[];
}) {
  const home = stats.find((stat) => stat.team_id === homeTeamId);
  const away = stats.find((stat) => stat.team_id === awayTeamId);

  return (
    <Panel title="Match Stats" icon={<BarChart3 className="h-4 w-4" aria-hidden="true" />}>
      {error ? <SectionError message="Could not load match stats." onRetry={onRetry} /> : null}
      {!error && (!home || !away) ? <EmptyState title="No stats yet" body="Seeded team stats are not available for this match." /> : null}
      {!error && home && away ? (
        <div className="space-y-3">
          <div className="grid grid-cols-[1fr_96px_1fr] text-xs font-medium text-muted-foreground">
            <span>{home.team_name}</span>
            <span className="text-center">Metric</span>
            <span className="text-right">{away.team_name}</span>
          </div>
          {statRows.map((row) => (
            <div className="grid grid-cols-[1fr_96px_1fr] items-center gap-3 text-sm" key={row.value}>
              <span className="font-medium">{formatStatValue(home[row.value], row.suffix)}</span>
              <span className="text-center text-xs text-muted-foreground">{row.label}</span>
              <span className="text-right font-medium">{formatStatValue(away[row.value], row.suffix)}</span>
            </div>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}

function MomentumPanel({
  error,
  momentum,
  onRetry,
}: {
  error: boolean;
  momentum: MatchMomentum[];
  onRetry: () => void;
}) {
  return (
    <Panel title="Momentum" icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}>
      {error ? <SectionError message="Could not load tactical snapshots." onRetry={onRetry} /> : null}
      {!error && momentum.length === 0 ? (
        <EmptyState title="No momentum snapshots" body="No seeded tactical snapshots are available for this match." />
      ) : null}
      {!error && momentum.length > 0 ? <MomentumChart momentum={momentum} /> : null}
    </Panel>
  );
}

function MomentumChart({ momentum }: { momentum: MatchMomentum[] }) {
  const width = 560;
  const height = 180;
  const padding = 28;
  const maxMinute = Math.max(...momentum.map((snapshot) => snapshot.minute), 90);
  const teams = Array.from(new Set(momentum.map((snapshot) => snapshot.team_id)));

  function x(minute: number) {
    return padding + (minute / maxMinute) * (width - padding * 2);
  }

  function y(confidence: number) {
    return height - padding - Math.max(0, Math.min(confidence, 1)) * (height - padding * 2);
  }

  return (
    <div>
      <svg className="h-auto w-full overflow-visible" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Tactical momentum confidence by minute">
        <line x1={padding} x2={width - padding} y1={height - padding} y2={height - padding} className="stroke-border" />
        <line x1={padding} x2={padding} y1={padding} y2={height - padding} className="stroke-border" />
        {[0.25, 0.5, 0.75, 1].map((tick) => (
          <g key={tick}>
            <line x1={padding} x2={width - padding} y1={y(tick)} y2={y(tick)} className="stroke-border/60" />
            <text x={4} y={y(tick) + 4} className="fill-muted-foreground text-[10px]">
              {Math.round(tick * 100)}
            </text>
          </g>
        ))}
        {teams.map((teamId, index) => {
          const teamSnapshots = momentum.filter((snapshot) => snapshot.team_id === teamId);
          return teamSnapshots.map((snapshot) => (
            <circle
              cx={x(snapshot.minute)}
              cy={y(snapshot.confidence)}
              fill={index === 0 ? "hsl(var(--primary))" : "hsl(var(--foreground))"}
              key={snapshot.snapshot_id}
              r="5"
            />
          ));
        })}
      </svg>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {momentum.map((snapshot) => (
          <div className="rounded-md border border-border p-3 text-xs" key={snapshot.snapshot_id}>
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">{snapshot.team_name}</span>
              <span className="text-muted-foreground">{snapshot.minute} min</span>
            </div>
            <p className="mt-2 text-muted-foreground">
              {snapshot.formation}; {snapshot.possession_style}
            </p>
            <p className="mt-1 text-muted-foreground">
              Press {snapshot.press_intensity}; line {snapshot.defensive_line}; confidence{" "}
              {Math.round(snapshot.confidence * 100)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventTimeline({
  error,
  events,
  onRetry,
}: {
  error: boolean;
  events: MatchEvent[];
  onRetry: () => void;
}) {
  return (
    <Panel title="Event Timeline" icon={<Clock3 className="h-4 w-4" aria-hidden="true" />}>
      {error ? <SectionError message="Could not load match events." onRetry={onRetry} /> : null}
      {!error && events.length === 0 ? <EmptyState title="No events yet" body="No seeded timeline events are available for this match." /> : null}
      {!error && events.length > 0 ? (
        <ol className="space-y-3">
          {events.map((event) => (
            <li className="rounded-md border border-border p-3" key={event.event_id}>
              <div className="flex items-start gap-3">
                <span className="w-12 shrink-0 rounded-md bg-muted px-2 py-1 text-center text-xs font-medium">
                  {formatMinute(event)}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    {formatStage(event.event_type)} · {event.team_name}
                  </p>
                  {event.player_name ? <p className="mt-1 text-xs text-muted-foreground">{event.player_name}</p> : null}
                  {event.description ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{event.description}</p> : null}
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </Panel>
  );
}

function AiAnalystPanel() {
  return (
    <Panel title="AI Analyst" icon={<Bot className="h-4 w-4" aria-hidden="true" />}>
      <label className="sr-only" htmlFor="ai-question">
        Ask the AI analyst
      </label>
      <textarea
        className="min-h-24 w-full resize-none rounded-md border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:bg-muted/40"
        disabled
        id="ai-question"
        placeholder="Ask about tactics, players, or match context"
      />
      <div className="mt-3 flex justify-end">
        <span title="Available after Phase 06 integration">
          <Button aria-label="Ask AI analyst" disabled>
            Ask
          </Button>
        </span>
      </div>
    </Panel>
  );
}

function Panel({ children, icon, title }: { children: ReactNode; icon: ReactNode; title: string }) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="mb-4 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-muted text-muted-foreground">{icon}</span>
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ body, title }: { body: string; title: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/40 p-4">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{body}</p>
    </div>
  );
}

function SectionError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-md border border-border p-4">
      <p className="text-sm font-medium">{message}</p>
      <Button className="mt-3 h-8 px-3 text-xs" onClick={onRetry} variant="secondary">
        Retry
      </Button>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatMinute(event: MatchEvent) {
  return event.stoppage_minute ? `${event.minute}+${event.stoppage_minute}'` : `${event.minute}'`;
}

function formatStage(value: string) {
  return value
    .split("_")
    .join(" ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatStatValue(value: number | null, suffix = "") {
  if (value === null) return "N/A";
  return `${Number.isInteger(value) ? value : value.toFixed(1)}${suffix}`;
}
