"""Compile-time scaling code generators (nordlow/compiler-benchmark style).

Generates one source file with `functionCount` independent call chains, each
`functionDepth` functions deep, with constants randomized from a seed so no
compiler cache can help. For chain n, innermost level first:

    addIntN{n}H0(x)  = x + c
    addIntN{n}H{h}(x) = x + addIntN{n}H{h-1}(x) + c      (h = 1 .. depth-2)
    addIntN{n}(x)    = x + addIntN{n}H{depth-2}(x) + c

main sums addIntN{n}(n) over every chain with wrapping 64-bit arithmetic and
prints the signed result, identical in every language; expectedChecksum()
computes it in Python.

API:
    LANGUAGES[name] = {
        "extension": ".c",
        "available": bool,                   # toolchain found on this machine
        "maximumSize": int | None,           # cap on functionCount * functionDepth
        "generate": fn(functionCount, functionDepth, seed) -> str,
        "operations": {operationName: fn(sourcePath, outputDir) -> (argv, producedPathOrNone)},
        "run": fn(producedPath) -> argv,     # how to execute a "build" result
    }
    expectedChecksum(functionCount, functionDepth, seed) -> int

Operations (only where the toolchain supports them):
    check          syntax/type check, no code generation
    compile        code generation without linking (zephyr: assembly text, .s)
    build          unoptimized executable
    buildOptimized optimized executable
An operation function only prepares the output directory and returns the
command line; the caller runs (and times) it.

Usage: python bench/compilegen.py    (self-check at 20x20 for every available language)
"""
import glob
import os
import random
import shutil
import subprocess
import sys
import tempfile

repositoryRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
zephyrCompiler = os.environ.get("ZEPHYR_COMPILER", os.path.join(repositoryRoot, "zc_new.exe"))
executableSuffix = ".exe" if os.name == "nt" else ""
wordMask = (1 << 64) - 1

# gcc/g++ live in MSYS2 on this machine; their runtime DLLs must be on PATH too.
msysBinDirectory = r"C:\msys64\ucrt64\bin"
if shutil.which("gcc") is None and os.path.isdir(msysBinDirectory):
    os.environ["PATH"] = msysBinDirectory + os.pathsep + os.environ["PATH"]


def randomConstants(functionCount, functionDepth, seed):
    """constants[n][h]: h = 0 is the innermost level, h = depth-1 the chain's entry."""
    generator = random.Random(seed)
    return [[generator.randrange(1, 1 << 31) for h in range(functionDepth)] for n in range(functionCount)]


def expectedChecksum(functionCount, functionDepth, seed):
    total = 0
    for n, chainConstants in enumerate(randomConstants(functionCount, functionDepth, seed)):
        value = 0
        for h, constant in enumerate(chainConstants):
            value = (n + (value if h > 0 else 0) + constant) & wordMask
        total = (total + value) & wordMask
    return total - (1 << 64) if total >= 1 << 63 else total


def functionName(n, h, functionDepth):
    return f"addIntN{n}" if h == functionDepth - 1 else f"addIntN{n}H{h}"


def chainLevels(functionCount, functionDepth, seed):
    """Yield (name, calleeNameOrNone, constant) for every function, innermost first."""
    for n, chainConstants in enumerate(randomConstants(functionCount, functionDepth, seed)):
        for h, constant in enumerate(chainConstants):
            callee = functionName(n, h - 1, functionDepth) if h > 0 else None
            yield functionName(n, h, functionDepth), callee, constant


def generateZephyr(functionCount, functionDepth, seed):
    lines = []
    for name, callee, constant in chainLevels(functionCount, functionDepth, seed):
        body = f"x + {callee}(x) + {constant}" if callee else f"x + {constant}"
        lines.append(f"fn {name}(x: int) -> int {{ return {body} }}")
    lines.append("var sum = 0")
    lines += [f"sum += addIntN{n}({n})" for n in range(functionCount)]
    lines.append("print(sum)")
    return "\n".join(lines) + "\n"


def generateCFamily(functionCount, functionDepth, seed, isCpp):
    lines = ["#include <cstdio>" if isCpp else "#include <stdio.h>", "typedef unsigned long long word;"]
    for name, callee, constant in chainLevels(functionCount, functionDepth, seed):
        body = f"x + {callee}(x) + {constant}ULL" if callee else f"x + {constant}ULL"
        lines.append(f"static word {name}(word x) {{ return {body}; }}")
    lines.append("int main(void) {")
    lines.append("    word sum = 0;")
    lines += [f"    sum += addIntN{n}({n});" for n in range(functionCount)]
    lines.append(f"    {'std::' if isCpp else ''}printf(\"%lld\\n\", (long long)sum);")
    lines.append("    return 0;")
    lines.append("}")
    return "\n".join(lines) + "\n"


