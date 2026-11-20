"""Measure source frames and independent Pirate limb cross-sections."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=["source_rest.py","--",str(p.parents[2]/"anim_library/humanoid_set/1Hand.glb")]
runpy.run_path(str(p/"scripts/source_rest.py"),run_name="__main__")
sys.argv=["fit_joints.py","--",str(p/"work/step1.blend"),"Body"]
runpy.run_path(str(p/"scripts/fit_joints.py"),run_name="__main__")
assert (p/"work/joints.json").is_file()
