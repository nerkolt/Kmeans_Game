@echo off
setlocal

REM Always run from repo root (so relative paths work even if launched elsewhere)
pushd "%~dp0\..\.."

REM Usage:
REM   build_exe.bat onedir
REM   build_exe.bat onefile
REM   build_exe.bat installer
REM Default: onedir

set MODE=%1
if "%MODE%"=="" set MODE=onedir
set NAME=KmeansGame

echo Building %NAME% (%MODE%)...

python -m pip install --upgrade pip
python -m pip install pyinstaller pillow

set ENTRY=Scripts\Kmeans_Game_Debug.py
set ICON_OUT=build\logo.ico
set ICON_SRC=Assets\logo.png
if not exist "%ICON_SRC%" set ICON_SRC=Assets\logo_try.png
if exist "%ICON_SRC%" (
  python tools\make_icon.py "%ICON_SRC%" %ICON_OUT%
) else (
  echo Warning: no icon source found (Assets\logo.png or Assets\logo_try.png). Building without icon.
  set ICON_OUT=
)

if /I "%MODE%"=="onefile" (
  if "%ICON_OUT%"=="" (
    python -m PyInstaller --noconfirm --clean --windowed --onefile --name %NAME% --paths Scripts %ENTRY%
  ) else (
    python -m PyInstaller --noconfirm --clean --windowed --onefile --name %NAME% --icon %ICON_OUT% --paths Scripts %ENTRY%
  )
  echo Done. Output: dist\%NAME%.exe
) else if /I "%MODE%"=="installer" (
  if "%ICON_OUT%"=="" (
    python -m PyInstaller --noconfirm --clean --windowed --name %NAME% --paths Scripts %ENTRY%
  ) else (
    python -m PyInstaller --noconfirm --clean --windowed --name %NAME% --icon %ICON_OUT% --paths Scripts %ENTRY%
  )
  echo Built app folder. Output: dist\%NAME%\%NAME%.exe
  where iscc >nul 2>nul
  if errorlevel 1 (
    echo Inno Setup compiler (iscc) not found.
    echo Install Inno Setup, then run: iscc installer.iss
    echo Or run this script again after installing Inno Setup.
    goto :eof
  )
  iscc installer.iss
  echo Done. Output: dist-installer\%NAME%-Setup-*.exe
) else (
  if "%ICON_OUT%"=="" (
    python -m PyInstaller --noconfirm --clean --windowed --name %NAME% --paths Scripts %ENTRY%
  ) else (
    python -m PyInstaller --noconfirm --clean --windowed --name %NAME% --icon %ICON_OUT% --paths Scripts %ENTRY%
  )
  echo Done. Output: dist\%NAME%\%NAME%.exe
)

endlocal

popd