def generateRust(functionCount, functionDepth, seed):
    lines = ["#![allow(non_snake_case)]"]
    for name, callee, constant in chainLevels(functionCount, functionDepth, seed):
        body = f"x.wrapping_add({callee}(x)).wrapping_add({constant})" if callee else f"x.wrapping_add({constant})"
        lines.append(f"fn {name}(x: i64) -> i64 {{ {body} }}")
    lines.append("fn main() {")
    lines.append("    let mut sum: i64 = 0;")
    lines += [f"    sum = sum.wrapping_add(addIntN{n}({n}));" for n in range(functionCount)]
    lines.append('    println!("{}", sum);')
    lines.append("}")
    return "\n".join(lines) + "\n"


def generateManaged(functionCount, functionDepth, seed, isJava):
    # Java: a non-public class may live in a file of any name, so the generated
    # class name never has to match the caller's file name.
    lines = ["class CompileBenchmark {"]
    for name, callee, constant in chainLevels(functionCount, functionDepth, seed):
        body = f"x + {callee}(x) + {constant}L" if callee else f"x + {constant}L"
        lines.append(f"    static long {name}(long x) {{ return {body}; }}")
    signature = "public static void main(String[] arguments)" if isJava else "static void Main()"
    lines.append(f"    {signature} {{")
    lines.append("        long sum = 0;")
    lines += [f"        sum += addIntN{n}({n});" for n in range(functionCount)]
    lines.append(f"        {'System.out.println' if isJava else 'System.Console.WriteLine'}(sum);")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def outputPath(sourcePath, outputDir, extension):
    stem = os.path.splitext(os.path.basename(sourcePath))[0]
    os.makedirs(outputDir, exist_ok=True)
    return os.path.join(outputDir, stem + extension)


def gccOperations(driver):
    def check(sourcePath, outputDir):
        return [driver, "-fsyntax-only", sourcePath], None

    def compileObject(sourcePath, outputDir):
        objectPath = outputPath(sourcePath, outputDir, ".o")
        return [driver, "-c", "-O0", sourcePath, "-o", objectPath], objectPath

    def build(sourcePath, outputDir):
        executablePath = outputPath(sourcePath, outputDir, executableSuffix)
        return [driver, "-O0", sourcePath, "-o", executablePath], executablePath

    def buildOptimized(sourcePath, outputDir):
        executablePath = outputPath(sourcePath, outputDir, executableSuffix)
        return [driver, "-O2", sourcePath, "-o", executablePath], executablePath

    return {"check": check, "compile": compileObject, "build": build, "buildOptimized": buildOptimized}


def rustCheck(sourcePath, outputDir):
    metadataPath = outputPath(sourcePath, outputDir, ".rmeta")
    return ["rustc", "--emit=metadata", sourcePath, "-o", metadataPath], None


def rustCompile(sourcePath, outputDir):
    objectPath = outputPath(sourcePath, outputDir, ".o")
    return ["rustc", "-C", "opt-level=0", "--emit=obj", sourcePath, "-o", objectPath], objectPath


def rustBuild(sourcePath, outputDir):
    executablePath = outputPath(sourcePath, outputDir, executableSuffix)
    return ["rustc", "-C", "opt-level=0", sourcePath, "-o", executablePath], executablePath


def rustBuildOptimized(sourcePath, outputDir):
    executablePath = outputPath(sourcePath, outputDir, executableSuffix)
    return ["rustc", "-O", sourcePath, "-o", executablePath], executablePath


def zephyrCompile(sourcePath, outputDir):
    # zc has no check-only mode; a .s output runs the whole front end and code
    # generator but stops before writing the executable.
    assemblyPath = outputPath(sourcePath, outputDir, ".s")
    return [zephyrCompiler, "--rt", sourcePath, assemblyPath], assemblyPath


def zephyrBuild(sourcePath, outputDir):
    executablePath = outputPath(sourcePath, outputDir, ".exe")
    return [zephyrCompiler, "--rt", sourcePath, executablePath], executablePath


def zephyrBuildOptimized(sourcePath, outputDir):
    executablePath = outputPath(sourcePath, outputDir, ".exe")
    return [zephyrCompiler, "--rt", "-O2", sourcePath, executablePath], executablePath


def javaBuild(sourcePath, outputDir):
    os.makedirs(outputDir, exist_ok=True)
    return ["javac", "-d", outputDir, sourcePath], os.path.join(outputDir, "CompileBenchmark.class")


def findCsharpToolchain():
    """(dotnet, csc.dll, reference directory, runtime version) or None; needs no project file."""
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        return None
    dotnetRoot = os.path.dirname(os.path.realpath(dotnet))
    versionKey = lambda path: [int(part) if part.isdigit() else 0 for part in os.path.basename(path).split(".")]
    compilers = sorted(glob.glob(os.path.join(dotnetRoot, "sdk", "*", "Roslyn", "bincore", "csc.dll")),
                       key=lambda path: versionKey(os.path.dirname(os.path.dirname(os.path.dirname(path)))))
    referencePacks = sorted(glob.glob(os.path.join(dotnetRoot, "packs", "Microsoft.NETCore.App.Ref", "*")), key=versionKey)
    if not compilers or not referencePacks:
        return None
    runtimeVersion = os.path.basename(referencePacks[-1])
    referenceDirectories = glob.glob(os.path.join(referencePacks[-1], "ref", "net*"))
    if not referenceDirectories:
        return None
    return dotnet, compilers[-1], referenceDirectories[0], runtimeVersion


