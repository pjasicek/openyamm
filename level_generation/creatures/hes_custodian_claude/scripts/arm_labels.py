"""Render the +x arm (creature's left) from the side (+x) and the front (-y) with each component's index at its mean
point, to map the arm's joints. Args: -- <out prefix>"""
import json, math, os, random, sys
import bmesh, bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
prefix = sys.argv[sys.argv.index('--') + 1]
obj = cc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = cc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
keep = [c for c in range(labels.max() + 1) if co[labels == c][:, 0].mean() > 0.3]
random.seed(5)
cols = {c: (random.random(), random.random(), random.random(), 1) for c in range(labels.max() + 1)}
layer = bm.loops.layers.color.new('c')
for f in bm.faces:
    c = labels[f.verts[0].index]
    for l in f.loops:
        l[layer] = cols[c] if c in keep else (0.15, 0.15, 0.15, 1)
bm.to_mesh(obj.data); bm.free()
obj.data.color_attributes.active_color_name = 'c'
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 1000
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.75
marks = {}
for view, d, centre in (('side', Vector((1, 0, 0)), Vector((0.43, -0.1, -0.15))), ('front', Vector((0, -1, 0)), Vector((0.42, 0, -0.15))),
                        ('top', Vector((0, 0, 1)), Vector((0.42, -0.1, 0)))):
    cam.location = centre + d * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = cc.path(f'{prefix}_{view}.png')
    bpy.ops.render.render(write_still=True)
    marks[view] = []
    for c in keep:
        p = co[labels == c]
        q = world_to_camera_view(sc, cam, Vector(p.mean(0)))
        marks[view].append((c, q.x, 1 - q.y, int(len(p))))
json.dump(marks, open(cc.path(prefix + '_marks.json'), 'w'))
