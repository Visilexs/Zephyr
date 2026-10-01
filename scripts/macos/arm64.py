"""Lower Zephyr's assembly IR and native loop operations to AArch64 Mach-O.

The existing frontend emits an Intel-shaped instruction IR. This pass selects
ARM64 instructions at build time; generated executables contain ARM64 code only.
Raw x86 vector/OS operations fail explicitly rather than emitting x86.
"""
import re
import struct
from pathlib import Path

REG = dict(zip('rax rcx rdx rbx rsp rbp rsi rdi r8 r9 r10 r11 r12 r13 r14 r15'.split(),
               'x9 x10 x11 x19 x28 x29 x20 x21 x12 x13 x14 x15 x22 x23 x24 x25'.split()))
ALIASES = {}
for name, reg in REG.items():
    short = {'rax': 'eax ax al', 'rcx': 'ecx cx cl', 'rdx': 'edx dx dl', 'rbx': 'ebx bx bl',
             'rsp': 'esp sp spl', 'rbp': 'ebp bp bpl', 'rsi': 'esi si sil', 'rdi': 'edi di dil'}.get(name, f'{name}d {name}w {name}b')
    for alias, width in zip(short.split(), [32, 16, 8]): ALIASES[alias] = (reg, width)
COND = {'e': 'eq', 'z': 'eq', 'ne': 'ne', 'nz': 'ne', 'l': 'lt', 'le': 'le', 'g': 'gt', 'ge': 'ge',
        'b': 'lo', 'be': 'ls', 'a': 'hi', 'ae': 'hs', 's': 'mi', 'ns': 'pl', 'p': 'vs', 'np': 'vc'}
INVERSE = {'eq':'ne','ne':'eq','lt':'ge','ge':'lt','gt':'le','le':'gt','lo':'hs','hs':'lo','hi':'ls','ls':'hi','mi':'pl','pl':'mi','vs':'vc','vc':'vs'}
# Exactly the 256 values representable by an AArch64 double FMOV immediate.
FLOAT_IMMEDIATES={int.from_bytes(struct.pack('>d',sign*(1+fraction/16)*2**exponent),'big'):
                  repr(sign*(1+fraction/16)*2**exponent)
                  for sign in (1,-1) for fraction in range(16) for exponent in range(-3,5)}
# Native C platform functions take ordinary Darwin AArch64 arguments.
ARITY = dict(VirtualAlloc=4,VirtualProtect=4,GetStdHandle=1,WriteFile=5,ReadFile=5,
             CreateFileA=7,GetFileSize=2,CloseHandle=1,ExitProcess=1,GetCommandLineA=0,
             GetModuleFileNameA=3,GetFileAttributesA=1,GetFullPathNameA=4,
             InitializeCriticalSection=1,EnterCriticalSection=1,LeaveCriticalSection=1,TryEnterCriticalSection=1,
             GetCurrentThreadId=0,GetCurrentThreadStackLimits=2,TlsAlloc=0,TlsSetValue=2,TlsGetValue=1,
             GetCurrentProcess=0,FlushInstructionCache=3,LoadLibraryA=1,GetProcAddress=2,
             SuspendThread=1,ResumeThread=1,GetThreadContext=2,CreateThread=6,GetSystemInfo=1,VirtualFree=3,
             SetLastError=1,GetLastError=0,DeleteFileA=1,GetEnvironmentVariableA=3,
             GetTickCount64=0,QueryPerformanceCounter=1,QueryPerformanceFrequency=1,Sleep=1,
             FindFirstFileA=2,FindNextFileA=2,FindClose=1,CreateProcessA=10,WaitForSingleObject=2,GetExitCodeProcess=2,UnsupportedNativeInterop=0)

class LoweringError(ValueError): pass

