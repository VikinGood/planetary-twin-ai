// Generates MOCK data for the Explorer so the dashboard can be built and demoed before
// the real export exists. Every file it writes is labeled mock: true and the UI shows a
// MOCK banner. Run: yarn mock   (scripts/export_static.py overwrites these files.)
// Portions generated with AI (Claude); reviewed by the team.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const CONFIG = path.resolve(here, '../../config');
const OUT = path.resolve(here, '../public/data');

const CHARS = ['topography', 'geology', 'thermal', 'aridity', 'ice_polar', 'volcanic_caves', 'surface_optics', 'illumination'];
const slug = (s) => s.replace(/[–—]/g, ' ').normalize('NFKD').replace(/[^\w\s-]/g, '').trim().toLowerCase().replace(/[\s-]+/g, '_');

// Seeded random numbers so the mock is the same on every run.
let seed = 20261115;
const rand = () => ((seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296);
const clamp = (x) => Math.max(0, Math.min(1, x));

// Land regions with rough traits: arid, polar, volcanic, cave, flat (0-1), albedo.
const REGIONS = [
  ['Puna de Atacama', -25, -67.5, 0.9, 0.1, 0.8, 0.5, 0.6, 0.3],
  ['Payunia volcanic field', -36.4, -69.2, 0.6, 0, 1, 0.8, 0.5, 0.12],
  ['Patagonian basalt plateaus', -47, -70.5, 0.6, 0.1, 0.8, 0.4, 0.8, 0.18],
  ['Altiplano salt flats', -20.3, -67.6, 0.8, 0.1, 0.3, 0, 1, 0.6],
  ['Namib Desert', -24.5, 15.3, 1, 0, 0.1, 0, 0.6, 0.35],
  ['Sahara, Tibesti', 20.8, 18, 1, 0, 0.8, 0.4, 0.4, 0.25],
  ['Sahara, Hoggar', 23.3, 5.6, 1, 0, 0.7, 0.3, 0.5, 0.28],
  ['Arabian Harrat Khaybar', 25.8, 39.9, 0.95, 0, 1, 0.9, 0.6, 0.14],
  ['Rub al Khali', 20.5, 50, 1, 0, 0, 0, 0.7, 0.38],
  ['Afar depression', 13, 41, 0.85, 0, 1, 0.6, 0.5, 0.16],
  ['Gobi Desert', 43, 104, 0.85, 0.2, 0.2, 0, 0.8, 0.3],
  ['Taklamakan Desert', 39, 83, 0.95, 0.1, 0, 0, 0.8, 0.33],
  ['Qaidam Basin', 37.5, 93, 0.9, 0.2, 0.1, 0, 0.9, 0.36],
  ['Tibetan Plateau, Changtang', 34.5, 85, 0.7, 0.5, 0.2, 0, 0.6, 0.27],
  ['Lut Desert', 30, 58.5, 1, 0, 0.1, 0, 0.6, 0.3],
  ['Great Victoria Desert', -28.5, 128, 0.85, 0, 0, 0, 0.9, 0.32],
  ['Pilbara', -22, 118, 0.75, 0, 0.2, 0, 0.6, 0.22],
  ['Kalahari', -23.5, 22, 0.7, 0, 0, 0, 0.9, 0.3],
  ['Mojave volcanic fields', 34.9, -116, 0.9, 0, 0.7, 0.6, 0.6, 0.2],
  ['Snake River Plain', 43.4, -113.5, 0.6, 0.2, 1, 0.9, 0.8, 0.15],
  ['Sonoran, Pinacate', 31.8, -113.5, 0.9, 0, 0.9, 0.6, 0.6, 0.16],
  ['Columbia Plateau', 47, -119.5, 0.5, 0.2, 0.9, 0.5, 0.8, 0.17],
  ['Canadian Arctic Archipelago', 76, -95, 0.7, 1, 0, 0, 0.6, 0.5],
  ['Greenland ice-free margin', 70, -51, 0.6, 1, 0.1, 0, 0.4, 0.45],
  ['Ellesmere Island', 80, -80, 0.75, 1, 0, 0, 0.5, 0.55],
  ['Taymyr Peninsula', 75, 100, 0.5, 1, 0, 0, 0.8, 0.4],
  ['Kamchatka lava fields', 55.8, 160.3, 0.3, 0.6, 1, 0.8, 0.4, 0.12],
  ['Yakutia permafrost plains', 66, 125, 0.4, 0.9, 0, 0, 0.9, 0.35],
  ['Antarctic Peninsula ice-free', -63.5, -57, 0.7, 1, 0.5, 0.2, 0.4, 0.5],
  ['Transantarctic nunataks', -84, -170, 0.95, 1, 0.1, 0, 0.3, 0.6],
  ['Ethiopian Highlands lava', 11.5, 39.5, 0.4, 0, 0.9, 0.6, 0.4, 0.13],
  ['Deccan Traps', 19, 75, 0.4, 0, 0.9, 0.3, 0.7, 0.14],
  ['Siberian Traps', 66, 95, 0.4, 0.9, 0.9, 0.3, 0.6, 0.15],
  ['Mongolian volcanic plateau', 47.5, 99, 0.6, 0.4, 0.8, 0.6, 0.7, 0.15],
  ['Sinai Peninsula', 29, 33.8, 0.95, 0, 0.3, 0.1, 0.5, 0.3],
  ['Danakil salt plain', 14.2, 40.3, 1, 0, 0.6, 0.2, 0.9, 0.45],
  ['Karakum Desert', 39.5, 60, 0.9, 0.1, 0, 0, 0.8, 0.31],
  ['Thar Desert', 27, 71, 0.85, 0, 0, 0, 0.8, 0.3],
  ['Chihuahuan basalt fields', 31.5, -107.2, 0.85, 0, 0.7, 0.5, 0.7, 0.18],
  ['Andean altiplano volcanoes', -22.5, -68, 0.85, 0.2, 1, 0.5, 0.4, 0.2],
];

// Known analogs (validation set). Cells within 1 degree are flagged is_known_analog.
const KNOWN = [
  ['Atacama Desert core', -24.1, -70.0],
  ['Haughton Crater, Devon Island', 75.4, -89.7],
  ['Death Valley', 36.5, -117.1],
  ['McMurdo Dry Valleys', -77.5, 162.0],
  ['Svalbard', 79.0, 16.0],
  ['Rio Tinto', 37.7, -6.6],
  ['Craters of the Moon, Idaho', 43.4, -113.5],
  ['Lanzarote', 29.0, -13.6],
  ['Mauna Kea, Hawaii', 19.8, -155.5],
  ['Iceland central highlands', 64.9, -17.5],
];

const mission = (file) => JSON.parse(fs.readFileSync(path.join(CONFIG, 'missions', file), 'utf8'));
const characteristics = JSON.parse(fs.readFileSync(path.join(CONFIG, 'characteristics.json'), 'utf8'));

const presets = {};
for (const key of ['moon-landing', 'moon-base', 'mars-landing', 'mars-base']) {
  const m = mission(`${key}.json`);
  presets[key.replace('-', '_')] = {
    body: m.body,
    mission_type: m.mission_type,
    default_characteristics: m.default_characteristics,
    default_weights: m.default_weights,
    targets: m.reference_targets.map((t) => ({
      id: slug(t.name),
      name: t.name,
      lat: t.lat,
      lon: t.lon,
      description: t.description,
      coordinate_status: t.coordinate_status,
      value_origin: 'literature',
    })),
  };
}

// How well a trait set matches each characteristic for a body and mission.
function charScores(tr, body, missionType, targetBias) {
  const [arid, polar, volcanic, cave, flat, albedo] = tr;
  const targetAlbedo = body === 'moon' ? 0.12 : 0.25;
  const n = () => (rand() - 0.5) * 0.18;
  const s = {
    topography: missionType === 'landing' ? flat : 0.5 * flat + 0.5 * (1 - flat) * 0.9,
    geology: body === 'moon' ? 0.3 + 0.7 * volcanic : 0.4 + 0.3 * volcanic + 0.3 * arid,
    thermal: body === 'moon' ? 0.3 + 0.4 * polar + 0.3 * arid : 0.3 + 0.4 * arid + 0.3 * polar,
    aridity: arid,
    ice_polar: polar * (body === 'mars' ? 0.9 : 1),
    volcanic_caves: 0.15 + 0.85 * cave * volcanic,
    surface_optics: Math.exp(-((albedo - targetAlbedo) ** 2) / (2 * 0.08 ** 2)),
    illumination: body === 'moon' ? 0.2 + 0.8 * polar : 0.5 + 0.3 * (1 - polar),
  };
  const out = {};
  for (const c of CHARS) out[c] = Math.round(clamp(s[c] + n() + targetBias[c]) * 1000) / 1000;
  return out;
}

function buildCollection(presetKey) {
  const p = presets[presetKey];
  const features = [];
  const biases = Object.fromEntries(p.targets.map((t) => [t.id, Object.fromEntries(CHARS.map((c) => [c, (rand() - 0.5) * 0.12]))]));
  for (const [name, lat0, lon0, ...traits] of REGIONS) {
    for (let k = 0; k < 24; k++) {
      const lat = Math.round((lat0 + (rand() - 0.5) * 3) * 4) / 4 + 0.125;
      const lon = Math.round((lon0 + (rand() - 0.5) * 3) * 4) / 4 + 0.125;
      const scores = Object.fromEntries(CHARS.map((c) => [c, {}]));
      for (const t of p.targets) {
        const s = charScores(traits, p.body, p.mission_type, biases[t.id]);
        for (const c of CHARS) scores[c][t.id] = s[c];
      }
      const [arid, polar, volcanic, cave, flat, albedo] = traits;
      const tags = [];
      if (Math.abs(lat) > 60 || polar > 0.8) tags.push('polar');
      if (arid > 0.85) tags.push('desert');
      if (arid > 0.6) tags.push('arid');
      if (volcanic > 0.6) tags.push('volcanic');
      if (cave * volcanic > 0.4) tags.push('cave');
      const known = KNOWN.find(([, la, lo]) => Math.abs(la - lat) <= 1 && Math.abs(lo - lon) <= 1);
      features.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [lon, lat] },
        properties: {
          cell_id: `E_${lat.toFixed(3)}_${lon.toFixed(3)}`,
          lat_center: lat,
          lon_center: lon,
          region_hint: name,
          land_fraction: 1,
          is_known_analog: Boolean(known),
          known_analog_name: known ? known[0] : null,
          environment_tags: tags,
          scores,
          confidence: { volcanic_caves: 'low', thermal: 'medium' },
          values: {
            slope_mean_deg: { value: Math.round((1 + (1 - flat) * 14 + rand() * 2) * 10) / 10, units: 'degrees', source: 'MOCK' },
            broadband_albedo: { value: Math.round(clamp(albedo + (rand() - 0.5) * 0.05) * 100) / 100, units: '0-1', source: 'MOCK' },
            aridity_index: { value: Math.round((1 - arid) * 0.5 * 1000) / 1000, units: 'P/PET', source: 'MOCK' },
            longest_polar_night_days: { value: Math.abs(lat) > 66.56 ? Math.round((Math.abs(lat) - 66.56) * 7) : 0, units: 'days', source: 'MOCK' },
          },
        },
      });
    }
  }
  // Keep one cell per grid position.
  const seen = new Set();
  const unique = features.filter((f) => !seen.has(f.properties.cell_id) && seen.add(f.properties.cell_id));
  return { type: 'FeatureCollection', mock: true, features: unique };
}

