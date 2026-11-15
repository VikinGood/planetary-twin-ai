// Unit tests for the client-side ranking. Run: yarn test
import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeWeights, scoreCell, rankCandidates, passesFilters, overlap, knownAnalogRecall } from './scoring.mjs';

const cell = (id, scores, extra = {}) => ({
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [0, 0] },
  properties: { cell_id: id, lat_center: 0, lon_center: 0, environment_tags: [], is_known_analog: false, scores, ...extra },
});

test('weights are normalized over the selection', () => {
  const w = normalizeWeights(['a', 'b'], { a: 0.35, b: 0.15, c: 0.5 });
  assert.ok(Math.abs(w.a - 0.7) < 1e-9);
  assert.ok(Math.abs(w.b - 0.3) < 1e-9);
});

test('weighted geometric mean matches the methodology formula', () => {
  const f = cell('x', { topography: { t: 0.779 }, surface_optics: { t: 0.923 }, thermal: { t: 0.906 }, illumination: { t: 0.636 } });
  const weights = { topography: 0.35, surface_optics: 0.2, thermal: 0.2, illumination: 0.25 };
  const r = scoreCell(f, 't', Object.keys(weights), weights);
  const expected = 0.779 ** 0.35 * 0.923 ** 0.2 * 0.906 ** 0.2 * 0.636 ** 0.25;
  assert.ok(Math.abs(r.total - expected) < 1e-9);
  assert.equal(r.coverage, 1);
});

test('a zero on a selected characteristic drops the cell', () => {
  const f = cell('x', { a: { t: 0 }, b: { t: 1 } });
  assert.equal(scoreCell(f, 't', ['a', 'b'], { a: 0.5, b: 0.5 }).total, 0);
});

test('missing data reduces coverage instead of counting as zero', () => {
  const f = cell('x', { a: { t: 0.81 }, b: { t: null } });
  const r = scoreCell(f, 't', ['a', 'b'], { a: 0.5, b: 0.5 });
  assert.ok(Math.abs(r.total - 0.81) < 1e-9);
  assert.equal(r.coverage, 0.5);
});

test('ranking changes when the selection changes', () => {
  const fs = [cell('A', { a: { t: 0.9 }, b: { t: 0.2 } }), cell('B', { a: { t: 0.5 }, b: { t: 0.9 } })];
  const onlyA = rankCandidates(fs, { targetId: 't', selected: ['a'], weights: { a: 1 }, tags: [], excludeKnown: true });
  const onlyB = rankCandidates(fs, { targetId: 't', selected: ['b'], weights: { b: 1 }, tags: [], excludeKnown: true });
  assert.equal(onlyA[0].feature.properties.cell_id, 'A');
  assert.equal(onlyB[0].feature.properties.cell_id, 'B');
});

test('neighbouring cells are collapsed so the top list shows distinct places', () => {
  const near = (id, lat, s) => cell(id, { a: { t: s } }, { lat_center: lat, lon_center: 0 });
  const fs = [near('A', 0, 0.9), near('B', 0.25, 0.89), near('C', 10, 0.5)];
  const top = rankCandidates(fs, { targetId: 't', selected: ['a'], weights: { a: 1 }, tags: [], excludeKnown: true });
  assert.deepEqual(top.map((r) => r.feature.properties.cell_id), ['A', 'C']);
  const all = rankCandidates(fs, { targetId: 't', selected: ['a'], weights: { a: 1 }, tags: [], excludeKnown: true, minSeparationDeg: 0 });
  assert.equal(all.length, 3);
});

test('filters: known analogs and environment tags', () => {
  const k = cell('K', {}, { is_known_analog: true, environment_tags: ['volcanic'] });
  assert.equal(passesFilters(k, { excludeKnown: true }), false);
  assert.equal(passesFilters(k, { excludeKnown: false, tags: ['volcanic'] }), true);
  assert.equal(passesFilters(k, { excludeKnown: false, tags: ['polar'] }), false);
});

test('overlap finds the same cell in both lists', () => {
  const a = [{ feature: cell('X', {}) }];
  const b = [{ feature: cell('X', {}) }];
  assert.equal(overlap(a, b).length, 1);
});

test('known analog recall counts hits in the top N', () => {
  const fs = [cell('K', { a: { t: 0.9 } }, { is_known_analog: true }), cell('N', { a: { t: 0.1 } })];
  const r = knownAnalogRecall(fs, { targetId: 't', selected: ['a'], weights: { a: 1 }, tags: [] }, 1);
  assert.deepEqual(r, { hits: 1, known: 1, topN: 1 });
});
