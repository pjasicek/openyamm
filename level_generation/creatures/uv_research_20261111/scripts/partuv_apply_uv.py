"""PartUV study: write packed per-face UVs onto the mesh and export a measurement GLB (skinned, one blank 2048 image
per material so claude_shared/texture_quality.py measures each texture set) and optionally the neutral static upload
GLB in the format of mm9_magreeb_claude/scripts/uv_atlas_v8.py (mesh only, no skin, materials or attributes).

Args: <in .blend|.glb> <mesh object name> <out measure glb> <out upload glb or -> set=<mesh.npz>:<uv.npz> [...]
      [upload_material=<substring>] [save_blend=<path>] [blender_pack=raw|avg|fraction]
      [image_size=<w>,<h>] (measurement image, default 2048,2048)
  set: a mesh npz from partuv_export_mesh.py (its face_index says which faces) and a packed uv npz (uv M x 3 x 2);
  several sets for a body with separate texture sets. upload_material keeps only the faces of materials whose name
  contains the substring in the upload (one Meshy job per texture set).
"""
import os
import sys

import bmesh
import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, NAME, MEASURE, UPLOAD = argv[:4]
sets = [a.split('=', 1)[1].split(':') for a in argv[4:] if a.startswith('set=')]
opts = dict(a.split('=', 1) for a in argv[4:] if not a.startswith('set='))
if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
rig = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        rig = o
        if o.animation_data:
            o.animation_data.action = None
        for b in o.pose.bones:
            b.matrix_basis.identity()
bpy.context.view_layer.update()
obj = bpy.data.objects[NAME]
me = obj.data
corner = np.zeros((len(me.polygons), 3, 2))
if me.uv_layers:
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get('uv', flat)
    flat = flat.reshape(-1, 2)
    corner = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
for mesh_npz, uv_npz in sets:
    faces = np.load(mesh_npz)['face_index']
    corner[faces] = np.load(uv_npz)['uv']
for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
me.uv_layers.new(name='UVMap')
flat = np.zeros((len(me.loops), 2), np.float32)
for p in me.polygons:
    flat[list(p.loop_indices)] = corner[p.index]
me.uv_layers['UVMap'].data.foreach_set('uv', flat.ravel())
if opts.get('blender_pack'):
    # PartUV's own packing (pack/pack_blender.py of the repo): pack_islands(margin=0.001) on the unpacked charts, each
    # in its own unit square; 'avg' first evens the island scales (commented out in their script)
    bpy.context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    if opts['blender_pack'] == 'avg':
        bpy.ops.uv.average_islands_scale()
    if opts['blender_pack'] == 'fraction':
        # uv_atlas.py's packer='blender' call: islands keep their relative scale (head factor), exact 2 px margin
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='ANY', scale=True,
                                merge_overlap=False, margin_method='FRACTION', margin=2 / 2048,
                                shape_method='CONCAVE')
    else:
        bpy.ops.uv.pack_islands(margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
if opts.get('save_blend'):
    bpy.ops.wm.save_as_mainfile(filepath=opts['save_blend'])

if UPLOAD != '-':
    dup = obj.copy()
    dup.data = me.copy()
    dup.modifiers.clear()
    dup.parent = None
    dup.matrix_world = obj.matrix_world
    bpy.context.scene.collection.objects.link(dup)
    if opts.get('upload_material'):
        keep = {i for i, m in enumerate(dup.data.materials) if m and opts['upload_material'] in m.name}
        bm = bmesh.new()
        bm.from_mesh(dup.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context='FACES')
        bm.to_mesh(dup.data)
        bm.free()
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    os.makedirs(os.path.dirname(os.path.abspath(UPLOAD)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                              export_skins=False, export_animations=False, export_materials='NONE',
                              export_attributes=False)
    print('UPLOAD', UPLOAD, len(dup.data.polygons))
    bpy.data.objects.remove(dup)

# measurement copy: one blank image shared by every material of the object (the object is one texture set;
# texture_quality.py measures per base-colour image)
if not me.materials:
    me.materials.append(bpy.data.materials.new('Body'))
w, h = map(int, opts.get('image_size', '2048,2048').split(','))
img = bpy.data.images.new('measure_0', w, h)
img.generated_color = (0.5, 0.5, 0.5, 1.0)
img.pack()
for mat in me.materials:
    if mat is None:
        continue
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    out = nodes.new('ShaderNodeOutputMaterial')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = img
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
for o in bpy.data.objects:
    o.select_set(o == obj or o == rig)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=MEASURE, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=True, export_animations=False, export_materials='EXPORT',
                          export_image_format='JPEG', export_attributes=False)
print('MEASURE', MEASURE)
