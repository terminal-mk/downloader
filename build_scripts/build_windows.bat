:: Run on a Windows machine (PyInstaller cannot cross-compile from Linux/macOS).
:: Produces dist\terminal.mk-dl.exe and dist\terminal.mk-dl-gui.exe
@echo off
cd /d "%~dp0\.."

python -m venv .venv-build || exit /b 1
call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip || exit /b 1
pip install -r build_scripts\requirements-build.txt || exit /b 1

set PYTHONDONTWRITEBYTECODE=1
pyinstaller build_scripts\terminal.mk-dl-cli.spec --distpath dist --workpath build\pyinstaller --noconfirm || exit /b 1
pyinstaller build_scripts\terminal.mk-dl-gui.spec --distpath dist --workpath build\pyinstaller --noconfirm || exit /b 1

echo Binaries: dist\terminal.mk-dl.exe, dist\terminal.mk-dl-gui.exe
echo.
echo The GUI registers itself as the terminal.mk-dl:// handler automatically
echo the first time it's run. To re-register manually (e.g. after another
echo app steals the association), use the "Re-register app" button on its
echo blank/start screen, or run: dist\terminal.mk-dl.exe register

call .venv-build\Scripts\deactivate.bat
