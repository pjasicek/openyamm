import os,sys,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);L=P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
for side in ['R','L']:
 os.environ['HAND_SIDE']=side;run('grip_from_source.py',[L,'2HandAxeIdle:8']);os.environ['GRIP_RENDER']=str(P/f'review/grip_{side}');os.environ['GRIP_SCALE']='.3';run('grip_solve.py',['work/rig_v4.blend','Standing',8])
shutil.copyfile(P/'work/grip_pose_R.json',P/'work/grip_pose.json')
