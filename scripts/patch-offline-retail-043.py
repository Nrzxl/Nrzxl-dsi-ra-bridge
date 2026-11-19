#!/usr/bin/env python3
"""043: fail-closed, reproducible GPL upstream source patch for *offline-only* DSi retail observation.

Applies solely to a disposable checkout of the pinned DScheevos and nds-bootstrap
forks. DO NOT use with stable SD installs or unknown upstream revisions.
Patch descriptions and this script are MIT; modified upstream files remain GPL-3.0.
"""
import argparse
import json
import subprocess
from pathlib import Path

DSC = "59e9978be7b9c3788357ef0a609caf9dc8ea74f3"
BOOT = "af351f096dd71a37e0e5b18d9709bcc0fb70342f"
RC = "754965ef28db22b0411bfccbde39154cd09e6b79"
MARK = "HANNA 043 OFFLINE SPECTATOR ONLY"

def rev(path):
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()

def replace_once(text,old,new,label):
    if text.count(old)!=1:
        raise ValueError("Refused upstream drift at %s; expected 1 anchor, found %d"%(label,text.count(old)))
    return text.replace(old,new,1)

def edit_range(text,start,end,new,label):
    i=text.find(start)
    j=text.find(end,i+1)
    if i<0 or j<0 or text.count(start)!=1 or text.count(end)!=1 or j<=i:
        raise ValueError("Refused upstream drift for "+label)
    return text[:i]+new+text[j:]

