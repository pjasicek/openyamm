"""Remove redundant feather compensation outside the preserved floor-folded corpse clips."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig']
 for role in C.ROLES:
  if role in ['Death','Dead']:continue
  C.reset();C.activate(role,0);a=bpy.data.actions[role];names=[b.name for b in r.pose.bones if b.name.startswith('Feather')]
  for slot in a.slots:
   for layer in a.layers:
    for strip in layer.strips:
     bag=strip.channelbag(slot)
     if bag:
      for fc in list(bag.fcurves):
       if any(fc.data_path.startswith('pose.bones["'+n+'"]')for n in names):bag.fcurves.remove(fc)
  for f in [0,int(a.frame_range[1])]:
   bpy.context.scene.frame_set(f)
   for n in names:
    b=r.pose.bones[n];b.matrix_basis.identity()
    for attr in ['location','rotation_quaternion','scale']:b.keyframe_insert(attr,frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
