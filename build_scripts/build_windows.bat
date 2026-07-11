:: Run on a Windows machine (PyInstaller cannot cross-compile from Linux/macOS).
:: Produces dist\terminal.mk-dl.exe
@echo off
cd /d "%~dp0\.."

python -m venv .venv-build
call .venv-build\Scripts\activate.bat
pip install --upgrade pip
pip install -e .
pip install pyinstaller

pyinstaller build_scripts\terminal.mk-dl-cli.spec --distpath dist --workpath build\pyinstaller --noconfirm
pyinstaller build_scripts\terminal.mk-dl-gui.spec --distpath dist --workpath build\pyinstaller --noconfirm

echo Binaries: dist\terminal.mk-dl.exe, dist\terminal.mk-dl-gui.exe
echo.
echo The GUI registers itself as the terminal.mk-dl:// handler automatically
echo the first time it's run. To re-register manually (e.g. after another
echo app steals the association), use the "Re-register app" button on its
echo blank/start screen, or run: dist\terminal.mk-dl.exe register
echo.
echo Optional: wrap dist\terminal.mk-dl.exe with an installer (Inno Setup /
echo WiX) so protocol registration happens automatically at install time instead
echo of requiring the user to run "register" manually.

call .venv-build\Scripts\deactivate.bat
