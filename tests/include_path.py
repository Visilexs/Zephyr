#!/usr/bin/env python3
"""zc -I: imports not found beside the importing file are searched in -I dirs."""
import os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZC = ROOT / ("zc-linux" if sys.platform.startswith("linux") else "zc")

with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    (t / "lib/sub").mkdir(parents=True)
    (t / "app").mkdir()
    (t / "lib/sub/helper.zeph").write_text('import "other.zeph"\nfn helper() -> int { return other() + 1 }\n')
    (t / "lib/sub/other.zeph").write_text('fn other() -> int { return 41 }\n')
    (t / "app/main.zeph").write_text('import "sub/helper.zeph"\nfn main() { print("{helper()}") }\n')
    exe = t / "app/main"
    for flags in (["-I", str(t / "lib")], ["-I" + str(t / "lib") + "/"]):
        r = subprocess.run([str(ZC), "--linux", "--rt", *flags, str(t / "app/main.zeph"), str(exe)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        os.chmod(exe, 0o755)
        out = subprocess.run([str(exe)], capture_output=True, text=True).stdout
        assert out == "42\n", out
    r = subprocess.run([str(ZC), "--linux", "--rt", str(t / "app/main.zeph"), str(exe)], capture_output=True, text=True)
    assert r.returncode != 0, "import without -I should fail"
print("include_path: ok")
