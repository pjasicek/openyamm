import os, sys, runpy
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv = ["meshy_joints.py", "--", P+"/meshy/rig_v1/result_rigged_character_glb_url.glb", P+"/work/step1.blend"]
runpy.run_path(P+"/scripts/meshy_joints.py", run_name="__main__")
