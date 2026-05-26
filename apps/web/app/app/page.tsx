"use client";

import { useQuery } from "@tanstack/react-query";
import { LogOut, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchProfile, type ProfileResponse } from "@/lib/api/profile";
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
                    {profileQuery.data.profile.profile_completed ? "Profile complete" : "Profile incomplete"}
                  </p>
                </div>
              </div>
            </section>
            <section className="rounded-md border border-border p-5">
              <h2 className="text-lg font-semibold">Preferences</h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Favorite teams: {profileQuery.data.preferences.favorite_team_ids.length}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Match tags: {profileQuery.data.preferences.preferred_match_tags.join(", ") || "None"}
              </p>
            </section>
          </div>
        ) : null}
      </section>
    </main>
  );
}
