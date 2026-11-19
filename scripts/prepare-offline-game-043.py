#!/usr/bin/env python3
"""DSi RA Bridge 043: offline-only, spectator-only Super Mario 64 DS (ASMP) TEST SD staging.

- Reads the user's own ROM locally. Never uploads ROM or credentials.
- Verifies SHA256 against the user's 042 preflight report.
- Implements the Nintendo DS rcheevos MD5 content recipe at pinned commit,
  verified *against* the real rcheevos C code by CI. NOT MD5 of the whole ROM.
- Creates a completely NEW directory under the user's home directory (Windows).
- NEVER writes to an existing SD card, game/save, or existing _nds files.
- Packages a self-contained **test-card-only** layout; the retail bootstrap
  may still require _nds scratch files on that test card.
NO OFFICIAL RETROACHIEVEMENTS AWARDS, NO LOGIN, NO LIVE NETWORK.
"""
import argparse
import calendar
import hashlib
import json
import os
import shutil
import struct
import time
from pathlib import Path

GAME_CODE="ASMP"
MAX_ROM_BYTES=1024*1024*1024
PREFIX="DSiRABridge_043"
BOOT_SIZE=604
GAME_PATH="sd:/DSiRABridge_043/mario_europe.nds"
SAVE_PATH="sd:/DSiRABridge_043/mario_test_only.sav"
DSCHEEVOS_PIN="59e9978be7b9c3788357ef0a609caf9dc8ea74f3"
BOOT_PIN="af351f096dd71a37e0e5b18d9709bcc0fb70342f"
RC_PIN="754965ef28db22b0411bfccbde39154cd09e6b79"
SPECTATOR=0x01
EXPECTED_FMT="DSIRB043_OFFLINE_SPECTATOR_ONLY"

def sha256(path):
    m=hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b:break
            m.update(b)
    return m.hexdigest()

def read_range(f,offset,size,file_size,allow_short=False):
    if size<0 or size>16*1024*1024 or offset<0 or offset>file_size:
        raise ValueError("DS ROM range invalid")
    f.seek(offset)
    data=f.read(size)
    if len(data)<size:
        if not allow_short:raise ValueError("DS ROM section unexpectedly truncated")
        data+=b"\0"*(size-len(data))
    return data

def ra_hash_ds(path):
    """Port of pinned rcheevos rc_hash_nintendo_ds(); CI must compare to C binary."""
    size=Path(path).stat().st_size
    if not 0x1000<=size<=MAX_ROM_BYTES:raise ValueError("Invalid NDS ROM size")
    with Path(path).open("rb") as f:
        header=f.read(512)
        if len(header)!=512:raise ValueError("NDS header truncated")
        ofs=0
        if header[:4]==b"\x2e\x00\x00\xea" and header[0xB0:0xB4]==b"\x44\x46\x96\x00":
            ofs=512
            header=read_range(f,ofs,512,size)
        a9=struct.unpack_from("<II",header,0x20)[0]  # arm9 offset
        s9=struct.unpack_from("<I",header,0x2C)[0]
        a7=struct.unpack_from("<I",header,0x30)[0]
        s7=struct.unpack_from("<I",header,0x3C)[0]
        banner=struct.unpack_from("<I",header,0x68)[0]
        if s9+s7>16*1024*1024 or min(s9,s7)<1:
            raise ValueError("Unsupported NDS code sections")
        m=hashlib.md5()
        m.update(header[:0x160])
        m.update(read_range(f,a9+ofs,s9,size))
        m.update(read_range(f,a7+ofs,s7,size))
        # rcheevos zero pads missing banner bytes
        m.update(read_range(f,banner+ofs,0xA00,size,allow_short=True))
        return m.hexdigest()

def fixed_ascii(text,n):
    raw=text.encode("ascii")
    if len(raw)>=n:raise ValueError("Text too large for session field")
    return raw + bytes(n-len(raw))

def synthetic_set():
    # These are LOCAL QA triggers, not RetroAchievements achievement IDs.
    def ach(num,title,mem):
        return {"ID":num,"Title":title,"Description":"LOCAL QA ONLY - NO OFFICIAL AWARD",
          "Flags":3,"Points":1,"MemAddr":mem,
          "Author":"HANNA_QA","BadgeName":"0","Created":1,"Modified":1}
    return {"Success":True,"GameId":9983,"Title":"Mario DS - LOCAL QA 043",
      "ConsoleId":18,"ImageIconUrl":"","RichPresenceGameId":9983,"RichPresencePatch":"",
      "Sets":[{"AchievementSetId":1,"GameId":9983,"Title":None,"Type":"core",
       "ImageIconUrl":"","Achievements":[
          ach(90004301,"QA: 300 real frames (RAM read)","0xH000000=0xH000000.300."),
          ach(90004302,"QA: 900 real frames (RAM read)","0xH000000=0xH000000.900."),
          ach(90004303,"QA: should never trigger","0=1")],
       "Leaderboards":[]}]}

