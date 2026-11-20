"""Texel mask (head set, HeadUV) of the mouth-slit plate: the small head loose part inside the lips (Meshy's mouth
interior, 24 vertices, the part nearest MOUTH). Writes work/mouth_uv.json (the part's HeadUV triangles)
for mouth_paint.py. Args (Blender): <blend> [x,y,z of the mouth, Blender rest; default 0,-0.06,0.695]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
M = Vector([float(x) for x in a[1].split(',')]) if len(a) > 1 else Vector((0, -0.06, 0.695))
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int['head']
comp = [-1] * len(bm.verts); n = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = n
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = n; st.append(y)
    n += 1
import collections
size = collections.Counter(comp)
cand = [k for k, s in size.items() if s <= 40]
best = min(cand, key=lambda k: min((v.co - M).length for v in bm.verts if comp[v.index] == k))
uvl = bm.loops.layers.uv['HeadUV']
tris = []
for f in bm.faces:
    if comp[f.verts[0].index] == best and f[hl]:
        tris.append([[l[uvl].uv.x, l[uvl].uv.y] for l in f.loops])
import json
json.dump(tris, open(a[0].rsplit('/work/', 1)[0] + '/work/mouth_uv.json', 'w'))
print('MOUTHMASK part', best, 'verts', size[best], 'faces', len(tris))
