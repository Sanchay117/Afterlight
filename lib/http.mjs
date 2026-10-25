import http from 'node:http';
import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { randomBytes } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { publicContext, analyze, scenarios, verifyEvidence } from './engine.mjs';
import { createLedger } from './ledger.mjs';
import { DemoSessions } from './sessions.mjs';

const projectRoot=fileURLToPath(new URL('../',import.meta.url));
const files={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/favicon.svg':'favicon.svg','/brand/logo.svg':'brand/logo.svg','/brand/icon.svg':'brand/icon.svg','/fonts/bricolage.ttf':'fonts/BricolageGrotesque.ttf'};
const send=(res,status,value)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
const loopback=host=>['localhost','127.0.0.1','[::1]'].includes(host?.replace(/:\d+$/,'').toLowerCase());
function error(message,status=400){return Object.assign(new Error(message),{status});}
async function body(req){
  if(!req.headers['content-type']?.startsWith('application/json'))throw error('JSON body required',415);
  let text='';for await(const chunk of req){text+=chunk;if(text.length>40000)throw error('Request too large',413);}
  try{return JSON.parse(text||'{}');}catch{throw error('Invalid JSON');}
}
export async function createService({mode='local',publicOrigin,dataDirectory,maxSessions=6,idleMs=20*60_000,now}={}){
  if(!['local','hosted-demo'].includes(mode))throw error('AFTERLIGHT_MODE must be local or hosted-demo');
  const hosted=mode==='hosted-demo';let origin;
  if(hosted){
    if(!publicOrigin)throw error('Hosted mode requires AFTERLIGHT_PUBLIC_ORIGIN or RENDER_EXTERNAL_URL');
    const parsed=new URL(publicOrigin);
    if(!['http:','https:'].includes(parsed.protocol)||parsed.username||parsed.password||parsed.pathname!=='/'||parsed.search||parsed.hash)throw error('Public origin must be a plain HTTP(S) origin');
    if(parsed.protocol!=='https:'&&!loopback(parsed.host))throw error('Public deployments require HTTPS');
    origin=parsed;
    if(!Number.isInteger(maxSessions)||maxSessions<1||maxSessions>24||!Number.isFinite(idleMs)||idleMs<1000)throw error('Invalid hosted session limits');
  }
  const directory=path.resolve(projectRoot,dataDirectory??'.data');
  let local;
  if(!hosted){
    await mkdir(directory,{recursive:true});let reports={};
    try{reports=JSON.parse(await readFile(path.join(directory,'reports.json'),'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
    local={id:'local',ledger:await createLedger(directory),csrf:randomBytes(24).toString('hex'),reports,busy:false};
  }
  const pool=hosted?new DemoSessions({maxSessions,idleMs,secure:origin.protocol==='https:',now}):null;
  const persist=async session=>{
    if(hosted)return;
    await writeFile(path.join(directory,'reports.tmp'),JSON.stringify(session.reports));await rename(path.join(directory,'reports.tmp'),path.join(directory,'reports.json'));
  };
  const describe=async session=>({...await session.ledger.describe(),...(hosted?{network:'Isolated session EVM · Ganache'}:{})});
  const server=http.createServer(async(req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");
    try{
      const url=new URL(req.url,'http://localhost');
      if(req.method==='GET'&&url.pathname==='/healthz')return send(res,200,{ok:true,mode});
      const isApi=url.pathname.startsWith('/api/');
      if(isApi){
        const host=req.headers.host?.toLowerCase();
        if(hosted?host!==origin.host:!loopback(host))return send(res,403,{error:'Unexpected host'});
        if(req.headers.origin&&req.headers.origin!==(hosted?origin.origin:`http://${req.headers.host}`))return send(res,403,{error:'Unexpected origin'});
      }
      if(req.method==='GET'&&url.pathname==='/api/context'){
        const s=hosted?await pool.get(req,res,true):local;
        return send(res,200,{...publicContext(),csrf:s.csrf,ledger:await describe(s),certificates:await s.ledger.history(),deployment:{mode,sessionIdleMinutes:hosted?idleMs/60000:null,persistence:hosted?'Per-browser sandbox; expires on inactivity or server restart':'Local persistent chain'}});
      }
      if(req.method==='GET'&&url.pathname==='/api/evidence'){
        const s=hosted?await pool.get(req,res):local,report=s.reports[url.searchParams.get('id')];
        return report?send(res,200,report):send(res,404,{error:'Evidence not found'});
      }
      if(req.method==='POST'&&isApi){
        const s=hosted?await pool.get(req,res):local;
        if(req.headers['x-afterlight-token']!==s.csrf)return send(res,403,{error:'Session token does not match. Reload the application.'});
        const b=await body(req);
        if(!b||typeof b!=='object'||Array.isArray(b))return send(res,400,{error:'JSON object required'});
        if(s.busy)return send(res,409,{error:'Another ledger action is in progress'});
        s.busy=true;
        try{
          if(url.pathname==='/api/analyze'){
            const scenario=scenarios.find(x=>x.id===b.scenario),report=analyze(b.claim??scenario?.claim,b.label??scenario?.name??'Custom claim');
            if(s.reports[report.id]?.receipt)report.receipt=s.reports[report.id].receipt;
            s.reports[report.id]=report;
            if(hosted)while(Object.keys(s.reports).length>64)delete s.reports[Object.keys(s.reports)[0]];
            await persist(s);return send(res,200,report);
          }
          if(url.pathname==='/api/verify')return send(res,200,{valid:verifyEvidence(b.evidence,b.root)});
          const report=s.reports[b.reportId];
          if(url.pathname==='/api/issue'){
            if(!report||!verifyEvidence(report.evidence,report.root))return send(res,400,{error:'Valid stored evidence required'});
            const recomputed=analyze(report.evidence.readings.map(r=>r.claimWh));
            if(recomputed.root!==report.root||recomputed.status!=='PASS')return send(res,422,{error:'Claim has not passed screening'});
            if((await s.ledger.history()).some(c=>c.root===report.root))return send(res,409,{error:'DuplicateInterval: this asset/day is already certified'});
            const receipt=await s.ledger.issue(recomputed);report.receipt=receipt;await persist(s);
            return send(res,200,{receipt,certificates:await s.ledger.history(),ledger:await describe(s)});
          }
          if(url.pathname==='/api/duplicate'){
            if(!report)return send(res,400,{error:'Analyze a claim first'});
            return send(res,200,await s.ledger.duplicate(report));
          }
          if(url.pathname==='/api/retire'){
            if(!Number.isSafeInteger(b.id)||b.id<1||typeof b.beneficiary!=='string'||b.beneficiary.trim().length<2||b.beneficiary.length>100)return send(res,400,{error:'Certificate ID and beneficiary (2–100 characters) required'});
            const receipt=await s.ledger.retire(b.id,b.beneficiary.trim());return send(res,200,{receipt,certificates:await s.ledger.history(),ledger:await describe(s)});
          }
          return send(res,404,{error:'Unknown operation'});
        }finally{s.busy=false;}
      }
      if(req.method==='GET'&&files[url.pathname]){
        const name=files[url.pathname],ext=path.extname(name),type={'.html':'text/html','.css':'text/css','.svg':'image/svg+xml','.ttf':'font/ttf','.js':'text/javascript'}[ext];
        const bytes=await readFile(path.join(projectRoot,'public',name));res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-cache'});return res.end(bytes);
      }
      return send(res,404,{error:'Not found'});
    }catch(e){
      if(res.headersSent){res.destroy();return;}
      send(res,e.status??400,{error:e.revert?.name??(e.receipt?'EVM transaction reverted':e.shortMessage??e.message)});
    }
  });
  const close=async()=>{
    if(server.listening){const done=new Promise(resolve=>server.close(resolve));server.closeIdleConnections();await done;}
    if(pool)await pool.close();else await local.ledger.close();
  };
  return {server,close,pool,mode,directory,defaultHost:hosted?'0.0.0.0':'127.0.0.1'};
}