csharpToolchain = findCsharpToolchain()


def csharpOperation(optimize):
    def operation(sourcePath, outputDir):
        dotnet, compilerPath, referenceDirectory, runtimeVersion = csharpToolchain
        assemblyPath = outputPath(sourcePath, outputDir, ".dll")
        frameworkMoniker = os.path.basename(referenceDirectory)
        with open(os.path.splitext(assemblyPath)[0] + ".runtimeconfig.json", "w") as configFile:
            configFile.write('{"runtimeOptions": {"tfm": "%s", "framework": {"name": "Microsoft.NETCore.App", "version": "%s"}}}\n'
                             % (frameworkMoniker, runtimeVersion))
        argv = [dotnet, compilerPath, "-nologo", "-target:exe", "-optimize" + ("+" if optimize else "-"),
                "-r:" + os.path.join(referenceDirectory, "System.Runtime.dll"),
                "-r:" + os.path.join(referenceDirectory, "System.Console.dll"),
                "-out:" + assemblyPath, sourcePath]
        return argv, assemblyPath
    return operation


def toolExists(tool):
    return shutil.which(tool) is not None or os.path.isfile(tool)


LANGUAGES = {
    "zephyr": {
        "extension": ".zeph",
        "available": toolExists(zephyrCompiler),
        "maximumSize": None,
        "generate": generateZephyr,
        "operations": {"compile": zephyrCompile, "build": zephyrBuild, "buildOptimized": zephyrBuildOptimized},
        "run": lambda producedPath: [producedPath],
    },
    "c": {
        "extension": ".c",
        "available": toolExists("gcc"),
        "maximumSize": None,
        "generate": lambda functionCount, functionDepth, seed: generateCFamily(functionCount, functionDepth, seed, False),
        "operations": gccOperations("gcc"),
        "run": lambda producedPath: [producedPath],
    },
    "cpp": {
        "extension": ".cpp",
        "available": toolExists("g++"),
        "maximumSize": None,
        "generate": lambda functionCount, functionDepth, seed: generateCFamily(functionCount, functionDepth, seed, True),
        "operations": gccOperations("g++"),
        "run": lambda producedPath: [producedPath],
    },
    "rust": {
        "extension": ".rs",
        "available": toolExists("rustc"),
        "maximumSize": None,
        "generate": generateRust,
        "operations": {"check": rustCheck, "compile": rustCompile, "build": rustBuild, "buildOptimized": rustBuildOptimized},
        "run": lambda producedPath: [producedPath],
    },
    "java": {
        "extension": ".java",
        "available": toolExists("javac") and toolExists("java"),
        # One class holds every method; the class-file constant pool (65535
        # entries, ~5 per method: method ref, name-and-type, name, 2-slot long
        # constant) overflows past ~13100 methods. Measured: 114x114 ok, 115x115 fails.
        "maximumSize": 13000,
        "generate": lambda functionCount, functionDepth, seed: generateManaged(functionCount, functionDepth, seed, True),
        "operations": {"build": javaBuild},
        "run": lambda producedPath: ["java", "-cp", os.path.dirname(producedPath), "CompileBenchmark"],
    },
    "csharp": {
        "extension": ".cs",
        "available": csharpToolchain is not None,
        "maximumSize": None,
        "generate": lambda functionCount, functionDepth, seed: generateManaged(functionCount, functionDepth, seed, False),
        "operations": {"build": csharpOperation(False), "buildOptimized": csharpOperation(True)},
        "run": lambda producedPath: [csharpToolchain[0], producedPath],
    },
}


def selfCheck(functionCount=20, functionDepth=20, seed=1):
    expected = expectedChecksum(functionCount, functionDepth, seed)
    print(f"expected checksum {functionCount}x{functionDepth} seed {seed}: {expected}")
    failures = 0
    with tempfile.TemporaryDirectory() as workDirectory:
        for languageName, language in LANGUAGES.items():
            if not language["available"]:
                print(f"{languageName:8} skipped (toolchain not found)")
                continue
            sourcePath = os.path.join(workDirectory, f"generated_{languageName}{language['extension']}")
            with open(sourcePath, "w", newline="\n") as sourceFile:
                sourceFile.write(language["generate"](functionCount, functionDepth, seed))
            outputDir = os.path.join(workDirectory, languageName)
            argv, producedPath = language["operations"]["build"](sourcePath, outputDir)
            subprocess.run(argv, check=True, timeout=600)
            printed = subprocess.run(language["run"](producedPath), check=True, capture_output=True, text=True, timeout=60).stdout.strip()
            status = "ok" if printed == str(expected) else f"MISMATCH (printed {printed})"
            failures += status != "ok"
            print(f"{languageName:8} {status}")
    assert failures == 0, f"{failures} language(s) printed the wrong checksum"


if __name__ == "__main__":
    selfCheck()