class Arm64:
    def __init__(self): self.lines=[]; self.serial=0; self.imports=set(); self.float_flags=False; self.text=False; self.float_constants={}
    def emit(self,*lines): self.lines.extend(lines)
    def imm(self, reg, n):
        n=int(n,0) if isinstance(n,str) else n; n &= (1<<64)-1
        self.emit(f'movz {reg}, #{n&65535}')
        for shift in (16,32,48):
            if (n>>shift)&65535:self.emit(f'movk {reg}, #{(n>>shift)&65535}, lsl #{shift}')
    def symbol(self,s): return 'L'+s[1:] if s.startswith('.') else '_'+s
    def sync(self): self.emit('and x16, x28, #0xfffffffffffffff0','mov sp, x16')
    def arithmetic_immediate(self,operand):
        try: value=int(operand,0)
        except ValueError: return None
        if 0<=value<=4095: return f'#{value}'
        if 0<=value<=4095*4096 and value%4096==0: return f'#{value//4096}, lsl #12'
        return None
    def logical_immediate(self,operand):
        try: value=int(operand,0)&((1<<64)-1)
        except ValueError: return None
        for size in (2,4,8,16,32,64):
            mask=(1<<size)-1;pattern=value&mask
            if pattern in (0,mask) or sum(pattern<<i for i in range(0,64,size))!=value: continue
            for shift in range(size):
                rotated=((pattern>>shift)|(pattern<<(size-shift)))&mask
                if rotated&(rotated+1)==0: return f'#{value}'
        return None
    def memory(self,operand,width):
        """Select native addressing modes without materializing a scratch address."""
        body=operand[operand.index('[')+1:operand.index(']')].replace(' ','')
        match=re.fullmatch(r'([a-z0-9]+)([+-](?:0x[0-9a-fA-F]+|[0-9]+))?',body)
        if match and match[1] in REG:
            offset=int(match[2],0) if match[2] else 0
            size=width//8
            if -256<=offset<=255 or (0<=offset<=4095*size and offset%size==0):
                return f'[{REG[match[1]]}, #{offset}]'
        match=re.fullmatch(r'([a-z0-9]+)\+([a-z0-9]+)(?:\*(1|2|4|8))?',body)
        if match and match[1] in REG and match[2] in REG:
            shift=int(match[3] or '1').bit_length()-1
            if shift in (0,(width//8).bit_length()-1):
                return f'[{REG[match[1]]}, {REG[match[2]]}, lsl #{shift}]'
        return None
    def addr(self,operand,out='x17'):
        body=operand[operand.index('[')+1:operand.index(']')].replace(' ','')
        terms=re.findall(r'[+-]?[^+-]+',body)
        initialized=False
        for term in terms:
            sign=-1 if term.startswith('-') else 1; term=term.lstrip('+-')
            if term=='rip':continue
            if '*' in term:
                reg,scale=term.split('*');shift=int(scale).bit_length()-1
                if not initialized and sign>0:self.emit(f'lsl {out}, {REG[reg]}, #{shift}')
                else:
                    if not initialized:self.imm(out,0)
                    self.emit(f'{"add" if sign>0 else "sub"} {out}, {out}, {REG[reg]}, lsl #{shift}')
            elif term in REG:
                if not initialized:self.emit(f'{"mov" if sign>0 else "neg"} {out}, {REG[term]}')
                else:self.emit(f'{"add" if sign>0 else "sub"} {out}, {out}, {REG[term]}')
            else:
                try:n=int(term,0)*sign
                except ValueError:
                    sym=self.symbol(term);scratch='x16' if initialized else out
                    self.emit(f'adrp {scratch}, {sym}@PAGE',f'add {scratch}, {scratch}, {sym}@PAGEOFF')
                    if initialized:self.emit(f'add {out}, {out}, {scratch}')
                    initialized=True;continue
                if not initialized:self.imm(out,n)
                elif n:
                    immediate=self.arithmetic_immediate(str(abs(n)))
                    if immediate:self.emit(f'{"add" if n>=0 else "sub"} {out}, {out}, {immediate}')
                    else:self.imm('x16',abs(n));self.emit(f'{"add" if n>=0 else "sub"} {out}, {out}, x16')
            initialized=True
        if not initialized:self.imm(out,0)
        return out
    def read_float(self,operand,destination):
        operand=operand.removeprefix('qword ptr ')
        if operand.startswith('xmm'):
            source='d'+operand[3:]
            if source!=destination:self.emit(f'fmov {destination}, {source}')
        elif '[' in operand:
            # Constant pools are eight-byte aligned, so a PAGEOFF load can
            # address them directly without an integer load and bit transfer.
            symbol=re.fullmatch(r'\[rip\s*\+\s*([A-Za-z_.][A-Za-z0-9_.]*)\]',operand)
            if symbol:
                bits=self.float_constants.get(symbol[1])
                if bits==0:self.emit(f'fmov {destination}, xzr')
                elif bits in FLOAT_IMMEDIATES:self.emit(f'fmov {destination}, #{FLOAT_IMMEDIATES[bits]}')
                else:
                    name=self.symbol(symbol[1]);self.emit(f'adrp x17, {name}@PAGE',f'ldr {destination}, [x17, {name}@PAGEOFF]')
            else:
                address=self.memory(operand,64) or f'[{self.addr(operand)}]'
                self.emit(f'ldr {destination}, {address}')
        else:self.emit(f'fmov {destination}, {self.read(operand)}')
    def read(self,o,out='x0'):
        o=o.strip()
        if o in REG:return REG[o]
        if o in ALIASES:
            reg,w=ALIASES[o];self.emit(f'ubfx {out}, {reg}, #0, #{w}');return out
        if o.startswith('xmm'):return 'd'+o[3:]
        if '[' in o:
            width=8 if 'byte ptr' in o else 16 if o.startswith('word ptr ') else 32 if 'dword ptr' in o else 64
            address=self.memory(o,width) or f'[{self.addr(o)}]'
            self.emit(f'{"ldrb" if width==8 else "ldrh" if width==16 else "ldr"} {out.replace("x","w",1) if width<64 else out}, {address}');return out
        try:self.imm(out,int(o,0));return out
        except ValueError:raise LoweringError(f'unsupported operand {o}')
    def write(self,o,value):
        o=o.strip()
        if o in REG:
            if REG[o]!=value:self.emit(f'mov {REG[o]}, {value}')
            if o=='rsp':self.sync()
        elif o in ALIASES:
            reg,w=ALIASES[o]
            if w==32:self.emit(f'mov {reg.replace("x","w",1)}, {value.replace("x","w",1)}')
            else:self.emit(f'bfi {reg}, {value}, #0, #{w}')
        elif o.startswith('xmm'):self.emit(f'fmov d{o[3:]}, {value}')
        elif '[' in o:
            width=8 if 'byte ptr' in o else 16 if o.startswith('word ptr ') else 32 if 'dword ptr' in o else 64
            address=self.memory(o,width) or f'[{self.addr(o)}]'
            self.emit(f'{"strb" if width==8 else "strh" if width==16 else "str"} {value.replace("x","w",1) if width<64 else value}, {address}')
        else:raise LoweringError(f'unsupported destination {o}')
    def condition(self,c):
        # x86 UCOMISD uses Z/C/P: NaN sets all three. ARM FCMP uses
        # N/Z/C/V, so ordered comparisons require the ARM floating predicates.
        if self.float_flags:return {'b':'mi','be':'ls','a':'gt','ae':'ge','p':'vs','np':'vc'}.get(c,COND[c])
        return COND[c]
    def instruction(self,line):
        if line == 'macos_axpy2':
            # Inputs: x14/output, x15/input, x9/pair count; factor at [x28].
            # 64-bit products wrap exactly like scalar int multiplication:
            # lo*lo + ((lo*hi + hi*lo) << 32), evaluated in two NEON lanes.
            # v26-v31 and x16 are scratch, outside the scalar IR register bank.
            self.serial+=1;loop=f'Larm_axpy{self.serial}';done=f'Larm_axpy_done{self.serial}'
            self.emit(f'cbz x9, {done}','ldr x16, [x28]','dup v26.2d, x16',
                      'xtn v27.2s, v26.2d','ushr v26.2d, v26.2d, #32','xtn v28.2s, v26.2d',
                      loop+':','ldr q29, [x15], #16','xtn v30.2s, v29.2d',
                      'ushr v29.2d, v29.2d, #32','xtn v29.2s, v29.2d',
                      'umull v31.2d, v27.2s, v30.2s','mul v29.2s, v27.2s, v29.2s',
                      'mla v29.2s, v28.2s, v30.2s','shll v29.2d, v29.2s, #32',
                      'add v31.2d, v31.2d, v29.2d','ldr q30, [x14]',
                      'add v31.2d, v31.2d, v30.2d','str q31, [x14], #16',
                      'subs x9, x9, #1',f'b.ne {loop}',done+':')
            self.float_flags=False;return
        if line == 'rep_stosq':
            # REP STOSQ leaves condition flags unchanged. Use non-flag-setting
            # count arithmetic and scratch v31/x16 for four words per store pair.
            self.serial+=1;loop=f'Larm_fill{self.serial}';tail=f'Larm_fill_tail{self.serial}';scalar=f'Larm_fill_scalar{self.serial}';done=f'Larm_fill_done{self.serial}'
            self.emit('lsr x16, x10, #2',f'cbz x16, {tail}','dup v31.2d, x9',loop+':',
                      'stp q31, q31, [x21], #32','sub x16, x16, #1',f'cbnz x16, {loop}',
                      tail+':','and x10, x10, #3',f'cbz x10, {done}',scalar+':',
                      'str x9, [x21], #8','sub x10, x10, #1',f'cbnz x10, {scalar}',done+':');return
        if line == 'macos_reduce2':
            # x14/data, x9/pair count; [x28] contains two nonnegative
            # 32-bit indices. Return the wrapping weighted sum in x9.
            self.serial+=1;loop=f'Larm_reduce{self.serial}'
            self.emit('ldr q26, [x28]','xtn v27.2s, v26.2d','movi v28.2s, #2',
                      'movi v26.2d, #0',loop+':','ldr q29, [x14], #16',
                      'xtn v30.2s, v29.2d','ushr v29.2d, v29.2d, #32','xtn v29.2s, v29.2d',
                      'umull v31.2d, v30.2s, v27.2s','mul v29.2s, v29.2s, v27.2s',
                      'shll v29.2d, v29.2s, #32','add v31.2d, v31.2d, v29.2d',
                      'add v26.2d, v26.2d, v31.2d','add v27.2s, v27.2s, v28.2s',
                      'subs x9, x9, #1',f'b.ne {loop}','addp d26, v26.2d','fmov x9, d26')
            self.float_flags=False;return
        op,_,body=line.partition(' ');args=[x.strip() for x in body.split(',')] if body else []
        if op in ('mov','movabs','movzx'):
            dst,src=args
            if '[' in dst and src in ALIASES and ' ptr ' not in dst:
                dst={8:'byte',16:'word',32:'dword'}[ALIASES[src][1]]+' ptr '+dst
            if '[' in src and dst in ALIASES and ' ptr ' not in src:
                src={8:'byte',16:'word',32:'dword'}[ALIASES[dst][1]]+' ptr '+src
            self.write(dst,self.read(src));return
        if op=='lea':self.write(args[0],self.addr(args[1],'x0'));return
        if op=='push':
            val=self.read(args[0]);self.emit('sub x28, x28, #8');self.sync();self.emit(f'str {val}, [x28]');return
        if op=='pop':self.emit('ldr x0, [x28]','add x28, x28, #8');self.write(args[0],'x0');self.sync();return
        if op=='ret':self.emit('ret');return
        if op=='call':
            target=args[0]
            if target == "r10": target="__imp_k_UnsupportedNativeInterop"
            if target.startswith('__imp_k_'):
                name=target[8:]
                if name=='RtlCaptureContext':
                    for i,r in enumerate(REG.values()):self.emit(f'str {r}, [x10, #{120+8*i}]')
                    self.emit('mov x9, #0');return
                if name not in ARITY:raise LoweringError(f'unsupported macOS API {name}')
                self.imports.add(name)
                for i,r in enumerate(('x10','x11','x12','x13')[:ARITY[name]]):self.emit(f'mov x{i}, {r}')
                for i in range(4,min(8,ARITY[name])):self.emit(f'ldr x{i}, [x28, #{32+8*(i-4)}]')
                # Preserve IR registers across the native Darwin call. The
                # register bank is only a compile-time allocation, never a VM.
                self.emit('mov x8, x28','sub sp, sp, #368')
                for i in range(8,ARITY[name]): self.emit(f'ldr x16, [x28, #{32+8*(i-4)}]',f'str x16, [sp, #{8*(i-8)}]')
                saved=['x9','x10','x11','x12','x13','x14','x15','x30']
                for i,r in enumerate(saved):self.emit(f'str {r}, [sp, #{16+8*i}]')
                for i in range(16):self.emit(f'str q{i}, [sp, #{80+16*i}]')
                self.emit('str x8, [sp, #336]',f'bl _darwin_{name}','ldr x28, [sp, #336]','mov x9, x0')
                for i,r in enumerate(saved[1:],1):self.emit(f'ldr {r}, [sp, #{16+8*i}]')
                for i in range(16):self.emit(f'ldr q{i}, [sp, #{80+16*i}]')
                self.sync();return
            if target.startswith('__imp_'):raise LoweringError('Windows DLL interop is unavailable on native macOS')
            self.emit('sub x28, x28, #8');self.sync();self.emit('str x30, [x28]')
            if target in REG:self.emit(f'blr {REG[target]}')
            else:self.emit('bl '+self.symbol(target))
            self.emit('ldr x30, [x28]','add x28, x28, #8');self.sync();return
        if op=='jmp':self.emit('b '+self.symbol(args[0]));return
        if op.startswith('j'):
            c=self.condition(op[1:]);self.serial+=1;label=f'Larm_skip{self.serial}'
            self.emit(f'b.{INVERSE[c]} {label}','b '+self.symbol(args[0]),label+':');return
        if op.startswith('set'):
            c=self.condition(op[3:]);self.emit(f'cset x0, {c}');self.write(args[0],'x0');return
        if op in ('cmp','test'):
            a=self.read(args[0],'x0')
            b=(self.arithmetic_immediate(args[1]) if op=='cmp' else self.logical_immediate(args[1])) or self.read(args[1],'x1')
            self.emit(f'{"cmp" if op=="cmp" else "tst"} {a}, {b}');self.float_flags=False;return
        if op in ('add','sub','and','or','xor'):
            a=self.read(args[0],'x0')
            b=(self.arithmetic_immediate(args[1]) if op in ('add','sub') else self.logical_immediate(args[1])) or self.read(args[1],'x1')
            inst={'add':'adds','sub':'subs','and':'ands','or':'orr','xor':'eor'}[op]
            destination=REG.get(args[0],'x0')
            self.emit(f'{inst} {destination}, {a}, {b}')
            if op in ('or','xor'): self.emit(f'tst {destination}, {destination}')
            if args[0] not in REG:self.write(args[0],destination)
            elif args[0]=='rsp':self.sync()
            self.float_flags=False;return
        if op in ('inc','dec','neg','not'):
            a=self.read(args[0]);destination=REG.get(args[0],'x0')
            self.emit(f'{"adds" if op=="inc" else "subs" if op=="dec" else "neg" if op=="neg" else "mvn"} {destination}, {a}'+(', #1' if op in ('inc','dec') else ''))
            if args[0] not in REG:self.write(args[0],destination)
            elif args[0]=='rsp':self.sync()
            return
        if op in ('shl','shr','sar'):
            a=self.read(args[0]);destination=REG.get(args[0],'x0')
            try:b=f'#{int(args[1],0)&63}'
            except ValueError:b=self.read(args[1],'x1')
            self.emit(f'{"lsl" if op=="shl" else "lsr" if op=="shr" else "asr"} {destination}, {a}, {b}')
            if args[0] not in REG:self.write(args[0],destination)
            elif args[0]=='rsp':self.sync()
            return
        if op=='imul':
            a=self.read(args[1] if len(args)==3 else args[0]);b=self.read(args[2] if len(args)==3 else args[1],'x1')
            destination=REG.get(args[0],'x0');self.emit(f'mul {destination}, {a}, {b}')
            if args[0] not in REG:self.write(args[0],destination)
            elif args[0]=='rsp':self.sync()
            return
        if op=='mul':
            b=self.read(args[0]);self.emit(f'mov x2, {b}','umulh x11, x9, x2','mul x9, x9, x2');return
        if op=='cqo':self.emit('asr x11, x9, #63');return
        if op in ('div','idiv'):
            b=self.read(args[0]);self.emit(f'mov x2, {b}',f'{"sdiv" if op=="idiv" else "udiv"} x0, x9, x2','msub x11, x0, x2, x9','mov x9, x0');return
        if op in ('movsd','movapd','movq'):
            dst,src=args
            if src.startswith('xmm'):
                if dst.startswith('xmm'):self.read_float(src,'d'+dst[3:])
                elif '[' in dst:
                    address=self.memory(dst,64) or f'[{self.addr(dst)}]'
                    self.emit(f'str d{src[3:]}, {address}')
                else:self.emit(f'fmov x0, d{src[3:]}');self.write(dst,'x0')
            else:
                self.read_float(src,'d'+dst[3:])
            return
        if op in ('addsd','subsd','mulsd','divsd'):
            a='d'+args[0][3:]
            if args[1].startswith('xmm'):b='d'+args[1][3:]
            else:self.read_float(args[1],'d31');b='d31'
            self.emit(f'f{op[:-2]} {a}, {a}, {b}');return
        if op in ('maxsd','minsd'):
            a='d'+args[0][3:]
            if args[1].startswith('xmm'): b='d'+args[1][3:]
            else:
                self.read_float(args[1],'d31');b='d31'
            self.emit('mrs x26, nzcv',f'fcmp {a}, {b}',f'fcsel {a}, {a}, {b}, {"gt" if op=="maxsd" else "mi"}','msr nzcv, x26');return
        if op=='sqrtsd':
            self.emit(f'fsqrt d{args[0][3:]}, d{args[1][3:]}');return
        if op in ('xorpd','xorps'):
            self.emit(f'eor v{args[0][3:]}.16b, v{args[0][3:]}.16b, v{args[1][3:]}.16b');return
        if op in ('ucomisd','comisd'):

            if args[1].startswith('xmm'): b='d'+args[1][3:]
            else:
                self.read_float(args[1],'d31');b='d31'
            self.emit(f'fcmp d{args[0][3:]}, {b}');self.float_flags=True;return
        if op=='cvtsi2sd':self.emit(f'scvtf d{args[0][3:]}, {self.read(args[1])}');return
        if op=='cvttsd2si':self.emit(f'fcvtzs x0, d{args[1][3:]}');self.write(args[0],'x0');return
        raise LoweringError(f'unsupported ARM64 instruction: {line}')
    def relax_branches(self):
        # Keep the long form for targets outside B.cond's signed 19-bit range.
        # Padding is deliberately overestimated; shortening can only decrease
        # distances, so a single conservative pass is sufficient.
        positions=[];labels={};offset=0
        for line in self.lines:
            positions.append(offset)
            if line.endswith(':'):labels[line[:-1]]=offset
            elif line.startswith('.balign '):offset+=int(line.split()[1])-1
            elif line.startswith('.quad '):offset+=8*len(line[6:].split(','))
            elif line.startswith('.byte '):offset+=len(line[6:].split(','))
            elif line.startswith('.zero '):offset+=int(line.split()[1])
            elif line.startswith(('.ascii ','.asciz ')):offset+=len(line.encode())
            elif line and not line.startswith('.'):offset+=4
        result=[];index=0
        while index<len(self.lines):
            line=self.lines[index]
            match=re.fullmatch(r'b\.(\w+) (Larm_skip\d+)',line)
            if match and index+2<len(self.lines) and self.lines[index+1].startswith('b ') and self.lines[index+2]==match[2]+':':
                target=self.lines[index+1][2:]
                if target in labels and abs(labels[target]-positions[index])<(1<<20)-16:
                    result.append(f'b.{INVERSE[match[1]]} {target}');index+=3;continue
            result.append(line);index+=1
        return result
    def lower(self,source):
        # Only frontend-owned immutable double pools are eligible for immediate
        # substitution; ordinary memory keeps its load and all bits are exact.
        for match in re.finditer(r'^(__fc\d+):\s*\n[ \t]*\.quad (-?0x[0-9a-fA-F]+|-?[0-9]+)\s*$',source,re.M):
            self.float_constants[match[1]]=int(match[2],0)&((1<<64)-1)
        for number,line in enumerate(source.splitlines(),1):
            line=line.strip()
            if not line:continue
            try:
                if line=='.intel_syntax noprefix':continue
                if line=='.text':self.text=True;self.emit('.text');continue
                if line=='.globl zephyrMain':self.emit('.globl _zephyrMain');continue
                if line=='.section .rdata':self.text=False;self.emit('.data');continue
                if line=='.section .bss':self.text=False;self.emit('.data');continue
                if line.endswith(':'):self.emit(self.symbol(line[:-1])+':');continue
                if line.startswith('.'):
                    if self.text and line.startswith('.byte '):
                        encoded=[int(x.strip()) for x in line[6:].split(',')]
                        if encoded == [243,72,171]:
                            # The optimizer's REP STOSQ is a fill operation in
                            # the IR. Select a native store loop, not x86 bytes.
                            self.instruction('rep_stosq');continue
                        raise LoweringError('raw x86 vector instructions cannot be used on ARM64; compile with --macos-ir')
                    if line.startswith('.quad '):
                        items=line[6:].split(', ');items=[self.symbol(i) if re.match(r'^[A-Za-z_.]',i) else i for i in items];self.emit('.quad '+', '.join(items))
                    else:self.emit(line)
                    continue
                self.instruction(line)
            except (ValueError,KeyError) as e:raise LoweringError(f'line {number}: {e}') from e
        return '\n'.join(self.relax_branches())+'\n'

def lower_file(source,output):
    lower=Arm64();Path(output).write_text(lower.lower(Path(source).read_text()));return lower.imports

if __name__=='__main__':
    import sys
    lower_file(sys.argv[1],sys.argv[2])
