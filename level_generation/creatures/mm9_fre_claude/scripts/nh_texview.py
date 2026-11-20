"""Pass 7: unlit/flat textured views of a head npz (co, tri, uv) with one base-colour image (workbench, texture colour, flat lighting),
for checking a paint on our UVs. Args: <head_uv npz> <image> <out prefix> [views]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri, uv = D['co'], D['tri'], D['uv']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('h'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
L = me.uv_layers.new(name='UVMap').data
for p in me.polygons:
    for li, vi in zip(p.loop_indices, p.vertices): L[li].uv = uv[vi]
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('h', me); bpy.context.scene.collection.objects.link(o)
m = bpy.data.materials.new('m'); m.use_nodes = True; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(a[1])
nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color']); me.materials.append(m)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = a[4] if len(a) > 4 else 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 700; sc.world = bpy.data.worlds.new('W'); sc.world.color = (.3, .3, .33)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(__import__('os').environ.get('ORTHO', '0.32')); cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in __import__('os').environ.get('CENTRE', '0,0,0.68').split(',')])
for nm, d in {'front': (0, -1, 0.05), 'q34': (-1, -1.2, 0.2), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05), 'back': (0, 1, 0.1), 'low': (-0.5, -1, -0.8)}.items():
    d = Vector(d).normalized(); cam.location = ce + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{nm}.png'; bpy.ops.render.render(write_still=True)
