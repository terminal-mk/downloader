# PyInstaller entry point. The package's own __main__.py and gui.py use
# relative imports, which fail when PyInstaller runs them as top-level scripts.
import sys

from terminalmk_downloader.cli import main

sys.exit(main())
