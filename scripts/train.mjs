import { readFile, writeFile } from 'node:fs/promises';
import { sha, train } from '../lib/model.mjs';
const bytes = await readFile(new URL('../data/pvgis-izmir-2023.json',import.meta.url),'utf8');
const model = train(JSON.parse(bytes).outputs.hourly,sha(bytes));
await writeFile(new URL('../data/model.json',import.meta.url),JSON.stringify(model,null,2)+'\n');
console.log(JSON.stringify({version:model.version,radiusKW:model.radius,metrics:model.metrics},null,2));
