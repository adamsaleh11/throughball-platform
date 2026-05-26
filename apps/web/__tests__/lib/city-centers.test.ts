import { describe, it, expect } from "vitest";
import { cityCenter, allCityCentersResolved } from "@/lib/city-centers";
import { hostCities } from "@/lib/reference-data";

describe("cityCenter", () => {
  it("returns a non-null lat/lng for every host city", () => {
    for (const city of hostCities) {
      const center = cityCenter(city.id);
      expect(center, `Missing center for ${city.name}`).toBeDefined();
      expect(typeof center.lat).toBe("number");
      expect(typeof center.lng).toBe("number");
    }
  });

  it("returns a fallback for an unknown city ID", () => {
    const center = cityCenter("unknown-city-id");
    expect(center).toBeDefined();
    expect(typeof center.lat).toBe("number");
    expect(typeof center.lng).toBe("number");
  });

  it("resolves all 16 host cities", () => {
    expect(hostCities).toHaveLength(16);
    expect(allCityCentersResolved()).toBe(true);
  });
});
