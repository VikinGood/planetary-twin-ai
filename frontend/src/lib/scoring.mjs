// Client-side ranking for the Explorer dashboard.
// Portions generated with AI (Claude); reviewed by the team.
//
// The exported files store one score in [0, 1] per characteristic and per target for
// every candidate cell. The dashboard combines the characteristics the user selects with
// a weighted geometric mean (docs/METHODOLOGY.md): total = prod(s_i ^ w_i), with the
// weights normalized over the selected characteristics.
//
// Score values in the export:
//   0..1   similarity. Values below SCORE_FLOOR (rounding zeros, "low likelihood") are
//          raised to SCORE_FLOOR: heavily penalized, but they do not drop the cell.
//   -1     a hard requirement failed (for example landing slope above the cap): the cell
//          is dropped when that characteristic is selected.
//   null   no data: left out of the product; it lowers `coverage`, shown in the UI.

export const SCORE_FLOOR = 0.01;
export const HARD_FAIL = -1;

/** Normalize the weights of the selected characteristics so they sum to 1. */
export function normalizeWeights(selected, weights) {
  const raw = selected.map((id) => Math.max(0, Number(weights[id] ?? 0)));
  const sum = raw.reduce((a, b) => a + b, 0);
  const out = {};
  selected.forEach((id, i) => {
    out[id] = sum > 0 ? raw[i] / sum : 1 / selected.length;
  });
  return out;
}

/**
 * Score one cell for one target.
 * @returns {{total: number|null, coverage: number, parts: Array}}
 */
export function scoreCell(feature, targetId, selected, weights) {
  const w = normalizeWeights(selected, weights);
  const scores = feature.properties.scores || {};
  let logSum = 0;
  let usedWeight = 0;
  let zero = false;
  const parts = selected.map((id) => {
    const value = scores[id]?.[targetId];
    const has = typeof value === 'number' && Number.isFinite(value);
    if (has) {
      usedWeight += w[id];
      if (value < 0) zero = true; // hard requirement failed
      else logSum += w[id] * Math.log(Math.min(1, Math.max(SCORE_FLOOR, value)));
    }
    return { id, score: has ? (value < 0 ? 0 : value) : null, weight: w[id], hardFail: has && value < 0 };
  });
  if (usedWeight === 0) return { total: null, coverage: 0, parts };
  // Geometric mean over the characteristics that have data, re-normalized.
  const total = zero ? 0 : Math.exp(logSum / usedWeight);
  return { total, coverage: usedWeight, parts };
}

/** Does the cell pass the environment-family and known-analog filters? */
export function passesFilters(feature, { tags = [], excludeKnown = true } = {}) {
  const p = feature.properties;
  if (excludeKnown && p.is_known_analog) return false;
  if (tags.length > 0) {
    const cellTags = p.environment_tags || [];
    if (!tags.some((t) => cellTags.includes(t))) return false;
  }
  return true;
}

/**
 * Rank features for one target and selection; returns the top `limit`.
 * Neighbouring 0.25 deg cells are near duplicates, so by default a candidate is kept only
 * if it is at least `minSeparationDeg` (lat and lon) away from every better one: the top
 * list shows distinct places instead of ten cells of the same region.
 */
export function rankCandidates(features, { targetId, selected, weights, tags, excludeKnown, limit = 10, minSeparationDeg = 3 }) {
  const rows = [];
  for (const f of features) {
    if (!passesFilters(f, { tags, excludeKnown })) continue;
    const r = scoreCell(f, targetId, selected, weights);
    if (r.total === null) continue;
    rows.push({ feature: f, ...r });
  }
  rows.sort((a, b) => b.total - a.total || b.coverage - a.coverage);
  const kept = [];
  for (const r of rows) {
    if (kept.length >= limit) break;
    const p = r.feature.properties;
    const tooClose =
      minSeparationDeg > 0 &&
      kept.some((k) => {
        const q = k.feature.properties;
        return Math.abs(p.lat_center - q.lat_center) < minSeparationDeg && Math.abs(p.lon_center - q.lon_center) < minSeparationDeg;
      });
    if (!tooClose) kept.push(r);
  }
  return kept.map((r, i) => ({ ...r, rank: i + 1 }));
}

/** Share of known analogs that land in the top N when they are not excluded. */
export function knownAnalogRecall(features, opts, topN = 100) {
  const known = features.filter((f) => f.properties.is_known_analog).length;
  if (known === 0) return null;
  const top = rankCandidates(features, { ...opts, excludeKnown: false, limit: topN, minSeparationDeg: 0 });
  const hits = top.filter((r) => r.feature.properties.is_known_analog).length;
  return { hits, known, topN };
}

/** Cells that rank high in both lists (same cell, or within `toleranceDeg`). */
export function overlap(listA, listB, toleranceDeg = 0.5) {
  const pairs = [];
  for (const a of listA) {
    const pa = a.feature.properties;
    for (const b of listB) {
      const pb = b.feature.properties;
      if (
        pa.cell_id === pb.cell_id ||
        (Math.abs(pa.lat_center - pb.lat_center) <= toleranceDeg &&
          Math.abs(pa.lon_center - pb.lon_center) <= toleranceDeg)
      ) {
        pairs.push({ a, b });
        break;
      }
    }
  }
  return pairs;
}
