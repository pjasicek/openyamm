import bpy,bmesh,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'))
mesh=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
names={g.index:g.name for g in mesh.vertex_groups};weight={v.index:sum(g.weight for g in v.groups if names[g.group] in ['Head','Jaw']) for v in mesh.data.vertices}
mat=bpy.data.materials.new('WyrmHead');mat.use_nodes=True;mesh.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in mesh.data.polygons:
    f.select=sum(weight[v] for v in f.vertices)/len(f.vertices)>.48
    if f.select:f.material_index=1
original_uv=[u.uv.copy() for u in mesh.data.uv_layers.active.data]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(75),island_margin=.006);bpy.ops.uv.pack_islands(rotate=True,margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
for f in mesh.data.polygons:
    if f.material_index==0:
        for li in f.loop_indices:mesh.data.uv_layers.active.data[li].uv=original_uv[li]
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_uv.blend'))
head=mesh.copy();head.data=mesh.data.copy();head.modifiers.clear();head.parent=None;bpy.context.collection.objects.link(head)
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bm.to_mesh(head.data);bm.free()
head.data.materials.clear();head.name='WyrmHead'
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/wyrm_head_neutral.glb'),use_selection=True,export_format='GLB',export_skins=False,export_animations=False,export_materials='NONE')
print('HEAD',len(head.data.polygons),'triangles')
