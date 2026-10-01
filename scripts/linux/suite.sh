#!/bin/bash
# scripts/linux/suite.sh - run the Windows PowerShell test suites on Linux.
# Builds a native Linux zc from the current compiler/ sources, copies the
# checkout to a scratch tree whose zc.exe is a wrapper around that compiler
# (targeting --linux), and runs each suite with Linux PowerShell plus a `cmd`
# stand-in. Tests that need Windows itself (kernel32 calls, .exe semantics)
# fail here by construction; compare against a baseline run. Suites get
# /dev/null as stdin: some fixtures (basics/cube.zeph) run until input ends.
# Usage: scripts/linux/suite.sh OUTDIR [suite.ps1 ...]
#   needs: pwsh on PATH or at /opt/pwsh/pwsh, and a Linux zc seed at $ZC_SEED
#   (default /tmp/zr/current-zc, left by scripts/linux/selfbuild.sh)
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:?usage: suite.sh OUTDIR [suites]}; shift
SUITES=${*:-run_tests.ps1 std_tests.ps1 optimizer_parity.ps1 run_parity.ps1}
PWSH=$(command -v pwsh || echo /opt/pwsh/pwsh)
SEED=${ZC_SEED:-/tmp/zr/current-zc}
TREE=$OUT/tree
rm -rf "$TREE" && mkdir -p "$TREE" "$OUT"
(cd "$ROOT" && tar --exclude=.git -cf - .) | tar -xf - -C "$TREE"
# a native compiler from the current sources, beside compiler/ and lib/
(cd "$TREE" && "$SEED" --linux --rt compiler/zc.zeph zc-linux-bin)
chmod +x "$TREE/zc-linux-bin"
cat > "$TREE/zc.exe" <<'WRAP'
#!/bin/bash
# zc.exe stand-in: backslashes to slashes, --linux unless a target is given,
# space-free aliases for paths with spaces (the Linux zc splits arguments on
# spaces), and the output made executable.
here=$(cd "$(dirname "$0")" && pwd)
alias_dir=$(mktemp -d)
args=(); target=--linux; out=""; moveback=""
n=0
for a in "$@"; do n=$((n+1)); done
i=0
for a in "$@"; do
  i=$((i+1))
  a=${a//\\//}
  case $a in --wasm|--linux) target="";; esac
  if [[ $a == *" "* ]]; then
    alias="$alias_dir/a$i.${a##*.}"
    if [ -e "$a" ]; then ln -s "$a" "$alias"; else moveback="$a"; fi
    [ $i -eq $n ] && out="$a"
    args+=("$alias")
  else
    [ $i -eq $n ] && out="$a"
    args+=("$a")
  fi
done
"$here/zc-linux-bin" $target "${args[@]}"
code=$?
if [ -n "$moveback" ] && [ -e "${args[$((n-1))]}" ]; then mv "${args[$((n-1))]}" "$moveback"; fi
[ -n "$out" ] && [ -f "$out" ] && chmod +x "$out"
rm -rf "$alias_dir"
exit $code
WRAP
chmod +x "$TREE/zc.exe"
cat > "$TREE/linux-preamble.ps1" <<'PRE'
$env:TEMP = [System.IO.Path]::GetTempPath()
function global:cmd {
    $line = ($args[1..($args.Count - 1)] -join ' ') -replace '\\', '/'
    & bash -c $line
}
PRE
for s in $SUITES; do
  (cd "$TREE" && "$PWSH" -NoLogo -NoProfile -Command '. ./linux-preamble.ps1; & ./tests/'"$s"'; exit $LASTEXITCODE' < /dev/null > "$OUT/${s%.ps1}.log" 2>&1) || true
  pass=$(grep -c '^PASS' "$OUT/${s%.ps1}.log" || true); fail=$(grep -c '^FAIL' "$OUT/${s%.ps1}.log" || true)
  echo "$s: $pass pass, $fail fail; last line: $(tail -1 "$OUT/${s%.ps1}.log")"
done
