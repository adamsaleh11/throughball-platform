export type Profile = {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
  profile_completed: boolean;
  created_at: string;
  updated_at: string;
};

export type Preferences = {
  user_id: string;
  home_city_id: string | null;
  preferred_match_tags: string[];
  favorite_team_ids: string[];
  created_at: string;
  updated_at: string;
};

export type ProfileResponse = {
  profile: Profile;
  preferences: Preferences;
  meta: {
    request_id: string;
    trace_id: string;
    degraded: boolean;
  };
};

export type ProfileUpdateInput = {
  display_name?: string;
  avatar_url?: string;
  home_city_id?: string;
  preferred_match_tags?: string[];
  favorite_team_ids?: string[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchProfile(accessToken: string): Promise<ProfileResponse> {
  const response = await fetch(`${API_BASE_URL}/me/profile`, {
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error("Unable to load profile.");
  }

  return response.json();
}

export async function updateProfile(
  accessToken: string,
  input: ProfileUpdateInput
): Promise<ProfileResponse> {
  const response = await fetch(`${API_BASE_URL}/me/profile`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(input)
  });

  if (!response.ok) {
    throw new Error("Unable to update profile.");
  }

  return response.json();
}
