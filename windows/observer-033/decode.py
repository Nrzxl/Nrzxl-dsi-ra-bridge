"""MIT. Offline observer decoder. Never connects to RetroAchievements.
A 4 MiB emulator dump and a 0xD000 hardware export have distinct provenance."""
import argparse,json,struct,zlib,subprocess
from pathlib import Path
BASE=0x02200000
def decode(raw,provenance):
    if provenance not in ("NDS_EMULATOR","HARDWARE_EXPORT","SYNTHETIC_TEST"):raise ValueError("explicit provenance required")
    if len(raw)==0x400000:
        if provenance=="HARDWARE_EXPORT":raise ValueError("hardware requires bounded export, not general RAM")
        window=raw[0x200000:0x220000]
    elif len(raw)==0xD000:window=raw
    else:raise ValueError("bounded export or exact DS RAM required")
    if window[:8]!=b"DSIOBS33":raise ValueError("observer not loaded")
    h=struct.unpack_from("<14I",window,8)
    if h[:3]!=(1,64,20) or h[6:10]!=(0x02203000,32,1200,0x02202000):raise ValueError("layout")
    if not 0x02000000<=h[3]<=0x02100000-20 or h[3]&3:raise ValueError("watch address")
    calls,invalid,stored,maxlines,last,first,minsp,guard,bad=struct.unpack_from("<9I",window,0x2000)
    if stored!=1200 or calls<1800 or invalid or guard or bad:raise ValueError("incomplete/invalid observation: "+str((calls,invalid,stored,guard,bad)))
    if not 0x0221C000<minsp<=0x02220000:raise ValueError("stack bounds")
    records=[]
    for i in range(stored):
        offset=0x3000+i*32;r=struct.unpack_from("<8I",window,offset)
        if zlib.crc32(window[offset:offset+28])!=r[7]:raise ValueError("record CRC "+str(i))
        frame,generation,counter,buttons,checksum,lines,valid,_=r
        if frame!=i or counter!=first+i or generation!=counter*2 or not valid or checksum!=(counter^buttons^0x9317A55A):raise ValueError("order/state "+str(i))
        records.append(dict(frame=frame,counter=counter,buttons=buttons,read_scanlines=lines))
    if last<records[-1]["counter"]+600:raise ValueError("observer did not continue after recording ring filled")
    return dict(status="PASS",provenance=provenance,scope="fixture-specific external ARM9 VBlank interposer; independent full NDS",
        frames_observed=calls,stored=stored,first_counter=first,last_counter=last,
        records_crc="PASS",invalid=invalid,private_stack_used_at_least=0x02220000-minsp,
        private_stack_capacity=16384,stack_guard="PASS",resident_reserved_bytes=0x20000,
        coarse_read_span_max_scanlines=maxlines,full_hook_cpu_time="NOT_MEASURED",
        submitted=False,records=records)
def evaluate(result,engine):
    trace="".join("33 %u %u\n"%(r["frame"],r["counter"]) for r in result["records"])
    p=subprocess.run([str(Path(engine).resolve())],input=trace,text=True,capture_output=True,check=True,timeout=30)
    events=[json.loads(x) for x in p.stdout.splitlines()]
    triggers=[x for x in events if x.get("event")=="LOCAL_TEST_TRIGGER"]
    if [x["id"] for x in triggers]!=[1,2] or any(x.get("submitted") is not False for x in events):raise ValueError("local engine evidence")
    result["rcheevos"]=dict(status="PASS",mode="LOCAL_TEST_ONLY",triggers=triggers,progress_frames=len([x for x in events if x.get("event")=="LOCAL_TEST_PROGRESS"]),official_awards=0)
def main():
    p=argparse.ArgumentParser();p.add_argument("capture",type=Path);p.add_argument("--provenance",required=True,choices=["NDS_EMULATOR","HARDWARE_EXPORT","SYNTHETIC_TEST"]);p.add_argument("--engine");p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=decode(a.capture.read_bytes(),a.provenance)
    if a.engine:evaluate(r,a.engine)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    summary={k:v for k,v in r.items() if k!="records"};print(json.dumps(summary))
if __name__=="__main__":main()
