"""Freeze native animated master UVs, retain a separate static texture upload."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_full_v1.blend'))
arm=bpy.data.objects['Goblin_Rig'];body=bpy.data.objects['Goblin_Body'];sword=bpy.data.objects['Goblin_Sword'];arm.data.pose_position='REST'
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(58),island_margin=.002,area_weight=.25,correct_aspect=True,scale_to_bounds=False);bpy.ops.uv.average_islands_scale();bpy.ops.object.mode_set(mode='OBJECT')
uv=body.data.uv_layers.active;uv.name='Goblin_Atlas_4K';parent=list(range(len(body.data.polygons)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
seen={}
for p in body.data.polygons:
 for li in p.loop_indices:
  key=(body.data.loops[li].vertex_index,*[round(x,6) for x in uv.data[li].uv])
  if key in seen:parent[root(p.index)]=root(seen[key])
  else:seen[key]=p.index
islands={}
for p in body.data.polygons:islands.setdefault(root(p.index),[]).append(p)
for ps in islands.values():
 loops=[i for p in ps for i in p.loop_indices];center=sum((body.data.vertices[body.data.loops[i].vertex_index].co for i in loops),Vector())/len(loops);factor=1.65 if center.z>1.31 else 1.35 if abs(center.x)>.47 and center.z<.83 else 1
 mid=sum((uv.data[i].uv for i in loops),Vector((0,0)))/len(loops)
 for i in loops:uv.data[i].uv=mid+(uv.data[i].uv-mid)*factor
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=True,rotate_method='ANY',scale=True,margin_method='FRACTION',margin=.003,shape_method='CONCAVE',merge_overlap=False);bpy.ops.object.mode_set(mode='OBJECT')
# Reuse the established local folded-chart repair, limited to this body collection.
import sys
sys.path.insert(0,str(OUT.parent/'blender_rebuild_20260928/authoring'))
import uv_repair
collection=bpy.data.collections.new('GB15 Character');bpy.context.scene.collection.children.link(collection);collection.objects.link(body)
uv_repair.ROOT=OUT;(OUT/'authoring').mkdir(exist_ok=True);uv_repair.repair();bpy.data.collections.remove(collection)
body['uv_contract']='Unique 4K body charts, nominal 12px padding; head 1.65x, hands 1.35x linear chart density; no stacking.'
arm.data.pose_position='POSE';bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work/native_uv_v1.blend'))
# Copy unmodified rest surface into a body-only, non-skinned upload; preserve the animated master on disk.
mesh=body.data.copy();static=bpy.data.objects.new('Goblin_body_texture_upload',mesh);bpy.context.scene.collection.objects.link(static)
bpy.ops.object.select_all(action='DESELECT');static.select_set(True);bpy.context.view_layer.objects.active=static
bpy.ops.export_scene.gltf(filepath=str(OUT/'work/body_for_texture_v1.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_apply=True,export_image_format='AUTO',export_texcoords=True,export_normals=True,export_tangents=True)
report={'body_triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'uv_islands':len(islands),'texture_resolution':4096,'padding_fraction':.003,'unique_asymmetric_charts':True,'animated_master':'work/native_uv_v1.blend','static_upload':'work/body_for_texture_v1.glb'}
for key in ['animated_master','static_upload']:report[key+'_sha256']=hashlib.sha256((OUT/report[key]).read_bytes()).hexdigest()
(OUT/'review/uv_preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
