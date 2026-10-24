import { writeFile } from 'node:fs/promises';
const url='https://re.jrc.ec.europa.eu/api/v5_3/seriescalc?lat=38.4237&lon=27.1428&startyear=2023&endyear=2023&pvcalculation=1&peakpower=100&loss=14&angle=30&aspect=0&outputformat=json';
const res = await fetch(url,{signal:AbortSignal.timeout(60000)});
if(!res.ok) throw new Error(`PVGIS ${res.status}`);
const bytes=await res.text(), data=JSON.parse(bytes);
if(data.outputs?.hourly?.length!==8760) throw new Error('Unexpected hourly dataset; retaining existing snapshot');
await writeFile(new URL('../data/pvgis-izmir-2023.json',import.meta.url),bytes);
console.log('Updated public PVGIS reference. Run npm run train and npm test before use.');
