"""Preview existing one-handed spear sources before selecting Triton motion."""
from pathlib import Path
import json
import os
import runpy
import sys

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
PREVIEW = ROOT / "level_generation/creatures/mm6_natm_claude/scripts/spear_preview.py"
SOURCE = ROOT / "anim_library/humanoid_set/1Hand.glb"
assert SOURCE.is_file() and PREVIEW.is_file()
# Triton raises the trident overhand; source handedness is mirrored during retargeting.
os.environ["SPEAR_SIGN"] = "1"
for view in ("front", "left", "three_quarter"):
    out = PROJECT / "review/g1_forward" / view
    sys.argv = [str(PREVIEW), "--", str(SOURCE), str(out), view, "7",
                "SpearAttackR1", "SpearAttackR4", "SpearAttackR6"]
    runpy.run_path(str(PREVIEW), run_name="__main__")
    rows = json.loads((out / "frames.json").read_text())
    assert len(rows) == 3 and all(len(row) == 7 for row in rows)
print("G1 candidate renders complete; visual selection pending.")
