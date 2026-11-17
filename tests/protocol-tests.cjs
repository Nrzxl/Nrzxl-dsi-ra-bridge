/* Same tests run in V8 and Node; no test framework dependency. */
module.exports = function(P) {
  let checks=0;
  function ok(x,name){if(!x)throw Error("FAIL "+name);checks++;}
  function rejects(fn,name){let threw=false;try{fn();}catch(_){threw=true;}ok(threw,name);}
  ok(P.crc32(Uint8Array.from([49,50,51,52,53,54,55,56,57]))===0xCBF43926,"CRC known vector");
  const pkt=P.encode({seq:3,frame:8,counter:10,buttons:1});
  const x=P.decode(pkt);
  ok(x.seq===3&&x.frame===8&&x.words[1]===10,"roundtrip");
  ok(!x.officialEligible&&x.provenance==="SIMULATED","sim no awards");
  ok(P.decode(P.encode({source:1})).provenance==="CONTROLLED_RUNTIME_UNVERIFIED","no hardware attestation");
  rejects(()=>P.decode(pkt.subarray(0,63)),"truncated");
  rejects(()=>P.decode(new Uint8Array(65)),"oversize");
  const bad=pkt.slice();bad[48]^=1;rejects(()=>P.decode(bad),"bit flip");
  function changed(pos,value){const b=pkt.slice();b[pos]=value;
    new DataView(b.buffer).setUint32(60,P.crc32(b.subarray(0,60)),true);return b;}
  for(const [pos,value,name] of [[0,0,"magic"],[4,2,"version"],[5,3,"source"],
    [6,2,"mode"],[7,0,"flags"],[28,43,"header"],[30,5,"count"],
    [32,15,"payload"],[34,1,"reserved"],[36,0,"watch"],[44,0,"value"]])
      rejects(()=>P.decode(changed(pos,value)),name);
  for(const [o,n,s,want] of [[0,16,16,true],[15,1,16,true],[16,1,16,false],
    [16,0,16,false],[-1,1,16,false],[0xFFFFFFFF,4,16,false],
    [0,17,16,false],[0.5,1,16,false]])
      ok(P.safeRange(o,n,s)===want,"bounds "+[o,n,s]);
  const stats=new P.Stats();
  let r=stats.push(P.decode(P.encode({seq:1})),0);
  r=stats.push(P.decode(P.encode({seq:3})),1000);
  ok(r.missing===1&&r.accepted===2&&r.hz===1,"gap and rate");
  ok(stats.push(P.decode(P.encode({seq:3})),1100).duplicate===1,"duplicate");
  ok(stats.push(P.decode(P.encode({seq:2})),1200).reordered===1,"reordered");
  ok(stats.push(P.decode(P.encode({seq:0,session:2})),1300).missing===0,"session isolation");
  const wrap=new P.Stats();
  wrap.push(P.decode(P.encode({seq:0xFFFFFFFF})),0);
  ok(wrap.push(P.decode(P.encode({seq:0})),17).missing===0,"wrap");
  ok(r.latencyMs===null,"no invented one-way latency");
  for(let i=0;i<600;i++){
    const z=P.decode(P.encode({seq:i,counter:i,buttons:i&0xFFF}));
    ok(z.words[1]===i,"600-frame trace "+i);
  }
  return {status:"PASS",checks,scope:"protocol/bridge.cjs in JavaScript runtime"};
};
if(typeof require==="function"&&require.main===module)
  console.log(JSON.stringify(module.exports(require("../protocol/bridge.cjs"))));
