#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto"),P=require("../protocol/bridge.cjs"),L=require("../protocol/live.cjs");
function audit(b){
 if(!b.length||b.length%64||b.length>64*6000)throw Error("Capture length invalid");
 const seq=new L.Sequence(),frames=[],sessions=new Set();let prev=null;
 for(let i=0;i<b.length;i+=64){const x=P.decode(b.subarray(i,i+64));
  sessions.add(x.source+":"+x.mode+":"+x.session);seq.push(x.seq);
  if(prev!==null)frames.push((x.frame-prev)>>>0);prev=x.frame;
 }
 if(sessions.size!==1)throw Error("Mixed sessions");
 return {status:"PASS",scope:"binary integrity only; physical origin requires separate evidence",bytes:b.length,records:b.length/64,
  sha256:crypto.createHash("sha256").update(b).digest("hex"),...seq.report(),
  first:P.decode(b.subarray(0,64)),last:P.decode(b.subarray(-64)),frameStepHistogram:frames.reduce((a,x)=>(a[x]=(a[x]??0)+1,a),{})};
}
if(require.main===module){try{console.log(JSON.stringify(audit(fs.readFileSync(process.argv[2])),null,2));}
 catch(e){console.error("FAIL: "+e.message);process.exitCode=1;}}
module.exports={audit};
