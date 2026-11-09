#!/usr/bin/env python3
"""
Run the MM9 promotion playthrough (README.md here): the main playthrough's runner (../run.py) on this folder's
segments, with output under output/playthrough/mm9/promotions/.

    python3 tests/playthrough/mm9/promotions/run.py            # every segment, stopping at the first failure
    python3 tests/playthrough/mm9/promotions/run.py 21 22      # these segments (their checkpoints must exist)
    python3 tests/playthrough/mm9/promotions/run.py --reload   # also save and load back after each settling step
    python3 tests/playthrough/mm9/promotions/run.py --start    # first copy the starting checkpoints from the main run

The chain starts from output/playthrough/mm9/promotions/checkpoints/00_start.oysav, a copy of the main run's
53_connecting_tunnels.oysav (Yorwick, Chapter II; the new game's Knight, Cleric, Thief and Sorcerer). Block E's
branch (70-89) starts from 00_after_krohn.oysav, a copy of the main run's 60_krohn.oysav (the Jarls are back, key 108).
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mm9_playthrough_run", HERE.parent / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

runner.HERE = HERE
runner.OUT = runner.ROOT / "output/playthrough/mm9/promotions"
runner.CHECKPOINTS = "output/playthrough/mm9/promotions/checkpoints/"
runner.RELOAD_CHECKPOINTS = "output/playthrough/mm9/promotions/reload/checkpoints/"
MAIN = runner.ROOT / "output/playthrough/mm9/checkpoints"
STARTS = {"00_start.oysav": MAIN / "53_connecting_tunnels.oysav", "00_after_krohn.oysav": MAIN / "60_krohn.oysav"}


def main() -> int:
    if "--start" in sys.argv:
        sys.argv.remove("--start")
        (runner.OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
        for name, source in STARTS.items():
            shutil.copy2(source, runner.OUT / "checkpoints" / name)
    if "--reload" in sys.argv:
        (runner.OUT / "reload/checkpoints").mkdir(parents=True, exist_ok=True)
        for name in STARTS:
            start, reload_start = runner.OUT / "checkpoints" / name, runner.OUT / "reload/checkpoints" / name
            if start.exists() and not reload_start.exists():
                shutil.copy2(start, reload_start)
    return runner.main()


if __name__ == "__main__":
    sys.exit(main())
