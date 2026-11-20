"""Reimport exported geometry and recover only diagnostic region labels by exact rest position."""
import bpy,bmesh,sys,os,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];level=int(os.environ.get('MFP_LEVEL','0'));sel=json.loads((P/'review/reduction_soft/selection.json').read_text())[str(level)]
bpy.ops.wm.open_mainfile(filepath=str(P/sel['blend']));body=bpy.data.objects['Body'];kd=KDTree(len(body.data.vertices));ref={}
for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index);ref[v.index]=body.data.attributes['piece'].data[v.index].value
kd.balance();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.context.scene.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=str(P/f'work/final_check_lod{level}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';print('IMPORTED_OBJECTS',[(o.name,o.type,[g.name for g in o.vertex_groups][-10:]if o.type=='MESH'else[])for o in bpy.data.objects],flush=True);body=next(o for o in bpy.data.objects if o.type=='MESH'and'Knife'in o.vertex_groups);rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();g=body.vertex_groups['Knife'].index;prop={v.index for v in body.data.vertices if any(e.group==g and e.weight>.99 for e in v.groups)};assert prop
# BMesh topology edits drop custom split normals; carry the GLB corner normals through the split.
normal_attr=body.data.attributes.new('_runtime_normal','FLOAT_VECTOR','CORNER')
for dst,src in zip(normal_attr.data,body.data.corner_normals):dst.vector=src.vector
for name,remove in [('KnifeAsset',False),('Body',True)]:
 ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob);ob.name=name+'_part';bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if(v.index in prop)==remove],context='VERTS');bm.to_mesh(ob.data);bm.free()
 for face in ob.data.polygons:face.use_smooth=True
 normals=[v.vector[:]for v in ob.data.attributes['_runtime_normal'].data];assert len(normals)==len(ob.data.loops);ob.data.normals_split_custom_set(normals)
 ob.data.attributes.remove(ob.data.attributes['_runtime_normal'])
 if name=='Body':
  attr=ob.data.attributes.new('piece','INT','POINT');worst=0
  for v in ob.data.vertices:
   _,i,d=kd.find(ob.matrix_world@v.co);worst=max(worst,d);attr.data[v.index].value=ref[i]
  assert worst<1e-5,worst
bpy.data.objects.remove(body,do_unlink=True);bpy.data.objects['Body_part'].name='Body';bpy.data.objects['KnifeAsset_part'].name='KnifeAsset'
for act in bpy.data.actions:act.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/export_reimport_lod{level}.blend'));print('REIMPORT',level,'rest error m',worst,flush=True)
