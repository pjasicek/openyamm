import os, sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]]; runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('meshy_joints.py',p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend')
