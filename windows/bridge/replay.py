"""Independent stdlib replay. Diagnostic only; never contacts RetroAchievements."""
import argparse
import json
import struct
import zlib
from pathlib import Path

def decode(packet):
    if len(packet) != 64:
        raise ValueError("length")
    if packet[:4] != b"DSRB" or packet[4] != 1:
        raise ValueError("magic/version")
    if packet[5] not in (1, 2) or packet[6] > 1 or packet[7] != 1:
        raise ValueError("source/mode/flags")
    if struct.unpack_from("<HHHHI", packet, 28) != (44, 4, 16, 0, 0xD1A60001):
        raise ValueError("layout")
    if zlib.crc32(packet[:60]) != struct.unpack_from("<I", packet, 60)[0]:
        raise ValueError("crc")
    words = struct.unpack_from("<IIII", packet, 44)
    if words[0] != 0x44534931 or words[2] > 0x3FFF or words[3] != (words[1] ^ words[2] ^ 0xA5A55A5A):
        raise ValueError("controlled value")
    return dict(provenance="CONTROLLED_RUNTIME_UNVERIFIED" if packet[5] == 1 else "SIMULATED",
                officialEligible=False, mode=packet[6],
                session=struct.unpack_from("<I", packet, 8)[0],
                seq=struct.unpack_from("<I", packet, 12)[0],
                frame=struct.unpack_from("<I", packet, 16)[0],
                readTicks=struct.unpack_from("<I", packet, 20)[0],
                words=words, latencyMs=None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    size = args.file.stat().st_size
    if not size or size % 64 or size > 64 * 60000:
        raise SystemExit("Invalid/truncated capture size")
    with args.file.open("rb") as stream:
        while packet := stream.read(64):
            print(json.dumps(decode(packet)))
