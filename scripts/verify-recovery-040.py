#!/usr/bin/env python3
"""Read-only integrity verifier for exact 033 outputs used in checkpoint 040."""
import hashlib
import json
import struct
import sys
from pathlib import Path

EXPECTED = {
    "SD_COPIAR/nds/DSiRABridge_033/Fixture_B_033_control.nds":
        "524ed6166af75afc4ea88791c359d1c0d6071b3194ee112952842d48c179313e",
    "SD_COPIAR/nds/DSiRABridge_033/Launcher_A_033.nds":
        "5e2e0a785c2808836eb5a74bc6620f79d5f17b1722cc27d4a7c066133976b9ad",
    "SD_COPIAR/DSiRABridge_033/Fixture_B_033_observed.nds":
        "5c30731de87f1f45f6e08ea8e54ec008b8b82f245aa6f5847b5fa8429f8e141a",
}
EXPECTED_ZIP_SHA = {
    "PACOTE_ORIGINAL_SD_033.zip":
        "21b7844a63a16ff99b7ac7cafa0d07b546994008c9051a466d1cad7a5b1835d8",
    "FONTE_COMPLETA_033.zip":
        "951e69e783ae03efc6a335c55ddc54a0b6c7fb34c26260e29f5cc57e03650d04",
}

def validate(root):
    details=[]
    for path,expected in {**EXPECTED,**EXPECTED_ZIP_SHA}.items():
        file=root/path
        if not file.is_file():
            raise ValueError("Missing "+path)
        b=file.read_bytes()
        observed=hashlib.sha256(b).hexdigest()
        if observed != expected:
            raise ValueError("SHA256 mismatch "+path)
        if path.endswith(".nds"):
            if len(b)<0x200:
                raise ValueError("Truncated NDS "+path)
            for header_offset in (0x20,0x30):
                rom,entry,ram,length=struct.unpack_from("<4I",b,header_offset)
                if not (rom>=0x200 and length>0 and rom+length<=len(b)
                       and ram<=(entry&~1)<ram+length):
                    raise ValueError("Invalid NDS CPU segment "+path)
        details.append({"path":path,"bytes":len(b),"sha256":observed,"status":"PASS"})
    return {"status":"STATIC_INTEGRITY_PASS_PHYSICAL_NOT_RUN",
            "origin":"uploaded 033 artifacts; unchanged NDS",
            "files":details,
            "physical_dsi":"NOT_RUN_FOR_033",
            "retroachievements_awards":0}

def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(".")
    try:
        result=validate(root)
    except Exception as e:
        print("BLOCKED:",e)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
