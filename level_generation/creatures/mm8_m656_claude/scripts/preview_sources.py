"""Preview local source clips with the Barbarian's measured source-hand sword grip."""
from pathlib import Path
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[4]
PROJECT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "level_generation/creatures/mm6_bar1_claude/scripts/rpg_preview.py"
GROUPS = [
    ("1Hand", ["SwordAttackR1", "SwordAttackR2", "SwordAttackR3"]),
    ("Armed", ["ArmedIdle", "ArmedWalk", "ArmedDeath1"]),
    ("Unarmed", ["UnarmedGetHitF1"]),
]
for group, clips in GROUPS:
    source = ROOT / "anim_library/humanoid_set" / (group + ".glb")
    assert source.is_file() and PREVIEW.is_file()
    for view in ("front", "left", "three_quarter"):
        output = PROJECT / "review/g1" / group / view
        sys.argv = [str(PREVIEW), "--", str(source), str(output), view, "7", *clips]
        runpy.run_path(str(PREVIEW), run_name="__main__")
        rows = json.loads((output / "frames.json").read_text())
        assert len(rows) == len(clips) and all(len(row) == 7 for row in rows)
print("G1 source previews rendered; visual selection remains required.")
