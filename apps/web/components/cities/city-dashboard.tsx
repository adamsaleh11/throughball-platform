"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  Building2,
  CalendarClock,
  ChevronLeft,
  ExternalLink,
  Landmark,
  MapPin,
  MessageSquare,
  RefreshCw,
  Sparkles,
  UsersRound,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  fetchCity,
  fetchCityEvents,
  fetchCityMatches,
  fetchCityTouristSpots,
  fetchCityVenues,
  type City,
  type CityEvent,
  type MatchSummary,
  type TouristSpot,
  type Venue,
} from "@/lib/api/city-guide";
import { fetchHotspots, type Hotspot } from "@/lib/api/fan";
import {
  buildCityTonightWindow,
  CITY_DASHBOARD_STORAGE_KEY,
  cityVisualClass,
  isKnownHostCity,
} from "@/lib/city-dashboard";
import { cn } from "@/lib/utils";
import { hostCities } from "@/lib/reference-data";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

type CityDashboardProps = {
  cityId: string;
};

const queryOptions = {
  retry: false,
  refetchOnWindowFocus: false,
  refetchInterval: false,
  staleTime: 5 * 60 * 1000,
} as const;

const sortedCities = [...hostCities].sort((a, b) => a.name.localeCompare(b.name));

export function CityDashboard({ cityId }: CityDashboardProps) {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const [conciergeOpen, setConciergeOpen] = useState(false);
  const knownCity = isKnownHostCity(cityId);

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setAuthChecked(true);
      return;
    }

    const supabase = createSupabaseBrowserClient();
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setAuthChecked(true);
    });
  }, [router]);

  useEffect(() => {
    if (knownCity) localStorage.setItem(CITY_DASHBOARD_STORAGE_KEY, cityId);
  }, [cityId, knownCity]);

  const cityQuery = useQuery({
    queryKey: ["city-guide", cityId, "detail"],
    queryFn: () => fetchCity(cityId),
    enabled: authChecked && knownCity,
    ...queryOptions,
  });

  const city = cityQuery.data?.city;
  const tonightWindow = useMemo(
    () => (city?.timezone ? buildCityTonightWindow(city.timezone) : null),
    [city?.timezone]
  );

  const matchesQuery = useQuery({
    queryKey: ["city-guide", cityId, "matches"],
    queryFn: () => fetchCityMatches(cityId),
    enabled: authChecked && knownCity && cityQuery.isSuccess,
    ...queryOptions,
  });

  const hotspotsQuery = useQuery({
    queryKey: ["city-guide", cityId, "hotspots"],
    queryFn: () => fetchHotspots(cityId),
    enabled: authChecked && knownCity && cityQuery.isSuccess,
    ...queryOptions,
  });

  const venuesQuery = useQuery({
    queryKey: ["city-guide", cityId, "venues"],
    queryFn: () => fetchCityVenues(cityId),
    enabled: authChecked && knownCity && cityQuery.isSuccess,
    ...queryOptions,
  });

  const eventsQuery = useQuery({
    queryKey: ["city-guide", cityId, "events-tonight", tonightWindow],
    queryFn: () =>
      fetchCityEvents(cityId, {
        startsAfter: tonightWindow?.startsAfter,
        startsBefore: tonightWindow?.startsBefore,
        pageSize: 6,
      }),
    enabled: authChecked && knownCity && cityQuery.isSuccess && Boolean(tonightWindow),
    ...queryOptions,
  });

  const touristSpotsQuery = useQuery({
    queryKey: ["city-guide", cityId, "tourist-spots"],
    queryFn: () => fetchCityTouristSpots(cityId),
    enabled: authChecked && knownCity && cityQuery.isSuccess,
    ...queryOptions,
  });

  function handleCityChange(nextCityId: string) {
    localStorage.setItem(CITY_DASHBOARD_STORAGE_KEY, nextCityId);
    router.push(`/app/cities/${nextCityId}`);
  }

  if (!authChecked) return null;

  if (!knownCity) {
    return <CityNotFoundShell cityId={cityId} onCityChange={handleCityChange} />;
  }

  if (cityQuery.isLoading) {
    return (
      <DashboardShell cityId={cityId} onCityChange={handleCityChange} title="Host City">
        <div className="space-y-4">
          <div className="h-52 rounded-md bg-muted" />
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="h-48 rounded-md bg-muted" />
            <div className="h-48 rounded-md bg-muted" />
            <div className="h-48 rounded-md bg-muted" />
          </div>
        </div>
      </DashboardShell>
    );
  }

  if (cityQuery.isError || !city) {
    return (
      <DashboardShell cityId={cityId} onCityChange={handleCityChange} title="Host City">
        <FullPageState
          icon={<AlertTriangle className="h-8 w-8 text-muted-foreground" aria-hidden="true" />}
          title="Could not load city"
          body="This host city is supported, but the city guide API did not return its details."
          action={
            <Button className="gap-2" onClick={() => cityQuery.refetch()} variant="secondary">
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Retry
            </Button>
          }
        />
      </DashboardShell>
    );
  }

  const matches = [...(matchesQuery.data?.matches ?? [])].sort(
    (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
  );
  const hotspots = [...(hotspotsQuery.data?.hotspots ?? [])].sort((a, b) => b.score - a.score);
  const venues = venuesQuery.data?.venues ?? [];
  const events = eventsQuery.data?.events ?? [];
  const touristSpots = touristSpotsQuery.data?.tourist_spots ?? [];

  return (
    <DashboardShell cityId={cityId} onCityChange={handleCityChange} title="Host City">
      <CityHero
        city={city}
        eventCount={events.length}
        hotspotCount={hotspots.length}
        matchCount={matches.length}
        touristSpotCount={touristSpots.length}
        venueCount={venues.length}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.85fr)]">
        <div className="space-y-4">
          <UpcomingMatchesSection
            error={matchesQuery.isError}
            isLoading={matchesQuery.isLoading}
            matches={matches}
            onRetry={() => matchesQuery.refetch()}
          />
          <HotspotsSection
            error={hotspotsQuery.isError}
            hotspots={hotspots}
            isLoading={hotspotsQuery.isLoading}
            onRetry={() => hotspotsQuery.refetch()}
          />
          <VenuesSection
            error={venuesQuery.isError}
            isLoading={venuesQuery.isLoading}
            onRetry={() => venuesQuery.refetch()}
            venues={venues}
          />
        </div>
        <div className="space-y-4">
          <ConciergePanel open={conciergeOpen} onToggle={() => setConciergeOpen((open) => !open)} />
          <EventsTonightSection
            city={city}
            error={eventsQuery.isError}
            events={events}
            isLoading={eventsQuery.isLoading}
            onRetry={() => eventsQuery.refetch()}
            tonightWindow={tonightWindow}
          />
          <TouristSpotsSection
            error={touristSpotsQuery.isError}
            isLoading={touristSpotsQuery.isLoading}
            onRetry={() => touristSpotsQuery.refetch()}
            touristSpots={touristSpots}
          />
        </div>
      </div>
    </DashboardShell>
  );
}

