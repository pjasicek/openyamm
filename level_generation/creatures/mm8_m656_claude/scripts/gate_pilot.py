import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
with bpy.data.libraries.load(str(P/'work/pilot_refined.blend')) as (src,dst):dst.actions=src.actions
for a in bpy.data.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot_actions.blend'))
run('twist_bones.py',P/'work/pilot_actions.blend',P/'work/pilot_twist.blend')
run('weights_fix.py',P/'work/pilot_twist.blend',P/'work/pilot_weight.blend')
run('finger_weights.py',P/'work/pilot_weight.blend',P/'work/pilot_final.blend')
run('floor_fit.py',P/'work/pilot_final.blend',P/'work/pilot_grounded.blend','Standing','Walking','Attack')
run('g6_head_clearance.py',P/'work/pilot_grounded.blend','Standing','Walking','Attack')
run('g4_weights.py',P/'work/pilot_grounded.blend','pilot_final','Attack:14','Attack:21','Attack:28')
run('export_pilot.py')
