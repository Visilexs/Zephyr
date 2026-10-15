#!/usr/bin/env bash
# tests/linux/diagnostics.sh -- compiler diagnostics, CLI, `zc run`, the --test
# runner and runtime panic messages (Phase 3 "agentic coding").
#
#   tests/linux/diagnostics.sh DIR
# DIR holds zc-linux, compiler/runtime.zeph and lib/ (tests/linux/run.sh
# passes its work dir). Every program check runs at baseline and -O2.
set -u
root="$(cd "$(dirname "$0")/../.." && pwd)"
dir="${1:?usage: diagnostics.sh DIR}"
zc="$dir/zc-linux"
cases="$root/tests/diagnostics"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
failures=0

fail() { echo "FAIL: $*"; failures=$((failures + 1)); }

# expect_text NAME EXPECTED ACTUAL
expect_text() {
    if [ "$2" != "$3" ]; then
        fail "$1"
        echo "  expected: $(printf '%s' "$2" | head -c 600)"
        echo "  actual:   $(printf '%s' "$3" | head -c 600)"
    fi
}

# compile_error FILE.zeph: stderr must equal FILE.expected, exit code 2
compile_error() {
    local name="$1" flag
    for flag in "" "-O2"; do
        local output code
        output="$(cd "$cases" && timeout 60 "$zc" --linux $flag "$name.zeph" "$tmp/out" 2>&1 </dev/null)"
        code=$?
        expect_text "$name $flag: exit code" "2" "$code"
        expect_text "$name $flag: diagnostics" "$(cat "$cases/$name.expected")" "$output"
    done
}

# snippet NAME SOURCE EXPECTED-STDERR: compile one inline program, expect exit 2
snippet() {
    printf '%s\n' "$2" >"$tmp/h.zeph"
    local output code
    output="$(cd "$tmp" && timeout 60 "$zc" --linux h.zeph "$tmp/out" 2>&1 </dev/null)"
    code=$?
    expect_text "$1: exit code" "2" "$code"
    expect_text "$1" "$3" "$output"
}

compile_error multi
compile_error generic

# --error-format=json: one object per line
output="$(cd "$cases" && timeout 60 "$zc" --linux --error-format=json multi.zeph "$tmp/out" 2>&1 </dev/null)"
expect_text "json first line" '{"file":"multi.zeph","line":2,"col":5,"severity":"error","code":"type","message":"initializer: expected str, got int","hint":null}' "$(echo "$output" | head -1)"
expect_text "json line count" "4" "$(echo "$output" | wc -l | tr -d ' ')"
output="$(cd "$tmp" && printf 'let x = null\n' >j.zeph && timeout 60 "$zc" --linux --error-format=json j.zeph "$tmp/out" 2>&1 </dev/null)"
expect_text "json hint" '{"file":"j.zeph","line":1,"col":9,"severity":"error","code":"type","message":"unknown variable '"'"'null'"'"'","hint":"Zephyr has no null; use an optional: `let x: T? = none`, test with `if let v = x { ... }` or `x.or(default)`"}' "$output"

# hints for habits from other languages
snippet "hint &&" 'if true && false { print(1) }' "h.zeph:1:9: error: unexpected '&&'
  hint: Zephyr spells logical and as 'and': if a and b { ... }"
snippet "hint ||" 'let a = true || false' "h.zeph:1:14: error: unexpected '||'
  hint: Zephyr spells logical or as 'or': if a or b { ... }"
snippet "hint !" 'if !true { print(1) }' "h.zeph:1:4: error: unexpected '!'
  hint: Zephyr spells logical not as 'not': if not done { ... }"
snippet "hint ++" 'var i = 0
i++' "h.zeph:2:2: error: unexpected '++'
  hint: there is no ++; write x += 1"
snippet "hint --" 'var i = 0
i--' "h.zeph:2:2: error: unexpected '--'
  hint: there is no --; write x -= 1"
snippet "hint ;" 'let x = 1;' "h.zeph:1:10: error: unexpected ';'
  hint: statements end at a newline; remove the ';' (put two statements on two lines)"
