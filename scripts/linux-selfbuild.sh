#!/bin/sh
# linux-selfbuild.sh — rebuild the Zephyr compiler natively on Linux (no wine).
#
# Requires an existing zc-linux (bootstrap it once with:
#   wine zc.exe --linux --rt compiler/zc.zeph zc-linux && chmod +x zc-linux)
# After that, this script keeps the compiler at its self-build fixpoint:
# generation N and N+1 must be byte-identical.
#
# The compiler builds itself with -O2: about 50 s a generation instead of 2,
# for a compiler that runs 2-3x faster. OPT= (empty) builds it unoptimized.
set -e
opt="${OPT--O2}"
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [ ! -x ./zc-linux ]; then
    echo "no ./zc-linux — bootstrap once with wine:" >&2
    echo "  wine zc.exe --linux --rt compiler/zc.zeph zc-linux && chmod +x zc-linux" >&2
    exit 1
fi

echo "== Zephyr compiles Zephyr (native Linux): zc-linux -> zc.new =="
./zc-linux $opt --linux --rt compiler/zc.zeph zc.new
chmod +x zc.new

echo "== generation 2 =="
./zc.new $opt --linux --rt compiler/zc.zeph zc.chk
chmod +x zc.chk

echo "== generation 3 =="
./zc.chk $opt --linux --rt compiler/zc.zeph zc.third
chmod +x zc.third

if cmp -s zc.chk zc.third; then
    mv zc.chk zc-linux
    rm -f zc.new zc.third
    echo "updated ./zc-linux — generations 2 and 3 are byte-identical"
else
    echo "FIXPOINT FAILED — compiler is not self-consistent" >&2
    rm -f zc.new zc.chk zc.third
    exit 1
fi
./zc-linux --version
