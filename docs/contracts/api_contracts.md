# API Contracts

Source of truth for platform and AI integration DTOs. These contracts intentionally prefer seeded, cached, and deterministic platform data over live third-party APIs.

## Contract Rules

- Base path: `/api/v1`
- Payload format: JSON.
- Timestamps: ISO 8601 UTC strings.
- IDs: stable strings.
- Coordinates: never expose exact user coordinates. Use rounded or aggregate location fields only.
- Demo data: use seeded and cached data. Do not require live third-party APIs.
- AI cost: include `estimated_cost` only in AI-related responses.
- Observability: relevant responses include `request_id`, `trace_id`, `latency_ms`, `retries`, and `degraded`.

## Shared DTOs

### ObservabilityMeta

```json
{
  "request_id": "req_01HX7RZQ7K4C9XQ1XQ7B5D2F8A",
  "trace_id": "trc_01HX7S0P0M8Z7V9E1C4A2B6D3F",
  "latency_ms": 42,
  "retries": 0,
  "degraded": false
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `request_id` | string | yes | Unique per API request. |
| `trace_id` | string | yes | Trace correlation ID. |
| `latency_ms` | integer | yes | Server-side latency in milliseconds. |
| `retries` | integer | yes | Retry count for internal dependencies. |
| `degraded` | boolean | yes | True when cached, partial, or fallback execution was used. |

### PageRequest

```json
{
  "page": 1,
  "page_size": 20
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `page` | integer | no | Default `1`; minimum `1`. |
| `page_size` | integer | no | Default `20`; maximum `100`. |

### PageMeta

```json
{
  "page": 1,
  "page_size": 20,
  "total_items": 84,
  "total_pages": 5,
  "has_next": true
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `page` | integer | yes | Current page. |
| `page_size` | integer | yes | Items requested per page. |
| `total_items` | integer | yes | Total matching records. |
| `total_pages` | integer | yes | Total pages available. |
| `has_next` | boolean | yes | True when another page exists. |

### ErrorResponse

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload.",
    "details": [
      {
        "field": "email",
        "issue": "Must be a valid email address."
      }
    ]
  },
  "meta": {
    "request_id": "req_01HX7RZQ7K4C9XQ1XQ7B5D2F8A",
    "trace_id": "trc_01HX7S0P0M8Z7V9E1C4A2B6D3F",
    "latency_ms": 12,
    "retries": 0,
    "degraded": false
  }
}
```

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `error.code` | string | yes | Stable machine-readable code. |
| `error.message` | string | yes | Human-readable message. |
| `error.details` | array | no | Field or domain-specific details. |
| `meta` | ObservabilityMeta | yes | Standard observability metadata. |

Standard error codes:

| Code | HTTP Status |
| --- | --- |
| `VALIDATION_ERROR` | 400 |
| `UNAUTHORIZED` | 401 |
| `FORBIDDEN` | 403 |
| `NOT_FOUND` | 404 |
| `CONFLICT` | 409 |
| `RATE_LIMITED` | 429 |
| `INTERNAL_ERROR` | 500 |
| `DEGRADED_RESPONSE` | 503 |

## Auth DTOs

Signup, login, logout, and refresh are handled directly by Supabase Auth from the Next.js frontend. FastAPI does not expose `/auth/*` proxy endpoints for this ticket.

Production should enable email confirmation in Supabase. Local development may disable email confirmation for faster testing.

## Profile DTOs

### Profile

```json
{
  "user_id": "usr_123",
  "display_name": "Alex",
  "avatar_url": "https://example.com/avatar.png",
  "profile_completed": true,
  "created_at": "2026-05-25T12:00:00Z",
  "updated_at": "2026-05-25T12:30:00Z"
}
```

### GetProfileResponse

```json
{
  "profile": {
    "user_id": "usr_123",
    "display_name": "Alex",
    "avatar_url": null,
    "profile_completed": true,
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T12:30:00Z"
  },
  "preferences": {
    "user_id": "usr_123",
    "home_city_id": "city_toronto",
    "favorite_team_ids": ["team_canada"],
    "preferred_match_tags": ["rivalry"],
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T12:30:00Z"
  },
  "meta": {
    "request_id": "req_200",
    "trace_id": "trc_200",
    "latency_ms": 18,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /me/profile`

### UpdateProfileRequest

```json
{
  "display_name": "Alex M.",
  "avatar_url": "https://example.com/avatar.png",
  "home_city_id": "city_toronto",
  "favorite_team_ids": ["team_canada", "team_toronto_fc"],
  "preferred_match_tags": ["rivalry", "knockout"]
}
```

### UpdateProfileResponse

```json
{
  "profile": {
    "user_id": "usr_123",
    "display_name": "Alex M.",
    "avatar_url": "https://example.com/avatar.png",
    "profile_completed": true,
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T13:00:00Z"
  },
  "preferences": {
    "user_id": "usr_123",
    "home_city_id": "city_toronto",
    "favorite_team_ids": ["team_canada", "team_toronto_fc"],
    "preferred_match_tags": ["rivalry", "knockout"],
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T13:00:00Z"
  },
  "meta": {
    "request_id": "req_201",
    "trace_id": "trc_201",
    "latency_ms": 24,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `PUT /me/profile`

## City DTOs

### City

```json
{
  "city_id": "city_toronto",
  "name": "Toronto",
  "country_code": "CA",
  "timezone": "America/Toronto",
  "center": {
    "lat": 43.65,
    "lng": -79.38
  },
  "data_status": "seeded"
}
```

### ListCitiesResponse

```json
{
  "cities": [
    {
      "city_id": "city_toronto",
      "name": "Toronto",
      "country_code": "CA",
      "timezone": "America/Toronto",
      "center": {
        "lat": 43.65,
        "lng": -79.38
      },
      "data_status": "seeded"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false
  },
  "meta": {
    "request_id": "req_300",
    "trace_id": "trc_300",
    "latency_ms": 15,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /cities?page=1&page_size=20`

## Match DTOs

### Match

```json
{
  "match_id": "match_2026_001",
  "city_id": "city_toronto",
  "home_team": "Canada",
  "away_team": "Mexico",
  "competition": "World Cup",
  "starts_at": "2026-06-12T23:00:00Z",
  "status": "scheduled",
  "tags": ["world-cup", "group-stage"]
}
```

### ListMatchesResponse

```json
{
  "matches": [
    {
      "match_id": "match_2026_001",
      "city_id": "city_toronto",
      "home_team": "Canada",
      "away_team": "Mexico",
      "competition": "World Cup",
      "starts_at": "2026-06-12T23:00:00Z",
      "status": "scheduled",
      "tags": ["world-cup", "group-stage"]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false
  },
  "meta": {
    "request_id": "req_400",
    "trace_id": "trc_400",
    "latency_ms": 17,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /matches?city_id=city_toronto&page=1&page_size=20`

## Venue DTOs

### Venue

```json
{
  "venue_id": "venue_queen_pub",
  "city_id": "city_toronto",
  "name": "Queen Street Football Pub",
  "venue_type": "bar",
  "area_label": "Queen West",
  "location": {
    "lat": 43.64,
    "lng": -79.41,
    "precision": "neighborhood"
  },
  "capacity_estimate": 180,
  "amenities": ["screens", "food", "patio"],
  "data_status": "cached"
}
```

### ListVenuesResponse

```json
{
  "venues": [
    {
      "venue_id": "venue_queen_pub",
      "city_id": "city_toronto",
      "name": "Queen Street Football Pub",
      "venue_type": "bar",
      "area_label": "Queen West",
      "location": {
        "lat": 43.64,
        "lng": -79.41,
        "precision": "neighborhood"
      },
      "capacity_estimate": 180,
      "amenities": ["screens", "food", "patio"],
      "data_status": "cached"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false
  },
  "meta": {
    "request_id": "req_500",
    "trace_id": "trc_500",
    "latency_ms": 20,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /venues?city_id=city_toronto&page=1&page_size=20`

## Fan Check-In DTOs

### CreateCheckInRequest

```json
{
  "venue_id": "venue_queen_pub",
  "match_id": "match_2026_001",
  "party_size": 3,
  "visibility": "aggregate_only"
}
```

Exact user coordinates and raw check-in locations must not be accepted by this public contract.

### CheckIn

```json
{
  "check_in_id": "chk_789",
  "user_id": "usr_123",
  "venue_id": "venue_queen_pub",
  "match_id": "match_2026_001",
  "party_size": 3,
  "visibility": "aggregate_only",
  "created_at": "2026-05-25T14:00:00Z"
}
```

### CreateCheckInResponse

```json
{
  "check_in": {
    "check_in_id": "chk_789",
    "user_id": "usr_123",
    "venue_id": "venue_queen_pub",
    "match_id": "match_2026_001",
    "party_size": 3,
    "visibility": "aggregate_only",
    "created_at": "2026-05-25T14:00:00Z"
  },
  "meta": {
    "request_id": "req_600",
    "trace_id": "trc_600",
    "latency_ms": 25,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `POST /check-ins`

### VenueCheckInAggregate

```json
{
  "venue_id": "venue_queen_pub",
  "match_id": "match_2026_001",
  "supporter_count": 74,
  "party_count": 29,
  "confidence": 0.82,
  "updated_at": "2026-05-25T14:05:00Z"
}
```

### ListVenueCheckInAggregatesResponse

```json
{
  "aggregates": [
    {
      "venue_id": "venue_queen_pub",
      "match_id": "match_2026_001",
      "supporter_count": 74,
      "party_count": 29,
      "confidence": 0.82,
      "updated_at": "2026-05-25T14:05:00Z"
    }
  ],
  "meta": {
    "request_id": "req_601",
    "trace_id": "trc_601",
    "latency_ms": 19,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /check-ins/aggregates?match_id=match_2026_001`

## Hotspot DTOs

### Hotspot

```json
{
  "hotspot_id": "hotspot_queen_west_001",
  "city_id": "city_toronto",
  "match_id": "match_2026_001",
  "area_label": "Queen West",
  "center": {
    "lat": 43.64,
    "lng": -79.41,
    "precision": "neighborhood"
  },
  "score": 91,
  "confidence": 0.86,
  "supporter_count": 240,
  "top_venue_ids": ["venue_queen_pub"],
  "ranking_factors": {
    "check_in_weight": 0.45,
    "venue_capacity_weight": 0.25,
    "match_relevance_weight": 0.2,
    "recency_weight": 0.1
  },
  "updated_at": "2026-05-25T14:05:00Z"
}
```

### ListHotspotsResponse

```json
{
  "hotspots": [
    {
      "hotspot_id": "hotspot_queen_west_001",
      "city_id": "city_toronto",
      "match_id": "match_2026_001",
      "area_label": "Queen West",
      "center": {
        "lat": 43.64,
        "lng": -79.41,
        "precision": "neighborhood"
      },
      "score": 91,
      "confidence": 0.86,
      "supporter_count": 240,
      "top_venue_ids": ["venue_queen_pub"],
      "ranking_factors": {
        "check_in_weight": 0.45,
        "venue_capacity_weight": 0.25,
        "match_relevance_weight": 0.2,
        "recency_weight": 0.1
      },
      "updated_at": "2026-05-25T14:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false
  },
  "meta": {
    "request_id": "req_700",
    "trace_id": "trc_700",
    "latency_ms": 28,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `GET /hotspots?city_id=city_toronto&match_id=match_2026_001&page=1&page_size=20`

## Recommendation DTOs

### RecommendationRequest

```json
{
  "city_id": "city_toronto",
  "match_id": "match_2026_001",
  "party_size": 3,
  "preferences": {
    "venue_types": ["bar"],
    "amenities": ["screens", "food"],
    "max_results": 5
  }
}
```

### Recommendation

```json
{
  "recommendation_id": "rec_001",
  "venue_id": "venue_queen_pub",
  "rank": 1,
  "score": 94,
  "confidence": 0.88,
  "reason_codes": ["high_check_ins", "screens_available", "match_relevant"],
  "deterministic_factors": {
    "hotspot_score": 91,
    "venue_fit_score": 96,
    "capacity_fit_score": 89
  }
}
```

### RecommendationResponse

```json
{
  "recommendations": [
    {
      "recommendation_id": "rec_001",
      "venue_id": "venue_queen_pub",
      "rank": 1,
      "score": 94,
      "confidence": 0.88,
      "reason_codes": ["high_check_ins", "screens_available", "match_relevant"],
      "deterministic_factors": {
        "hotspot_score": 91,
        "venue_fit_score": 96,
        "capacity_fit_score": 89
      }
    }
  ],
  "meta": {
    "request_id": "req_800",
    "trace_id": "trc_800",
    "latency_ms": 31,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `POST /recommendations`

## Itinerary DTOs

### CreateItineraryRequest

```json
{
  "city_id": "city_toronto",
  "match_id": "match_2026_001",
  "venue_ids": ["venue_queen_pub"],
  "start_area_label": "Queen West",
  "party_size": 3
}
```

### ItineraryStop

```json
{
  "stop_id": "stop_001",
  "venue_id": "venue_queen_pub",
  "order": 1,
  "planned_arrival_at": "2026-06-12T21:00:00Z",
  "duration_minutes": 120,
  "score": 94,
  "reason_codes": ["best_match_atmosphere", "capacity_fit"]
}
```

### Itinerary

```json
{
  "itinerary_id": "itin_001",
  "city_id": "city_toronto",
  "match_id": "match_2026_001",
  "party_size": 3,
  "stops": [
    {
      "stop_id": "stop_001",
      "venue_id": "venue_queen_pub",
      "order": 1,
      "planned_arrival_at": "2026-06-12T21:00:00Z",
      "duration_minutes": 120,
      "score": 94,
      "reason_codes": ["best_match_atmosphere", "capacity_fit"]
    }
  ],
  "created_at": "2026-05-25T14:20:00Z"
}
```

### CreateItineraryResponse

```json
{
  "itinerary": {
    "itinerary_id": "itin_001",
    "city_id": "city_toronto",
    "match_id": "match_2026_001",
    "party_size": 3,
    "stops": [
      {
        "stop_id": "stop_001",
        "venue_id": "venue_queen_pub",
        "order": 1,
        "planned_arrival_at": "2026-06-12T21:00:00Z",
        "duration_minutes": 120,
        "score": 94,
        "reason_codes": ["best_match_atmosphere", "capacity_fit"]
      }
    ],
    "created_at": "2026-05-25T14:20:00Z"
  },
  "meta": {
    "request_id": "req_900",
    "trace_id": "trc_900",
    "latency_ms": 34,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `POST /itineraries`

## AI DTOs

AI endpoints only synthesize explanations from deterministic platform results. They must not rank, filter, or invent recommendations.

### AISummaryRequest

```json
{
  "city_id": "city_toronto",
  "match_id": "match_2026_001",
  "context": {
    "hotspot_ids": ["hotspot_queen_west_001"],
    "recommendation_ids": ["rec_001"],
    "itinerary_id": "itin_001"
  },
  "tone": "concise"
}
```

### AISummaryResponse

```json
{
  "summary": {
    "headline": "Queen West is the strongest match-day area.",
    "body": "Queen West ranks highest based on aggregate check-ins, venue capacity, and match relevance. Queen Street Football Pub is the top fit for a party of three.",
    "source_ids": {
      "hotspot_ids": ["hotspot_queen_west_001"],
      "recommendation_ids": ["rec_001"],
      "itinerary_id": "itin_001"
    }
  },
  "estimated_cost": {
    "currency": "USD",
    "amount": 0.0021,
    "input_tokens": 620,
    "output_tokens": 85
  },
  "meta": {
    "request_id": "req_1000",
    "trace_id": "trc_1000",
    "latency_ms": 410,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `POST /ai/summaries`

### AIRecommendationExplanationRequest

```json
{
  "recommendation_ids": ["rec_001"],
  "audience": "fan",
  "max_sentences": 3
}
```

### AIRecommendationExplanationResponse

```json
{
  "explanations": [
    {
      "recommendation_id": "rec_001",
      "text": "Queen Street Football Pub is ranked first because it has strong aggregate fan activity, enough estimated capacity for your group, and the right amenities for the match."
    }
  ],
  "estimated_cost": {
    "currency": "USD",
    "amount": 0.0014,
    "input_tokens": 420,
    "output_tokens": 60
  },
  "meta": {
    "request_id": "req_1001",
    "trace_id": "trc_1001",
    "latency_ms": 360,
    "retries": 0,
    "degraded": false
  }
}
```

Endpoint: `POST /ai/recommendation-explanations`

## Endpoint Summary

| Method | Path | Request DTO | Response DTO | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/me/profile` | none | GetProfileResponse | Auth required. |
| `PUT` | `/me/profile` | UpdateProfileRequest | UpdateProfileResponse | Auth required. |
| `GET` | `/cities` | PageRequest query | ListCitiesResponse | Seeded city data. |
| `GET` | `/matches` | `city_id`, PageRequest query | ListMatchesResponse | Seeded/cached match data. |
| `GET` | `/venues` | `city_id`, PageRequest query | ListVenuesResponse | Seeded/cached venue data. |
| `POST` | `/check-ins` | CreateCheckInRequest | CreateCheckInResponse | No exact coordinates. |
| `GET` | `/check-ins/aggregates` | `match_id` query | ListVenueCheckInAggregatesResponse | Aggregate only. |
| `GET` | `/hotspots` | `city_id`, `match_id`, PageRequest query | ListHotspotsResponse | Deterministic rankings. |
| `POST` | `/recommendations` | RecommendationRequest | RecommendationResponse | Deterministic recommendations. |
| `POST` | `/itineraries` | CreateItineraryRequest | CreateItineraryResponse | Deterministic ordering. |
| `POST` | `/ai/summaries` | AISummaryRequest | AISummaryResponse | AI synthesis only. |
| `POST` | `/ai/recommendation-explanations` | AIRecommendationExplanationRequest | AIRecommendationExplanationResponse | AI explanation only. |
