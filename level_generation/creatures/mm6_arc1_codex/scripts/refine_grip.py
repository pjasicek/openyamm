import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('grip_from_source.py',[P.parents[2]/'anim_library/humanoid_set/2Hand Bow.glb','2HandBowIdle:8'])
os.environ['R_HANDLE']='0.012'
os.environ['GRIP_RENDER']='review/grip'
run('grip_solve.py',['work/rig_fingers.blend','Standing','8'])
run('apply_grip.py',['work/rig_fingers.blend','work/rig_grip.blend'])
