"""Symmetric rig for the v2 MM7 Dragon (Blender): body chain and legs as in scripts/rig_dragon.py (v1), procedural
wings with six bones per side.

- Bones: body bones on x = 0; leg joints are the v1 left-leg joints moved by the straightening field
  (work/v2/midline_field.npz) and mirrored for the right side; wing bones come from scripts/build_wing.py.
- Body weights: the v1 rules (head/jaw/cheek ownership, leg domains by nearest chain, soft leg roots, crest shells
  bound rigidly to their anchor), evaluated on the +X half only and mirrored onto the -X partner of every vertex
  (L/R bone names swapped); midline vertices take the mean of a weight and its mirror. So the weights are exactly
  symmetric.
- Wing weights: analytic, from the wing build (scripts/assemble_wing.py writes them next to the blend).
Writes work/v2/rig_v2.blend, work/v2/rig_report.json. Usage: rig_v2.py -- <static_v5.blend> <out.blend>"""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']; me = o.data
co = np.array([v.co[:] for v in me.vertices]); pa = np.array([v.value for v in me.attributes['part'].data])
wk = np.array([v.value for v in me.attributes['wing_kind'].data])
WW = np.load(P / 'work/v2/static_v5_wing_weights.npz')
x, y, z = co.T; ax = np.abs(x)
body_v = wk < 0

# ---------------------------------------------------------------- straightening field for the v1 leg joints
F = np.load(P / 'work/v2/midline_field.npz'); fys, fzs, fc = F['ys'], F['zs'], F['c']
def field(yy, zz):
    fy = (yy - fys[0]) / (fys[1] - fys[0]); fz = (zz - fzs[0]) / (fzs[1] - fzs[0])
    i = int(np.clip(np.floor(fy), 0, len(fys) - 2)); j = int(np.clip(np.floor(fz), 0, len(fzs) - 2)); u = np.clip(fy - i, 0, 1); v = np.clip(fz - j, 0, 1)
    return float((1 - u) * (1 - v) * fc[i, j] + u * (1 - v) * fc[i + 1, j] + (1 - u) * v * fc[i, j + 1] + u * v * fc[i + 1, j + 1])
def moved(p): return (p[0] - field(p[1], p[2]), p[1], p[2])

# ---------------------------------------------------------------- domains (body vertices only)
head = body_v & (y < -.300) & (z > .383) & (ax < .09)
head |= body_v & (pa > 0) & (y < -.29) & (z > .37)
jaw = head & (y < -.345) & (z < .4015) & (pa == 0)
fore_box = body_v & (y < -.25) & (z < .236) & ~head
hind_box = body_v & (y > -.20) & (y < .03) & (z < .175)

bones = {}
def chain(names, points, parent):
    for i, n in enumerate(names):
        bones[n] = (np.array(points[i], float), np.array(points[i + 1], float), parent if i == 0 else names[i - 1])
chain(['Root'], [(0, -.10, .19), (0, -.10, .23)], None)
chain(['Spine1', 'Spine2'], [(0, -.10, .19), (0, -.185, .212), (0, -.268, .236)], 'Root')
chain(['Neck1', 'Neck2', 'Neck3'], [(0, -.268, .236), (0, -.296, .29), (0, -.304, .34), (0, -.306, .392)], 'Spine2')
chain(['Head'], [(0, -.306, .392), (0, -.402, .424)], 'Neck3')
chain(['Jaw'], [(0, -.345, .399), (0, -.393, .394)], 'Head')
chain(['Socket_Mouth'], [(0, -.385, .405), (0, -.405, .403)], 'Head')
tail_y = np.linspace(-.02, .47, 11); tailpts = [(0, -.10, .19)]
for yy in tail_y[1:]:
    q = co[body_v & (np.abs(y - yy) < .015) & (ax < .05) & (z > .05) & (z < .2)]
    tailpts.append((0., float(yy), float(np.quantile(q[:, 2], .45)) if len(q) > 5 else tailpts[-1][2]))
