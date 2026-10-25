import http from 'node:http';
import { readFile, writeFile, mkdir, rename, unlink } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { randomBytes } from 'node:crypto';
import { publicContext, analyze, scenarios, verifyEvidence } from './lib/engine.mjs';
import { createLedger } from './lib/ledger.mjs';

const root=path.dirname(fileURLToPath(import.meta.url)), port=Number(process.env.PORT??4173);
const directory=path.resolve(root,process.env.AFTERLIGHT_DATA_DIR??'.data');
await mkdir(directory,{recursive:true});
const ledger=await createLedger(directory),csrf=randomBytes(24).toString('hex');
let reports={};
try {reports=JSON.parse(await readFile(path.join(directory,'reports.json'),'utf8'));} catch(e){if(e.code!=='ENOENT') throw e;}
const persist=async()=>{await writeFile(path.join(directory,'reports.tmp'),JSON.stringify(reports));await rename(path.join(directory,'reports.tmp'),path.join(directory,'reports.json'));};
let mutating=false;
const files={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/favicon.svg':'favicon.svg','/brand/logo.svg':'brand/logo.svg','/brand/icon.svg':'brand/icon.svg','/fonts/bricolage.ttf':'fonts/BricolageGrotesque.ttf'};
const send=(res,status,value)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
async function body(req) {
  if(!req.headers['content-type']?.startsWith('application/json')) throw new Error('JSON body required');
  let text=''; for await(const chunk of req){text+=chunk;if(text.length>40000) throw new Error('Request too large');}
  return JSON.parse(text||'{}');
}
const server=http.createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");
  try {
    const url=new URL(req.url,'http://localhost');
    if(req.method==='GET' && url.pathname==='/api/context') return send(res,200,{...publicContext(),csrf,ledger:await ledger.describe(),certificates:await ledger.history()});
    if(req.method==='GET' && url.pathname==='/api/evidence') {
      const report=reports[url.searchParams.get('id')];if(!report)return send(res,404,{error:'Evidence not found'});
      return send(res,200,report);
    }
    if(req.method==='POST' && url.pathname.startsWith('/api/')) {
      const origin=req.headers.origin;
      const host=req.headers.host;
      if(!host||!['127.0.0.1','localhost','[::1]'].includes(host.replace(/:\d+$/,''))) return send(res,403,{error:'Loopback host required'});
      if((origin && origin!==`http://${host}`)||req.headers['x-afterlight-token']!==csrf) return send(res,403,{error:'Open AFTERLIGHT locally to perform this action'});
      const b=await body(req);
      if(mutating) return send(res,409,{error:'Another ledger action is in progress'});
      mutating=true;
      try {
        if(url.pathname==='/api/analyze') {
          const scenario=scenarios.find(s=>s.id===b.scenario);
          const report=analyze(b.claim??scenario?.claim,b.label??scenario?.name??'Custom claim');
          if(reports[report.id]?.receipt) report.receipt=reports[report.id].receipt;
          reports[report.id]=report;await persist();return send(res,200,report);
        }
        if(url.pathname==='/api/verify') return send(res,200,{valid:verifyEvidence(b.evidence,b.root)});
        const report=reports[b.reportId];
        if(url.pathname==='/api/issue') {
          if(!report || !verifyEvidence(report.evidence,report.root)) return send(res,400,{error:'Valid stored evidence required'});
          const recomputed=analyze(report.evidence.readings.map(r=>r.claimWh));
          if(recomputed.root!==report.root||recomputed.status!=='PASS') return send(res,422,{error:'Claim has not passed screening'});
          if((await ledger.history()).some(c=>c.root===report.root)) return send(res,409,{error:'DuplicateInterval: this asset/day is already certified'});
          const receipt=await ledger.issue(recomputed);report.receipt=receipt;await persist();
          return send(res,200,{receipt,certificates:await ledger.history(),ledger:await ledger.describe()});
        }
        if(url.pathname==='/api/duplicate') {
          if(!report)return send(res,400,{error:'Analyze a claim first'});
          return send(res,200,await ledger.duplicate(report));
        }
        if(url.pathname==='/api/retire') {
          if(!Number.isSafeInteger(b.id)||b.id<1||typeof b.beneficiary!=='string'||b.beneficiary.trim().length<2||b.beneficiary.length>100) return send(res,400,{error:'Certificate ID and beneficiary (2–100 characters) required'});
          const receipt=await ledger.retire(b.id,b.beneficiary.trim());return send(res,200,{receipt,certificates:await ledger.history(),ledger:await ledger.describe()});
        }
        return send(res,404,{error:'Unknown operation'});
      } finally {mutating=false;}
    }
    if(req.method==='GET' && files[url.pathname]) {
      const name=files[url.pathname];res.writeHead(200,{'Content-Type':name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.svg')?'image/svg+xml':name.endsWith('.ttf')?'font/ttf':'text/javascript','Cache-Control':'no-cache'});
      return res.end(await readFile(path.join(root,'public',name)));
    }
    return send(res,404,{error:'Not found'});
  } catch(e) {
    const message=e.revert?.name??(e.receipt?'EVM transaction reverted':e.shortMessage??e.message);
    send(res,400,{error:message});
  }
});
server.listen(port,'127.0.0.1',async()=>{await writeFile(path.join(directory,'server.pid'),String(process.pid));console.log(`AFTERLIGHT ready at http://127.0.0.1:${port}`);});
let closing=false;
async function close(){if(closing)return;closing=true;server.close();await ledger.close();await unlink(path.join(directory,'server.pid')).catch(()=>{});process.exit(0);}
process.on('SIGINT',close);process.on('SIGTERM',close);
