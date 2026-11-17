#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),
 http=require("node:http"),dgram=require("node:dgram"),crypto=require("node:crypto"),
 {performance}=require("node:perf_hooks"),{spawn}=require("node:child_process");
const P=require("../../protocol/bridge.cjs"),L=require("../../protocol/live.cjs");
const opt={bind:"127.0.0.1",port:18216,web:18217,logDir:"logs-030",engine:null};
for(let i=2;i<process.argv.length;i+=2){
 const k=process.argv[i].slice(2);if(!(k in opt)||!process.argv[i+1])throw Error("Unknown/missing argument");
 opt[k]=process.argv[i+1];
}
opt.port=Number(opt.port);opt.web=Number(opt.web);
for(const n of [opt.port,opt.web])if(!Number.isInteger(n)||n<1024||n>65535)throw Error("port");
if(opt.bind!=="127.0.0.1"&&opt.bind!=="0.0.0.0"&&!L.privateIP(opt.bind))throw Error("Only loopback/private LAN binds");
fs.mkdirSync(opt.logDir,{recursive:true});
const logPath=path.join(opt.logDir,"session-"+Date.now()+"-"+crypto.randomBytes(4).toString("hex")+".jsonl");
const log=fs.createWriteStream(logPath,{flags:"wx"});
let logBlocked=false,logDropped=0;log.on("drain",()=>{logBlocked=false;});
log.on("error",e=>{console.error("LOG ERROR",e.message);shutdown();});
function event(row){if(logBlocked){logDropped++;return;}logBlocked=!log.write(JSON.stringify({time:new Date().toISOString(),...row})+"\n");}
const sessions=new Map(),totals={crcErrors:0,malformed:0,unregistered:0,capacityDropped:0,rateDropped:0};
const udp=dgram.createSocket("udp4"),csrf=crypto.randomBytes(24).toString("hex");
const interfaces=Object.values(os.networkInterfaces()).flat().filter(x=>x&&x.family==="IPv4"&&!x.internal)
 .map(x=>x.address).filter(L.privateIP);
let child=null,activeEngineSession=null,engineText="",engineAvailable=false,engineDropped=0,stopping=false;
const localEvents=[];
if(opt.engine){
 const exe=path.resolve(opt.engine);if(!fs.existsSync(exe))throw Error("Engine executable missing");
 child=spawn(exe,[],{stdio:["pipe","pipe","pipe"],windowsHide:true});
 child.on("error",e=>{event({type:"engine_error",error:e.message});engineAvailable=false;});
 child.on("exit",()=>{engineAvailable=false;});
 child.stdin.on("error",()=>{engineAvailable=false;});
 child.stdout.on("data",chunk=>{
  engineText+=chunk.toString("utf8");
  if(engineText.length>16384){engineText="";return;}
  let at;while((at=engineText.indexOf("\n"))>=0){
   const line=engineText.slice(0,at);engineText=engineText.slice(at+1);
   try {const row=JSON.parse(line);row.type="rcheevos_local";row.submitted=false;
    localEvents.push(row);if(localEvents.length>20)localEvents.shift();event(row);}
   catch(_){event({type:"engine_message",message:line.slice(0,200)});}
  }
 });
 child.stderr.on("data",b=>event({type:"engine_stderr",message:b.toString().slice(0,200)}));
 child.on("spawn",()=>{engineAvailable=true;event({type:"engine_ready",path:exe});});
}
function key(peer,s){return [peer.address,peer.port,s.source,s.mode,s.session].join(":");}
function summary(s){
 const age=performance.now()-s.last;
 return {id:s.id,peer:s.peer.address+":"+s.peer.port,session:s.session,source:s.source,mode:s.mode,
  provenance:s.source===2?"SIMULATED":s.manual?"PHYSICAL_CONFIRMED_MANUALLY":"RUNTIME_UNVERIFIED",
  manualNote:s.manual??null,connection:age>3500?"DISCONNECTED":"ACTIVE",ageMs:Math.round(age),
  ...s.sequence.report(),frame:s.lastSample?.frame??null,values:s.lastSample?.words??null,
  readTicks:s.lastSample?.readTicks??null,producerDropped:s.lastSample?.producerDropped??0,
  hz:s.sequence.received>1?(s.sequence.received-1)*1000/Math.max(1,s.lastData-s.firstData):null,
  rttMs:s.rtt.length?s.rtt[s.rtt.length-1]:null,oneWayLatencyMs:null,officialEligible:false};
}
function state(){return {version:"0.3.0",listen:opt.bind+":"+opt.port,windowsIPs:interfaces,
 sessions:[...sessions.values()].map(summary),totals,logDropped,logPath,
 engine:{available:engineAvailable,activeSession:activeEngineSession,dropped:engineDropped,
  scope:"CONDIÇÕES LOCAIS CONTROLADAS; NÃO ENVIADAS AO RETROACHIEVEMENTS",events:localEvents}};}