function DashboardShell({
  children,
  cityId,
  onCityChange,
  title,
}: {
  children: ReactNode;
  cityId: string;
  onCityChange: (cityId: string) => void;
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
            <p className="text-xs text-muted-foreground">City guide intelligence</p>
          </div>
          <label htmlFor="city-dashboard-select" className="sr-only">
            Select host city
          </label>
          <select
            id="city-dashboard-select"
            value={isKnownHostCity(cityId) ? cityId : ""}
            onChange={(event) => onCityChange(event.target.value)}
            className="h-9 max-w-full rounded-md border border-border bg-background px-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {!isKnownHostCity(cityId) ? <option value="">Select city</option> : null}
            {sortedCities.map((city) => (
              <option key={city.id} value={city.id}>
                {city.name}
              </option>
            ))}
          </select>
        </header>
          {children}
      </section>
    </main>
  );
}

function CityHero({
  city,
  eventCount,
  hotspotCount,
  matchCount,
  touristSpotCount,
  venueCount,
}: {
  city: City;
  eventCount: number;
  hotspotCount: number;
  matchCount: number;
  touristSpotCount: number;
  venueCount: number;
}) {
  return (
    <section className={cn("overflow-hidden rounded-md bg-gradient-to-br p-5 text-white", cityVisualClass(city.city_id))}>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="min-w-0">
          <p className="text-xs uppercase text-white/70">{city.country_code}</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-normal md:text-4xl">{city.name}</h2>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-white/80">
            {city.stadium_name ? (
              <span className="rounded-md border border-white/20 bg-white/10 px-2 py-1">{city.stadium_name}</span>
            ) : null}
            {city.timezone ? (
              <span className="rounded-md border border-white/20 bg-white/10 px-2 py-1">{city.timezone}</span>
            ) : null}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5 lg:w-[520px]">
          <Metric label="Matches" value={matchCount} />
          <Metric label="Hotspots" value={hotspotCount} />
          <Metric label="Venues" value={venueCount} />
          <Metric label="Tonight" value={eventCount} />
          <Metric label="Spots" value={touristSpotCount} />
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-white/20 bg-white/10 p-3">
      <p className="text-xl font-semibold">{value}</p>
      <p className="mt-1 text-[11px] text-white/70">{label}</p>
    </div>
  );
}

