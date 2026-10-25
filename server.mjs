import { writeFile, unlink } from 'node:fs/promises';
import path from 'node:path';
import { createService } from './lib/http.mjs';

const service=await createService({
  mode:process.env.AFTERLIGHT_MODE??'local',
  publicOrigin:process.env.AFTERLIGHT_PUBLIC_ORIGIN??process.env.RENDER_EXTERNAL_URL,
  dataDirectory:process.env.AFTERLIGHT_DATA_DIR,
  maxSessions:Number(process.env.AFTERLIGHT_MAX_SESSIONS??6),
  idleMs:Number(process.env.AFTERLIGHT_SESSION_TTL_MINUTES??20)*60_000
});
const port=Number(process.env.PORT??4173);
if(!Number.isInteger(port)||port<0||port>65535)throw new Error('Invalid PORT');
service.server.listen(port,service.defaultHost,async()=>{
  if(service.mode==='local')await writeFile(path.join(service.directory,'server.pid'),String(process.pid));
  console.log(`AFTERLIGHT ready at http://${service.defaultHost}:${service.server.address().port} (${service.mode})`);
});
let closing=false;
async function close(){if(closing)return;closing=true;await service.close();if(service.mode==='local')await unlink(path.join(service.directory,'server.pid')).catch(()=>{});process.exit(0);}
process.on('SIGINT',close);process.on('SIGTERM',close);
