@echo off
echo Building UTAR WiFi Helper in C++...

:: Check if cl is in path
where cl >nul 2>nul
if %errorlevel% neq 0 (
    echo Loading Visual Studio Developer Environment...
    call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" amd64
)

echo Compiling Resources...
rc.exe resource.rc

echo Compiling C++ Code...
cl.exe /EHsc /O2 /MT /DUNICODE /D_UNICODE utarwifihelper.cpp resource.res /link /SUBSYSTEM:WINDOWS

if %errorlevel% equ 0 (
    echo Clean up intermediate files...
    del resource.res utarwifihelper.obj
    echo [✓] Build Successful! Created utarwifihelper.exe
) else (
    echo [✗] Build Failed!
)