function UpcomingMatchesSection({
  error,
  isLoading,
  matches,
  onRetry,
}: {
  error: boolean;
  isLoading: boolean;
  matches: MatchSummary[];
  onRetry: () => void;
}) {
  return (
    <DashboardSection
      action={error ? <RetryButton onRetry={onRetry} /> : null}
      icon={<CalendarClock className="h-4 w-4" aria-hidden="true" />}
      title="Upcoming matches"
    >
      <SectionBody
        emptyBody="No matches are currently seeded for this city."
        emptyTitle="No matches yet"
        error={error}
        errorTitle="Could not load matches"
        isEmpty={matches.length === 0}
        isLoading={isLoading}
      >
        <div className="space-y-2">
          {matches.slice(0, 5).map((match) => (
            <div className="rounded-md border border-border p-3" key={match.match_id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    {match.home_team ?? "TBD"} vs {match.away_team ?? "TBD"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{match.competition}</p>
                </div>
                <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                  {formatDateTime(match.starts_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </SectionBody>
    </DashboardSection>
  );
}

function HotspotsSection({
  error,
  hotspots,
  isLoading,
  onRetry,
}: {
  error: boolean;
  hotspots: Hotspot[];
  isLoading: boolean;
  onRetry: () => void;
}) {
  return (
    <DashboardSection
      action={
        <div className="flex items-center gap-2">
          {error ? <RetryButton onRetry={onRetry} /> : null}
          <Button asChild className="h-8 gap-1.5 px-2.5 text-xs" variant="secondary">
            <Link href="/app/heatmap" title="Full heatmap available on the Fan Heatmap page">
              <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
              Full heatmap
            </Link>
          </Button>
        </div>
      }
      icon={<UsersRound className="h-4 w-4" aria-hidden="true" />}
      title="Fan hotspots"
    >
      <SectionBody
        emptyBody="No supporter activity is recorded for this city yet."
        emptyTitle="No hotspots yet"
        error={error}
        errorTitle="Could not load hotspots"
        isEmpty={hotspots.length === 0}
        isLoading={isLoading}
      >
        <div className="grid gap-2 md:grid-cols-2">
          {hotspots.slice(0, 4).map((hotspot) => (
            <div className="rounded-md border border-border p-3" key={hotspot.hotspot_id}>
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium">{hotspot.area_label}</p>
                <span className="rounded-md bg-primary/10 px-2 py-1 text-xs text-primary">
                  {Math.round(hotspot.score)}
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {hotspot.supporter_count} supporters · {Math.round(hotspot.confidence * 100)}% confidence
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Updated {formatDateTime(hotspot.updated_at)}</p>
            </div>
          ))}
        </div>
      </SectionBody>
    </DashboardSection>
  );
}

function VenuesSection({
  error,
  isLoading,
  onRetry,
  venues,
}: {
  error: boolean;
  isLoading: boolean;
  onRetry: () => void;
  venues: Venue[];
}) {
  return (
    <DashboardSection
      action={error ? <RetryButton onRetry={onRetry} /> : null}
      icon={<Building2 className="h-4 w-4" aria-hidden="true" />}
      title="Venues"
    >
      <SectionBody
        emptyBody="No sourced venue records are available for this city yet."
        emptyTitle="No venues yet"
        error={error}
        errorTitle="Could not load venues"
        isEmpty={venues.length === 0}
        isLoading={isLoading}
      >
        <div className="grid gap-2 md:grid-cols-2">
          {venues.slice(0, 6).map((venue) => (
            <SourceCard
              key={venue.venue_id}
              name={venue.name}
              sourceName={venue.source_name}
              sourceUrl={venue.source_url}
              subtitle={[formatLabel(venue.venue_type), venue.area_label].filter(Boolean).join(" · ")}
              tags={[...venue.amenities.slice(0, 2), ...venue.tags.slice(0, 2)]}
            />
          ))}
        </div>
      </SectionBody>
    </DashboardSection>
  );
}

function EventsTonightSection({
  city,
  error,
  events,
  isLoading,
  onRetry,
  tonightWindow,
}: {
  city: City;
  error: boolean;
  events: CityEvent[];
  isLoading: boolean;
  onRetry: () => void;
  tonightWindow: { startsAfter: string; startsBefore: string } | null;
}) {
  return (
    <DashboardSection
      action={error ? <RetryButton onRetry={onRetry} /> : null}
      icon={<CalendarClock className="h-4 w-4" aria-hidden="true" />}
      title="Events tonight"
    >
      {!city.timezone || !tonightWindow ? (
        <EmptyState
          body="This city is missing timezone data, so the dashboard will not guess at tonight's event window."
          title="Event timing unavailable"
        />
      ) : (
        <SectionBody
          emptyBody="No sourced events are scheduled in the city-local tonight window."
          emptyTitle="No events tonight"
          error={error}
          errorTitle="Could not load events"
          isEmpty={events.length === 0}
          isLoading={isLoading}
        >
          <div className="space-y-2">
            {events.slice(0, 6).map((event) => (
              <SourceCard
                key={event.event_id}
                name={event.title}
                sourceName={event.source_name}
                sourceUrl={event.source_url}
                subtitle={[formatLabel(event.event_type), event.area_label, event.starts_at ? formatDateTime(event.starts_at) : ""]
                  .filter(Boolean)
                  .join(" · ")}
                tags={event.tags.slice(0, 4)}
              />
            ))}
          </div>
        </SectionBody>
      )}
    </DashboardSection>
  );
}

function TouristSpotsSection({
  error,
  isLoading,
  onRetry,
  touristSpots,
}: {
  error: boolean;
  isLoading: boolean;
  onRetry: () => void;
  touristSpots: TouristSpot[];
}) {
  return (
    <DashboardSection
      action={error ? <RetryButton onRetry={onRetry} /> : null}
      icon={<Landmark className="h-4 w-4" aria-hidden="true" />}
      title="Tourist spots"
    >
      <SectionBody
        emptyBody="No sourced tourist spot records are available for this city yet."
        emptyTitle="No tourist spots yet"
        error={error}
        errorTitle="Could not load tourist spots"
        isEmpty={touristSpots.length === 0}
        isLoading={isLoading}
      >
        <div className="space-y-2">
          {touristSpots.slice(0, 5).map((spot) => (
            <SourceCard
              key={spot.spot_id}
              name={spot.name}
              sourceName={spot.source_name}
              sourceUrl={spot.source_url}
              subtitle={[formatLabel(spot.spot_type), spot.area_label].filter(Boolean).join(" · ")}
              tags={spot.tags.slice(0, 4)}
            />
          ))}
        </div>
      </SectionBody>
    </DashboardSection>
  );
}

function ConciergePanel({ onToggle, open }: { onToggle: () => void; open: boolean }) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
          <Bot className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold">AI concierge</h3>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">Entry point staged for a later integration.</p>
        </div>
        <Button className="h-8 gap-1.5 px-2.5 text-xs" onClick={onToggle} type="button" variant="secondary">
          <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
          Open
        </Button>
      </div>
      {open ? (
        <div className="mt-4 rounded-md border border-dashed border-border bg-muted/40 p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Concierge ready for Phase 06
          </div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            No AI request is connected from this dashboard entry.
          </p>
        </div>
      ) : null}
    </section>
  );
}

function DashboardSection({
  action,
  children,
  icon,
  title,
}: {
  action?: ReactNode;
  children: ReactNode;
  icon: ReactNode;
  title: string;
}) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">{icon}</div>
        <h3 className="min-w-0 flex-1 text-sm font-semibold">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function SectionBody({
  children,
  emptyBody,
  emptyTitle,
  error,
  errorTitle,
  isEmpty,
  isLoading,
}: {
  children: ReactNode;
  emptyBody: string;
  emptyTitle: string;
  error: boolean;
  errorTitle: string;
  isEmpty?: boolean;
  isLoading: boolean;
}) {
  if (isLoading) return <SectionSkeleton />;
  if (error) return <EmptyState body="Check the API connection and retry this section." title={errorTitle} />;
  if (isEmpty) return <EmptyState body={emptyBody} title={emptyTitle} />;
  return children;
}

function SectionSkeleton() {
  return (
    <div className="space-y-2">
      <div className="h-16 rounded-md bg-muted" />
      <div className="h-16 rounded-md bg-muted" />
    </div>
  );
}

function EmptyState({ body, title }: { body: string; title: string }) {
  return (
    <div className="rounded-md border border-dashed border-border bg-muted/30 p-4">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{body}</p>
    </div>
  );
}

function FullPageState({
  action,
  body,
  icon,
  title,
}: {
  action?: ReactNode;
  body: string;
  icon: ReactNode;
  title: string;
}) {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center justify-center rounded-md border border-border p-8 text-center">
      {icon}
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

function CityNotFoundShell({
  cityId,
  onCityChange,
}: {
  cityId: string;
  onCityChange: (cityId: string) => void;
}) {
  return (
    <DashboardShell cityId={cityId} onCityChange={onCityChange} title="Host City">
      <FullPageState
        icon={<AlertTriangle className="h-8 w-8 text-muted-foreground" aria-hidden="true" />}
        title="City not found"
        body="This city is not in the supported World Cup host city catalog."
        action={
          <div className="flex max-h-56 flex-wrap justify-center gap-2 overflow-y-auto">
            {sortedCities.slice(0, 8).map((city) => (
              <Button asChild className="h-8 px-3 text-xs" key={city.id} variant="secondary">
                <Link href={`/app/cities/${city.id}`}>{city.name}</Link>
              </Button>
            ))}
          </div>
        }
      />
    </DashboardShell>
  );
}

function SourceCard({
  name,
  sourceName,
  sourceUrl,
  subtitle,
  tags,
}: {
  name: string;
  sourceName: string;
  sourceUrl: string;
  subtitle: string;
  tags: string[];
}) {
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">{name}</p>
          {subtitle ? <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p> : null}
        </div>
        <a
          aria-label={`Source for ${name}`}
          className="shrink-0 text-muted-foreground hover:text-foreground"
          href={sourceUrl}
          rel="noreferrer"
          target="_blank"
        >
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
        </a>
      </div>
      {tags.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span className="rounded-full border border-border px-2 py-0.5 text-[11px] text-muted-foreground" key={tag}>
              {formatLabel(tag)}
            </span>
          ))}
        </div>
      ) : null}
      <p className="mt-3 text-[11px] text-muted-foreground">Source: {sourceName}</p>
    </div>
  );
}

function RetryButton({ onRetry }: { onRetry: () => void }) {
  return (
    <Button className="h-8 gap-1.5 px-2.5 text-xs" onClick={onRetry} type="button" variant="secondary">
      <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
      Retry
    </Button>
  );
}

function formatLabel(value: string): string {
  return value.replace(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
