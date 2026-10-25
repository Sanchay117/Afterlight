import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import path from 'node:path';
import { tmpdir } from 'node:os';
import http from 'node:http';
import { createService } from '../lib/http.mjs';

async function start(options){const app=await createService(options);app.server.listen(0,'127.0.0.1');await once(app.server,'listening');return {...app,url:`http://127.0.0.1:${app.server.address().port}`};}
async function request(app,route,{method='GET',body,cookie,token,host,origin}={}){
  const headers={...(host?{Host:host}:{}),...(origin?{Origin:origin}:{}),...(cookie?{Cookie:cookie}:{}),...(token?{'X-Afterlight-Token':token}:{}),...(body!==undefined?{'Content-Type':'application/json'}:{})};
  return new Promise((resolve,reject)=>{
    const req=http.request(app.url+route,{method,headers},res=>{
      let text='';res.setEncoding('utf8');res.on('data',chunk=>text+=chunk);
      res.on('end',()=>{try{resolve({status:res.statusCode,body:JSON.parse(text),setCookie:res.headers['set-cookie']?.[0]});}catch(e){reject(e);}});
    });
    req.on('error',reject);req.end(body===undefined?undefined:JSON.stringify(body));
  });
}
test('hosted demo isolates two visitors, protects sessions and expires idle chains',async t=>{
  let clock=0;const app=await start({mode:'hosted-demo',publicOrigin:'https://demo.example',maxSessions:2,idleMs:1000,now:()=>clock});t.after(()=>app.close());
  const base={host:'demo.example',origin:'https://demo.example'};
  const call=(route,options={})=>request(app,route,{...base,...options});
  assert.equal((await request(app,'/healthz')).status,200);
  assert.equal((await call('/api/context',{host:'evil.example'})).status,403);
  assert.equal((await call('/api/context',{origin:'https://evil.example'})).status,403);
  const [a,b]=await Promise.all([call('/api/context'),call('/api/context')]);
  assert.equal(a.status,200);assert.equal(b.status,200);
  assert.match(a.setCookie,/HttpOnly/);assert.match(a.setCookie,/SameSite=Strict/);assert.match(a.setCookie,/; Secure/);
  const ac=a.setCookie.split(';')[0],bc=b.setCookie.split(';')[0];assert.notEqual(ac,bc);assert.notEqual(a.body.csrf,b.body.csrf);
  assert.equal(a.body.ledger.persistent,false);assert.equal(a.body.deployment.mode,'hosted-demo');
  assert.equal((await call('/api/context')).status,503);
  const post=(cookie,token,route,body)=>call(route,{method:'POST',cookie,token,body});
  assert.equal((await post(ac,b.body.csrf,'/api/analyze',{scenario:'clean'})).status,403);
  assert.equal((await post(undefined,a.body.csrf,'/api/analyze',{scenario:'clean'})).status,401);
  const ar=await post(ac,a.body.csrf,'/api/analyze',{scenario:'clean'});assert.equal(ar.body.status,'PASS');
  assert.equal((await call('/api/evidence?id='+ar.body.id,{cookie:bc})).status,404);
  const ai=await post(ac,a.body.csrf,'/api/issue',{reportId:ar.body.id});assert.equal(ai.status,200);assert.equal(ai.body.certificates.length,1);
  assert.equal((await call('/api/context',{cookie:bc})).body.certificates.length,0);
  const br=await post(bc,b.body.csrf,'/api/analyze',{scenario:'clean'});
  assert.equal((await post(bc,b.body.csrf,'/api/issue',{reportId:br.body.id})).status,200);
  assert.equal((await post(ac,a.body.csrf,'/api/duplicate',{reportId:ar.body.id})).body.blocked,true);
  assert.equal((await post(ac,a.body.csrf,'/api/retire',{id:1,beneficiary:'Visitor A'})).status,200);
  assert.equal((await call('/api/context',{cookie:bc})).body.certificates[0].retired,false);
  clock=2000;
  assert.equal((await post(ac,a.body.csrf,'/api/analyze',{scenario:'clean'})).status,401);
  const fresh=await call('/api/context',{cookie:ac});assert.equal(fresh.body.certificates.length,0);assert.notEqual(fresh.body.csrf,a.body.csrf);
});
test('local HTTP mode retains reports and certificates across restarts',async()=>{
  const directory=await mkdtemp(path.join(tmpdir(),'afterlight-http-'));let app;
  try{
    app=await start({dataDirectory:directory});
    const c=(await request(app,'/api/context')).body;
    const r=await request(app,'/api/analyze',{method:'POST',token:c.csrf,body:{scenario:'clean'}});assert.equal(r.status,200);
    assert.equal((await request(app,'/api/issue',{method:'POST',token:c.csrf,body:{reportId:r.body.id}})).status,200);
    await app.close();app=await start({dataDirectory:directory});
    assert.equal((await request(app,'/api/context')).body.certificates.length,1);
    assert.equal((await request(app,'/api/evidence?id='+r.body.id)).body.root,r.body.root);
    assert.equal((await request(app,'/api/context',{host:'evil.example'})).status,403);
  }finally{if(app)await app.close();await rm(directory,{recursive:true,force:true});}
});
test('hosted configuration refuses accidental insecure public origins',async()=>{
  await assert.rejects(()=>createService({mode:'hosted-demo'}),/requires/);
  await assert.rejects(()=>createService({mode:'hosted-demo',publicOrigin:'http://public.example'}),/HTTPS/);
  await assert.rejects(()=>createService({mode:'hosted-demo',publicOrigin:'https://public.example/path'}),/plain/);
});
