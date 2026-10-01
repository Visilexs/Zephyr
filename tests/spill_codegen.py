#!/usr/bin/env python3
"""Check Windows integer spill instructions against a wrapping-integer model."""
import argparse
import operator
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = (("+", operator.add, -2147483648), ("-", operator.sub, 2147483647),
              ("&", operator.and_, -257), ("|", operator.or_, 32),
              ("^", operator.xor, 4294967296))
COMPARISONS = (("<", operator.lt, 0), ("<=", operator.le, -2147483648),
               (">", operator.gt, 2147483647), (">=", operator.ge, 4294967296),
               ("==", operator.eq, 0), ("!=", operator.ne, -(1 << 63)))
SEEDS = (0, -1, (1 << 63) - 1, -(1 << 63), -173, 4294966611, 2147480910)
MEMORY = r"qword ptr \[rsp \+ [0-9]+\]"


def wrap(value):
    return (value + (1 << 63)) % (1 << 64) - (1 << 63)


def literal(value):
    return "(-9223372036854775807 - 1)" if value == -(1 << 63) else str(value)


def expected_result(rounds, seed):
    """Evaluate bounded arithmetic with independent Python integers and predicates."""
    values = [wrap(seed + index * 171 + 1) for index in range(30)]
    flags = 0
    for _ in range(rounds):
        for index in range(30):
            _, operation, right = OPERATIONS[index % len(OPERATIONS)]
            values[index] = wrap(operation(values[index], right))
        values[5] = wrap(values[5] * 3)
        values[6] = wrap(values[6] + values[7])
        values[8], values[9] = wrap(values[9] - values[10]), values[8]
        for index, (_, compare, right) in enumerate(COMPARISONS):
            flags += int(compare(values[index], right))
            if compare(values[index + 12], right):
                flags += index + 2
    return wrap(sum(values) + flags)


def program():
    """Keep thirty integers live and materialize booleans across real calls."""
    lines = ["var trace = 0", "fn spillBool(value: bool) -> int {"]
    # Exceed the AST inline limit so comparisons remain values passed to a call.
    lines += ["    trace = trace + 0"] * 40
    lines += ["    if value { return 1 }", "    return 0", "}",
              "fn spillPressure(rounds: int, seed: int) -> int {"]
    lines += [f"    var x{index} = seed + {index * 171 + 1}" for index in range(30)]
    lines += ["    var flags = 0", "    for step in 0..rounds {"]
    for index in range(30):
        symbol, _, right = OPERATIONS[index % len(OPERATIONS)]
        lines.append(f"        x{index} = x{index} {symbol} {literal(right)}")
    lines += ["        x5 = x5 * 3", "        x6 = x6 + x7",
              "        let saved = x8", "        x8 = x9 - x10", "        x9 = saved"]
    for index, (symbol, _, right) in enumerate(COMPARISONS):
        lines.append(f"        flags = flags + spillBool(x{index} {symbol} {literal(right)})")
        lines.append(f"        if x{index + 12} {symbol} {literal(right)} {{ flags = flags + {index + 2} }}")
    lines += ["    }", "    return flags + " + " + ".join(f"x{index}" for index in range(30)), "}"]
    expected = []
    for seed in SEEDS:
        for rounds in (0, 1, 3):
            lines.append(f"print(spillPressure({rounds}, {literal(seed)}))")
            expected.append(str(expected_result(rounds, seed)))
    return "\n".join(lines) + "\n", ("\n".join(expected) + "\n").encode("ascii")


def run(command):
    """Bound compiler/program execution while keeping runtime lookup at repo root."""
    return subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=30, check=False)


