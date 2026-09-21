@echo off
REM Builds vxngx.dll - the flat C shim over NGX that Zephyr's DLL-only FFI needs.
REM DLSS_SDK must point at a checkout of github.com/NVIDIA/DLSS.
REM The SDK is proprietary and is deliberately NOT vendored into this repo.

if "%DLSS_SDK%"=="" (
  echo ERROR: set DLSS_SDK to the DLSS SDK root first
  exit /b 1
)
if "%VULKAN_SDK%"=="" (
  echo ERROR: VULKAN_SDK is not set
  exit /b 1
)

call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 ( echo ERROR: vcvars64 failed & exit /b 1 )

REM Build from this directory with plain relative names. Passing /Fo"%~dp0" fails
REM because the trailing backslash escapes the closing quote for MSVC's parser.
pushd "%~dp0"

REM /MT because nvsdk_ngx_s.lib is the static-CRT build; mixing it with /MD
REM produces a link full of duplicate CRT symbols.
cl /nologo /LD /MT /O2 ^
   /I"%DLSS_SDK%\include" /I"%VULKAN_SDK%\Include" ^
   vxngx.c ^
   /Fevxngx.dll ^
   /link "%DLSS_SDK%\lib\Windows_x86_64\x64\nvsdk_ngx_s.lib" ^
   advapi32.lib user32.lib ole32.lib shlwapi.lib dxgi.lib

set RC=%errorlevel%
popd
exit /b %RC%
