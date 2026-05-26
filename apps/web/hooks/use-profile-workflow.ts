"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { fetchProfile, updateProfile, type ProfileResponse } from "@/lib/api/profile";
import { footballExperiences, teams } from "@/lib/reference-data";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

type UseProfileWorkflowOptions = {
  onSaveSuccess?: (profile: ProfileResponse) => void;
};

export function useProfileWorkflow({ onSaveSuccess }: UseProfileWorkflowOptions = {}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState("");

  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [homeCityId, setHomeCityId] = useState("");
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [selectedExperiences, setSelectedExperiences] = useState<string[]>([]);
  const [teamSearch, setTeamSearch] = useState("");

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
    if (!profileQuery.data) {
      return;
    }

    setDisplayName(profileQuery.data.profile.display_name ?? "");
    setAvatarUrl(profileQuery.data.profile.avatar_url ?? "");
    setHomeCityId(profileQuery.data.preferences.home_city_id ?? "");
    setSelectedTeams(profileQuery.data.preferences.favorite_team_ids);
    const knownExperienceIds = new Set(footballExperiences.map((experience) => experience.id));
    setSelectedExperiences(
      profileQuery.data.preferences.preferred_match_tags.filter((tag) => knownExperienceIds.has(tag))
    );
  }, [profileQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateProfile(accessToken as string, {
        display_name: displayName,
        avatar_url: avatarUrl || undefined,
        home_city_id: homeCityId || undefined,
        favorite_team_ids: selectedTeams,
        preferred_match_tags: selectedExperiences
      }),
    onSuccess: (profile) => {
      queryClient.invalidateQueries({ queryKey: ["me", "profile"] });
      onSaveSuccess?.(profile);
    }
  });

  const selectedTeamSet = useMemo(() => new Set(selectedTeams), [selectedTeams]);
  const selectedExperienceSet = useMemo(() => new Set(selectedExperiences), [selectedExperiences]);

  const filteredTeams = useMemo(
    () => teams.filter((team) => team.name.toLowerCase().includes(teamSearch.toLowerCase())),
    [teamSearch]
  );

  function toggleTeam(id: string) {
    if (selectedTeamSet.has(id)) {
      setSelectedTeams(selectedTeams.filter((teamId) => teamId !== id));
      return;
    }
    if (selectedTeams.length < 10) {
      setSelectedTeams([...selectedTeams, id]);
    }
  }

  function toggleExperience(id: string) {
    if (selectedExperienceSet.has(id)) {
      setSelectedExperiences(selectedExperiences.filter((experienceId) => experienceId !== id));
      return;
    }
    if (selectedExperiences.length < 20) {
      setSelectedExperiences([...selectedExperiences, id]);
    }
  }

  return {
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
  };
}
