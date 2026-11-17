#!/usr/bin/env node
"use strict";
// SIMULATED agent; actual production C selective sender drives all data/retries.
const {spawn}=require("node:child_process"),dgram=require("node:dgram"),crypto=require("node:crypto"),
 fs=require("node:fs"),path=require("node:path"),{performance}=require("node:perf_hooks"),
 P=require("../../protocol/bridge.cjs"),R=require("../../protocol/reliable.cjs");
const o={sender:null,port:18216,host:"127.0.0.1",frames:600,start:0,faults:"false",out:null};
for(let i=2;i<process.argv.length;i+=2){const k=process.argv[i].slice(2);if(!(k in o))throw Error("option");o[k]=process.argv[i+1];}
if(!o.sender)throw Error("--sender compiled C helper required");
const total=Number(o.frames),start=Number(o.start)>>>0,port=Number(o.port);
if(total<1||total>6000||!Number.isInteger(total))throw Error("frames");
if(o.host!=="127.0.0.1")throw Error("test pilot only supports loopback");
const lo=crypto.randomBytes(4).readUInt32LE()||1,hi=crypto.randomBytes(4).readUInt32LE()||1;
const sid=hi.toString(16).padStart(8,"0")+lo.toString(16).padStart(8,"0");
const socket=dgram.createSocket("udp4"),child=spawn(path.resolve(o.sender),[String(lo),String(hi),String(start)],
 {stdio:["pipe","pipe","pipe"],windowsHide:true});
let text="",errors="",ready=false,finished=false,offering=false,next=0,budget=0;
let stats=null,lastHello=-1000,lastStatus=-1000,finAt=-1000,ackCount=0,dataTx=0,dropped=0;
const captures=[],attempts=[],dropOnce=new Set(),began=performance.now(),now=()=>Math.floor(performance.now()-began);
const fault=o.faults==="true",end=(start+total)>>>0;
const packet=(kind,seq=0,a=0,b=0,payload=null)=>R.encode({kind,source:2,mode:1,lo,hi,seq,a,b,payload});
function netSend(b){socket.send(b,port,o.host,e=>{if(e)fail(e);});}
function command(s){if(child.stdin.writableLength>4096){fail(Error("pilot IPC backpressure"));return;}child.stdin.write(s+"\n");}
function offer(){
 if(!ready||offering||next>=total||budget<=0||finished)return;
 const p=Buffer.from(P.encode({source:2,mode:1,session:lo,seq:(start+next)>>>0,frame:next*6,counter:next}));
 offering=true;captures[next]=p;command("O "+now()+" "+p.toString("hex"));
}
function status(st){
 const values=[st.queued,st.queued,st.originalAttempts,st.originalAccepted,st.sendFailed,st.retryAttempts,
 st.retryAccepted,st.acked,st.pending,st.queuePeak,st.backpressure,0,ackCount,0,st.rtoMs,st.captureToAckMaxMs];
 const b=Buffer.alloc(64);values.forEach((x,i)=>b.writeUInt32LE(x>>>0,i*4));
 netSend(packet(R.K.STATUS,st.next,next>=total?2:1,total,b));
}
function fail(e){if(finished)return;console.error(e.stack??e);finish(1);}
function finish(code){
 if(finished)return;finished=true;clearInterval(timer);clearTimeout(deadline);
 try{socket.close();}catch(_){}child.stdin.end();
 setTimeout(()=>child.kill(),300).unref();process.exitCode=code;
}
socket.on("message",bytes=>{
 let p;try{p=R.decode(bytes);}catch(e){fail(e);return;}
 if(p.sid!==sid)return;
 if(p.kind===R.K.ACK){
  ready=true;ackCount++;
  const sendAck=()=>{if(!finished)command("A "+p.seq+" "+p.a+" "+p.b+" "+now());};
  if(fault&&ackCount===8)setTimeout(sendAck,200);else sendAck();
  if(fault&&ackCount===12)sendAck(); // intentionally duplicated ACK
 }else if(p.kind===R.K.PING)netSend(packet(R.K.PONG,p.seq));
 else if(p.kind===R.K.FINACK){
  if(!stats||stats.acked!==total||stats.pending!==0||p.seq!==end){fail(Error("premature FINACK"));return;}
  if(o.out){
   fs.mkdirSync(o.out,{recursive:true});fs.writeFileSync(path.join(o.out,"capture.drb"),Buffer.concat(captures.slice(0,total)));
   fs.writeFileSync(path.join(o.out,"sender.json"),JSON.stringify({version:"0.3.2",sid,session:lo,sessionHi:hi,
    captured:total,simulated:true,txAttempts:attempts.join(""),...stats},null,2));
  }
  console.log(JSON.stringify({status:"PASS",provenance:"SIMULATED",sid,snapshots:total,
   actualC:stats,datagramsSent:dataTx,injectedDrops:dropped,faults:fault}));finish(0);
 }
});
child.stdout.on("data",chunk=>{
 text+=chunk.toString();let at;
 while((at=text.indexOf("\n"))>=0){
  const line=text.slice(0,at).trim();text=text.slice(at+1);
  if(line.startsWith("Q ")){offering=false;if(line==="Q 1"){next++;budget--;}else budget=0;offer();}
  else if(line.startsWith("D ")){
   const b=Buffer.from(line.slice(2),"hex"),p=R.decode(b),offset=R.dist(p.seq,start);dataTx++;attempts[offset]=Math.max(attempts[offset]??0,p.a);
   if(fault&&[66,555].includes(offset)&&!dropOnce.has(offset)){
    dropOnce.add(offset);dropped++;continue;
   }
   if(fault&&offset===20&&p.a===1){setTimeout(()=>{if(!finished)netSend(b);},80);continue;}
   netSend(b);
   if(fault&&offset%97===9)netSend(b); // duplicate originals and retransmissions stay explicit
  }else if(line.startsWith("S ")){
   stats=JSON.parse(line.slice(2));
   if(stats.failed){fail(Error("C sender retry budget exhausted"));return;}
   if(now()-lastStatus>500){status(stats);lastStatus=now();}
   if(next===total&&stats.acked===total&&stats.pending===0&&now()-finAt>200){
    status(stats);netSend(packet(R.K.FIN,end));finAt=now();
   }
  }else if(line==="ERROR")fail(Error("native pilot command rejected"));
 }
});
child.stderr.on("data",b=>errors+=b);
child.on("error",fail);child.on("exit",code=>{if(!finished)fail(Error("C sender exited "+code+" "+errors));});
const timer=setInterval(()=>{
 if(finished)return;const t=now();
 if(t-lastHello>500){netSend(packet(R.K.HELLO,start,10,total));lastHello=t;}
 if(ready){budget=8;offer();command("T "+t);command("S");}
},10);
const deadline=setTimeout(()=>fail(Error("reliable pilot deadline; "+JSON.stringify(stats))),120000);
socket.on("error",fail);socket.bind(0,"127.0.0.1");
