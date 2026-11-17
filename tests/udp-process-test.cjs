"use strict";
const assert=require("node:assert/strict"),{spawn}=require("node:child_process"),
 net=require("node:net"),dgram=require("node:dgram"),fs=require("node:fs"),os=require("node:os"),path=require("node:path");
const L=require("../protocol/live.cjs"),P=require("../protocol/bridge.cjs");
async function freeTCP(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on("error",reject);
 s.listen(0,"127.0.0.1",()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
async function freeUDP(){return new Promise((resolve,reject)=>{const s=dgram.createSocket("udp4");s.on("error",reject);
 s.bind(0,"127.0.0.1",()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
function finish(p){return new Promise((resolve,reject)=>{p.on("error",reject);p.on("exit",c=>c===0?resolve():reject(Error("child exit "+c)));});}
async function main(){
 const udpPort=await freeUDP(),webPort=await freeTCP(),dir=fs.mkdtempSync(path.join(os.tmpdir(),"dsirb030-"));
 const engine=process.argv[2],args=["windows/receiver/server.cjs","--port",String(udpPort),"--web",String(webPort),"--logDir",dir];
 if(engine)args.push("--engine",path.resolve(engine));
 const server=spawn(process.execPath,args,{stdio:["ignore","pipe","pipe"],windowsHide:true});
 let stderr="";server.stderr.on("data",b=>{stderr+=b;});
 const end=Date.now()+20000;
 let capSocket=null;
 try {
  await new Promise((resolve,reject)=>{
   let output="";const t=setTimeout(()=>reject(Error("receiver startup timeout "+stderr)),5000);
   server.on("error",reject);server.stdout.on("data",b=>{output+=b;if(output.includes("RECEIVER http")){clearTimeout(t);resolve();}});
  });
  const sender=spawn(process.execPath,["windows/receiver/simulate.cjs","--port",String(udpPort),"--frames","120","--inject","true"],
   {stdio:["ignore","pipe","pipe"],windowsHide:true});
  let senderError="";sender.stderr.on("data",b=>{senderError+=b;});
  const timeout=setTimeout(()=>sender.kill(),10000);
  try{await finish(sender);}catch(e){throw Error(e.message+" "+senderError);}finally{clearTimeout(timeout);}
  const base="http://127.0.0.1:"+webPort;
  let state=await(await fetch(base+"/state")).json();
  let sim=state.sessions.find(s=>s.source===2);
  assert.ok(sim,"simulator handshake");
  assert.equal(sim.received,120);assert.equal(sim.provenance,"SIMULATED");
  assert.equal(sim.duplicate,1);assert.equal(sim.missingInferred,0);
  assert.equal(state.totals.crcErrors,1);assert.equal(state.totals.malformed,1);
  assert.ok(sim.rttMs!==null&&sim.rttMs>=0,"measured RTT");
  assert.equal(sim.officialEligible,false);
  const html=await(await fetch(base)).text();
  assert.ok(html.includes("DSi RA Bridge Receiver"));
  const token=html.match(/const csrf="([a-f0-9]+)"/)[1];
  assert.equal((await fetch(base+"/confirm",{method:"POST",body:"{}"})).status,403);
  assert.equal((await fetch(base+"/confirm",{method:"POST",headers:{"X-DSRB-Token":token},
    body:JSON.stringify({id:sim.id,note:"synthetic negative test"})})).status,400);
  // Forged source=1 is deliberately NOT treated as evidence of physical hardware.
  const fake=dgram.createSocket("udp4");
  await new Promise((resolve,reject)=>{
   fake.on("error",reject);fake.on("message",b=>{try{
    if(L.parseControl(b).kind==="DSA3"){
     fake.send(P.encode({source:1,mode:1,session:9009,seq:0}),udpPort,"127.0.0.1",()=>resolve());
    }}catch(_){}});
   fake.send(L.control("DSH3",{source:1,mode:1,session:9009,nonce:7}),udpPort,"127.0.0.1");
  });
  fake.close();
  for(let i=0;i<20;i++){
   state=await(await fetch(base+"/state")).json();
   if(state.sessions.some(s=>s.source===1&&s.received===1))break;
   await new Promise(r=>setTimeout(r,25));
  }
  assert.equal(state.sessions.find(s=>s.source===1).provenance,"RUNTIME_UNVERIFIED");
  if(engine){
   for(let i=0;i<20&&state.engine.events.length<2;i++){
    await new Promise(r=>setTimeout(r,50));state=await(await fetch(base+"/state")).json();
   }
   assert.deepEqual(state.engine.events.map(e=>e.id),[1,2]);
   assert.ok(state.engine.events.every(e=>e.submitted===false));
  }
  while(Date.now()<end){
   state=await(await fetch(base+"/state")).json();
   if(state.sessions.every(s=>s.connection==="DISCONNECTED"))break;
   await new Promise(r=>setTimeout(r,300));
  }
  assert.ok(state.sessions.every(s=>s.connection==="DISCONNECTED"),"disconnect timeout");
  const again=spawn(process.execPath,["windows/receiver/simulate.cjs","--port",String(udpPort),"--session","3004","--frames","10"],
   {stdio:["ignore","pipe","pipe"],windowsHide:true});
  await finish(again);
  state=await(await fetch(base+"/state")).json();
  const reconnect=state.sessions.find(s=>s.session===3004);
  assert.ok(reconnect&&reconnect.received===10,"new-session reconnect");
  assert.equal(reconnect.duplicate,0);assert.equal(reconnect.missingInferred,0);
  assert.equal(reconnect.provenance,"SIMULATED");
  capSocket=dgram.createSocket("udp4");
  for(let id=10000;id<10012;id++){
   await new Promise((resolve,reject)=>capSocket.send(L.control("DSH3",{source:2,mode:1,session:id,nonce:1}),udpPort,"127.0.0.1",e=>e?reject(e):resolve()));
  }
  for(let i=0;i<20;i++){
   state=await(await fetch(base+"/state")).json();
   if(state.totals.capacityDropped>0)break;
   await new Promise(r=>setTimeout(r,25));
  }
  assert.ok(state.sessions.length<=8&&state.totals.capacityDropped>0,"bounded session capacity");
  console.log(JSON.stringify({status:"PASS",scope:"real UDP between separate Node processes",
   packets:130,crcRejected:1,duplicate:1,malformedRejected:1,manualSpoofRejected:true,reconnect:true,sessionCapacity:true,
   rcheevos:engine?"PASS: real compiled local engine":"NOT_RUN: executable not provided",evidenceDirectory:dir}));
 }finally{
  if(capSocket)capSocket.close();
  server.kill();await new Promise(r=>setTimeout(r,200));
 }
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
