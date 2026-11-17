/* Structural validator for this diagnostic, NOT a hardware compatibility test. */
(function(root,factory){
  if(typeof module==="object"&&module.exports)module.exports=factory();
  else root.DSRBNds=factory();
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  function crc16(bytes) {
    let crc=0xFFFF;
    for(const x of bytes){crc^=x;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xA001:0);}
    return crc;
  }
  function within(start,size,total) {
    return Number.isInteger(start)&&Number.isInteger(size)&&start>=0&&size>0&&
      start<=total&&size<=total-start;
  }
  function validate(bytes) {
    function need(x,msg){if(!x)throw Error(msg);}
    need(bytes instanceof Uint8Array&&bytes.length>=0x200,"short header");
    need(bytes.length<=32*1024*1024,"diagnostic exceeds size policy");
    const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
    const u32=o=>v.getUint32(o,true),u16=o=>v.getUint16(o,true);
    const headerSize=u32(0x84),unitCode=bytes[0x12];
    need([0,2,3].includes(unitCode),"unit code");
    need(headerSize>=0x200&&headerSize<=bytes.length&&headerSize%0x200===0,"header size");
    need(u16(0x15E)===crc16(bytes.subarray(0,0x15E)),"header CRC16");
    need(u16(0x15C)===crc16(bytes.subarray(0xC0,0x15C)),"logo CRC16");
    const regions=[];
    function segment(name,off,entry,ram,size,allowed) {
      need(within(off,size,bytes.length)&&off>=headerSize&&off%4===0,name+" file range");
      need(size%4===0&&ram%4===0,name+" alignment");
      need(allowed.some(([low,high])=>ram>=low&&size<=high-ram&&ram<high),name+" RAM range");
      const codeEntry=(entry&0xFFFFFFFE)>>>0;
      need(codeEntry>=ram&&codeEntry-ram<size,name+" entry");
      need(bytes.subarray(off,off+size).some(x=>x!==0),name+" empty binary");
      const row={name,offset:off,entry,ram,size,end:off+size};regions.push(row);return row;
    }
    const arm9=segment("ARM9",u32(0x20),u32(0x24),u32(0x28),u32(0x2C),
      [[0x02000000,0x03000000]]);
    const arm7=segment("ARM7",u32(0x30),u32(0x34),u32(0x38),u32(0x3C),
      [[0x02000000,0x03000000],[0x037C0000,0x03810000]]);
    const used=u32(0x80);
    need(used>=Math.max(arm9.end,arm7.end)&&used<=bytes.length,"used ROM size");
    if(unitCode&2){
      need(headerSize>=0x1000&&bytes.length>=0x1000,"TWL header size");
      for(const [name,at] of [["ARM9i",0x1C0],["ARM7i",0x1D0]]){
        const off=u32(at),ram=u32(at+8),size=u32(at+12);
        if(size){
          need(within(off,size,bytes.length)&&off>=headerSize&&off%4===0,name+" file range");
          need(size%4===0&&ram%4===0,name+" alignment");
          need(ram>=0x02000000&&ram<0x04000000&&size<=0x04000000-ram,name+" RAM range");
          regions.push({name,offset:off,ram,size,end:off+size});
        }else need(off===0||off<=bytes.length,name+" empty offset");
      }
    }
    for(let i=0;i<regions.length;i++)for(let j=i+1;j<regions.length;j++)
      need(regions[i].end<=regions[j].offset||regions[j].end<=regions[i].offset,"file segments overlap");
    const title=Array.from(bytes.subarray(0,12),c=>c?String.fromCharCode(c):"").join("");
    // ndstool 2.3.x can use the generic "HOMEBREW" ROM-header title.
    // For identity, verify the actual 0x840-byte banner and its checksum.
    need(title==="HOMEBREW" || title==="DSIRABRIDGE", "unexpected ROM header title");
    const bannerOffset=u32(0x68);
    const bannerLength=0x840;
    need(within(bannerOffset,bannerLength,bytes.length) &&
      bannerOffset>=headerSize && bannerOffset%4===0,"banner file range");
    need(u16(bannerOffset)===1,"banner version");
    need(u16(bannerOffset+2)===crc16(bytes.subarray(bannerOffset+0x20,bannerOffset+0x840)),
      "banner CRC16");
    const bannerTitle=Array.from({length:128},(_,i)=>
      u16(bannerOffset+0x240+i*2)).map(c=>c?String.fromCharCode(c):" ")
      .join("").split("\n")[0].trim();
    need(bannerTitle==="DSIRABRIDGE", "unexpected diagnostic banner title");
    need(used>=bannerOffset+bannerLength,"used ROM size excludes banner");
    return {status:"PASS",scope:"NDS structural checks only",bytes:bytes.length,
      unitCode,headerSize,title,bannerTitle,headerCrc16:u16(0x15E),logoCrc16:u16(0x15C),
      regions,hardware:"NOT_RUN",officialAchievements:"NOT_RUN"};
  }
  return {crc16,within,validate};
});
