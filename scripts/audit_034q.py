#!/usr/bin/env python3
"""034Q offline compare of physically proven P0 PASS vs P1 WHITE (no DSi access)."""
import argparse
import collections
import hashlib
import json
import re
import struct
from pathlib import Path

def digest(b):
    return hashlib.sha256(b).hexdigest()

def read_nds_cpu(path, cpu):
    blob=Path(path).read_bytes()
    if len(blob)<0x200:raise ValueError("truncated NDS")
    offset=0x20 if cpu=="ARM9" else 0x30
    rom,entry,ram,size=struct.unpack_from("<4I",blob,offset)
    if rom<0x200 or not size or rom+size>len(blob) or not ram<=(entry&~1)<ram+size:
        raise ValueError("invalid "+cpu+" segment")
    return {"size":size,"sha256":digest(blob[rom:rom+size]),
            "entry":"0x%08X"%entry,"load":"0x%08X"%ram}

def parse_elf(path):
    b=Path(path).read_bytes()
    if len(b)<52 or b[:6]!=b"\x7fELF\x01\x01":
        raise ValueError("expected ELF32 LE")
    phoff,shoff=struct.unpack_from("<II",b,28)
    phents,phnum,shents,shnum,shstr=struct.unpack_from("<5H",b,42)
    if phents<32 or phnum>128 or shents<40 or shnum<1 or shnum>8192:
        raise ValueError("invalid ELF dimensions")
    if phoff+phents*phnum>len(b) or shoff+shents*shnum>len(b):
        raise ValueError("invalid ELF header bounds")
    h=[struct.unpack_from("<10I",b,shoff+i*shents) for i in range(shnum)]
    if shstr>=len(h):raise ValueError("bad section name index")
    def strof(tab,idx):
        if idx>=len(tab):return "<INVALID>"
        end=tab.find(b"\0",idx)
        return tab[idx:end].decode("utf-8","replace") if end>=0 else "<INVALID>"
    names=b[h[shstr][4]:h[shstr][4]+h[shstr][5]]
    secs=[]
    for i,x in enumerate(h):
        name=strof(names,x[0])
        typ,flags,addr,off,size,link,info,align,entsize=x[1:]
        if typ!=8 and off+size>len(b):raise ValueError("bad section "+name)
        raw=None if typ==8 else b[off:off+size]
        secs.append({"name":name,"type":typ,"flags":flags,
            "addr":addr,"size":size,"off":off,"link":link,"entsize":entsize,
            "sha256":None if raw is None else digest(raw)})
    loads=[]
    for i in range(phnum):
        typ,off,vaddr,paddr,filesz,memsz,flags,align=struct.unpack_from("<8I",b,phoff+i*phents)
        if typ!=1:continue
        if memsz<filesz or off+filesz>len(b):raise ValueError("bad PT_LOAD")
        loads.append({"vma":"0x%08X"%vaddr,"lma":"0x%08X"%paddr,
            "file_bytes":filesz,"mem_bytes":memsz,
            "zero_fill_bytes":memsz-filesz,"end_vma":"0x%08X"%(vaddr+memsz),
            "flags":flags})
    symbols={}
    for s in secs:
        if s["type"]!=2:continue
        if s["link"]>=len(secs):raise ValueError("bad symtab strtab")
        string=secs[s["link"]]
        if string["type"]!=3:raise ValueError("missing strtab")
        stab=b[string["off"]:string["off"]+string["size"]]
        step=s["entsize"] or 16
        if step<16 or s["size"]%step:raise ValueError("bad symtab entries")
        for i in range(s["size"]//step):
            nm,addr,size,info,other,idx=struct.unpack_from("<IIIBBH",b,s["off"]+step*i)
            if idx==0 or (info>>4) not in (1,2) or (info&15) not in (1,2):
                continue
            name=strof(stab,nm)
            if not name:continue
            sect=secs[idx]["name"] if idx<len(secs) else "ABS"
            new={"name":name,"addr":"0x%08X"%addr,"size":size,"section":sect}
            if name not in symbols or symbols[name]["size"]<size:
                symbols[name]=new
    relocations=sum(s["size"]//s["entsize"] for s in secs
                    if s["type"] in (4,9) and s["entsize"])
    return {"sections":secs,"loads":loads,"symbols":symbols,
            "elf_sha256":digest(b),"remaining_relocations":relocations}

def linker_members(path):
    source=Path(path).read_text(errors="replace")
    marker="Archive member included to satisfy reference by file (symbol)"
    if marker not in source:raise ValueError("GNU ld map missing archive inclusion header")
    section=source.split(marker,1)[1]
    for cutoff in ("\nAllocating common symbols","\nMemory Configuration",
                   "\nDiscarded input sections","\nLinker script and memory map"):
        section=section.split(cutoff,1)[0]
    return list(dict.fromkeys(re.findall(r"(?m)^(\S+\.a\([^)]+\))\s*$",section)))

def extract_relevant(elf):
    return [
        {"name":s["name"],"addr":"0x%08X"%s["addr"],"size":s["size"],
         "type":s["type"],"sha256":s["sha256"]}
        for s in elf["sections"] if s["size"] and s["name"].startswith(
            (".text",".rodata",".data",".bss",".twl",".init_array",".preinit_array",".fini_array"))
    ]

def analyze(arg):
    nds={name:{cpu:read_nds_cpu(path,cpu) for cpu in ("ARM7","ARM9")}
         for name,path in (("O2",arg.o2_nds),("P0",arg.p0_nds),("P1",arg.p1_nds))}
    if nds["O2"]["ARM7"]["sha256"]!=nds["P0"]["ARM7"]["sha256"] or nds["O2"]["ARM9"]["sha256"]!=nds["P0"]["ARM9"]["sha256"]:
        raise RuntimeError("BLOCKED P0 differs from working O2 CPU payload")
    if nds["P0"]["ARM9"]["sha256"]!=nds["P1"]["ARM9"]["sha256"]:
        raise RuntimeError("BLOCKED ARM9 changed")
    if nds["P0"]["ARM7"]["sha256"]==nds["P1"]["ARM7"]["sha256"]:
        raise RuntimeError("BLOCKED no ARM7 change")
    a,b=parse_elf(arg.p0_elf),parse_elf(arg.p1_elf)
    if "Wifi_Update" in a["symbols"] or "Wifi_Update" not in b["symbols"]:
        raise RuntimeError("BLOCKED DSWiFi symbol control missing")
    am,bm=linker_members(arg.p0_map),linker_members(arg.p1_map)
    if not am or not bm:raise RuntimeError("BLOCKED empty map archives")
    extra=[m for m in bm if m not in set(am)]
    new=[x for name,x in b["symbols"].items() if name not in a["symbols"]]
    new.sort(key=lambda x:(-x["size"],x["name"]))
    sec0={s["name"]:s for s in a["sections"]}
    sec1={s["name"]:s for s in b["sections"]}
    changes=[]
    for name in sorted(set(sec0)|set(sec1)):
        s,t=sec0.get(name),sec1.get(name)
        if s and t and (s["size"],s["addr"],s["sha256"])==(t["size"],t["addr"],t["sha256"]):
            continue
        if not (s and s["size"]) and not (t and t["size"]):continue
        changes.append({"name":name,"P0_bytes":s["size"] if s else 0,
            "P1_bytes":t["size"] if t else 0,
            "delta":(t["size"] if t else 0)-(s["size"] if s else 0),
            "P0_addr":"0x%08X"%s["addr"] if s else None,
            "P1_addr":"0x%08X"%t["addr"] if t else None})
    selected={}
    for name in ("Wifi_Update","WifiData","Wifi_TWL_Update","Wifi_NTR_Update",
                 "Wifi_Init","installWifiFIFO","main","fifoSendValue32"):
        selected[name]={"P0":a["symbols"].get(name),"P1":b["symbols"].get(name)}
    report={
      "status":"034Q_OFFLINE_AUDIT_PASS_NOT_RUNTIME_PROOF",
      "physical":{"P0":"PASS_STAGE1_AND_STAGE2_REACHED",
                  "P1":"WHITE","P2":"BLOCKED_NOT_RUN"},
      "sdk":"BlocksDS_v1.24.0_pinned",
      "nds":nds,
      "elf":{"P0":{"sha256":a["elf_sha256"],"loads":a["loads"],
                   "sections":extract_relevant(a),"remaining_relocations":a["remaining_relocations"]},
             "P1":{"sha256":b["elf_sha256"],"loads":b["loads"],
                   "sections":extract_relevant(b),"remaining_relocations":b["remaining_relocations"]}},
      "changed_sections":changes,
      "added_symbols_count":len(new),
      "largest_new_global_symbols":new[:90],
      "selected_symbols":selected,
      "archive":{"P0_member_count":len(am),"P1_member_count":len(bm),
                 "P1_only_members":extra,"P0_only_members":[m for m in am if m not in set(bm)]},
      "proof_limits":{"function_executed":"NOT_VERIFIED",
                      "NWRAM_MBK_mapping_at_runtime":"NOT_VERIFIED",
                      "root_cause":"NOT_ESTABLISHED"},
      "network":"NOT_USED","NAND":"NOT_MODIFIED","official_RA_awards":0,
    }
    return report

def markdown(r):
    lines=["# 034Q — P0 PASS versus P1 WHITE: relatório offline","",
      "P0: dois STAGE REACHED no DSi XL; P1: WHITE apenas com referência Wifi_Update; P2: BLOQUEADO.",
      "Não executamos Wi-Fi, jogos, escrita no SD nem testes no DSi nesta auditoria.",
      "",
      "## Tamanho das CPU sections NDS","",
      "| Variante | ARM7 bytes | ARM9 bytes |","|---|---:|---:|"]
    for label,cpus in r["nds"].items():
        lines.append("| %s | %s | %s |"%(label,cpus["ARM7"]["size"],cpus["ARM9"]["size"]))
    lines+=["","## Segmentos PT_LOAD ARM7","",
      "| Variante | Endereço virtual | Endereço final | Inicializado | Memória | Flags |",
      "|---|---|---|---:|---:|---:|"]
    for label in ("P0","P1"):
        for seg in r["elf"][label]["loads"]:
            lines.append("| %s | %s | %s | %d | %d | %d |"%(
              label,seg["vma"],seg["end_vma"],seg["file_bytes"],seg["mem_bytes"],seg["flags"]))
    lines+=["","## Seções alteradas","",
        "| Nome | P0 | P1 | Delta | VMA P0 | VMA P1 |","|---|---:|---:|---:|---|---|"]
    for z in r["changed_sections"]:
        if z["name"].startswith((".text",".rodata",".data",".bss",".twl",".init_array",".preinit_array",".fini_array")):
            lines.append("| %s | %d | %d | %+d | %s | %s |"%(
                z["name"],z["P0_bytes"],z["P1_bytes"],z["delta"],z["P0_addr"],z["P1_addr"]))
    lines+=["","## Objetos de biblioteca selecionados somente no P1",""]
    for member in r["archive"]["P1_only_members"]:
        lines.append("- "+member)
    lines+=["","## Principais símbolos novos (global)","",
            "| Nome | Endereço | Bytes | Seção |","|---|---|---:|---|"]
    for z in r["largest_new_global_symbols"][:40]:
        lines.append("| %s | %s | %d | %s |"%(z["name"],z["addr"],z["size"],z["section"]))
    lines+=["","## Símbolos de interesse","",
            "| Nome | P0 | P1 |","|---|---|---|"]
    for name,v in r["selected_symbols"].items():
        lines.append("| %s | %s | %s |"%(name,
          v["P0"]["addr"] if v["P0"] else "ausente",
          v["P1"]["addr"] if v["P1"] else "ausente"))
    lines+=["","## Restrições de interpretação","",
       "A presença de objetos no mapa prova inclusão no vínculo, não execução ou causa da tela branca.",
       "A configuração efetiva de MBK/NWRAM do DSi não foi lida.",
       "A versão 0.3.4-Q não distribui novo NDS e NÃO deve ser testada no console.",
       "Não repetir P1; não iniciar P2. Preservar boot.nds, _nds, private, NAND e Unlaunch.",""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    for flag in ("o2_nds","p0_nds","p1_nds","p0_elf","p1_elf","p0_map","p1_map","json_out","md_out"):
        p.add_argument("--"+flag.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    r=analyze(a)
    a.json_out.parent.mkdir(parents=True,exist_ok=True)
    a.json_out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    a.md_out.write_text(markdown(r),encoding="utf-8")
    print(json.dumps({
      "status":r["status"],
      "P0_arm7_bytes":r["nds"]["P0"]["ARM7"]["size"],
      "P1_arm7_bytes":r["nds"]["P1"]["ARM7"]["size"],
      "P1_only_archive_members":r["archive"]["P1_only_members"],
      "added_global_symbols":r["added_symbols_count"],
      "symbols":r["selected_symbols"],
      "P0_load":r["elf"]["P0"]["loads"],
      "P1_load":r["elf"]["P1"]["loads"],
    },indent=2,ensure_ascii=False))
if __name__=="__main__":main()
