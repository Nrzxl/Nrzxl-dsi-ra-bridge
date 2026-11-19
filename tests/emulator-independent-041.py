"""Full DS/NTR emulation with free BIOS; not a physical DSi test."""
import argparse,subprocess,json,importlib.util,shutil,hashlib,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("decode",ROOT/"windows/observer-033/decode.py");d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
p=argparse.ArgumentParser();p.add_argument("--emulator",type=Path,required=True);p.add_argument("--build",type=Path,required=True);p.add_argument("--sd",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--engine",type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
a.sd.mkdir(parents=True,exist_ok=False);(a.sd/"DSiRABridge_041").mkdir()
shutil.copyfile(a.build/"instrumented/Fixture_B_041_observed.nds",a.sd/"DSiRABridge_041/Fixture_B_041_observed.nds")
script=a.output/"input.txt";script.write_text("600 1 10\n900 2 10\n")
manifest=json.loads((a.build/"instrumented/instrumentation.json").read_text())
summary={"provenance":"NDS_EMULATOR","emulator":"skierrz/melonDS@8a63c88333c8cb4efed76d866872fc3b6ed0de96","mode":"DS/NTR FreeBIOS","hardware":"NOT_RUN","tests":[]}
for name,rom,extra in [
    ("control",a.build/"DSiRABridge_Fixture_B_041.nds",[]),
    ("observed",a.build/"instrumented/Fixture_B_041_observed.nds",[]),
    ("chainload",a.build/"DSiRABridge_Launcher_A_041_EMU_ONLY.nds",["--sd",str(a.sd),"--arg","fat:/DSiRABridge_041/Launcher_A_EMU_ONLY.nds"])]:
    dump=a.output/(name+".ram");shot=a.output/(name+".ppm")
    cmd=[str(a.emulator.resolve()),"--rom",str(rom.resolve()),"--mode","ds","--frames","2400","--until","FIXTURE_B_DONE","--script",str(script),"--dump-ram",str(dump),"--screenshot",str(shot)]+extra
    begin=time.monotonic();r=subprocess.run(cmd,text=True,capture_output=True,timeout=180)
    log=r.stdout+r.stderr;(a.output/(name+".log")).write_text(log)
    print(name,log[-4500:],flush=True)
    if r.returncode or "FIXTURE_B_MAIN" not in log or "FIXTURE_B_DONE" not in log:raise RuntimeError(name+" did not boot/finish: "+str(r.returncode))
    if name=="chainload" and "A_CHAINLOAD_ACCEPTED" not in log:raise RuntimeError("missing full chainload")
    raw=dump.read_bytes();offset=manifest["watch_address"]-0x02000000
    generation,counter,buttons,checksum,tag=struct.unpack_from("<5I",raw,offset)
    if counter<1800 or generation!=counter*2 or checksum!=counter^buttons^0x9317A55A or tag!=0x47414D33:raise RuntimeError("B state corrupt")
    # Log-free host elapsed time is not a console CPU benchmark.
    result=dict(name=name,status="PASS",b_counter=counter,emulator_host_seconds=time.monotonic()-begin)
    if name=="control":
        control_counter=counter
    if name=="observed" and counter!=control_counter:raise RuntimeError("fixture counter diverged from uninstrumented control at equal video-frame budget")
    if name=="control":
        if raw[0x200000:0x200008]==b"DSIOBS33":raise RuntimeError("control unexpectedly has monitor")
        result["observer_present"]=False
    else:
        evidence=d.decode(raw,"NDS_EMULATOR");d.evaluate(evidence,a.engine)
        if not any(x["buttons"]&1 for x in evidence["records"]) or not any(x["buttons"]&2 for x in evidence["records"]):raise RuntimeError("independent input not observed")
        (a.output/(name+".json")).write_text(json.dumps(evidence,indent=2)+"\n")
        result.update({k:v for k,v in evidence.items() if k!="records"})
    summary["tests"].append(result)
for name in ["DSiRABridge_Fixture_B_041.nds","instrumented/Fixture_B_041_observed.nds"]:
    r=subprocess.run([str(a.engine.resolve().with_name("dsirb_nds_hash")),str((a.build/name).resolve())],capture_output=True,text=True,check=True)
    summary.setdefault("official_ds_hashes",{})[name]=json.loads(r.stdout)
if len({x["hash"] for x in summary["official_ds_hashes"].values()})!=2:raise RuntimeError("modified fixture unexpectedly has original game hash")
summary["status"]="PASS";(a.output/"validation.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary))
