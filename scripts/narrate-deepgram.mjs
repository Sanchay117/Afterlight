import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const envIndex=process.argv.indexOf('--env-file');
let key=process.env.DEEPGRAM_API_KEY??process.env.DEEPGRAM_KEY??process.env.DEEPGRAM_API;
if(!key&&envIndex>=0){
  const content=await readFile(process.argv[envIndex+1],'utf8');
  for(const line of content.split(/\r?\n/)){
    const match=line.match(/^\s*(?:export\s+)?(?:DEEPGRAM_API_KEY|DEEPGRAM_KEY|DEEPGRAM_API)\s*=\s*(.*?)\s*$/);
    if(match){key=match[1].replace(/^(['"])(.*)\1$/,'$2');break;}
  }
}
if(!key)throw new Error('Set DEEPGRAM_API_KEY or pass --env-file with a local credential file.');
const scenes=JSON.parse(await readFile(path.join(root,'docs/demo-scenes.json'),'utf8'));
const out=path.join(root,'artifacts/narration');await mkdir(out,{recursive:true});
const model=process.env.DEEPGRAM_VOICE??'aura-2-thalia-en';
const speed=1.04;
const manifest={provider:'Deepgram',model,encoding:'linear16',container:'wav',sampleRate:48000,speed,scenes:[]};
// Sequential synthesis avoids exceeding project concurrency limits. Only demo text leaves the device.
for(const [index,scene] of scenes.entries()){
  const digest=createHash('sha256').update(JSON.stringify({text:scene.narration,model,speed})).digest('hex');
  const filename=`scene-${String(index).padStart(2,'0')}.wav`,dest=path.join(out,filename);
  let previous;
  try{previous=JSON.parse(await readFile(dest+'.json','utf8'));}catch{}
  if(previous?.digest!==digest){
    const params=new URLSearchParams({model,encoding:'linear16',container:'wav',sample_rate:'48000',speed:String(speed)});
    let bytes;
    for(let attempt=0;attempt<3;attempt++){
      try{
        const response=await fetch('https://api.deepgram.com/v1/speak?'+params,{method:'POST',headers:{Authorization:'Token '+key,'Content-Type':'application/json'},body:JSON.stringify({text:scene.narration}),signal:AbortSignal.timeout(45000)});
        if(!response.ok){const error=new Error(`Deepgram rejected scene ${index+1} (HTTP ${response.status}).`);error.permanent=response.status<500&&response.status!==429;throw error;}
        bytes=Buffer.from(await response.arrayBuffer());break;
      }catch(error){if(error.permanent||attempt===2)throw new Error(`Scene ${index+1} synthesis failed after ${attempt+1} attempt(s). ${error.permanent?error.message:'Connection failure; rerun to resume cached clips.'}`);console.log(`Retrying scene ${index+1} after a connection interruption`);await new Promise(r=>setTimeout(r,1000*(attempt+1)));}
    }
    if(bytes.length<1000||bytes.toString('ascii',0,4)!=='RIFF')throw new Error(`Unexpected audio response for scene ${index+1}`);
    await writeFile(dest,bytes);await writeFile(dest+'.json',JSON.stringify({digest,provider:'Deepgram',model,speed}));
  }
  const audioBytes=await readFile(dest);
  manifest.scenes.push({scene:index+1,file:filename,digest,audioSha256:createHash('sha256').update(audioBytes).digest('hex'),bytes:audioBytes.length});
  console.log(`Deepgram narration ${index+1}/${scenes.length} ready`);
}
await writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
// This public provenance record contains no environment path or credential.
await writeFile(path.join(root,'artifacts/narration-provenance.json'),JSON.stringify(manifest,null,2)+'\n');
