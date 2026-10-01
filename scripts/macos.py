#!/usr/bin/env python3
"""Native Apple Silicon build/run/self-build driver for Zephyr."""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from macos.arm64 import lower_file, LoweringError

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / 'zc-macos'
DARWIN = ROOT / 'bootstrap' / 'macos'

def execute(command, **kwargs):
    subprocess.run([str(x) for x in command], check=True, **kwargs)

def require_host():
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise ValueError('This driver requires native Apple Silicon macOS and an ARM64 Python 3.')
    if not shutil.which('clang'):
        raise ValueError('Apple Command Line Tools are required (xcode-select --install).')
    if not CORE.is_file():
        raise ValueError('zc-macos is missing. Restore the native compiler seed from this repository.')
    # A checked-in ARM64 compiler seed is the starting point for self-hosting.
    with CORE.open('rb') as f:
        header=f.read(8)
    if header != bytes.fromhex('cffaedfe0c000001'):
        raise ValueError('zc-macos must be a native ARM64 Mach-O executable.')

def build(source, output, flags=(), compiler=CORE):
    source=Path(source).resolve(); output=Path(output).resolve()
    if not source.is_file(): raise ValueError(f'Source file does not exist: {source}')
    if not output.parent.is_dir(): raise ValueError(f'Output directory does not exist: {output.parent}')
    if source == output: raise ValueError('Source and output paths must be different.')
    # Replace the destination only after a successful complete build. Failed
    # frontend, lowering or linking steps cannot accidentally run stale output.
    with tempfile.TemporaryDirectory(prefix='zephyr-arm64-') as directory:
        work=Path(directory); ir=work/'program-ir.s'; arm=work/'program.s'
        execute([compiler,'--macos-ir','--rt',*flags,source,ir])
        lower_file(ir,arm)
        if output.suffix=='.s':
            data=arm.read_bytes()
            with tempfile.NamedTemporaryFile(dir=output.parent,delete=False) as f: f.write(data); stage=Path(f.name)
        else:
            with tempfile.NamedTemporaryFile(dir=output.parent,delete=False) as f: stage=Path(f.name)
            try:
                execute(['clang','-arch','arm64','-mmacosx-version-min=13.0','-O2','-Wall','-Wextra','-Werror',arm,
                         DARWIN/'darwin.c',DARWIN/'main.c',DARWIN/'entry.s',
                         '-o',stage])
            except BaseException:
                stage.unlink(missing_ok=True);raise
        try: os.replace(stage,output)
        finally: stage.unlink(missing_ok=True)
    return output

def selfbuild():
    source=ROOT/'compiler'/'zc.zeph'
    with tempfile.TemporaryDirectory(prefix='zephyr-selfbuild-') as directory:
        work=Path(directory)
        # Keep intermediates beside the repository's runtime/library sources by
        # asking native seeds to use those files through the working directory.
        first=work/'zc1'; second=work/'zc2'
        print('Building native ARM64 compiler stage 1...',flush=True)
        build(source,first)
        print('Building native ARM64 compiler stage 2...',flush=True)
        build(source,second,compiler=first)
        # The signed Mach-O executable contains its output filename in signing
        # metadata. Compare the assembly fixpoint instead of that metadata.
        a=work/'stage2.s'; b=work/'stage3.s'
        build(source,a,compiler=first)
        build(source,b,compiler=second)
        if a.read_bytes()!=b.read_bytes(): raise ValueError('ARM64 self-build fixpoint failed.')
        execute([second,'--version'])
        with tempfile.NamedTemporaryFile(dir=ROOT,delete=False) as f: replacement=Path(f.name)
        try:
            shutil.copy2(second,replacement)
            os.replace(replacement,CORE)
        finally: replacement.unlink(missing_ok=True)
        print('Updated native ARM64 compiler; assembly self-build fixpoint verified.')

def main():
    parser=argparse.ArgumentParser(description='Zephyr native Apple Silicon compiler')
    args=sys.argv[1:]
    if args in (['--help'],['-h']):
        parser.print_help();print('zc [--rt] [-O2] [--test] input.zeph output\nzc run [-O2] input.zeph [arguments...]\nzc selfbuild');return
    require_host()
    if args==['selfbuild']:
        # Drivers called outside the checkout still use the intended sources.
        os.chdir(ROOT);selfbuild();return
    if args==['--version']:
        execute([CORE,'--version']);print('Target: Apple Silicon macOS (ARM64 Mach-O)');return
    if not args:parser.error('usage: zc [--rt] [-O2] [--test] input.zeph output | zc run input.zeph [arguments...] | zc selfbuild')
    running=args[0]=='run'
    if running:args=args[1:]
    flags=[]
    while args and args[0].startswith('-'):
        flag=args.pop(0)
        if flag=='--rt':continue
        if flag not in ('-O2','--test','--opt-report','--opt-dump'):
            raise ValueError(f'Unsupported native macOS option: {flag}')
        flags.append(flag)
    if not args:raise ValueError('A .zeph input file is required.')
    source=args.pop(0)
    if running:
        # build to a temporary executable, then run it with the remaining arguments
        with tempfile.TemporaryDirectory(prefix='zephyr-run-') as directory:
            program=build(source,Path(directory)/'program',flags)
            sys.exit(subprocess.run([str(program),*args]).returncode)
    else:
        if len(args)!=1:raise ValueError('Specify exactly one output path.')
        build(source,args[0],flags)

if __name__=='__main__':
    try:main()
    except (ValueError,LoweringError,OSError) as error:
        print(f'zc: {error}',file=sys.stderr);sys.exit(1)
    except subprocess.CalledProcessError as error:sys.exit(error.returncode if error.returncode>0 else 1)
