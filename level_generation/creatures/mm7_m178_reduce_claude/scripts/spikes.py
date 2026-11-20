"""Spike faces of the rest source (skull/shoulder/back/forearm spikes, horns, ear tips, toe claws, heel spurs): the
source project's own spike rule (mm7_m178_claude/scripts/weights_fix.py): inward thickness of the closed skin by ray
casts along -normal and three tilted directions, seeds thinner than SEED (3.5 cm), grown through edges while thinner
than GROW (6 cm); hands and tail excluded (the claws and the tail have their own groups). A face is a spike face when
all three vertices are flagged; TIP_* marks the outer part of each spike (vertices thinner than TIP, 2 cm) for an
exact keep. Writes work/spike_faces.npy, work/spike_tips.npy (bool per face, dump_mesh.py order).
Usage: blender -b -P spikes.py"""
import os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED, GROW, TIP = (float(os.environ.get(k, d)) for k, d in (('SEED', '0.035'), ('GROW', '0.06'), ('TIP', '0.02')))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); f = d['faces']; co = d['verts']; nv = len(co)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])


def components(edges, n):
    par = np.arange(n)

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    return np.array([find(i) for i in range(n)])


lab = components(e, nv)
skin_piece = np.bincount(lab).argmax(); skin = lab == skin_piece
tree = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(t) for t in f if skin[t[0]]])
names = [g.name for g in o.vertex_groups]
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
excl = W[:, [i for i, n in enumerate(names) if 'Hand' in n or 'Finger' in n or n.startswith('B_Tail')]].sum(1) > 0.5
th = np.ones(nv)
for v in me.vertices:
    if not skin[v.index]:
        continue
    n = v.normal; p = v.co - n * 0.002
    for dv in (-n, (-n + Vector((0.3, 0, 0))).normalized(), (-n + Vector((0, 0.3, 0))).normalized(),
               (-n + Vector((0, 0, 0.3))).normalized()):
        loc, nrm, idx, dist = tree.ray_cast(p, dv, 1.0)
        if loc is not None:
            th[v.index] = min(th[v.index], dist)
flag = skin & ~excl & (th < SEED)
E = np.unique(np.sort(e, 1), axis=0)
for _ in range(30):
    grow = flag.copy()
    for a, b in ((0, 1), (1, 0)):
        m = flag[E[:, a]] & ~flag[E[:, b]] & (th[E[:, b]] < GROW) & ~excl[E[:, b]]
        grow[E[m, b]] = True
    if (grow == flag).all():
        break
    flag = grow
fl = flag[f].all(1); tip = (flag & (th < TIP))[f].any(1) & fl
EF = E[flag[E[:, 0]] & flag[E[:, 1]]]
sl = components(EF, nv)
nspk = len(np.unique(sl[flag]))
np.save(os.path.join(HERE, 'work', 'spike_faces.npy'), fl); np.save(os.path.join(HERE, 'work', 'spike_tips.npy'), tip)
print('SPIKES', nspk, 'spikes', int(flag.sum()), 'vertices', int(fl.sum()), 'faces', int(tip.sum()), 'tip faces')
