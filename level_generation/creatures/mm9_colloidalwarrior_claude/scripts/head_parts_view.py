"""Head-only Meshy: render the shell alone and the shell with its small parts coloured (diagnosis). Args: <glb> <out prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.mesh.separate(type='LOOSE')
obs = sorted([x for x in bpy.data.objects if x.type == 'MESH'], key=lambda x: -len(x.data.vertices))
shell = obs[0]
bm = bmesh.new(); bm.from_mesh(shell.data)
print('SHELL', len(bm.verts), 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold)); bm.free()
cols = [(1, .2, .2, 1), (.2, 1, .2, 1), (.2, .4, 1, 1), (1, 1, .2, 1), (1, .2, 1, 1)]
for i, x in enumerate(obs):
    x.color = (.75, .75, .75, 1) if i == 0 else cols[min(i - 1, 4)] if i < 5 else (1, .6, 0, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.6
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector((0, -0.3, 0.07))
for tag, hide in (('all', False), ('shell', True)):
    for x in obs[1:]: x.hide_render = hide
    for v, d in {'front': (0, -1, 0), 'q': (-1, -1.3, 0.1), 'side': (-1, 0, 0)}.items():
        d = Vector(d).normalized(); cam.location = C + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[1]}_{tag}_{v}.png'; bpy.ops.render.render(write_still=True)
