import os
from uuid import uuid4

import pytest
import requests


REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_TEST_USER_A_EMAIL",
    "SUPABASE_TEST_USER_A_PASSWORD",
    "SUPABASE_TEST_USER_B_EMAIL",
    "SUPABASE_TEST_USER_B_PASSWORD",
]


def require_supabase_env() -> dict[str, str]:
    values = {name: os.environ.get(name, "") for name in REQUIRED_ENV}
    missing = [name for name, value in values.items() if not value]
    if missing:
        pytest.skip(f"Supabase RLS integration env vars are missing: {', '.join(missing)}")
    return values


def login(supabase_url: str, anon_key: str, email: str, password: str) -> str:
    response = requests.post(
        f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "content-type": "application/json"},
        json={"email": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def rest_headers(anon_key: str, access_token: str) -> dict[str, str]:
    return {
        "apikey": anon_key,
        "authorization": f"Bearer {access_token}",
        "content-type": "application/json",
    }


def test_rls_prevents_cross_user_profile_access() -> None:
    env = require_supabase_env()
    supabase_url = env["SUPABASE_URL"].rstrip("/")
    anon_key = env["SUPABASE_ANON_KEY"]
    token_a = login(
        supabase_url,
        anon_key,
        env["SUPABASE_TEST_USER_A_EMAIL"],
        env["SUPABASE_TEST_USER_A_PASSWORD"],
    )
    token_b = login(
        supabase_url,
        anon_key,
        env["SUPABASE_TEST_USER_B_EMAIL"],
        env["SUPABASE_TEST_USER_B_PASSWORD"],
    )

    user_b_response = requests.get(
        f"{supabase_url}/auth/v1/user",
        headers=rest_headers(anon_key, token_b),
        timeout=10,
    )
    user_b_response.raise_for_status()
    user_b_id = user_b_response.json()["id"]

    cross_read = requests.get(
        f"{supabase_url}/rest/v1/profiles?id=eq.{user_b_id}",
        headers=rest_headers(anon_key, token_a),
        timeout=10,
    )
    cross_read.raise_for_status()
    assert cross_read.json() == []

    cross_preference_update = requests.patch(
        f"{supabase_url}/rest/v1/user_preferences?user_id=eq.{user_b_id}",
        headers={**rest_headers(anon_key, token_a), "prefer": "return=representation"},
        json={"preferred_match_tags": ["rivalry"]},
        timeout=10,
    )
    cross_preference_update.raise_for_status()
    assert cross_preference_update.json() == []

    cross_favorite_insert = requests.post(
        f"{supabase_url}/rest/v1/user_favorite_teams",
        headers=rest_headers(anon_key, token_a),
        json={"user_id": user_b_id, "team_id": str(uuid4())},
        timeout=10,
    )
    assert cross_favorite_insert.status_code in {401, 403, 404, 409}
