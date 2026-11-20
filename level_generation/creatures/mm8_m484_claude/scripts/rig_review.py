from pathlib import Path
import sys,runpy,os
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('hand_xray.py',['work/rig_v1.blend','R','review/hand_rest'])
run('joint_xray.py',['work/step1.blend','Body','work/joints_final.json','review/joints','work/meshy_joints.json'])
run('proportions.py',['source',P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'])
