#!/usr/bin/env python3
"""Check Windows frame-free entry returns, results, and calling-convention guards."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tests/regression/entry_return.zeph"
EXPECTED = """lt 3 4329
le 4 4359
gt 2 4329
ge -9 4329
eq 3 4329
ne 2 4323
extreme -3 9223372036854775807 -9223372036854775808
literals 9223372036854775806 9223372036854775807 -9223372036854775808 0
left 37 9223372036854775770
three -3 917
fib -1 0 1 55
effect -3 12 1
globals -2 3 0 3
calls -2 3 -2 3 4
arithmetic -2 3 -1 4
types -2 3 -2 3
five 5 54329
values -2 3 7 9
equal 2222 2 2222 2 2 2222
""".encode("ascii")
ELIGIBLE = {
    "entryLt", "entryLe", "entryGt", "entryGe", "entryEq", "entryNe",
    "entryMax", "entryMin", "entryLiteralLeft", "entryThree", "entryFib", "entryEffect",
}
REPORT_PREFIX = "opt: entry return "


def run(command):
    """Bound child processes and retain the repository's runtime resource lookup."""
    return subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=30, check=False)


def check_prefix(assembly, name):
    """Require a conditional return before the frame, preserving every argument."""
    body = assembly.split("lm_" + name + ":\n", 1)[1].split("\nlm_", 1)[0]
    prefix = body.split("push rbp", 1)[0]
    lines = [line.strip() for line in prefix.splitlines() if line.strip()]
    assert lines.count("ret") == 1, f"{name}: missing single pre-frame return"
    branches = [line for line in lines if re.fullmatch(r"j(?:l|le|g|ge|e|ne) \.L[0-9]+", line)]
    assert len(branches) == 1, f"{name}: missing signed conditional branch"
    assert lines[-1] == branches[0].split()[1] + ":", f"{name}: slow branch misses frame"
    for line in lines[:-1]:
        # The only writes permitted before the frame target volatile scratch registers.
        assert (line == "ret" or line == branches[0] or
                re.fullmatch(r"cmp (?:r(?:ax|cx|dx|8|9|10|11)|-?[0-9]+), (?:r(?:ax|cx|dx|8|9|10|11)|-?[0-9]+)", line) or
                re.fullmatch(r"mov(?:abs)? (?:rax|r10|r11), (?:r(?:ax|cx|dx|8|9|10|11)|-?[0-9]+)", line)), f"{name}: unsafe prefix instruction {line!r}"
    assert "call lm_" + name + "\n" in assembly, f"{name}: prefix is never called"


def main():
    """Check runtime semantics and optimized prefixes independently."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    options = parser.parse_args()
    if os.name != "nt":
        parser.error("this optimization test requires native Windows")
    compiler = options.compiler.resolve()
    source = SOURCE.read_text(encoding="utf-8")
    fixture_names = set(re.findall(r"fn (\w+)\(", source)) | {"closure"}
    # Force real calls for tiny nonrecursive cases instead of testing inlined copies.
    # Global no-op stores survive AST folding and put each body over its inline limit.
    for name in ELIGIBLE - {"entryFib"}:
        pattern = r"(fn " + name + r"\([^\n]+\n    if [^\n]+\n)"
        source, count = re.subn(pattern, lambda match: match[1] + "    trace = trace + 0\n" * 40, source)
        assert count == 1, f"missing entry guard for {name}"
    source += 'print("equal", ' + ", ".join(
        name + "(2, 2, 2, 2)"
        for name in ("entryLt", "entryLe", "entryGt", "entryGe", "entryEq", "entryNe")
    ) + ")\n"
    passed = 0
    failed = 0
    with tempfile.TemporaryDirectory(prefix="zephyr_entry_return_") as directory:
        directory = Path(directory)
        fixture = directory / "entry_return.zeph"
        fixture.write_text(source, encoding="utf-8")
        for tier, flags, expected_names in (
            ("baseline", [], set()),
            ("O2", ["-O2"], ELIGIBLE),
            ("O2-debug", ["-O2", "-g"], set()),
        ):
            executable = directory / (tier + ".exe")
            try:
                build = run([str(compiler), "--rt", *flags, "--opt-report", str(fixture), str(executable)])
                assert build.returncode == 0, f"compile exit {build.returncode}: {(build.stdout + build.stderr)[-500:]!r}"
                result = run([str(executable)])
                assert result.returncode == 0, f"run exit {result.returncode}: {result.stderr[:200]!r}"
                assert result.stdout == EXPECTED, f"stdout: {result.stdout!r}"
                passed += 1
                print(f"PASS {tier}:output")
            except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                failed += 1
                print(f"FAIL {tier}:output: {error}")
                continue
            report = (build.stdout + build.stderr).decode("utf-8", errors="replace")
            names = [line[len(REPORT_PREFIX):] for line in report.splitlines() if line.startswith(REPORT_PREFIX)]
            names = [name for name in names if name in fixture_names]
            if set(names) == expected_names and len(names) == len(expected_names):
                passed += 1
                print(f"PASS {tier}:report")
            else:
                failed += 1
                print(f"FAIL {tier}:report: got {sorted(names)}, expected {sorted(expected_names)}")
        try:
            assembly_path = directory / "O2.s"
            build = run([str(compiler), "--rt", "-O2", str(fixture), str(assembly_path)])
            assert build.returncode == 0, f"assembly compile exit {build.returncode}"
            assembly = assembly_path.read_text(encoding="utf-8")
            for name in sorted(ELIGIBLE):
                check_prefix(assembly, name)
            for name in fixture_names - ELIGIBLE - {"closure"}:
                body = assembly.split("lm_" + name + ":\n", 1)[1]
                assert body.lstrip().startswith("push rbp\n"), f"{name}: unexpected frame-free entry"
            passed += 1
            print("PASS O2:assembly (12 real-call prefixes; rejected cases retain frames)")
        except (AssertionError, IndexError, OSError, subprocess.TimeoutExpired) as error:
            failed += 1
            print(f"FAIL O2:assembly: {error}")
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
