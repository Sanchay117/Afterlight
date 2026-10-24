import { access, mkdir, rename } from 'node:fs/promises';
const root=new URL('../',import.meta.url),date=new Date().toISOString().replace(/[:.]/g,'-');
try {await access(new URL('.data',root));}catch {console.log('No demo state exists. Run npm start.');process.exit(0);}
// Preserve previous evidence and chain state instead of deleting it.
await mkdir(new URL('.sessions',root),{recursive:true});
await rename(new URL('.data',root),new URL(`.sessions/${date}`,root));
console.log('Previous local session archived. Run npm start for a fresh demo. Stop the server before resetting.');
