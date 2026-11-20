"""Smart UV Project on the Treant (rest pose; after mm7_m278_claude/scripts/uv_export.py), then a neutral unrigged GLB
for the Meshy retexture (enable_original_uv: true). Face islands (the front of the trunk between the roots and the
crown: mouth, lips, teeth, nose ridge, eye area) get 2x texel density (claude_shared/uv_head_density.py) through a
temporary vertex group 'Face'. Args: -- <in blend> <out blend>   (writes texturing/m479_upload.glb)  env UV_ANGLE (rad, default 1.55: fewer strand islands)"""
import bpy, os, sys
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
from uv_head_density import scale_head_islands
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
mesh = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
co = np.array([tuple(v.co) for v in mesh.data.vertices])
pa = np.zeros(len(co), np.int32); mesh.data.attributes['part'].data.foreach_get('value', pa)
face = ((co[:, 1] < -0.3) & (np.abs(co[:, 0]) < 0.8) & (co[:, 2] > 0.3) & (co[:, 2] < 2.2)) | (pa > 0)
g = mesh.vertex_groups.new(name='Face'); g.add([int(i) for i in np.nonzero(face)[0]], 1.0, 'REPLACE')
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=float(os.environ.get('UV_ANGLE', '1.55')), island_margin=0.002, area_weight=0.0,
                         scale_to_bounds=False)
scale_head_islands(mesh, ('Face',), factor=2.0)
# concave packing: the first pass (default bounding-box packing) covered only 13 % of the atlas with ~1800 strand islands
bpy.ops.uv.pack_islands(shape_method='CONCAVE', margin_method='FRACTION', margin=0.002, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.vertex_groups.remove(mesh.vertex_groups['Face'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None; dup.vertex_groups.clear()
for at in [a.name for a in dup.data.attributes if a.name in ('piece', 'orig_co', 'part')]:
    dup.data.attributes.remove(dup.data.attributes[at])
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'm479_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('UVEXPORT face islands', int(face.sum()), 'verts; exported texturing/m479_upload.glb')
