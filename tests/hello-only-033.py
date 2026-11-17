import importlib.util,unittest,struct,zlib,subprocess,socket,tempfile,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location("h",ROOT/"windows/observer-033/hello_only_032.py");h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def packet():
    b=bytearray(96);b[:8]=b"DSR2\x02\x02\x01\x02";struct.pack_into("<5I",b,8,1,2,0,10,6000);struct.pack_into("<I",b,92,zlib.crc32(b[:92]));return b
class Tests(unittest.TestCase):
    def test_ack(self):
        b,_=h.ack_hello(packet());self.assertEqual(b[5],3);self.assertEqual(struct.unpack_from("<3I",b,16),(0,0,32));self.assertEqual(struct.unpack_from("<I",b,92)[0],zlib.crc32(b[:92]))
    def test_bad_crc(self):
        b=packet();b[90]^=1
        with self.assertRaises(ValueError):h.ack_hello(b)
    def test_data_no_ack(self):
        b=packet();b[5]=1;struct.pack_into("<I",b,92,zlib.crc32(b[:92]))
        with self.assertRaises(ValueError):h.ack_hello(b)
    def test_loopback_process(self):
        with tempfile.TemporaryDirectory() as d,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as reservation:
            reservation.bind(("127.0.0.1",0));port=reservation.getsockname()[1];reservation.close()
            p=subprocess.Popen([sys.executable,str(ROOT/"windows/observer-033/hello_only_032.py"),"--bind","127.0.0.1","--port",str(port),"--seconds","2","--log",str(Path(d)/"hello.jsonl")],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                row=json.loads(p.stdout.readline());self.assertEqual(row["type"],"ready")
                with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
                    client.settimeout(2);client.sendto(packet(),("127.0.0.1",port));b,_=client.recvfrom(2048);self.assertEqual(b[5],3)
                out,err=p.communicate(timeout=6);self.assertEqual(p.returncode,0,err);self.assertIn('"data_evaluated": 0',out)
            finally:
                if p.poll() is None:p.kill();p.wait()
if __name__=="__main__":unittest.main()
