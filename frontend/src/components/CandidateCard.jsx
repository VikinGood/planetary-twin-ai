// Characterization card for one candidate.
// Portions generated with AI (Claude); reviewed by the team.
import React, { useEffect, useState } from 'react';
import { evaluateActivities } from '../lib/activities.js';
import { loadInterpretation } from '../lib/data.js';

const pct = (x) => `${Math.round(x * 100)}%`;

export default function CandidateCard({ row, preset, presetKey, target, charNames, cannotReproduce, onClose }) {
  const p = row.feature.properties;
  const [interp, setInterp] = useState(undefined);

  useEffect(() => {
    let alive = true;
    setInterp(undefined);
    loadInterpretation(presetKey, target.id, p.cell_id).then((x) => alive && setInterp(x));
    return () => {
      alive = false;
    };
  }, [presetKey, target.id, p.cell_id]);

  const activities = evaluateActivities(preset.mission_type, row.parts);
  const values = p.values || {};
  const conf = p.confidence || {};

  return (
    <aside className="card" aria-label="Candidate details">
      <header className="card-head">
        <div>
          <p className="eyebrow">
            #{row.rank} · {preset.body === 'moon' ? 'Moon' : 'Mars'} · {preset.mission_type === 'landing' ? 'Landing site' : 'Permanent base'}
          </p>
          <h2>{p.region_hint || `Cell ${p.cell_id}`}</h2>
          <p className="muted">
            {p.lat_center.toFixed(3)}°, {p.lon_center.toFixed(3)}° · 0.25° cell · analog of {target.name}
          </p>
        </div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close details">
          ×
        </button>
      </header>

      <section className="score-block">
        <div className="big-score">{row.total.toFixed(2)}</div>
        <div>
          <div className="muted">Combined score (weighted geometric mean)</div>
          <div className="muted">Data coverage: {pct(row.coverage)} of selected weight</div>
        </div>
      </section>

      <div className="tags">
        {(p.environment_tags || []).map((t) => (
          <span key={t} className="tag">{t}</span>
        ))}
        {p.is_known_analog && <span className="tag tag-known">known analog{p.known_analog_name ? `: ${p.known_analog_name}` : ''}</span>}
      </div>

      <h3>Score by characteristic</h3>
      <ul className="bars">
        {row.parts.map((part) => (
          <li key={part.id}>
            <div className="bar-label">
              <span>{charNames[part.id] || part.id}</span>
              <span className="muted">
                {part.score === null ? 'no data' : part.score.toFixed(2)} · weight {pct(part.weight)}
                {conf[part.id] ? ` · ${conf[part.id]} confidence` : ''}
              </span>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: part.score === null ? 0 : pct(part.score) }} />
            </div>
          </li>
        ))}
      </ul>

      <h3>What this site can test</h3>
      <ul className="activities">
        {activities.map((a) => (
          <li key={a.name} className={a.status.replace(' ', '-')}>
            <span>{a.name}</span>
            <span className="muted">{a.status}</span>
          </li>
        ))}
      </ul>

      {Object.keys(values).length > 0 && (
        <>
          <h3>Measured values</h3>
          <table className="values">
            <thead>
              <tr>
                <th>Variable</th>
                <th>Earth cell</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(values).map(([k, v]) => (
                <tr key={k}>
                  <td>{k.replace(/_/g, ' ')}</td>
                  <td>
                    {v.value} {v.units}
                  </td>
                  <td className="muted">{v.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h3>Reference target</h3>
      <p>
        {target.name} ({target.lat}°, {target.lon}°) — {target.description}
      </p>
      <p className="muted small">
        Coordinates {String(target.coordinate_status || '').toLowerCase()}; reference values compiled from the literature.
      </p>

      <h3>What Earth cannot reproduce</h3>
      <ul className="plain">
        {cannotReproduce.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>

      <section className="ai-block" aria-label="AI interpretation">
        <p className="eyebrow">AI interpretation</p>
        {interp === undefined && <p className="muted">Loading…</p>}
        {interp === null && <p className="muted">Not available for this candidate. Measured data and scores above are complete without it.</p>}
        {interp && (
          <>
            <p>{interp.analog_summary}</p>
            <p>{interp.non_analog_summary}</p>
            {interp.testable_activities?.length > 0 && (
              <ul className="plain">
                {interp.testable_activities.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            )}
            <p className="muted small">{interp.confidence_note}</p>
            <p className="muted small">
              {interp.ai_disclosure} Model: {interp.model}.
            </p>
          </>
        )}
      </section>
    </aside>
  );
}