def check_assembly(assembly, report):
    """Require spill fast paths and legal fallbacks without fixing allocator slots."""
    match = re.search(r"opt: function spillPressure: optimized, ([0-9]+) spills", report)
    assert match and int(match[1]) > 0, "pressure function did not optimize with spills"
    body = assembly.split("lm_spillPressure:\n", 1)[1]
    body = re.split(r"(?m)^[A-Za-z_]\w*:", body, maxsplit=1)[0]
    counts = {}
    for mnemonic in ("add", "sub", "and", "or", "xor"):
        counts[mnemonic] = len(re.findall(r"(?m)^  " + mnemonic + " " + MEMORY + ", ", body))
        assert counts[mnemonic], f"missing memory-destination {mnemonic}"
    assert re.search(r"cmp " + MEMORY + r", [^\n]+\n  set", body), "missing materialized spill comparison"
    assert re.search(r"cmp " + MEMORY + r", [^\n]+\n  j", body), "missing branch spill comparison"
    for immediate in (0, -2147483648, 2147483647):
        assert re.search(r"cmp " + MEMORY + ", " + str(immediate) + r"\n", body), f"missing spill comparison with {immediate}"
    assert re.search(r"xor " + MEMORY + r", r[a-z0-9]+\n", body), "missing register-held large-constant update"
    assert re.search(r"mov rax, " + MEMORY + r"\n  cmp rax, " + MEMORY, body), "missing memory-memory compare fallback"
    assert re.search(r"sub rax, " + MEMORY + r"\n  mov " + MEMORY + r", rax", body), "missing separate-result subtraction fallback"
    assert "  imul " in body, "missing multiplication fallback"
    assert "call lm_spillBool\n" in body, "boolean consumer was inlined"
    for line in body.splitlines():
        instruction = line.strip()
        if re.match(r"(?:add|sub|and|or|xor|cmp) " + MEMORY + ", ", instruction):
            assert instruction.count("[") == 1, f"illegal memory-memory instruction: {instruction}"
            right = instruction.rsplit(", ", 1)[1]
            if re.fullmatch(r"-?[0-9]+", right):
                assert -(1 << 31) <= int(right) < (1 << 31), f"unencodable immediate: {instruction}"
        assert not re.match(r"(?:test|imul) " + MEMORY, instruction), f"unexpected memory destination: {instruction}"
    return f"{match[1]} spills; memory updates {counts}"


def main():
    """Compare baseline/O2 results to the model, then check optimized instructions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    options = parser.parse_args()
    if os.name != "nt":
        parser.error("this code-generation test requires native Windows")
    compiler = options.compiler.resolve()
    source, expected = program()
    passed = 0
    failed = 0
    with tempfile.TemporaryDirectory(prefix="zephyr_spill_codegen_") as directory:
        directory = Path(directory)
        fixture = directory / "spill_codegen.zeph"
        fixture.write_text(source, encoding="utf-8")
        for tier, flags in (("baseline", []), ("O2", ["-O2"])):
            try:
                executable = directory / (tier + ".exe")
                build = run([str(compiler), "--rt", *flags, str(fixture), str(executable)])
                assert build.returncode == 0, f"compile exit {build.returncode}: {(build.stdout + build.stderr)[-500:]!r}"
                result = run([str(executable)])
                assert result.returncode == 0, f"run exit {result.returncode}: {result.stderr[:200]!r}"
                assert result.stdout == expected, f"stdout {result.stdout!r}, expected {expected!r}"
                passed += 1
                print(f"PASS {tier}:output (21 wrapping-model cases)")
            except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                failed += 1
                print(f"FAIL {tier}:output: {error}")
        try:
            assembly_path = directory / "O2.s"
            build = run([str(compiler), "--rt", "-O2", "--opt-report", str(fixture), str(assembly_path)])
            assert build.returncode == 0, f"assembly compile exit {build.returncode}"
            details = check_assembly(assembly_path.read_text(encoding="utf-8"),
                                     (build.stdout + build.stderr).decode("utf-8", errors="replace"))
            passed += 1
            print(f"PASS O2:assembly ({details})")
        except (AssertionError, IndexError, OSError, subprocess.TimeoutExpired) as error:
            failed += 1
            print(f"FAIL O2:assembly: {error}")
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
