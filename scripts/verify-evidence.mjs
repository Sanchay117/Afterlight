import { readFile } from 'node:fs/promises';
import { verifyEvidence } from '../lib/engine.mjs';
const filename=process.argv[2];
if(!filename){console.error('Usage: npm run evidence:verify -- path/to/exported-evidence.json');process.exit(2);}
const packet=JSON.parse(await readFile(filename,'utf8'));
if(!verifyEvidence(packet.evidence,packet.root)){console.error('MISMATCH: this packet does not match its committed root.');process.exit(1);}
console.log(`MATCH: ${packet.root}\nIntegrity verified. To establish anchoring, compare this root with the certificate in contract storage. Integrity alone does not authenticate generation.`);
