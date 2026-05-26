"use client";

import { useQuery } from "@tanstack/react-query";
import { LogOut, MapPin, Settings, Tag, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchProfile, type ProfileResponse } from "@/lib/api/profile";
import { footballExperiences, hostCities } from "@/lib/reference-data";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function ProtectedAppPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setAuthError("Supabase is not configured for this environment.");
      return;
    }

    const supabase = createSupabaseBrowserClient();
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setAccessToken(data.session.access_token);
    });
  }, [router]);

  const profileQuery = useQuery<ProfileResponse>({
    queryKey: ["me", "profile", accessToken],
    queryFn: () => fetchProfile(accessToken as string),
    enabled: Boolean(accessToken),
    retry: false
  });

  useEffect(() => {
    if (profileQuery.data && !profileQuery.data.profile.profile_completed) {
      router.replace("/onboarding");
    }
  }, [profileQuery.data, router]);

  async function logout() {
    const supabase = createSupabaseBrowserClient();
    await supabase.auth.signOut();
    router.replace("/login");
  }

  return (
    <main className="min-h-screen bg-background px-6 py-8">
      <section className="mx-auto max-w-5xl space-y-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-5">
          <div>
            <p className="text-sm text-muted-foreground">Protected workspace</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-normal">Throughball App</h1>
          </div>
          <Button className="gap-2" onClick={logout} variant="secondary">
            <LogOut aria-hidden="true" className="h-4 w-4" />
            Log out
          </Button>
        </header>

        {authError ? <p className="text-sm text-red-600">{authError}</p> : null}
        {profileQuery.isLoading ? <p className="text-sm text-muted-foreground">Loading profile...</p> : null}
        {profileQuery.error ? (
          <div className="rounded-md border border-border p-4">
            <p className="text-sm font-medium">Profile API unavailable</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Your Supabase session is active, but the backend profile API could not be loaded.
            </p>
          </div>
        ) : null}
        {profileQuery.data ? (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <section className="rounded-md border border-border p-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-muted">
                    <UserRound aria-hidden="true" className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold">
                      {profileQuery.data.profile.display_name ?? "Unnamed fan"}
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {(() => {
                        const city = hostCities.find(
                          (c) => c.id === profileQuery.data.preferences.home_city_id
                        );
                        return city ? city.name : "No home city set";
                      })()}
                    </p>
                  </div>
                </div>
              </section>
              <section className="rounded-md border border-border p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Preferences</h2>
                  <Button
                    className="gap-2 text-xs"
                    onClick={() => router.push("/profile")}
                    type="button"
                    variant="secondary"
                  >
                    <Settings aria-hidden="true" className="h-3.5 w-3.5" />
                    Edit
                  </Button>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  {profileQuery.data.preferences.favorite_team_ids.length} team
                  {profileQuery.data.preferences.favorite_team_ids.length !== 1 ? "s" : ""} following
                </p>
                {profileQuery.data.preferences.preferred_match_tags.length > 0 ? (
                  <div className="mt-3 flex max-h-24 flex-wrap gap-1.5 overflow-y-auto pr-1">
                    {profileQuery.data.preferences.preferred_match_tags.map((tagId) => {
                      const exp = footballExperiences.find((e) => e.id === tagId);
                      return (
                        <span
                          className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                          key={tagId}
                        >
                          <Tag aria-hidden="true" className="h-3 w-3 shrink-0" />
                          {exp ? exp.title : tagId}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <p className="mt-1 text-sm text-muted-foreground">No experiences selected yet.</p>
                )}
              </section>
            </div>
            <Link
              href="/app/heatmap"
              className="flex items-center gap-3 rounded-md border border-border p-5 transition-colors hover:bg-muted/40"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-muted">
                <MapPin aria-hidden="true" className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold">Fan Intelligence</p>
                <p className="text-sm text-muted-foreground">
                  Explore supporter hotspots across host cities
                </p>
              </div>
            </Link>
            {!profileQuery.data.profile.profile_completed && (
              <div className="rounded-md border border-border bg-muted/40 p-4">
                <p className="text-sm font-medium">Complete your profile</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Personalize your World Cup experience to get the most out of Throughball.
                </p>
                <Button
                  className="mt-3"
                  onClick={() => router.push("/onboarding")}
                  type="button"
                  variant="secondary"
                >
                  Finish setup
                </Button>
              </div>
            )}
          </div>
        ) : null}
      </section>
    </main>
  );
}
