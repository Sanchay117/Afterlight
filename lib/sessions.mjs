import { randomBytes } from 'node:crypto';
import { createLedger } from './ledger.mjs';

export const SESSION_COOKIE='afterlight_session';
export class DemoSessions {
  constructor({maxSessions=6,idleMs=20*60_000,secure=true,now=Date.now}={}){
    this.sessions=new Map();this.pending=0;this.max=maxSessions;this.idleMs=idleMs;this.secure=secure;this.now=now;this.closed=false;
    this.timer=setInterval(()=>this.sweep().catch(()=>{}),30_000);this.timer.unref();
  }
  cookie(req){
    const part=(req.headers.cookie??'').split(';').map(s=>s.trim()).find(s=>s.startsWith(SESSION_COOKIE+'='));
    const value=part?.slice(SESSION_COOKIE.length+1);
    return /^[a-f0-9]{64}$/.test(value??'')?value:null;
  }
  touch(session,res){
    session.lastSeen=this.now();
    res.setHeader('Set-Cookie',`${SESSION_COOKIE}=${session.id}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${Math.ceil(this.idleMs/1000)}${this.secure?'; Secure':''}`);
  }
  async sweep(){
    const expired=[];
    for(const [id,s] of this.sessions)if(!s.busy&&this.now()-s.lastSeen>=this.idleMs){this.sessions.delete(id);expired.push(s.ledger.close());}
    await Promise.all(expired);
  }
  async get(req,res,create=false){
    if(this.closed)throw Object.assign(new Error('The demo is restarting. Reload shortly.'),{status:503});
    await this.sweep();
    let session=this.sessions.get(this.cookie(req));
    if(!session&&create){
      if(this.sessions.size+this.pending>=this.max)throw Object.assign(new Error('All demo slots are busy. Please try again shortly.'),{status:503});
      this.pending++;
      try{
        const ledger=await createLedger();
        if(this.closed){await ledger.close();throw Object.assign(new Error('The demo is restarting.'),{status:503});}
        session={id:randomBytes(32).toString('hex'),csrf:randomBytes(24).toString('hex'),reports:{},busy:false,lastSeen:this.now(),ledger};
        this.sessions.set(session.id,session);
      }finally{this.pending--;}
    }
    if(!session)throw Object.assign(new Error('Demo session expired. Reload the page for a fresh sandbox.'),{status:401});
    this.touch(session,res);return session;
  }
  async close(){
    this.closed=true;clearInterval(this.timer);
    await Promise.all([...this.sessions.values()].map(s=>s.ledger.close()));this.sessions.clear();
  }
}
