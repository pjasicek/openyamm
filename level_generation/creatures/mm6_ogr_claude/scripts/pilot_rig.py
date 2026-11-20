from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]; lib=p.parents[2]/'anim_library/humanoid_set'
def run(name,args=()):
 s=p/'scripts'/name; sys.argv=[str(s),'--']+[str(x) for x in args]
 runpy.run_path(str(s),run_name='__main__')
# Retarget walking with the measured clearance correction; preserve the other source motions.
os.environ['ARM_ABDUCT_DEG']='10'
run('retarget.py',[p/'work/rig_v2.blend',p/'work/rig_v2.blend',f'{lib/"Armed.glb"}:ArmedWalk:Walking'])
os.environ.pop('ARM_ABDUCT_DEG')
run('twist_bones.py',[p/'work/rig_v2.blend',p/'work/rig_v2t.blend'])
run('weights_fix.py',[p/'work/rig_v2t.blend',p/'work/rig_v3.blend'])
run('finger_weights.py',[p/'work/rig_v3.blend',p/'work/rig_v4f.blend'])
run('reduce_rigged.py',[p/'work/rig_v4f.blend',p/'work/rig_v4r.blend'])
run('subdivide_fingers.py',[p/'work/rig_v4r.blend',p/'work/rig_v4.blend'])
os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',[p/'work/rig_v4.blend','Standing',8])
run('apply_grip.py',[p/'work/rig_v4.blend',p/'work/rig_v5.blend'])
run('g5_hand_stretch.py',[p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit'])
run('g6_contacts.py',[p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit'])

for view in ('front','left','three_quarter'):
 run('clip_sheet.py',[p/'work/rig_v5.blend',p/'review'/('pilot_'+view),view,7,'Standing','Walking','Attack'])
