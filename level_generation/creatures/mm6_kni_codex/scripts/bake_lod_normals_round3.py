"""One normal map per LOD's tangent frame; base, mask and MR remain shared across LODs and tiers."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from collections import Counter
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';T=P/'textures/round3';sys.path.insert(0,str(P/'scripts'));from bake_components_round3 import components

def bake(lod):
 bpy.ops.wm.open_mainfile(filepath=str(W/f'rebaked_l{lod}.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 initial=set(bpy.data.objects);initial_actions=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(P/f'work/round2/baseline_body_l{lod}.glb'));added=set(bpy.data.objects)-initial;high=next(o for o in added if o.type=='MESH');hrig=next(o for o in added if o.type=='ARMATURE');hrig.animation_data.action=None
 for pb in hrig.pose.bones:pb.matrix_basis.identity()
 hi=components(high);lo=components(body);unique=sorted(set(hi));tree=kdtree.KDTree(len(hi))
 for v in high.data.vertices:tree.insert(v.co,v.index)
 tree.balance();mapping={c:Counter(hi[tree.find(v.co)[1]]for v in body.data.vertices if lo[v.index]==c).most_common(1)[0][0]for c in set(lo)};restore={}
 for obj,ids in [(high,hi),(body,[mapping[x]for x in lo])]:
  restore[obj]=[v.co.copy()for v in obj.data.vertices]
  for v,part in zip(obj.data.vertices,ids):
   k=unique.index(part);v.co+=Vector(((k%9)*3,(k//9)*3,0))
  obj.data.update()
 bpy.context.view_layer.update();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.03;sc.render.bake.max_ray_distance=.1;sc.render.bake.margin=12;sc.render.bake.normal_space='TANGENT';sc.render.bake.normal_r='POS_X';sc.render.bake.normal_g='POS_Y';sc.render.bake.normal_b='POS_Z'
 mat=body.data.materials[0].copy();body.data.materials.clear();body.data.materials.append(mat);node=mat.node_tree.nodes.new('ShaderNodeTexImage');size={1:1024,2:512,3:256}[lod];im=bpy.data.images.new(f'LOD{lod} rebaked normal',width=size,height=size,alpha=False);im.colorspace_settings.name='Non-Color';node.image=im;mat.node_tree.nodes.active=node
 body.hide_render=False;body.hide_viewport=False;body.hide_set(False);high.hide_render=False;high.hide_viewport=False;high.hide_set(False)
 for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);high.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.bake(type='NORMAL');im.filepath_raw=str(T/f'knight_normal_l{lod}.png');im.file_format='PNG';im.save()
 for obj,co in restore.items():
  for v,c in zip(obj.data.vertices,co):v.co=c
  obj.data.update()
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-initial_actions:bpy.data.actions.remove(a)
 bpy.context.view_layer.update();assert all(tuple(v.co)==tuple(c)for v,c in zip(body.data.vertices,restore[body]))
 # Only textures change. Original geometry and weights remain in the selected authoring blends.
 receipt={'lod':lod,'source':f'work/round2/baseline_body_l{lod}.glb','normal':f'textures/round3/knight_normal_l{lod}.png','size':size,'shared_by_all_tiers':True,'base_mask_MR_shared_with_LOD0':True,'geometry_unchanged':True};(R/f'normal_bake_l{lod}.json').write_text(json.dumps(receipt,indent=2));print('LOD NORMAL',receipt,flush=True)
if __name__=='__main__':
 for lod in [1,2,3]:bake(lod)
