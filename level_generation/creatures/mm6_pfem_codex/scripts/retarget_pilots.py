import bpy,runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];s=p/'scripts'
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(s/name),run_name='__main__')
run('retarget.py',p/'work/rig_fingers.blend',p/'work/pilots_raw.blend',
 'anim_library/humanoid_set/Relax.glb:RelaxIdle:Standing',
 'anim_library/humanoid_set/Relax.glb:RelaxWalkForward:Walking',
 'anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1:Death')
run('twist_bones.py',p/'work/pilots_raw.blend',p/'work/pilots_twist.blend')
for view in ('front','left','three_quarter'):
 run('clip_sheet.py',p/'work/pilots_twist.blend',p/'review/pilots_raw'/view,view,5,'Standing','Walking','Death')
run('g5_hand_stretch.py',p/'work/pilots_twist.blend','Standing','Walking','Death')
