"""Native ARM64 in-memory execution with feedback-directed function tiering.

Clang is used as an assembler, never to link a guest executable. We relocate
its Mach-O objects into MAP_JIT memory ourselves. Stable function entry stubs
keep closures/vtables valid while future invocations move to the optimized
tier. Existing frames finish in their original code; both tiers share globals.
"""
import ctypes
import hashlib
import json
import re
import resource
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .arm64 import Arm64

CAPACITY = 64 * 1024 * 1024
BODY = '_jit_body'


def align(value, alignment):
    return (value + alignment - 1) & -alignment


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


class JitError(ValueError):
    pass


def source_versions(root, compiler, source):
    # Recompilation must observe the same program as the initial compile.
    # Track disk imports recursively and the shipped runtime/library sources;
    # embedded imports are protected by the compiler seed's own hash.
    versions = {}
    pending = [source, compiler, root/'compiler/runtime.zeph', *sorted((root/'lib').rglob('*.zeph'))]
    while pending:
        path = pending.pop().resolve()
        if path in versions or not path.is_file():
            continue
        content = path.read_bytes()
        versions[path] = hashlib.sha256(content).digest()
        if path.suffix != '.zeph':
            continue
        for match in re.finditer(r'\bimport\s+("(?:[^"\\]|\\.)*")', content.decode()):
            try:
                name = json.loads(match[1])
            except ValueError:
                raise JitError('Cannot safely track an escaped import path for JIT recompilation')
            candidates = [path.parent/name, root/name, root/'lib'/name]
            for candidate in candidates:
                if candidate.is_file():
                    pending.append(candidate)
                    break
                # A new relative file could shadow a shipped/embedded import.
                versions.setdefault(candidate.resolve(), None)
    return versions


def check_versions(versions):
    for path, expected in versions.items():
        changed = path.exists() if expected is None else not path.is_file() or hashlib.sha256(path.read_bytes()).digest() != expected
        if changed:
            raise JitError(f'Source or compiler changed during JIT execution: {path}')


class Object:
    """The small, validated Mach-O vocabulary emitted by our ARM64 assembler."""
    def __init__(self, path):
        self.bytes = Path(path).read_bytes()
        self.sections = []
        self.symbols = []
        header = self.unpack('<8I', 0)
        if header[:4] != (0xfeedfacf, 0x100000c, 0, 1):
            raise JitError('JIT requires an ARM64 Mach-O object')
        offset = 32
        symtab = None
        for _ in range(header[4]):
            command, size = self.unpack('<II', offset)
            if size < 8 or offset + size > len(self.bytes):
                raise JitError('Malformed Mach-O command')
            if command == 0x19:
                count = self.unpack('<I', offset + 64)[0]
                for index in range(count):
                    values = self.unpack('<16s16sQQ8I', offset + 72 + index * 80)
                    name, segment, address, length, file_offset, power, reloc, nreloc, flags, *_ = values
                    name = name.rstrip(b'\0').decode()
                    if name not in ('__text', '__data') or power > 20:
                        raise JitError(f'Unsupported JIT section {name}')
                    self.sections.append(dict(name=name, address=address, size=length,
                                              offset=file_offset, align=1 << power,
                                              reloc=reloc, nreloc=nreloc))
            elif command == 2:
                symtab = self.unpack('<4I', offset + 8)
            elif command not in (0xb, 0x32, 0x24, 0x25, 0x26):
                raise JitError(f'Unsupported Mach-O command {command}')
            offset += size
        if not symtab:
            raise JitError('Missing JIT symbol table')
        start, count, strings, string_size = symtab
        names = self.read(strings, string_size)
        for index in range(count):
            name_offset, kind, section, description, value = self.unpack('<IBBHQ', start + index * 16)
            if name_offset >= len(names):
                raise JitError('Invalid JIT symbol name')
            name = names[name_offset:].split(b'\0', 1)[0].decode()
            if kind & 0xe0 or kind & 0xe not in (0, 0xe):
                raise JitError(f'Unsupported JIT symbol {name}')
            self.symbols.append(dict(name=name, section=section, value=value))

    def read(self, offset, size):
        if offset < 0 or size < 0 or offset + size > len(self.bytes):
            raise JitError('Truncated Mach-O object')
        return self.bytes[offset:offset + size]

    def unpack(self, fmt, offset):
        return struct.unpack(fmt, self.read(offset, struct.calcsize(fmt)))


