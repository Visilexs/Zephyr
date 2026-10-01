#!/usr/bin/env python3
"""Check native argument parsing, including empty and large arguments."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tests/fixtures/basics/arguments.zeph"


def run(command):
    """Bound compiler and fixture execution without inheriting terminal input."""
    if os.name == "nt":
        assert len(subprocess.list2cmdline(command)) < 32767, "command line too long"
    return subprocess.run(
        command, cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=30, check=False,
    )


def check_arguments(executable, arguments):
    """Compare every supplied argument, excluding the platform-specific argv[0]."""
    expected = f"{len(arguments) + 1}\n"
    expected += "".join(f"{len(argument)}\n{argument}\n" for argument in arguments)
    expected = expected.encode("ascii")
    result = run([str(executable), *arguments])
    assert result.returncode == 0, f"exit {result.returncode}: {result.stderr[:200]!r}"
    if result.stdout != expected:
        mismatch = next(
            (i for i, (actual, wanted) in enumerate(zip(result.stdout, expected))
             if actual != wanted), min(len(result.stdout), len(expected)),
        )
        raise AssertionError(
            f"stdout differs at {mismatch}; lengths {len(result.stdout)} != {len(expected)}; "
            f"actual {result.stdout[mismatch:mismatch + 60]!r}, "
            f"expected {expected[mismatch:mismatch + 60]!r}"
        )


def main():
    """Compile both tiers and run the same argument cases against each binary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    options = parser.parse_args()
    compiler = options.compiler.resolve()
    cases = [
        ("none", []),
        ("spaces", ["two words", " leading and trailing "]),
        ("empty", ["before", "", "after", ""]),
        ("tabs", ["tab\tseparated", "\t"]),
    ]
    for size in (2047, 2048, 2049, 4095, 4096, 4097, 12000):
        cases.append((f"length-{size}", ["x" * size]))
    cases.append(("multiple-large", ["a" * 2047, "b" * 4097, "c" * 12000, "", "two words"]))
    passed = 0
    failed = 0
    with tempfile.TemporaryDirectory(prefix="zephyr_arguments_") as directory:
        for tier, flags in (("baseline", []), ("O2", ["-O2"])):
            executable = Path(directory) / (tier + (".exe" if os.name == "nt" else ""))
            target_flags = ["--linux"] if sys.platform.startswith("linux") else []
            try:
                result = run([str(compiler), *target_flags, "--rt", *flags, str(SOURCE), str(executable)])
                assert result.returncode == 0, f"compile exit {result.returncode}: {(result.stdout + result.stderr)[:400]!r}"
                assert executable.is_file(), "compiler did not create executable"
                if os.name != "nt":
                    executable.chmod(executable.stat().st_mode | 0o111)
            except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                failed += 1
                print(f"FAIL {tier}: {error}")
                continue
            for name, arguments in cases:
                try:
                    check_arguments(executable, arguments)
                except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                    failed += 1
                    print(f"FAIL {tier}:{name}: {error}")
                else:
                    passed += 1
                    print(f"PASS {tier}:{name}")
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
