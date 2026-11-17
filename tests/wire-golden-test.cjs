"use strict";
const assert=require("node:assert/strict"),{execFileSync}=require("node:child_process"),
 P=require("../protocol/bridge.cjs"),L=require("../protocol/live.cjs");
const lines=execFileSync(process.argv[2],[],{encoding:"utf8",timeout:5000}).trim().split(/\r?\n/);
assert.equal(lines[0],L.control("DSH3",{source:1,mode:1,session:0xFFFFFFFF,nonce:73}).toString("hex"));
assert.equal(lines[1],Buffer.from(P.encode({source:1,mode:1,session:0xFFFFFFFF,seq:0x7FFFFFFE,
 frame:131,counter:131,buttons:0x1001,readTicks:3,producerDropped:4,address:0x02001000})).toString("hex"));
console.log(JSON.stringify({status:"PASS",scope:"compiled C serializer equals production Node encoder",packets:2}));
