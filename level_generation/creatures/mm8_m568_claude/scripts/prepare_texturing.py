"""Separate head texel budget while the body retexture unwraps the complete silhouette."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
for pb in rig.pose.bones:pb.matrix_basis.identity()
me.materials.clear()
for name in ['Salamander','SalamanderHead']:
 mat=bpy.data.materials.new(name);mat.use_nodes=True;me.materials.append(mat)
for f in me.polygons:f.material_index=0
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/body_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
pa=np.array([v.value for v in me.attributes['part'].data]);co=np.array([v.co[:] for v in me.vertices]);head=[]
for f in me.polygons:
 c=co[list(f.vertices)].mean(0);parts=pa[list(f.vertices)];head.append(c[2]>1.925 or (np.all(parts!=1) and abs(c[0])<.3))
attr=me.attributes.new('head','INT','FACE');attr.data.foreach_set('value',np.array(head,dtype=int))
if not me.uv_layers:me.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select=bool(head[f.index])
bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004,area_weight=0.0,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.004,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
for f,h in zip(me.polygons,head):f.material_index=int(h)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
dup=body.copy();dup.data=me.copy();dup.modifiers.clear();dup.parent=None;dup.vertex_groups.clear();bpy.context.collection.objects.link(dup)
bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not head[f.index]],context='FACES');bm.to_mesh(dup.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/head_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
print('HEAD FACES',sum(head),'BODY',len(head)-sum(head))
