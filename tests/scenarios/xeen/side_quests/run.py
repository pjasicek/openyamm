#!/usr/bin/env python3
"""Runs the Xeen side-quest scenarios of this folder (each starts from a new game) with the Xeen build
(build-xeen/game/openyamm) and prints PASS or FAIL per quest. Logs go to output/scenarios/xeen/side_quests/. Owner: A3.

    python3 tests/scenarios/xeen/side_quests/run.py              # every quest
    python3 tests/scenarios/xeen/side_quests/run.py q-c20 x1-tam # quests whose file names start so
    python3 tests/scenarios/xeen/side_quests/run.py --reload q-c15   # also save and load back after each settling step
    python3 tests/scenarios/xeen/side_quests/run.py --repeat 2 q-c15 # twice each (determinism)

Each result lists the scenario's ISSUE, BLOCKER and CONVENTION lines (PLAYBOOK section 2). A run of every quest (no
names given) also writes report.md beside the logs.

--reload runs copies (output/scenarios/xeen/side_quests/reload/) with a `reload` step after every step that settles
the state, as the playthrough runner's --reload (tests/playthrough/xeen/run.py).

Every scenario runs from a copy (output/scenarios/xeen/side_quests/scenarios/, or reload/) that ends with a party log
(D-82, PLAYBOOK section 2): `PARTY end: [c0] [c1] [c2] [c3]`, each member's conditions. It asserts nothing (nothing
continues from a side quest); the runner itself fails a step that leaves nobody able to act (PARTY DOWN). Each result
line and the report show it.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GAME = ROOT / "build-xeen/game/openyamm"
LOGS = ROOT / "output/scenarios/xeen/side_quests"
PARTY_LOG = "log('PARTY end: [' .. conditions(0) .. '] [' .. conditions(1) .. '] [' .. conditions(2) .. '] [' .. conditions(3) .. ']')"
RELOAD_AFTER = {"assert", "walk_to", "play_lua", "travel", "party_defeat", "clear_hostiles", "climb", "pick_up"}
DIALOGUE_GOES_ON = {"select_topic", "press_action", "answer_input"}


def reads_status_line(step) -> bool:
    """A play_lua that reads the status line (status()) before it clicks anything: it reads what the step before it
    showed, and a status line does not outlive a save and load, so no reload goes between them (D-90's status-line
    finds and touches)."""
    payload = step.get("play_lua") if isinstance(step, dict) else None
    source = payload.get("source", "") if isinstance(payload, dict) else ""
    head = source.split("status()")[0] if "status()" in source else None
    return head is not None and "click(" not in head and "execute(" not in head


def awaits_message(steps, index: int) -> bool:
    """An advance_runtime that presents dialogs and an assert on the dialog right after it: it shows a message the
    step before it raised (a timer's or a click's evt.SimpleMessage), and a player cannot save over an open message,
    so no reload goes between them."""
    if index + 1 >= len(steps) or not isinstance(steps[index], dict) or not isinstance(steps[index + 1], dict):
        return False
    advance = steps[index].get("advance_runtime")
    check = steps[index + 1].get("assert")
    return isinstance(advance, dict) and bool(advance.get("present_dialogs")) and isinstance(check, dict) \
        and "dialog" in check


def prepared(scenario: Path, reload: bool) -> Path:
    """A copy of the scenario that ends with the party log; with reload, also a reload after each settling step (none
    before a step that continues a dialogue)."""
    document = yaml.safe_load(scenario.read_text())
    steps, out = document["steps"], []
    for index, step in enumerate(steps):
        out.append(step)
        kind = next(iter(step)) if isinstance(step, dict) else None
        following = steps[index + 1] if index + 1 < len(steps) else None
        next_kind = next(iter(following)) if isinstance(following, dict) else None
        # an advance_runtime that only lets the line appear belongs to the status read after it
        if next_kind == "advance_runtime" and index + 2 < len(steps) and reads_status_line(steps[index + 2]):
            following = steps[index + 2]
        if reload and kind in RELOAD_AFTER and next_kind not in DIALOGUE_GOES_ON and following is not None \
                and not reads_status_line(following) and not awaits_message(steps, index + 1):
            out.append({"reload": {}})
    out.append({"play_lua": {"source": PARTY_LOG}})
    document["steps"] = out
    if reload:
        document["id"] = document["id"] + ".reload"
    target = LOGS / ("reload" if reload else "scenarios") / scenario.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(document, sort_keys=False, width=1000))
    return target


def marked(text: str) -> list[str]:
    """The logged ISSUE, BLOCKER, CONVENTION and PARTY lines (play_lua's log() prints them as 'PLAY <line>')."""
    lines = []
    for line in text.splitlines():
        body = line[len("PLAY "):] if line.startswith("PLAY ") else line
        if body.startswith(("ISSUE", "BLOCKER", "CONVENTION", "PARTY end")):
            lines.append(body.rstrip())
    return lines


def main() -> int:
    args = sys.argv[1:]
    reload = "--reload" in args
    repeat = 1
    if "--repeat" in args:
        position = args.index("--repeat")
        repeat = int(args[position + 1])
        del args[position:position + 2]
    selected = [arg for arg in args if arg != "--reload"]
    files = sorted(HERE.glob("*.yml"))
    if selected:
        files = [f for f in files if any(f.name.startswith(s) for s in selected)]
    logs = LOGS / "reload" if reload else LOGS
    logs.mkdir(parents=True, exist_ok=True)
    failed = 0
    report = ["# Xeen side quests" + (" (with save and load)" if reload else ""), "",
              f"Run {time.strftime('%Y-%m-%d %H:%M')}; logs in `{logs.relative_to(ROOT)}/`.", ""]
    for scenario in files:
        scenario = prepared(scenario, reload)
        for attempt in range(repeat):
            log = logs / f"{scenario.stem}.log"
            start = time.monotonic()
            with log.open("w") as handle:
                result = subprocess.run([str(GAME), "--headless-run-scenario", str(scenario.relative_to(ROOT)),
                                         "--scenario-no-color"], cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
            text = log.read_text(errors="replace")
            ok = result.returncode == 0 and "Scenario passed" in text
            failed += 0 if ok else 1
            seconds = time.monotonic() - start
            print(f"{'PASS' if ok else 'FAIL'} {scenario.name} ({seconds:.0f} s)")
            notes = marked(text)
            failures = [line for line in text.splitlines() if line.startswith("Scenario failure")]
            for line in failures + notes:
                print("  " + line)
            report += [f"- {'PASS' if ok else 'FAIL'} `{scenario.stem}` ({seconds:.0f} s)",
                       *[f"  - {line}" for line in failures + notes]]
    if not selected:
        (logs / "report.md").write_text("\n".join(report) + "\n")
        print(f"report: {logs / 'report.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
