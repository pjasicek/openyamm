#!/usr/bin/env python3
"""
Run the MM9 side-quest scenarios (tests/scenarios/mm9/side_quests/*.yml): standalone headless scenarios, each a new
game set up for one quest and played from its giver to its reward (README.md). Writes each scenario's log
(logs/<stem>.log) and evidence (reports/<stem>.md: dialogue lines, walks, clicks, ISSUE lines) under
output/side_quests/mm9/, and the run's whole report to report.md (rewritten by every run).

    python3 tests/scenarios/mm9/side_quests/run.py                   # every scenario
    python3 tests/scenarios/mm9/side_quests/run.py find_gungnir      # some (file stems, or a prefix of one)
    python3 tests/scenarios/mm9/side_quests/run.py --reload          # save and load back at each settling step
    python3 tests/scenarios/mm9/side_quests/run.py --repeat 2        # each scenario twice (determinism)

--reload uses the playthrough runner's rule (tests/playthrough/mm9/run.py): a `reload` step after every assert, walk,
scripted play, travel and defeat whose next step does not go on with an open dialogue.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "output/side_quests/mm9"

_spec = importlib.util.spec_from_file_location("playthrough_run", ROOT / "tests/playthrough/mm9/run.py")
playthrough = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(playthrough)


def scenarios(selected: list[str]) -> list[Path]:
    files = sorted(HERE.glob("*.yml"))
    if selected:
        files = [f for f in files if any(f.stem.startswith(s) for s in selected)]
    return files


def with_reloads(scenario: Path) -> Path:
    document = yaml.safe_load(scenario.read_text())
    steps, out = document["steps"], []
    for index, step in enumerate(steps):
        out.append(step)
        kind = next(iter(step)) if isinstance(step, dict) else None
        following = steps[index + 1] if index + 1 < len(steps) else None
        next_kind = next(iter(following)) if isinstance(following, dict) else None
        if kind in playthrough.RELOAD_AFTER and next_kind not in playthrough.DIALOGUE_GOES_ON and following is not None:
            out.append({"reload": {}})
    document["steps"] = out
    document["id"] = document["id"] + ".reload"
    target = OUT / "reload" / scenario.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(document, sort_keys=False, width=1000))
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenarios", nargs="*")
    parser.add_argument("--reload", action="store_true", help="save and load back at each settling step")
    parser.add_argument("--repeat", type=int, default=1, help="run each scenario this many times")
    args = parser.parse_args()
    base = OUT / "reload" if args.reload else OUT
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    report = ["# MM9 side quests" + (" (with save and load)" if args.reload else ""), "",
              f"Run {time.strftime('%Y-%m-%d %H:%M')}; logs in `{logs.relative_to(ROOT)}/`.", ""]
    failed = []
    for scenario in scenarios(args.scenarios):
        target = with_reloads(scenario) if args.reload else scenario
        for attempt in range(max(1, args.repeat)):
            ok, seconds, evidence = playthrough.run(target, logs)
            status = "PASS" if ok else "FAIL"
            suffix = f" #{attempt + 1}" if args.repeat > 1 else ""
            print(f"{status} {scenario.name}{suffix} ({seconds:.0f} s)", flush=True)
            section = [f"## {status}: {scenario.stem}{suffix} ({seconds:.0f} s)", "", "```", *evidence, "```", ""]
            report += section
            (base / "reports").mkdir(exist_ok=True)
            (base / "reports" / f"{scenario.stem}.md").write_text("\n".join(section) + "\n")
            if not ok:
                failed.append(scenario.stem)
                break
    (base / "report.md").write_text("\n".join(report) + "\n")
    print(f"report: {base / 'report.md'}")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
