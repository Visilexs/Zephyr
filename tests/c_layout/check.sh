#!/bin/sh
# check.sh ZC -- @C struct layouts against gcc: layout.zeph (baseline and -O2)
# must print exactly what layout.c prints. Run by tests/linux/run.sh when gcc
# exists.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
zc="${1:-$here/../../zc-linux}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
gcc -O0 -o "$work/layout-c" "$here/layout.c"
"$work/layout-c" >"$work/c.out"
for opt in "" -O2; do
    timeout 300 "$zc" $opt --linux --rt "$here/layout.zeph" "$work/layout-z" </dev/null
    chmod +x "$work/layout-z"
    timeout 60 "$work/layout-z" </dev/null >"$work/z.out"
    if ! diff -u "$work/c.out" "$work/z.out"; then
        echo "FAIL @C layout differs from gcc ($opt)"
        exit 1
    fi
done
echo "ok   @C layouts match gcc"
