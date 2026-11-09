import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',['meshy/rig_v1/result_rigged_character_glb_url.glb','work/step1.blend'])
run('fit_merchant_joints.py')
run('build_rig.py')
run('fit_fingers.py',['work/rig_v1.blend'])
run('finger_joints.py',['work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',['work/rig_v1.blend'])
run('joint_xray.py',['work/step1.blend','Body','work/joints_final.json','review/joints','work/meshy_joints.json'])
