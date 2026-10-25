import { compileContract } from '../lib/contract-artifact.mjs';
const artifact=await compileContract();
console.log(`Built Afterlight with Solidity ${artifact.compiler}; source ${artifact.sourceHash.slice(0,12)}`);