tailpts[1] = (0., .0, .165)
chain([f'Tail{i}' for i in range(1, 11)], tailpts, 'Root')
FORE = [moved(p) for p in [(.062, -.255, .214), (.057, -.330, .200), (.072, -.380, .174), (.056, -.425, .150)]]
HIND = [moved(p) for p in [(.060, -.115, .175), (.066, -.143, .115), (.064, -.060, .085), (.076, -.033, .006)]]
mir = lambda pts: [(-p[0], p[1], p[2]) for p in pts]
bp = json.loads(str(WW['bone_pts']))
WING = {'Wing0': 'Spine2', 'Wing1': 'Wing0', 'Wing2': 'Wing1', 'Wing3': 'Wing2', 'WingF2': 'Wing1', 'WingF3': 'Wing1'}
for s, sg in (('L', 1), ('R', -1)):
    chain([s + 'ForeUpper', s + 'ForeLower', s + 'ForeFoot'], FORE if sg > 0 else mir(FORE), 'Spine2')
    chain([s + 'HindUpper', s + 'HindLower', s + 'HindFoot'], HIND if sg > 0 else mir(HIND), 'Root')
    for n, parent in WING.items():
        h, t = np.array(bp[n][0]), np.array(bp[n][1]); h[0] *= sg; t[0] *= sg
        bones[s + n] = (h, t, parent if parent.startswith('Spine') else s + parent)

def distance(p, h, t):
    d = t - h; u = np.clip(np.dot(p - h, d) / np.dot(d, d), 0, 1); return np.linalg.norm(p - h - u * d)
def chain_distance(p, names): return min(distance(p, *bones[n][:2]) for n in names)
body_chain = ['Spine1', 'Spine2', 'Neck1', 'Neck2'] + [f'Tail{i}' for i in range(1, 6)]
fore = np.zeros(len(co), bool); hind = np.zeros(len(co), bool)
for i in np.where(fore_box | hind_box)[0]:
    s_ = 'L' if x[i] > 0 else 'R'; other = 'R' if s_ == 'L' else 'L'; body_d = chain_distance(co[i], body_chain)
    if fore_box[i]:
        d = min(chain_distance(co[i], [s_ + n for n in ('ForeUpper', 'ForeLower', 'ForeFoot')]), chain_distance(co[i], [other + n for n in ('ForeUpper', 'ForeLower', 'ForeFoot')]))
        fore[i] = d < .9 * body_d and (abs(x[i]) > .012 or y[i] < -.33)
    if hind_box[i]:
        d = min(chain_distance(co[i], [s_ + n for n in ('HindUpper', 'HindLower', 'HindFoot')]), chain_distance(co[i], [other + n for n in ('HindUpper', 'HindLower', 'HindFoot')]))
        hind[i] = d < .9 * body_d

arm = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', arm); bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, (h, t, parent) in bones.items():
    b = arm.edit_bones.new(n); b.head = h; b.tail = t; b.align_roll(Vector((0, 0, 1)))
    b.parent = arm.edit_bones.get(parent) if parent else None; b.use_deform = n != 'Socket_Mouth'
# mirror-consistent rolls: R bones take the mirrored roll of their L partner
for b in arm.edit_bones:
    if b.name.startswith('R') and 'L' + b.name[1:] in arm.edit_bones:
        b.roll = -arm.edit_bones['L' + b.name[1:]].roll
bpy.ops.object.mode_set(mode='OBJECT')
names = [n for n in bones if n != 'Socket_Mouth']
groups = {n: o.vertex_groups.new(name=n) for n in names}

def blend(p, names_, width=.012):
    ds = np.array([distance(p, *bones[n][:2]) for n in names_]); ix = np.argsort(ds)[:4]
    w = np.exp(-((ds[ix] - ds.min()) / width) ** 2); w[w < .025] = 0; w /= w.sum()
    return {names_[j]: float(v) for j, v in zip(ix, w) if v > 0}
