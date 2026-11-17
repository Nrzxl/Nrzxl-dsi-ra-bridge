#!/usr/bin/env bash
# Runs inside an official preinstalled devkitPro image, network disabled.
set -euo pipefail
case "$1" in first|second) build_name="$1";; *) exit 2;; esac
dest="/out/$build_name"
mkdir -p "$dest"
cp -R /src/dsi/diagnostics/. /work/
export SOURCE_DATE_EPOCH=1794862800
export TZ=UTC LC_ALL=C
if command -v dkp-pacman >/dev/null; then pkg=dkp-pacman
elif command -v pacman >/dev/null; then pkg=pacman
else echo "BLOCKED: package inventory unavailable"; exit 3; fi
{
  arm-none-eabi-gcc --version
  ndstool 2>&1 || true
  "$pkg" -Q
  sha256sum "$DEVKITARM/ds_rules"
} > "$dest/toolchain.txt"
"$pkg" -Q libnds | grep -E '^libnds 1\.8\.' >/dev/null || {
  echo "BLOCKED: this source targets classic libnds 1.8.x; do not silently mix Calico APIs"; exit 3;
}
make -C /work all
name=DSiRABridge_Diagnostic_020
test -s "/work/$name.nds"
test -s "/work/$name.elf"
cp "/work/$name.nds" "/work/$name.elf" "$dest/"
if test -f "/work/build/$name.map"; then cp "/work/build/$name.map" "$dest/"; fi
if test -f "/work/build/$name.lst"; then cp "/work/build/$name.lst" "$dest/"; fi
arm-none-eabi-readelf -h "/work/$name.elf" > "$dest/elf-header.txt"
arm-none-eabi-size "/work/$name.elf" > "$dest/elf-size.txt"
# Collect licenses actually present in the selected SDK for review/distribution.
mkdir -p "$dest/licenses"
find "$DEVKITPRO" -maxdepth 5 -type f \( -iname '*license*' -o -iname 'COPYING*' \) -print0 |
while IFS= read -r -d '' license_path; do
  relative_path="$(printf '%s' "$license_path" | sed "s|^$DEVKITPRO/||")"
  mkdir -p "$dest/licenses/$(dirname "$relative_path")"
  cp "$license_path" "$dest/licenses/$relative_path"
done
