#!/bin/bash
# scripts/linux/selfbuild.sh - the selfbuild.ps1 procedure on Linux.
# 1. regenerate the EMBED section (embed_gen.py, a port of embed-gen.ps1);
# 2. Windows, under Wine: the seed zc.exe builds gen1, gen1 builds gen2 and
#    gen2 builds gen3; gen2 and gen3 must be byte-identical. (selfbuild.ps1
#    compares seed output with gen1's, which only holds when the seed was
#    built from the current sources; the checked-in seed is older.)
# 3. Linux: the same fixpoint for the native ELF compiler.
# --install replaces zc.exe with the verified zc.new.exe.
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
export WINEDEBUG=-all
python3 scripts/linux/embed_gen.py
rm -f zc.gen1.exe zc.new.exe zc.chk.exe
echo "== Windows, under Wine: seed -> gen1 -> gen2 -> gen3 =="
wine ./zc.exe --rt compiler/zc.zeph zc.gen1.exe
wine ./zc.gen1.exe --rt compiler/zc.zeph zc.new.exe
wine ./zc.new.exe --rt compiler/zc.zeph zc.chk.exe
a=$(sha256sum zc.new.exe | cut -c1-64); b=$(sha256sum zc.chk.exe | cut -c1-64)
rm -f zc.chk.exe zc.gen1.exe
[ "$a" = "$b" ] || { echo "WINDOWS FIXPOINT FAILED"; rm -f zc.new.exe; exit 1; }
echo "windows fixpoint ok (${a:0:16})"
echo "== Linux fixpoint =="
tmp=$(mktemp -d); mkdir -p "$tmp/a" "$tmp/b"
ln -s "$ROOT/compiler" "$tmp/a/compiler"; ln -s "$ROOT/lib" "$tmp/a/lib"
ln -s "$ROOT/compiler" "$tmp/b/compiler"; ln -s "$ROOT/lib" "$tmp/b/lib"
wine ./zc.new.exe --linux --rt compiler/zc.zeph "$tmp/a/zc"; chmod +x "$tmp/a/zc"
"$tmp/a/zc" --linux --rt compiler/zc.zeph "$tmp/b/zc"; chmod +x "$tmp/b/zc"
"$tmp/b/zc" --linux --rt compiler/zc.zeph "$tmp/c"
a=$(sha256sum "$tmp/b/zc" | cut -c1-64); b=$(sha256sum "$tmp/c" | cut -c1-64)
[ "$a" = "$b" ] || { echo "LINUX FIXPOINT FAILED"; exit 1; }
echo "linux fixpoint ok (${a:0:16})"
cp "$tmp/b/zc" "${ZC_LINUX_OUT:-/tmp/zr/current-zc}"
rm -rf "$tmp"
if [ "$1" = "--install" ]; then mv -f zc.new.exe zc.exe; echo "installed zc.exe"; else rm -f zc.new.exe; fi
