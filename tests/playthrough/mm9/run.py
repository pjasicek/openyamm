#!/usr/bin/env python3
"""
Run the MM9 playthrough: each segment is a headless scenario that loads the checkpoint the previous one saved
(output/playthrough/mm9/checkpoints/) and saves its own. Writes each segment's log to output/playthrough/mm9/logs/
and the evidence (what the party did, where it walked, what it won) to output/playthrough/mm9/report.md.

    python3 tests/playthrough/mm9/run.py            # every segment, stopping at the first failure
    python3 tests/playthrough/mm9/run.py 02 03      # these segments (their checkpoints must exist)
    python3 tests/playthrough/mm9/run.py --reload   # also save and load back after each step that settles the state
    python3 tests/playthrough/mm9/run.py --reload --reload-every 3   # at every third such point

--reload runs copies of the segments (output/playthrough/mm9/reload/) with a `reload` step (save, then load straight
back) after each assert, walk, scripted play, travel and defeat whose next step does not go on with an open
dialogue; a reload is skipped while a player could not save. Its checkpoints are kept apart
(output/playthrough/mm9/reload/checkpoints/), so a reload run never changes the normal ones.

The first segment starts from output/playthrough/mm9/checkpoints/00_after_council.oysav (README).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "output/playthrough/mm9"
GAME = ROOT / "build/game/openyamm"
EVIDENCE = re.compile(
    r"^(PLAY |WALK |CLEAR |DEFEAT |RELOAD |PICKUP |CLIMB |CONSOLE |Scenario (passed|failure)|FAIL step|\s+\[\d+\] )")
RELOAD_AFTER = {"assert", "walk_to", "play_lua", "travel", "party_defeat", "clear_hostiles", "climb", "pick_up"}
DIALOGUE_GOES_ON = {"select_topic", "press_action", "answer_input"}
CHECKPOINTS = "output/playthrough/mm9/checkpoints/"
RELOAD_CHECKPOINTS = "output/playthrough/mm9/reload/checkpoints/"
QUIET = re.compile(r"^(PLAY done|WALK t=[\d.]+s at |CONSOLE qbit dump)")


def segments(selected: list[str]) -> list[Path]:
    files = sorted(HERE.glob("[0-9][0-9]_*.yml"))
    if selected:
        files = [f for f in files if f.name[:2] in selected]
    return files


def with_reloads(segment: Path, every: int) -> Path:
    """A copy of the segment with a reload after every `every`-th settling step, on its own checkpoints."""
    document = yaml.safe_load(segment.read_text().replace(CHECKPOINTS, RELOAD_CHECKPOINTS))
    steps, out, eligible = document["steps"], [], 0
    for index, step in enumerate(steps):
        out.append(step)
        kind = next(iter(step)) if isinstance(step, dict) else None
        following = steps[index + 1] if index + 1 < len(steps) else None
        next_kind = next(iter(following)) if isinstance(following, dict) else None
        if kind in RELOAD_AFTER and next_kind not in DIALOGUE_GOES_ON and following is not None:
            eligible += 1
            if eligible % every == 0:
                out.append({"reload": {}})
    document["steps"] = out
    document["id"] = document["id"] + ".reload"
    target = OUT / "reload" / segment.name
    target.write_text(yaml.safe_dump(document, sort_keys=False, width=1000))
    return target


def run(segment: Path, logs: Path) -> tuple[bool, float, list[str]]:
    log = logs / f"{segment.stem}.log"
    start = time.monotonic()
    with log.open("w") as handle:
        result = subprocess.run([str(GAME), "--headless-run-scenario", str(segment.relative_to(ROOT)),
                                 "--scenario-no-color"], cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    seconds = time.monotonic() - start
    lines = [line.rstrip() for line in log.read_text(errors="replace").splitlines()]
    evidence = [line for line in lines if EVIDENCE.match(line) and not QUIET.match(line)]
    walked = [line for line in lines if line.startswith("WALK t=") and " at " in line and "stuck" not in line]
    # Keep one in five of the walk's positions: enough to follow the route.
    evidence += [f"(route) {line}" for line in walked[::5]]
    return result.returncode == 0 and any(line.startswith("Scenario passed") for line in lines), seconds, evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", nargs="*")
    parser.add_argument("--reload", action="store_true", help="save and load back at each settling step")
    parser.add_argument("--reload-every", type=int, default=1)
    args = parser.parse_args()
    base = OUT / "reload" if args.reload else OUT
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    if args.reload:
        (OUT / "reload/checkpoints").mkdir(parents=True, exist_ok=True)
        start = OUT / "checkpoints/00_after_council.oysav"
        if start.exists() and not (OUT / "reload/checkpoints" / start.name).exists():
            shutil.copy2(start, OUT / "reload/checkpoints" / start.name)
    report = ["# MM9 playthrough" + (" (with save and load)" if args.reload else ""), "",
              f"Run {time.strftime('%Y-%m-%d %H:%M')}; logs in `{logs.relative_to(ROOT)}/`.", ""]
    passed_all = True
    for segment in segments(args.segments):
        if args.reload:
            segment = with_reloads(segment, max(1, args.reload_every))
        ok, seconds, evidence = run(segment, logs)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {segment.name} ({seconds:.0f} s)")
        report += [f"## {status}: {segment.stem} ({seconds:.0f} s)", "", "```", *evidence, "```", ""]
        if not ok:
            passed_all = False
            break
    (base / "report.md").write_text("\n".join(report) + "\n")
    print(f"report: {base / 'report.md'}")
    return 0 if passed_all else 1


if __name__ == "__main__":
    sys.exit(main())
