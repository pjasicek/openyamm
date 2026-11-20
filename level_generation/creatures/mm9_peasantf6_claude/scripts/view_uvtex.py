"""Textured views of the uv npz mesh (rest pose): material 0 with <body png>, material 1 with <head png> (or grey). Workbench, flat light.
Args: <uv npz> <body png> <head png|-> <out prefix> <centre x,y,z> <ortho> <size> <views name=dx,dy,dz:...>"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('m'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
ul = me.uv_layers.new(name='UVMap'); li = np.array([l.vertex_index for l in me.loops]); ul.data.foreach_set('uv', uv[li].ravel())
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(o)
for k, img in enumerate(a[1:3]):
    m = bpy.data.materials.new(f'm{k}'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    if img != '-':
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(img); nt.links.new(tx.outputs['Color'], bs.inputs['Base Color'])
    o.data.materials.append(m)
me.polygons.foreach_set('material_index', mat.tolist()); me.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
import os
if os.environ.get('NEAREST'):
    [setattr(n, 'interpolation', 'Closest') for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type == 'TEX_IMAGE']
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = int(a[6]); sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.4, 0.4, 0.4); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[5]); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in a[4].split(',')])
V = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05), 'q34': (-0.7, -1, 0.3), 'below': (0.3, -1, -0.6)}
for v in a[7].split(':'):
    if '=' in v: nm, d = v.split('='); d = tuple(float(x) for x in d.split(','))
    else: nm, d = v, V[v]
    cam.location = ce + Vector(d).normalized() * 8; cam.rotation_euler = (ce - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[3]}_{nm}.png'; bpy.ops.render.render(write_still=True)
