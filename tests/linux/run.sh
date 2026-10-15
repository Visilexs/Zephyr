#!/usr/bin/env bash
# tests/linux/run.sh -- the Linux test harness.
#
# Builds every self-checking test at baseline and -O2 with zc-linux, runs it
# with a timeout, and checks the exit code, the .expected file next to the
# source (when one exists) and that both tiers print the same thing. Also runs
# the leak checks (tests/leaks), the python checks that work on Linux,
# tests/linux_extern.sh (when gcc is available) and tests/linux/diagnostics.sh
# (compile errors, CLI, zc run, the --test runner, runtime panic messages).
#
# The compiler, runtime and lib/ are copied into a temp dir first, so the
# repository stays clean.
#
#   tests/linux/run.sh [-k PATTERN] [-j N] [-v]
#     -k PATTERN  only run units whose name matches PATTERN (grep -E)
#     -j N        run N tests in parallel (default: nproc)
#     -v          print the output of failing units
#   ZC=path/to/zc-linux overrides the compiler (default: <repo>/zc-linux).
#
# Every unit prints PASS, FAIL, XFAIL (a known failure, listed in KNOWN_FAIL
# with the audit item it maps to) or XPASS (a known failure that now passes:
# remove it from KNOWN_FAIL). Exit status is nonzero on any FAIL or XPASS.
set -u
root="$(cd "$(dirname "$0")/../.." && pwd)"
pattern=""
jobs="$(nproc 2>/dev/null || echo 4)"
verbose=0
while getopts "k:j:v" option; do
    case "$option" in
        k) pattern="$OPTARG" ;;
        j) jobs="$OPTARG" ;;
        v) verbose=1 ;;
        *) echo "usage: $0 [-k PATTERN] [-j N] [-v]" >&2; exit 2 ;;
    esac
done
zc="${ZC:-$root/zc-linux}"
[ -x "$zc" ] || { echo "no compiler at $zc (copy zc-linux into the repo root or set ZC)" >&2; exit 2; }

# Known failures: unit name -> audit item (docs/audit-2026-10-15.txt). A unit
# is "<test>:base", "<test>:O2", "<test>:parity" or "py:<check>". Remove an
# entry when its bug is fixed; the harness reports XPASS until you do.
declare -A KNOWN_FAIL=(
    [macos_loops:base]="codegen: tryReduce weighted-reduction fast path runs on maps"
    [macos_loops:O2]="codegen: tryReduce weighted-reduction fast path runs on maps"
    [leaks/replace:base]="rc/runtime: runtimeStringReplace leaks intermediate strings"
    [leaks/replace:O2]="rc/runtime: runtimeStringReplace leaks intermediate strings"
    [leaks/padleft:O2]="rc: -O2 inliner takeOwnership leaks owned temporary argument"
    [leaks/readfile:base]="runtime: readFile/writeFile/args leak temporaries"
    [leaks/readfile:O2]="runtime: readFile/writeFile/args leak temporaries"
    [leaks/args:base]="runtime: readFile/writeFile/args leak temporaries"
    [leaks/args:O2]="runtime: readFile/writeFile/args leak temporaries"
    [py:argument_tests]="frontend: Linux args() splits on spaces, drops empty args, truncates at 4 KB"
)
# Tests that are expected to exit nonzero (an intentional panic).
declare -A EXPECT_EXIT=(
    [fill_loops]=1
)
# Tests whose two tiers may legitimately print different things.
no_parity() { case "$1" in leaks/*) return 0 ;; esac; return 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/compiler" "$work/out" "$work/res"
cp "$zc" "$work/zc-linux"
cp "$root/compiler/runtime.zeph" "$work/compiler/"
cp -r "$root/lib" "$work/lib"

tests=()
for source in "$root"/tests/*.zeph "$root"/tests/regression/*.zeph \
              "$root"/tests/fixtures/basics/*.zeph "$root"/tests/fixtures/threads/*.zeph \
              "$root"/tests/linux/*.zeph "$root"/tests/leaks/*.zeph; do
    [ -f "$source" ] || continue
    name="${source#"$root"/tests/}"
    name="${name%.zeph}"
    tests+=("$name")
done

# run_tier NAME TIER: compile and run one tier; writes out/<id>.<tier>.{out,log}
# and prints "ok" or a failure reason.
run_tier() {
    local name="$1" tier="$2" id="${1//\//__}" flag=""
    [ "$tier" = O2 ] && flag="-O2"
    local exe="$work/out/$id.$tier" log="$work/out/$id.$tier.log"
    if ! timeout 300 "$work/zc-linux" --linux --rt $flag "$root/tests/$name.zeph" "$exe" >"$log" 2>&1; then
        echo "compile failed"; return
    fi
    chmod +x "$exe"
    (cd "$work" && timeout 60 "$exe" </dev/null >"$exe.out" 2>>"$log")
    local code=$? want="${EXPECT_EXIT[${name##*/}]:-0}"
    if [ "$code" != "$want" ]; then echo "exit $code (want $want)"; return; fi
    local expected="$root/tests/$name.expected"
    if [ -f "$expected" ] && ! cmp -s "$exe.out" "$expected"; then echo "output differs from .expected"; return; fi
    echo ok
}

