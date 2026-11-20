"""G1: preview local sword clips on their original source mannequin before model generation."""
from pathlib import Path
import runpy
import sys

project = Path(__file__).resolve().parents[1]
scripts = project / "scripts"
repo = project.parents[2]
source = repo / "anim_library/humanoid_set/1Hand.glb"
assert source.is_file()
sys.path.insert(0, str(scripts))
sys.argv = ["grip_from_source.py", "--", str(source), "SwordAttackR1:0"]
runpy.run_path(str(scripts / "grip_from_source.py"), run_name="__main__")
for view in ["front", "left", "three_quarter"]:
    out = project / "review" / ("g1_" + view)
    sys.argv = ["rpg_preview.py", "--", str(source), str(out), view, "7",
                "SwordAttackR1", "SwordAttackR2", "SwordAttackR4"]
    runpy.run_path(str(scripts / "rpg_preview.py"), run_name="__main__")
    assert (out / "frames.json").is_file()
