"""Bell-sleeve chains (m372; after banner_rig.py): the long hanging bell of each sleeve (gown vertices weighted to
one arm, lying more than DROP below that forearm's axis) gets NCOL columns x NSEG bones from the bottom of the
sleeve tube straight down to the bell's lowest point in that column, parented to B_<s>_Forearm. Rigid on the forearm
the bells stood up like horns when the corpse lay down, and never swung. Each bell vertex blends its two
neighbouring columns and two height bones linearly; between DROP and DROP + RAMP below the axis it blends from its
arm weights into the chain weights (no tear at the cuff). Simulated by robe_sim.py (CHAINS_KEY=sleeve_chains_<s>
ROOT=B_<s>_Forearm PREFIX=Sleeve_<s> TILT=B_Spine1). Writes scene['sleeve_chains_L'/'_R'].
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cfg
src, out = sys.argv[sys.argv.index('--') + 1:]
NCOL, NSEG = int(os.environ.get('NCOL', '3')), int(os.environ.get('NSEG', '3'))
DROP, RAMP = float(cfg.C.get('sleeve_drop', 0.06)), 0.03
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; scene = bpy.context.scene
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([v.co[:] for v in me.vertices]); nv = len(co)
gv = np.array([a.value for a in me.attributes['garment'].data])
names = [g.name for g in body.vertex_groups]; gid = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
J = lambda n: np.array(rig.data.bones[n].head_local)
allch = {}
for s in ('L', 'R'):
    arm = [gid[n] for n in names if n.startswith(f'B_{s}_') and any(t in n for t in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
    el, wr = J(f'B_{s}_Forearm'), J(f'B_{s}_Hand')
    ax = (wr - el) / np.linalg.norm(wr - el); L = np.linalg.norm(wr - el) + 0.10
    rel = co - el; t = np.clip(rel @ ax, 0, L); onax = el + np.outer(t, ax)
    below = onax[:, 2] - co[:, 2]
    sl = (gv == 1) & (W[:, arm].sum(1) > 0.9) & (np.sign(co[:, 0]) == (1 if s == 'L' else -1)) & (below > DROP)
    ids = np.where(sl)[0]
    tv = t[ids]; edges = np.linspace(tv.min(), tv.max(), NCOL + 1)
    cols, chains = [], []
    for k in range(NCOL):
        m = ids[(tv >= edges[k] - 1e-6) & (tv <= edges[k + 1] + 1e-6)]
        tc = (edges[k] + edges[k + 1]) / 2; base = el + ax * tc
        bot = co[m][np.argmin(co[m, 2])]
        top = np.array([base[0], base[1], base[2] - DROP])
        btm = np.array([top[0] * 0.5 + bot[0] * 0.5, top[1] * 0.5 + bot[1] * 0.5, bot[2]])
        pts = [top + (btm - top) * (j / NSEG) for j in range(NSEG + 1)]
        nm = [f'Sleeve_{s}{k}_{j}' for j in range(NSEG)]
        chains.append({'deg': 90.0 if s == 'L' else -90.0, 'group': s, 'pts': [p.tolist() for p in pts], 'bones': nm})
        cols.append((tc, top[2], btm[2], nm))
    allch[s] = (chains, cols, ids, below, t)
    print('SLEEVE', s, 'bell vertices', len(ids), 'columns', [round(c[0], 3) for c in cols], 'length',
          [round(c[1] - c[2], 3) for c in cols])
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for s, (chains, *_r) in allch.items():
    for ch in chains:
        parent = rig.data.edit_bones[f'B_{s}_Forearm']
        for k, n in enumerate(ch['bones']):
            b = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
            b.head = ch['pts'][k]; b.tail = ch['pts'][k + 1]; b.parent = parent; b.use_connect = k > 0; parent = b
bpy.ops.object.mode_set(mode='OBJECT')
for s, (chains, *_r) in allch.items():
    for ch in chains:
        for n in ch['bones']:
            if n not in gid:
                body.vertex_groups.new(name=n); names.append(n); gid[n] = len(names) - 1
W = np.hstack([W, np.zeros((nv, len(names) - W.shape[1]))])
for s, (chains, cols, ids, below, t) in allch.items():
    tcs = np.array([c[0] for c in cols])
    # the ramp band just above the bell (DROP - RAMP .. DROP) belongs to the same arm's sleeve
    arm = [gid[n] for n in names if n.startswith(f'B_{s}_') and any(x in n for x in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
    band = np.where((gv == 1) & (W[:, arm].sum(1) > 0.9) & (np.sign(co[:, 0]) == (1 if s == 'L' else -1))
                    & (below > DROP - RAMP))[0]
    for i in band:
        a = float(np.interp(t[i], tcs, np.arange(len(tcs)))); lo = int(math.floor(a)); hi = min(lo + 1, len(tcs) - 1); f = a - lo
        w = np.zeros(len(names))
        for ci, mix in ((lo, 1 - f), (hi, f)):
            _, ztop, zbot, nm = cols[ci]
            u = float(np.clip((ztop - co[i, 2]) / max(ztop - zbot, 1e-6), 0, 1)) * NSEG
            k = min(NSEG - 1, int(u)); v = u - k
            w[gid[nm[k]]] += mix * (1 - v * (k + 1 < NSEG))
            if k + 1 < NSEG:
                w[gid[nm[k + 1]]] += mix * v
        r = float(np.clip((below[i] - (DROP - RAMP)) / RAMP, 0, 1))
        W[i] = W[i] * (1 - r) + w * r
for i in range(nv):
    w = W[i]; top = np.argsort(-w)[:4]; sm = w[top].sum(); keep = np.zeros_like(w)
    keep[top] = w[top] / sm if sm > 0 else 0; W[i] = keep
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for gi in range(len(names)):
    for i in np.where(W[:, gi] > 1e-5)[0]:
        body.vertex_groups[names[gi]].add([int(i)], float(W[i, gi]), 'REPLACE')
for s, (chains, *_r) in allch.items():
    scene[f'sleeve_chains_{s}'] = json.dumps(chains)
assert len(rig.data.bones) <= 128, len(rig.data.bones)
print('SLEEVE chains', sum(len(c[0]) for c in allch.values()), 'bones', len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
