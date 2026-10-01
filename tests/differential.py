"""Seeded, terminating programs checked against a small independent value model."""

import argparse
import random
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def signed(value):
    """Zephyr int arithmetic wraps at 64 bits."""
    return (value + 2**63) % 2**64 - 2**63


def arithmetic(rng, prefix, pure):
    """Evaluate generated expressions left to right, including global writes."""
    initial = rng.randrange(1, 30)
    delta = rng.randrange(1, 10)
    state = initial

    def expression(depth):
        nonlocal state
        if depth and rng.random() < 0.65:
            left, a = expression(depth - 1)
            operator = rng.choice(["+", "-", "*"])
            right, b = expression(depth - 1)
            value = {"+": a + b, "-": a - b, "*": a * b}[operator]
            return f"({left} {operator} {right})", signed(value)
        choice = rng.randrange(3)
        if choice == 0:
            return prefix + "g", state
        if choice == 1:
            if not pure:
                state = signed(state + delta)
            return prefix + "call()", delta
        value = rng.randrange(10)
        return str(value), value

    body = "" if pure else f"{prefix}g += {delta}\n"
    source = f"var {prefix}g = {initial}\nfn {prefix}call() -> int {{\n{body}return {delta}\n}}\n"
    expected = []
    for _ in range(6):
        code, value = expression(3)
        if rng.choice([False, True]):
            source += f"{prefix}g = {code}\nprint({prefix}g)\n"
            state = value
        else:
            source += f"print({code})\n"
        expected.append(str(value))
    count = rng.randrange(2, 25)
    source += f"var {prefix}acc = 0\nfor i in 0..{count} {{ {prefix}acc = i }}\n"
    source += f"print({prefix}acc + {prefix}call(), {prefix}acc)\n"
    expected.append(f"{count - 1 + delta} {count - 1}")
    return source, "\n".join(expected) + "\n"


def scenario(rng, prefix, kind):
    """Reference values for ownership and typed operations use Python values."""
    a, b = rng.randrange(1, 30), rng.randrange(31, 60)
    if kind == "float":
        source = f"""var {prefix}g = {a}.5
fn {prefix}call() -> float {{ {prefix}g = {b}.5
return 0.5 }}
print({prefix}g + {prefix}call(), {prefix}g)
"""
        return source, f"{a + 1} {b}.5\n"
    if kind == "ownership":
        source = f"""struct {prefix}Box {{ value: int }}
var {prefix}items = [{prefix}Box{{value: {a}}}]
fn {prefix}replace() -> int {{ {prefix}items = [{prefix}Box{{value: {b}}}]
return 0 }}
let {prefix}alias = {prefix}items[0]
print({prefix}items[{prefix}replace()].value, {prefix}alias.value, {prefix}items[0].value)
let {prefix}nested = [[{a}], [{b}]]
let {prefix}inner = {prefix}nested[0]
{prefix}nested[0] = [{b}]
print({prefix}inner[0], {prefix}nested[0][0])
"""
        return source, f"{a} {a} {b}\n{a} {b}\n"
    if kind == "closures":
        source = f"""fn {prefix}capture(xs: [int]) -> fn() -> int {{
return fn() -> int {{ return xs[0] }}
}}
var {prefix}xs = [{a}]
let {prefix}read = {prefix}capture({prefix}xs)
{prefix}xs = [{b}]
print({prefix}read(), {prefix}xs[0])
"""
        return source, f"{a} {b}\n"
    if kind == "interfaces":
        source = f"""interface {prefix}Value {{ fn get(self) -> int }}
struct {prefix}Box {{ value: int }}
impl {prefix}Box {{ fn get(self) -> int {{ return self.value }} }}
fn {prefix}sum(xs: [{prefix}Value]) -> int {{
var total = 0
for x in xs {{ total += x.get() }}
return total
}}
let {prefix}xs: [{prefix}Value] = [{prefix}Box{{value: {a}}}, {prefix}Box{{value: {b}}}]
print({prefix}sum({prefix}xs))
"""
        return source, f"{a + b}\n"
    if kind == "maps":
        source = f"""fn {prefix}identity[T](x: T) -> T {{ return x }}
let {prefix}map = [1: {a}, 2: {b}]
var {prefix}sum = 0
for key, value in {prefix}map {{ {prefix}sum += key * value }}
print({prefix}identity({prefix}sum), {prefix}identity("generic"))
"""
        return source, f"{a + 2 * b} generic\n"
    count = rng.randrange(1, 20)
    chunk = rng.choice(["a", "xy", "123"])
    source = f"""var {prefix}text = ""
for i in 0..{count} {{ {prefix}text = {prefix}text + "{chunk}" }}
print({prefix}text)
"""
    return source, chunk * count + "\n"


