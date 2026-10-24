import ganache from 'ganache';
import solc from 'solc';
import { BrowserProvider, Contract, ContractFactory, id } from 'ethers';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { asset } from './engine.mjs';

export async function createLedger(directory) {
  if(directory) await mkdir(directory,{recursive:true});
  const rpc=ganache.provider({logging:{quiet:true},wallet:{deterministic:true,totalAccounts:3},chain:{chainId:31337,hardfork:'shanghai'},...(directory?{database:{dbPath:path.join(directory,'chain')}}:{})});
  const provider=new BrowserProvider(rpc);
  provider.pollingInterval=30;
  const verifier=await provider.getSigner(0),operator=await provider.getSigner(1);
  const input={language:'Solidity',sources:{'Afterlight.sol':{content:await readFile(new URL('../contracts/Afterlight.sol',import.meta.url),'utf8')}},settings:{optimizer:{enabled:true,runs:200},evmVersion:'shanghai',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
  const output=JSON.parse(solc.compile(JSON.stringify(input)));
  const errors=(output.errors??[]).filter(e=>e.severity==='error');
  if(errors.length) throw new Error(errors.map(e=>e.formattedMessage).join('\n'));
  const artifact=output.contracts['Afterlight.sol'].Afterlight;
  let address;
  if(directory) try {address=JSON.parse(await readFile(path.join(directory,'deployment.json'),'utf8')).address;} catch(e) {if(e.code!=='ENOENT') throw e;}
  let contract;
  if(address && await provider.getCode(address)!=='0x') contract=new Contract(address,artifact.abi,verifier);
  else {
    contract=await new ContractFactory(artifact.abi,artifact.evm.bytecode.object,verifier).deploy();
    await contract.waitForDeployment();
    address=await contract.getAddress();
    await (await contract.registerAsset(id(asset.id),await operator.getAddress(),100000)).wait();
    if(directory) await writeFile(path.join(directory,'deployment.json'),JSON.stringify({address,chainId:31337}));
  }
  const day=BigInt(Date.parse(asset.day+'T00:00:00Z')/1000);
  const describe=async()=>({chainId:31337,network:'Local EVM · Ganache',address,verifier:await verifier.getAddress(),operator:await operator.getAddress(),block:await rpc.request({method:'eth_blockNumber',params:[]}).then(x=>parseInt(x,16)),compiler:solc.version(),persistent:!!directory});
  const history=async()=>{
    const count=Number(await contract.count()),out=[];
    // Read a concrete tip directly: ethers may cache "latest" before a just-mined transaction.
    const tip=parseInt(await rpc.request({method:'eth_blockNumber',params:[]}),16);
    const events=await contract.queryFilter(contract.filters.Issued(),0,tip);
    for(let i=count;i>=Math.max(1,count-19);i--) {
      const c=await contract.certificates(i);
      const event=events.find(e=>Number(e.args[0])===i);
      const receipt=event?await provider.getTransactionReceipt(event.transactionHash):null;
      out.push({id:i,asset:c.asset,day:Number(c.day),kWh:Number(c.wattHours)/1000,root:c.evidenceRoot,owner:c.owner,retired:c.retired,beneficiary:c.beneficiary,transactionHash:event?.transactionHash,block:event?.blockNumber,gasUsed:receipt?.gasUsed.toString()});
    }
    return out;
  };
  return {contract,provider,verifier,operator,rpc,describe,history,
    async issue(report) {
      if(report.status!=='PASS') throw new Error('Screening must pass before issuance. Review or reject claims cannot be issued.');
      const tx=await contract.issue(id(asset.id),day,report.evidence.readings.map(r=>r.claimWh),report.root,{gasLimit:2000000});
      const receipt=await tx.wait();
      return {hash:receipt.hash,block:receipt.blockNumber,gasUsed:receipt.gasUsed.toString(),certificateId:Number(await contract.count())};
    },
    async duplicate(report) {
      const attemptedRoot=id('AFTERLIGHT replay challenge:'+report.root);
      try {await contract.issue.staticCall(id(asset.id),day,report.evidence.readings.map(r=>r.claimWh),attemptedRoot);return {blocked:false,reason:'Intervals have not been consumed yet. Issue the clean claim first.'};}
      catch(e) {const decoded=e.revert?.name; if(decoded==='DuplicateInterval') return {blocked:true,reason:'DuplicateInterval',hour:Number(e.revert.args[0]),contract:address,attemptedRoot,changedEvidenceRoot:true}; throw e;}
    },
    async retire(certificateId,beneficiary) {
      const tx=await contract.connect(operator).retire(certificateId,id(beneficiary),{gasLimit:150000});
      const receipt=await tx.wait();
      return {hash:receipt.hash,block:receipt.blockNumber,gasUsed:receipt.gasUsed.toString()};
    },
    async close(){await rpc.disconnect();}
  };
}
