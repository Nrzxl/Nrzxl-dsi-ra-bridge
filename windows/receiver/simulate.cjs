#!/usr/bin/env node
"use strict";
const dgram=require("node:dgram"),P=require("../../protocol/bridge.cjs"),L=require("../../protocol/live.cjs");
const args=process.argv.slice(2),o={host:"127.0.0.1",port:18216,frames:120,session:3003,inject:"false"};
for(let i=0;i<args.length;i+=2){const k=args[i].slice(2);if(!(k in o)||!args[i+1])throw Error("option");o[k]=args[i+1];}
const port=Number(o.port),frames=Number(o.frames),session=Number(o.session)>>>0;
if(!Number.isInteger(frames)||frames<1||frames>6000)throw Error("frames");
if(o.host!=="127.0.0.1"&&!L.privateIP(o.host))throw Error("Private LAN/loopback only");
const sock=dgram.createSocket("udp4");let acknowledged=false,seq=0,timer=null;
const hello=setInterval(()=>sock.send(L.control("DSH3",{source:2,mode:1,session,nonce:73}),port,o.host),200);
const timeout=setTimeout(()=>{console.error("SIMULATED handshake timeout");finish(1);},5000);
function finish(code){clearInterval(hello);clearInterval(timer);clearTimeout(timeout);sock.close();process.exitCode=code;}
sock.on("message",b=>{
 try{
  const x=L.parseControl(b);if(x.session!==session||x.source!==2)return;
  if(x.kind==="DSP3")sock.send(L.control("DSO3",{...x}),port,o.host);
  if(x.kind==="DSA3"&&!acknowledged){
   acknowledged=true;clearInterval(hello);clearTimeout(timeout);
   timer=setInterval(()=>{
    const p=P.encode({source:2,mode:1,session,seq,frame:seq*4,counter:seq*4});
    sock.send(p,port,o.host);seq++;
    if(seq>=frames){
     clearInterval(timer);
     if(o.inject==="true"){
      sock.send(p,port,o.host); // duplicate
      const bad=p.slice();bad[48]^=1;sock.send(bad,port,o.host); // bad CRC
      sock.send(Buffer.from([1,2,3]),port,o.host); // malformed
     }
     setTimeout(()=>{console.log("SIMULATED: "+frames+" snapshots sent; hardware unverified.");finish(0);},500);
    }
   },1000/60);
  }
 }catch(_){}
});
sock.on("error",e=>{console.error(e.message);finish(1);});
sock.bind(0,"0.0.0.0");
