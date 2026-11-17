"use strict";
const R=require("./reliable.cjs"),crypto=require("node:crypto");
const digest=b=>crypto.createHash("sha256").update(b).digest("hex");
class ReliableCore{
 constructor({now,send,evaluate,event=()=>{}}){
  this.now=now;this.transport=send;this.evaluate=evaluate;this.event=event;this.sessions=new Map();
  this.totals={datagrams:0,bytes:0,invalid:0,sendErrors:0,rejected:0};this.active=null;
 }
 send(s,kind,seq=s.next,a=0,b=0){
  const out=R.encode({...s,kind,seq,a,b});
  try{this.transport(out,s.peer,e=>{if(e){this.totals.sendErrors++;this.event({type:"reliable_send_error",sid:s.sid,code:e.code});}});}
  catch(e){this.totals.sendErrors++;this.event({type:"reliable_send_error",sid:s.sid,code:e.code});}
 }
 ack(s){
  let mask=0;for(let i=0;i<32;i++)if(s.buffer.has((s.next+i)>>>0))mask=(mask|(1<<i))>>>0;
  this.send(s,R.K.ACK,s.next,mask,32-s.buffer.size);s.ackSent++;s.lastAck=this.now();
 }
 reject(reason,p,peer){
  this.totals.rejected++;this.event({type:"reliable_rejected",reason,sid:p?.sid,seq:p?.seq,peer:peer.address+":"+peer.port});
 }
 receive(bytes,peer){
  this.totals.datagrams++;this.totals.bytes+=bytes.length;let p;
  try{p=R.decode(bytes);}catch(e){this.totals.invalid++;this.event({type:"reliable_invalid",reason:e.message,length:bytes.length});return;}
  let s=this.sessions.get(p.sid),now=this.now();
  if(p.kind===R.K.HELLO){
   if(!s){
    if(this.active!==null){this.reject("SESSION_BUSY",p,peer);return;}
    if(p.a<1||p.a>30||p.b<1||p.b>6000){this.reject("HELLO_LIMIT",p,peer);return;}
    // Keep at most four completed/timed-out histories, never an unbounded session table.
    if(this.sessions.size>=4){const old=[...this.sessions.values()].find(x=>x.closed||now-x.last>15000);
     if(!old){this.reject("CAPACITY",p,peer);return;}this.sessions.delete(old.sid);}
    s={...p,peer:{address:peer.address,port:peer.port},next:p.seq,start:p.seq,first:now,last:now,
     buffer:new Map(),history:new Map(),holes:new Set(),high:null,inflight:null,closed:false,failed:false,
     configuredHz:p.a,target:p.b,received:0,duplicates:0,conflicting:0,recovered:0,gaps:0,
     evaluated:0,delivered:0,engineEvents:0,originalDatagrams:0,retryDatagrams:0,wire:0,bytes:0,
     ackSent:0,lastAck:now,queuePeak:0,evalMsMax:0,evalMsSum:0,status:null,finSeen:false,
     rtt:[],ping:null,manual:null,lastSample:null};
    this.sessions.set(s.sid,s);this.active=s.sid;
    this.event({type:"reliable_hello",sid:s.sid,source:s.source,mode:s.mode,start:s.start,target:s.target});
   }else if(s.closed){this.reject("SESSION_ID_REUSE",p,peer);return;}
   else if(s.start!==p.seq||s.configuredHz!==p.a||s.target!==p.b){this.reject("HELLO_CHANGED",p,peer);return;}
   if(!this.samePeer(s,p,peer)){this.reject("SESSION_PEER_MISMATCH",p,peer);return;}
   s.last=now;this.ack(s);return;
  }
  if(!s||!this.samePeer(s,p,peer)){this.reject("UNREGISTERED_SESSION",p,peer);return;}
  s.last=now;s.wire++;s.bytes+=bytes.length;
  if(p.kind===R.K.DATA){
   p.retry?s.retryDatagrams++:s.originalDatagrams++;
   const fp=digest(p.payload),d=R.dist(p.seq,s.next);
   const existing=s.buffer.get(p.seq)?.fingerprint??s.history.get(p.seq);
   if(existing){
    if(existing!==fp){s.conflicting++;s.failed=true;this.reject("CONFLICTING_SNAPSHOT",p,peer);return;}
    s.duplicates++;this.event({type:"reliable_duplicate",sid:s.sid,seq:p.seq,retry:p.retry,attempt:p.a,
     fingerprint:fp,afterCommit:d>=0x80000000});this.ack(s);return;
   }
   if(s.closed||s.failed||d>=32){this.reject(d>=0x80000000?"LATE_HISTORY_EXPIRED":"OUTSIDE_WINDOW",p,peer);this.ack(s);return;}
   if(s.buffer.size>=32){this.reject("BUFFER_FULL",p,peer);this.ack(s);return;}
   if(s.high===null){for(let j=0;j<d;j++)s.holes.add((s.next+j)>>>0);s.gaps+=d;s.high=p.seq;}
   else{
    const advance=R.dist(p.seq,s.high);
    if(advance<0x80000000&&advance>0){for(let j=1;j<advance;j++)s.holes.add((s.high+j)>>>0);s.gaps+=advance-1;s.high=p.seq;}
   }
   if(s.holes.delete(p.seq))s.recovered++;
   s.buffer.set(p.seq,{...p,fingerprint:fp,receivedAt:now});s.received++;
   s.queuePeak=Math.max(s.queuePeak,s.buffer.size);
   this.event({type:"reliable_snapshot",sid:s.sid,seq:p.seq,frame:p.sample.frame,fingerprint:fp,
    retry:p.retry,attempt:p.a,captureTickMs:p.b,words:p.sample.words});
   this.ack(s);this.pump(s);return;
  }
  if(p.kind===R.K.STATUS){
   s.status={state:p.a,target:p.b,nextProduced:p.seq,
    ...Object.fromEntries(["captured","queued","originalAttempts","originalAccepted","sendFailed","retryAttempts",
     "retryAccepted","acked","unacked","queuePeak","backpressure","exhausted","ackRx","ackDuplicate","rtoMs",
     "captureToAckMaxMs"].map((k,i)=>[k,p.payload.readUInt32LE(i*4)]))};
   this.event({type:"reliable_sender_status",sid:s.sid,status:s.status});return;
  }
  if(p.kind===R.K.FIN){
   s.finSeen=true;
   if(p.seq===s.next&&!s.buffer.size&&s.inflight===null&&!s.failed){
    s.closed=true;if(this.active===s.sid)this.active=null;this.send(s,R.K.FINACK,s.next);
    this.event({type:"reliable_complete",sid:s.sid,received:s.received,evaluated:s.evaluated,delivered:s.delivered});
   }else{this.reject("FIN_PENDING_OR_MISSING",p,peer);this.ack(s);}return;
  }
  if(p.kind===R.K.PONG&&s.ping?.nonce===p.seq){
   const rtt=now-s.ping.at;if(rtt>=0&&rtt<3000){s.rtt.push(rtt);if(s.rtt.length>128)s.rtt.shift();}
   s.ping=null;return;
  }
  this.reject("UNEXPECTED_CONTROL_STATE",p,peer);
 }
 samePeer(s,p,peer){return s.peer.address===peer.address&&s.peer.port===peer.port&&s.source===p.source&&s.mode===p.mode;}
 pump(s){
  if(s.inflight!==null||s.failed||s.closed)return;
  const row=s.buffer.get(s.next);if(!row)return;s.inflight=row.seq;
  let consumed=false;
  const done=(error,engineEvaluated=true)=>{
   if(consumed)return;consumed=true;
   if(s.closed||s.failed)return;
   if(error){s.failed=true;this.event({type:"reliable_engine_failed",sid:s.sid,seq:row.seq,error:String(error)});return;}
   if(s.inflight!==row.seq){s.failed=true;return;}
   const delay=this.now()-row.receivedAt;s.evalMsSum+=delay;s.evalMsMax=Math.max(s.evalMsMax,delay);
   s.delivered++;if(engineEvaluated)s.evaluated++;
   s.lastSample=row.sample;s.buffer.delete(row.seq);s.history.set(row.seq,row.fingerprint);
   while(s.history.size>1025)s.history.delete(s.history.keys().next().value);
   s.next=(s.next+1)>>>0;s.inflight=null;
   this.event({type:"reliable_evaluated",sid:s.sid,seq:row.seq,frame:row.sample.frame,
    fingerprint:row.fingerprint,engineEvaluated,receiveToEvaluationMs:delay,captureTickMs:row.b});
   this.ack(s);this.pump(s);
  };
  try{this.evaluate(s,row,done);}catch(e){done(e);}
 }
 tick(){
  const now=this.now();
  for(const s of this.sessions.values()){
   if(s.closed)continue;
   if(now-s.last>15000){
    s.failed=true;s.closed=true;if(this.active===s.sid)this.active=null;
    this.event({type:"reliable_timeout",sid:s.sid,uncommitted:s.buffer.size});continue;
   }
   if(now-s.lastAck>500)this.ack(s);
   if(!s.ping||now-s.ping.at>2500){
    const nonce=crypto.randomBytes(4).readUInt32LE();s.ping={nonce,at:now};this.send(s,R.K.PING,nonce);
   }
  }
 }
 summary(s){
  const rt=s.rtt;
  return {id:s.sid,sid:s.sid,protocol:2,peer:s.peer.address+":"+s.peer.port,source:s.source,mode:s.mode,
   provenance:s.source===2?"SIMULATED":s.manual?"PHYSICAL_CONFIRMED_MANUALLY":"RUNTIME_UNVERIFIED",
   manualNote:s.manual,connection:s.closed?(s.failed?"FAILED":"COMPLETE"):s.failed?"FAILED":this.now()-s.last>3500?"DISCONNECTED":"ACTIVE",
   durationMs:this.now()-s.first,configuredHz:s.configuredHz,received:s.received,duplicate:s.duplicates,
   recovered:s.recovered,missingInferred:s.holes.size,conflicting:s.conflicting,
   evaluated:s.evaluated,delivered:s.delivered,nextToEvaluate:s.next,queue:s.buffer.size,queuePeak:s.queuePeak,
   originalDatagrams:s.originalDatagrams,retryDatagrams:s.retryDatagrams,datagrams:s.wire,bytes:s.bytes,
   sender:s.status,receiveToEvaluationMs:{max:s.evalMsMax,mean:s.delivered?s.evalMsSum/s.delivered:null},
   captureToEvaluationMs:null,captureToEvaluationNote:"Clocks are not synchronized. Sender captureToAckMaxMs is an upper bound, not exact one-way latency.",
   rttMs:rt.length?rt.at(-1):null,rtt:{count:rt.length,minMs:rt.length?Math.min(...rt):null,
    maxMs:rt.length?Math.max(...rt):null,meanMs:rt.length?rt.reduce((a,b)=>a+b,0)/rt.length:null,
    jitterMs:rt.length>1?rt.slice(1).reduce((a,b,i)=>a+Math.abs(b-rt[i]),0)/(rt.length-1):null},
   frame:s.lastSample?.frame??null,values:s.lastSample?.words??null,officialEligible:false};
 }
}
module.exports={ReliableCore};
