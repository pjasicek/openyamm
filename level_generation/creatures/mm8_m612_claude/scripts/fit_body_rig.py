"""Replay source measurements, independent mesh rings and automatic joint estimates."""
from pathlib import Path
import runpy,sys,os

P=Path(__file__).resolve().parents[1]
R=P.parents[2]
def step(name,*args):
    script=P/'scripts'/name
    sys.argv=[str(script),'--',*map(str,args)]
    runpy.run_path(str(script),run_name='__main__')
step('source_rest.py',R/'anim_library/humanoid_set/Armed.glb')
step('proportions.py','source',R/'anim_library/humanoid_set/Armed.glb')
step('meshy_joints.py',P/'meshy/rig_v1/result_rigged_character_glb_url.glb',P/'work/step1.blend')
step('fit_joints.py',P/'work/step1.blend','Body')

step('joint_xray.py',P/'work/step1.blend','Body',P/'work/joints_final.json',P/'review/joints',P/'work/joints.json')
step('build_rig.py')
step('fit_fingers.py',P/'work/rig_v1.blend')