def make_session(rom_path,game_hash,now=None):
    """Construct the documented dscm_boot_t (ABI7, 604B) with offline test replies."""
    if len(game_hash)!=32 or any(ch not in "0123456789abcdef" for ch in game_hash):
        raise ValueError("Bad rcheevos Nintendo DS hash")
    if now is None:
        # DSi RTC stores local clock, upstream mksession mirrors it as UTC.
        now=calendar.timegm(time.localtime())
    replies=[
      {"Success":True,"User":"LOCAL_QA","Token":"","Score":0,"SoftcoreScore":0,"Messages":0},
      synthetic_set(),
      {"Success":True,"Unlocks":[],"HardcoreUnlocks":[],"ServerNow":int(now)}]
    body=bytearray()
    offsets=[]
    lengths=[]
    for reply in replies:
        r=json.dumps(reply,separators=(",",":"),ensure_ascii=True).encode("ascii")
        offsets.append(BOOT_SIZE+len(body))
        lengths.append(len(r))
        body.extend(r)
        body.extend(bytes(4-len(r)%4))
    total=BOOT_SIZE+len(body)
    if total>0x60000:raise ValueError("Offline session too large")
    head=bytearray(BOOT_SIZE)
    struct.pack_into("<III",head,0,0x53435344,BOOT_SIZE,total)
    head[0x0C:0x0C+256]=fixed_ascii(rom_path,256)
    head[0x10C:0x10C+64]=fixed_ascii("http://127.0.0.1:9",64)
    head[0x14C:0x14C+32]=fixed_ascii("LOCAL_QA",32)
    head[0x16C:0x16C+64]=fixed_ascii("",64)
    head[0x1AC:0x1AC+33]=fixed_ascii(game_hash,33)
    head[0x1CD]=0  # softcore - but no awards
    head[0x1CE]=SPECTATOR
    head[0x1CF]=0 # UTC flag unknown, no network
    struct.pack_into("<I",head,0x1D4,int(now)&0xFFFFFFFF)
    struct.pack_into("<3I",head,0x1D8,*offsets)
    struct.pack_into("<3I",head,0x1E4,*lengths)
    head[0x1F6]=0  # never use Wi-Fi
    return bytes(head+body)

def verify_session(data,rom_hash):
    if len(data)<BOOT_SIZE or struct.unpack_from("<III",data,0)!=(0x53435344,BOOT_SIZE,len(data)):
        raise ValueError("Offline session invalid")
    if data[0x1CD]!=0 or data[0x1CE]!=SPECTATOR or data[0x1F6]!=0:
        raise ValueError("Session must be spectator, softcore, offline")
    if data[0x16C:0x1AC].strip(b"\0"):
        raise ValueError("Session must never contain login token")
    if data[0x1AC:0x1AC+32].decode("ascii")!=rom_hash:
        raise ValueError("Session hash mismatch")
    if data[0x0C:0x0C+len(GAME_PATH)]!=GAME_PATH.encode("ascii"):
        raise ValueError("Session targets wrong game path")
    return True

def nds_header(path):
    with Path(path).open("rb") as f:
        h=f.read(0x200)
    if len(h)<0x200 or h[12:16]!=GAME_CODE.encode() or h[0x12]!=0:
        raise ValueError("Expected EU Super Mario 64 DS code ASMP, unit 0")
    return h

def verify_binaries(boot,module,manifest):
    m=json.loads(Path(manifest).read_text(encoding="utf-8"))
    if m.get("format")!=EXPECTED_FMT or not m.get("offline_gates_passed"):
        raise ValueError("Unsafe/unverified 043 manifest")
    if m.get("source_bootstrap")!=BOOT_PIN or m.get("source_dscheevos")!=DSCHEEVOS_PIN or m.get("source_rcheevos")!=RC_PIN:
        raise ValueError("Unexpected source revision")
    for name,p in (("bootstrap",boot),("module",module)):
        if sha256(p)!=m.get(name+"_sha256"):
            raise ValueError(name+" has unexpected bytes or was modified")
    b=Path(boot).read_bytes()
    if not (b[:12].startswith(b"NDSBOOTSTRAP") and b[12:16]==b"KBSE"):
        raise ValueError("Unexpected bootstrap image")
    with Path(module).open("rb") as f:h=f.read(12)
    if len(h)!=12 or h[:4]!=b"DSCV" or struct.unpack_from("<I",h,4)[0]!=7:
        raise ValueError("ARM9 module magic/ABI mismatch")
    return m

