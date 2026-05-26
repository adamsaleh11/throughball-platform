"use client";

import { Check, ChevronLeft, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { ExperienceCard } from "@/components/ui/experience-card";
import { Button } from "@/components/ui/button";
import { footballExperiences, hostCities } from "@/lib/reference-data";
import { useProfileWorkflow } from "@/hooks/use-profile-workflow";

export default function ProfilePage() {
  const router = useRouter();
  const {
    accessToken,
    authError,
    avatarUrl,
    displayName,
    filteredTeams,
    homeCityId,
    profileQuery,
    saveMutation,
    selectedExperienceSet,
    selectedExperiences,
    selectedTeamSet,
    selectedTeams,
    setAvatarUrl,
    setDisplayName,
    setHomeCityId,
    setTeamSearch,
    teamSearch,
    toggleExperience,
    toggleTeam
  } = useProfileWorkflow({
    onSaveSuccess: () => router.push("/app")
  });

  const homeCityName = hostCities.find((c) => c.id === homeCityId)?.name;

  return (
    <main className="min-h-screen bg-background px-6 py-10">
      <div className="mx-auto max-w-3xl space-y-10">
        <header>
          <button
            className="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            onClick={() => router.push("/app")}
            type="button"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back to app
          </button>
          <h1 className="text-3xl font-semibold tracking-tight">Edit preferences</h1>
          <p className="mt-2 text-muted-foreground">Update your profile and World Cup preferences at any time.</p>
        </header>

        {authError ? <p className="text-sm text-red-600">{authError}</p> : null}
        {profileQuery.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading profile…
          </div>
        ) : null}
        {profileQuery.error ? (
          <p className="text-sm text-red-600">Unable to load profile. Please try again.</p>
        ) : null}

        {/* Profile info */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Profile</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block space-y-2 text-sm font-medium">
              <span>Display name</span>
              <input
                className="w-full rounded-md border border-border bg-background px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                maxLength={50}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="How should we call you?"
                value={displayName}
              />
            </label>
            <label className="block space-y-2 text-sm font-medium">
              <span>Avatar URL <span className="font-normal text-muted-foreground">(optional)</span></span>
              <input
                className="w-full rounded-md border border-border bg-background px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                maxLength={500}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://…"
                type="url"
                value={avatarUrl}
              />
            </label>
          </div>
          <label className="block space-y-2 text-sm font-medium">
            <span>
              Home city{" "}
              {homeCityName ? (
                <span className="font-normal text-muted-foreground">— {homeCityName}</span>
              ) : null}
            </span>
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
              onChange={(e) => setHomeCityId(e.target.value)}
              value={homeCityId}
            >
              <option value="">No home city selected</option>
              {hostCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </label>
        </section>

        {/* Teams */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Favorite teams</h2>
            {selectedTeams.length > 0 && (
              <span className="text-xs text-muted-foreground">{selectedTeams.length} / 10</span>
            )}
          </div>
          <div className="relative">
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            />
            <input
              className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 focus:outline-none focus:ring-2 focus:ring-primary"
              onChange={(e) => setTeamSearch(e.target.value)}
              placeholder="Search teams…"
              value={teamSearch}
            />
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {filteredTeams.map((team) => (
              <button
                aria-pressed={selectedTeamSet.has(team.id)}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-left text-sm transition-colors hover:border-primary/40 hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary aria-pressed:border-primary aria-pressed:bg-primary/5"
                key={team.id}
                onClick={() => toggleTeam(team.id)}
                type="button"
              >
                {team.name}
                {selectedTeamSet.has(team.id) ? (
                  <Check aria-hidden="true" className="h-4 w-4 shrink-0 text-primary" />
                ) : null}
              </button>
            ))}
            {filteredTeams.length === 0 && (
              <p className="col-span-2 py-4 text-center text-sm text-muted-foreground">No teams match your search.</p>
            )}
          </div>
        </section>

        {/* Experiences */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Your World Cup vibe</h2>
              <p className="mt-1 text-sm text-muted-foreground">Pick the experiences that excite you most.</p>
            </div>
            {selectedExperiences.length > 0 && (
              <span className="text-xs text-muted-foreground">{selectedExperiences.length} selected</span>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {footballExperiences.map((exp) => (
              <ExperienceCard
                description={exp.description}

                id={exp.id}
                key={exp.id}
                onToggle={toggleExperience}
                selected={selectedExperienceSet.has(exp.id)}
                title={exp.title}
              />
            ))}
          </div>
        </section>

        {/* Save */}
        <div className="flex flex-wrap items-center gap-3 pb-10">
          {saveMutation.error ? (
            <p className="w-full text-sm text-red-600">Unable to save changes. Please try again.</p>
          ) : null}
          <Button
            className="gap-2"
            disabled={!accessToken || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
            type="button"
          >
            {saveMutation.isPending ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
            Save changes
          </Button>
          <Button onClick={() => router.push("/app")} type="button" variant="secondary">
            Cancel
          </Button>
        </div>
      </div>
    </main>
  );
}
