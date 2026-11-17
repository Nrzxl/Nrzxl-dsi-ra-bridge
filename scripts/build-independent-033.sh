#!/usr/bin/env bash
# Inspected source and immutable SDK. No network in this container.
set -euo pipefail
export DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM
export PATH="$DEVKITARM/bin:$DEVKITPRO/tools/bin:$PATH"
pass="$1";phase="$2"
case "$pass" in first|second);; *) exit 2;; esac
dest="/out/independent-$pass";mkdir -p "$dest"
export SOURCE_DATE_EPOCH=1794933000 TZ=UTC LC_ALL=C
if test "$phase" = parts; then
 cp -R /src/dsi/fixture-033 /work/fixture
 cp -R /src/dsi/observer-033 /work/observer
 cp -R /src/third_party/nds-bootloader /work/loader
 make -C /work/fixture all
 cp /work/fixture/DSiRABridge_Fixture_B_033.nds /work/fixture/DSiRABridge_Fixture_B_033.elf "$dest/"
 arm-none-eabi-nm -n /work/fixture/DSiRABridge_Fixture_B_033.elf > "$dest/fixture-symbols.txt"
 arm-none-eabi-size /work/fixture/DSiRABridge_Fixture_B_033.elf > "$dest/fixture-size.txt"
 arm-none-eabi-gcc -std=gnu11 -O2 -march=armv5te -mtune=arm946e-s -marm -ffreestanding \
  -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables -I/work/observer \
  -c /work/observer/observer.c -o /work/observer/observer.o
 arm-none-eabi-gcc -march=armv5te -marm -c /work/observer/entry.s -o /work/observer/entry.o
 arm-none-eabi-gcc -march=armv5te -marm -nostdlib -Wl,-T,/work/observer/observer.ld,-Map,/work/observer/observer.map,--no-undefined \
  /work/observer/entry.o /work/observer/observer.o -o /work/observer/observer.elf
 arm-none-eabi-objcopy -O binary /work/observer/observer.elf "$dest/observer.bin"
 arm-none-eabi-nm -n /work/observer/observer.elf > "$dest/observer-symbols.txt"
 arm-none-eabi-objdump -d /work/observer/observer.elf > "$dest/observer-disassembly.txt"
 cp /work/observer/observer.elf /work/observer/observer.map "$dest/"
 # SD-only lab: remove the upstream volatile NAND AES-keyslot repair.
 # No NAND device is opened or written by this loader.
 python3 -c 'from pathlib import Path;p=Path("/work/loader/source/boot.c");s=p.read_text();a=s.index("\t// Repair AES keyslot used by NAND encryption");b=s.index("\n}",a);p.write_text(s[:a]+"\t/* SD-only lab: NAND crypto register repair intentionally omitted. */\n"+s[b:])'
 make -C /work/loader
 cp /work/loader/load.bin "$dest/load.bin"
 cp -R /work/loader/source "$dest/loader-source"
 cp /work/loader/Makefile /work/loader/load.ld "$dest/"
 { arm-none-eabi-gcc --version; dkp-pacman -Q; } > "$dest/toolchain.txt"
 mkdir -p "$dest/licenses"
 find "$DEVKITPRO" -maxdepth 5 -type f \( -iname '*license*' -o -iname 'COPYING*' \) -print0 |
 while IFS= read -r -d '' file; do
  relative="$(printf '%s' "$file" | sed "s|^$DEVKITPRO/||")"
  mkdir -p "$dest/licenses/$(dirname "$relative")";cp "$file" "$dest/licenses/$relative"
 done
elif test "$phase" = launchers; then
 cp -R /src/dsi/launcher-033-gpl /work/launcher
 cp "$dest/instrumented/expected.h" "$dest/generated/load_bin.h" "$dest/generated/load_bin.c" /work/launcher/source/
 make -C /work/launcher all
 cp /work/launcher/DSiRABridge_Launcher_A_033.nds /work/launcher/DSiRABridge_Launcher_A_033.elf "$dest/"
 make -C /work/launcher clean
 make -C /work/launcher TARGET=DSiRABridge_Launcher_A_033_EMU_ONLY LAB_CFLAGS=-DRESIDENT_EMU_LAB=1
 cp /work/launcher/DSiRABridge_Launcher_A_033_EMU_ONLY.nds "$dest/"
else exit 2;fi
