import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
const base=process.env.AFTERLIGHT_URL??'http://127.0.0.1:4173';
const c=await fetch(base+'/api/context').then(r=>r.json());
const post=async(path,data,token=c.csrf)=>{
  const r=await fetch(base+'/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Afterlight-Token':token},body:JSON.stringify(data)});
  return {status:r.status,body:await r.json()};
};
const checks=[];
for(const [scenario,status] of [['clean','PASS'],['night','REJECT'],['peak','REVIEW'],['shift','REJECT']]) {
  const r=await post('analyze',{scenario});assert.equal(r.status,200);assert.equal(r.body.status,status);checks.push({scenario,status,flaggedHours:r.body.flaggedHours});
}
assert.equal((await post('analyze',{scenario:'clean'},'incorrect')).status,403);
assert.equal((await post('analyze',{claim:[1,2,3]})).status,400);
const clean=(await post('analyze',{scenario:'clean'})).body;
const rejected=(await post('analyze',{scenario:'night'})).body;
assert.equal((await post('issue',{reportId:rejected.id})).status,422);
let issued=c.certificates.find(x=>x.root===clean.root);
let receipt=issued?{hash:issued.transactionHash,block:issued.block,gasUsed:issued.gasUsed,certificateId:issued.id}:undefined;
if(!issued){const r=await post('issue',{reportId:clean.id});assert.equal(r.status,200);receipt=r.body.receipt;issued=r.body.certificates[0];}
assert.equal((await post('issue',{reportId:clean.id})).status,409);
const duplicate=await post('duplicate',{reportId:clean.id});assert.equal(duplicate.body.blocked,true);
assert.equal(duplicate.body.changedEvidenceRoot,true);
assert.equal((await post('verify',{evidence:clean.evidence,root:clean.root})).body.valid,true);
const edited=structuredClone(clean.evidence);edited.readings[20].claimWh+=1000;
assert.equal((await post('verify',{evidence:edited,root:clean.root})).body.valid,false);
if(!issued.retired){const r=await post('retire',{id:issued.id,beneficiary:'IEEE ClimateChain automated demo'});assert.equal(r.status,200);assert.equal(r.body.certificates[0].retired,true);}
assert.equal((await post('retire',{id:issued.id,beneficiary:'second retirement'})).status,400);
const evidence=await fetch(base+'/api/evidence?id='+clean.id).then(r=>r.json());assert.equal(evidence.root,clean.root);
await writeFile(new URL('../artifacts/clean-evidence.json',import.meta.url),JSON.stringify({...evidence,provenance:c.data,model:c.model,contract:c.ledger},null,2)+'\n');
const result={verifiedAt:new Date().toISOString(),checks,security:'CSRF and malformed claim checks passed',contract:c.ledger.address,chainId:31337,evidenceRoot:clean.root,receipt:receipt??evidence.receipt,duplicate:duplicate.body,retirement:'verified',tamper:'original verifies; modified reading fails'};
await writeFile(new URL('../artifacts/verification.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
