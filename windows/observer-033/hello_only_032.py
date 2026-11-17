"""032 HELLO-only diagnostic. No DATA ACK, no engine and no RetroAchievements calls."""
import argparse,socket,struct,zlib,json,time,ipaddress
from pathlib import Path
def ack_hello(b):
    if len(b)!=96:raise ValueError("length")
    if b[:4]!=b"DSR2" or b[4]!=2 or b[5]!=2 or b[6] not in (1,2) or b[7] not in (0,2):raise ValueError("HELLO header")
    if zlib.crc32(b[:92])!=struct.unpack_from("<I",b,92)[0]:raise ValueError("CRC")
    lo,hi,seq,hz,target=struct.unpack_from("<5I",b,8)
    if not (lo or hi) or seq!=0 or not 1<=hz<=30 or not 1<=target<=6000:raise ValueError("HELLO limits")
    out=bytearray(96);out[:8]=b[:8];out[5]=3
    struct.pack_into("<5I",out,8,lo,hi,0,0,32);struct.pack_into("<I",out,92,zlib.crc32(out[:92]))
    return bytes(out),dict(sid="%08x%08x"%(hi,lo),source=b[6],mode=b[7]>>1,hz=hz,target=target,provenance="RUNTIME_UNVERIFIED")
def audit(path):
    raw=Path(path).read_bytes()
    if len(raw)>96 or raw.startswith(b"\xef\xbb\xbf"):raise ValueError("config length/BOM")
    items=raw.decode("ascii").split()
    if len(items)!=3:raise ValueError("expected IPv4 port Hz")
    ip,port,hz=items[0],int(items[1]),int(items[2]);addr=ipaddress.IPv4Address(ip)
    if not addr.is_private or addr.is_loopback or not 1024<=port<=65535 or not 1<=hz<=30:raise ValueError("config bounds")
    return dict(status="PASS",ip=ip,port=port,hz=hz,note="format only; compare with actual PC LAN address; no reachability claim")
def main():
    p=argparse.ArgumentParser();p.add_argument("--config");p.add_argument("--bind",default="0.0.0.0");p.add_argument("--port",type=int,default=18216);p.add_argument("--seconds",type=int,default=30);p.add_argument("--log",type=Path);a=p.parse_args()
    if a.config:print(json.dumps(audit(a.config)));return
    if not 1<=a.seconds<=120 or not 1024<=a.port<=65535:raise ValueError("bounds")
    if a.bind!="0.0.0.0" and not ipaddress.IPv4Address(a.bind).is_private:raise ValueError("LAN only")
    name=a.log or Path("hello-032-"+str(time.time_ns())+".jsonl")
    with name.open("x",encoding="utf-8") as log,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        def event(row):
            row.update(time=time.time(),diagnostic="HELLO_ONLY",submitted=False);line=json.dumps(row);print(line,flush=True);log.write(line+"\n");log.flush()
        sock.bind((a.bind,a.port));sock.settimeout(0.25);event(dict(type="ready",bind=a.bind,port=a.port,instruction="stop regular receiver; DSi press Y only, never A"))
        end=time.monotonic()+a.seconds;received=accepted=0
        while time.monotonic()<end:
            try:b,peer=sock.recvfrom(2048)
            except socket.timeout:continue
            received+=1
            try:out,meta=ack_hello(b)
            except ValueError as e:event(dict(type="ignored",reason=str(e),length=len(b)));continue
            accepted+=1;event(dict(type="hello_received",peer=peer,**meta))
            try:sent=sock.sendto(out,peer);event(dict(type="hello_ack_sent",bytes=sent))
            except OSError as e:event(dict(type="send_error",error=str(e)))
        event(dict(type="summary",datagrams=received,hellos=accepted,physical_roundtrip="NOT_VERIFIED",data_evaluated=0))
if __name__=="__main__":main()
