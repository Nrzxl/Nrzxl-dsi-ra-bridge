#!/usr/bin/env bash
# Compatibility entry point: Phase 2 supersedes the 010 build.
set -euo pipefail
case "$1" in /out/pass1) pass=first;; /out/pass2) pass=second;; *) exit 2;; esac
exec bash /src/scripts/build-arm-020.sh "$pass"
