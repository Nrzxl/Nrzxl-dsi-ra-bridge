#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),
 http=require("node:http"),dgram=require("node:dgram"),crypto=require("node:crypto"),
 {performance}=require("node:perf_hooks"),{spawn}=require("node:child_process");
const L=require("../../protocol/live.cjs"),{Core,feedEngine}=require("../../protocol/receiver-core.cjs");
const opt={bind:"127.0.0.1",port:18216,web:18217,logDir:"logs-031",engine:null};
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
let diagnosticsAt=0,diagnosticsCount=0,diagnosticsSuppressed=0;
const core=new Core({now:()=>performance.now(),send:(b,peer,cb)=>{try{udp.send(b,peer.port,peer.address,cb);}catch(e){cb(e);}},event:row=>{
 if(row.type==="packet_diagnostic"||row.type==="control_repeat"){
  const now=performance.now();if(now-diagnosticsAt>=1000){diagnosticsAt=now;diagnosticsCount=0;}
  if(++diagnosticsCount>60){diagnosticsSuppressed++;return;}
 }
 event(row);
}});
const sessions=core.sessions,totals=core.totals;
const udp=dgram.createSocket("udp4"),csrf=crypto.randomBytes(24).toString("hex");
const interfaces=Object.values(os.networkInterfaces()).flat().filter(x=>x&&x.family==="IPv4"&&!x.internal)
 .map(x=>x.address).filter(L.privateIP);
let child=null,activeEngineSession=null,engineText="",engineAvailable=false,engineDropped=0,stopping=false;
const localEvents=[];let engineProgress=null;
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
    if(row.event==="LOCAL_TEST_TRIGGER"){localEvents.push(row);if(localEvents.length>20)localEvents.shift();}
    else engineProgress=row;
    event(row);}
   catch(_){event({type:"engine_message",message:line.slice(0,200)});}
  }
 });
 child.stderr.on("data",b=>event({type:"engine_stderr",message:b.toString().slice(0,200)}));
 child.on("spawn",()=>{engineAvailable=true;event({type:"engine_ready",path:exe});});
}
function summary(s){return core.summary(s);}
function state(){return {version:"0.3.1",listen:opt.bind+":"+opt.port,windowsIPs:interfaces,
 sessions:[...sessions.values()].map(summary),totals,recentDiagnostics:core.recent,diagnosticsSuppressed,logDropped,logPath,
 engine:{available:engineAvailable,activeSession:activeEngineSession,dropped:engineDropped,
  scope:"CONDIÇÕES LOCAIS CONTROLADAS; NÃO ENVIADAS AO RETROACHIEVEMENTS",events:localEvents,progress:engineProgress}};}
udp.on("message",(bytes,peer)=>{
 const result=core.receive(bytes,peer);
 if(result&&child&&engineAvailable){
  const {sample,session:s}=result;
  if(activeEngineSession===null)activeEngineSession=s.id;
  if(activeEngineSession===s.id&&!feedEngine(child.stdin,sample.session+" "+sample.seq+" "+sample.words[1]+"\n")){
   engineDropped++;event({type:"engine_input_dropped",id:s.id,seq:sample.seq});
  }
 }
});
const timer=setInterval(()=>core.tick(),1000);
udp.on("error",e=>{
 totals.udpErrors++;event({type:"udp_socket_error",code:e.code??"UNKNOWN"});
 if(!["ECONNRESET","ECONNREFUSED","ENETUNREACH","EHOSTUNREACH","EAGAIN","ENOBUFS"].includes(e.code)){
  console.error(e.message);shutdown();process.exitCode=1;
 }
});
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
  res.setHeader("Content-Disposition",'attachment; filename="DSi_RA_Bridge_031_Result.json"');
  res.end(JSON.stringify(state(),null,2));return;
 }
 if(req.method==="POST"&&u.pathname==="/stop"){
  if(req.headers["x-dsrb-token"]!==csrf){res.writeHead(403);res.end();return;}
  res.end("Receiver encerrando; dados finais no JSONL.");setTimeout(shutdown,50);return;
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
 event({type:"shutdown",result:state()});
 try{udp.close();}catch(_){}try{server.close();}catch(_){}
 if(child)child.stdin.end();log.end();
 setTimeout(()=>{if(child)child.kill();},500).unref();
}
process.on("SIGINT",shutdown);process.on("SIGTERM",shutdown);
udp.bind(opt.port,opt.bind,()=>{event({type:"start",bind:opt.bind,port:opt.port});console.log("UDP "+opt.bind+":"+opt.port);});
server.listen(opt.web,"127.0.0.1",()=>console.log("RECEIVER http://127.0.0.1:"+opt.web));
