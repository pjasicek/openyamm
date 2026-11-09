import bpy,bmesh,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted.blend'));o=bpy.data.objects['Body'];me=o.data
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
# Smooth the compressed tail's noisy shallow ridges, retaining the outer silhouette and tip.
g=o.vertex_groups.new(name='TailSmooth')
for v in me.vertices:
 if v.co.y>.8:g.add([v.index],min(1.,(v.co.y-.8)*3), 'REPLACE')
m=o.modifiers.new('TailSurface','SMOOTH');m.vertex_group=g.name;m.factor=.45;m.iterations=3;bpy.ops.object.modifier_apply(modifier=m.name);o.vertex_groups.remove(o.vertex_groups["TailSmooth"])
me.materials.clear();mat=bpy.data.materials.new('ThunderLizard');mat.use_nodes=True;me.materials.append(mat)
if not me.uv_layers:me.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004);bpy.ops.uv.pack_islands(margin=.004,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/body_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
co=np.array([v.co[:] for v in me.vertices]);head=[]
for f in me.polygons:
 c=co[list(f.vertices)].mean(0);head.append(c[2]>1.31 and c[1]<-.25)
a=me.attributes.new('head','INT','FACE');a.data.foreach_set('value',np.array(head,dtype=int));mat=bpy.data.materials.new('ThunderLizardHead');mat.use_nodes=True;me.materials.append(mat)
bpy.ops.object.mode_set(mode='EDIT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select=bool(head[f.index])
bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.006);bpy.ops.uv.pack_islands(margin=.006,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
for f,h in zip(me.polygons,head):f.material_index=int(h)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_uv.blend'))
dup=o.copy();dup.data=me.copy();bpy.context.collection.objects.link(dup);bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not head[f.index]],context='FACES');bm.to_mesh(dup.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/head_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
print('Head triangles',sum(head),'body',len(head)-sum(head));assert 1500<sum(head)<7000
