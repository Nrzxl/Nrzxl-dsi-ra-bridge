"use strict";
// Production packet/state machine, injectable monotonic clock and transport.
// Snapshot v1 and control v1 remain byte compatible with 020/030.
const P=require("./bridge.cjs"),L=require("./live.cjs"),crypto=require("node:crypto");
const REASONS=["INVALID_CRC","INVALID_LENGTH","INVALID_HEADER","UNKNOWN_CONTROL","INVALID_VALUE",
 "UNEXPECTED_CONTROL_STATE","UNREGISTERED_SESSION","LATE_PACKET","DUPLICATE_SNAPSHOT",
 "CONFLICTING_SNAPSHOT","SEQUENCE_DISCONTINUITY","CAPACITY_DROPPED","RATE_DROPPED"];
const WIRE_ERRORS=new Set(REASONS.slice(0,5));
function configuredHz(n){return (n>>>8)===0xD53101&&(n&255)>=1&&(n&255)<=30?n&255:null;}
function parse(bytes){
 if(bytes.length!==20&&bytes.length!==64)throw Error("INVALID_LENGTH");
 if(bytes.length===20){
  if(bytes[4]!==1||![1,2].includes(bytes[5])||bytes[6]>1||bytes[7])throw Error("INVALID_HEADER");
  if(bytes.readUInt32LE(16)!==P.crc32(bytes.subarray(0,16)))throw Error("INVALID_CRC");
  if(!["DSH3","DSA3","DSP3","DSO3"].includes(bytes.toString("ascii",0,4)))throw Error("UNKNOWN_CONTROL");
  return {control:L.parseControl(bytes)};
 }
 // Header/layout validation remains delegated to the original decoder.
 try{return {sample:P.decode(bytes)};}catch(e){
  throw Error(e.message==="crc"?"INVALID_CRC":e.message==="controlled-value"?"INVALID_VALUE":"INVALID_HEADER");
 }
}
class Core{
 constructor({now,send,event=()=>{},nonce=()=>crypto.randomBytes(4).readUInt32LE()}){
  this.now=now;this.transport=send;this.event=event;this.nonce=nonce;
  this.sessions=new Map();this.recent=[];this.started=now();
  this.totals={datagrams:0,bytes:0,snapshotDatagrams:0,controlDatagrams:0,acceptedBytes:0,
   crcErrors:0,malformed:0,unregistered:0,capacityDropped:0,rateDropped:0,controlRejected:0,
   expectedControlRepeats:0,sendErrors:0,udpErrors:0,reasons:Object.fromEntries(REASONS.map(x=>[x,0]))};
 }
 key(peer,c){return [peer.address,peer.port,c.source,c.mode,c.session].join(":");}
 anomaly(reason,bytes,peer,s,extra={}){
  this.totals.reasons[reason]++;
  if(WIRE_ERRORS.has(reason)){
   if(reason==="INVALID_CRC")this.totals.crcErrors++;else this.totals.malformed++;
  }
  if(reason==="UNREGISTERED_SESSION")this.totals.unregistered++;
  if(reason==="CAPACITY_DROPPED")this.totals.capacityDropped++;
  if(reason==="RATE_DROPPED")this.totals.rateDropped++;
  if(reason==="UNEXPECTED_CONTROL_STATE"||reason==="LATE_PACKET")this.totals.controlRejected++;
  const row={type:"packet_diagnostic",reason,id:s?.id??null,peer:peer.address+":"+peer.port,
   length:bytes.length,magic:bytes.subarray(0,4).toString("hex"),fingerprint:crypto.createHash("sha256").update(bytes).digest("hex"),
   ...extra};
  this.recent.push({atMs:Math.round(this.now()-this.started),...row});
  if(this.recent.length>64)this.recent.shift();
  this.event(row);
 }
 send(kind,s,nonce){
  const b=L.control(kind,{...s,nonce});
  this.transport(b,s.peer,e=>{if(e)this.sendError(e,kind,s);});
 }
 sendError(e,kind,s){
  this.totals.sendErrors++;this.event({type:"udp_send_error",code:e.code??"UNKNOWN",kind,id:s?.id??null});
 }
 receive(bytes,peer){
  bytes=Buffer.from(bytes);const now=this.now();this.totals.datagrams++;this.totals.bytes+=bytes.length;
  let packet;try{packet=parse(bytes);}catch(e){this.anomaly(e.message,bytes,peer);return null;}
  const c=packet.control??packet.sample,id=this.key(peer,c);let s=this.sessions.get(id);
  if(packet.control){
   this.totals.controlDatagrams++;
   if(c.kind==="DSH3"){
    if(!s){
     if(this.sessions.size>=8){
      const expired=[...this.sessions.values()].find(x=>now-x.last>10000);
      if(expired){this.event({type:"session_evicted",id:expired.id,summary:this.summary(expired)});this.sessions.delete(expired.id);}
      else{this.anomaly("CAPACITY_DROPPED",bytes,peer);return null;}
     }
     s={...c,id,peer:{address:peer.address,port:peer.port},sequence:new L.Sequence(),fingerprints:new Map(),
      first:now,last:now,lastData:now,firstData:now,rtt:[],rttCount:0,rttSum:0,rttMin:null,rttMax:null,
      pending:null,pings:new Map(),manual:null,lastSample:null,rateAt:now,rateCount:0,helloAt:-1000,
      helloRx:0,ackTx:0,pingTx:0,pongRx:0,pongRepeat:0,pongLate:0,helloRepeat:0,
      reconnects:0,datagrams:0,bytes:0,snapshotDatagrams:0,configuredHz:configuredHz(c.nonce)};
     this.sessions.set(id,s);this.event({type:"hello",id,source:c.source,configuredHz:s.configuredHz,
      provenance:c.source===2?"SIMULATED":"RUNTIME_UNVERIFIED"});
    }else{
     s.helloRepeat++;this.totals.expectedControlRepeats++;
     if(now-s.last>3500){s.reconnects++;this.event({type:"session_resumed",id,sequencePreserved:true});}
    }
    s.datagrams++;s.bytes+=bytes.length;s.helloRx++;
    s.configuredHz=configuredHz(c.nonce);
    if(now-s.helloAt>=300){this.send("DSA3",s,c.nonce);s.ackTx++;s.helloAt=now;}
    s.last=now;return null;
   }
   if(!s){this.anomaly("UNREGISTERED_SESSION",bytes,peer,null,{kind:c.kind});return null;}
   s.datagrams++;s.bytes+=bytes.length;
   if(c.kind==="DSO3"){
    s.pongRx++;const ping=s.pings.get(c.nonce);
    if(ping){
     const delay=now-ping.at;
     if(ping.answered){s.pongRepeat++;this.totals.expectedControlRepeats++;
      this.event({type:"control_repeat",id,kind:c.kind,nonce:c.nonce,delayMs:delay});return null;}
     if(delay>=3000||now-s.last>3500){s.pongLate++;ping.answered=true;
      this.anomaly("LATE_PACKET",bytes,peer,s,{kind:c.kind,nonce:c.nonce,delayMs:delay});return null;}
     ping.answered=true;s.rtt.push(delay);if(s.rtt.length>30)s.rtt.shift();
     s.rttCount++;s.rttSum+=delay;s.rttMin=s.rttMin===null?delay:Math.min(s.rttMin,delay);
     s.rttMax=s.rttMax===null?delay:Math.max(s.rttMax,delay);
     if(s.pending?.nonce===c.nonce)s.pending=null;
     s.last=now;return null;
    }
   }
   this.anomaly("UNEXPECTED_CONTROL_STATE",bytes,peer,s,{kind:c.kind,nonce:c.nonce});return null;
  }
  this.totals.snapshotDatagrams++;
  if(!s){this.anomaly("UNREGISTERED_SESSION",bytes,peer);return null;}
  s.datagrams++;s.bytes+=bytes.length;s.snapshotDatagrams++;
  if(now-s.last>3500){this.anomaly("LATE_PACKET",bytes,peer,s,{seq:c.seq,detail:"HELLO required after timeout"});return null;}
  if(now-s.rateAt>=1000){s.rateAt=now;s.rateCount=0;}
  if(++s.rateCount>120){this.anomaly("RATE_DROPPED",bytes,peer,s,{seq:c.seq});return null;}
  const digest=crypto.createHash("sha256").update(bytes).digest("hex"),old=s.fingerprints.get(c.seq);
  let accepted;try{accepted=s.sequence.push(c.seq);}catch(e){
   this.anomaly("SEQUENCE_DISCONTINUITY",bytes,peer,s,{seq:c.seq});return null;
  }
  s.last=now;
  if(old){
   this.anomaly(old===digest?"DUPLICATE_SNAPSHOT":"CONFLICTING_SNAPSHOT",bytes,peer,s,
    {seq:c.seq,frame:c.frame,identical:old===digest,previousFingerprint:old});return null;
  }
  s.fingerprints.set(c.seq,digest);
  for(const seq of s.fingerprints.keys())if(((s.sequence.high-seq)>>>0)>1024)s.fingerprints.delete(seq);
  if(!accepted){this.event({type:"snapshot_reordered",id,seq:c.seq,frame:c.frame});return null;}
  if(s.sequence.received===1)s.firstData=now;
  s.lastData=now;s.lastSample=c;this.totals.acceptedBytes+=bytes.length;
  this.event({type:"snapshot",id,provenance:s.source===2?"SIMULATED":"RUNTIME_UNVERIFIED",
   session:c.session,seq:c.seq,frame:c.frame,words:c.words,readTicks:c.readTicks,fingerprint:digest});
  return {sample:c,session:s};
 }
 tick(){
  const now=this.now();
  for(const s of this.sessions.values()){
   if(now-s.last>3500)continue;
   if(s.pending&&now-s.pending.at<2000)continue;
   let nonce=this.nonce()>>>0;
   // Never overwrite a retained challenge if the random source repeats.
   while(s.pings.has(nonce))nonce=(nonce+1)>>>0;
   const ping={nonce,at:now,answered:false};s.pending=ping;s.pings.set(nonce,ping);
   while(s.pings.size>32)s.pings.delete(s.pings.keys().next().value);
   s.pingTx++;this.send("DSP3",s,nonce);
  }
 }
 summary(s){
  const now=this.now(),age=now-s.last,duration=now-s.first;
  return {id:s.id,peer:s.peer.address+":"+s.peer.port,session:s.session,source:s.source,mode:s.mode,
   provenance:s.source===2?"SIMULATED":s.manual?"PHYSICAL_CONFIRMED_MANUALLY":"RUNTIME_UNVERIFIED",
   manualNote:s.manual??null,connection:age>3500?"DISCONNECTED":"ACTIVE",ageMs:Math.round(age),
   durationMs:Math.round(duration),...s.sequence.report(),frame:s.lastSample?.frame??null,values:s.lastSample?.words??null,
   readTicks:s.lastSample?.readTicks??null,producerDropped:s.lastSample?.producerDropped??0,
   configuredHz:s.configuredHz,configuredHzOrigin:s.configuredHz===null?"UNKNOWN_LEGACY":"HELLO_NONCE_031",
   hz:s.sequence.received>1?(s.sequence.received-1)*1000/Math.max(1,s.lastData-s.firstData):null,
   packetsHz:s.datagrams*1000/Math.max(1,duration),datagrams:s.datagrams,bytes:s.bytes,snapshotDatagrams:s.snapshotDatagrams,
   controls:{helloRx:s.helloRx,helloRepeat:s.helloRepeat,ackTx:s.ackTx,pingTx:s.pingTx,pongRx:s.pongRx,
    pongRepeat:s.pongRepeat,pongLate:s.pongLate},reconnects:s.reconnects,
   rttMs:s.rtt.length?s.rtt.at(-1):null,
   rtt:{count:s.rttCount,minMs:s.rttMin,maxMs:s.rttMax,meanMs:s.rttCount?s.rttSum/s.rttCount:null},
   oneWayLatencyMs:null,officialEligible:false};
 }
}
function feedEngine(stream,line){
 if(stream.destroyed||!stream.writable||stream.writableLength+Buffer.byteLength(line)>4096)return false;
 stream.write(line);return true;
}
module.exports={Core,parse,configuredHz,feedEngine,REASONS};