def leg_side(p, kind):
    dl = chain_distance(p, ['L' + kind + n for n in ('Upper', 'Lower', 'Foot')]); dr = chain_distance(p, ['R' + kind + n for n in ('Upper', 'Lower', 'Foot')])
    return 'L' if dl < dr else 'R'
body = ['Spine1', 'Spine2', 'Neck1', 'Neck2', 'Neck3', 'Head'] + [f'Tail{i}' for i in range(1, 11)]
weights = [None] * len(co)
half = np.where(body_v & (x >= 0))[0]
for i in half:
    p = co[i]; s = 'L'
    if fore[i]: s = leg_side(p, 'Fore')
    if hind[i]: s = leg_side(p, 'Hind')
    if head[i]:
        cheek = -.38 < p[1] < -.335 and .392 < p[2] < .412 and pa[i] == 0
        if cheek:
            jz = float(np.clip((.408 - p[2]) / .014, 0, 1)); jy = float(np.clip((-.338 - p[1]) / .02, 0, 1))
            j = jz * jz * (3 - 2 * jz) * jy * jy * (3 - 2 * jy); w = {'Jaw': j, 'Head': 1 - j}
        elif jaw[i]:
            j = float(np.clip((-.343 - p[1]) / .012, 0, 1)); j = j * j * (3 - 2 * j); w = {'Jaw': j, 'Head': 1 - j}
        elif pa[i] == 0 and p[1] > -.322 and p[2] < .41:
            w = blend(p, ['Neck2', 'Neck3', 'Head'], .012)
        else:
            w = {'Head': 1.}
    elif fore[i]:
        nm_ = [s + 'ForeUpper', s + 'ForeLower', s + 'ForeFoot']
        if np.linalg.norm(p - np.array(bones[s + 'ForeFoot'][0])) < .012 or p[1] < bones[s + 'ForeFoot'][0][1] - .004: w = {s + 'ForeFoot': 1.}
        else: w = blend(p, nm_ + ['Spine2', 'Neck1'], .016)
    elif hind[i]:
        nm_ = [s + 'HindUpper', s + 'HindLower', s + 'HindFoot']
        w = {s + 'HindFoot': 1.} if p[2] < .045 else blend(p, nm_ + ['Spine1', 'Tail1', 'Tail2'], .016)
    else:
        w = blend(p, body, .012)
    weights[i] = {n: v for n, v in w.items() if v > .001}

adj = [[] for _ in co]
for e in me.edges:
    i, j = e.vertices; adj[i].append(j); adj[j].append(i)
soft = body_v & (x >= 0) & (pa == 0) & ~head & (((fore) & (y > -.345)) | ((hind) & (z > .10)) | ((~fore) & (~hind) & (z < .26) & (y < .04) & (y > -.30)))
shoulder = body_v & (x >= 0) & ~head & (np.linalg.norm(co - np.array(bones['LWing0'][0]), axis=1) < .07)
soft |= shoulder & (pa == 0)
for _ in range(10):
    old = list(weights)
    for i in np.where(soft)[0]:
        nbs = [j for j in adj[i] if old[j] is not None]
        if not nbs: continue
        w = {n: v * .5 for n, v in old[i].items()}
        for j in nbs:
            for n, v in old[j].items(): w[n] = w.get(n, 0) + v * .5 / len(nbs)
        w = dict(sorted(w.items(), key=lambda q: q[1], reverse=True)[:4]); t = sum(w.values()); weights[i] = {n: v / t for n, v in w.items()}

main = np.where(body_v & (pa == 0) & (x >= 0))[0]; tree = kdtree.KDTree(len(main))
for i in main: tree.insert(Vector(co[i]), int(i))
tree.balance()
for part in sorted(set(pa[body_v]) - {0}):
    ids = np.where(body_v & (pa == part) & (x >= 0))[0]
    if not len(ids): continue
    anchor = min((tree.find(Vector(co[i])) for i in ids), key=lambda q: q[2])[1]
    w = weights[anchor] if not head[ids].all() else {'Head': 1.}
    for i in ids: weights[i] = dict(w)