fs.mkdirSync(OUT, { recursive: true });
const meta = {
  mock: true,
  generated_at: new Date().toISOString(),
  note: 'MOCK data for interface development. Replaced by scripts/export_static.py.',
  characteristics: characteristics.map((c) => ({
    id: c.id,
    name: c.name,
    description: c.description,
    comparison_rule: c.comparison_rule,
    proxy: c.proxy_label === 'PROXY',
  })),
  presets,
  cannot_reproduce: {
    moon: ['Gravity: 1/6 g (1.62 m/s²)', 'Vacuum: about 10⁻¹⁰ Pa', 'Unfiltered solar and cosmic radiation', 'Absolute temperatures from about 40 K to 400 K', '14-day day/night cycle', 'Near-horizon sun all year at the south pole: on Earth the yearly maximum sun elevation is at least 23.4°', 'Sharp-edged, electrostatically charged regolith'],
    mars: ['Gravity: 0.38 g (3.72 m/s²)', 'Atmosphere: about 0.6 kPa, 95% CO₂', 'No ozone layer: full UV and ionizing radiation', 'Global dust storms', 'Absolute temperatures from about −140 °C to +20 °C', 'Perchlorates in the regolith'],
  },
  known_analogs: KNOWN.map(([name, lat, lon]) => ({ name, lat, lon })),
};
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));
for (const key of Object.keys(presets)) {
  const col = buildCollection(key);
  fs.writeFileSync(path.join(OUT, `${key}.json`), JSON.stringify(col));
  console.log(`${key}.json: ${col.features.length} MOCK cells`);
}
console.log('meta.json written (mock: true)');
