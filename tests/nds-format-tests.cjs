/* Synthetic headers in MEMORY ONLY. No .nds fixture is written or distributed. */
module.exports=function(N) {
  let checks=0;
  function ok(value,label){if(!value)throw Error("FAIL "+label);checks++;}
  function reject(bytes,label){let failed=false;try{N.validate(bytes);}catch(_){failed=true;}ok(failed,label);}
  function crc(b){
    const d=new DataView(b.buffer);
    d.setUint16(0x15C,N.crc16(b.subarray(0xC0,0x15C)),true);
    d.setUint16(0x15E,N.crc16(b.subarray(0,0x15E)),true);return b;
  }
  function synthetic(){
    const b=new Uint8Array(0x9000),v=new DataView(b.buffer);
    "DSIRABRIDGE".split("").forEach((c,i)=>b[i]=c.charCodeAt(0));
    [[0x20,0x4000],[0x24,0x02000000],[0x28,0x02000000],[0x2C,0x100],
     [0x30,0x8000],[0x34,0x03800000],[0x38,0x03800000],[0x3C,0x100],
     [0x80,0x8100],[0x84,0x4000]].forEach(([o,n])=>v.setUint32(o,n,true));
    b[0x4000]=0xEA;b[0x8000]=0xEA;return crc(b);
  }
  ok(N.crc16(Uint8Array.from([49,50,51,52,53,54,55,56,57]))===0x4B37,"CRC16 known");
  ok(N.validate(synthetic()).status==="PASS","synthetic structure only");
  reject(new Uint8Array(0x100),"truncation");
  let bad=synthetic();bad[0x15E]^=1;reject(bad,"bad header CRC");
  bad=synthetic();bad[0xC0]^=1;new DataView(bad.buffer).setUint16(0x15E,N.crc16(bad.subarray(0,0x15E)),true);
  reject(bad,"bad logo CRC");
  for(const [o,n,label] of [[0x20,0xFFFFFF00,"overflow"],[0x20,0x100,"inside header"],
    [0x20,0x4001,"file alignment"],[0x24,0x01000000,"entry outside"],
    [0x28,0x04000000,"ARM9 MMIO"],[0x2C,0,"ARM9 zero size"],
    [0x2C,0x101,"ARM9 size alignment"],[0x38,0x04000000,"ARM7 MMIO"],
    [0x3C,0,"ARM7 zero size"],[0x30,0x4000,"overlap"],[0x80,0x8000,"used too short"],
    [0x80,0xFFFFFFFF,"used overflow"],[0x84,0x100,"header too small"],
    [0x84,0x4001,"header alignment"]]){
      bad=synthetic();new DataView(bad.buffer).setUint32(o,n,true);reject(crc(bad),label);
  }
  bad=synthetic();bad[0x12]=1;reject(crc(bad),"unit code");
  bad=synthetic();bad[0]=0;reject(crc(bad),"wrong title");
  bad=synthetic();bad.fill(0,0x4000,0x4100);reject(bad,"empty ARM9");
  bad=synthetic();bad.fill(0,0x8000,0x8100);reject(bad,"empty ARM7");
  bad=synthetic();bad[0x12]=2;new DataView(bad.buffer).setUint32(0x1C0,0x4000,true);
  new DataView(bad.buffer).setUint32(0x1C8,0x02400000,true);
  new DataView(bad.buffer).setUint32(0x1CC,0x100,true);reject(crc(bad),"TWL overlap");
  ok(N.within(0,4,4)&&!N.within(0xFFFFFFFF,4,4),"overflow-safe range");
  return {status:"PASS",checks,scope:"synthetic NDS header unit checks in V8; not an ARM build"};
};
if(typeof require==="function"&&require.main===module)
 console.log(JSON.stringify(module.exports(require("../scripts/nds-format.cjs"))));