class Arena:
    def __init__(self, native):
        self.native = native
        self.code = native.zephyr_jit_open(CAPACITY)
        self.data = native.zephyr_jit_data()
        self.code_used = self.data_used = 0
        if not self.code or not self.data:
            raise JitError('Cannot allocate native MAP_JIT memory (check the host JIT entitlement)')

    def allocate(self, size, alignment, code=False):
        attribute = 'code_used' if code else 'data_used'
        offset = align(getattr(self, attribute), alignment)
        if offset + size > CAPACITY:
            raise JitError('JIT arena exhausted')
        setattr(self, attribute, offset + size)
        return (self.code if code else self.data) + offset

    def write(self, address, data, code=False):
        if code:
            if not self.native.zephyr_jit_publish(address - self.code, data, len(data)):
                raise JitError('Cannot publish JIT code')
        else:
            ctypes.memmove(address, data, len(data))

    def load(self, obj, externals, shared=None):
        shared = shared or {}
        sections = []
        for section in obj.sections:
            code = section['name'] == '__text'
            address = self.allocate(section['size'], max(16, section['align']), code)
            sections.append((address, bytearray(obj.read(section['offset'], section['size'])), code))
        symbols = {}
        addresses = []
        for symbol in obj.symbols:
            name = symbol['name']
            section = symbol['section']
            if section:
                if section > len(sections):
                    raise JitError('Invalid JIT symbol section')
                original = obj.sections[section - 1]
                offset = symbol['value'] - original['address']
                if not 0 <= offset <= original['size']:
                    raise JitError('Invalid JIT symbol offset')
                address = shared.get(name, sections[section - 1][0] + offset)
                symbols[name] = address
            else:
                address = externals.get(name)
                if address is None:
                    raise JitError(f'Unresolved native JIT symbol {name}')
            addresses.append(address)
        veneers = {}
        for section, (base, content, code) in zip(obj.sections, sections):
            addend = None
            for index in range(section['nreloc']):
                offset, info = obj.unpack('<iI', section['reloc'] + 8 * index)
                number, relative, length, external, kind = info & 0xffffff, (info >> 24) & 1, (info >> 25) & 3, (info >> 27) & 1, info >> 28
                if kind == 10:
                    if addend is not None:
                        raise JitError('Malformed ARM64 addend pair')
                    addend = signed(number, 24)
                    continue
                width = 1 << length
                if offset < 0 or offset + width > len(content):
                    raise JitError('Invalid ARM64 relocation offset')
                if external:
                    if number >= len(addresses):
                        raise JitError('Invalid ARM64 relocation symbol')
                    target = addresses[number]
                elif 0 < number <= len(sections):
                    target = sections[number - 1][0] - obj.sections[number - 1]['address']
                else:
                    raise JitError('Unsupported ARM64 local relocation')
                target += addend or 0
                addend = None
                word = int.from_bytes(content[offset:offset + width], 'little')
                pc = base + offset
                if kind == 0 and length == 3 and not relative:
                    word = (target + word) & ((1 << 64) - 1)
                elif kind == 2 and length == 2 and relative:
                    target += signed(word & 0x3ffffff, 26) * 4
                    delta = target - pc
                    if delta % 4:
                        raise JitError('Unaligned ARM64 branch')
                    if not -(1 << 27) <= delta < (1 << 27):
                        if target not in veneers:
                            veneer = self.allocate(16, 8, True)
                            self.write(veneer, struct.pack('<IIQ', 0x58000050, 0xd61f0200, target), True)
                            veneers[target] = veneer
                        delta = veneers[target] - pc
                    if not -(1 << 27) <= delta < (1 << 27):
                        raise JitError('ARM64 branch exceeds arena range')
                    word = (word & 0xfc000000) | ((delta // 4) & 0x3ffffff)
                elif kind == 3 and length == 2 and relative:
                    delta = ((target & -4096) - (pc & -4096)) // 4096
                    if not -(1 << 20) <= delta < (1 << 20):
                        raise JitError('ARM64 data is outside ADRP range')
                    word = (word & ~((3 << 29) | (0x7ffff << 5))) | ((delta & 3) << 29) | (((delta >> 2) & 0x7ffff) << 5)
                elif kind == 4 and length == 2 and not relative:
                    # ADD immediate has byte offsets; unsigned LDR/STR scales
                    # by operand size, with the extra SIMD Q bit adding 16B.
                    scale = 0
                    if word & 0x3b000000 == 0x39000000:
                        scale = (word >> 30) & 3
                        if word & 0x04000000 and word & 0x00800000:
                            scale = 4
                    displacement = target & 4095
                    if displacement % (1 << scale):
                        raise JitError('Unaligned ARM64 PAGEOFF load')
                    word = (word & ~(0xfff << 10)) | ((displacement >> scale) << 10)
                else:
                    raise JitError(f'Unsupported ARM64 relocation {kind}')
                content[offset:offset + width] = word.to_bytes(width, 'little')
            if addend is not None:
                raise JitError('Unpaired ARM64 relocation addend')
            self.write(base, bytes(content), code)
        return symbols


def assemble(text, work, name):
    source, output = work / f'{name}.s', work / f'{name}.o'
    source.write_text(text)
    subprocess.run(['clang', '-arch', 'arm64', '-mmacosx-version-min=13.0', '-c', str(source), '-o', str(output)], check=True)
    return Object(output)


def separate_entries(assembly, names):
    # Make references to stable entries external so the assembler cannot bind
    # recursive calls or closure addresses directly to a replaceable body.
    result = []
    for line in assembly.splitlines():
        if line.endswith(':') and line[:-1] in names:
            name = line[:-1]
            result.extend([f'.globl {BODY + name}', BODY + name + ':'])
        elif line.startswith('.globl ') and line[7:] in names:
            continue
        else:
            result.append(line)
    return '\n'.join(result) + '\n'


def hot_module(assembly, selected, original_entries):
    """Keep the hot body and its outlined loops, not copies of cold code."""
    text, data = assembly.split('.data', 1)
    lines = ['.text']
    include = False
    for line in text.splitlines():
        if line.endswith(':') and line.startswith('_'):
            name = line[:-1]
            include = name == selected or name not in original_entries
        if include:
            lines.append(line)
    # Constants and ownership descriptors belong to this generation. Only the
    # mutable global array is rebound to the original image by the linker.
    return '\n'.join(lines) + '\n.data' + data


def stubs(names, threshold):
    lines = ['.text']
    for index, name in enumerate(names):
        lines.extend([f'.globl {name}', '.p2align 2', name + ':',
                      f'adrp x16, _jit_state{index}@PAGE', f'add x16, x16, _jit_state{index}@PAGEOFF',
                      'ldr x17, [x16, #8]', f'cbz x17, Ldispatch{index}',
                      'sub x17, x17, #1', 'str x17, [x16, #8]', f'cbnz x17, Ldispatch{index}',
                      # No guest register, return address or NZCV changes at
                      # the callback boundary, including float/closure args.
                      'sub sp, sp, #416', 'stp x30, x28, [sp, #384]', 'mrs x17, nzcv', 'str x17, [sp, #400]'])
        for register in range(0, 16, 2):
            lines.append(f'stp x{register}, x{register+1}, [sp, #{register*8}]')
        for register in range(0, 16, 2):
            lines.append(f'stp q{register}, q{register+1}, [sp, #{128+register*16}]')
        lines.extend([f'mov x0, #{index}', 'bl _jit_hot'])
        for register in range(0, 16, 2):
            lines.append(f'ldp q{register}, q{register+1}, [sp, #{128+register*16}]')
        for register in range(0, 16, 2):
            lines.append(f'ldp x{register}, x{register+1}, [sp, #{register*8}]')
        lines.extend(['ldr x17, [sp, #400]', 'msr nzcv, x17', 'ldp x30, x28, [sp, #384]', 'add sp, sp, #416',
                      f'adrp x16, _jit_state{index}@PAGE', f'add x16, x16, _jit_state{index}@PAGEOFF',
                      f'Ldispatch{index}:', 'ldr x16, [x16]', 'br x16'])
    lines.append('.data')
    for index in range(len(names)):
        lines.extend(['.balign 8', f'_jit_state{index}:', f'.quad 0, {threshold}'])
    return '\n'.join(lines) + '\n'


def native_library(root, work):
    directory = root / 'bootstrap/macos'
    library = work / 'native.dylib'
    subprocess.run(['clang', '-arch', 'arm64', '-mmacosx-version-min=13.0', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-dynamiclib', str(directory/'darwin.c'), str(directory/'jit.c'), str(directory/'jit-entry.s'),
                    '-o', str(library)], check=True)
    native = ctypes.CDLL(str(library))
    native.zephyr_jit_open.argtypes = [ctypes.c_size_t]
    native.zephyr_jit_open.restype = ctypes.c_void_p
    native.zephyr_jit_data.restype = ctypes.c_void_p
    native.zephyr_jit_publish.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    native.zephyr_jit_execute.argtypes = [ctypes.c_void_p]
    native.zephyr_jit_execute.restype = ctypes.c_int
    native.zephyr_jit_close.restype = None
    native.zephyr_macos_init.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p), ctypes.c_char_p]
    native.zephyr_macos_init.restype = None
    return native


