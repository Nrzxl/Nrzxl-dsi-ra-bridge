#!/usr/bin/env python3
"""034R static-only NTR vs TWL symbol closure & CPU hash audit."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_034q import parse_elf,linker_members,read_nds_cpu

def pack_elf(path,linkmap):
    x=parse_elf(path)
    return {
        "loads":x["loads"],"sha256":x["elf_sha256"],
        "sections":{s["name"]:{"bytes":s["size"],"address":"0x%08X"%s["addr"],
                    "sha256":s["sha256"]}
                    for s in x["sections"]
                    if s["name"].startswith((".twl",".bss",".text",".data",".rodata",".init_array",".preinit_array"))},
        "symbols":{k:v for k,v in x["symbols"].items()
                   if k in ("Wifi_Update","Wifi_NTR_Update","Wifi_TWL_Update",
                            "WifiData","installWifiFIFO","main")},
        "archive_members":linker_members(linkmap)
    }

def main():
    p=argparse.ArgumentParser()
    for key in ("p0_nds","r0_nds","r1_nds","r2_nds","p0_elf","r0_elf","r1_elf","r2_elf",
                "p0_map","r0_map","r1_map","r2_map","json_out","md_out"):
        p.add_argument("--"+key.replace("_","-"),required=True,type=Path)
    a=p.parse_args()
    args=vars(a)
    cs={n:{cpu:read_nds_cpu(args[n+"_nds"],cpu) for cpu in ("ARM7","ARM9")}
        for n in ("p0","r0","r1","r2")}
    if cs["p0"]!=cs["r0"]:
        raise ValueError("BLOCKED R0 CPU bytes not identical to physical P0")
    if len({cs[n]["ARM9"]["sha256"] for n in ("p0","r0","r1","r2")})!=1:
        raise ValueError("BLOCKED ARM9 changed")
    for n in ("r1","r2"):
        if cs[n]["ARM7"]["sha256"]==cs["r0"]["ARM7"]["sha256"]:
            raise ValueError("BLOCKED ARM7 linkage not retained in "+n)
    elves={n:pack_elf(args[n+"_elf"],args[n+"_map"]) for n in ("p0","r0","r1","r2")}
    if elves["p0"]["sha256"]!=elves["r0"]["sha256"]:
        raise ValueError("BLOCKED R0 ELF not identical to P0")
    # Strict symbol partition: mixed link cannot establish NTR vs TWL separately.
    syms={n:set(elves[n]["symbols"]) for n in elves}
    if "Wifi_Update" in syms["r1"] or "Wifi_Update" in syms["r2"]:
        raise ValueError("BLOCKED selected full Wifi_Update trampoline")
    if "Wifi_NTR_Update" not in syms["r1"] or "Wifi_TWL_Update" in syms["r1"]:
        raise ValueError("BLOCKED NTR link unexpectedly pulled TWL Update or lost NTR")
    if "Wifi_TWL_Update" not in syms["r2"] or "Wifi_NTR_Update" in syms["r2"]:
        raise ValueError("BLOCKED TWL link unexpectedly pulled NTR Update or lost TWL")
    if any("Wifi_" in s for s in syms["r0"]):
        raise ValueError("BLOCKED R0 has unexpected DSWiFi")
    base=set(elves["r0"]["archive_members"])
    for n in ("r1","r2"):
        elves[n]["new_archive_members"]=[m for m in elves[n]["archive_members"] if m not in base]
        if not elves[n]["new_archive_members"]:
            raise ValueError("BLOCKED no linked library delta in "+n)
    for n in elves:
        elves[n]["archive_member_count"]=len(elves[n]["archive_members"])
        del elves[n]["archive_members"]
    report={
      "status":"STATIC_NTR_TWL_SYMBOL_PARTITION_PASS_PHYSICAL_NOT_RUN",
      "sdk":"BlocksDS v1.24.0 fixed",
      "physical":{"p0":"PASS_both_STAGES_REACHED","r0":"NOT_RUN","r1":"NOT_RUN","r2":"NOT_RUN"},
      "known_failure":{"p1":"WHITE_with_Wifi_Update_link_not_called"},
      "nds":cs,"elf":elves,
      "warnings":["A linked symbol does not prove execution","MBK/NWRAM runtime mapping not measured",
                  "Neither WiFi subsystem is initialized by source",
                  "Any physical WHITE stops all subsequent probe execution"],
      "network_connections":0,"commercial_games_tested":0,"official_awards":0
    }
    a.json_out.parent.mkdir(parents=True,exist_ok=True)
    a.json_out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# 034R — Comparação estática NTR vs TWL","",
          "Controle físico P0: STAGE 1/2 REACHED. P1 Wifi_Update LINK: WHITE.",
          "R0/R1/R2 não foram executados em DSi; CI não substitui teste físico.",
          "",
          "| Variante | ARM7 NDS bytes | ARM9 SHA256 | Símbolos de update |",
          "|---|---:|---|---|"]
    for n in ("p0","r0","r1","r2"):
        lines.append("| %s | %d | %s | %s |"%(n.upper(),cs[n]["ARM7"]["size"],
                     cs[n]["ARM9"]["sha256"][:14],
                     ", ".join(sorted(s for s in syms[n] if "Update" in s)) or "nenhum"))
    lines+=["","## Seções e endereços de carregamento","",
            "| Probe | Seção | Tamanho (bytes) | VMA |",
            "|---|---|---:|---|"]
    for n in ("r0","r1","r2"):
        for k,s in elves[n]["sections"].items():
            if k in (".text",".rodata",".bss",".twl",".twl_bss"):
                lines.append("| %s | %s | %d | %s |"%(n.upper(),k,s["bytes"],s["address"]))
    lines+=["","## Membros de biblioteca vinculados exclusivamente ao novo símbolo",""]
    for n in ("r1","r2"):
        lines+=["", "### "+n.upper()]
        for member in elves[n]["new_archive_members"]:
            lines.append("- "+member)
    lines+=["","## Limites e segurança","",
      "Nenhum código Wi-Fi foi executado voluntariamente; nenhuma conexão testada.",
      "NTR e TWL são rotas internas do driver, **não garantias de conexão à rede**.",
      "Somente o uso real no DSi poderá confirmar se uma das rotas inicia.",
      "Não alterar boot.nds, private, _nds, NAND ou Unlaunch; não testar antigos P1/P2.",
      ""]
    a.md_out.write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":report["status"],
      "nds_arm7_bytes":{n:cs[n]["ARM7"]["size"] for n in cs},
      "symbols":{n:sorted(s for s in syms[n] if "Update" in s) for n in elves},
      "new_archive_member_counts":{n:len(elves[n].get("new_archive_members",[])) for n in ("r1","r2")}},
      indent=2))

if __name__=="__main__":main()
