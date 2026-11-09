import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=Path('anim_library/humanoid_set/2Hand Sword.glb').resolve()
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
clips={'Standing':'2HandSwordIdle','Walking':'2HandSwordWalk','Attack':'2HandSwordAttack1','Hit':'2HandSwordGetHitF1','Death':'2HandSwordDeath1','Fidget':'2HandSwordIdleAlert1'}
run('retarget.py',p/'work/rig_v1.blend',p/'work/rig_v2.blend',*[str(source)+':'+clip+':'+role for role,clip in clips.items()])
for side in ('R','L'):
 os.environ['GRIP_SIDE']=side
 run('grip_from_source.py',source,'2HandSwordIdle:0','2HandSwordAttack1:8')
