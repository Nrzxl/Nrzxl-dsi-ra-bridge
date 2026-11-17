import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("directory",type=Path);a=p.parse_args()
target=a.directory/"generated";target.mkdir(exist_ok=False)
data=(a.directory/"load.bin").read_bytes()
(target/"load_bin.h").write_text("#include <stdint.h>\nextern const uint8_t load_bin[];\nextern const uint32_t load_bin_size;\n")
(target/"load_bin.c").write_text('#include "load_bin.h"\nconst uint8_t load_bin[] __attribute__((aligned(4)))={'+",".join(map(str,data))+"};\nconst uint32_t load_bin_size="+str(len(data))+";\n")
