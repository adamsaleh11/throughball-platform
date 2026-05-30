"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ChevronLeft,
  Copy,
  ListChecks,
  Loader2,
  Map,
  RefreshCw,
  Route,
  Save,
  Send,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchCityMatches, type MatchSummary } from "@/lib/api/city-guide";
import {
  fetchMyItineraries,
  generateItinerary,
  ItineraryApiError,
  type GenerateItineraryStubResponse,
  type Itinerary,
  type ItineraryInput,
  type ItineraryItem,
} from "@/lib/api/itineraries";
import {
  buildItineraryShareUrl,
  cityName,
  defaultItineraryInput,
  findMatchingItinerary,
  itineraryInputKey,
  itineraryInterestOptions,
  itineraryPaceOptions,
  normalizedItineraryInput,
} from "@/lib/itinerary-utils";
import { hostCities } from "@/lib/reference-data";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type GenerationState =
  | { status: "idle" }
  | { status: "blocked"; message: string }
  | { status: "unavailable"; response: GenerateItineraryStubResponse };

const queryOptions = {
  retry: false,
  refetchOnWindowFocus: false,
  refetchInterval: false,
  staleTime: 5 * 60 * 1000,
} as const;

const sortedCities = [...hostCities].sort((a, b) => a.name.localeCompare(b.name));

