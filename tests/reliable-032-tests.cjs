"use strict";
const A=require("node:assert/strict"),P=require("../protocol/bridge.cjs"),R=require("../protocol/reliable.cjs"),
 {ReliableCore}=require("../protocol/reliable-core.cjs"),{spawnSync}=require("node:child_process");
let checks=0;const eq=(a,b)=>{A.deepEqual(a,b);checks++;};
function run(count,start=0){
 let t=0,acks=[],evaluated=[],pending=[],events=[],sendFailure=false;
 const core=new ReliableCore({now:()=>t,send:(b,p,cb)=>{acks.push(R.decode(b));cb(sendFailure?{code:"ENOBUFS"}:null);},
  event:r=>events.push(r),evaluate:(s,row,done)=>{evaluated.push(row.seq);pending.push(done);}});
 const peer={address:"127.0.0.1",port:1234},lo=27,hi=19;
 const wire=(kind,seq=start,a=0,b=0,retry=false,payload=null)=>R.encode({kind,seq,a,b,retry,payload,lo,hi,source:2,mode:1});
 const packet=(offset,attempt=1)=>wire(R.K.DATA,(start+offset)>>>0,attempt,offset*100,attempt>1,
  P.encode({source:2,mode:1,session:lo,seq:(start+offset)>>>0,counter:offset}));
 const drain=()=>{while(pending.length)pending.shift()(null,true);};
 core.receive(wire(R.K.HELLO,start,10,count),peer);
 const s=[...core.sessions.values()][0];
 // ACK cannot advance before the engine receipt. Duplicate seq0 cannot be dispatched twice.
 core.receive(packet(0),peer);core.receive(packet(0),peer);
 eq(evaluated.length,1);eq(acks.at(-1).seq,start);eq(acks.at(-1).a,1);drain();
 for(let i=1;i<count;i++){
  t+=10;
  if(i===66||i===555)continue;
  core.receive(packet(i),peer);
  if(i%97===9)core.receive(packet(i),peer);
  if(i===69)core.receive(packet(66,2),peer);
  if(i===558)core.receive(packet(555,2),peer);
  drain();
 }
 drain();
 eq(s.evaluated,count);eq(new Set(evaluated).size,count);
 eq(evaluated,Array.from({length:count},(_,i)=>(start+i)>>>0));
 eq(s.holes.size,0);eq(s.recovered,count>555?2:count>66?1:0);
 A.ok(s.history.size<=1025&&s.buffer.size<=32);checks++;
 core.receive(wire(R.K.FIN,(start+count)>>>0),peer);eq(s.closed,true);eq(acks.at(-1).kind,R.K.FINACK);
 core.receive(wire(R.K.FIN,(start+count)>>>0),peer);eq(acks.at(-1).kind,R.K.FINACK);
 core.receive(packet(count-1,2),peer);eq(s.evaluated,count);
 core.receive(wire(R.K.HELLO,start,10,count),peer);eq(events.at(-1).reason,"SESSION_ID_REUSE");
 // Consecutive fresh SID; old data cannot enter the new state.
 const hello2=R.encode({kind:R.K.HELLO,lo:28,hi,source:2,mode:1,seq:0,a:10,b:10});
 core.receive(hello2,peer);eq(core.active,hi.toString(16).padStart(8,"0")+"0000001c");
 // Invalid frame types, CRC, truncation and conflicting payload are visible.
 const bad=packet(0);bad[40]^=1;core.receive(bad,peer);
 core.receive(Buffer.alloc(95),peer);eq(core.totals.invalid,2);
 sendFailure=true;core.receive(hello2,peer);eq(core.totals.sendErrors,1);
 return {core,s};
}
run(600);run(1200);run(6000);run(600,0xFFFFFF00);
const {core}=run(10);const s=[...core.sessions.values()].at(-1);
core.now=()=>20000;core.tick();eq(s.closed,true);eq(s.failed,true);
// Real C wire golden, same fields and nested v1 bytes.
if(process.argv[2]){
 const x=spawnSync(process.argv[2],["27","19","0"],{input:"G\n",encoding:"utf8"});
 eq(x.status,0);const hex=x.stdout.trim().slice(2);
 const expected=R.encode({kind:R.K.DATA,lo:27,hi:19,source:2,mode:1,seq:66,a:2,b:1234,retry:true,
  payload:P.encode({source:2,mode:1,session:27,seq:66,frame:396,counter:66,readTicks:2})});
 eq(hex,expected.toString("hex"));
}
{
 let now=0,acks=[],callbacks=[],dispatch=0;
 const peer={address:"127.0.0.1",port:42};
 const c=new ReliableCore({now:()=>now,send:(b,p,cb)=>{acks.push(R.decode(b));cb(null);},
  evaluate:(s,row,done)=>{dispatch++;callbacks.push(done);}});
 const hello=R.encode({kind:R.K.HELLO,lo:31,hi:32,source:2,mode:1,seq:0,a:10,b:100});
 const pkt=i=>R.encode({kind:R.K.DATA,lo:31,hi:32,source:2,mode:1,seq:i,a:1,b:0,
  payload:P.encode({source:2,mode:1,session:31,seq:i,counter:i})});
 c.receive(hello,peer);for(let i=0;i<32;i++)c.receive(pkt(i),peer);
 const s=[...c.sessions.values()][0];eq(s.buffer.size,32);eq(dispatch,1);eq(acks.at(-1).b,0);
 c.receive(pkt(32),peer);eq(s.buffer.size,32);
 c.receive(R.encode({kind:R.K.FIN,lo:31,hi:32,source:2,mode:1,seq:32}),peer);eq(s.closed,false);
 while(callbacks.length)callbacks.shift()(null,true);
 eq(s.next,32);eq(s.evaluated,32);eq(s.buffer.size,0);eq(acks.at(-1).b,32);
 c.receive(pkt(31),peer);eq(s.evaluated,32);
 c.receive(pkt(32),peer);eq(dispatch,33);now=20000;c.tick();callbacks.shift()(null,true);
 eq(s.evaluated,32);eq(s.failed,true);
}

console.log(JSON.stringify({status:"PASS",checks,sessions:[600,1200,6000],loss:[66,555],
 idempotent:true,ordered:true,ackAfterEvaluation:true,wrap:true,finiteBuffers:true,cGolden:!!process.argv[2]}));
