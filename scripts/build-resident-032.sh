#!/usr/bin/env bash
set -euo pipefail
export DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM
export PATH="$DEVKITARM/bin:$DEVKITPRO/tools/bin:$PATH"
case "$1" in first|second) pass="$1";; *) exit 2;; esac
dest="/out/resident-$pass";mkdir -p "$dest"
cp -R /src/dsi/resident-032/. /work/
export SOURCE_DATE_EPOCH=1794920000 TZ=UTC LC_ALL=C
arm-none-eabi-gcc -std=gnu11 -Os -march=armv5te -mtune=arm946e-s -marm -fPIC \
 -ffreestanding -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables -c payload.c -o payload.o
arm-none-eabi-gcc -march=armv5te -marm -nostdlib -Wl,-T,payload.ld,-Map,payload.map,--no-undefined \
 payload.o -o payload.elf
arm-none-eabi-objcopy -O binary -j .text payload.elf payload.bin
arm-none-eabi-readelf -r payload.elf | tee "$dest/payload-relocations.txt"
grep -q 'There are no relocations' "$dest/payload-relocations.txt"
arm-none-eabi-objdump -d payload.elf > "$dest/payload-disassembly.txt"
cp payload.bin payload.elf payload.map "$dest/"
make all
cp DSiRABridge_Resident_032.nds DSiRABridge_Resident_032.elf "$dest/"
arm-none-eabi-size DSiRABridge_Resident_032.elf > "$dest/elf-size.txt"
