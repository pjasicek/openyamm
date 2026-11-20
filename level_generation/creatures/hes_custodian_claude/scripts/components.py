"""List the raw return's connected components (bounds, vertex counts) and render it from 5 directions with a random
colour per component. Args: -- <out prefix>"""
import json, math, os, random, sys
import bmesh, bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
prefix = sys.argv[sys.argv.index('--') + 1]
obj = cc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = cc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
print('BOUNDS', co.min(0).round(3), co.max(0).round(3), 'verts', len(co), 'faces', len(bm.faces))
rows = []
for c in range(labels.max() + 1):
    p = co[labels == c]
    rows.append({'c': c, 'n': int(len(p)), 'lo': p.min(0).round(3).tolist(), 'hi': p.max(0).round(3).tolist(),
                 'mid': p.mean(0).round(3).tolist()})
rows.sort(key=lambda r: -r['n'])
for r in rows[:40]:
    print('COMP', r['c'], r['n'], 'lo', r['lo'], 'hi', r['hi'], 'mid', r['mid'])
print('NCOMP', len(rows))
json.dump(rows, open(cc.path(prefix + '_components.json'), 'w'), indent=0)
random.seed(3)
cols = [(random.random(), random.random(), random.random(), 1) for _ in range(labels.max() + 1)]
layer = bm.loops.layers.color.new('c')
for f in bm.faces:
    for l in f.loops:
        l[layer] = cols[labels[l.vert.index]]
bm.to_mesh(obj.data); bm.free()
obj.data.color_attributes.active_color_name = 'c'
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 700
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = max(hi - lo)
cam.data.ortho_scale = size * 1.15
for view, (az, el) in {'front': (0, 0), 'left': (-90, 0), 'right': (90, 0), 'back': (180, 0), 'top': (0, 89)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = cc.path(f'{prefix}_{view}.png')
    bpy.ops.render.render(write_still=True)
