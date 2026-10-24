import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { id, ZeroHash } from 'ethers';
import { createLedger } from '../lib/ledger.mjs';
import { asset, analyze, scenarios } from '../lib/engine.mjs';
const clean=analyze(scenarios.find(s=>s.id==='clean').claim);
const day=BigInt(Date.parse(asset.day+'T00:00:00Z')/1000),assetId=id(asset.id);
const wh=clean.evidence.readings.map(r=>r.claimWh);
const reverts=name=>e=>e.revert?.name===name;
test('contract enforces issuance authority, asset validity, interval uniqueness and one-way retirement',async t=>{
  const l=await createLedger();t.after(()=>l.close());
  await t.test('only verifier can register and issue',async()=>{
    await assert.rejects(()=>l.contract.connect(l.operator).registerAsset.staticCall(id('OTHER'),l.operator.address,100000),reverts('Unauthorized'));
    await assert.rejects(()=>l.contract.connect(l.operator).issue.staticCall(assetId,day,wh,clean.root),reverts('Unauthorized'));
  });
  await t.test('invalid inputs cannot issue, including missing asset and non-midnight interval',async()=>{
    for(const [a,d,values,root] of [[id('MISSING'),day,wh,clean.root],[assetId,day+1n,wh,clean.root],[assetId,day,wh,ZeroHash],[assetId,day,Array(24).fill(0),clean.root],[assetId,day,Array(24).fill(100001),clean.root]]) {
      await assert.rejects(()=>l.contract.issue.staticCall(a,d,values,root),reverts('InvalidClaim'));
    }
    assert.equal(await l.contract.count(),0n);
  });
  await t.test('rejected screening cannot enter through verifier adapter',async()=>{
    await assert.rejects(()=>l.issue(analyze(scenarios.find(s=>s.id==='night').claim)),/Screening must pass/);
  });
  await t.test('real EVM issuance stores quantity, root and consumes zero-output intervals too',async()=>{
    const receipt=await l.issue(clean);assert.ok(/^0x[0-9a-f]{64}$/.test(receipt.hash));
    assert.equal(receipt.certificateId,1);
    const cert=(await l.history())[0];assert.equal(cert.root,clean.root);assert.equal(cert.kWh,481.064);
    assert.equal(cert.transactionHash,receipt.hash);assert.equal(cert.block,receipt.block);
    assert.equal(await l.contract.consumed(await l.contract.slot(assetId,day,0)),true);
  });
  await t.test('changed evidence root does not bypass interval nullifier',async()=>{
    await assert.rejects(()=>l.contract.issue.staticCall(assetId,day,wh,id('completely different receipt')),reverts('DuplicateInterval'));
    assert.equal((await l.duplicate(clean)).blocked,true);assert.equal(await l.contract.count(),1n);
  });
  await t.test('asset identity and capacity cannot be overwritten',async()=>{
    await assert.rejects(()=>l.contract.registerAsset.staticCall(assetId,l.operator.address,999999),reverts('InvalidClaim'));
  });
  await t.test('only owner can retire and retirement is permanent',async()=>{
    await assert.rejects(()=>l.contract.retire.staticCall(1,id('beneficiary')),reverts('Unauthorized'));
    const receipt=await l.retire(1,'IEEE demo');assert.ok(receipt.block>0);
    assert.equal((await l.history())[0].retired,true);
    await assert.rejects(()=>l.contract.connect(l.operator).retire.staticCall(1,id('another beneficiary')),reverts('AlreadyRetired'));
    assert.equal(await l.contract.consumed(await l.contract.slot(assetId,day,20)),true);
  });
});
test('chain persists after closing and reopening the embedded EVM',async()=>{
  const dir=await mkdtemp(path.join(tmpdir(),'afterlight-chain-'));
  let l;
  try {
    l=await createLedger(dir);const address=(await l.describe()).address;await l.issue(clean);await l.retire(1,'Persistent demo');await l.close();
    l=await createLedger(dir);assert.equal((await l.describe()).address,address);assert.equal((await l.history())[0].retired,true);assert.equal((await l.duplicate(clean)).blocked,true);
  } finally {if(l)await l.close();await rm(dir,{recursive:true,force:true});}
});