def swap(w): return {(('R' + n[1:]) if n[0] == 'L' and n[1:] in ('ForeUpper', 'ForeLower', 'ForeFoot', 'HindUpper', 'HindLower', 'HindFoot') or n[1:].startswith('Wing') and n[0] == 'L'
                     else ('L' + n[1:]) if n[0] == 'R' and (n[1:] in ('ForeUpper', 'ForeLower', 'ForeFoot', 'HindUpper', 'HindLower', 'HindFoot') or n[1:].startswith('Wing')) else n): v for n, v in w.items()}
kd = kdtree.KDTree(len(co))
for i, p in enumerate(co): kd.insert(Vector(p), i)
kd.balance()
worst = 0.
for i in np.where(body_v & (x < 0))[0]:
    _, j, d = kd.find(Vector((-co[i, 0], co[i, 1], co[i, 2]))); worst = max(worst, d)
    weights[i] = swap(weights[j])
for i in np.where(body_v & (x == 0))[0]:
    w = weights[i]; m = swap(w); avg = {n: .5 * (w.get(n, 0) + m.get(n, 0)) for n in set(w) | set(m)}
    # keep L/R partners together: drop the weakest pair (or centre bone) until at most four influences remain
    while len(avg) > 4:
        n = min(avg, key=avg.get); avg.pop(n)
        if n[:1] in 'LR' and n[1:] and (('R' if n[0] == 'L' else 'L') + n[1:]) in avg: avg.pop(('R' if n[0] == 'L' else 'L') + n[1:])
    t = sum(avg.values()); weights[i] = {n: v / t for n, v in avg.items()}

# wings: analytic weights carried as 'wing:<bone>' groups (left names everywhere after a symmetrize)
temp = {g.index: g.name[5:] for g in o.vertex_groups if g.name.startswith('wing:')}
for v in me.vertices:
    if wk[v.index] < 0: continue
    w = {temp[g.group]: g.weight for g in v.groups if g.group in temp and g.weight > 1e-4}
    if co[v.index, 0] < 0: w = {('R' + n[1:]) if n.startswith('LWing') else n: q for n, q in w.items()}
    weights[v.index] = w

for i, w in enumerate(weights):
    assert w, i
    t = sum(w.values())
    for n, v in w.items(): groups[n].add([i], v / t, 'REPLACE')
for g in [g for g in o.vertex_groups if g.name.startswith('wing:')]: o.vertex_groups.remove(g)
o.parent = rig; mod = o.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
wingmask = wk >= 0
for label, mask in [('wing', wingmask), ('head', head), ('jaw', jaw), ('fore', fore), ('hind', hind)]:
    if label in me.attributes: me.attributes.remove(me.attributes[label])
    me.attributes.new(label, 'BOOLEAN', 'POINT').data.foreach_set('value', mask)
for f in me.polygons:
    ids = list(f.vertices)
    if f.material_index != 2: f.material_index = 1 if head[ids].mean() > .5 else 0
report = {'bones': {n: {'head': h.tolist(), 'tail': t.tolist(), 'parent': p} for n, (h, t, p) in bones.items()},
          'unweighted': sum(not v.groups for v in me.vertices), 'max_influences': max(len(v.groups) for v in me.vertices),
          'triangles': sum(len(f.vertices) - 2 for f in me.polygons), 'vertices': len(co), 'mirror_partner_max_distance_m': worst,
          'domains': {n: int(m.sum()) for n, m in [('wing', wingmask), ('head', head), ('jaw', jaw), ('fore', fore), ('hind', hind)]}}
assert report['unweighted'] == 0 and report['max_influences'] <= 4, report
(P / 'work/v2/rig_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=a[1]); print('RIG', report['triangles'], report['domains'], 'mirror', worst)