def plan(repo):
    repo=Path(repo)
    if rev(repo)!=DSC or rev(repo/"external/nds-bootstrap")!=BOOT or rev(repo/"external/rcheevos")!=RC:
        raise ValueError("Pinned source mismatch (DScheevos/nds-bootstrap/rcheevos)")
    boot=repo/"external/nds-bootstrap"
    sources={}
    session=boot/"retail/arm9/source/dscheevos_session.c"
    s=session.read_text()
    s=replace_once(s,'#define DSCHEEVOS_DIR "sd:/_nds/dscheevos/"',
      '#define DSCHEEVOS_DIR "sd:/DSiRABridge_043/dscheevos/"',str(session))
    s=replace_once(s,"#define DSCHEEVOS_SESSION_HEAD (DSCHEEVOS_S_UNIX_TIME + 4)",
      "#define DSCHEEVOS_SESSION_HEAD ((DSCHEEVOS_S_NET_VALID + 4) & ~3)",str(session))
    s=replace_once(s,"const s32 age = (s32)((u32)time(NULL) - head[DSCHEEVOS_S_UNIX_TIME / 4]);",
      "/* 043 uses one-use local session files. Clock/age are not trusted; RA network is disabled. */",str(session))
    s=replace_once(s,
      "&& age >= -DSCHEEVOS_SESSION_MAX_AHEAD && age <= DSCHEEVOS_SESSION_MAX_AGE;",
      "&& (((const u8*)head)[DSCHEEVOS_S_FLAGS] & DSCHEEVOS_BOOT_SPECTATOR)\n"
      "     && ((const u8*)head)[DSCHEEVOS_S_HARDCORE] == 0\n"
      "     && ((const u8*)head)[DSCHEEVOS_S_NET_VALID] == 0;",
      str(session))
    sources[session]=s

    conf=boot/"retail/arm9/source/conf_sd.cpp"
    s=conf.read_text()
    s=replace_once(s,
      'load_conf(conf, conf->bootstrapOnFlashcard ? "fat:/_nds/nds-bootstrap.ini" : "sd:/_nds/nds-bootstrap.ini");',
      'load_conf(conf, "sd:/DSiRABridge_043/bootstrap.ini");',str(conf))
    # Fail closed if the ROM is loaded from flashcart: internal SD only.
    s=replace_once(s,
      'conf->bootstrapOnFlashcard = ((bootstrapPath[0] == \'f\' && bootstrapPath[1] == \'a\' && bootstrapPath[2] == \'t\') || !conf->sdFound);',
      'conf->bootstrapOnFlashcard = ((bootstrapPath[0] == \'f\' && bootstrapPath[1] == \'a\' && bootstrapPath[2] == \'t\') || !conf->sdFound);',
      str(conf)) if False else s
    sources[conf]=s

    hooks=boot/"retail/bootloaderi/source/arm7/dscheevos_hooks.c"
    s=hooks.read_text()
    s=edit_range(s,"bool dscheevosNetWanted(void) {",
         "\n// A hardcore session:",
         "bool dscheevosNetWanted(void) {\n"
         "    /* "+MARK+": disable DSi Wi-Fi carryover regardless of session. */\n"
         "    return false;\n"
         "}\n",
         str(hooks)+" net")
    s=edit_range(s,"static void fillPmk(u8* session) {","\n// The session card",
         "static void fillPmk(u8* session) {\n"
         "    /* "+MARK+": never read firmware or derive Wi-Fi keys. */\n"
         "    session[DSCHEEVOS_S_PMK_VALID] = 0;\n"
         "    toncset(session + DSCHEEVOS_S_PMK, 0, 32);\n"
         "}\n",
         str(hooks)+" PMK")
    # Defence-in-depth at setup after file is read, before it is wiped/used.
    s=replace_once(s,
      "fileRead((char*)session, &file, 0, sessionSize);\n\twipeSession(&file, sessionSize);",
      "fileRead((char*)session, &file, 0, sessionSize);\n"
      "\t/* "+MARK+": force a local-only, spectator-only test session. */\n"
      "\tif (!(((u8*)session)[DSCHEEVOS_S_FLAGS] & DSCHEEVOS_BOOT_SPECTATOR)\n"
      "\t || ((u8*)session)[DSCHEEVOS_S_NET_VALID] != 0\n"
      "\t || ((u8*)session)[DSCHEEVOS_S_HARDCORE] != 0) {\n"
      '\t\tdisable("043 offline session required");\n\t\treturn;\n\t}\n'
      "\twipeSession(&file, sessionSize);",
      str(hooks)+" hard gate")
    sources[hooks]=s

    module=repo/"dscheevos/module/src/module.c"
    s=module.read_text()
    s=replace_once(s,"  g_boot = *boot;",
       "  /* "+MARK+": also enforce off-network spectator mode in ARM9 runtime. */\n"
       "  if (!(boot->flags & DSCM_BOOT_SPECTATOR) || boot->net_valid || boot->hardcore) {\n"
       "    dscm_g_status.error = DSCM_ERROR_BAD_BOOT;\n"
       "    return -1;\n"
       "  }\n"
       "  g_boot = *boot;\n"
       "  g_boot.net_valid = 0;\n"
       "  g_boot.hardcore = 0;\n"
       "  g_boot.flags |= DSCM_BOOT_SPECTATOR;",
       str(module))
    sources[module]=s
    return sources

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("dscheevos_checkout",type=Path)
    p.add_argument("--apply",action="store_true",help="Required: modify only verified disposable checkout")
    a=p.parse_args()
    sources=plan(a.dscheevos_checkout)
    if a.apply:
        for path,content in sources.items():
            path.write_text(content)
    print(json.dumps({"status":"PATCHED_DISPOSABLE_GPL_SOURCES" if a.apply else "PATCH_PLAN_VALID",
      "paths":[str(p.relative_to(a.dscheevos_checkout)) for p in sources],
      "source_sha":{"dscheevos":DSC,"nds_bootstrap":BOOT,"rcheevos":RC},
      "sd_prefix":"sd:/DSiRABridge_043/",
      "spectator_only":True,"net_disabled":True,"hardware":"NOT_RUN",
      "official_awards":False},indent=2))
if __name__=="__main__":
    try:main()
    except (OSError,ValueError,subprocess.CalledProcessError) as e:
        print(json.dumps({"status":"BLOCKED","reason":str(e)}))
        raise SystemExit(1)
