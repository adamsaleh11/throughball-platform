import { describe, expect, it } from "vitest";
import {
  buildItineraryShareUrl,
  findMatchingItinerary,
  itineraryInputKey,
} from "@/lib/itinerary-utils";
import type { Itinerary } from "@/lib/api/itineraries";

const baseInput = {
  city_id: "city-1",
  match_id: null,
  date: "2026-06-12",
  party_size: 2,
  interests: [" fan_zone", "food", "food"],
  pace: "balanced",
};

describe("itinerary utils", () => {
  it("normalizes interest order, whitespace, and duplicates into the same key", () => {
    expect(itineraryInputKey(baseInput)).toBe(
      itineraryInputKey({
        ...baseInput,
        interests: ["food", "fan_zone"],
      })
    );
  });

  it("finds a saved itinerary matching normalized input", () => {
    const itinerary = {
      itinerary_id: "itin-1",
      input: {
        ...baseInput,
        interests: ["food", "fan_zone"],
      },
    } as Itinerary;

    expect(findMatchingItinerary(baseInput, [itinerary])?.itinerary_id).toBe("itin-1");
  });

  it("builds private app share URLs", () => {
    expect(buildItineraryShareUrl("http://localhost:3000", "itin 1")).toBe(
      "http://localhost:3000/app/itineraries?itinerary=itin%201"
    );
  });
});
