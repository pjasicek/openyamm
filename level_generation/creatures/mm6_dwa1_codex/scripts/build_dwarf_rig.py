import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('fit_dwarf_joints.py')
run('build_rig.py')
run('fit_fingers.py',['work/rig_v1.blend'])
run('finger_joints.py',['work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',['work/rig_v1.blend'])
run('joint_xray.py',['work/step1.blend','Body','work/joints_final.json','review/joints','work/meshy_joints.json'])
for side in ['R','L']:run('hand_xray.py',['work/rig_v1.blend',side,'review/hand_'+side])
