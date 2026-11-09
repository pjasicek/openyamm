import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('meshy_joints.py',[p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend'])
run('arm_rings.py',[p/'work/step1.blend'])
run('joint_xray.py',[p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/joints',p/'work/meshy_joints.json'])
