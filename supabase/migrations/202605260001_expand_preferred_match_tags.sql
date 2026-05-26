-- Drop the hard-coded tag allowlist constraint so the expanded
-- experience set can be stored. The length limit (≤ 20 tags) remains.
alter table public.user_preferences
  drop constraint if exists preferred_match_tags_allowed;
