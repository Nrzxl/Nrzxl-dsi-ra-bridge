"use strict";
/* Protocol-level integration test. No UDP hardware, no award/engine calls. */
const {execFileSync}=require("node:child_process");
const fs=require("node:fs"),os=require("node:os"),path=require("node:path");
const assert=require("node:assert/strict");
const L=require("../protocol/live.cjs"),P=require("../protocol/bridge.cjs");
const {Core}=require("../protocol/receiver-core.cjs");
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),"dsirb-041-"));
try{
 const exe=path.join(tmp,"wire041");
 execFileSync("cc",["-std=c11","-Wall","-Wextra","-Werror",
   "-Idsi/fixture-041/include","tests/wire-observer-041.c","-o",exe]);
 const wire=execFileSync(exe);
 assert.equal(wire.length,84);
 const hello=wire.subarray(0,20),sample=wire.subarray(20);
 const h=L.parseControl(hello),s=P.decode(sample);
 assert.equal(h.kind,"DSH3");
 assert.equal(h.session,0x41003341);assert.equal(h.nonce,0xD531010A);
 assert.equal(s.frame,1234);assert.equal(s.words[1],1234);assert.equal(s.words[2],3);
 assert.equal(s.address,0x02006400);assert.equal(s.mode,1);
 const events=[],sent=[],peer={address:"192.168.0.10",port:59312};
 let now=1000;
 const core=new Core({now:()=>now,send:(b,p,cb)=>{sent.push(Buffer.from(b));cb(null);},
   nonce:()=>0x12345678,event:e=>events.push(e)});
 assert.equal(core.receive(hello,peer),null);
 assert.equal(sent[0].subarray(0,4).toString(),"DSA3");
 now+=100;
 const accepted=core.receive(sample,peer);
 assert.equal(accepted.sample.words[1],1234);
 assert.equal(core.summary(accepted.session).received,1);
 assert.equal(accepted.session.source,1);
 assert.equal(accepted.session.mode,1);
 assert.equal(core.receive(sample,peer),null);
 assert.equal(core.totals.reasons.DUPLICATE_SNAPSHOT,1);
 const wrong=Buffer.from(sample);wrong[46]^=1;
 assert.equal(core.receive(wrong,peer),null);
 assert.equal(core.totals.reasons.INVALID_CRC,1);
 console.log("041 wire: C serializer → JS original decoder → real receiver Core PASS");
}finally{fs.rmSync(tmp,{recursive:true,force:true});}
