/* DSi RA Bridge protocol v1. Original code, MIT. No network/RA calls. */
(function(root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DSRB = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const SIZE = 64, WATCH = 0xD1A60001, MAGIC_WORD = 0x44534931;
  function integer(n, max=0xFFFFFFFF) { return Number.isInteger(n) && n >= 0 && n <= max; }
  function safeRange(offset, length, size) {
    return integer(offset) && integer(length) && integer(size) &&
      length > 0 && offset <= size && length <= size-offset;
  }
  function crc32(bytes) {
    let c=0xFFFFFFFF;
    for (const b of bytes) {
      c ^= b;
      for(let k=0;k<8;k++) c=(c>>>1)^((c&1)?0xEDB88320:0);
    }
    return (c^0xFFFFFFFF)>>>0;
  }
  function decode(bytes) {
    if (!(bytes instanceof Uint8Array) || bytes.length !== SIZE) throw Error("length");
    const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
    if (v.getUint32(0,true)!==0x42525344) throw Error("magic");
    if (v.getUint8(4)!==1) throw Error("version");
    const source=v.getUint8(5), mode=v.getUint8(6);
    if (![1,2].includes(source) || mode>1 || v.getUint8(7)!==1) throw Error("source/mode/flags");
    if (v.getUint16(28,true)!==44 || v.getUint16(30,true)!==4 ||
        v.getUint16(32,true)!==16 || v.getUint16(34,true)!==0 ||
        v.getUint32(36,true)!==WATCH) throw Error("layout/watch");
    if (v.getUint32(60,true)!==crc32(bytes.subarray(0,60))) throw Error("crc");
    const words=[0,1,2,3].map(i=>v.getUint32(44+i*4,true));
    if (words[0]!==MAGIC_WORD || words[2]>0x3FFF ||
        words[3]!==((words[1]^words[2]^0xA5A55A5A)>>>0)) throw Error("controlled-value");
    return {source,mode,session:v.getUint32(8,true),seq:v.getUint32(12,true),
      frame:v.getUint32(16,true),readTicks:v.getUint32(20,true),
      producerDropped:v.getUint32(24,true),address:v.getUint32(40,true),words,
      provenance:source===1?"CONTROLLED_RUNTIME_UNVERIFIED":"SIMULATED",
      officialEligible:false};
  }
  function encode(sample={}) {
    const b=new Uint8Array(SIZE), v=new DataView(b.buffer);
    const seq=sample.seq??0, frame=sample.frame??seq, counter=sample.counter??frame;
    const buttons=sample.buttons??0, source=sample.source??2, mode=sample.mode??0;
    for(const n of [seq,frame,counter,buttons,source,mode,sample.session??1,
                    sample.readTicks??0,sample.producerDropped??0,sample.address??0])
      if(!integer(n)) throw Error("integer");
    v.setUint32(0,0x42525344,true);
    b[4]=1;b[5]=source;b[6]=mode;b[7]=1;
    [[8,sample.session??1],[12,seq],[16,frame],[20,sample.readTicks??0],
     [24,sample.producerDropped??0],[36,WATCH],[40,sample.address??0],
     [44,MAGIC_WORD],[48,counter],[52,buttons],
     [56,(counter^buttons^0xA5A55A5A)>>>0]].forEach(([p,n])=>v.setUint32(p,n,true));
    [[28,44],[30,4],[32,16]].forEach(([p,n])=>v.setUint16(p,n,true));
    v.setUint32(60,crc32(b.subarray(0,60)),true);
    decode(b);
    return b;
  }
  class Stats {
    constructor(){ this.streams=new Map(); }
    push(sample, nowMs) {
      if(!Number.isFinite(nowMs)) throw Error("clock");
      const key=[sample.source,sample.mode,sample.session].join(":");
      let s=this.streams.get(key);
      if(!s){s={accepted:0,missing:0,duplicate:0,reordered:0,last:null,start:nowMs,lastTime:nowMs};
        this.streams.set(key,s);}
      if(s.last!==null) {
        const d=(sample.seq-s.last)>>>0;
        if(d===0){s.duplicate++;return {...s,acceptedNow:false};}
        if(d>=0x80000000){s.reordered++;return {...s,acceptedNow:false};}
        s.missing+=d-1;
      }
      s.last=sample.seq;s.accepted++;s.lastTime=nowMs;
      return {...s,acceptedNow:true,hz:s.accepted>1&&nowMs>s.start?
        (s.accepted-1)*1000/(nowMs-s.start):null,
        latencyMs:null};
    }
  }
  return {SIZE,WATCH,MAGIC_WORD,safeRange,crc32,decode,encode,Stats};
});