def run(root, compiler, source, flags, arguments, threshold=1000, report=None, adaptive=True):
    started = time.perf_counter()
    source = Path(source).resolve()
    if not source.is_file():
        raise JitError(f'Source file does not exist: {source}')
    if not 1 <= threshold <= (1 << 63)-1:
        raise JitError('JIT threshold must be between 1 and 9223372036854775807')
    if report and Path(report).resolve() in (source, Path(compiler).resolve()):
        raise JitError('The JIT report must not replace the source file or compiler')
    guest_args = [str(source), *arguments]
    versions = source_versions(root, compiler, source)
    if report and Path(report).resolve() in versions:
        raise JitError('The JIT report must not replace a compiler input')
    if any('"' in value for value in guest_args):
        raise JitError('Literal double quotes in arguments are not supported by the runtime parser')
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    wanted = min(64*1024*1024, hard) if hard != resource.RLIM_INFINITY else 64*1024*1024
    if soft < wanted:
        try:
            resource.setrlimit(resource.RLIMIT_STACK, (wanted, hard))
        except (OSError, ValueError):
            pass  # Darwin can enforce a lower stack ceiling than getrlimit.
    stats = dict(mode='native-arm64-jit', adaptive=adaptive and '-O2' not in flags,
                 threshold=threshold, promotions=[], errors=[])
    with tempfile.TemporaryDirectory(prefix='zephyr-jit-') as directory:
        work = Path(directory)
        native = native_library(root, work)
        arena = Arena(native)
        try:
            def compile_tier(name, tier_flags):
                ir = work / f'{name}-ir.s'
                subprocess.run([str(compiler), '--macos-ir', '--rt', *tier_flags, str(source), str(ir)], check=True)
                return Arm64().lower(ir.read_text())

            assembly = compile_tier('baseline', flags)
            check_versions(versions)
            text = assembly.split('.data', 1)[0]
            entries = re.findall(r'^(_[A-Za-z0-9_.$]+):$', text, re.M)
            users = [name for name in entries if name.startswith('_lm_')]
            externals = {}
            for name in re.findall(r'\b(_darwin_\w+)\b', assembly):
                externals[name] = ctypes.cast(getattr(native, name[1:]), ctypes.c_void_p).value
            callback_type = ctypes.CFUNCTYPE(None, ctypes.c_uint64)
            states = {}
            baseline = {}
            stopped_counts = {}

            @callback_type
            def hot(index):
                begin = time.perf_counter()
                # Exceptions cannot unwind a ctypes callback into a native
                # frame. Failed optimization leaves the valid baseline live.
                try:
                    name = users[index]
                    check_versions(versions)
                    optimized_assembly = compile_tier(f'optimized{index}', [*flags, '--jit-hot', name[1:]])
                    check_versions(versions)
                    optimized_entries = re.findall(r'^(_[A-Za-z0-9_.$]+):$', optimized_assembly.split('.data',1)[0], re.M)
                    missing = set(entries) - set(optimized_entries)
                    if missing:
                        raise JitError(f'Tier changed function identities: {sorted(missing)}')
                    def globals_size(code):
                        match = re.search(r'^___zephyr_globals:\n\.space (\d+)$', code, re.M)
                        return int(match[1]) if match else 0
                    if globals_size(optimized_assembly) != globals_size(assembly):
                        raise JitError('Tier changed the shared globals layout')
                    module = hot_module(optimized_assembly, name, entries)
                    optimized = arena.load(assemble(separate_entries(module, [name]), work, f'optimized{index}'),
                                           externals, {'___zephyr_globals': baseline['___zephyr_globals']} if '___zephyr_globals' in baseline else {})
                    elapsed = (time.perf_counter()-begin)*1000
                    stats['optimization_ms'] = stats.get('optimization_ms', 0) + elapsed
                    target = optimized[BODY + name]
                    ctypes.c_uint64.from_address(states[name]).value = target
                    stats['promotions'].append(dict(function=name.removeprefix('_lm_'), calls=threshold,
                                                    baseline=baseline[BODY+name], optimized=target, compilation_ms=elapsed))
                except Exception as error:
                    stats['failed_optimization_ms'] = stats.get('failed_optimization_ms', 0) + (time.perf_counter()-begin)*1000
                    stats['errors'].append(str(error))
                    stats['profiling_stopped'] = True
                    print(f'zc JIT: optimization failed; continuing in baseline: {error}', file=sys.stderr)
                    for entry, state in states.items():
                        stopped_counts[entry] = ctypes.c_uint64.from_address(state+8).value
                        ctypes.c_uint64.from_address(state+8).value = 0

            externals['_jit_hot'] = ctypes.cast(hot, ctypes.c_void_p).value
            stub_symbols = arena.load(assemble(stubs(users, threshold if stats['adaptive'] else 0), work, 'entries'), externals)
            for index, name in enumerate(users):
                states[name] = stub_symbols[f'_jit_state{index}']
                externals[name] = stub_symbols[name]
            # Native runtime/main entries are not profiled or replaced. Bind
            # them to their bodies after first reserving the object's symbols.
            obj = assemble(separate_entries(assembly, users), work, 'baseline')
            baseline = arena.load(obj, externals)
            for name in entries:
                if name not in users:
                    externals[name] = baseline[name]
            for name, state in states.items():
                ctypes.c_uint64.from_address(state).value = baseline[BODY+name]
            stats['startup_ms'] = (time.perf_counter()-started)*1000
            argv = (ctypes.c_char_p * len(guest_args))(*(value.encode() for value in guest_args))
            native.zephyr_macos_init(len(guest_args), argv, str(compiler).encode())
            sys.stdout.flush()
            guest_started = time.perf_counter()
            stats['exit_code'] = native.zephyr_jit_execute(baseline['_zephyrMain'])
            stats['guest_ms'] = (time.perf_counter()-guest_started)*1000
            stats['execution_excluding_compilation_ms'] = stats['guest_ms'] - stats.get('optimization_ms', 0) - stats.get('failed_optimization_ms', 0)
            stats['functions'] = [dict(function=name.removeprefix('_lm_'),
                                       calls_before_promotion=(threshold-stopped_counts.get(name, ctypes.c_uint64.from_address(state+8).value)) if stats['adaptive'] else None,
                                       promoted=any(item['function']==name.removeprefix('_lm_') for item in stats['promotions']))
                                  for name, state in states.items()]
            stats['code_bytes'] = arena.code_used
            stats['data_bytes'] = arena.data_used
            stats['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            stats['total_ms'] = (time.perf_counter()-started)*1000
            if report:
                Path(report).write_text(json.dumps(stats, indent=2)+'\n')
            return stats
        finally:
            native.zephyr_jit_close()