# verdict UNIT REASON: prints the status line for one unit.
verdict() {
    local unit="$1" reason="$2" known="${KNOWN_FAIL[$1]:-}"
    if [ "$reason" = ok ]; then
        if [ -n "$known" ]; then echo "XPASS $unit  (listed as known: $known)"; else echo "PASS  $unit"; fi
    else
        if [ -n "$known" ]; then echo "XFAIL $unit  ($known)"; else echo "FAIL  $unit  ($reason)"; fi
    fi
}

run_test() {
    local name="$1" id="${1//\//__}" base o2
    base="$(run_tier "$name" base)"
    o2="$(run_tier "$name" O2)"
    {
        verdict "$name:base" "$base"
        verdict "$name:O2" "$o2"
        if ! no_parity "$name"; then
            if [ -f "$work/out/$id.base.out" ] && [ -f "$work/out/$id.O2.out" ] &&
               cmp -s "$work/out/$id.base.out" "$work/out/$id.O2.out"; then
                verdict "$name:parity" ok
            else
                verdict "$name:parity" "baseline and -O2 output differ"
            fi
        fi
    } >"$work/res/$id"
}

run_python() {
    local check="$1" id="py__$1" result reason=ok
    shift
    result="$(cd "$root" && timeout 600 python3 "tests/$check.py" "$@" 2>&1)" || reason="exit $?"
    if [ "$check" = argument_tests ]; then
        # argument_tests.py exits 0 even when cases fail; read its summary
        echo "$result" | grep -q ' 0 failed$' || reason="$(echo "$result" | tail -1)"
    fi
    printf '%s\n' "$result" >"$work/out/$id.log"
    verdict "py:$check" "$reason" >"$work/res/$id"
}

run_extern() {
    local reason=ok
    (cd "$root" && timeout 600 sh tests/linux_extern.sh) >"$work/out/sh__linux_extern.log" 2>&1 || reason="failed"
    verdict "sh:linux_extern" "$reason" >"$work/res/sh__linux_extern"
}

run_diagnostics() {
    local reason=ok
    (cd "$root" && timeout 600 bash tests/linux/diagnostics.sh "$work") >"$work/out/sh__diagnostics.log" 2>&1 || reason="$(tail -1 "$work/out/sh__diagnostics.log")"
    verdict "sh:diagnostics" "$reason" >"$work/res/sh__diagnostics"
}

export -f run_tier verdict run_test run_python run_extern run_diagnostics no_parity
export root work
export KNOWN_FAIL_DUMP="$(declare -p KNOWN_FAIL EXPECT_EXIT)"

matches() { [ -z "$pattern" ] || echo "$1" | grep -Eq -- "$pattern"; }

{
    for name in "${tests[@]}"; do matches "$name" && echo "run_test $name"; done
    matches "py:include_path" && echo "run_python include_path"
    matches "py:assert_message_release" && echo "run_python assert_message_release"
    matches "py:argument_tests" && echo "run_python argument_tests --compiler $work/zc-linux"
    if command -v gcc >/dev/null && matches "sh:linux_extern"; then echo "run_extern"; fi
    matches "sh:diagnostics" && echo "run_diagnostics"
} | xargs -P "$jobs" -I{} bash -c 'eval "$KNOWN_FAIL_DUMP"; {}'

pass=0 fail=0 xfail=0 xpass=0
for result in "$work"/res/*; do
    [ -f "$result" ] || continue
    while IFS= read -r line; do
        echo "$line"
        case "$line" in
            PASS*) pass=$((pass + 1)) ;;
            XFAIL*) xfail=$((xfail + 1)) ;;
            XPASS*) xpass=$((xpass + 1)) ;;
            FAIL*)
                fail=$((fail + 1))
                if [ "$verbose" = 1 ]; then
                    id="$(basename "$result")"
                    cat "$work"/out/"$id"*.log 2>/dev/null | sed 's/^/    /' | head -40
                fi ;;
        esac
    done <"$result"
done
echo "linux harness: $pass passed, $fail failed, $xfail xfail, $xpass xpass"
[ "$fail" = 0 ] && [ "$xpass" = 0 ]
