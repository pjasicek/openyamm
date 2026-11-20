import bpy, sys, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
mp = bpy.data.objects['MeshyPosed']
P = np.array([tuple(v.co) for v in mp.data.vertices])
sel_f = []
for p in mp.data.polygons:
    f = list(p.vertices)
    e = max(np.linalg.norm(P[f[i]] - P[f[(i + 1) % len(f)]]) for i in range(len(f)))
    c = P[f].mean(0)
    if e > float(argv[2]) and 0.4 < abs(c[0]) < 4.3 and -3.7 < c[1] < 1.0 and 14.3 < c[2] < 17.6:
        sel_f.append(p.index)
print('SPIKEFACES', len(sel_f), sel_f)
col = mp.data.color_attributes.new('s', 'FLOAT_COLOR', 'CORNER')
for p in mp.data.polygons:
    for li in p.loop_indices:
        col.data[li].color = (1, 0, 0, 1) if p.index in sel_f else (0.8, 0.8, 0.8, 1)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o != mp
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 10; cd.clip_end = 1000
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -1, 15.5))
for k, dv in enumerate([(0, -1, 0.15), (-1, -1.25, 0.55), (0, 0.0001, 1)]):
    dv = Vector(dv).normalized(); cam.location = c + dv * 80
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = argv[1].replace('.png', f'_{k}.png'); bpy.ops.render.render(write_still=True)
