"use client";

import { Check, ChevronLeft, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { ExperienceCard } from "@/components/ui/experience-card";
import { Button } from "@/components/ui/button";
import { footballExperiences, hostCities } from "@/lib/reference-data";
import { useProfileWorkflow } from "@/hooks/use-profile-workflow";

const TOTAL_STEPS = 3;

const STEPS = [
  { label: "Profile", title: "Tell us about yourself", subtitle: "A few details to get you started." },
  { label: "Teams", title: "Which teams are you following?", subtitle: "Select up to 10 teams you want to track." },
  {
    label: "Experiences",
    title: "What's your World Cup vibe?",
    subtitle: "Pick the experiences that excite you most."
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const topRef = useRef<HTMLDivElement>(null);
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
    onSaveSuccess: (data) => {
      if (data.profile.profile_completed) {
        router.push("/app");
      }
    }
  });

  function goToStep(next: number) {
    setStep(next);
    topRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  const isLastStep = step === TOTAL_STEPS - 1;
  const progressPercent = ((step + 1) / TOTAL_STEPS) * 100;

  return (
    <main className="min-h-screen bg-background" ref={topRef}>
      {/* Progress bar */}
      <div className="h-1 w-full bg-muted">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="mx-auto max-w-3xl px-6 py-10">
        {/* Step indicator */}
        <div className="mb-2 flex items-center gap-2">
          {step > 0 && (
            <button
              className="mr-1 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              onClick={() => goToStep(step - 1)}
              type="button"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </button>
          )}
          <span className="text-xs text-muted-foreground">
            Step {step + 1} of {TOTAL_STEPS}
          </span>
        </div>

        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">{STEPS[step].title}</h1>
          <p className="mt-2 text-muted-foreground">{STEPS[step].subtitle}</p>
        </header>

        {authError ? <p className="mb-6 text-sm text-red-600">{authError}</p> : null}
        {profileQuery.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading your profile…
          </div>
        ) : null}

        {/* Step 0: Profile */}
        {step === 0 && (
          <div className="space-y-5">
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
              <span>Home city <span className="font-normal text-muted-foreground">(optional)</span></span>
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
          </div>
        )}

        {/* Step 1: Teams */}
        {step === 1 && (
          <div className="space-y-4">
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
            {selectedTeams.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedTeams.length} / 10 selected
              </p>
            )}
            <div className="grid gap-2 sm:grid-cols-2">
              {filteredTeams.map((team) => (
                <button
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-left text-sm transition-colors hover:border-primary/40 hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary aria-pressed:border-primary aria-pressed:bg-primary/5"
                  aria-pressed={selectedTeamSet.has(team.id)}
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
          </div>
        )}

        {/* Step 2: Experiences */}
        {step === 2 && (
          <div className="space-y-4">
            {selectedExperiences.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedExperiences.length} selected — pick as many as you like
              </p>
            )}
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
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex flex-wrap items-center gap-3">
          {saveMutation.error ? (
            <p className="w-full text-sm text-red-600">Unable to save profile. Please try again.</p>
          ) : null}
          {isLastStep ? (
            <>
              <Button
                className="gap-2"
                disabled={!accessToken || saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
                type="button"
              >
                {saveMutation.isPending ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
                Finish setup
              </Button>
              <Button onClick={() => router.push("/app")} type="button" variant="secondary">
                Skip for now
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => goToStep(step + 1)} type="button">
                Continue
              </Button>
              <Button onClick={() => router.push("/app")} type="button" variant="secondary">
                Skip for now
              </Button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
