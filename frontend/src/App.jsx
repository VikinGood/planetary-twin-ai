// Planetary Twin AI Explorer — main view.
// Portions generated with AI (Claude); reviewed by the team.
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import MapView from './components/MapView.jsx';
import CandidateCard from './components/CandidateCard.jsx';
import { loadCollection, loadMeta } from './lib/data.js';
import { knownAnalogRecall, overlap, rankCandidates } from './lib/scoring.mjs';
import { FAMILIES } from './lib/activities.js';

const presetKey = (body, missionType) => `${body}_${missionType}`;
const MISSION_LABEL = { landing: 'Landing site', base: 'Permanent base' };

function initialSelection(meta) {
  const sel = {};
  for (const [key, p] of Object.entries(meta.presets)) {
    sel[key] = {
      targetId: p.targets[0]?.id,
      selected: [...p.default_characteristics],
      weights: { ...p.default_weights },
    };
  }
  return sel;
}

export default function App() {
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);
  const [body, setBody] = useState('moon');
  const [mode, setMode] = useState('landing'); // landing | base | compare
  const [selection, setSelection] = useState({});
  const [collections, setCollections] = useState({});
  const [tags, setTags] = useState([]);
  const [excludeKnown, setExcludeKnown] = useState(true);
  const [picked, setPicked] = useState(null); // { key, presetKey, row }

  useEffect(() => {
    loadMeta()
      .then((m) => {
        setMeta(m);
        setSelection(initialSelection(m));
      })
      .catch((e) => setError(String(e)));
  }, []);

  const visibleKeys = mode === 'compare' ? [presetKey(body, 'landing'), presetKey(body, 'base')] : [presetKey(body, mode)];

  useEffect(() => {
    if (!meta) return;
    for (const k of visibleKeys) {
      if (collections[k]) continue;
      loadCollection(k)
        .then((c) => setCollections((prev) => ({ ...prev, [k]: c })))
        .catch((e) => setError(String(e)));
    }
  }, [meta, body, mode]); // eslint-disable-line react-hooks/exhaustive-deps

  const ranked = useMemo(() => {
    const out = {};
    for (const k of visibleKeys) {
      const col = collections[k];
      const s = selection[k];
      if (!col || !s) continue;
      const opts = { targetId: s.targetId, selected: s.selected, weights: s.weights, tags, excludeKnown };
      out[k] = {
        rows: s.selected.length ? rankCandidates(col.features, { ...opts, limit: 10 }) : [],
        recall: s.selected.length ? knownAnalogRecall(col.features, opts, 100) : null,
      };
    }
    if (mode === 'compare') {
      const [a, b] = visibleKeys;
      if (out[a] && out[b]) {
        const pairs = overlap(out[a].rows, out[b].rows);
        const inA = new Set(pairs.map((x) => x.a.feature.properties.cell_id));
        const inB = new Set(pairs.map((x) => x.b.feature.properties.cell_id));
        out[a].rows = out[a].rows.map((r) => ({ ...r, both: inA.has(r.feature.properties.cell_id) }));
        out[b].rows = out[b].rows.map((r) => ({ ...r, both: inB.has(r.feature.properties.cell_id) }));
        out.overlapCount = pairs.length;
      }
    }
    return out;
  }, [collections, selection, tags, excludeKnown, mode, body]); // eslint-disable-line react-hooks/exhaustive-deps

  const layers = useMemo(
    () =>
      visibleKeys
        .filter((k) => ranked[k])
        .map((k) => ({
          key: k,
          label: MISSION_LABEL[meta.presets[k].mission_type],
          rows: ranked[k].rows,
          className: mode === 'compare' ? `layer-${meta.presets[k].mission_type}` : 'layer-single',
        })),
    [ranked] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const onSelect = useCallback((key, pk, row) => setPicked({ key, presetKey: pk, row }), []);

  // Keep the open card in sync with re-ranking; close it if the cell left the list.
  useEffect(() => {
    if (!picked) return;
    const rows = ranked[picked.presetKey]?.rows || [];
    const row = rows.find((r) => r.feature.properties.cell_id === picked.row.feature.properties.cell_id);
    if (!row) setPicked(null);
    else if (row !== picked.row) setPicked({ ...picked, row });
  }, [ranked]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <div className="fatal">Could not load data: {error}</div>;
  if (!meta) return <div className="fatal">Loading…</div>;

  const charNames = Object.fromEntries(meta.characteristics.map((c) => [c.id, c.name]));
  const isMock = meta.mock || Object.values(collections).some((c) => c.mock);

  const update = (k, fn) => setSelection((prev) => ({ ...prev, [k]: fn(prev[k]) }));
  const toggleChar = (k, id) =>
    update(k, (s) => {
      const on = s.selected.includes(id);
      const selected = on ? s.selected.filter((x) => x !== id) : [...s.selected, id];
      const weights = { ...s.weights };
      if (!on && !(weights[id] > 0)) weights[id] = 0.15;
      return { ...s, selected, weights };
    });
  const resetPreset = (k) => update(k, () => initialSelection({ presets: { [k]: meta.presets[k] } })[k]);

  return (
    <div className="app">
      {isMock && (
        <div className="mock-banner" role="status">
          MOCK DATA — interface preview. Scores and values are synthetic until the real export replaces them.
        </div>
      )}
      <header className="topbar">
        <div>
          <h1>Planetary Twin AI</h1>
          <p className="muted">New Earth analogs for Moon and Mars landing sites and permanent bases</p>
        </div>
        <div className="segmented" role="group" aria-label="Planetary body">
          {['moon', 'mars'].map((b) => (
            <button key={b} type="button" className={body === b ? 'on' : ''} onClick={() => { setBody(b); setPicked(null); }}>
              {b === 'moon' ? 'Moon' : 'Mars'}
            </button>
          ))}
        </div>
        <div className="segmented" role="group" aria-label="Mission type">
          {['landing', 'base', 'compare'].map((m) => (
            <button key={m} type="button" className={mode === m ? 'on' : ''} onClick={() => { setMode(m); setPicked(null); }}>
              {m === 'compare' ? 'Compare both' : MISSION_LABEL[m]}
            </button>
          ))}
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          {visibleKeys.map((k) => {
            const p = meta.presets[k];
            const s = selection[k];
            if (!p || !s) return null;
            return (
              <section key={k} className={`panel ${mode === 'compare' ? `panel-${p.mission_type}` : ''}`}>
                <div className="panel-head">
                  <h2>{MISSION_LABEL[p.mission_type]}</h2>
                  <button type="button" className="link-btn" onClick={() => resetPreset(k)}>
                    Reset preset
                  </button>
                </div>
                <label className="field">
                  <span>Reference target</span>
                  <select value={s.targetId} onChange={(e) => update(k, (x) => ({ ...x, targetId: e.target.value }))}>
                    {p.targets.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </label>
                <fieldset className="chips">
                  <legend>Characteristics (select one or more)</legend>
                  {meta.characteristics.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      className={`chip ${s.selected.includes(c.id) ? 'on' : ''}`}
                      aria-pressed={s.selected.includes(c.id)}
                      title={c.description}
                      onClick={() => toggleChar(k, c.id)}
                    >
                      {c.name}
                      {c.proxy ? ' (proxy)' : ''}
                    </button>
                  ))}
                </fieldset>
                {s.selected.length === 0 && <p className="warn">Select at least one characteristic.</p>}
                <div className="weights">
                  {s.selected.map((id) => {
                    const total = s.selected.reduce((a, x) => a + (Number(s.weights[x]) || 0), 0) || 1;
                    return (
                      <label key={id} className="weight">
                        <span>
                          {charNames[id]} <b>{Math.round(((Number(s.weights[id]) || 0) / total) * 100)}%</b>
                        </span>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={s.weights[id] ?? 0}
                          onChange={(e) => update(k, (x) => ({ ...x, weights: { ...x.weights, [id]: Number(e.target.value) } }))}
                        />
                      </label>
                    );
                  })}
                </div>
                {ranked[k]?.recall && (
                  <p className="badge" title="Known analogs found in the top 100 when they are not excluded">
                    Validation: {ranked[k].recall.hits} of {ranked[k].recall.known} known analogs in the top {ranked[k].recall.topN}
                  </p>
                )}
              </section>
            );
          })}

          <section className="panel">
            <fieldset className="chips">
              <legend>Environment family (challenge list)</legend>
              {FAMILIES.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`chip ${tags.includes(t) ? 'on' : ''}`}
                  aria-pressed={tags.includes(t)}
                  onClick={() => setTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))}
                >
                  {t}
                </button>
              ))}
            </fieldset>
            <label className="switch">
              <input type="checkbox" checked={excludeKnown} onChange={(e) => setExcludeKnown(e.target.checked)} />
              <span>Exclude known analogs (show only new candidates)</span>
            </label>
          </section>
        </aside>

        <main className="main">
          <MapView
            layers={layers}
            knownAnalogs={meta.known_analogs}
            selectedKey={picked?.key}
            onSelect={onSelect}
          />
          {mode === 'compare' && ranked.overlapCount !== undefined && (
            <p className="compare-note">
              <span className="dot dot-landing" /> Landing site <span className="dot dot-base" /> Permanent base{' '}
              <span className="dot dot-both" /> Top 10 in both: {ranked.overlapCount}
            </p>
          )}
          <div className={`rankings ${mode === 'compare' ? 'two' : ''}`}>
            {visibleKeys.map((k) => {
              const p = meta.presets[k];
              const r = ranked[k];
              const target = p.targets.find((t) => t.id === selection[k]?.targetId);
              return (
                <section key={k} className="ranking">
                  <h2>
                    Top 10 · {MISSION_LABEL[p.mission_type]} · {target?.name}
                  </h2>
                  {!r && <p className="muted">Loading…</p>}
                  {r && r.rows.length === 0 && <p className="muted">No candidates match the current filters.</p>}
                  <ol>
                    {r?.rows.map((row) => {
                      const fp = row.feature.properties;
                      const key = `${k}:${fp.cell_id}`;
                      return (
                        <li key={fp.cell_id}>
                          <button
                            type="button"
                            className={`row ${picked?.key === key ? 'on' : ''}`}
                            onClick={() => onSelect(key, k, row)}
                          >
                            <span className="rank">{row.rank}</span>
                            <span className="row-main">
                              <span>{fp.region_hint || fp.cell_id}</span>
                              <span className="muted small">
                                {fp.lat_center.toFixed(2)}°, {fp.lon_center.toFixed(2)}° · {(fp.environment_tags || []).join(', ') || 'no tags'}
                                {row.both ? ' · in both lists' : ''}
                              </span>
                            </span>
                            <span className="row-score">{row.total.toFixed(2)}</span>
                          </button>
                        </li>
                      );
                    })}
                  </ol>
                </section>
              );
            })}
          </div>
        </main>

        {picked && meta.presets[picked.presetKey] && (
          <CandidateCard
            row={picked.row}
            preset={meta.presets[picked.presetKey]}
            presetKey={picked.presetKey}
            target={meta.presets[picked.presetKey].targets.find((t) => t.id === selection[picked.presetKey].targetId)}
            charNames={charNames}
            cannotReproduce={meta.cannot_reproduce?.[meta.presets[picked.presetKey].body] || picked.row.feature.properties.cannot_reproduce || []}
            onClose={() => setPicked(null)}
          />
        )}
      </div>

      <footer className="footer muted small">
        Data: NASA (LOLA, MOLA, TES, MODIS), Copernicus DEM, TerraClimate and others listed in the README. Map ©
        OpenStreetMap contributors. Scores combine only the selected characteristics with a weighted geometric mean.
        Built with AI assistance (see README, Use of Artificial Intelligence).
      </footer>
    </div>
  );
}
