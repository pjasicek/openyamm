#!/usr/bin/env python3
"""The Xeen playthrough chain (devdocs/xeen/ROADMAP.md section 5.10, tests/playthrough/PLAYBOOK.md): runs the
segments NN_*.yml of this folder in order with the Xeen build (build-xeen/game/openyamm). The first segment starts a
new Xeen game; each segment ends by saving a checkpoint (output/playthrough/xeen/checkpoints/) that the next one
loads. Writes each segment's log to output/playthrough/xeen/logs/ and the evidence (what the party did, where it
walked, what it won) to output/playthrough/xeen/report.md.

    python3 tests/playthrough/xeen/run.py            # every segment, stopping at the first failure
    python3 tests/playthrough/xeen/run.py 02 03      # these segments (their checkpoints must exist)
    python3 tests/playthrough/xeen/run.py --reload   # also save and load back after each step that settles the state
    python3 tests/playthrough/xeen/run.py --reload --reload-every 3   # at every third such point
    python3 tests/playthrough/xeen/run.py --game build/game/openyamm  # another binary

--reload runs copies of the segments (output/playthrough/xeen/reload/) with a `reload` step (save, then load straight
back) after the steps that settle the state, on their own checkpoints (output/playthrough/xeen/reload/checkpoints/),
so a reload run never changes the normal ones. A3 writes the segments with each act's quests; A1 keeps this runner.

The report lists the CONVENTION lines (D-68, PLAYBOOK section 2: logged stand-ins for progress the chain does not
play, such as a stat gate's shortfall) in their own section ahead of the segments; a clean run may have them.

Every segment runs from a copy (output/playthrough/xeen/segments/, or reload/ for --reload) with a party check just
before its final save_game (D-82, PLAYBOOK section 2): it logs `PARTY <segment> end: [c0] [c1] [c2] [c3]` (each
member's conditions) and fails the segment when a member is Dead, Eradicated, Petrified, Paralyzed or Unconscious
(the game's defeat list, Party::hasActableMember). The report lists those lines in a PARTY section.

A checkpoint that holds a map's state from before that map's last rebuild makes the game reset the map when the party
enters it (devdocs/SAVED_MAP_STATE_IDENTITY.md): its doors, monsters and map variables start fresh, though the quest
bits that the chain set there stay. The chain does not expect that, and a later step may fail for it (A1, 2026-11-22:
the reload runs of 83 and 85 started from reload checkpoints older than the XD-12 and DD-15 rebuilds). The runner
prints a STALE line for each segment whose log shows such a reset, and the report lists them in a STALE section:
rerun the chain (with --reload for the reload checkpoints) from the segment that last left the map.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "output/playthrough/xeen"
GAME = ROOT / "build-xeen/game/openyamm"
EVIDENCE = re.compile(
    r"^(PLAY |WALK |CLEAR |DEFEAT |RELOAD |PICKUP |CLIMB |CONSOLE |Scenario (passed|failure)|FAIL step|\s+\[\d+\] )")
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
CHECKPOINTS = "output/playthrough/xeen/checkpoints/"
RELOAD_CHECKPOINTS = "output/playthrough/xeen/reload/checkpoints/"
STALE = re.compile(r"^Saved map state: map (\S+) changed since the save; its state was reset")
QUIET = re.compile(r"^(PLAY done|WALK t=[\d.]+s at |CONSOLE qbit dump)")
CONVENTION = "PLAY CONVENTION "
PARTY = "PLAY PARTY "
PARTY_CHECK = """local shown, down = {}, {}
for i = 0, 3 do
  local c = conditions(i)
  shown[#shown + 1] = '[' .. c .. ']'
  for _, name in ipairs({'Dead', 'Eradicated', 'Petrified', 'Paralyzed', 'Unconscious'}) do
    if (' ' .. c .. ' '):find(' ' .. name .. ' ', 1, true) then down[#down + 1] = 'member ' .. i .. ' ' .. c; break end
  end
end
log('PARTY SEGMENT end: ' .. table.concat(shown, ' '))
if #down > 0 then error('PARTY DOWN at the end of segment SEGMENT: ' .. table.concat(down, ' | ')) end
"""


def segments(selected: list[str]) -> list[Path]:
    files = sorted(HERE.glob("[0-9][0-9]_*.yml"))
    if selected:
        files = [f for f in files if f.name[:2] in selected]
    return files


JOURNAL = ROOT / "assets_dev/worlds/xeen/data_tables/english/quests.txt"


def journal_rows() -> dict[int, tuple[list[int], list[int]]]:
    """Current Quests rows of english/quests.txt: qbit -> (required, forbidden)."""
    rows = {}
    for line in JOURNAL.read_text().splitlines()[2:]:
        cells = line.split("\t")
        if len(cells) >= 6 and cells[0].strip().isdigit():
            rows[int(cells[0])] = tuple([int(v) for v in cell.split(",") if v.strip()] for cell in (cells[4], cells[5]))
    return rows


def with_journal_checks(document: dict) -> None:
    """Expands `journal: {shown: [qbit], gone: [qbit], unstarted: [qbit]}` (A3 s38) into the qbit asserts that decide
    a Current Quests line, as JournalQuestTable::isVisible: shown = every required bit set and every forbidden bit
    clear; gone = its required bits and its one forbidden bit set; unstarted = its required bits clear."""
    rows, out = None, []
    for step in document["steps"]:
        if not (isinstance(step, dict) and "journal" in step):
            out.append(step)
            continue
        rows = rows or journal_rows()
        spec = step["journal"]
        for kind in spec:
            if kind not in ("shown", "gone", "unstarted"):
                raise SystemExit(f"journal step: unknown key {kind}")
        for qbit in spec.get("shown", []):
            required, forbidden = rows[qbit]
            out.append({"assert": {"qbit_set": required}})
            if forbidden:
                out.append({"assert": {"qbit_clear": forbidden}})
        for qbit in spec.get("gone", []):
            required, forbidden = rows[qbit]
            if len(forbidden) != 1:
                raise SystemExit(f"journal step: line {qbit} has {len(forbidden)} ending bits; assert them directly")
            out.append({"assert": {"qbit_set": required + forbidden}})
        for qbit in spec.get("unstarted", []):
            out.append({"assert": {"qbit_clear": rows[qbit][0]}})
    document["steps"] = out


def with_party_check(document: dict, number: str) -> None:
    """Inserts the party check (D-82) before the segment's last save_game."""
    steps = document["steps"]
    saves = [index for index, step in enumerate(steps) if isinstance(step, dict) and "save_game" in step]
    if not saves:
        raise SystemExit(f"segment {number} has no save_game")
    steps.insert(saves[-1], {"play_lua": {"source": PARTY_CHECK.replace("SEGMENT", number)}})


def checked(segment: Path) -> Path:
    """A copy of the segment with the party check, for the normal run."""
    document = yaml.safe_load(segment.read_text())
    with_journal_checks(document)
    with_party_check(document, segment.name[:2])
    target = OUT / "segments" / segment.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(document, sort_keys=False, width=1000))
    return target


def with_reloads(segment: Path, every: int) -> Path:
    """A copy of the segment with a reload after every `every`-th settling step, on its own checkpoints, and the
    party check before its last save."""
    document = yaml.safe_load(segment.read_text().replace(CHECKPOINTS, RELOAD_CHECKPOINTS))
    with_journal_checks(document)
    steps, out, eligible = document["steps"], [], 0
    for index, step in enumerate(steps):
        out.append(step)
        kind = next(iter(step)) if isinstance(step, dict) else None
        following = steps[index + 1] if index + 1 < len(steps) else None
        next_kind = next(iter(following)) if isinstance(following, dict) else None
        # an advance_runtime that only lets the line appear belongs to the status read after it
        if next_kind == "advance_runtime" and index + 2 < len(steps) and reads_status_line(steps[index + 2]):
            following = steps[index + 2]
        if kind in RELOAD_AFTER and next_kind not in DIALOGUE_GOES_ON and following is not None \
                and not reads_status_line(following) and not awaits_message(steps, index + 1):
            eligible += 1
            if eligible % every == 0:
                out.append({"reload": {}})
    document["steps"] = out
    document["id"] = document["id"] + ".reload"
    with_party_check(document, segment.name[:2])
    target = OUT / "reload" / segment.name
    target.write_text(yaml.safe_dump(document, sort_keys=False, width=1000))
    return target


def run(segment: Path, logs: Path, game: Path) -> tuple[bool, float, list[str], list[str]]:
    log = logs / f"{segment.stem}.log"
    start = time.monotonic()
    with log.open("w") as handle:
        result = subprocess.run([str(game), "--headless-run-scenario", str(segment.relative_to(ROOT)),
                                 "--scenario-no-color"], cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    seconds = time.monotonic() - start
    lines = [line.rstrip() for line in log.read_text(errors="replace").splitlines()]
    evidence = [line for line in lines if EVIDENCE.match(line) and not QUIET.match(line)]
    walked = [line for line in lines if line.startswith("WALK t=") and " at " in line and "stuck" not in line]
    # Keep one in five of the walk's positions: enough to follow the route.
    evidence += [f"(route) {line}" for line in walked[::5]]
    # Maps whose saved state the checkpoint held from before their last rebuild (reset on entry).
    stale = sorted({match.group(1) for line in lines if (match := STALE.match(line))})
    passed = result.returncode == 0 and any(line.startswith("Scenario passed") for line in lines)
    return passed, seconds, evidence, stale


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", nargs="*")
    parser.add_argument("--reload", action="store_true", help="save and load back at each settling step")
    parser.add_argument("--reload-every", type=int, default=1)
    parser.add_argument("--game", type=Path, default=GAME, help="the game binary (default build-xeen)")
    args = parser.parse_args()
    game = args.game if args.game.is_absolute() else ROOT / args.game
    if not segments(args.segments):
        print("no segments yet (NN_*.yml in tests/playthrough/xeen/)")
        return 0
    base = OUT / "reload" if args.reload else OUT
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    if args.reload:
        (OUT / "reload/checkpoints").mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    report = ["# Xeen playthrough" + (" (with save and load)" if args.reload else ""), "",
              f"Run {time.strftime('%Y-%m-%d %H:%M')}; logs in `{logs.relative_to(ROOT)}/`.", ""]
    passed_all = True
    sections, conventions, parties, stales = [], [], [], []
    for segment in segments(args.segments):
        segment = with_reloads(segment, max(1, args.reload_every)) if args.reload else checked(segment)
        ok, seconds, evidence, stale = run(segment, logs, game)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {segment.name} ({seconds:.0f} s)")
        if stale:
            line = (f"STALE {segment.stem}: the checkpoint held {', '.join(stale)} from before a rebuild; the game reset "
                    "them on entry (rerun the chain from the segment that last left them)")
            print(line)
            stales.append(f"- {line}")
        sections += [f"## {status}: {segment.stem} ({seconds:.0f} s)", "", "```", *evidence, "```", ""]
        conventions += [f"- {segment.stem}: {line[len('PLAY '):]}" for line in evidence if line.startswith(CONVENTION)]
        parties += [f"- {line[len(PARTY):]}" for line in evidence if line.startswith(PARTY)]
        parties += [f"- {segment.stem}: {line.strip()}" for line in evidence if "PARTY DOWN" in line]
        if not ok:
            passed_all = False
            break
    report += ["## STALE (maps reset on entry: the checkpoint predates their rebuild)", "", *(stales or ["(none)"]), "",
               "## CONVENTION", "", *(conventions or ["(none)"]), "",
               "## PARTY (each member's conditions before the segment's save; D-82)", "", *(parties or ["(none)"]),
               "", *sections]
    (base / "report.md").write_text("\n".join(report) + "\n")
    print(f"report: {base / 'report.md'}")
    return 0 if passed_all else 1


if __name__ == "__main__":
    sys.exit(main())
