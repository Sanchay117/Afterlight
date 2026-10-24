import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { model, source, scenarios, analyze, buildEvidence, evidenceRoot, verifyEvidence } from '../lib/engine.mjs';
import { train, sha } from '../lib/model.mjs';
const clean=scenarios.find(s=>s.id==='clean');
test('source snapshot and learned model reproduce exactly, with untouched chronological test months',async()=>{
  const bytes=await readFile(new URL('../data/pvgis-izmir-2023.json',import.meta.url),'utf8');
  assert.equal(sha(bytes),model.dataHash);
  assert.deepEqual(train(source.outputs.hourly,sha(bytes)),model);
  assert.equal(model.metrics.test.count,2208);
  assert.equal(model.metrics.daylightTest.count,902);
  assert.ok(model.metrics.daylightTest.maeKW<0.4);
  assert.ok(model.metrics.daylightTest.coverage>0.9);
});
test('clean reference-derived claim passes all 24 intervals',()=>{
  const r=analyze(clean.claim);assert.equal(r.status,'PASS');assert.equal(r.flaggedHours,0);assert.equal(r.totalKWh,481.064);
});
test('phantom night rejects exactly four forged hours and questions all 72 kWh',()=>{
  const r=analyze(scenarios.find(s=>s.id==='night').claim);
  assert.equal(r.status,'REJECT');assert.equal(r.flaggedHours,4);assert.equal(r.unsupportedKWh,72);
  assert.deepEqual(r.hours.filter(h=>h.status==='REJECT').map(h=>h.hour),[19,20,21,22]);
});
test('peak attack below capacity triggers learned-envelope review',()=>{
  const s=scenarios.find(s=>s.id==='peak'),r=analyze(s.claim);
  assert.ok(Math.max(...s.claim)<100000);assert.equal(r.status,'REVIEW');assert.equal(r.flaggedHours,6);
});
test('clock displacement preserves daily sum but fails hourly screening',()=>{
  const r=analyze(scenarios.find(s=>s.id==='shift').claim);
  assert.equal(r.totalKWh,analyze(clean.claim).totalKWh);assert.equal(r.status,'REJECT');assert.ok(r.flaggedHours>=10);
});
test('missing, negative, fractional, string and non-finite readings fail closed',()=>{
  for(const value of [null,[],Array(24).fill(-1),Array(24).fill(1.5),Array(24).fill('10'),Array(24).fill(Infinity)]) assert.throws(()=>analyze(value));
});
test('Merkle receipt is stable across labels and commits all metadata and readings',()=>{
  const a=analyze(clean.claim,'a'),b=analyze(clean.claim,'b');assert.equal(a.root,b.root);assert.ok(verifyEvidence(a.evidence,a.root));
  for(const mutate of [e=>e.readings[20].claimWh++,e=>e.readings.reverse(),e=>e.asset='OTHER',e=>e.day='2023-10-16',e=>e.modelHash='edited',e=>e.datasetHash='edited',e=>e.policy.capacityWh++]) {
    const edited=structuredClone(a.evidence);mutate(edited);assert.equal(verifyEvidence(edited,a.root),false);
  }
  assert.equal(verifyEvidence({},a.root),false);
  assert.equal(evidenceRoot(buildEvidence(clean.claim)),a.root);
});
