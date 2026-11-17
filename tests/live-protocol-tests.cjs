"use strict";
const assert=require("node:assert/strict"),L=require("../protocol/live.cjs");
let checks=0;
function ok(x){assert.ok(x);checks++;}
for(const kind of ["DSH3","DSA3","DSP3","DSO3"]){
 const c=L.parseControl(L.control(kind,{source:1,mode:1,session:0xFFFFFFFF,nonce:3}));
 ok(c.kind===kind&&c.session===0xFFFFFFFF&&c.nonce===3);
}
for(const b of [Buffer.alloc(19),Buffer.alloc(21),Buffer.alloc(20)]){
 assert.throws(()=>L.parseControl(b));checks++;
}
let b=L.control("DSH3",{source:2,session:5});b[12]^=1;assert.throws(()=>L.parseControl(b));checks++;
for(const [ip,want] of [["192.168.0.2",true],["10.0.0.1",true],["172.16.0.2",true],
 ["172.31.1.5",true],["172.32.0.2",false],["8.8.8.8",false],["192.168.1.255",false],
 ["256.1.1.1",false],["1.2.3",false],["1e1.0.0.1",false]])ok(L.privateIP(ip)===want);
const s=new L.Sequence();ok(s.push(0));ok(s.push(2));ok(!s.push(1));ok(s.push(3));ok(s.push(5));ok(!s.push(5));
ok(s.report().missingInferred===1);ok(s.report().duplicate===1);ok(s.report().lateRecovered===1);
const w=new L.Sequence();w.push(0xFFFFFFFF);ok(w.push(0));ok(w.report().missingInferred===0);
assert.throws(()=>w.push(10000));checks++;
for(let i=6;i<3000;i++)s.push(i);
ok(s.seen.size<=1025&&s.holes.size<=1025);
console.log(JSON.stringify({status:"PASS",checks,scope:"live controls, loss/reordering, bounded windows; no hardware"}));
