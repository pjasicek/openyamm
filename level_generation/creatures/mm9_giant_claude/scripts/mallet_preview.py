"""Textured preview of work/mallet.npz with given base colour (third pass). Args: <npz> <base png> <out prefix>"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z = np.load(a[0]); V, F, UVc = Z['V'], Z['F'], Z['UVc']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('M'); me.from_pydata([(p[0], p[2], -p[1]) for p in V], [], F.tolist()); me.update()
uv = me.uv_layers.new(name='UVMap')
for p, c in zip(me.polygons, UVc):
    for l, k in zip(p.loop_indices, range(3)): uv.data[l].uv = tuple(c[k])
ob = bpy.data.objects.new('M', me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('m'); mat.use_nodes = True; nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(a[1]); nt.links.new(tx.outputs[0], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.8
me.materials.append(mat)
for p in me.polygons: p.use_smooth = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x, sc.render.resolution_y = 700, 900
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
for n, d, cen, s in (('q', (0.8, -0.8, 0.4), (0, 0, -0.45), 1.9), ('front', (0, -1, 0), (0, 0, -0.45), 1.9), ('end', (-1, 0, 0.1), (0, 0, 0.19), 0.6), ('head', (0.7, -0.7, 0.5), (0, 0, 0.19), 0.75), ('grip', (0.3, -1, 0.1), (0, 0, -0.85), 0.6)):
    d = Vector(d).normalized(); cam.location = Vector(cen) + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = s
    sc.render.filepath = f'{a[2]}_{n}.png'; bpy.ops.render.render(write_still=True)
