"""Colour Body by the dominant bone of each face and render close-ups; prints each finger chain's joints.
Args: blend outdir prefix substring(bones) spec..."""
import bpy, sys, os, colorsys
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
BL, outdir, prefix, sub = argv[:4]
bpy.ops.wm.open_mainfile(filepath=BL)
sc = bpy.context.scene
b = bpy.data.objects['Body']; me = b.data; rig = b.parent
names = [g.name for g in b.vertex_groups]
vb = np.zeros(len(me.vertices), np.int32)
for v in me.vertices:
    vb[v.index] = max(v.groups, key=lambda g: g.weight).group if v.groups else -1
for i, n in enumerate(names):
    m = bpy.data.materials.new(n); m.diffuse_color = (*colorsys.hsv_to_rgb((i * 0.381966) % 1, 0.8, 0.95), 1)
    me.materials.append(m)
for p in me.polygons:
    p.material_index = int(vb[p.vertices[0]])
for bn in rig.data.bones:
    if sub in bn.name:
        print('BONE', bn.name, np.round(rig.matrix_world @ bn.head_local, 3).tolist(), bn.parent.name if bn.parent else None)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True; sh.show_cavity = True
sc.render.resolution_x = 800; sc.render.resolution_y = 800
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in argv[4:]:
    n, c, o, d = s.split(':')
    c = Vector([float(x) for x in c.split(',')]); d = Vector([float(x) for x in d.split(',')]).normalized()
    cd.ortho_scale = float(o); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{n}.png'); bpy.ops.render.render(write_still=True)
