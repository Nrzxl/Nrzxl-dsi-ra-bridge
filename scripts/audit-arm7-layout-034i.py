#!/usr/bin/env python3
"""Static ELF32/NDS diagnostic for known 034G/H ARM7 homebrew builds.
Read-only; does not modify ROMs, write an SD card or run a game.
"""
import argparse
import json
import struct
from pathlib import Path

def info(elf_path, nds_path, label):
    data=elf_path.read_bytes()
    if len(data)<52 or data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        raise ValueError("expected 32-bit little endian ELF")
    e_phoff=struct.unpack_from("<I", data,28)[0]
    e_phentsize=struct.unpack_from("<H", data,42)[0]
    e_phnum=struct.unpack_from("<H", data,44)[0]
    if e_phentsize < 32 or e_phnum > 96 or e_phoff+e_phentsize*e_phnum > len(data):
        raise ValueError("unexpected ELF program headers")
    segments=[]
    for index in range(e_phnum):
        off=e_phoff+index*e_phentsize
        tp, fileoff, va, pa, filesize, memorysize, flags, align = struct.unpack_from("<8I", data,off)
        if tp == 1:
            if filesize > memorysize or fileoff+filesize>len(data):
                raise ValueError("invalid load segment")
            segments.append({
                "vaddr":f"0x{va:08X}","paddr":f"0x{pa:08X}",
                "file_size":filesize,"mem_size":memorysize,
                "uninitialized_bytes":memorysize-filesize,
                "memory_end":f"0x{va+memorysize:08X}",
                "flags":flags
            })
    nds=nds_path.read_bytes()[:0x200]
    if len(nds)<0x200:
        raise ValueError("invalid NDS header")
    start, entry, load_addr, length = struct.unpack_from("<4I",nds,0x30)
    nsize=nds_path.stat().st_size
    if length==0 or start+length>nsize:
        raise ValueError("NDS ARM7 out of bounds")
    return {
        "label":label,
        "elf_program_load_segments":segments,
        "nds_arm7":{
            "rom_offset":f"0x{start:08X}",
            "entry":f"0x{entry:08X}",
            "ram_load_start":f"0x{load_addr:08X}",
            "ram_load_end":f"0x{load_addr+length:08X}",
            "bytes":length
        },
        "source_of_truth":"ELF program headers and final NDS header, offline static only",
        "runtime_memory_availability":"NOT_VERIFIED",
        "hardware": "NOT_RUN",
        "official_awards":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--label",required=True)
    p.add_argument("--elf",type=Path,required=True)
    p.add_argument("--nds",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=info(a.elf,a.nds,a.label)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    main()
