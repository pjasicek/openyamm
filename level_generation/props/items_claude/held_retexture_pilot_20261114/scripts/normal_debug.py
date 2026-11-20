"""Debug render of a sword export's normal map only (README.md): grey dielectric, low grazing light from +X then from
-X, orthographic top view, so a ridge shows one half lit and the other dark, consistently along every UV piece.
Usage: blender -b --python normal_debug.py -- <in.glb> <out_prefix>"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = [o for o in bpy.data.objects if o.type == 'MESH'][0]
mat = o.data.materials[0]
b = mat.node_tree.nodes['Principled BSDF']
for l in list(b.inputs['Base Color'].links) + list(b.inputs['Metallic'].links) + list(b.inputs['Roughness'].links):
    mat.node_tree.links.remove(l)
b.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1); b.inputs['Metallic'].default_value = 0
b.inputs['Roughness'].default_value = 0.6
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]); lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2
L = float(max(hi - lo))
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = L * 1.05; cam.location = Vector((c[0], c[1], hi[2] + 2)); cam.rotation_euler = (0, 0, 0)
sc.camera = cam; sc.render.resolution_x = sc.render.resolution_y = 1000
long_ax = int(np.argmax((hi - lo)[:2])); side = 1 - long_ax
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 4
for k, sgn in (('pos', 1), ('neg', -1)):
    d = Vector((0, 0, 1)); d[side] = sgn * 2.5
    sun.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{k}.png'
    bpy.ops.render.render(write_still=True)
