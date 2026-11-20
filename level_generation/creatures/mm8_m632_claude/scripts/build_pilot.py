"""Initial retarget/deformation pilot; final carry/contact/timing pass follows inspection."""
import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(name,*args):
    sys.argv=[name,'--',*map(str,args)]
    runpy.run_path(str(P/'scripts'/name),run_name='__main__')
source=Path('anim_library/humanoid_set/2Hand Crossbow.glb').resolve()
run('retarget.py',W/'rig_v1.blend',W/'motion_source.blend',*[f'{source}:2HandCrossbow{clip}:{name}' for clip,name in [('Idle','Standing'),('Walk','Walking'),('Attack2','Attack'),('GetHitF1','Hit'),('Death1','Death')]])
run('retarget_mixamo.py',W/'motion_source.blend',W/'motion_mixamo.blend',f"{Path('anim_library/mixamo/Standard Run.fbx').resolve()}:Running")
run('weights_fix.py',W/'motion_mixamo.blend',W/'motion_weights.blend')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.05,0.3'
run('twist_bones.py',W/'motion_weights.blend',W/'motion_twist.blend')
run('finger_weights.py',W/'motion_twist.blend',W/'rig_pilot.blend')
for view in ('front','left','back'):
    run('pilot_sheet.py',W/'rig_pilot.blend',P/f'review/pilot_{view}',view,5,'Standing','Walking','Attack','Hit','Death','Running')
