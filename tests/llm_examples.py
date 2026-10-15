#!/usr/bin/env python3
"""Compile and run every ```zephyr block in docs/llm.md (Linux).

    python3 tests/llm_examples.py [--compiler ZC] [-O2]

Each block is a complete program: it must compile at baseline and -O2 and
exit 0. The compiler needs compiler/runtime.zeph and lib/ next to it (the
repository root works, as does the harness work dir)."""
import os
import re
import subprocess
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
compiler = os.path.join(root, "zc-linux")
if "--compiler" in sys.argv:
    compiler = os.path.abspath(sys.argv[sys.argv.index("--compiler") + 1])

text = open(os.path.join(root, "docs", "llm.md")).read()
blocks = re.findall(r"```zephyr\n(.*?)```", text, re.S)
failures = 0
with tempfile.TemporaryDirectory() as work:
    for number, block in enumerate(blocks, 1):
        source = os.path.join(work, f"example{number}.zeph")
        with open(source, "w") as handle:
            handle.write(block)
        first = block.strip().splitlines()[0]
        for flags in ([], ["-O2"]):
            program = os.path.join(work, f"example{number}")
            build = subprocess.run([compiler, "--linux", *flags, source, program],
                                   capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
            if build.returncode != 0:
                print(f"FAIL example {number} {flags} does not compile ({first}):\n{build.stdout}{build.stderr}")
                failures += 1
                continue
            os.chmod(program, 0o755)
            run = subprocess.run([program], capture_output=True, text=True, timeout=60, cwd=work, stdin=subprocess.DEVNULL)
            if run.returncode != 0:
                print(f"FAIL example {number} {flags} exits {run.returncode} ({first}):\n{run.stdout}{run.stderr}")
                failures += 1
print(f"llm.md examples: {len(blocks)} blocks, {failures} failures")
sys.exit(1 if failures or not blocks else 0)
