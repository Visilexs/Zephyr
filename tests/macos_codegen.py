#!/usr/bin/env python3
"""Execute ARM64 instruction-selection boundary cases on an Apple Silicon Mac."""
from pathlib import Path
import subprocess
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from macos.arm64 import Arm64

def main():
    lines=['.intel_syntax noprefix','.text','.globl zephyrMain','zephyrMain:','sub rsp, 64']
    checks=0
    def check(operand,expected):
        nonlocal checks
        checks+=1
        lines.extend([f'cmp {operand}, {expected}',f'je passed{checks}',
                      f'mov qword ptr [rip + result], {checks}','add rsp, 64','ret',f'passed{checks}:'])
    mask=(1<<64)-1
    def signed(n):return ((n+(1<<63))&mask)-(1<<63)
    for value in [0,1,-1,4095,4096,4097,(1<<63)-1,-(1<<63),0x123456789abcdef]:
        for operation,constant in [('add',1),('sub',4096),('and',-16),('or',0xff00ff00ff00ff00),
                                   ('xor',0x8000000000000000),('imul',-3),('shl',65),('shr',-1),('sar',63)]:
            if operation=='add':expected=signed(value+constant)
            elif operation=='sub':expected=signed(value-constant)
            elif operation=='and':expected=signed(value&constant)
            elif operation=='or':expected=signed(value|constant)
            elif operation=='xor':expected=signed(value^constant)
            elif operation=='imul':expected=signed(value*constant)
            elif operation=='shl':expected=signed(value<<(constant&63))
            elif operation=='shr':expected=(value&mask)>>(constant&63)
            else:expected=value>>(constant&63)
            for destination in ['rax','qword ptr [rsp + 16]']:
                lines.extend([f'mov {destination}, {value}',f'{operation} {destination}, {constant}'])
                check(destination,expected)
    # A second memory operand must not overwrite a value already loaded into
    # scratch x0; partial registers must still zero-extend or preserve high bits.
    lines.extend(['mov qword ptr [rsp], 17','mov qword ptr [rsp + 8], 23',
                  'add qword ptr [rsp], qword ptr [rsp + 8]'])
    check('qword ptr [rsp]',40)
    lines.extend(['mov rax, -1','mov eax, 17']);check('rax',17)
    lines.extend(['mov rax, -1','mov al, 17']);check('rax',-239)
    lines.extend(['mov rcx, 129','mov rax, 3','shl rax, cl']);check('rax',6)
    # Floating loads/stores preserve raw payloads, including signed zero and NaN.
    float_bits=[0,1,1<<63,0x7ff8000000001234,0x7ff0000000000000]
    for sign in [1,-1]:
        for numerator in range(16,32):
            for power in range(-3,5):
                float_bits.append(int.from_bytes(struct.pack('>d',sign*numerator/16*2**power),'big'))
    for index,bits in enumerate(float_bits):
        for prefix in ['', 'qword ptr ']:
            lines.extend([f'movsd xmm2, {prefix}[rip + __fc{index}]','movsd [rsp + 24], xmm2',
                          'movsd xmm3, [rsp + 24]','movq rax, xmm3'])
            check('rax',signed(bits))
    # Near the reduction kernel's 32-bit index limit, high product bits must
    # still contribute to the wrapping 64-bit result.
    for low in [0,1,2147483645]:
        for first,second in [(-1,-(1<<63)),((1<<63)-1,0x123456789abcdef)]:
            lines.extend(['lea rbx, [rip + buffer]',f'mov qword ptr [rbx], {first}',
                          f'mov qword ptr [rbx + 8], {second}',f'mov qword ptr [rsp], {low}',
                          f'mov qword ptr [rsp + 8], {low+1}','mov r10, rbx','mov rax, 1','macos_reduce2'])
            check('rax',signed(first*low+second*(low+1)))
    # REP-style fills must handle short counts and tails without clobbering
    # preceding comparison flags or writing either surrounding canary.
    for count in range(16):
        lines.extend(['lea rbx, [rip + buffer]','mov qword ptr [rbx], 123',
                      f'mov qword ptr [rbx + {8*(count+1)}], 456',
                      'lea rdi, [rbx + 8]','mov rax, -7',f'mov rcx, {count}',
                      'cmp rax, -7','rep_stosq'])
        checks+=1
        lines.extend([f'je flags{checks}',f'mov qword ptr [rip + result], {checks}',
                      'add rsp, 64','ret',f'flags{checks}:'])
        check('qword ptr [rbx]',123);check(f'qword ptr [rbx + {8*(count+1)}]',456)
        for i in range(count):check(f'qword ptr [rbx + {8*(i+1)}]',-7)
        check('rcx',0)
    lines.extend(['mov rax, 1','cmp rax, 1','je farTarget',
                  'mov qword ptr [rip + result], 999','add rsp, 64','ret',
                  '.zero 1048576','farTarget:','add rsp, 64','ret',
                  '.section .rdata','.globl _result','.balign 8','result:','.quad 0','buffer:','.zero 160'])
    for index,bits in enumerate(float_bits):
        lines.extend([f'__fc{index}:',f'  .quad {signed(bits)}'])
    assembly=Arm64().lower('\n'.join(lines))
    # Execute both relaxed short branches and an out-of-range long branch.
    assert 'b.eq _passed1' in assembly
    assert 'b _farTarget' in assembly
    assert assembly.count('fmov d2, #')==512 # both frontend constant operand forms
    with tempfile.TemporaryDirectory(prefix='zephyr-codegen-test-') as directory:
        work=Path(directory);source=work/'test.s';source.write_text(assembly)
        harness=work/'main.c'
        harness.write_text('#include <stdio.h>\nextern void zephyr_entry(void); extern long long result;\n'
                           'int main(void) { zephyr_entry(); if (result) fprintf(stderr, "Failed instruction check %lld\\n", result); return result != 0; }\n')
        executable=work/'test'
        subprocess.run(['clang','-arch','arm64',source,ROOT/'bootstrap/macos/entry.s',harness,'-o',executable],check=True)
        result=subprocess.run([executable])
        assert result.returncode==0,f'ARM64 instruction check failed: {result.returncode}'
    print(f'{checks} native instruction checks passed, including a branch over 1 MiB.')

if __name__=='__main__':main()
