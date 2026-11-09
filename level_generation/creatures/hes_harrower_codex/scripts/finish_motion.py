"""Run the established floor, tail and cloth passes, then hold the final fall pose."""
from pathlib import Path
import sys,runpy
import bpy
P=Path(__file__).resolve().parents[1]
roles=['Standing','Walking','Running','Attack','Attack2','Hit','Fidget','Roar','Spent']
clips=['Harrower_'+x for x in roles]
def run(script,src,dst,args):
 sys.argv=[script,'--',str(P/'work'/src),str(P/'work'/dst),*args]
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')
run('foot_floor.py','feet_prepared.blend','floor_final.blend',clips)
run('tail_anim.py','floor_final.blend','tail_final.blend',clips+['Harrower_Death'])
run('robe_sim.py','tail_final.blend','cloth_final.blend',['cloth',*clips,'Harrower_Death'])
run('robe_sim.py','cloth_final.blend','motion_final.blend',['mantle',*clips,'Harrower_Death'])
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
act=bpy.data.actions['Harrower_Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
sc.frame_set(int(act.frame_range[1]));pose={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Harrower_Dead'])
dead=bpy.data.actions.new('Harrower_Dead');dead.use_fake_user=True;rig.animation_data.action=dead
for f in (0,1):
 for n,m in pose.items():
  b=rig.pose.bones[n];b.matrix_basis=m
  for prop in ('location','rotation_quaternion','scale'):b.keyframe_insert(prop,frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_final.blend'))
