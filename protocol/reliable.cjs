"use strict";
const P=require("./bridge.cjs");
const SIZE=96,WINDOW=32,K={DATA:1,HELLO:2,ACK:3,STATUS:4,FIN:5,FINACK:6,PING:7,PONG:8};
function dist(a,b){return (a-b)>>>0;}
function encode(p){
 const b=Buffer.alloc(SIZE);b.write("DSR2");b[4]=2;b[5]=p.kind;b[6]=p.source??2;
 b[7]=((p.mode??1)<<1)|(p.retry?1:0);
 for(const [o,v]of [[8,p.lo],[12,p.hi],[16,p.seq],[20,p.a],[24,p.b]])b.writeUInt32LE((v??0)>>>0,o);
 if(p.payload){if(p.payload.length!==64)throw Error("PAYLOAD_LENGTH");b.set(p.payload,28);}
 b.writeUInt32LE(P.crc32(b.subarray(0,92)),92);decode(b);return b;
}
function decode(bytes){
 const b=Buffer.from(bytes);
 if(b.length!==96)throw Error("INVALID_LENGTH");
 if(b.toString("ascii",0,4)!=="DSR2"||b[4]!==2||!Object.values(K).includes(b[5])||
  ![1,2].includes(b[6])||b[7]>3)throw Error("INVALID_HEADER");
 if(b.readUInt32LE(92)!==P.crc32(b.subarray(0,92)))throw Error("INVALID_CRC");
 const p={kind:b[5],source:b[6],mode:b[7]>>>1,retry:!!(b[7]&1),lo:b.readUInt32LE(8),hi:b.readUInt32LE(12),
  seq:b.readUInt32LE(16),a:b.readUInt32LE(20),b:b.readUInt32LE(24),payload:b.subarray(28,92)};
 if(!p.lo&&!p.hi)throw Error("ZERO_SESSION");
 p.sid=p.hi.toString(16).padStart(8,"0")+p.lo.toString(16).padStart(8,"0");
 if(p.kind===K.DATA){
  if(p.a<1||p.a>6||p.retry!==(p.a>1))throw Error("INVALID_ATTEMPT");
  p.sample=P.decode(p.payload);if(p.sample.seq!==p.seq||p.sample.session!==p.lo||p.sample.source!==p.source||p.sample.mode!==p.mode)throw Error("INNER_MISMATCH");
 }else if(p.retry)throw Error("INVALID_FLAGS");
 return p;
}
module.exports={SIZE,WINDOW,K,dist,encode,decode};
