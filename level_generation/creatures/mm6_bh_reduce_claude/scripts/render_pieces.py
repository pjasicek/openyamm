"""Mouth close-up of the welded source with every connected piece in its own colour (work/components.npy), front and
three-quarter. Usage: blender -b -P render_pieces.py -- <mesh npz> <components npy> <out prefix>"""
import sys, math, colorsys, bpy, numpy as np
from mathutils import Vector
npz, comp, out = sys.argv[sys.argv.index('--') + 1:][:3]
d = np.load(npz); c = np.load(comp)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('M'); me.from_pydata(d['verts'].tolist(), [], d['faces'].tolist()); me.update()
ob = bpy.data.objects.new('M', me); bpy.context.scene.collection.objects.link(ob)
ids = sorted(set(c.tolist()))
for k in ids:
    m = bpy.data.materials.new(f'p{k}'); m.use_nodes = True
    r, g, b = colorsys.hsv_to_rgb((k * 0.137) % 1, .7 if k != 1 else .05, .9 if k != 1 else .5)
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (r, g, b, 1)
    me.materials.append(m)
me.polygons.foreach_set('material_index', [ids.index(k) for k in c.tolist()])
sc = bpy.context.scene
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .32
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(60), 0, math.radians(180)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .5, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 800
sc.render.engine = 'BLENDER_EEVEE'
c0 = Vector((0, -.3, .36))
for view, dv in {'front': (0, -1, 0), 'q34': (.6, -.8, .2), 'below': (0, -.6, -.8)}.items():
    cam.location = c0 + Vector(dv) * 2; cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{view}.png'; bpy.ops.render.render(write_still=True)
