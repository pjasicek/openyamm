"""Face close-ups of a raw head GLB (smooth shading + wire): the nose = the most -Y vertex; views front, q34, profile,
below. Args: -- <glb> <out dir> <prefix> [ortho]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
obs = [o for o in sc.objects if o.type == 'MESH']
P = np.array([tuple(o.matrix_world @ v.co) for o in obs for v in o.data.vertices])
H = float(np.ptp(P[:, 2]))
nose = P[np.argmin(P[:, 1])]
c = Vector(nose) + Vector((0, 0.15 * H, -0.02 * H))
import os as _os
TEX = _os.environ.get('TEX') == '1'
for o in obs:
    for p in o.data.polygons:
        p.use_smooth = True
    if TEX:
        continue
    me2 = o.data.copy(); w = bpy.data.objects.new('w', me2); sc.collection.objects.link(w); w.matrix_world = o.matrix_world
    m = w.modifiers.new('wf', 'WIREFRAME'); m.thickness = H * 0.0012; m.use_replace = True
    w.color = (0.05, 0.05, 0.08, 1); o.color = (0.75, 0.75, 0.77, 1)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE' if TEX else 'OBJECT'
sc.render.resolution_x = sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.32, 0.33, 0.36)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = H * float(a[3] if len(a) > 3 else 0.45)
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in (('front', (0, -1, 0)), ('q34', (-0.8, -1, 0.1)), ('profile', (-1, 0, 0)), ('below', (0, -0.7, -0.7))):
    dv = Vector(d).normalized(); cam.location = c + dv * 10 * H
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(a[1], f'{a[2]}_{nm}.png'); bpy.ops.render.render(write_still=True)
print('NOSE', nose, 'H', H, 'verts', len(P))
