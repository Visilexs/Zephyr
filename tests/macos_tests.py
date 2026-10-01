#!/usr/bin/env python3
"""Run the language/runtime regressions as native ARM64 Mac executables."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
# scripts/macos.py shares a name with the backend directory; load the driver
# under a distinct module name, leaving that namespace available to it.
import importlib.util
spec=importlib.util.spec_from_file_location('macos_driver',ROOT/'scripts/macos.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)

FEATURES='''
import "std/list.zeph"
struct Point { x: float, y: float }
fn distance(p: Point) -> float { return sqrt(p.x * p.x + p.y * p.y) }
assert(distance(Point{x: 3.0, y: 4.0}) == 5.0)
fn fib(n: int) -> int { if n < 2 { return n }; return fib(n - 1) + fib(n - 2) }
assert(fib(20) == 6765)
var values = [3, 1, 2]
assert(values.len() == 3)
let offset = 7
let addOffset = fn(n: int) -> int { return n + offset }
assert(addOffset(5) == 12)
var words: [str: int] = ["a": 1, "b": 2]
assert(words["b"] == 2)
var optional: int? = 0
assert(optional.has() and optional.get() == 0)
print("ok")
'''.replace(';','\n')

MEMORY='''
let bytes = " ".repeat(16)
let p = addr(bytes) + 8
store64(p, -1)
store64(p + 8, -1)
store8(p + 3, 0)
assert(load8(p + 2) == 255 and load8(p + 3) == 0 and load8(p + 4) == 255)
store32(p + 4, 0)
assert(load32(p + 4) == 0 and load8(p + 8) == 255)
assert(load16(p) == 65535 and load32(p) == 16777215)
assert(load64(p) == 16777215)
var text = ""
for i in 0..100 { text = text + chr(65 + i % 26) }
assert(text.len() == 100)
var held: [str] = []
for i in 0..200000 {
    let value = "value {i}"
    if i % 20000 == 0 { held.push(value) }
}
assert(held.len() == 10 and held[9] == "value 180000")
print("ok")
'''

IO='''
import "std/io.zeph"
import "std/list.zeph"
let path = args()[1]
writeFile(path, "line1\\n")
appendFile(path, "line2\\n")
assert(fileExists(path))
assert(readFile(path) == "line1\\nline2\\n")
assert(environmentVariable("ZEPHYR_MAC_TEST").get() == "native value")
assert(not environmentVariable("ZEPHYR_MAC_TEST_ABSENT").has())
assert(nowNanoseconds() > 0 and nowMilliseconds() > 0)
assert(run("/usr/bin/true") == 0 and run("/usr/bin/false") == 1)
let directory = args()[2]
assert(listDirectory(directory).contains("data file.txt"))
assert(readLine().get() == "first" and readLine().get() == "second")
assert(not readLine().has())
assert(deleteFile(path) and not fileExists(path))
assert(args()[3] == "" and args()[4] == "two words" and args()[5] == "café")
print("ok")
'''

def native(path):
    with path.open('rb') as f:
        header=f.read(8)
    assert header==bytes.fromhex('cffaedfe0c000001'),f'Not ARM64 Mach-O: {path}'

def run_case(source,out,expected=None,flags=(),arguments=(),stdin='',env=None,panic=None):
    driver.build(source,out,flags)
    native(out)
    result=subprocess.run([str(out),*arguments],input=stdin,capture_output=True,text=True,timeout=60,env=env)
    if panic:
        assert result.returncode!=0 and panic in result.stderr,f'{source}: expected {panic}, got {result.stderr}'
    else:
        assert result.returncode==0,f'{source}: exit {result.returncode}: {result.stderr}'
    if expected is not None: assert result.stdout.strip()==expected,f'{source}: {result.stdout!r}'
    return result.stdout

def main():
    driver.require_host();native(driver.CORE)
    subprocess.run([sys.executable,ROOT/'tests/macos_codegen.py'],check=True)
    count=1
    with tempfile.TemporaryDirectory(prefix='zephyr mac tests ') as directory:
        work=Path(directory)
        for name,expected in [('hello','Hello, Zephyr!'),('convert','10.5\n6.28\n13\ncount is 13\n3.5\n-7'),('shapes','5\n5\nPoint{x: 6, y: 8}\n3\n(0, 0)\n(3, 4)\n(6, 8)'),('oop','len = 5\nb = (8, 10)\ncircle has area 12.5663706\nrect has area 12\ncircle has area 3.14159265\ntotal area = 27.70796325')]:
            run_case(ROOT/'tests/fixtures/basics'/f'{name}.zeph',work/name,expected);count+=1;print('PASS',name,flush=True)
            if name=='oop':
                run_case(ROOT/'tests/fixtures/basics'/f'{name}.zeph',work/name,expected,flags=['-O2']);count+=1;print('PASS interface dispatch -O2',flush=True)
        for name,source in [('features',FEATURES),('memory',MEMORY)]:
            path=work/f'{name}.zeph';path.write_text(source)
            for flags in ([],['-O2']):
                run_case(path,work/name,'ok',flags);count+=1;print('PASS',name,*flags,flush=True)
        path=work/'io.zeph';path.write_text(IO)
        environment=dict(os.environ,ZEPHYR_MAC_TEST='native value');environment.pop('ZEPHYR_MAC_TEST_ABSENT',None)
        run_case(path,work/'io','ok',arguments=[str(work/'data file.txt'),str(work),'','two words','café'],stdin='first\nsecond\n',env=environment)
        count+=1;print('PASS files, directory, stdin, environment, clock and arguments',flush=True)
        for name in ['optionals','moves','borrow_roots','global_references','match_bindings','scoped_borrows','map_regression','numeric_codegen','math_fns','macos_axpy','macos_loops']:
            source=ROOT/'tests'/f'{name}.zeph'
            baseline=run_case(source,work/name)
            optimized=run_case(source,work/name,flags=['-O2'])
            assert baseline==optimized,f'{name}: optimization changed output'
            if name=='numeric_codegen': assert baseline.strip()=='signed 0\nfloat 0\nnearMiss 0',repr(baseline)
            count+=2;print('PASS',name,'baseline/-O2 parity',flush=True)
        # Fast range guards must retain the scalar panic when either list is
        # short, the offset is negative, or signed index arithmetic wraps.
        for name,arguments in [
            ('short-output','zeros(5), zeros(8), 0, 0, 0, 6, 2'),
            ('short-input','zeros(8), zeros(5), 0, 0, 0, 6, 2'),
            ('negative-offset','zeros(8), zeros(8), -1, 0, 0, 6, 2'),
            ('overflow-offset','zeros(8), zeros(8), 9223372036854775807, 0, 1, 5, 2'),
        ]:
            path=work/f'axpy-{name}.zeph'
            path.write_text('fn axpy(output: [int], input: [int], a: int, b: int, lo: int, hi: int, factor: int) {\n'
                            '    for j in lo..hi { output[a + j] += factor * input[b + j] }\n}\n'
                            f'axpy({arguments})\n')
            for flags in ([],['-O2']):
                run_case(path,work/f'axpy-{name}',flags=flags,panic='bounds');count+=1
            print('PASS axpy',name,'bounds panic baseline/-O2',flush=True)
        for name,lo,hi in [('short-list',0,6),('negative-index',-1,4),('oversized-range',0,9223372036854775807)]:
            path=work/f'reduce-{name}.zeph'
            path.write_text('fn weighted(values: [int], lo: int, hi: int) -> int {\n'
                            '    var sum = 0\n    for i in lo..hi { sum += values[i] * i }\n    return sum\n}\n'
                            f'print(weighted([1, 2, 3, 4, 5], {lo}, {hi}))\n')
            for flags in ([],['-O2']):
                run_case(path,work/f'reduce-{name}',flags=flags,panic='bounds');count+=1
            print('PASS reduction',name,'bounds panic baseline/-O2',flush=True)
        source=ROOT/'tests/fill_loops.zeph'
        baseline=run_case(source,work/'fill',panic='bounds')
        optimized=run_case(source,work/'fill',flags=['-O2'],panic='bounds')
        assert baseline==optimized and 'unreachable' not in baseline
        count+=2;print('PASS fill-loop bounds panic baseline/-O2 parity',flush=True)
        for source in sorted((ROOT/'tests/regression').glob('*.zeph')):
            run_case(source,work/source.stem);count+=1;print('PASS',source.name,flush=True)
        bad=work/'bad.zeph';bad.write_text('let value: int = "wrong"\n')
        result=subprocess.run([str(ROOT/'zc'),str(bad),str(work/'must-not-exist')],capture_output=True,text=True)
        assert result.returncode!=0 and not (work/'must-not-exist').exists()
        count+=1;print('PASS compile error does not produce output',flush=True)
        panic=work/'panic.zeph';panic.write_text('var values = [1]\nprint(values[5])\n')
        driver.build(panic,work/'panic')
        result=subprocess.run([str(work/'panic')],capture_output=True,text=True)
        assert result.returncode!=0 and 'bounds' in result.stderr
        count+=1;print('PASS bounds panic',flush=True)
        result=subprocess.run([str(ROOT/'zc'),'run',str(ROOT/'tests/fixtures/basics/hello.zeph')],capture_output=True,text=True,timeout=60,cwd=work)
        assert result.returncode==0 and result.stdout.strip()=='Hello, Zephyr!'
        count+=1;print('PASS run from outside the checkout',flush=True)
    print(f'{count} native ARM64 checks passed.')

if __name__=='__main__': main()
