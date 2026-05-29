"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { MatchDashboard } from "@/components/matches/match-dashboard";
import { createSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function MatchIntelligencePage() {
  const params = useParams<{ matchId: string | string[] }>();
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const matchId = Array.isArray(params.matchId) ? params.matchId[0] : params.matchId;

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

  if (!authChecked) return null;

  return <MatchDashboard matchId={matchId} />;
}
