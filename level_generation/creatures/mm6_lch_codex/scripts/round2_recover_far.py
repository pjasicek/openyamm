"""Recover the previously accepted cheap far meshes without changing their geometry or weights."""
import bpy,bmesh,sys,json,copy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';W=P/'work/round2';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
for level in [2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'review/triangle_reduction/baseline/work/rig_textured.blend'))
 source=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];source.name='SourceHidden'
 for ob in list(bpy.data.objects):
  if ob not in (source,rig):bpy.data.objects.remove(ob,do_unlink=True)
 doc,binary=read_glb(P/'review/triangle_reduction/baseline/export/mm6_lch.glb');node=next(n for n in doc['nodes']if n.get('name')=='Lich');mi=doc['meshes'][node['mesh']]['extras']['openyamm_lods'][level-1]
 doc['meshes']=[copy.deepcopy(doc['meshes'][mi])];doc['meshes'][0].pop('extras',None);node['mesh']=0;doc.pop('animations',None)
 temp=W/f'accepted_lod{level}.glb';write_glb(temp,doc,binary)
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(temp));body=bpy.data.objects['Lich']
 bpy.context.view_layer.update();transform=source.matrix_world.inverted()@body.matrix_world
 body.data.transform(transform);body.parent=rig;body.matrix_world=source.matrix_world.copy()
 for mod in body.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 for ob in list(bpy.data.objects):
  if ob not in before and ob!=body:bpy.data.objects.remove(ob,do_unlink=True)
 body.name='Body';source.hide_render=True
 sm=source.data;sm.calc_loop_triangles();tri=[tuple(t.vertices)for t in sm.loop_triangles];tree=BVHTree.FromPolygons([v.co for v in sm.vertices],tri,all_triangles=True)
 me=body.data;uv=me.uv_layers.active;uv.name='UVMap';head=me.uv_layers.new(name='HeadUV');ha=me.attributes.new('head','INT','FACE');pa=me.attributes.new('piece','INT','POINT')
 for f in me.polygons:
  ishead=sum(uv.data[i].uv.x for i in f.loop_indices)/len(f.loop_indices)>.5;ha.data[f.index].value=int(ishead)
  for li in f.loop_indices:
   old=uv.data[li].uv.copy();old.x=(old.x*2080-(1056 if ishead else 0))/1024
   uv.data[li].uv=old;head.data[li].uv=old
 for v in me.vertices:
  hit=tree.find_nearest(v.co);ids=tri[hit[2]];nearest=min(ids,key=lambda i:(sm.vertices[i].co-v.co).length)
  pa.data[v.index].value=sm.attributes['piece'].data[nearest].value
 bpy.data.objects.remove(source,do_unlink=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}_accepted.blend'))
 print('ACCEPTED_FAR',level,sum(len(f.vertices)-2 for f in me.polygons),flush=True)
