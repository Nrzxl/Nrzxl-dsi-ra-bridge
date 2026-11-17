/* Unit integration of the actual CLI with an in-memory filesystem.
 * This does not test Windows processes, real files or UDP sockets.
 */
module.exports=function(P,source){
  let checks=0;
  const files=new Map(), logs=[],err=[];
  let descriptors=new Map(),next=1;
  const fs={
    openSync(name,flag){if(flag!=="wx")throw Error("unexpected open");
      if(files.has(name))throw Error("EEXIST");files.set(name,new Uint8Array(0));
      const id=next++;descriptors.set(id,name);return id;},
    writeSync(id,data){const name=descriptors.get(id);if(!name)throw Error("bad descriptor");
      if(typeof data==="string")data=Uint8Array.from(Array.from(data,c=>c.charCodeAt(0)));
      const old=files.get(name),b=new Uint8Array(old.length+data.length);
      b.set(old);b.set(data,old.length);files.set(name,b);return data.length;},
    closeSync(id){descriptors.delete(id);},
    readFileSync(name){if(!files.has(name))throw Error("ENOENT");return files.get(name);},
    statSync(name){if(!files.has(name))throw Error("ENOENT");return {size:files.get(name).length};}
  };
  function ok(value,name){if(!value)throw Error("FAIL "+name);checks++;}
  function run(args){
    logs.length=0;err.length=0;let time=0;
    const process={argv:["node","bridge.cjs",...args],exitCode:0};
    const require=name=>{
      if(name==="../../protocol/bridge.cjs")return P;
      if(name==="node:fs")return fs;
      if(name==="node:path")return {};
      if(name==="node:dgram")return {createSocket(){throw Error("network not allowed in unit test");}};
      if(name==="node:perf_hooks")return {performance:{now:()=>++time}};
      throw Error("unexpected dependency "+name);
    };
    new Function("require","process","console",source.replace(/^#![^\n]*\n/, ""))(require,process,
      {log:s=>logs.push(s),error:s=>err.push(s)});
    return process;
  }
  run(["simulate","--out","SIM.drb","--frames","600"]);
  ok(files.get("SIM.drb").length===38400,"600 CLI records");
  ok(P.decode(files.get("SIM.drb").subarray(0,64)).source===2,"CLI simulated marker");
  const p=run(["replay","--file","SIM.drb"]);
  ok(p.exitCode===0&&logs.length===601,"CLI replay 600 records and note");
  ok(JSON.parse(logs[599]).officialEligible===false,"CLI replay cannot award");
  const damaged=files.get("SIM.drb").slice();damaged[48]^=1;files.set("BAD.drb",damaged);
  ok(run(["replay","--file","BAD.drb"]).exitCode===1&&err.length===1,"CRC rejection is logged");
  files.set("SHORT.drb",new Uint8Array(63));let caught=false;
  try{run(["replay","--file","SHORT.drb"]);}catch(_){caught=true;}
  ok(caught,"truncated CLI capture rejected");
  caught=false;try{run(["simulate","--out","SIM.drb"]);}catch(_){caught=true;}
  ok(caught&&files.get("SIM.drb").length===38400,"no overwrite");
  return {status:"PASS",checks,scope:"CLI unit integration; mocked filesystem, no OS/UDP"};
};
if(typeof require==="function"&&require.main===module){
  const fs=require("node:fs");
  console.log(JSON.stringify(module.exports(require("../protocol/bridge.cjs"),
    fs.readFileSync(require("node:path").join(__dirname,"../windows/bridge/bridge.cjs"),"utf8"))));
}
