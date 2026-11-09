import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
sys.argv=["meshy_joints.py","--","meshy/rig_v1/result_rigged_character_glb_url.glb","work/step1.blend"]
runpy.run_path(str(P/"scripts/meshy_joints.py"),run_name="__main__")
