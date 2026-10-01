#!/bin/sh
# Build a Linux-native zc from the checked-in zc.exe (needs Wine), for research measurements.
# Result: /tmp/zr/root/zc, beside symlinks to compiler/ and lib/ (zc resolves them next to itself).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
command -v wine >/dev/null || (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq wine64 time hyperfine)
mkdir -p /tmp/zr/root
ln -sfn "$ROOT/compiler" /tmp/zr/root/compiler
ln -sfn "$ROOT/lib" /tmp/zr/root/lib
cd "$ROOT"
WINEDEBUG=-all wine zc.exe --linux --rt compiler/zc.zeph /tmp/zr/root/zc
chmod +x /tmp/zr/root/zc
/tmp/zr/root/zc --version
