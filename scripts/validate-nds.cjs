#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),crypto=require("node:crypto");
const N=require("./nds-format.cjs");
const [file,jsonFile]=process.argv.slice(2);
if(!file)throw Error("Usage: node scripts/validate-nds.cjs file.nds [report.json]");
const size=fs.statSync(file).size;
if(size>32*1024*1024)throw Error("size limit");
const data=fs.readFileSync(file);
const result={...N.validate(data),sha256:crypto.createHash("sha256").update(data).digest("hex")};
if(jsonFile)fs.writeFileSync(jsonFile,JSON.stringify(result,null,2)+"\n",{flag:"wx"});
console.log(JSON.stringify(result,null,2));
