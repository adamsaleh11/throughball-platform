"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ChevronLeft, MapPin, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchHotspots, fetchMatches, type Match } from "@/lib/api/fan";
import { fetchProfile } from "@/lib/api/profile";
import { hostCities } from "@/lib/reference-data";
import { cityCenter } from "@/lib/city-centers";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

const sortedCities = [...hostCities].sort((a, b) => a.name.localeCompare(b.name));

const DynamicHotspotMap = dynamic(
  () => import("@/components/fan/hotspot-map").then((m) => m.HotspotMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading map...
      </div>
    ),
  }
);

export default function HeatmapPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [selectedCityId, setSelectedCityId] = useState<string>(sortedCities[0].id);
  const [selectedMatchId, setSelectedMatchId] = useState<string>("");

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

  const profileQuery = useQuery({
    queryKey: ["me", "profile", accessToken],
    queryFn: () => fetchProfile(accessToken as string),
    enabled: Boolean(accessToken),
    retry: false,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (!profileQuery.data) return;
    const homeCityId = profileQuery.data.preferences.home_city_id;
    if (homeCityId && hostCities.some((c) => c.id === homeCityId)) {
      setSelectedCityId(homeCityId);
    }
  }, [profileQuery.data]);

  const matchesQuery = useQuery({
    queryKey: ["matches", selectedCityId],
    queryFn: () => fetchMatches(selectedCityId),
    enabled: Boolean(selectedCityId),
    retry: false,
    refetchOnWindowFocus: false,
    refetchInterval: false,
    staleTime: 5 * 60 * 1000,
  });

  const hotspotsQuery = useQuery({
    queryKey: ["hotspots", selectedCityId, selectedMatchId || null],
    queryFn: () => fetchHotspots(selectedCityId, selectedMatchId || undefined),
    enabled: Boolean(selectedCityId),
    retry: false,
    refetchOnWindowFocus: false,
    refetchInterval: false,
    staleTime: Infinity,
  });

  const hotspots = hotspotsQuery.data?.hotspots ?? [];
  const matches: Match[] = matchesQuery.data?.matches ?? [];
  const fallbackCenter = cityCenter(selectedCityId);

  const lastUpdated =
    hotspots.length > 0
      ? new Date(
          Math.max(...hotspots.map((h) => new Date(h.updated_at).getTime()))
        )
      : null;

  function handleCityChange(cityId: string) {
    setSelectedCityId(cityId);
    setSelectedMatchId("");
  }

  if (!authChecked) return null;

  return (
    <main className="flex h-screen flex-col bg-background">
      <header className="shrink-0 border-b border-border px-4 py-3 md:px-6 md:py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3">
          <Link
            href="/app"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </Link>

          <div className="flex-1 min-w-0">
            <h1 className="text-base font-semibold md:text-lg">Fan Intelligence</h1>
            <p className="text-xs text-muted-foreground">Supporter hotspots by city</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <label htmlFor="city-select" className="sr-only">
              Select city
            </label>
            <select
              id="city-select"
              value={selectedCityId}
              onChange={(e) => handleCityChange(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {sortedCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>

            {matches.length > 0 && (
              <>
                <label htmlFor="match-select" className="sr-only">
                  Filter by match
                </label>
                <select
                  id="match-select"
                  value={selectedMatchId}
                  onChange={(e) => setSelectedMatchId(e.target.value)}
                  className="h-9 rounded-md border border-border bg-background px-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All matches</option>
                  {matches.map((match) => (
                    <option key={match.id} value={match.id}>
                      {match.label ?? match.title ?? match.id}
                    </option>
                  ))}
                </select>
              </>
            )}

            <div className="flex items-center gap-2">
              {lastUpdated && (
                <span className="hidden text-xs text-muted-foreground sm:inline">
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <Button
                variant="secondary"
                className="h-9 gap-1.5 px-3 text-sm"
                onClick={() => hotspotsQuery.refetch()}
                disabled={hotspotsQuery.isFetching}
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${hotspotsQuery.isFetching ? "animate-spin" : ""}`}
                  aria-hidden="true"
                />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="relative min-h-0 flex-1">
        {hotspotsQuery.isLoading && (
          <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-background/80">
            <p className="text-sm text-muted-foreground">Loading hotspots...</p>
          </div>
        )}

        {hotspotsQuery.isError && !hotspotsQuery.isLoading && (
          <div className="absolute inset-0 z-[1000] flex flex-col items-center justify-center gap-4 bg-background">
            <MapPin className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
            <div className="text-center">
              <p className="font-medium">Could not load hotspots</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Check your connection and try again.
              </p>
            </div>
            <Button variant="secondary" onClick={() => hotspotsQuery.refetch()}>
              Try again
            </Button>
          </div>
        )}

        {hotspotsQuery.isSuccess && !hotspotsQuery.isLoading && hotspots.length === 0 && (
          <div className="absolute inset-x-0 top-4 z-[1000] flex justify-center px-4">
            <div className="rounded-md border border-border bg-background/95 px-4 py-3 text-center shadow-sm">
              <p className="text-sm font-medium">No hotspots yet</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                No supporter activity recorded for this city and filter.
              </p>
            </div>
          </div>
        )}

        <DynamicHotspotMap hotspots={hotspots} fallbackCenter={fallbackCenter} />
      </div>
    </main>
  );
}
