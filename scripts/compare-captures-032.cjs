#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto"),P=require("../protocol/bridge.cjs");
function compare(capture,sender,receiver,log){
 if(!capture.length||capture.length%64||capture.length>6000*64)throw Error("DRB length");
 const rows=[];for(let i=0;i<capture.length;i+=64){
  const b=capture.subarray(i,i+64),sample=P.decode(b);
  rows.push({...sample,fingerprint:crypto.createHash("sha256").update(b).digest("hex")});
 }
 const keys=new Set(rows.map(x=>[x.source,x.mode,x.session].join(":")));
 if(keys.size!==1)throw Error("DRB mixes sessions");
 const low=sender.session;
 if(low!==undefined&&rows[0].session!==low)throw Error("sender/DRB session mismatch");
 const sid=sender.sid??((sender.sessionHi??0).toString(16).padStart(8,"0")+rows[0].session.toString(16).padStart(8,"0"));
 const reliable=receiver.reliable?.sessions?.find(x=>x.sid===sid);
 const legacy=receiver.sessions?.find(x=>x.session===rows[0].session&&x.source===rows[0].source&&x.mode===rows[0].mode);
 const session=reliable??legacy;if(!session)throw Error("receiver/DRB session mismatch");
 const relevant=log.filter(x=>reliable?x.sid===sid:x.id===session.id);
 const received=relevant.filter(x=>["snapshot","reliable_snapshot"].includes(x.type));
 const evaluated=relevant.filter(x=>x.type==="reliable_evaluated"&&x.engineEvaluated);
 const rx=new Map(received.map(x=>[x.seq,x])),evalCounts=new Map();
 for(const x of evaluated)evalCounts.set(x.seq,(evalCounts.get(x.seq)??0)+1);
 const missing=[],mismatch=[],duplicateEvaluation=[];
 for(const x of rows){
  if(!rx.has(x.seq))missing.push(x.seq);
  else if(rx.get(x.seq).fingerprint!==x.fingerprint)mismatch.push(x.seq);
  if((evalCounts.get(x.seq)??0)>1)duplicateEvaluation.push(x.seq);
 }
 const captureSeq=rows.map(x=>x.seq),continuous=captureSeq.every((x,i)=>!i||x===((captureSeq[i-1]+1)>>>0));
 const senderCaptured=sender.captured,summaryMatches=senderCaptured===rows.length&&session.received===rx.size;
 const consistent=continuous&&summaryMatches&&!mismatch.length&&!duplicateEvaluation.length;
 const complete=!missing.length&&(!reliable||evaluated.length===rows.length);
 return {status:consistent?"PASS":"FAIL",delivery:complete?"COMPLETE":"INCOMPLETE",version:sender.version,
  scope:"file comparison only; physical origin is separate manual evidence",captured:rows.length,
  capturedContinuous:continuous,receiverUnique:rx.size,engineEvaluated:reliable?evaluated.length:null,
  missing,mismatchedFingerprints:mismatch,duplicateEvaluation,summaryMatches,source:rows[0].source,
  capturedSha256:crypto.createHash("sha256").update(capture).digest("hex")};
}
if(require.main===module){try{
 const [drb,tx,rx,jsonl]=process.argv.slice(2);
 const result=compare(fs.readFileSync(drb),JSON.parse(fs.readFileSync(tx,"utf8")),
  JSON.parse(fs.readFileSync(rx,"utf8")),fs.readFileSync(jsonl,"utf8").trim().split("\n").filter(Boolean).map(JSON.parse));
 console.log(JSON.stringify(result,null,2));if(result.status!=="PASS")process.exitCode=1;
}catch(e){console.error(e.stack);process.exitCode=1;}}
module.exports={compare};
