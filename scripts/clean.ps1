# clean.ps1 - delete build artifacts, keep everything that is a source.
#
# zc.exe is EXCLUDED on purpose: it is the compiler, and selfbuild.ps1 needs an
# existing zc.exe to rebuild itself. If you ever do lose it, re-seed with
#   .\bootstrap\build.ps1              (gcc, from the C seed)
# or .\bootstrap\zephyr.exe build selfhost\zc.zeph -o zc.exe --rt
# and then run .\selfbuild.ps1 to get back to the self-hosted fixpoint.

$root = Split-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location $root
try {
    $kept = 0
    $removed = 0

    # compiled samples/examples anywhere except the compiler itself
    Get-ChildItem -Recurse -Filter *.exe -File |
        Where-Object { $_.Name -ne 'zc.exe' -and $_.FullName -notlike '*\bootstrap\*' } |
        ForEach-Object { Remove-Item $_.FullName -Force; $removed++ }

    # rendered output and object files
    foreach ($p in @('out.bmp', 'out.png', 'bootstrap\runtime.o')) {
        if (Test-Path $p) { Remove-Item $p -Force; $removed++ }
    }

    # package.ps1 output (GETTING-STARTED.md is a source, so it stays)
    Get-ChildItem 'dist' -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force; $removed++ }
    Get-ChildItem 'dist' -Filter *.zip -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Force; $removed++ }

    if (Test-Path 'zc.exe') { $kept = 1 }
    Write-Host "removed $removed artifact(s); zc.exe kept: $(if ($kept) { 'yes' } else { 'MISSING - re-seed, see header' })"
}
finally { Pop-Location }
