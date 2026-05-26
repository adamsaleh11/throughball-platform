"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchProfile, updateProfile, type ProfileResponse } from "@/lib/api/profile";
import { hostCities, matchTags, teams } from "@/lib/reference-data";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function OnboardingPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
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
    if (profileQuery.data) {
      setSelectedTeams(profileQuery.data.preferences.favorite_team_ids);
      setSelectedTags(profileQuery.data.preferences.preferred_match_tags);
    }
  }, [profileQuery.data]);

  const mutation = useMutation({
    mutationFn: (form: FormData) =>
      updateProfile(accessToken as string, {
        display_name: String(form.get("display_name") ?? ""),
        avatar_url: String(form.get("avatar_url") ?? "") || undefined,
        home_city_id: String(form.get("home_city_id") ?? "") || undefined,
        favorite_team_ids: selectedTeams,
        preferred_match_tags: selectedTags
      }),
    onSuccess: (data) => {
      if (data.profile.profile_completed) {
        router.push("/app");
      }
    }
  });

  const selectedTeamSet = useMemo(() => new Set(selectedTeams), [selectedTeams]);
  const selectedTagSet = useMemo(() => new Set(selectedTags), [selectedTags]);

  function toggleValue(value: string, values: string[], setValues: (next: string[]) => void, max: number) {
    if (values.includes(value)) {
      setValues(values.filter((item) => item !== value));
      return;
    }
    if (values.length < max) {
      setValues([...values, value]);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate(new FormData(event.currentTarget));
  }

  return (
    <main className="min-h-screen bg-background px-6 py-8">
      <section className="mx-auto max-w-3xl space-y-8">
        <header>
          <p className="text-sm text-muted-foreground">Account setup</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-normal">Onboarding</h1>
        </header>

        {authError ? <p className="text-sm text-red-600">{authError}</p> : null}
        {profileQuery.isLoading ? <p className="text-sm text-muted-foreground">Loading profile...</p> : null}

        <form className="space-y-6" onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm font-medium">
              <span>Display name</span>
              <input
                className="w-full rounded-md border border-border px-3 py-2"
                defaultValue={profileQuery.data?.profile.display_name ?? ""}
                maxLength={50}
                name="display_name"
              />
            </label>
            <label className="block space-y-2 text-sm font-medium">
              <span>Avatar URL</span>
              <input
                className="w-full rounded-md border border-border px-3 py-2"
                defaultValue={profileQuery.data?.profile.avatar_url ?? ""}
                maxLength={500}
                name="avatar_url"
                type="url"
              />
            </label>
          </div>

          <label className="block space-y-2 text-sm font-medium">
            <span>Home city</span>
            <select
              className="w-full rounded-md border border-border px-3 py-2"
              defaultValue={profileQuery.data?.preferences.home_city_id ?? ""}
              name="home_city_id"
            >
              <option value="">No home city</option>
              {hostCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </label>

          <section className="space-y-3">
            <h2 className="text-sm font-medium">Favorite teams</h2>
            <div className="grid gap-2 sm:grid-cols-2">
              {teams.map((team) => (
                <button
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-left text-sm"
                  key={team.id}
                  onClick={() => toggleValue(team.id, selectedTeams, setSelectedTeams, 10)}
                  type="button"
                >
                  {team.name}
                  {selectedTeamSet.has(team.id) ? <Check aria-hidden="true" className="h-4 w-4 text-primary" /> : null}
                </button>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-medium">Match tags</h2>
            <div className="grid gap-2 sm:grid-cols-2">
              {matchTags.map((tag) => (
                <button
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-left text-sm"
                  key={tag.id}
                  onClick={() => toggleValue(tag.id, selectedTags, setSelectedTags, 20)}
                  type="button"
                >
                  {tag.label}
                  {selectedTagSet.has(tag.id) ? <Check aria-hidden="true" className="h-4 w-4 text-primary" /> : null}
                </button>
              ))}
            </div>
          </section>

          {mutation.error ? <p className="text-sm text-red-600">Unable to save onboarding.</p> : null}
          <div className="flex flex-wrap gap-3">
            <Button className="gap-2" disabled={!accessToken || mutation.isPending} type="submit">
              {mutation.isPending ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
              Save profile
            </Button>
            <Button onClick={() => router.push("/app")} type="button" variant="secondary">
              Skip
            </Button>
          </div>
        </form>
      </section>
    </main>
  );
}