def check(compiler, units, work):
    """Compare each compiler tier with the reference, with closed stdin/timeouts."""
    source = work / "program.zeph"
    source.write_text("\n".join(code for code, _ in units), encoding="utf-8")
    expected = "".join(output for _, output in units).encode()
    for flags in ([], ["-O2"]):
        name = "O2" if flags else "baseline"
        binary = work / f"{name}.exe"
        try:
            compiled = subprocess.run(
                [str(compiler), "--rt", *flags, str(source), str(binary)],
                cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
            )
            if compiled.returncode:
                return f"{name}: compile exit {compiled.returncode}\n" + compiled.stdout.decode(errors="replace") + compiled.stderr.decode(errors="replace")
            result = subprocess.run(
                [str(binary)], cwd=ROOT, stdin=subprocess.DEVNULL,
                capture_output=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            return f"{name}: timeout"
        actual = result.stdout.replace(b"\r\n", b"\n")
        if result.returncode or actual != expected:
            return f"{name}: exit {result.returncode}\nexpected: {expected!r}\nactual: {actual!r}\nstderr: {result.stderr!r}"
    return None


def reduce_failure(compiler, units, work):
    """Drop independent source units while preserving a reference mismatch."""
    index = 0
    while len(units) > 1 and index < len(units):
        candidate = units[:index] + units[index + 1:]
        if check(compiler, candidate, work):
            units = candidate
        else:
            index += 1
    return units


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=ROOT / "zc.exe")
    parser.add_argument("--seed", type=int, default=20261001)
    parser.add_argument("--cases", type=int, default=100)
    parser.add_argument("--pure", action="store_true", help="calls do not mutate shared state")
    parser.add_argument("--repro-dir", type=Path, default=ROOT / "repro")
    args = parser.parse_args()
    if args.cases < 1:
        parser.error("--cases must be positive")
    compiler = args.compiler.resolve()
    kinds = ["closures", "interfaces", "maps", "strings"]
    if not args.pure:
        kinds += ["float", "ownership"]
    with tempfile.TemporaryDirectory(prefix="zephyr-fuzz-") as directory:
        work = Path(directory)
        for index in range(args.cases):
            seed = args.seed + index
            rng = random.Random(seed)
            units = [arithmetic(rng, "arith_", args.pure)]
            units += [scenario(rng, f"case_{i}_", kind) for i, kind in enumerate(kinds)]
            failure = check(compiler, units, work)
            if failure:
                args.repro_dir.mkdir(parents=True, exist_ok=True)
                path = args.repro_dir / f"fuzz-{seed}{'-pure' if args.pure else ''}.zeph"
                reduced = reduce_failure(compiler, units, work)
                path.write_text("\n".join(code for code, _ in reduced), encoding="utf-8")
                path.with_suffix(".expected").write_text("".join(out for _, out in reduced), encoding="utf-8")
                path.with_suffix(".txt").write_text(check(compiler, reduced, work) or failure, encoding="utf-8")
                print(f"FAIL seed {seed}; reduced reproduction: {path}", flush=True)
                print(failure, flush=True)
                return 1
            if (index + 1) % 10 == 0 or index + 1 == args.cases:
                print(f"PASS {index + 1}/{args.cases} programs, both tiers and reference", flush=True)
    print(f"{args.cases} programs passed; 0 mismatches; seed {args.seed}; pure={args.pure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
