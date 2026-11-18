#!/usr/bin/env bash
# 034-B isolated ARM build; depends on pinned devkitPro container from Actions.
set -euo pipefail
export DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM
export PATH="$DEVKITARM/bin:$DEVKITPRO/tools/bin:$PATH"
export SOURCE_DATE_EPOCH=1794933000 TZ=UTC LC_ALL=C
pass="$1"
case "$pass" in first|second);; *) echo "invalid pass" >&2; exit 2;; esac
dest="/out/scout-$pass"
mkdir -p "$dest"
cp -R /src/dsi/scout-034b /work/scout
make -C /work/scout all
cp /work/scout/DSIRB_Scout_034B.nds /work/scout/DSIRB_Scout_034B.elf "$dest/"
arm-none-eabi-nm -n /work/scout/DSIRB_Scout_034B.elf > "$dest/symbols.txt"
arm-none-eabi-objdump -h /work/scout/DSIRB_Scout_034B.elf > "$dest/sections.txt"
arm-none-eabi-size /work/scout/DSIRB_Scout_034B.elf > "$dest/size.txt"
sha256sum "$dest/DSIRB_Scout_034B.nds" > "$dest/nds-sha256.txt"
