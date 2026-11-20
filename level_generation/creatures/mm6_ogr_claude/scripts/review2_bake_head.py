"""Bake detailed head normals onto the reduced head while carrying its generated base-colour UVs unchanged."""
from pathlib import Path
import bpy,bmesh,sys,runpy
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
body=bpy.data.objects['Body'];source=bpy.data.objects['HeadSource'];rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
head=body.copy();head.data=body.data.copy();head.name='BakeHead';head.modifiers.clear();head.parent=None;bpy.context.collection.objects.link(head)
bm=bmesh.new();bm.from_mesh(head.data);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[hd]],context='FACES');loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(head.data);bm.free();head.data.uv_layers.active=head.data.uv_layers['HeadUV'];head.data.uv_layers['HeadUV'].active_render=True
mat=bpy.data.materials.new('HeadNormalBake');mat.use_nodes=True;head.data.materials.clear();head.data.materials.append(mat)
for f in head.data.polygons:f.material_index=0
im=bpy.data.images.new('HeadNormalBake',width=2048,height=2048,alpha=False);im.colorspace_settings.name='Non-Color'
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.004;scene.render.bake.max_ray_distance=.012;scene.render.bake.margin=16;scene.render.bake.use_clear=True
for o in bpy.context.view_layer.objects:
 o.hide_render=o not in [head,source];o.select_set(False)
source.hide_set(False);head.hide_set(False);source.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=head
bpy.ops.object.bake(type='NORMAL')
im.filepath_raw=str(p/'revision_02/head_normal_bake.png');im.file_format='PNG';im.save()
print('HEAD_NORMAL_BAKED',len(head.data.polygons))
# Raster positions/material regions on the actual fitted master for grading and neck correction.
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(p/'work/rig_v9.blend'),layer,'1024'];runpy.run_path(str(p/'scripts/uv_raster.py'),run_name='__main__')
