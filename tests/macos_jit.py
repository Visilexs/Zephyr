#!/usr/bin/env python3
"""Execute native JIT transitions and compare their behavior with native AOT."""
import importlib.util
import ctypes
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def execute(source, report, flags=(), arguments=(), stdin='', env=None, cwd=None):
    result = subprocess.run([str(ROOT/'zc'), 'run', '--jit-report', str(report), *flags, str(source), *arguments],
                            input=stdin, capture_output=True, text=True, timeout=240, env=env, cwd=cwd)
    stats = json.loads(report.read_text()) if report.exists() else None
    return result, stats


def main():
    count = 0
    with tempfile.TemporaryDirectory(prefix='zephyr jit tests ') as directory:
        work = Path(directory)
        report = work/'profile.json'
        source = ROOT/'tests/macos_jit.zeph'
        for flags in (['--jit-baseline'], ['-O2'], ['--jit-threshold', '4']):
            result, stats = execute(source, report, flags)
            assert result.returncode == 0 and result.stdout.strip() == 'jit ok', (result.returncode, result.stdout, result.stderr)
            assert stats and not stats['errors'], stats
            if stats['adaptive']:
                promoted = stats['promotions']
                assert any(item['function'] == 'fib' for item in promoted), stats
                assert any(item['function'] == 'wide' for item in promoted), stats
                assert any(item['function'] == 'floating' for item in promoted), stats
                assert all(item['baseline'] != item['optimized'] and item['calls'] == 4 for item in promoted), stats
            else:
                assert not stats['promotions']
                assert all(item['calls_before_promotion'] is None for item in stats['functions'])
            count += 1
            print('PASS JIT recursion, closures, stack/float args, globals, interfaces', *flags, flush=True)

        # Original regression fixtures exercise borrowed roots and descriptors
        # that move between independently linked compiler generations.
        for name in ('global_references', 'borrow_roots', 'moves', 'numeric_codegen', 'macos_axpy', 'macos_loops', 'oop'):
            source = ROOT/'tests/fixtures/basics/oop.zeph' if name == 'oop' else ROOT/'tests'/f'{name}.zeph'
            executable = work/name
            subprocess.run([str(ROOT/'zc'), '-O2', str(source), str(executable)], check=True, capture_output=True)
            expected = subprocess.run([str(executable)], check=True, capture_output=True, text=True).stdout
            result, stats = execute(source, report, ['--jit-threshold', '4'])
            assert result.returncode == 0 and result.stdout == expected, (name, result.returncode, result.stdout, result.stderr)
            assert not stats['errors'], stats
            count += 1
            print('PASS original fixture JIT/AOT parity', name, flush=True)

        # Make the first optimization fail, without invalidating live frames.
        script = work/'failure.py'
        script.write_text('''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + '/scripts')
from macos import jit
original = jit.assemble
def fail(text, work, name):
    if name.startswith('optimized'): raise jit.JitError('injected optimization failure')
    return original(text, work, name)
jit.assemble = fail
root = Path(sys.argv[1])
stats = jit.run(root, root/'zc-macos', root/'tests/macos_jit.zeph', [], [], threshold=4, report=sys.argv[2])
assert stats['errors'] == ['injected optimization failure']
assert not stats['promotions'] and stats['exit_code'] == 0
assert stats['profiling_stopped']
assert any(item['function'] == 'wide' and item['calls_before_promotion'] == 0 for item in stats['functions'])
''')
        result = subprocess.run([sys.executable, str(script), str(ROOT), str(report)], capture_output=True, text=True, timeout=120)
        assert result.returncode == 0 and result.stdout.strip() == 'jit ok', (result.stdout, result.stderr)
        count += 1
        print('PASS failed optimization preserves baseline execution', flush=True)

        changed = work/'changed.zeph'
        changed.write_text((ROOT/'tests/macos_jit.zeph').read_text())
        script.write_text('''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + '/scripts')
from macos import jit
original = jit.assemble
def change(text, work, name):
    obj = original(text, work, name)
    if name == 'baseline': Path(sys.argv[3]).write_text('panic("changed program")\\n')
    return obj
jit.assemble = change
root = Path(sys.argv[1])
stats = jit.run(root, root/'zc-macos', Path(sys.argv[3]), [], [], threshold=4, report=sys.argv[2])
assert len(stats['errors']) == 1 and 'changed during JIT execution' in stats['errors'][0]
assert not stats['promotions'] and stats['exit_code'] == 0
''')
        result = subprocess.run([sys.executable, str(script), str(ROOT), str(report), str(changed)], capture_output=True, text=True, timeout=120)
        assert result.returncode == 0 and result.stdout.strip() == 'jit ok', (result.stdout, result.stderr)
        count += 1
        print('PASS source changes cannot replace the running program', flush=True)

        cold = work/'cold.zeph'
        cold.write_text('fn cold(n: int) -> int { var sum = 0\nfor i in 0..n { sum += i }\nreturn sum }\nassert(cold(20) == 190)\nprint("cold ok")\n')
        result, stats = execute(cold, report, ['--jit-threshold','10'])
        assert result.returncode == 0 and result.stdout.strip() == 'cold ok', result.stderr
        assert not stats['promotions'] and 'optimization_ms' not in stats, stats
        assert any(item['function'] == 'cold' and item['calls_before_promotion'] == 1 for item in stats['functions']), stats
        count += 1
        print('PASS cold function is not optimized', flush=True)

        # Run the same native I/O fixture used by the original Mac suite.
        spec = importlib.util.spec_from_file_location('macos_tests', ROOT/'tests/macos_tests.py')
        tests = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tests)
        io = work/'io.zeph'
        io.write_text(tests.IO)
        environment = dict(os.environ, ZEPHYR_MAC_TEST='native value')
        environment.pop('ZEPHYR_MAC_TEST_ABSENT', None)
        result, stats = execute(io, report, arguments=[str(work/'data file.txt'), str(work), '', 'two words', 'café'],
                                stdin='first\nsecond\n', env=environment, cwd=work)
        assert result.returncode == 0 and result.stdout.strip() == 'ok' and not stats['errors'], result.stderr
        count += 1
        print('PASS JIT files, subprocesses, stdin, environment and arguments', flush=True)

        panic = work/'panic.zeph'
        panic.write_text('fn check(n: int) -> int { let data = [1, 2, 3]\nreturn data[n] }\nfor i in 0..8 { print(check(i % 3)) }\nprint(check(9))\n')
        result, stats = execute(panic, report, ['--jit-threshold','4'])
        assert result.returncode != 0 and 'bounds' in result.stderr, result.stderr
        assert stats['exit_code'] != 0 and not stats['errors'], stats
        assert stats['promotions'], stats
        count += 1
        print('PASS optimized guest panic returns exit status and writes profile', flush=True)

        exiting = work/'exit.zeph'
        exiting.write_text('let ignored = win("ExitProcess", 42)\nprint("unreachable")\n')
        result, stats = execute(exiting, report)
        assert result.returncode == 42 and stats['exit_code'] == 42 and 'unreachable' not in result.stdout, (result.returncode, result.stdout, stats)
        count += 1
        print('PASS explicit guest exit status preserved', flush=True)

        bad = work/'bad.zeph'
        bad.write_text('let value: int = "wrong"\n')
        report.unlink()
        result, stats = execute(bad, report)
        assert result.returncode != 0 and stats is None
        count += 1
        print('PASS JIT compile failure', flush=True)

        # Independent ARM64 assembler fixtures verify the relocator rather than
        # mirroring the selector. libc supplies a genuinely distant branch.
        sys.path.insert(0, str(ROOT/'scripts'))
        from macos import jit
        native = jit.native_library(ROOT, work)
        arena = jit.Arena(native)
        try:
            obj = jit.assemble('''
.text
.globl _probe_page
_probe_page:
    adrp x1, _numbers@PAGE+4104
    ldr x0, [x1, _numbers@PAGEOFF+4104]
    ret
.globl _probe_float
_probe_float:
    adrp x1, _double@PAGE
    ldr d0, [x1, _double@PAGEOFF]
    fmov x0, d0
    ret
.globl _probe_veneer
_probe_veneer:
    stp x29, x30, [sp, #-16]!
    adrp x0, _text@PAGE
    add x0, x0, _text@PAGEOFF
    bl _strlen
    ldp x29, x30, [sp], #16
    ret
.data
.balign 8
_numbers:
    .quad 13, 29
    .space 4088
    .quad 73
_double:
    .double 4.25
_pointer:
    .quad _probe_page+4
_text:
    .asciz "native"
''', work, 'relocations')
            libc = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
            symbols = arena.load(obj, {'_strlen': ctypes.cast(libc.strlen, ctypes.c_void_p).value})
            assert ctypes.CFUNCTYPE(ctypes.c_uint64)(symbols['_probe_page'])() == 73
            assert ctypes.CFUNCTYPE(ctypes.c_uint64)(symbols['_probe_float'])() == struct.unpack('<Q', struct.pack('<d',4.25))[0]
            assert ctypes.CFUNCTYPE(ctypes.c_uint64)(symbols['_probe_veneer'])() == 6
            assert ctypes.c_uint64.from_address(symbols['_pointer']).value == symbols['_probe_page']+4
            count += 1
            print('PASS native branch veneers, paired addends, page loads and pointers', flush=True)
            # Reject an unsupported relocation before any new code is entered.
            data = bytearray(obj.bytes)
            relocation = next(section['reloc'] for section in obj.sections if section['nreloc'])
            info = struct.unpack_from('<I',data,relocation+4)[0]
            struct.pack_into('<I',data,relocation+4,(info & 0x0fffffff) | (15 << 28))
            obj.bytes = bytes(data)
            try:
                arena.load(obj, {'_strlen': ctypes.cast(libc.strlen, ctypes.c_void_p).value})
            except jit.JitError:
                pass
            else:
                raise AssertionError('Unsupported relocation was accepted')
            count += 1
            print('PASS unsupported relocation rejected', flush=True)
        finally:
            native.zephyr_jit_close()
    print(f'{count} native ARM64 JIT checks passed.')


if __name__ == '__main__':
    main()