def prepare(rom,preflight,boot,module,manifest,destination):
    rom,preflight,boot,module,manifest,destination=map(Path,(rom,preflight,boot,module,manifest,destination))
    if destination.exists():
        raise ValueError("Output directory already exists; NEVER overwrite any existing folder")
    if os.name=="nt":
        home=Path.home().resolve()
        if os.path.commonpath([str(home),str(destination.resolve())]).casefold()!=str(home).casefold():
            raise ValueError("Choose a new staging folder under your Windows user profile, not an SD drive")
    if destination.resolve()==destination.resolve().anchor:
        raise ValueError("Never use a drive root")
    header=nds_header(rom)
    pf=json.loads(preflight.read_text(encoding="utf-8"))
    if pf.get("gate")!="HEADER_ONLY_PASS_MORE_GATES_REQUIRED" or pf.get("game_code_from_header")!=GAME_CODE:
        raise ValueError("042 preflight report does not approve ASMP")
    if sha256(rom)!=pf.get("sha256_original_rom"):
        raise ValueError("ROM differs from 042 preflight report")
    if rom.stat().st_size!=pf.get("game_bytes"):
        raise ValueError("ROM size differs from 042 report")
    version=verify_binaries(boot,module,manifest)
    rhash=ra_hash_ds(rom)
    session=make_session(GAME_PATH,rhash)
    verify_session(session,rhash)
    # Extra preflight: all safety checks must finish before touching disk.
    root=destination/"SD_ROOT"
    folder=root/PREFIX
    dsc=folder/"dscheevos"
    dsc.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(rom,folder/"mario_europe.nds")
    shutil.copyfile(boot,folder/"Bootstrap_043.nds")
    shutil.copyfile(module,dsc/"dscheevos9.bin")
    (dsc/"session.bin").write_bytes(session)
    # Experimental clean save; do not import or modify any of the owner's existing saves.
    (folder/"mario_test_only.sav").write_bytes(b"\xff"*(512*1024))
    (folder/"bootstrap.ini").write_text(
      "[NDS-BOOTSTRAP]\n"+
      "NDS_PATH = "+GAME_PATH+"\n"+
      "SAV_PATH = "+SAVE_PATH+"\n"+
      "LOGGING = 0\n"+
      "LOADING_SCREEN = 0\n"+
      "B4DS_MODE = 0\n"+
      "DSI_MODE = 0\n"+
      "BOOST_CPU = 0\n",encoding="ascii")
    report={
      "status":"STAGED_OFFLINE_043_FOR_SPARE_SD_ONLY",
      "game_code":"ASMP","region":"EUROPE","rom_bytes":rom.stat().st_size,
      "ra_ds_hash":rhash,"hash_algorithm":"pinned rcheevos Nintendo DS",
      "boot_sha256":version["bootstrap_sha256"],"module_sha256":version["module_sha256"],
      "network":False,"spectator":True,"real_ra_unlocks":False,
      "tested_physical":False,"target":"separate SD clone only, never production SD",
      "launch_path":"sd:/DSiRABridge_043/Bootstrap_043.nds",
      "expected_output":"In-game DScheevos local QA progress; no official awards",
      "limitations":["Requires compatible DSi launch rights","nds-bootstrap may write scratch _nds paths on TEST SD only",
                     "First test does not establish official RA hardware support"]}
    (destination/"STAGING_MANIFEST.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (destination/"LEIA_ANTES_DO_DSI.txt").write_text(
      "DSi RA Bridge 0.4.3 - ROTEIRO EXPERIMENTAL, SOMENTE CARTAO SD RESERVA\n"
      "SEM LOGIN, SEM REDE, SEM CONQUISTAS OFICIAIS.\n\n"
      "1. NUNCA copie para o cartao SD original em uso. Preserve uma copia de seguranca.\n"
      "2. Em outro cartao SD, clone localmente seu SD do Lenny/Flipnote/HBMenu.\n"
      "3. Nesse cartao TESTE, copie o conteudo de SD_ROOT para a raiz.\n"
      "4. Abra Flipnote Lenny > HBMenu > DSiRABridge_043/Bootstrap_043.nds.\n"
      "5. O jogo Mario EU deve abrir com saves temporarios em DSiRABridge_043.\n"
      "6. No jogo, a combinacao L + DOWN + SELECT do in-game menu pode exibir\n"
      "   a pagina DScheevos com QA: 300/900 frames. Isto nao e award RA.\n"
      "7. Desligue, extraia o SD TESTE e volte ao original para rollback.\n\n"
      "NAO use os binarios 042 DO_NOT_INSTALL. Nao substitua _nds da instalacao principal.\n"
      "Se houver tela branca ou falha na leitura, desligue e nao force gravacoes.\n"
      "O primeiro teste fisico ainda pode revelar restricoes do Flipnote Lenny.\n",
      encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--preflight",type=Path,required=True)
    p.add_argument("--bootstrap",type=Path,required=True)
    p.add_argument("--module",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True,help="NEW directory under user profile, NOT SD")
    a=p.parse_args()
    try:
        print(json.dumps(prepare(a.rom,a.preflight,a.bootstrap,a.module,a.manifest,a.out),
                         indent=2,ensure_ascii=False))
    except (OSError,ValueError,struct.error) as e:
        print(json.dumps({"status":"BLOCKED","reason":str(e)},ensure_ascii=False))
        raise SystemExit(1)
if __name__=="__main__":main()
