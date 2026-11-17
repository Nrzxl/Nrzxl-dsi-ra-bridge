#!/usr/bin/env node
/* Windows 10/11 diagnostic client. Built-in modules only. NO RA endpoints. */
"use strict";
const fs=require("node:fs"), path=require("node:path"), dgram=require("node:dgram");
const {performance}=require("node:perf_hooks");
const P=require("../../protocol/bridge.cjs");
function options(args) {
  const out={};
  for(let i=0;i<args.length;i+=2){
    if(!args[i].startsWith("--")||!args[i+1])throw Error("Expected --key value");
    out[args[i].slice(2)]=args[i+1];
  }
  return out;
}
const [mode,...rest]=process.argv.slice(2), o=options(rest);
const stats=new P.Stats();
function consume(bytes,origin,log=null) {
  try{
    const s=P.decode(bytes), r=stats.push(s,performance.now());
    const row={origin,provenance:s.provenance,officialEligible:false,
      session:s.session,seq:s.seq,frame:s.frame,words:s.words,
      readTicks:s.readTicks,producerDropped:s.producerDropped,
      accepted:r.acceptedNow,missing:r.missing,duplicate:r.duplicate,
      reordered:r.reordered,arrivalHz:r.hz??null,latencyMs:null};
    if(log!==null)fs.writeSync(log,JSON.stringify(row)+"\n");
    console.log(JSON.stringify(row));
  }catch(e){
    const row={origin,status:"REJECTED",error:String(e.message)};
    if(log!==null)fs.writeSync(log,JSON.stringify(row)+"\n");
    console.error(JSON.stringify(row));
    if(mode==="replay")process.exitCode=1;
  }
}
if(mode==="simulate"){
  const n=Number(o.frames??600);
  if(!Number.isInteger(n)||n<1||n>60000)throw Error("frames 1..60000");
  const file=o.out??"SIMULATED.drb";
  const fd=fs.openSync(file,"wx");
  try{for(let i=0;i<n;i++)fs.writeSync(fd,P.encode({source:2,session:1,seq:i,counter:i}));}
  finally{fs.closeSync(fd);}
  console.log("SIMULATED ONLY: "+file+"; no RetroAchievements requests.");
}else if(mode==="replay"){
  if(!o.file)throw Error("--file required");
  const size=fs.statSync(o.file).size;
  if(size>64*60000||size%64!==0||!size)throw Error("Invalid/truncated capture size");
  const data=fs.readFileSync(o.file), fd=o.log?fs.openSync(o.log,"wx"):null;
  try{for(let at=0;at<data.length;at+=64)consume(data.subarray(at,at+64),"OFFLINE_IMPORT",fd);}
  finally{if(fd!==null)fs.closeSync(fd);}
  console.log("Replay arrivalHz is processing rate, not hardware capture Hz. Latency unavailable.");
}else if(mode==="listen"){
  const bind=o.bind??"127.0.0.1", port=Number(o.port??18216);
  if(!Number.isInteger(port)||port<1024||port>65535)throw Error("port");
  const log=fs.openSync(o.log??("dsrb-"+Date.now()+".jsonl"),"wx");
  const socket=dgram.createSocket("udp4");
  socket.on("message",(msg,peer)=>{
    if(msg.length===5&&msg.toString("ascii")==="DSRB?"){
      socket.send(Buffer.from("DSRB! diagnostic-only/0.2.0"),peer.port,peer.address);
      return;
    }
    consume(msg,"UDP_UNAUTHENTICATED "+peer.address+":"+peer.port,log);
  });
  socket.on("error",e=>{console.error(e.message);socket.close();process.exitCode=1;});
  socket.on("close",()=>fs.closeSync(log));
  process.on("SIGINT",()=>socket.close());
  socket.bind(port,bind,()=>console.log("DIAGNOSTIC ONLY "+bind+":"+port+
    "; no hardware agent Wi-Fi implementation supplied."));
}else if(mode==="send-sim"){
  const host=o.host??"127.0.0.1", port=Number(o.port??18216);
  if(!Number.isInteger(port)||port<1024||port>65535)throw Error("port");
  const sock=dgram.createSocket("udp4");
  let seq=0;
  const t=setInterval(()=>{
    sock.send(P.encode({source:2,seq:seq,counter:seq}),port,host,e=>{
      if(e){console.error(e.message);clearInterval(t);sock.close();process.exitCode=1;}
    });
    if(++seq===120){clearInterval(t);setTimeout(()=>sock.close(),100);}
  },1000/60);
}else {
  console.log("node windows/bridge/bridge.cjs simulate --out SIMULATED.drb");
  console.log("node windows/bridge/bridge.cjs replay --file CAP000.drb --log replay.jsonl");
  console.log("node windows/bridge/bridge.cjs listen --bind 127.0.0.1 --port 18216");
  console.log("node windows/bridge/bridge.cjs send-sim --host 127.0.0.1 --port 18216");
}
