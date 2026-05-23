"""Kase startup banner."""

import shutil
from datetime import datetime
from kase import __version__


BANNER = """\
╔══════════════════════════════════════════════════╗
║                    ✦ Kase ✦                      ║
║     The Next-Generation AI Agent by Kyssta       ║
║            Smarter · Faster · Better              ║
╚══════════════════════════════════════════════════╝"""


def show_banner() -> None:
    width = min(shutil.get_terminal_size().columns, 80)
    print(BANNER)
    print(f"  Kase v{__version__}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
