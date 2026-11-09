import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for filename in ('work/textured_uv.blend','export/mm6_pfem_master.blend'):
 bpy.ops.wm.open_mainfile(filepath=str(p/filename))
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in list(bag.fcurves):
      if any(n in fc.data_path for n in ('B_L_Toe0','B_R_Toe0')):bag.fcurves.remove(fc)
 bpy.ops.wm.save_as_mainfile(filepath=str(p/filename))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/roundtrip.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(71)
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=[o.matrix_world@v.co for v in m.vertices]
print('DEATH BOUNDS BLENDER',[(min(v[i] for v in P),max(v[i] for v in P)) for i in range(3)])
print('HEAD',tuple(r.matrix_world@r.pose.bones['B_Head'].head))
ev.to_mesh_clear()
