import bpy,sys,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from rebake_render import render
for expansion in [.005,.01]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/far_pixels3.blend'));r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();xyz=[v.co.copy()for v in me.vertices];ev.to_mesh_clear();pv=[x.value for x in ob.data.attributes['piece'].data];names=[g.name for g in ob.vertex_groups];matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted()for g in ob.vertex_groups if g.name in r.pose.bones}
 for v in ob.data.vertices:
  if pv[v.index]>=201:continue
  hand=sum(g.weight for g in v.groups if names[g.group]=='B_L_Hand'or names[g.group].startswith('B_L_Finger'));w=(1-hand)**2;target=xyz[v.index].copy();target.x*=1+expansion*w;target.y*=1+expansion*w
  matrix=Matrix([[0]*4 for _ in range(4)])
  for g in v.groups:
   if g.group in matrices:matrix+=matrices[g.group]*g.weight
  v.co=matrix.inverted()@target
 r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();tag=f'round4_outline{int(expansion*1000)}';path=P/f'work/round4/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,tag,3,parts=('actor',),palette=('round4_shared','lzd_a'),samples=128,camera_path=P/'review/round4/camera.json')
