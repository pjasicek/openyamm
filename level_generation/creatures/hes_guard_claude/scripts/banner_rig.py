"""Banner chains: each of the two back banners (garment 10, pieces 7 R / 8 L) hangs from its rod. Rigid on the chest it
stood up in the air when the corpse lay prone and never swung. NCOL columns per banner, each a chain of NSEG bones
from the banner's top edge (on the rod) straight down to its lowest point in that column, parented to B_Spine2; every
banner vertex blends its two neighbouring columns and two height bones linearly (top row 100 % on the root bone's
start, i.e. it follows the chest with the rod). Simulated by robe_sim.py (CHAINS_KEY=banner_chains ROOT=B_Spine2
PREFIX=Banner_), with neighbour spacing kept inside each banner only.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
NCOL, NSEG = int(os.environ.get('NCOL', '3')), int(os.environ.get('NSEG', '3'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; scene = bpy.context.scene
co = np.array([v.co[:] for v in me.vertices]); nv = len(co)
pv = np.array([a.value for a in me.attributes['piece'].data])
chains = []; plan = []
import cfg
for side, piece in cfg.C['banners'].items():
    ids = np.where(pv == piece)[0]; c = co[ids]
    xs = np.linspace(c[:, 0].min(), c[:, 0].max(), NCOL + 2)[1:-1]
    cols = []
    for k, x in enumerate(xs):
        band = c[np.abs(c[:, 0] - x) < 0.03]
        top = band[np.argmax(band[:, 2])]; bot = band[np.argmin(band[:, 2])]
        top = np.array([x, band[:, 1].mean(), top[2]]); bot = np.array([x, band[:, 1].mean(), bot[2]])
        pts = [top + (bot - top) * (j / NSEG) for j in range(NSEG + 1)]
        name = [f'Banner_{side}{k}_{j}' for j in range(NSEG)]
        chains.append({'deg': 0.0, 'group': side, 'pts': [p.tolist() for p in pts], 'bones': name})
        cols.append((x, top[2], bot[2], name))
    plan.append((ids, cols))
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for ch in chains:
    parent = rig.data.edit_bones['B_Spine2']
    for k, n in enumerate(ch['bones']):
        b = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
        b.head = ch['pts'][k]; b.tail = ch['pts'][k + 1]; b.parent = parent; b.use_connect = k > 0; parent = b
bpy.ops.object.mode_set(mode='OBJECT')
groups = {g.name: g for g in body.vertex_groups}
for ch in chains:
    for n in ch['bones']:
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
for ids, cols in plan:
    xs = np.array([c[0] for c in cols])
    for i in ids:
        x, y, z = co[i]
        for g in body.vertex_groups:
            g.remove([int(i)])
        a = float(np.interp(x, xs, np.arange(len(xs)))); lo = int(math.floor(a)); hi = min(lo + 1, len(xs) - 1); t = a - lo
        w = {}
        for ci, mix in ((lo, 1 - t), (hi, t)):
            _, ztop, zbot, names = cols[ci]
            u = float(np.clip((ztop - z) / max(ztop - zbot, 1e-6), 0, 1)) * NSEG
            k = min(NSEG - 1, int(u)); v = u - k
            # a bone deforms what lies along it: the first bone's top end is the rod, so the top rows stay on it
            w[names[k]] = w.get(names[k], 0) + mix * (1 - v * (k + 1 < NSEG))
            if k + 1 < NSEG:
                w[names[k + 1]] = w.get(names[k + 1], 0) + mix * v
        best = sorted(w.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in best)
        for n, v in best:
            if v > 1e-6:
                groups[n].add([int(i)], v / s, 'REPLACE')
scene['banner_chains'] = json.dumps(chains)
assert len(rig.data.bones) <= 128, len(rig.data.bones)
print('BANNERS chains', len(chains), 'bones', len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
