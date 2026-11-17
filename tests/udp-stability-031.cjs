"use strict";
const A=require("node:assert/strict"),{spawn}=require("node:child_process"),net=require("node:net"),
 dgram=require("node:dgram"),fs=require("node:fs"),os=require("node:os"),path=require("node:path"),
 P=require("../protocol/bridge.cjs"),L=require("../protocol/live.cjs");
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function free(t){return new Promise((resolve,reject)=>{
 const s=t==="udp"?dgram.createSocket("udp4"):net.createServer();
 s.on("error",reject);const ready=()=>{const p=s.address().port;s.close(()=>resolve(p));};
 if(t==="udp")s.bind(0,"127.0.0.1",ready);else s.listen(0,"127.0.0.1",ready);
});}
function child(args){const p=spawn(process.execPath,args,{stdio:["ignore","pipe","pipe"],windowsHide:true});
 p.errors="";p.stderr.on("data",b=>p.errors+=b);return p;}
async function done(p,ms=30000){return new Promise((resolve,reject)=>{
 const t=setTimeout(()=>{p.kill();reject(Error("timeout "+p.errors));},ms);
 p.on("error",reject);p.on("exit",c=>{clearTimeout(t);c===0?resolve():reject(Error("exit "+c+" "+p.errors));});
});}
async function main(){
 const udp=await free("udp"),web=await free("tcp"),base="http://127.0.0.1:"+web;
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),"dsirb031-"));
 const args=["windows/receiver/server.cjs","--port",String(udp),"--web",String(web),"--logDir",dir];
 if(process.argv[2])args.push("--engine",path.resolve(process.argv[2]));
 const receiver=child(args);let socket,finished=false;
 try{
  await new Promise((resolve,reject)=>{let o="";const tm=setTimeout(()=>reject(Error("startup "+receiver.errors)),6000);
   receiver.stdout.on("data",b=>{o+=b;if(o.includes("RECEIVER http")){clearTimeout(tm);resolve();}});
   receiver.on("error",reject);
  });
  for(const [session,frames] of [[4100,600],[4101,1200]]){
   const sim=child(["windows/receiver/simulate.cjs","--port",String(udp),"--session",String(session),"--frames",String(frames)]);
   await done(sim,30000);
   const state=await(await fetch(base+"/state")).json(),s=state.sessions.find(x=>x.session===session);
   A.equal(s.received,frames);A.equal(s.duplicate,0);A.equal(s.missingInferred,0);A.equal(s.provenance,"SIMULATED");
  }
  socket=dgram.createSocket("udp4");const session=4900;
  const ctl=(k,nonce=0xD531010A)=>L.control(k,{source:2,mode:1,session,nonce});
  const send=b=>new Promise((resolve,reject)=>socket.send(b,udp,"127.0.0.1",e=>e?reject(e):resolve()));
  const sample=n=>Buffer.from(P.encode({source:2,mode:1,session,seq:n,counter:n}));
  socket.on("message",b=>{try{const c=L.parseControl(b);
   if(c.kind==="DSP3"){socket.send(ctl("DSO3",c.nonce),udp,"127.0.0.1");setTimeout(()=>{
    if(socket)socket.send(ctl("DSO3",c.nonce),udp,"127.0.0.1");
   },5);}
  }catch(_){}});
  await send(ctl("DSH3"));await wait(50);
  await send(sample(0));await send(sample(2));await send(sample(1));await send(sample(2));
  await send(ctl("DSA3",123));await send(Buffer.from([1,2,3]));
  const corrupt=sample(3);corrupt[48]^=1;await send(corrupt);
  await wait(1300);
  let state=await(await fetch(base+"/export")).json(),s=state.sessions.find(x=>x.session===session);
  A.equal(s.received,2);A.equal(s.duplicate,1);A.equal(s.reordered,1);A.equal(s.missingInferred,0);
  A.equal(s.configuredHz,10);A.ok(s.controls.pongRepeat>=1);
  A.equal(state.totals.reasons.UNEXPECTED_CONTROL_STATE,1);
  A.equal(state.totals.reasons.INVALID_LENGTH,1);A.equal(state.totals.crcErrors,1);
  A.equal(state.totals.malformed,1); // known repeated PONG is not invalid wire.
  A.ok(state.recentDiagnostics.some(x=>x.reason==="DUPLICATE_SNAPSHOT"));
  A.ok(state.totals.acceptedBytes>=1800*64);A.equal(state.version,"0.3.1");
  if(process.argv[2]){
   A.deepEqual(state.engine.events.map(e=>e.id),[1,2]);
   A.ok(state.engine.events.every(e=>e.submitted===false));
  }
  const html=await(await fetch(base)).text(),token=html.match(/const csrf="([a-f0-9]+)"/)[1];
  const exported=path.join(dir,"DSi_RA_Bridge_031_Result.json");fs.writeFileSync(exported,JSON.stringify(state,null,2));
  const exit=done(receiver,6000);
  const response=await fetch(base+"/stop",{method:"POST",headers:{"X-DSRB-Token":token}});
  A.equal(response.status,200);await exit;finished=true;socket.close();socket=null;
  const log=fs.readFileSync(state.logPath,"utf8").trim().split("\n").map(JSON.parse);
  A.ok(log.some(r=>r.type==="shutdown"));A.ok(log.some(r=>r.reason==="DUPLICATE_SNAPSHOT"));
  fs.mkdirSync("out/logs",{recursive:true});
  fs.copyFileSync(exported,"out/logs/udp-stability-result.json");
  fs.copyFileSync(state.logPath,"out/logs/udp-stability.jsonl");
  console.log(JSON.stringify({status:"PASS",scope:"separate Node processes / actual loopback UDP; simulated agents",
   consecutive:[600,1200],duplicate:true,reorder:true,repeatedPong:true,crc:true,truncated:true,unexpectedControl:true,
   export:true,shutdownDuringSession:true,engine:process.argv[2]?"PASS":"NOT_RUN",physical031:"NOT_RUN"}));
 }finally{if(socket)socket.close();if(!finished)receiver.kill();}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
