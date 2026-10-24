import { readFileSync } from 'node:fs';
import { predict, sha } from './model.mjs';
const bytes=readFileSync(new URL('../data/pvgis-izmir-2023.json',import.meta.url),'utf8');
export const source = JSON.parse(bytes);
export const model = JSON.parse(readFileSync(new URL('../data/model.json',import.meta.url),'utf8'));
if(sha(bytes)!==model.dataHash) throw new Error('Reference dataset does not match trained model');
export const modelHash = sha(model);
export const asset = {id:'IZMIR-DEMO-100',name:'Aegean solar cooperative',location:'İzmir, Türkiye',lat:38.4237,lon:27.1428,capacityKW:100,day:'2023-10-15',timezone:'UTC',demo:true};
export const dayRows=source.outputs.hourly.filter(r=>r.time.startsWith(asset.day.replaceAll('-','')));
export const scenarios = [
  {id:'clean',name:'Clean production',subtitle:'Reference-derived demonstration claim',claim:dayRows.map(r=>Math.round(r.P))},
  {id:'night',name:'Phantom night',subtitle:'Generation invented after sunset',claim:dayRows.map((r,i)=>Math.round(r.P)+(i>=19&&i<=22?18000:0))},
  {id:'peak',name:'Inflated peak',subtitle:'Daytime output quietly raised by 35%',claim:dayRows.map((r,i)=>Math.round(r.P*(i>=8&&i<=13?1.35:1)))},
  {id:'shift',name:'Clock shift',subtitle:'Meter timestamps displaced by 4 hours',claim:dayRows.map((_,i)=>Math.round(dayRows[(i+20)%24].P))}
];
export function validateClaim(claim) {
  if(!Array.isArray(claim)||claim.length!==24||claim.some(v=>!Number.isSafeInteger(v)||v<0||v>1_000_000)) throw new Error('Provide exactly 24 whole-number, non-negative watt-hour readings (maximum 1,000,000 each).');
}
export function merkle(leaves) {
  if(!leaves.length) throw new Error('Empty evidence');
  let level=leaves.map(sha);
  while(level.length>1) {
    const next=[];
    for(let i=0;i<level.length;i+=2) next.push(sha(level[i]+(level[i+1]??level[i])));
    level=next;
  }
  return '0x'+level[0];
}
export function buildEvidence(claim) {
  validateClaim(claim);
  return {
    schema:'afterlight-evidence-v1',asset:asset.id,day:asset.day,
    datasetHash:model.dataHash,modelHash,
    policy:{capacityWh:100000,nightToleranceWh:500,reviewMarginWh:3000,alpha:model.alpha},
    readings:dayRows.map((r,i)=>({hour:i,sourceTimestamp:r.time,claimWh:claim[i],irradiance:r['G(i)'],temperature:r.T2m,wind:r.WS10m,sunHeight:r.H_sun,reconstructed:r.Int}))
  };
}
export function evidenceRoot(e) {
  const {readings,...metadata}=e;
  return merkle([metadata,...readings]);
}
export function analyze(claim, label='Custom claim') {
  validateClaim(claim);
  if(typeof label!=='string'||label.length>120) throw new Error('Claim label must be text, up to 120 characters.');
  const hours=dayRows.map((r,i)=>{
    const expected=predict(r,model), low=r['G(i)']===0?0:Math.max(0,expected-model.radius), high=r['G(i)']===0?0:Math.min(100,expected+model.radius);
    const value=claim[i]/1000;
    let status='PASS',reason='Within screening tolerance';
    if(value>100) {status='REJECT';reason='Exceeds registered 100 kW capacity';}
    else if(r['G(i)']===0&&value>0.5) {status='REJECT';reason='Generation without solar irradiance';}
    else if(r.Int===1) {status='REVIEW';reason='Reconstructed source irradiance; independent evidence required';}
    else if(value>high+3||value<low-3) {status='REVIEW';reason=value>high?'Above weather-model envelope':'Below weather-model envelope';}
    return {hour:i,claim:value,expected,low,high,irradiance:r['G(i)'],temperature:r.T2m,status,reason,unsupported:Math.max(0,value-high),sourceTimestamp:r.time};
  });
  const status=hours.some(h=>h.status==='REJECT')?'REJECT':hours.some(h=>h.status==='REVIEW')?'REVIEW':'PASS';
  const evidence=buildEvidence(claim),root=evidenceRoot(evidence);
  return {id:root,label,status,hours,evidence,root,totalKWh:claim.reduce((s,v)=>s+v,0)/1000,expectedKWh:hours.reduce((s,h)=>s+h.expected,0),flaggedHours:hours.filter(h=>h.status!=='PASS').length,unsupportedKWh:hours.filter(h=>h.status!=='PASS').reduce((s,h)=>s+h.unsupported,0),createdAt:new Date().toISOString()};
}
export function verifyEvidence(evidence,root) {
  try {return evidenceRoot(evidence)===root;} catch {return false;}
}
export const publicContext = () => ({asset,scenarios,model:{...model,hash:modelHash},data:{source:'European Commission JRC · PVGIS 5.3',radiation:'SARAH3',meteorology:'ERA5',hours:8760,year:2023,hash:model.dataHash,units:'P(W) × 1 h / 1000 = approximate interval kWh',url:'https://re.jrc.ec.europa.eu/api/v5_3/seriescalc?lat=38.4237&lon=27.1428&startyear=2023&endyear=2023&pvcalculation=1&peakpower=100&loss=14&angle=30&aspect=0&outputformat=json'}});
