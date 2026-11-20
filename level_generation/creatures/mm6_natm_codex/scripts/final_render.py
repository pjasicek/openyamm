import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_render as R
# High-resolution comparison uses the final animation and attachment placement.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/authoring_high.blend'))
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for n in ['SpearMesh','BucklerMesh']:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
with bpy.data.libraries.load(str(P/'work/runtime_lod0.blend'),link=False)as(src,dst):dst.actions=list(src.actions);dst.objects=['SpearMesh','BucklerMesh']
r=bpy.data.objects['Rig']
for o in dst.objects:
 bpy.context.collection.objects.link(o);o.parent=r
 for mod in o.modifiers:
  if mod.type=='ARMATURE':mod.object=r
for a in bpy.data.actions:a.use_fake_user=True
C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/high_reference_final.blend'))
R.render(P/'work/high_reference_final.blend',P/'review/reduction/final_reference700',P/'textures',700)
R.render(P/'work/runtime_lod0.blend',P/'review/reduction/final_lod0_700',P/'export/textures_lod0',700)
for level,size in [(1,550),(2,220),(3,88)]:
 R.render(P/'work/runtime_lod0.blend',P/f'review/reduction/final_reference{size}',P/'export/textures_lod0',size)
 R.render(P/f'work/runtime_lod{level}.blend',P/f'review/reduction/final_lod{level}_{size}',P/f'export/textures_lod{level}',size)
