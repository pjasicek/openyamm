import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];kd=KDTree(len(body.data.vertices));ref={}
for v in body.data.vertices:
 kd.insert(body.matrix_world@v.co,v.index);ref[v.index]=(body.data.attributes['piece'].data[v.index].value,body.data.attributes['finger'].data[v.index].value)
kd.balance();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_dwa1_runtime_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';body=next(o for o in bpy.data.objects if o.type=='MESH');body.name='Body'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();g=body.vertex_groups['Axe'].index;sw={v.index for v in body.data.vertices if any(e.group==g and e.weight>.99 for e in v.groups)};assert sw
for name,remove in [('Axe',False),('Body',True)]:
 ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob);ob.name=name+'_part';bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.index in sw)==remove],context='VERTS');bm.to_mesh(ob.data);bm.free()
 if name=='Body':
  worst=0;attrs={n:ob.data.attributes.new(n,'INT','POINT')for n in ['piece','finger']}
  for v in ob.data.vertices:
   _,i,d=kd.find(ob.matrix_world@v.co);worst=max(worst,d)
   for n,val in zip(['piece','finger'],ref[i]):attrs[n].data[v.index].value=val
  assert worst<1e-5,worst;print('EXPORT REST CORRESPONDENCE',worst)
bpy.data.objects.remove(body,do_unlink=True);bpy.data.objects['Body_part'].name='Body';bpy.data.objects['Axe_part'].name='Axe';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/export_reimport.blend'))
