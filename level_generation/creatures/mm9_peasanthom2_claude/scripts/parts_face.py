"""Face close-up with chosen loose parts coloured (head_split.py part order). Args: <blend> <out prefix> <k=r,g,b ...>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
for pb in body.parent.pose.bones:
    pb.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(me.vertices), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
want = {}
for s in a[2:]:
    k, c = s.split('='); want[int(k)] = tuple(float(x) for x in c.split(',')) + (1,)
me.materials.clear()
m0 = bpy.data.materials.new('b'); m0.diffuse_color = (0.75, 0.75, 0.75, 1); me.materials.append(m0)
idx = {}
for k, c in want.items():
    m = bpy.data.materials.new(str(k)); m.diffuse_color = c; me.materials.append(m); idx[k] = len(me.materials) - 1
for p in me.polygons:
    p.material_index = idx.get(int(comp[p.vertices[0]]), 0)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.3
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -0.05, 0.80))
for v, d in {'front': Vector((0, -1, 0.0)), 'q34': Vector((0.7, -1, 0.0)), 'below': Vector((0, -1, -0.6))}.items():
    cam.location = c + d.normalized() * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'
    bpy.ops.render.render(write_still=True)
