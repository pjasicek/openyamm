"""Inspect the immutable Smart Topology return in an isolated Blender scene."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
sys.argv = ["examine_parts.py", "--", str(p / "meshy/smart_topology_v1/model_urls_glb.glb"), "st_v1"]
runpy.run_path(str(p / "scripts/examine_parts.py"), run_name="__main__")
assert (p / "work/st_v1_parts.blend").is_file()
sys.argv = ["proportions.py", "--", "source", str(repo / "anim_library/humanoid_set/1Hand.glb")]
runpy.run_path(str(p / "scripts/proportions.py"), run_name="__main__")
