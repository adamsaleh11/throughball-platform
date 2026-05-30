import type { Itinerary, ItineraryInput } from "@/lib/api/itineraries";
import { hostCities } from "@/lib/reference-data";

export const itineraryInterestOptions = [
  { id: "food", label: "Food" },
  { id: "fan_zone", label: "Fan zone" },
  { id: "culture", label: "Culture" },
  { id: "family", label: "Family" },
  { id: "nightlife", label: "Nightlife" },
  { id: "transit_friendly", label: "Transit friendly" },
  { id: "tourist_spots", label: "Tourist spots" },
  { id: "venues", label: "Venues" },
] as const;

export const itineraryPaceOptions = [
  { id: "relaxed", label: "Relaxed" },
  { id: "balanced", label: "Balanced" },
  { id: "packed", label: "Packed" },
] as const;

export function defaultItineraryInput(): ItineraryInput {
  return {
    city_id: hostCities[0].id,
    match_id: null,
    date: new Date().toISOString().slice(0, 10),
    party_size: 2,
    interests: ["fan_zone", "food"],
    pace: "balanced",
  };
}

export function normalizedItineraryInput(input: ItineraryInput): ItineraryInput {
  return {
    city_id: input.city_id.trim(),
    match_id: input.match_id?.trim() || null,
    date: input.date?.trim() || null,
    party_size: Number(input.party_size),
    interests: Array.from(
      new Set(input.interests.map((interest) => interest.trim()).filter(Boolean))
    ).sort(),
    pace: input.pace.trim() || "balanced",
  };
}

export function itineraryInputKey(input: ItineraryInput): string {
  return JSON.stringify(normalizedItineraryInput(input));
}

export function findMatchingItinerary(
  input: ItineraryInput,
  itineraries: Itinerary[]
): Itinerary | null {
  const key = itineraryInputKey(input);
  return itineraries.find((itinerary) => itineraryInputKey(itinerary.input) === key) ?? null;
}

export function cityName(cityId: string): string {
  return hostCities.find((city) => city.id === cityId)?.name ?? "Unknown city";
}

export function buildItineraryShareUrl(origin: string, itineraryId: string): string {
  return `${origin}/app/itineraries?itinerary=${encodeURIComponent(itineraryId)}`;
}
