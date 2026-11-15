// Loads the static export (or another base URL) for the Explorer.
// Portions generated with AI (Claude); reviewed by the team.
//
// Files expected under DATA_BASE:
//   meta.json                         characteristics, presets (targets), cannot_reproduce, known_analogs
//   {body}_{mission_type}.json        GeoJSON FeatureCollection from scripts/export_static.py
//   validation.json                   optional, Phase 6 (scripts/validate_phase6.py)
//   interpretations/{body}_{mission_type}/{target_id}/{cell_id}.json   optional, Phase 4
//
// Data source switch: ?data=<base url> in the page URL, or VITE_DATA_BASE at build time.

const fromQuery = new URLSearchParams(window.location.search).get('data');
export const DATA_BASE = (fromQuery || import.meta.env.VITE_DATA_BASE || 'data/').replace(/\/?$/, '/');

const cache = new Map();

async function getJson(path) {
  if (cache.has(path)) return cache.get(path);
  const p = fetch(DATA_BASE + path).then((r) => {
    if (!r.ok) throw new Error(`${r.status} loading ${DATA_BASE + path}`);
    return r.json();
  });
  cache.set(path, p);
  p.catch(() => cache.delete(path));
  return p;
}

export const loadMeta = () => getJson('meta.json');
export const loadValidation = () => getJson('validation.json').catch(() => null);
export const loadCollection = (presetKey) => getJson(`${presetKey}.json`);

export async function loadInterpretation(presetKey, targetId, cellId) {
  try {
    return await getJson(`interpretations/${presetKey}/${targetId}/${cellId}.json`);
  } catch {
    return null;
  }
}
