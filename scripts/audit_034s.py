#!/usr/bin/env python3
"""034S offline: compare working R0/R1, white R2, and staged S0-S3."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_034q import parse_elf, linker_members, read_nds_cpu

VARIANTS = ("r0","r1","r2","s0","s1","s2","s3")
TARGETS = {"s1":"dsirb_034s_twl_canary",
           "s2":"mbedtls_internal_aes_encrypt",
           "s3":"wifi_sdio_send_command"}
BASE_TWL, END_TWL = 0x03000000, 0x03040000

def gather(args, name):
    p = getattr(args,name+"_nds")
    cpu = {k: read_nds_cpu(p,k) for k in ("ARM7","ARM9")}
    e = parse_elf(getattr(args,name+"_elf"))
    members = linker_members(getattr(args,name+"_map"))
    if not members:
        raise RuntimeError("BLOCKED: empty linker map archive list for "+name)
    sec = {x["name"]:x for x in e["sections"]}
    def summary(key):
        x = sec.get(key)
        return {"size":x["size"],"vma":"0x%08X"%x["addr"],
                "end":"0x%08X"%(x["addr"]+x["size"]),
                "sha256":x["sha256"]} if x else None
    return {"cpu":cpu,
            "segments":e["loads"],
            "sections":{k:summary(k) for k in
                (".crt0",".text",".rodata",".data",".bss",
                 ".twl",".twl_bss",".init_array",".preinit_array")},
            "symbols":e["symbols"],"members":members,
            "relocations_left":e["remaining_relocations"]}

def audit(args):
    data = {k:gather(args,k) for k in VARIANTS}
    if data["r0"]["cpu"] != data["s0"]["cpu"]:
        raise RuntimeError("BLOCKED: S0 differs from physically booted R0")
    if len({data[n]["cpu"]["ARM9"]["sha256"] for n in VARIANTS})!=1:
        raise RuntimeError("BLOCKED: ARM9 source/payload differs")
    if data["s0"]["cpu"]["ARM7"]["sha256"]==data["s1"]["cpu"]["ARM7"]["sha256"]:
        raise RuntimeError("BLOCKED: TWL canary optimized out")
    for name,symbol in TARGETS.items():
        s = data[name]["symbols"].get(symbol)
        if not s or s["section"]!=".twl":
            raise RuntimeError("BLOCKED: selected symbol not in TWL: "+symbol)
        addr = int(s["addr"],16)
        if not BASE_TWL<=addr<END_TWL:
            raise RuntimeError("BLOCKED: out-of-bounds TWL symbol "+symbol)
    for name in ("s2","s3"):
        if data[name]["cpu"]["ARM7"]["sha256"]==data["s0"]["cpu"]["ARM7"]["sha256"]:
            raise RuntimeError("BLOCKED: target library link missing: "+name)
        if "Wifi_TWL_Update" in data[name]["symbols"] or "Wifi_Update" in data[name]["symbols"]:
            raise RuntimeError("BLOCKED: selected full TWL Wifi_Update indirectly in "+name)
    if "Wifi_TWL_Update" not in data["r2"]["symbols"] or "Wifi_NTR_Update" not in data["r1"]["symbols"]:
        raise RuntimeError("BLOCKED: known reference ELF symbols missing")
    for name,d in data.items():
        for section in (".twl",".twl_bss"):
            s = d["sections"][section]
            if not s or not BASE_TWL<=int(s["vma"],16)<END_TWL or int(s["end"],16)>END_TWL:
                raise RuntimeError("BLOCKED: invalid TWL VMA: "+name+" "+section)
        d["archive_member_count"]=len(d["members"])
        d["new_archive_members"]=[m for m in d["members"] if m not in set(data["r0"]["members"])]
    for d in data.values():
        focus={"main","Wifi_Update","Wifi_NTR_Update","Wifi_TWL_Update",
               "dsirb_034s_twl_canary","mbedtls_internal_aes_encrypt",
               "wifi_sdio_send_command","installWifiFIFO"}
        d["symbols"]={k:v for k,v in d["symbols"].items() if k in focus}
        del d["members"]
    report={
      "status":"034S_STATIC_TWL_SUBSYSTEM_GATES_PASS_NO_HARDWARE_PROOF",
      "baseline":{"r0":"PHYSICAL_BOOT","r1":"PHYSICAL_BOOT","r2":"PHYSICAL_WHITE",
                  "s0":"NOT_RUN","s1":"NOT_RUN","s2":"NOT_RUN","s3":"NOT_RUN"},
      "sdk":"BlocksDS_v1.24.0_fixed",
      "variants":data,
      "limits":{"crt0_twl_copy":"only if SCFG_A9ROM indicates DSi mode",
                "actual_SCFG_MBK":"NOT_OBSERVED",
                "linked_functions_executed":False,
                "root_cause":"NOT_ESTABLISHED",
                "wifi_connected":False,"retroachievements":False}
    }
    return report

def markdown(r):
    out=["# 0.3.4-S — Auditoria de carregamento TWL",
      "",
      "Observado no DSi XL: R0 e R1 iniciaram; R2 TWL_LINK apresentou tela branca.",
      "S0-S3 ainda não foram testados fisicamente. Wi-Fi não foi inicializado.",
      "",
      "| Variante | ARM7 bytes | TWL bytes | TWL BSS bytes | BSS bytes |",
      "|---|---:|---:|---:|---:|"]
    for name,d in r["variants"].items():
        s=d["sections"]
        out.append("| "+name.upper()+" | "+str(d["cpu"]["ARM7"]["size"])+" | "+
                   str(s[".twl"]["size"])+" | "+str(s[".twl_bss"]["size"])+" | "+
                   str(s[".bss"]["size"] if s[".bss"] else 0)+" |")
    out+=["","## Segmentos PT_LOAD","",
          "| Variante | VMA | LMA | End VMA | File | Mem |",
          "|---|---|---|---:|---:|---:|"]
    for name,d in r["variants"].items():
        for s in d["segments"]:
            out.append("| "+name.upper()+" | "+s["vma"]+" | "+s["lma"]+
                       " | "+s["end_vma"]+" | "+str(s["file_bytes"])+
                       " | "+str(s["mem_bytes"])+" |")
    out+=["","## Objetos vinculados adicionais (S2 AES / S3 SDIO)"]
    for name in ("s2","s3"):
        out+=["","### "+name.upper()]
        for m in r["variants"][name]["new_archive_members"]:
            out.append("- "+m)
    out+=["","## Interpretação","",
      "Aumentos de tamanho e novos objetos não provam causa de travamento.",
      "O CRT0 do BlocksDS 1.24 copia .twl quando detecta modo DSi, mas MBK e SCFG reais do Flipnote Lenny não foram lidos.",
      "Nenhuma função de Wi-Fi foi chamada. Não repetir R2, P1 ou outros binários que travaram.",
      "Nenhuma atualização de NAND, boot.nds, private ou _nds é necessária.",""]
    return "\n".join(out)

def main():
    p=argparse.ArgumentParser()
    for name in VARIANTS:
        for suffix in ("nds","elf","map"):
            p.add_argument("--"+name+"-"+suffix, type=Path,required=True)
    p.add_argument("--json-out",type=Path,required=True)
    p.add_argument("--md-out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a)
    a.json_out.parent.mkdir(parents=True,exist_ok=True)
    a.json_out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    a.md_out.write_text(markdown(result),encoding="utf-8")
    print(json.dumps({"status":result["status"],
      "sections":{k:{"ARM7":v["cpu"]["ARM7"]["size"],
        "TWL":v["sections"][".twl"]["size"],
        "TWL_BSS":v["sections"][".twl_bss"]["size"],
        "added_archive_members":len(v["new_archive_members"]),
        "targets":list(v["symbols"])} for k,v in result["variants"].items()}},
      indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