export function ItineraryWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [authChecked, setAuthChecked] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [formInput, setFormInput] = useState<ItineraryInput>(() => defaultItineraryInput());
  const [selectedItineraryId, setSelectedItineraryId] = useState<string | null>(
    () => searchParams.get("itinerary")
  );
  const [blockedInputKeys, setBlockedInputKeys] = useState<Set<string>>(() => new Set());
  const [generationState, setGenerationState] = useState<GenerationState>({ status: "idle" });
  const [copied, setCopied] = useState(false);
  const [staleSelection, setStaleSelection] = useState(false);

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
      setAccessToken(data.session.access_token);
      setAuthChecked(true);
    });
  }, [router]);

  const historyQuery = useQuery({
    queryKey: ["itineraries", "me", accessToken],
    queryFn: () => fetchMyItineraries(accessToken),
    enabled: authChecked,
    ...queryOptions,
  });

  const matchesQuery = useQuery({
    queryKey: ["itineraries", formInput.city_id, "matches"],
    queryFn: () => fetchCityMatches(formInput.city_id),
    enabled: authChecked && Boolean(formInput.city_id),
    ...queryOptions,
  });

  const generateMutation = useMutation({
    mutationFn: (input: ItineraryInput) => generateItinerary(input, accessToken),
    onError: (error, input) => {
      const inputKey = itineraryInputKey(input);
      if (error instanceof ItineraryApiError && error.status === 501) {
        setBlockedInputKeys((keys) => new Set(keys).add(inputKey));
        setGenerationState({
          status: "unavailable",
          response: error.body as GenerateItineraryStubResponse,
        });
        return;
      }

      setGenerationState({
        status: "blocked",
        message: error instanceof Error ? error.message : "Unable to generate itinerary.",
      });
    },
  });

  const itineraries = useMemo(() => historyQuery.data?.itineraries ?? [], [historyQuery.data?.itineraries]);
  const selectedItinerary =
    itineraries.find((itinerary) => itinerary.itinerary_id === selectedItineraryId) ?? null;
  const matchingItinerary = useMemo(
    () => findMatchingItinerary(formInput, itineraries),
    [formInput, itineraries]
  );
  const currentInputKey = itineraryInputKey(formInput);

  useEffect(() => {
    const requestedId = searchParams.get("itinerary");
    if (requestedId) setSelectedItineraryId(requestedId);
  }, [searchParams]);

  useEffect(() => {
    const requestedId = searchParams.get("itinerary");
    if (!historyQuery.isSuccess || !requestedId) return;

    const found = itineraries.some((itinerary) => itinerary.itinerary_id === requestedId);
    setStaleSelection(!found);
    if (!found) setSelectedItineraryId(null);
  }, [historyQuery.isSuccess, itineraries, searchParams]);

  function updateInput(partial: Partial<ItineraryInput>) {
    setGenerationState({ status: "idle" });
    setFormInput((current) => ({ ...current, ...partial }));
  }

  function toggleInterest(interestId: string) {
    const interests = formInput.interests.includes(interestId)
      ? formInput.interests.filter((interest) => interest !== interestId)
      : [...formInput.interests, interestId];
    updateInput({ interests });
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedInput = normalizedItineraryInput(formInput);
    const matching = findMatchingItinerary(normalizedInput, itineraries);
    const inputKey = itineraryInputKey(normalizedInput);

    if (matching) {
      setSelectedItineraryId(matching.itinerary_id);
      setGenerationState({
        status: "blocked",
        message: "A saved itinerary already matches these inputs.",
      });
      return;
    }

    if (blockedInputKeys.has(inputKey) || generateMutation.isPending) {
      setGenerationState({
        status: "blocked",
        message: "This itinerary request was already submitted for the current inputs.",
      });
      return;
    }

    generateMutation.mutate(normalizedInput);
  }

  async function shareSelectedItinerary() {
    if (!selectedItinerary) return;
    const url = buildItineraryShareUrl(window.location.origin, selectedItinerary.itinerary_id);
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  if (!authChecked) return null;

  return (
    <main className="min-h-screen bg-background px-4 py-5 md:px-6 md:py-7">
      <section className="mx-auto max-w-7xl space-y-5">
        <header className="flex flex-wrap items-center gap-3 border-b border-border pb-4">
          <Link href="/app" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </Link>
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-semibold md:text-lg">Itineraries</h1>
            <p className="text-xs text-muted-foreground">Saved plans and staged generation</p>
          </div>
          <Button
            className="h-9 gap-1.5 px-3 text-sm"
            disabled={!selectedItinerary}
            onClick={shareSelectedItinerary}
            type="button"
            variant="secondary"
          >
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            {copied ? "Copied" : "Share"}
          </Button>
        </header>

        <div className="grid gap-4 xl:grid-cols-[minmax(320px,0.85fr)_minmax(0,1.35fr)]">
          <div className="space-y-4">
            <ItineraryForm
              formInput={formInput}
              isGenerating={generateMutation.isPending}
              matches={matchesQuery.data?.matches ?? []}
              matchesError={matchesQuery.isError}
              matchesLoading={matchesQuery.isLoading}
              matchingItinerary={matchingItinerary}
              onCityChange={(cityId) => updateInput({ city_id: cityId, match_id: null })}
              onInputChange={updateInput}
              onSubmit={handleSubmit}
              onToggleInterest={toggleInterest}
              submittedDuplicate={blockedInputKeys.has(currentInputKey)}
            />
            <GenerationPanel state={generationState} isGenerating={generateMutation.isPending} />
            <SavedItinerariesPanel
              error={historyQuery.isError}
              isLoading={historyQuery.isLoading}
              itineraries={itineraries}
              matchingItineraryId={matchingItinerary?.itinerary_id ?? null}
              onRetry={() => historyQuery.refetch()}
              onSelect={setSelectedItineraryId}
              selectedItineraryId={selectedItineraryId}
              staleSelection={staleSelection}
            />
          </div>

          <div className="space-y-4">
            <ItineraryDetail itinerary={selectedItinerary} />
            <MapPlaceholder itinerary={selectedItinerary} />
          </div>
        </div>
      </section>
    </main>
  );
}

