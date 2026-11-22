#!/usr/bin/env python3
"""
Run the Xeen promotion playthrough (README.md here): the main chain's runner (../run.py) on this folder's segments,
with output under output/playthrough/xeen/promotions/. Owner: A3 (sub-lane A3-promo).

    python3 tests/playthrough/xeen/promotions/run.py            # every segment, stopping at the first failure
    python3 tests/playthrough/xeen/promotions/run.py 01 03      # these segments (their starting checkpoints must exist)
    python3 tests/playthrough/xeen/promotions/run.py --reload   # also save and load back after each settling step
    python3 tests/playthrough/xeen/promotions/run.py --start    # first copy the starting checkpoints from the main run

The chain has no new game of its own: every block starts from a copy of the main chain's checkpoint just before or
just after the promotion quest it covers (STARTS below; README "Blocks"), so a quest the main chain already plays is
never replayed. A start whose main checkpoint does not exist yet is skipped with a note.

Every run also checks the segments' `CONVENTION prerequisite` lines (D-75, devdocs/xeen/reviews/D75_DECISION.md): each
must end `; proven by <test path>`, the path must exist, and that test must have a `qbit_set` assert containing the
line's id. A miss is an ISSUE: printed, added to the report's "ISSUE" section, and the run fails.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("xeen_playthrough_run", HERE.parent / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

runner.HERE = HERE
runner.OUT = runner.ROOT / "output/playthrough/xeen/promotions"
runner.CHECKPOINTS = "output/playthrough/xeen/promotions/checkpoints/"
runner.RELOAD_CHECKPOINTS = "output/playthrough/xeen/promotions/reload/checkpoints/"
MAIN = runner.ROOT / "output/playthrough/xeen/checkpoints"
# start name -> the main chain's checkpoint it copies
STARTS = {
    "00_main_09.oysav": MAIN / "09_witch_tower.oysav",        # X1 at Valia's door: M4 and T1-A done
    "00_main_17.oysav": MAIN / "17_rivercity.oysav",          # X2: Q-C2 (T1-B) and Q-C17 done
    "00_main_21.oysav": MAIN / "21_court_again.oysav",        # X4 outside Castle Burlock: Q-C3 (T1-E) done; block B (Q-C10)
    "00_main_33.oysav": MAIN / "33_cave_of_illusion.oysav",   # X5 after the Cave of Illusion: block C (Q-C4)
    "00_main_59.oysav": MAIN / "59_dimitri.oysav",            # Castle Kalindra at stage 3: block D (T2-A)
    "00_main_49.oysav": MAIN / "49_temple_of_bark.oysav",     # D2 at Sharla's: Q-D10 done (polite)
    "00_main_63.oysav": MAIN / "63_heretics_of_mok.oysav",    # D1 at the Temple of Mok: Q-D6 done
    "00_main_65.oysav": MAIN / "65_jewel_of_ages.oysav",      # D3 at the Guild of Light: Q-D18 done
    "00_main_57.oysav": MAIN / "57_lost_souls.oysav",         # D4 at Lakeside's jetty: M20 started; block E (Leafpoint)
    "00_main_43.oysav": MAIN / "43_ogre_pass.oysav",          # D1 at Kramer's: Q-D11's peace done; block D (the burning)
    "00_main_55.oysav": MAIN / "55_southern_tower.oysav",     # D1 at Kalindra's gate: Q-D19 done; block G (inner circle)
    "00_main_35.oysav": MAIN / "35_tower_of_high_magic.oysav",  # X3 after the Tower of High Magic: block R (Q-C7)
    "00_main_83.oysav": MAIN / "83_castle_xeen.oysav",        # X4 outside Castle Burlock: block R (Q-C25, X7, XD-18)
}
# log('CONVENTION prerequisite <quest>.<bit> (<id>): <why>; proven by <path>') (D-75 point 8)
PREREQUISITE = re.compile(r"CONVENTION prerequisite (\S+) \((\d+)\): (?:(?!; proven by )[^'\"])*(?:; proven by ([\w./-]+))?")


def qbits_set(node) -> set[int]:
    """Every id under a `qbit_set` key anywhere in a scenario's steps."""
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "qbit_set" and isinstance(value, list):
                found |= {int(v) for v in value if isinstance(v, int)}
            else:
                found |= qbits_set(value)
    elif isinstance(node, list):
        for value in node:
            found |= qbits_set(value)
    return found


def prerequisite_checks() -> tuple[list[str], list[str]]:
    """(checked, issues) for every CONVENTION prerequisite line of this folder's segments (D-75 points 2 and 8)."""
    checked, issues = [], []
    for segment in sorted(HERE.glob("[0-9][0-9]_*.yml")):
        for match in PREREQUISITE.finditer(segment.read_text()):
            bit, qbit, proof = match.group(1), int(match.group(2)), match.group(3)
            where = f"{segment.stem}: {bit} ({qbit})"
            if not proof:
                issues.append(f"{where}: the line does not end '; proven by <test path>'")
                continue
            path = runner.ROOT / proof
            if not path.is_file():
                issues.append(f"{where}: {proof} does not exist")
                continue
            if qbit not in qbits_set(runner.yaml.safe_load(path.read_text())):
                issues.append(f"{where}: {proof} has no qbit_set assert of {qbit}")
                continue
            checked.append(f"{where}: proven by {proof} (qbit_set {qbit})")
    return checked, issues


def main() -> int:
    if "--start" in sys.argv:
        sys.argv.remove("--start")
        (runner.OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
        for name, source in STARTS.items():
            if source.exists():
                shutil.copy2(source, runner.OUT / "checkpoints" / name)
            else:
                print(f"start {name}: the main run's {source.name} does not exist yet, skipped")
    if "--reload" in sys.argv:
        (runner.OUT / "reload/checkpoints").mkdir(parents=True, exist_ok=True)
        for name in STARTS:
            start, reload_start = runner.OUT / "checkpoints" / name, runner.OUT / "reload/checkpoints" / name
            # A fresh --start replaces the reload run's copies too (newer start, or none yet).
            if start.exists() and (not reload_start.exists()
                                   or start.stat().st_mtime > reload_start.stat().st_mtime):
                shutil.copy2(start, reload_start)
    result = runner.main()
    checked, issues = prerequisite_checks()
    for line in issues:
        print(f"ISSUE CONVENTION prerequisite {line}")
    report = runner.OUT / ("reload" if "--reload" in sys.argv else "") / "report.md"
    if report.exists():
        text = report.read_text().replace("\n## CONVENTION\n", "\n## CONVENTION prerequisite checks (D-75)\n\n"
                                          + "\n".join(f"- {line}" for line in checked or ["(none)"])
                                          + "\n\n## ISSUE\n\n"
                                          + "\n".join(f"- {line}" for line in issues or ["(none)"])
                                          + "\n\n## CONVENTION\n", 1)
        report.write_text(text)
    return result or (1 if issues else 0)


if __name__ == "__main__":
    sys.exit(main())
