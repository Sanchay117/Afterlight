import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';

const sourceUrl=new URL('../contracts/Afterlight.sol',import.meta.url);
const artifactUrl=new URL('../contracts/Afterlight.json',import.meta.url);
const digest=text=>createHash('sha256').update(text).digest('hex');
let cached;
export async function compileContract(){
  const source=await readFile(sourceUrl,'utf8');
  const {default:solc}=await import('solc');
  const input={language:'Solidity',sources:{'Afterlight.sol':{content:source}},settings:{optimizer:{enabled:true,runs:200},evmVersion:'shanghai',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
  const output=JSON.parse(solc.compile(JSON.stringify(input)));
  const errors=(output.errors??[]).filter(e=>e.severity==='error');
  if(errors.length)throw new Error(errors.map(e=>e.formattedMessage).join('\n'));
  const compiled=output.contracts['Afterlight.sol'].Afterlight;
  const artifact={sourceHash:digest(source),compiler:solc.version(),abi:compiled.abi,bytecode:compiled.evm.bytecode.object};
  await writeFile(artifactUrl,JSON.stringify(artifact,null,2)+'\n');
  cached=Promise.resolve(artifact);return artifact;
}
export function loadContractArtifact(){
  return cached??= (async()=>{
    const source=await readFile(sourceUrl,'utf8');
    let artifact;
    try{artifact=JSON.parse(await readFile(artifactUrl,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
    if(!artifact||artifact.sourceHash!==digest(source))throw new Error('Contract artifact is missing or stale. Run npm run build.');
    return artifact;
  })();
}
