"""List the open boundary loops of body faces (no head/hand attribute) of a master blend: edges, centre, dominant bone.
Args (Blender): <blend>"""
import bpy, bmesh, sys, collections
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]
bm = bmesh.new(); bm.from_mesh(me)
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
dl = bm.verts.layers.deform.active
def plain(f): return f[lh] == 0 and f[lk] == 0
edges = [e for e in bm.edges if sum(1 for f in e.link_faces if plain(f)) == 1]
es = set(edges); seen = set(); loops = []
for e in edges:
    if e in seen: continue
    st = [e]; lp = []
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); lp.append(x)
        for v in x.verts:
            st += [y for y in v.link_edges if y in es and y not in seen]
    loops.append(lp)
for lp in sorted(loops, key=lambda l: -len(l)):
    vs = {v for e in lp for v in e.verts}
    c = np.mean([tuple(body.matrix_world @ v.co) for v in vs], 0)
    cnt = collections.Counter(names[max(v[dl].items(), key=lambda kv: kv[1])[0]] for v in vs if v[dl])
    if len(lp) >= 4: print('RIM', len(lp), np.round(c, 3), cnt.most_common(2))
