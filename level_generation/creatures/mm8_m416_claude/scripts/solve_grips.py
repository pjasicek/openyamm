from pathlib import Path
import runpy,sys,os
P=Path(__file__).resolve().parents[1];R=P.parents[2];W=P/'work'
def run(n,args=()):
 f=P/'scripts'/n;sys.argv=[str(f),'--',*map(str,args)];runpy.run_path(str(f),run_name='__main__')
run('weights_fix.py')
run('finger_weights.py',[W/'weighted.blend',W/'fingered.blend'])
for side in ['R','L']:
 os.environ['GRIP_SIDE']=side;os.environ['R_HANDLE']='0.015' if side=='R' else '0.019';os.environ['GRIP_RENDER']=str(P/f'review/grip_{side}')
 run('grip_from_source.py',[R/'anim_library/humanoid_set/2Hand Crossbow.glb','2HandCrossbowAimingFire:1'])
 run('grip_solve.py',[W/'fingered.blend','AimSource',0])