function ItineraryForm({
  formInput,
  isGenerating,
  matches,
  matchesError,
  matchesLoading,
  matchingItinerary,
  onCityChange,
  onInputChange,
  onSubmit,
  onToggleInterest,
  submittedDuplicate,
}: {
  formInput: ItineraryInput;
  isGenerating: boolean;
  matches: MatchSummary[];
  matchesError: boolean;
  matchesLoading: boolean;
  matchingItinerary: Itinerary | null;
  onCityChange: (cityId: string) => void;
  onInputChange: (partial: Partial<ItineraryInput>) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onToggleInterest: (interestId: string) => void;
  submittedDuplicate: boolean;
}) {
  const canGenerate = Boolean(formInput.city_id && formInput.date && formInput.party_size >= 1);

  return (
    <section className="rounded-md border border-border p-4">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted">
          <CalendarClock className="h-4 w-4" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-sm font-semibold">Generate itinerary</h2>
          <p className="text-xs text-muted-foreground">Structured inputs only</p>
        </div>
      </div>

      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="City" htmlFor="itinerary-city">
            <select
              id="itinerary-city"
              value={formInput.city_id}
              onChange={(event) => onCityChange(event.target.value)}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {sortedCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Match" htmlFor="itinerary-match">
            <select
              id="itinerary-match"
              value={formInput.match_id ?? ""}
              onChange={(event) => onInputChange({ match_id: event.target.value || null })}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">No match selected</option>
              {matches.map((match) => (
                <option key={match.match_id} value={match.match_id}>
                  {matchLabel(match)}
                </option>
              ))}
            </select>
          </Field>
        </div>

        {matchesLoading ? <p className="text-xs text-muted-foreground">Loading city matches...</p> : null}
        {matchesError ? <p className="text-xs text-red-600">Could not load matches. Match selection is optional.</p> : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Date" htmlFor="itinerary-date">
            <input
              id="itinerary-date"
              type="date"
              value={formInput.date ?? ""}
              onChange={(event) => onInputChange({ date: event.target.value || null })}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </Field>
          <Field label="Party size" htmlFor="itinerary-party-size">
            <input
              id="itinerary-party-size"
              min={1}
              max={20}
              type="number"
              value={formInput.party_size}
              onChange={(event) => onInputChange({ party_size: Number(event.target.value) })}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </Field>
        </div>

        <fieldset>
          <legend className="mb-2 text-xs font-medium text-muted-foreground">Interests</legend>
          <div className="grid grid-cols-2 gap-2">
            {itineraryInterestOptions.map((interest) => (
              <label
                key={interest.id}
                className={cn(
                  "flex min-h-10 items-center gap-2 rounded-md border border-border px-3 py-2 text-sm",
                  formInput.interests.includes(interest.id) && "border-primary/40 bg-primary/10 text-primary"
                )}
              >
                <input
                  checked={formInput.interests.includes(interest.id)}
                  className="h-4 w-4"
                  onChange={() => onToggleInterest(interest.id)}
                  type="checkbox"
                />
                <span>{interest.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-xs font-medium text-muted-foreground">Pace</legend>
          <div className="grid grid-cols-3 gap-2">
            {itineraryPaceOptions.map((pace) => (
              <label
                key={pace.id}
                className={cn(
                  "flex h-10 items-center justify-center rounded-md border border-border px-2 text-sm",
                  formInput.pace === pace.id && "border-primary/40 bg-primary/10 text-primary"
                )}
              >
                <input
                  checked={formInput.pace === pace.id}
                  className="sr-only"
                  name="itinerary-pace"
                  onChange={() => onInputChange({ pace: pace.id })}
                  type="radio"
                />
                {pace.label}
              </label>
            ))}
          </div>
        </fieldset>

        {matchingItinerary ? (
          <div className="rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
            Matching saved itinerary: {matchingItinerary.title}
          </div>
        ) : null}

        <Button
          className="w-full gap-2"
          disabled={!canGenerate || isGenerating || submittedDuplicate || Boolean(matchingItinerary)}
          type="submit"
        >
          {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />}
          Generate
        </Button>
      </form>
    </section>
  );
}

function Field({ children, htmlFor, label }: { children: ReactNode; htmlFor: string; label: string }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-muted-foreground" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
    </div>
  );
}

function GenerationPanel({ isGenerating, state }: { isGenerating: boolean; state: GenerationState }) {
  if (isGenerating) {
    return (
      <StatusPanel
        icon={<Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        title="Generating"
        body="Submitting the structured itinerary request."
      />
    );
  }

  if (state.status === "idle") {
    return (
      <StatusPanel
        icon={<ListChecks className="h-4 w-4" aria-hidden="true" />}
        title="Ready"
        body="Generation only runs after you submit the form."
      />
    );
  }

  if (state.status === "unavailable") {
    return (
      <StatusPanel
        icon={<AlertTriangle className="h-4 w-4" aria-hidden="true" />}
        title="Generation staged for Phase 06"
        body={state.response.error.message}
      />
    );
  }

  return (
    <StatusPanel
      icon={<AlertTriangle className="h-4 w-4" aria-hidden="true" />}
      title="Request not submitted"
      body={state.message}
    />
  );
}

function StatusPanel({ body, icon, title }: { body: string; icon: ReactNode; title: string }) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">{icon}</div>
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{body}</p>
        </div>
      </div>
    </section>
  );
}

function SavedItinerariesPanel({
  error,
  isLoading,
  itineraries,
  matchingItineraryId,
  onRetry,
  onSelect,
  selectedItineraryId,
  staleSelection,
}: {
  error: boolean;
  isLoading: boolean;
  itineraries: Itinerary[];
  matchingItineraryId: string | null;
  onRetry: () => void;
  onSelect: (itineraryId: string) => void;
  selectedItineraryId: string | null;
  staleSelection: boolean;
}) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted">
          <Save className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold">Saved itineraries</h2>
          <p className="text-xs text-muted-foreground">Private persisted plans</p>
        </div>
        {error ? (
          <Button className="h-8 gap-1.5 px-2.5 text-xs" onClick={onRetry} type="button" variant="secondary">
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Retry
          </Button>
        ) : null}
      </div>

      {staleSelection ? (
        <div className="mb-3 rounded-md border border-dashed border-border bg-muted/30 p-3 text-sm text-muted-foreground">
          The shared itinerary link is not in your saved history.
        </div>
      ) : null}

      {isLoading ? <SectionSkeleton /> : null}
      {error && !isLoading ? <EmptyState title="Could not load itineraries" body="Check the API connection and retry." /> : null}
      {!error && !isLoading && itineraries.length === 0 ? (
        <EmptyState title="No saved itineraries" body="Saved plans will appear here after generation is connected." />
      ) : null}
      {!error && !isLoading && itineraries.length > 0 ? (
        <div className="space-y-2">
          {itineraries.map((itinerary) => (
            <button
              className={cn(
                "w-full rounded-md border border-border p-3 text-left transition-colors hover:bg-muted/40 focus:outline-none focus:ring-2 focus:ring-primary",
                itinerary.itinerary_id === selectedItineraryId && "border-primary/50 bg-primary/10",
                itinerary.itinerary_id === matchingItineraryId && "border-primary/40"
              )}
              key={itinerary.itinerary_id}
              onClick={() => onSelect(itinerary.itinerary_id)}
              type="button"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{itinerary.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {cityName(itinerary.city_id)} · {itinerary.input.date ?? "No date"} · {itinerary.items.length} items
                  </p>
                </div>
                {itinerary.itinerary_id === matchingItineraryId ? (
                  <span className="rounded-md bg-primary/10 px-2 py-1 text-xs text-primary">Match</span>
                ) : null}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Party {itinerary.input.party_size} · {formatLabel(itinerary.input.pace)} · Updated{" "}
                {formatDateTime(itinerary.updated_at)}
              </p>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function ItineraryDetail({ itinerary }: { itinerary: Itinerary | null }) {
  if (!itinerary) {
    return (
      <section className="rounded-md border border-border p-4">
        <EmptyState title="Select an itinerary" body="Choose a saved itinerary to inspect its persisted details." />
      </section>
    );
  }

  const orderedItems = [...itinerary.items].sort((a, b) => a.position - b.position);

  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-primary" aria-hidden="true" />
            <p className="text-xs font-medium text-primary">Saved</p>
          </div>
          <h2 className="mt-2 text-xl font-semibold tracking-normal">{itinerary.title}</h2>
          {itinerary.summary ? (
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{itinerary.summary}</p>
          ) : null}
        </div>
        <div className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
          {cityName(itinerary.city_id)} · {itinerary.input.date ?? "No date"}
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <Metric label="Party" value={String(itinerary.input.party_size)} />
        <Metric label="Pace" value={formatLabel(itinerary.input.pace)} />
        <Metric label="Items" value={String(itinerary.items.length)} />
      </div>

      <div className="mt-5 space-y-3">
        <h3 className="text-sm font-semibold">Ordered items</h3>
        {orderedItems.length === 0 ? (
          <EmptyState title="No itinerary items" body="This saved itinerary has no persisted child items." />
        ) : (
          orderedItems.map((item) => <ItineraryItemRow item={item} key={item.item_id} />)
        )}
      </div>
    </section>
  );
}

function ItineraryItemRow({ item }: { item: ItineraryItem }) {
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-sm font-semibold">
          {item.position}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-medium">{item.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {[formatLabel(item.item_type), item.area_label].filter(Boolean).join(" · ")}
              </p>
            </div>
            {item.source_table ? (
              <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                {item.source_table}
              </span>
            ) : null}
          </div>
          {item.description ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p> : null}
          <div className="mt-3 flex flex-wrap gap-1.5 text-xs text-muted-foreground">
            {item.starts_at ? <span className="rounded-md border border-border px-2 py-1">Starts {formatDateTime(item.starts_at)}</span> : null}
            {item.ends_at ? <span className="rounded-md border border-border px-2 py-1">Ends {formatDateTime(item.ends_at)}</span> : null}
            {item.source_id ? <span className="rounded-md border border-border px-2 py-1">Source {item.source_id}</span> : null}
          </div>
          <RouteContext routeContext={item.route_context} />
        </div>
      </div>
    </div>
  );
}

function RouteContext({ routeContext }: { routeContext: Record<string, unknown> }) {
  const entries = Object.entries(routeContext).filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (entries.length === 0) return null;

  return (
    <div className="mt-3 rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
      {entries.map(([key, value]) => (
        <span className="mr-3 inline-block" key={key}>
          {formatLabel(key)}: {String(value)}
        </span>
      ))}
    </div>
  );
}

function MapPlaceholder({ itinerary }: { itinerary: Itinerary | null }) {
  const itemsWithArea = itinerary?.items.filter((item) => item.area_label || Object.keys(item.route_context).length > 0) ?? [];

  return (
    <section className="rounded-md border border-border p-4">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted">
          <Map className="h-4 w-4" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-sm font-semibold">Map view</h2>
          <p className="text-xs text-muted-foreground">Route context placeholder</p>
        </div>
      </div>

      {!itinerary ? (
        <EmptyState title="No itinerary selected" body="Select a saved itinerary to preview route context." />
      ) : itemsWithArea.length === 0 ? (
        <EmptyState title="No route context" body="This itinerary does not include area or route metadata yet." />
      ) : (
        <div className="space-y-2">
          {itemsWithArea.map((item) => (
            <div className="flex items-start gap-3 rounded-md border border-dashed border-border p-3" key={item.item_id}>
              <Route className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-sm font-medium">{item.area_label ?? item.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{routeSummary(item)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
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

function SectionSkeleton() {
  return (
    <div className="space-y-2">
      <div className="h-20 rounded-md bg-muted" />
      <div className="h-20 rounded-md bg-muted" />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <p className="text-sm font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function matchLabel(match: MatchSummary): string {
  return `${match.home_team ?? "TBD"} vs ${match.away_team ?? "TBD"}`;
}

function routeSummary(item: ItineraryItem): string {
  const fromPrevious = item.route_context.from_previous_label;
  const minutes = item.route_context.approx_minutes;
  const mode = item.route_context.mode;
  return [fromPrevious ? `From ${fromPrevious}` : null, minutes ? `${minutes} min` : null, mode ? String(mode) : null]
    .filter(Boolean)
    .join(" · ") || "Approximate route context will appear here when available.";
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
