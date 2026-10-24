import { access, mkdir, rename, readFile } from 'node:fs/promises';
const root=new URL('../',import.meta.url),date=new Date().toISOString().replace(/[:.]/g,'-');
try {await access(new URL('.data',root));}catch {console.log('No demo state exists. Run npm start.');process.exit(0);}
try {
  const pid=Number(await readFile(new URL('.data/server.pid',root),'utf8'));
  if(Number.isSafeInteger(pid)&&pid>0){try{process.kill(pid,0);console.error('Stop the AFTERLIGHT server before resetting.');process.exit(1);}catch(e){if(e.code!=='ESRCH')throw e;}}
}catch(e){if(e.code!=='ENOENT')throw e;}
// Preserve previous evidence and chain state instead of deleting it.
await mkdir(new URL('.sessions',root),{recursive:true});
await rename(new URL('.data',root),new URL(`.sessions/${date}`,root));
console.log('Previous local session archived. Run npm start for a fresh demo. Stop the server before resetting.');
