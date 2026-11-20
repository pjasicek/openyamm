import sys,os,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',['meshy/rig_v1/result_rigged_character_glb_url.glb','work/step1.blend'])
run('proportions.py',['source',ROOT/'anim_library/humanoid_set/Armed.glb'])
run('arm_rings.py',['work/step1.blend'])
run('build_rig.py')
run('fit_fingers.py',['work/rig_v1.blend'])
run('finger_joints.py',['work/rig_v1.blend'])
run('build_rig.py')
run('joint_xray.py',['work/step1.blend','Body','work/joints_final.json','review/g3','work/meshy_joints.json'])
for side in ['L','R']:run('hand_xray.py',['work/rig_v1.blend',side,'review/g3_hand_'+side])
