// World map with ranked candidates and known analogs.
// Portions generated with AI (Claude); reviewed by the team.
import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';

const OSM_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      maxzoom: 19,
      attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

/**
 * layers: [{ key, label, rows: ranked rows, className }]
 * knownAnalogs: [{ name, lat, lon }]
 */
export default function MapView({ layers, knownAnalogs, selectedKey, onSelect }) {
  const ref = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: ref.current,
      style: OSM_STYLE,
      center: [0, 15],
      zoom: 0.9,
      minZoom: 0.4,
      attributionControl: { compact: false },
      renderWorldCopies: true,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    mapRef.current = map;
    window.__ptaiMap = map; // handy for debugging in the browser console
    return () => map.remove();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    for (const k of knownAnalogs || []) {
      const el = document.createElement('div');
      el.className = 'marker-known';
      el.title = `Known analog: ${k.name}`;
      markersRef.current.push(new maplibregl.Marker({ element: el }).setLngLat([k.lon, k.lat]).addTo(map));
    }

    for (const layer of layers) {
      for (const row of layer.rows) {
        const p = row.feature.properties;
        const key = `${layer.key}:${p.cell_id}`;
        const el = document.createElement('button');
        el.type = 'button';
        el.className = `marker ${layer.className} ${row.both ? 'both' : ''} ${selectedKey === key ? 'selected' : ''}`;
        el.textContent = row.rank;
        el.style.setProperty('--score', row.total.toFixed(3));
        el.title = `${layer.label} #${row.rank} · score ${row.total.toFixed(2)} · ${p.lat_center.toFixed(2)}, ${p.lon_center.toFixed(2)}`;
        el.addEventListener('click', (e) => {
          e.stopPropagation();
          onSelect(key, layer.key, row);
        });
        markersRef.current.push(new maplibregl.Marker({ element: el }).setLngLat([p.lon_center, p.lat_center]).addTo(map));
      }
    }
  }, [layers, knownAnalogs, selectedKey, onSelect]);

  // Frame the candidates whenever the ranked set changes (not when a marker is selected).
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const pts = layers.flatMap((l) => l.rows.map((r) => [r.feature.properties.lon_center, r.feature.properties.lat_center]));
    if (pts.length === 0) return;
    const b = new maplibregl.LngLatBounds(pts[0], pts[0]);
    pts.forEach((pt) => b.extend(pt));
    map.fitBounds(b, { padding: 60, maxZoom: 4, duration: 600 });
  }, [layers]);

  return <div ref={ref} className="map" role="region" aria-label="World map of candidate analog sites" />;
}
