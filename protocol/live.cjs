"use strict";
const P=require("./bridge.cjs");
const MAGIC=["DSH3","DSA3","DSP3","DSO3"];
function control(kind,s={}) {
  if(!MAGIC.includes(kind))throw Error("control kind");
  const b=Buffer.alloc(20);b.write(kind,0,"ascii");b[4]=1;
  b[5]=s.source??1;b[6]=s.mode??1;b[7]=0;
  b.writeUInt32LE(s.session>>>0,8);b.writeUInt32LE(s.nonce>>>0,12);
  b.writeUInt32LE(P.crc32(b.subarray(0,16)),16);parseControl(b);return b;
}
function parseControl(b) {
  if(b.length!==20)throw Error("control length");
  const kind=Buffer.from(b.subarray(0,4)).toString("ascii");
  if(!MAGIC.includes(kind)||b[4]!==1||![1,2].includes(b[5])||b[6]>1||b[7])throw Error("control header");
  const v=new DataView(b.buffer,b.byteOffset,b.byteLength);
  if(v.getUint32(16,true)!==P.crc32(b.subarray(0,16)))throw Error("control CRC");
  return {kind,source:b[5],mode:b[6],session:v.getUint32(8,true),nonce:v.getUint32(12,true)};
}
function privateIP(ip) {
 const a=ip.split(".");if(a.length!==4||a.some(x=>!/^\d{1,3}$/.test(x)||Number(x)>255))return false;
 const [x,y,,z]=a.map(Number);
 return z!==255&&(x===10||(x===172&&y>=16&&y<=31)||(x===192&&y===168));
}
class Sequence {
 constructor(){this.high=null;this.seen=new Set();this.holes=new Set();this.received=0;this.duplicate=0;this.reordered=0;this.gaps=0;this.recovered=0;}
 push(n){
  if(!Number.isInteger(n)||n<0||n>0xFFFFFFFF)throw Error("sequence integer");
  if(this.seen.has(n)){this.duplicate++;return false;}
  if(this.high!==null){
   const d=(n-this.high)>>>0;
   if(d>=0x80000000){
    this.reordered++;
    if(this.holes.delete(n))this.recovered++;
    this.seen.add(n);this.trim();return false;
   }
   if(d>4096)throw Error("sequence discontinuity");
   for(let i=1;i<d;i++)this.holes.add((this.high+i)>>>0);
   this.gaps+=d-1;
  }
  this.high=n;this.received++;this.seen.add(n);this.trim();return true;
 }
 trim(){
  if(this.high===null)return;
  for(const set of [this.seen,this.holes])for(const n of set)
   if(((this.high-n)>>>0)>1024)set.delete(n);
 }
 report(){return {received:this.received,duplicate:this.duplicate,reordered:this.reordered,
  missingInferred:this.gaps-this.recovered,gapsTotal:this.gaps,lateRecovered:this.recovered};}
}
module.exports={control,parseControl,privateIP,Sequence};
