import bpy,bmesh,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/before/work/final_lod0.blend'))
b=bpy.data.objects['Body']; r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
head=b.copy();head.data=b.data.copy();head.modifiers.clear();head.parent=None;bpy.context.collection.objects.link(head)
bm=bmesh.new();bm.from_mesh(head.data)
ids={i for i,m in enumerate(head.data.materials) if 'Head' in m.name}
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index not in ids],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(head.data);bm.free()
head.data.uv_layers.active=head.data.uv_layers['MergedUV'];head.data.uv_layers['MergedUV'].active_render=True
for uv in list(head.data.uv_layers):
 if uv.name!='MergedUV':head.data.uv_layers.remove(uv)
head.data.materials.clear()
for f in head.data.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o==head)
bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/round2_head_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE',export_attributes=False)
print('HEAD_UPLOAD',len(head.data.polygons),len(head.data.vertices))
