"use client";

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Hotspot } from "@/lib/api/fan";
import { hotspotRadius, scoreColor } from "@/lib/heatmap-utils";
import { HotspotPopup } from "./hotspot-popup";

type BoundsFitterProps = {
  hotspots: Hotspot[];
  fallbackCenter: { lat: number; lng: number };
};

function BoundsFitter({ hotspots, fallbackCenter }: BoundsFitterProps) {
  const map = useMap();
  const prevCityKey = useRef<string>("");
  const centerKey = `${fallbackCenter.lat},${fallbackCenter.lng}`;

  useEffect(() => {
    const changed = prevCityKey.current !== centerKey;
    prevCityKey.current = centerKey;

    if (hotspots.length === 0) {
      map.setView([fallbackCenter.lat, fallbackCenter.lng], 11);
      return;
    }

    const lats = hotspots.map((h) => h.center.lat);
    const lngs = hotspots.map((h) => h.center.lng);

    if (changed || hotspots.length > 0) {
      map.fitBounds(
        [
          [Math.min(...lats), Math.min(...lngs)],
          [Math.max(...lats), Math.max(...lngs)],
        ],
        { padding: [48, 48], maxZoom: 13 }
      );
    }
  }, [hotspots, fallbackCenter, map, centerKey]);

  return null;
}

type HotspotMapProps = {
  hotspots: Hotspot[];
  fallbackCenter: { lat: number; lng: number };
};

export function HotspotMap({ hotspots, fallbackCenter }: HotspotMapProps) {
  return (
    <MapContainer
      center={[fallbackCenter.lat, fallbackCenter.lng]}
      zoom={11}
      className="h-full w-full"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <BoundsFitter hotspots={hotspots} fallbackCenter={fallbackCenter} />
      {hotspots.map((hotspot) => (
        <CircleMarker
          key={hotspot.hotspot_id}
          center={[hotspot.center.lat, hotspot.center.lng]}
          radius={hotspotRadius(hotspot.supporter_count)}
          pathOptions={{
            fillColor: scoreColor(hotspot.score),
            fillOpacity: 0.75,
            color: scoreColor(hotspot.score),
            weight: 1.5,
          }}
        >
          <Popup>
            <HotspotPopup hotspot={hotspot} />
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
