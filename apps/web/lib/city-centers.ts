import { hostCities } from "./reference-data";

// Coarse geographic centers for all 16 World Cup host cities.
// Used as fallback map center when no hotspots are returned.
const CITY_CENTERS: Record<string, { lat: number; lng: number }> = {
  "874c6b46-de32-5014-8e54-da12587a7d7f": { lat: 43.6532, lng: -79.3832 },  // Toronto
  "474d6beb-b593-5c05-92c4-a06aa502dbed": { lat: 49.2827, lng: -123.1207 }, // Vancouver
  "b671a503-b59c-5d9f-a123-9b1ea8a2c0d6": { lat: 20.6597, lng: -103.3496 }, // Guadalajara
  "b3a9b5e9-741b-591c-835c-a6f0d06e0f91": { lat: 19.4326, lng: -99.1332 },  // Mexico City
  "22a9693c-c752-5a4d-bacc-d2d30e7184b3": { lat: 25.6866, lng: -100.3161 }, // Monterrey
  "c50bfe5b-7584-5cbc-986a-3181ad4e24a5": { lat: 33.7490, lng: -84.3880 },  // Atlanta
  "de87922f-8512-5575-90ee-38d8c10282fe": { lat: 42.3601, lng: -71.0589 },  // Boston
  "b865e6bf-eb90-593f-aa76-7ffb55fd9fda": { lat: 32.7767, lng: -96.7970 },  // Dallas
  "713d1905-0f40-57b5-84fc-4409f300c919": { lat: 29.7604, lng: -95.3698 },  // Houston
  "4da740f5-55c8-53a1-bc01-2f16e943110d": { lat: 39.0997, lng: -94.5786 },  // Kansas City
  "8b2dc317-8b49-5b8a-8544-7d091044b4e1": { lat: 34.0522, lng: -118.2437 }, // Los Angeles
  "bd337c08-d7f9-57bb-8a33-c2feeb3ca18f": { lat: 25.7617, lng: -80.1918 },  // Miami
  "e0452c84-d22b-54b2-9f48-6805f73801c6": { lat: 40.7128, lng: -74.0060 },  // New York/New Jersey
  "4d1935bc-b2b5-5ebf-9ea9-36ba368d8972": { lat: 39.9526, lng: -75.1652 },  // Philadelphia
  "cc33e2c4-6c1c-5d5b-8985-6015ed027a07": { lat: 37.7749, lng: -122.4194 }, // San Francisco Bay Area
  "e5fae842-3ec7-5636-a2ae-ebb90793ee85": { lat: 47.6062, lng: -122.3321 }, // Seattle
};

const GEOGRAPHIC_CENTER_US = { lat: 39.5, lng: -98.35 };

export function cityCenter(cityId: string): { lat: number; lng: number } {
  return CITY_CENTERS[cityId] ?? GEOGRAPHIC_CENTER_US;
}

export function allCityCentersResolved(): boolean {
  return hostCities.every((city) => CITY_CENTERS[city.id] !== undefined);
}
