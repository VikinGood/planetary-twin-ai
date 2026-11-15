// Activities an analog site can help test, by mission type, and the characteristics
// each one depends on (from AGENTS.md mission presets).
// Portions generated with AI (Claude); reviewed by the team.

export const ACTIVITIES = {
  landing: [
    { name: 'Descent imaging and terrain-relative navigation', needs: ['surface_optics', 'illumination', 'topography'] },
    { name: 'Hazard detection and avoidance', needs: ['topography'] },
    { name: 'Landing pad and plume-surface interaction', needs: ['geology', 'aridity', 'topography'] },
    { name: 'First surface mobility', needs: ['topography', 'geology'] },
  ],
  base: [
    { name: 'Habitat construction and site preparation', needs: ['topography', 'geology'] },
    { name: 'ISRU water extraction from ground ice', needs: ['ice_polar'] },
    { name: 'Shelter in caves or lava tubes', needs: ['volcanic_caves'] },
    { name: 'Power systems in extreme light regimes', needs: ['illumination'] },
    { name: 'Long-duration crew operations in extreme cold and dryness', needs: ['thermal', 'aridity'] },
  ],
};

export const STRONG = 0.6;

/** Evaluate activities from the characteristic scores that are selected and available. */
export function evaluateActivities(missionType, parts) {
  const byId = Object.fromEntries(parts.filter((p) => p.score !== null).map((p) => [p.id, p.score]));
  return (ACTIVITIES[missionType] || []).map((a) => {
    const vals = a.needs.filter((n) => n in byId).map((n) => byId[n]);
    if (vals.length === 0) return { ...a, status: 'not assessed', mean: null };
    const mean = vals.reduce((x, y) => x + y, 0) / vals.length;
    return { ...a, mean, status: mean >= STRONG ? 'good analog' : 'weak analog' };
  });
}

export const FAMILIES = ['desert', 'polar', 'volcanic', 'arid', 'cave'];
