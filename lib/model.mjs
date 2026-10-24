import { createHash } from 'node:crypto';
export const sha = value => createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
export const features = r => {
  const g = r['G(i)'] / 1000, t = (r.T2m - 25) / 25, w = r.WS10m / 10;
  return [1, g, g*g, g*g*g, g*t, g*g*t, g*w, g*g*w];
};
function solve(a, b) {
  const m = a.map((row, i) => [...row, b[i]]), n = b.length;
  for (let k = 0; k < n; k++) {
    let best = k;
    for (let j = k+1; j < n; j++) if (Math.abs(m[j][k]) > Math.abs(m[best][k])) best = j;
    [m[k], m[best]] = [m[best], m[k]];
    const pivot = m[k][k];
    if (Math.abs(pivot) < 1e-12) throw new Error('Singular training system');
    for (let j = k; j <= n; j++) m[k][j] /= pivot;
    for (let i = 0; i < n; i++) if (i !== k) {
      const f = m[i][k];
      for (let j = k; j <= n; j++) m[i][j] -= f*m[k][j];
    }
  }
  return m.map(row => row[n]);
}
export function predict(r, model) {
  if (r['G(i)'] <= 0) return 0;
  return Math.max(0, Math.min(100, features(r).reduce((s, x, i) => s+x*model.weights[i], 0)));
}
export function train(raw, dataHash) {
  // Chronological split, with calibration and final test untouched by fitting.
  const daylight = raw.filter(r => r['G(i)'] > 0);
  const fit = daylight.filter(r => r.time < '20230701');
  const cal = daylight.filter(r => r.time >= '20230701' && r.time < '20231001');
  const test = raw.filter(r => r.time >= '20231001');
  const n = features(fit[0]).length;
  const a = Array.from({length:n}, () => Array(n).fill(0)), b = Array(n).fill(0);
  for (const r of fit) {
    const x = features(r), y = r.P/1000;
    for (let i=0; i<n; i++) { b[i] += x[i]*y; for (let j=0; j<n; j++) a[i][j] += x[i]*x[j]; }
  }
  for (let i=1; i<n; i++) a[i][i] += 0.001;
  const model = {version:'ridge-conformal-v1', weights:solve(a,b), dataHash, alpha:0.1};
  const residuals = cal.map(r => Math.abs(r.P/1000-predict(r,model))).sort((x,y)=>x-y);
  model.radius = residuals[Math.min(cal.length-1, Math.ceil((cal.length+1)*0.9)-1)];
  const testDay = test.filter(r=>r['G(i)']>0);
  const metrics = rows => ({
    count: rows.length,
    maeKW: rows.reduce((s,r)=>s+Math.abs(r.P/1000-predict(r,model)),0)/rows.length,
    coverage: rows.filter(r=>Math.abs(r.P/1000-predict(r,model)) <= model.radius).length/rows.length
  });
  model.metrics = {train:fit.length, calibration:cal.length, test:metrics(test), daylightTest:metrics(testDay)};
  model.note = 'Learned surrogate of PVGIS modeled output, not a model validated on real meter readings. Coverage is empirical on this site/year, not guaranteed under distribution shift.';
  return model;
}
