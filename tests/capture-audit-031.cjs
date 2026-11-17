"use strict";
const assert=require("node:assert/strict"),P=require("../protocol/bridge.cjs"),{audit}=require("../scripts/audit-capture.cjs");
const b=Buffer.concat(Array.from({length:600},(_,seq)=>Buffer.from(P.encode({source:2,mode:1,session:31,seq,frame:9336+seq*6,counter:seq}))));
const report=audit(b);assert.equal(report.records,600);assert.equal(report.duplicate,0);assert.equal(report.last.frame,12930);
assert.equal(report.frameStepHistogram[6],599);assert.equal(report.first.provenance,"SIMULATED");
const corrupt=Buffer.from(b);corrupt[48]^=1;assert.throws(()=>audit(corrupt));
assert.throws(()=>audit(b.subarray(0,b.length-1)));assert.throws(()=>audit(Buffer.alloc(0)));
const mixed=Buffer.from(b);mixed.set(P.encode({source:2,mode:1,session:99,seq:599}),599*64);assert.throws(()=>audit(mixed));
console.log(JSON.stringify({status:"PASS",checks:9,scope:"synthetic audit fixtures only; NOT user's NET000",records:600}));
