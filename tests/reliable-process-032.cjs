"use strict";
const A=require("node:assert/strict"),{spawn}=require("node:child_process"),net=require("node:net"),
 dgram=require("node:dgram"),fs=require("node:fs"),path=require("node:path"),os=require("node:os");
async function free(udp){return new Promise((resolve,reject)=>{
 const s=udp?dgram.createSocket("udp4"):net.createServer();s.on("error",reject);
 const cb=()=>{const p=s.address().port;s.close(()=>resolve(p));};
 udp?s.bind(0,"127.0.0.1",cb):s.listen(0,"127.0.0.1",cb);
});}
function launch(args){const p=spawn(process.execPath,args,{stdio:["ignore","pipe","pipe"],windowsHide:true});
 p.output="";p.errors="";p.stdout.on("data",b=>p.output+=b);p.stderr.on("data",b=>p.errors+=b);return p;}
function done(p,ms){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{p.kill();reject(Error("timeout "+p.errors));},ms);
 p.on("error",reject);p.on("exit",c=>{clearTimeout(timer);c===0?resolve():reject(Error("exit "+c+" "+p.errors));});});}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
 const engine=process.argv[2],sender=process.argv[3];A.ok(engine&&sender);
 const udp=await free(true),web=await free(false),dir=fs.mkdtempSync(path.join(os.tmpdir(),"dsirb032-"));
 const receiver=launch(["windows/receiver-032/server.cjs","--engine",path.resolve(engine),"--port",String(udp),"--web",String(web),"--logDir",dir]);
 let stopped=false;
 try{
  const base="http://127.0.0.1:"+web;let state;
  for(let i=0;i<100;i++){try{state=await(await fetch(base+"/state")).json();if(state.reliable.engineAvailable)break;}catch(_){}await wait(50);}
  A.ok(state?.reliable.engineAvailable,"reliable engine startup "+receiver.errors);
  const results=[];
  for(const count of [600,1200,6000]){
   const out=path.join(dir,String(count));
   const pilot=launch(["windows/receiver-032/simulate.cjs","--sender",path.resolve(sender),"--port",String(udp),
    "--frames",String(count),"--faults","true","--out",out]);
   await done(pilot,125000);const result=JSON.parse(pilot.output.trim());results.push(result);
   state=await(await fetch(base+"/export")).json();
   const session=state.reliable.sessions.find(x=>x.sid===result.sid);A.ok(session);
   A.equal(session.received,count);A.equal(session.evaluated,count);A.equal(session.delivered,count);
   A.equal(session.connection,"COMPLETE");A.ok(session.recovered>=2);A.equal(session.missingInferred,0);
   A.ok(session.duplicate>0);A.equal(session.conflicting,0);A.ok(result.actualC.retryAttempts>=2);
   A.equal(result.actualC.originalAttempts,count);A.equal(result.actualC.acked,count);
   A.equal(result.actualC.pending,0);A.ok(result.actualC.ackDuplicate>=1);A.ok(result.actualC.ackLate>=1);A.ok(result.actualC.queuePeak<=32);A.ok(session.queuePeak<=32);
   A.equal(session.provenance,"SIMULATED");A.equal(session.officialEligible,false);
   const events=state.reliable.events.filter(x=>x.sid===result.sid);
   A.deepEqual(events.map(x=>x.id),[1,2]);A.ok(events.every(x=>x.submitted===false));
   fs.writeFileSync(path.join(out,"receiver.json"),JSON.stringify(state,null,2));
  }
  // A real legacy 031 producer also works against the 032 socket and original Core.
  const legacy=launch(["windows/receiver/simulate.cjs","--port",String(udp),"--frames","20"]);
  await done(legacy,15000);state=await(await fetch(base+"/state")).json();
  A.equal(state.sessions.find(x=>x.source===2).received,20);
  const page=await(await fetch(base)).text(),token=page.match(/const csrf="([a-f0-9]+)"/)[1];
  const exit=done(receiver,8000);
  await fetch(base+"/stop",{method:"POST",headers:{"X-DSRB-Token":token}});await exit;stopped=true;
  const log=fs.readFileSync(state.logPath,"utf8").trim().split("\n").map(JSON.parse);
  for(const row of results){
   const evaluated=log.filter(x=>x.type==="reliable_evaluated"&&x.sid===row.sid);
   A.equal(evaluated.length,row.snapshots);A.equal(new Set(evaluated.map(x=>x.seq)).size,row.snapshots);
   const out=path.join(dir,String(row.snapshots));fs.copyFileSync(state.logPath,path.join(out,"receiver.jsonl"));
   const checked=await new Promise((resolve,reject)=>{
    const a=launch(["scripts/compare-captures-032.cjs",path.join(out,"capture.drb"),path.join(out,"sender.json"),path.join(out,"receiver.json"),path.join(out,"receiver.jsonl")]);
    done(a,10000).then(()=>resolve(JSON.parse(a.output)),reject);
   });A.equal(checked.status,"PASS");A.equal(checked.delivery,"COMPLETE");A.deepEqual(checked.missing,[]);
  }
  fs.mkdirSync("out/logs",{recursive:true});
  fs.copyFileSync(state.logPath,"out/logs/reliable-process.jsonl");
  fs.writeFileSync("out/logs/reliable-process-result.json",JSON.stringify({status:"PASS",results,state},null,2));
  console.log(JSON.stringify({status:"PASS",scope:"actual UDP / native production C sender / compiled rcheevos",
   sessions:[600,1200,6000],faultLoss:[66,555],orderedExactlyOnce:true,legacy031:true,evidence:dir,physical032:"NOT_RUN"}));
 }finally{if(!stopped)receiver.kill();}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
