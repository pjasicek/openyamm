"""Reuse the previously fitted distance topology with the shared near UV/material set."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
for level in [2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/near_runtime.blend'));rig=bpy.data.objects['Rig'];high=bpy.data.objects['Body'];high.name='NearSurface';rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 with bpy.data.libraries.load(str(P/f'work/rebake/lod{level}_selected_baked.blend'),link=False)as(src,dst):dst.objects=['Body']
 low=dst.objects[0];bpy.context.collection.objects.link(low);low.name='Body'
 for mod in low.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 # Reuse the near map indices and remap UVs by interpolated surface correspondence.
 for index,mat in enumerate(low.data.materials):
  name=mat.name.split('.')[0];group='Head'if'Head'in name else'Bow'if'Bow'in name else'Body';new=next(m for m in high.data.materials if ('Head'if'Head'in m.name else'Bow'if'Bow'in m.name else'Body')==group);low.data.materials[index]=new
 pv=np.array([x.value for x in low.data.attributes['piece'].data]);names=[g.name for g in low.vertex_groups]
 for v in low.data.vertices:
  z=v.co.z
  if pv[v.index]==1 and z>.96:
   t=min(1,(z-.96)/.05);v.co.z+=.14*t
   for g in low.vertex_groups:g.remove([v.index])
   low.vertex_groups['B_Pelvis'].add([v.index],1-.6*t,'REPLACE');low.vertex_groups['B_Spine'].add([v.index],.6*t,'REPLACE')
  if pv[v.index]==2 and z<1.14:
   t=max(0,min(1,(1.14-z)/.09));v.co.z-=.065*t;weights={g.group:g.weight*(1-.65*t)for g in v.groups};weights[low.vertex_groups['B_Pelvis'].index]=weights.get(low.vertex_groups['B_Pelvis'].index,0)+.65*t
   for gi,w in weights.items():low.vertex_groups[gi].add([v.index],w,'REPLACE')
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
 # UVs are transferred in neutral space, before any skeletal deformation.
 for m in high.modifiers:m.show_viewport=False
 for m in low.modifiers:m.show_viewport=False
 m=low.modifiers.new('Shared near UV correspondence','DATA_TRANSFER');m.object=high;m.use_loop_data=True;m.data_types_loops={'UV'};m.loop_mapping='POLYINTERP_NEAREST';m.islands_precision=1.;m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 for m in low.modifiers:m.show_viewport=True
 bpy.data.objects.remove(high,do_unlink=True)
 for o in list(bpy.data.objects):
  if o.type=='ARMATURE'and o!=rig:bpy.data.objects.remove(o,do_unlink=True)
 for a in bpy.data.actions:
  if a.name.endswith('.001'):bpy.data.actions.remove(a)
 path=P/f'work/round4/reuse_distance{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,f'round4_reuse{level}',level,parts=('actor',),palette=('round4_shared','lzd_a'),samples=32,camera_path=P/'review/round4/camera.json')
