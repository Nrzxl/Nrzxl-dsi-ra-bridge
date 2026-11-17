"use strict";
const assert=require("node:assert/strict"),P=require("../protocol/bridge.cjs"),L=require("../protocol/live.cjs"),
 {Core,feedEngine,parse}=require("../protocol/receiver-core.cjs");
let checks=0;
function eq(a,b,n){assert.deepEqual(a,b,n);checks++;}
function ok(a,n){assert.ok(a,n);checks++;}
let t=0,send=[],events=[],failSend=false;
const peer={address:"127.0.0.1",port:30001},session=31;
const core=new Core({now:()=>t,send:(b,p,cb)=>{send.push(Buffer.from(b));cb(failSend?{code:"ENOBUFS"}:null);},
 event:r=>events.push(r),nonce:()=>17});
const ctl=(kind,nonce=0xD531010A,ses=session)=>L.control(kind,{source:2,mode:1,session:ses,nonce});
const pkt=(seq,ses=session,counter=seq)=>Buffer.from(P.encode({source:2,mode:1,session:ses,seq,frame:seq,counter}));
core.receive(ctl("DSH3"),peer);
let s=[...core.sessions.values()][0];eq(core.summary(s).configuredHz,10);
for(let i=0;i<600;i++){t+=100;ok(core.receive(pkt(i),peer));}
eq(core.summary(s).received,600);eq(core.totals.bytes,600*64+20);
for(let i=600;i<1800;i++){t+=100;ok(core.receive(pkt(i),peer));}
eq(core.summary(s).received,1800);eq(s.fingerprints.size,1025);ok(s.sequence.seen.size<=1025);
core.receive(pkt(1799),peer);eq(s.sequence.duplicate,1);
eq(core.totals.reasons.DUPLICATE_SNAPSHOT,1);
core.receive(pkt(1799,session,999),peer);eq(core.totals.reasons.CONFLICTING_SNAPSHOT,1);
core.receive(pkt(1801),peer);core.receive(pkt(1800),peer);
eq(s.sequence.report().lateRecovered,1);eq(s.sequence.report().missingInferred,0);eq(s.sequence.reordered,1);
// Control duplicate must not become malformed. A concrete 030 misclassification.
core.tick();let ping=L.parseControl(send.at(-1));t+=4;
core.receive(ctl("DSO3",ping.nonce),peer);core.receive(ctl("DSO3",ping.nonce),peer);
eq(core.totals.malformed,0);eq(s.pongRepeat,1);eq(core.summary(s).rttMs,4);
core.receive(ctl("DSA3",1),peer);eq(core.totals.reasons.UNEXPECTED_CONTROL_STATE,1);
core.receive(ctl("DSO3",987654),peer);eq(core.totals.reasons.UNEXPECTED_CONTROL_STATE,2);
core.receive(ctl("DSH3"),peer);eq(s.helloRepeat,1);
// Timed-out ping survives a later challenge; late known response is classified.
t+=2001;core.tick();ping=L.parseControl(send.at(-1));t+=3100;
core.receive(ctl("DSO3",ping.nonce),peer);eq(core.totals.reasons.LATE_PACKET,1);
t+=4000;core.receive(pkt(1802),peer);eq(core.totals.reasons.LATE_PACKET,2);
core.receive(ctl("DSH3"),peer);eq(s.reconnects,1);
ok(core.receive(pkt(1802),peer)); // new hello permits continuation; no reset of sequence.
core.receive(pkt(0),peer);eq(s.sequence.reordered,2);eq(s.sequence.received,1802);
core.receive(ctl("DSH3",0xD531010A,32),peer);
ok(core.receive(pkt(0,32),peer));eq(core.sessions.size,2);
let w=new L.Sequence();w.push(0xFFFFFFFE);w.push(0xFFFFFFFF);w.push(0);w.push(1);
eq(w.report().missingInferred,0);eq(w.received,4);eq(w.push(0),false);
const bad=pkt(1803);bad[48]^=1;core.receive(bad,peer);eq(core.totals.crcErrors,1);
for(const len of [0,1,19,21,63,65])core.receive(Buffer.alloc(len),peer);
eq(core.totals.reasons.INVALID_LENGTH,6);
const unknown=Buffer.from(ctl("DSH3"));unknown.write("NOPE",0);unknown.writeUInt32LE(P.crc32(unknown.subarray(0,16)),16);
core.receive(unknown,peer);eq(core.totals.reasons.UNKNOWN_CONTROL,1);
const badHeader=pkt(2);badHeader[4]=9;core.receive(badHeader,peer);eq(core.totals.reasons.INVALID_HEADER,1);
const unreg=ctl("DSO3",1,999);core.receive(unreg,peer);eq(core.totals.unregistered,1);
failSend=true;t+=400;core.receive(ctl("DSH3",0xD531010A,32),peer);
eq(core.totals.sendErrors,1);failSend=false;t+=400;core.receive(ctl("DSH3",0xD531010A,32),peer);
ok(send.length>2); // temporary failure doesn't shut down transport.
const stream={destroyed:false,writable:true,writableLength:4095,write(){throw Error("must not enqueue");}};
eq(feedEngine(stream,"123\n"),false);
let line=null;eq(feedEngine({...stream,writableLength:0,write:x=>line=x},"31 0 120\n"),true);eq(line,"31 0 120\n");
for(let i=0;i<300;i++)core.receive(Buffer.alloc(1),peer);
eq(core.recent.length,64);ok(core.totals.reasons.INVALID_LENGTH===306);
ok(JSON.stringify({sessions:[...core.sessions.values()].map(x=>core.summary(x)),totals:core.totals,recent:core.recent}).includes("DUPLICATE_SNAPSHOT"));
const legacy=ctl("DSH3",0x1A030003,77);core.receive(legacy,peer);
eq(core.summary([...core.sessions.values()].find(x=>x.session===77)).configuredHz,null);
eq(parse(legacy).control.nonce,0x1A030003);
// Global session and per-session traffic bounds remain visible.
for(let id=100;id<112;id++)core.receive(ctl("DSH3",1,id),peer);
eq(core.sessions.size,8);ok(core.totals.capacityDropped>0);
for(let i=0;i<140;i++)core.receive(pkt(i,32),peer);
ok(core.totals.rateDropped>0);
console.log(JSON.stringify({status:"PASS",checks,snapshots:1800,scope:"production Core deterministic clock; not hardware",
 duplicateAudit:true,controlRepeat:true,timeoutReconnect:true,wrap:true,bounds:true,udpFailure:true,engineBackpressure:true}));
