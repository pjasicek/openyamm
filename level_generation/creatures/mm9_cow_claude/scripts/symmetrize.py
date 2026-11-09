"""Make the weighted 'Body' mirror-symmetric like the MM9 model: keep the creature's RIGHT half (-X, the side the
three-quarter HD master shows), mirror it about the MM9 skeleton's mid plane x = C and weld on the plane. Mirrored
vertices take the weights of their source with every L/R bone swapped (rigcfg.MIRROR); separate pieces (eyes, teats)
are mirrored with the half. Attributes are copied; the 'chain' attribute swaps the left/right leg chains.

Args: <in blend> <out blend> <report json> [keep side: -X|X]
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
KEEP = argv[3] if len(argv) > 3 else '-X'
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
ob = bpy.data.objects['Body']
# mid plane: the mean x of the MM9 left/right joint pairs
xs = []
for a, b in rigcfg.MIRROR.items():
    if a in arm.data.bones and b in arm.data.bones:
        xs.append((arm.data.bones[a].head_local.x + arm.data.bones[b].head_local.x) / 2)
C = float(np.mean(xs))
me = ob.data
before = len(me.polygons)
names = [g.name for g in ob.vertex_groups]
for a in list(rigcfg.MIRROR.values()):   # make sure every mirrored bone has a group
    if a not in names and a in arm.data.bones:
        ob.vertex_groups.new(name=a)
names = [g.name for g in ob.vertex_groups]
swap = {i: names.index(rigcfg.MIRROR[n]) if n in rigcfg.MIRROR and rigcfg.MIRROR[n] in names else i
        for i, n in enumerate(names)}
chains = list(rigcfg.CHAINS)
cswap = {}
for i, c in enumerate(chains):
    o = c[:-1] + {'l': 'r', 'r': 'l'}[c[-1]] if c.startswith('leg') else c
    cswap[i] = chains.index(o) if o in chains else i
cswap[-1] = -1

bm = bmesh.new()
bm.from_mesh(me)
for v in bm.verts:
    v.co.x -= C
# a separate piece with no mirror partner (goat beard, tail tassel) moves onto the mid plane, or it would double
pl0 = bm.verts.layers.int.get('piece')
bm.verts.ensure_lookup_table()
seen, pieces = set(), []
for v in bm.verts:
    if v.index in seen or v[pl0] == 0:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    pieces.append(c)
cents = [sum((v.co for v in c), v.co.__class__()) / len(c) for c in pieces]
centred = []
for i, c in enumerate(pieces):
    m = cents[i].copy(); m.x = -m.x
    if not any((m - q).length < 0.06 for j, q in enumerate(cents) if j != i):
        for v in c:
            v.co.x -= cents[i].x
        centred.append(len(c))
print('SYMPIECES', len(pieces), 'centred', centred)
keep_sign0 = -1 if KEEP == '-X' else 1
orig_keep = [v.co.copy() for v in bm.verts if v.co.x * keep_sign0 > 1e-4]
res = bmesh.ops.symmetrize(bm, input=list(bm.verts) + list(bm.edges) + list(bm.faces),
                           direction='-X' if KEEP == '-X' else 'X', dist=1e-5)
bm.verts.ensure_lookup_table()
xs_ = np.array([v.co.x for v in bm.verts])
dl = bm.verts.layers.deform.active
pl = bm.verts.layers.int.get('piece')
cl = bm.verts.layers.int.get('chain')
# vertices on the mirrored side are the new copies: find each one's source (mirror position) and copy its data
from mathutils.kdtree import KDTree
keep_sign = -1 if KEEP == '-X' else 1
src = [v for v in bm.verts if v.co.x * keep_sign >= -1e-6]
kd = KDTree(len(src))
for i, v in enumerate(src):
    kd.insert(v.co, i)
kd.balance()
kd0 = KDTree(len(orig_keep))
for i, c_ in enumerate(orig_keep):
    kd0.insert(c_, i)
kd0.balance()
kept_dev = max(kd0.find(v.co)[2] for v in bm.verts if v.co.x * keep_sign > 1e-3)
mirrored, worst = 0, 0.0
for v in bm.verts:
    if v.co.x * keep_sign < -1e-6:
        co = v.co.copy(); co.x = -co.x
        _, j, d = kd.find(co)
        s = src[j]
        worst = max(worst, d)
        w = dict(s[dl])
        v[dl].clear()
        for g, wt in w.items():
            v[dl][swap[g]] = wt
        if pl:
            v[pl] = s[pl]
        if cl:
            v[cl] = cswap.get(s[cl], s[cl])
        mirrored += 1
for v in bm.verts:
    v.co.x += C
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
rep = {'mid_plane_x': C, 'keep': KEEP, 'faces_before': before, 'faces_after': len(me.polygons),
       'mirrored_verts': mirrored, 'kept_side_moved_max': kept_dev, 'source_match_max': worst}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('SYMMETRIZE', json.dumps(rep))
