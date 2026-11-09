#!/usr/bin/env python3
"""Add the 2026-10-31 notes to a map README: the lighting note under its `## Baked lighting` heading, and a section on
the rebuild for the invisible ramp bottoms (from rebuild_1031/<stem>.log). Idempotent (skips a README that has them).

    python3 level_generation/projects/mm9r_common/rebuild_1031/readme_notes.py <stem>...
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LOGS = Path(__file__).resolve().parent
LIGHT = ("> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the "
         "end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar "
         "pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.\n")
MARK = "## Rebuild 2026-10-31: invisible ramp bottoms"


def section(stem: str) -> str:
    log_path = LOGS / f"{stem}.log"
    text = log_path.read_text() if log_path.exists() else ""
    start = re.search(r"rebuild start (\S+ \S+)", text)
    end = re.search(r"convert exit (\d+) end (\S+)", text)
    dropped = re.search(r"invisible bottoms dropped (\d+)", text)
    wrote = re.search(r"faces=(\d+)", text)
    scenarios = re.findall(r"scenario (\S+) exit (\d+) (\d+) failed asserts; (Scenario \w+)?", text)
    project = ROOT / f"level_generation/projects/mm9r_{stem}"
    lines = [MARK, "",
             f"Rebuilt {start.group(1) if start else '?'} (convert.py from the current shared converter, end "
             f"{end.group(2) if end else '?'}): {dropped.group(1) if dropped else '?'} down-facing faces of invisible "
             f"collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp "
             f"wedges and helper brushes resting at most the party's height over a floor, which stopped the party on "
             f"stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, \"Package change: invisible brush "
             f"bottoms\"); the BLV now has {wrote.group(1) if wrote else '?'} faces. The rebuild also carries the "
             f"converter's other changes of the day (monster collision sizes, water)."]
    if scenarios:
        lines.append("Scenarios after the rebuild: " + ", ".join(
            f"`{name}` {'pass' if code == '0' and fails == '0' else f'FAIL (exit {code}, {fails} failed asserts)'}"
            for name, code, fails, _ in scenarios) + ".")
    probes = project / "work/stair_probes.json"
    if probes.exists() and "stair probes" in text:
        found = json.loads(probes.read_text())
        stairs = [p for p in found if p.get("kind", "stair") == "stair"]
        blockers = [p for p in found if p.get("kind") == "blocker"]
        if stairs:
            better = sum(1 for p in stairs if p["after_xy_z"] and p["before_xy_z"]
                         and p["after_xy_z"][0] > p["before_xy_z"][0] + 20)
            lines.append(f"Stair probes (`scenario_stair_probes.yml`, `../mm9r_common/stair_probes.py`): {len(stairs)} "
                         f"walks up the ramps over dropped bottoms, before / after (xy, z native): "
                         + "; ".join(f"{p['before_xy_z']} / {p['after_xy_z']}" for p in stairs)
                         + f"; {better} walk farther after the rebuild.")
        if blockers:
            same = sum(1 for p in blockers if p["after_xy_z"] and p["before_xy_z"]
                       and abs(p["after_xy_z"][0] - p["before_xy_z"][0]) < 2)
            lines.append(f"Blocker probes: {len(blockers)} walks into helper brushes resting on the floor stop "
                         f"short of them, {same} identical before and after (their sides still block).")
    return "\n".join(lines) + "\n"


def main() -> int:
    for stem in sys.argv[1:]:
        path = ROOT / f"level_generation/projects/mm9r_{stem}/README.md"
        text = path.read_text()
        if "Baked lighting removed 2026-10-31" not in text:
            match = re.search(r"^## [^\n]*Baked lighting[^\n]*\n", text, re.M)
            if match:
                text = text[:match.end()] + "\n" + LIGHT + text[match.end():]
            else:
                text += "\n## Baked lighting\n\n" + LIGHT
        if MARK not in text:
            text = text.rstrip("\n") + "\n\n" + section(stem)
        path.write_text(text)
        print("noted", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