snippet "hint =>" 'match 1 { 1 => { } }' "h.zeph:1:13: error: unexpected '=>'
  hint: match arms are written \`pattern { ... }\` with no '=>'; closures are fn(x: int) -> int { ... }"
snippet "hint nil" 'let x = nil' "h.zeph:1:9: error: unknown variable 'nil'
  hint: Zephyr has no null; use an optional: \`let x: T? = none\`, test with \`if let v = x { ... }\` or \`x.or(default)\`"
snippet "hint None" 'let x = None' "h.zeph:1:9: error: unknown variable 'None'
  hint: Zephyr has no null; use an optional: \`let x: T? = none\`, test with \`if let v = x { ... }\` or \`x.or(default)\`"
snippet "hint True" 'let x = True' "h.zeph:1:9: error: unknown variable 'True'
  hint: booleans are lowercase: true"
snippet "hint False" 'let x = False' "h.zeph:1:9: error: unknown variable 'False'
  hint: booleans are lowercase: false"
snippet "hint len" 'print(len([1]))' "h.zeph:1:7: error: unknown function 'len'
  hint: length is a method: x.len()"
snippet "hint let mut" 'let mut x = 1' "h.zeph:1:5: error: unexpected 'mut'
  hint: a mutable variable is declared with var: var x = 1 (let is immutable)"
snippet "hint string" 'let s: string = "a"' "h.zeph:1:8: error: unknown type 'string'
  hint: the string type is str"
snippet "missing import" 'import "nothere.zeph"' "h.zeph:1:1: error: cannot find import 'nothere.zeph' (looked in: ./, $dir/, $dir/lib/, the library built into zc)
  hint: std modules are imported as \"std/name.zeph\"; add a directory with -I DIR"

# command line
cli() {   # cli NAME EXPECTED-CODE EXPECTED-FIRST-LINE ARGS...
    local name="$1" want="$2" first="$3" output code
    shift 3
    output="$(cd "$tmp" && timeout 60 "$zc" "$@" 2>&1 </dev/null)"
    code=$?
    expect_text "$name: exit code" "$want" "$code"
    expect_text "$name" "$first" "$(echo "$output" | head -1)"
}
printf 'print("hi")\n' >"$tmp/ok.zeph"
cli "unknown flag" 2 "zc: error: unknown flag '--bogus'" --bogus ok.zeph out
cli "missing input" 2 "zc: error: cannot read input 'nosuch.zeph': no such file" --linux nosuch.zeph out
cli "no output" 2 "zc: error: no output file (zc <input.zeph> <output>, or zc run <input.zeph>)" --linux ok.zeph
cli "extra argument" 2 "zc: error: unexpected extra argument 'more' (zc takes one input file and one output file)" --linux ok.zeph out more
cli "help" 0 "usage: zc [flags] <input.zeph> <output>       compile (output: exe, .s, .o with --linux, .wasm)" --help
# --linux implies --rt
rm -f "$tmp/out"
(cd "$tmp" && timeout 60 "$zc" --linux ok.zeph out </dev/null) && chmod +x "$tmp/out" &&
    expect_text "--linux implies --rt" "hi" "$(timeout 60 "$tmp/out" </dev/null)" || fail "--linux without --rt does not build"

# zc run: memfd + exec; the program's exit code and output come through
printf 'print("args {args().len()}")\nlet xs = [1]\nif args().len() > 2 { print(xs[5]) }\n' >"$tmp/run.zeph"
output="$(cd "$tmp" && timeout 60 "$zc" run run.zeph a 2>&1 </dev/null)"
expect_text "zc run: exit code" "0" "$?"
expect_text "zc run" "args 2" "$output"
output="$(cd "$tmp" && timeout 60 "$zc" run -O2 run.zeph a b 2>&1 </dev/null)"
expect_text "zc run panic: exit code" "1" "$?"
expect_text "zc run panic" "args 3
panic: run.zeph:3: index 5 out of bounds for length 1" "$output"

# runtime panics include the values, identically at both tiers
for flag in "" "-O2"; do
    (cd "$cases" && timeout 60 "$zc" --linux $flag panics.zeph "$tmp/panics" </dev/null) || { fail "panics.zeph $flag does not build"; continue; }
    chmod +x "$tmp/panics"
    check_panic() {   # check_panic ARGCOUNT EXPECTED
        local extra="" i
        for ((i = 1; i < $1; i++)); do extra="$extra x"; done
        local output
        output="$(cd "$tmp" && timeout 60 ./panics $extra 2>&1 </dev/null)"
        expect_text "panics $1 $flag: exit code" "1" "$?"
        expect_text "panics $1 $flag" "$2" "$output"
    }
    check_panic 1 "panic: panics.zeph:7: index 7 out of bounds for length 3"
    check_panic 2 'panic: panics.zeph:8: map key "b" not found'
    check_panic 3 "panic: panics.zeph:9: map key 7 not found"
    check_panic 4 "panic: panics.zeph:10: index 5 out of bounds for length 2"
    check_panic 5 "panic: panics.zeph:11: index 9 out of bounds for length 3"
    check_panic 6 "panic: panics.zeph:14: assertion failed: left == right
  left:  xy
  right: xz"
    check_panic 7 "panic: panics.zeph:18: assertion failed: left < right
  left:  1.5
  right: 1"
done

# --test keeps going after a failure, prints a summary, exits 1; --test-filter
for flag in "" "-O2"; do
    (cd "$cases" && timeout 60 "$zc" --linux --test $flag tests.zeph "$tmp/tests" </dev/null) || { fail "tests.zeph $flag does not build"; continue; }
    chmod +x "$tmp/tests"
    output="$(timeout 60 "$tmp/tests" 2>&1 </dev/null)"
    expect_text "--test $flag: exit code" "1" "$?"
    expect_text "--test $flag" "test adds ... ok
test broken ... panic: tests.zeph:3: assertion failed: left == right
  left:  3
  right: 4
FAILED
test strings ... ok
test panics ... panic: tests.zeph:7: index 3 out of bounds for length 1
FAILED
2 passed, 2 failed" "$output"
    (cd "$cases" && timeout 60 "$zc" --linux --test-filter str $flag tests.zeph "$tmp/tests" </dev/null) && chmod +x "$tmp/tests"
    output="$(timeout 60 "$tmp/tests" 2>&1 </dev/null)"
    expect_text "--test-filter $flag: exit code" "0" "$?"
    expect_text "--test-filter $flag" "test strings ... ok
1 test passed" "$output"
done

if [ "$failures" = 0 ]; then echo "diagnostics: all checks passed"; else echo "diagnostics: $failures failed"; exit 1; fi