function send(kind,s,nonce){udp.send(L.control(kind,{...s,nonce}),s.peer.port,s.peer.address);}
udp.on("message",(bytes,peer)=>{
 const now=performance.now();
 try {
  if(bytes.length===20){
   const c=L.parseControl(bytes),id=key(peer,c);let s=sessions.get(id);
   if(c.kind==="DSH3"){
    if(!s){
     if(sessions.size>=8){
      const expired=[...sessions.values()].find(x=>now-x.last>10000);
      if(expired)sessions.delete(expired.id);else{totals.capacityDropped++;return;}
     }
     s={...c,id,peer:{address:peer.address,port:peer.port},sequence:new L.Sequence(),
      last:now,lastData:now,firstData:now,rtt:[],pending:null,manual:null,lastSample:null,
      rateAt:now,rateCount:0,helloAt:-1000};sessions.set(id,s);
     event({type:"hello",id,source:c.source,provenance:c.source===2?"SIMULATED":"RUNTIME_UNVERIFIED"});
    }
    if(now-s.helloAt>=300){send("DSA3",s,c.nonce);s.helloAt=now;}
    s.last=now;return;
   }
   if(c.kind==="DSO3"&&s&&s.pending&&s.pending.nonce===c.nonce){
    const rtt=now-s.pending.at;
    if(rtt<3000){s.rtt.push(rtt);if(s.rtt.length>30)s.rtt.shift();}
    s.pending=null;s.last=now;return;
   }
   totals.malformed++;return;
  }
  const sample=P.decode(bytes),id=key(peer,sample),s=sessions.get(id);
  if(!s){totals.unregistered++;return;}
  if(now-s.rateAt>=1000){s.rateAt=now;s.rateCount=0;}
  if(++s.rateCount>120){totals.rateDropped++;return;}
  const accepted=s.sequence.push(sample.seq);s.last=now;
  if(!accepted)return;
  if(s.sequence.received===1)s.firstData=now;
  s.lastData=now;s.lastSample=sample;
  event({type:"snapshot",id,provenance:s.source===2?"SIMULATED":"RUNTIME_UNVERIFIED",
   session:sample.session,seq:sample.seq,frame:sample.frame,words:sample.words,readTicks:sample.readTicks});
  if(child&&engineAvailable){
   if(activeEngineSession===null)activeEngineSession=id;
   if(activeEngineSession===id){
    if(child.stdin.writableLength>4096)engineDropped++;
    else child.stdin.write(sample.session+" "+sample.seq+" "+sample.words[1]+"\n");
   }
  }
 }catch(e){if(String(e.message).toLowerCase().includes("crc"))totals.crcErrors++;else totals.malformed++;}
});
const timer=setInterval(()=>{
 const now=performance.now();
 for(const s of sessions.values()){
  if(now-s.last>3500)continue;
  if(s.pending&&now-s.pending.at<2000)continue;
  const nonce=crypto.randomBytes(4).readUInt32LE();s.pending={nonce,at:now};send("DSP3",s,nonce);
 }
},1000);
udp.on("error",e=>{console.error(e.message);shutdown();process.exitCode=1;});
const server=http.createServer((req,res)=>{
 const u=new URL(req.url,"http://127.0.0.1");
 res.setHeader("Cache-Control","no-store");res.setHeader("X-Content-Type-Options","nosniff");
 if(req.method==="GET"&&u.pathname==="/"){
  res.setHeader("Content-Type","text/html; charset=utf-8");
  res.end(fs.readFileSync(path.join(__dirname,"ui.html"),"utf8").replace("__CSRF__",csrf));return;
 }
 if(req.method==="GET"&&u.pathname==="/state"){
  res.setHeader("Content-Type","application/json");res.end(JSON.stringify(state()));return;
 }
 if(req.method==="GET"&&u.pathname==="/config"){
  const ip=u.searchParams.get("ip")??interfaces[0];
  if(!ip||!L.privateIP(ip)){res.writeHead(400);res.end("Choose a private IPv4 address");return;}
  res.setHeader("Content-Type","text/plain");res.setHeader("Content-Disposition",'attachment; filename="receiver.cfg"');
  res.end(ip+" "+opt.port+" 10\n");return;
 }
 if(req.method==="GET"&&u.pathname==="/export"){
  res.setHeader("Content-Type","application/json");
  res.setHeader("Content-Disposition",'attachment; filename="DSi_RA_Bridge_030_Result.json"');
  res.end(JSON.stringify(state(),null,2));return;
 }
 if(req.method==="POST"&&u.pathname==="/confirm"){
  if(req.headers["x-dsrb-token"]!==csrf){res.writeHead(403);res.end();return;}
  let body="";req.on("data",b=>{body+=b;if(body.length>1024)req.destroy();});
  req.on("end",()=>{try{
   const row=JSON.parse(body),s=sessions.get(row.id);
   if(!s||s.source!==1||typeof row.note!=="string"||row.note.trim().length<5||row.note.length>160)throw Error("manual evidence note required");
   s.manual=row.note.trim();event({type:"physical_confirmation_manual",id:s.id,note:s.manual,
    warning:"user declaration, not hardware authentication"});res.end("OK");
  }catch(e){res.writeHead(400);res.end(e.message);}});return;
 }
 res.writeHead(404);res.end();
});
server.on("error",e=>{console.error(e.message);shutdown();process.exitCode=1;});
function shutdown(){
 if(stopping)return;stopping=true;clearInterval(timer);
 try{udp.close();}catch(_){}try{server.close();}catch(_){}
 if(child)child.stdin.end();log.end();
 setTimeout(()=>{if(child)child.kill();},500).unref();
}
process.on("SIGINT",shutdown);process.on("SIGTERM",shutdown);
udp.bind(opt.port,opt.bind,()=>{event({type:"start",bind:opt.bind,port:opt.port});console.log("UDP "+opt.bind+":"+opt.port);});
server.listen(opt.web,"127.0.0.1",()=>console.log("RECEIVER http://127.0.0.1:"+opt.web));
