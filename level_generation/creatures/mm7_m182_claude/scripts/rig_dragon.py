"""Measured six-limb rig for the MM7 Dragon (adapted from mm8_m492_claude/scripts/rig_dragon.py).

Joints come from slices of the symmetric rest mesh (work/static_v4.blend: symmetric, cleaned; see README "Rig"). Weights are explicit:
spanwise stations on the wings with a soft root band, rigid head/jaw ownership, distance blends inside each limb
domain, soft leg roots averaged over neighbours, separate crest/tooth shells bound to their attachment vertex.
Writes work/rig_v1.blend, work/rig_report.json, work/rig_domains.npz."""
import bpy, json
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/static_v4.blend'))
o = bpy.data.objects['Body']; me = o.data
co = np.array([v.co[:] for v in me.vertices]); pa = np.array([v.value for v in me.attributes['part'].data])
x, y, z = co.T
ax = np.abs(x)

# ---------------------------------------------------------------- domains
wing = (ax > .085) & (z > .255) & (y > -.33) & (y < -.08)
head = (y < -.300) & (z > .383) & (ax < .09)
head |= (pa > 0) & (y < -.29) & (z > .37)            # crest spikes and loose head shells
jaw = head & (y < -.345) & (z < .4015) & (pa == 0)
# legs: inside the leg boxes, a vertex belongs to a leg when that leg's chain is nearer than the body chain
# (an |x| threshold put the right hind foot's inner toes, at x = -0.03, on the tail)
fore_box = (y < -.25) & (z < .236) & ~head & ~wing
hind_box = (y > -.20) & (y < .03) & (z < .175) & ~wing

# ---------------------------------------------------------------- bones
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
# tail centreline from the unbent mesh: median x, lower-third z per slice
tail_y = np.linspace(-.02, .47, 11); tailpts = [(0, -.10, .19)]
for yy in tail_y[1:]:
    a = co[(np.abs(y - yy) < .015) & (ax < .05) & (z > .05) & (z < .2)]
    tailpts.append((0., float(yy), float(np.quantile(a[:, 2], .45)) if len(a) > 5 else tailpts[-1][2]))
tailpts[1] = (0., .0, .165)
chain([f'Tail{i}' for i in range(1, 11)], tailpts, 'Root')
W = {'L': [(.075, -.262, .300), (.130, -.262, .382), (.185, -.295, .505), (.355, -.282, .590), (.522, -.298, .627)],
     'R': [(-.075, -.262, .300), (-.130, -.272, .405), (-.190, -.300, .525), (-.400, -.280, .600), (-.602, -.284, .648)]}
FORE = {'L': [(.062, -.255, .214), (.057, -.330, .200), (.072, -.380, .174), (.056, -.425, .150)],
        'R': [(-.048, -.255, .214), (-.045, -.310, .195), (-.052, -.342, .158), (-.046, -.372, .132)]}
HIND = {'L': [(.060, -.115, .175), (.066, -.143, .115), (.064, -.060, .085), (.076, -.033, .006)],
        'R': [(-.046, -.110, .172), (-.050, -.145, .118), (-.063, -.050, .080), (-.067, -.020, .006)]}
for s in 'LR':
    chain([s + 'Wing0', s + 'Wing1', s + 'Wing2', s + 'Wing3'], W[s], 'Spine2')
    chain([s + 'ForeUpper', s + 'ForeLower', s + 'ForeFoot'], FORE[s], 'Spine2')
    chain([s + 'HindUpper', s + 'HindLower', s + 'HindFoot'], HIND[s], 'Root')

def distance(p, h, t):
    d = t - h; u = np.clip(np.dot(p - h, d) / np.dot(d, d), 0, 1); return np.linalg.norm(p - h - u * d)

def chain_distance(p, names):
    return min(distance(p, *bones[n][:2]) for n in names)

body_chain = ['Spine1', 'Spine2', 'Neck1', 'Neck2'] + [f'Tail{i}' for i in range(1, 6)]
fore = np.zeros(len(co), bool); hind = np.zeros(len(co), bool)
for i in np.where(fore_box | hind_box)[0]:
    s_ = 'L' if x[i] > 0 else 'R'; other = 'R' if s_ == 'L' else 'L'
    body_d = chain_distance(co[i], body_chain)
    if fore_box[i]:
        d = min(chain_distance(co[i], [s_ + n for n in ('ForeUpper', 'ForeLower', 'ForeFoot')]),
                chain_distance(co[i], [other + n for n in ('ForeUpper', 'ForeLower', 'ForeFoot')]))
        fore[i] = d < .9 * body_d and (abs(x[i]) > .012 or y[i] < -.33)
    if hind_box[i]:
        d = min(chain_distance(co[i], [s_ + n for n in ('HindUpper', 'HindLower', 'HindFoot')]),
                chain_distance(co[i], [other + n for n in ('HindUpper', 'HindLower', 'HindFoot')]))
        hind[i] = d < .9 * body_d
arm = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', arm); bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, (h, t, parent) in bones.items():
    b = arm.edit_bones.new(n); b.head = h; b.tail = t; b.align_roll(Vector((0, 0, 1)))
    b.parent = arm.edit_bones.get(parent) if parent else None
    b.use_deform = n != 'Socket_Mouth'
bpy.ops.object.mode_set(mode='OBJECT')
groups = {n: o.vertex_groups.new(name=n) for n in bones if n != 'Socket_Mouth'}

def blend(p, names, width=.012):
    ds = np.array([distance(p, *bones[n][:2]) for n in names]); ix = np.argsort(ds)[:4]
    w = np.exp(-((ds[ix] - ds.min()) / width) ** 2); w[w < .025] = 0; w /= w.sum()
    return {names[j]: float(v) for j, v in zip(ix, w) if v > 0}

body = ['Spine1', 'Spine2', 'Neck1', 'Neck2', 'Neck3', 'Head'] + [f'Tail{i}' for i in range(1, 11)]
weights = []
def leg_side(p, kind):
    dl = chain_distance(p, ['L' + kind + n for n in ('Upper', 'Lower', 'Foot')])
    dr = chain_distance(p, ['R' + kind + n for n in ('Upper', 'Lower', 'Foot')])
    return 'L' if dl < dr else 'R'
for i, p in enumerate(co):
    s = 'L' if p[0] > 0 else 'R'
    if fore[i]: s = leg_side(p, 'Fore')
    if hind[i]: s = leg_side(p, 'Hind')
    if wing[i]:
        pts = W[s]; stations = [.045] + [abs(q[0]) for q in pts[:4]]; names = ['Spine2'] + [s + f'Wing{j}' for j in range(4)]
        w = {n: float(np.interp(abs(p[0]), stations, np.eye(5)[k])) for k, n in enumerate(names)}
        root = float(np.clip((abs(p[0]) - .085) / .05, 0, 1))
        # along the upper arm the skin belongs to the wing beyond a third of the bone, however close to the body it is
        h0, t0 = np.array(W[s][0]), np.array(W[s][1]); d0 = t0 - h0; u = float(np.dot(p - h0, d0) / np.dot(d0, d0))
        if distance(p, h0, t0) < .03: root = max(root, float(np.clip(u / .35, 0, 1)))
        root = root * root * (3 - 2 * root)
        bw = blend(p, ['Spine1', 'Spine2', 'Neck1'], .02)   # the wing root follows the shoulders, never the upper neck
        w = {n: root * w.get(n, 0) + (1 - root) * bw.get(n, 0) for n in set(w) | set(bw)}
        w = dict(sorted(w.items(), key=lambda q: q[1], reverse=True)[:4])
    elif head[i]:
        cheek = -.38 < p[1] < -.335 and .392 < p[2] < .412 and pa[i] == 0
        if cheek:
            # behind the open lips the jaw line crosses continuous cheek skin: blend over a 14 mm band, not a cut
            jz = float(np.clip((.408 - p[2]) / .014, 0, 1)); jy = float(np.clip((-.338 - p[1]) / .02, 0, 1))
            j = jz * jz * (3 - 2 * jz) * jy * jy * (3 - 2 * jy); w = {'Jaw': j, 'Head': 1 - j}
        elif jaw[i]:
            j = float(np.clip((-.343 - p[1]) / .012, 0, 1)); j = j * j * (3 - 2 * j); w = {'Jaw': j, 'Head': 1 - j}
        elif pa[i] == 0 and p[1] > -.322 and p[2] < .41:
            w = blend(p, ['Neck2', 'Neck3', 'Head'], .012)
        else:
            w = {'Head': 1.}
    elif fore[i]:
        names = [s + 'ForeUpper', s + 'ForeLower', s + 'ForeFoot']
        if np.linalg.norm(p - np.array(FORE[s][2])) < .012 or p[1] < FORE[s][2][1] - .004:
            w = {s + 'ForeFoot': 1.}
        else:
            w = blend(p, names + ['Spine2', 'Neck1'], .016)
    elif hind[i]:
        names = [s + 'HindUpper', s + 'HindLower', s + 'HindFoot']
        if p[2] < .045:
            w = {s + 'HindFoot': 1.}
        else:
            w = blend(p, names + ['Spine1', 'Tail1', 'Tail2'], .016)
    else:
        w = blend(p, body, .012)
    weights.append({n: v for n, v in w.items() if v > .001})

# soft leg roots: average with neighbours (claws and toes keep their ownership)
adj = [[] for _ in co]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
soft = (pa == 0) & ~wing & ~head & (((fore) & (y > -.31)) | ((hind) & (z > .10)) | ((~fore) & (~hind) & (z < .26) & (y < .04) & (y > -.30)))
# shoulders: the wing root turns up to ~60 degrees against the chest; spread that over the whole shoulder region
shoulder = np.zeros(len(co), bool)
for s_ in 'LR':
    shoulder |= (np.linalg.norm(co - np.array(W[s_][0]), axis=1) < .10) & ~head
soft |= shoulder & (pa == 0)
# the trailing membrane root along the back: inner wing vertices and the body skin within 3 cm of them
wtree = kdtree.KDTree(int(wing.sum()))
for i in np.where(wing)[0]: wtree.insert(Vector(co[i]), int(i))
wtree.balance()
near_wing = np.array([wtree.find(Vector(p))[2] < .03 for p in co])
soft |= (pa == 0) & ~head & ((wing & (ax < .13)) | (~wing & near_wing & (z > .2)))
for _ in range(10):
    old = weights; weights = list(old)
    for i in np.where(soft)[0]:
        if not adj[i]: continue
        w = {n: v * .5 for n, v in old[i].items()}
        for j in adj[i]:
            for n, v in old[j].items(): w[n] = w.get(n, 0) + v * .5 / len(adj[i])
        w = dict(sorted(w.items(), key=lambda q: q[1], reverse=True)[:4]); t = sum(w.values()); weights[i] = {n: v / t for n, v in w.items()}

# separate shells (crest spikes, teeth): rigid copy of their nearest main-body vertex
main = np.where(pa == 0)[0]; tree = kdtree.KDTree(len(main))
for i in main: tree.insert(Vector(co[i]), int(i))
tree.balance()
for part in sorted(set(pa) - {0}):
    ids = np.where(pa == part)[0]
    anchor = min((tree.find(Vector(co[i])) for i in ids), key=lambda q: q[2])[1]
    w = weights[anchor] if not head[ids].all() else {'Head': 1.}
    for i in ids: weights[i] = dict(w)
for i, w in enumerate(weights):
    t = sum(w.values()); assert t > 0
    for n, v in w.items(): groups[n].add([i], v / t, 'REPLACE')
o.parent = rig; mod = o.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
for label, mask in [('wing', wing), ('head', head), ('jaw', jaw), ('fore', fore), ('hind', hind)]:
    attr = me.attributes.new(label, 'BOOLEAN', 'POINT')
    for i, v in enumerate(mask): attr.data[i].value = bool(v)
me.materials.clear()
for name, color in [('DragonBody', (.35, .45, .35, 1)), ('DragonHead', (.55, .65, .5, 1)), ('DragonWings', (.6, .7, .4, 1))]:
    m = bpy.data.materials.new(name); m.diffuse_color = color; m.use_nodes = True; me.materials.append(m)
for f in me.polygons:
    ids = list(f.vertices); f.material_index = 2 if wing[ids].mean() > .5 else (1 if head[ids].mean() > .5 else 0)
report = {'bones': {n: {'head': h.tolist(), 'tail': t.tolist(), 'parent': p} for n, (h, t, p) in bones.items()},
          'unweighted': sum(not v.groups for v in me.vertices), 'max_influences': max(len(v.groups) for v in me.vertices),
          'triangles': sum(len(f.vertices) - 2 for f in me.polygons), 'vertices': len(co),
          'domains': {n: int(a.sum()) for n, a in [('wing', wing), ('head', head), ('jaw', jaw), ('fore', fore), ('hind', hind)]}}
assert report['unweighted'] == 0 and report['max_influences'] <= 4, report
(P / 'work/rig_report.json').write_text(json.dumps(report, indent=2) + '\n')
np.savez(P / 'work/rig_domains.npz', co=co, wing=wing, head=head, jaw=jaw, fore=fore, hind=hind)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_v1.blend'))
print('RIG', report['triangles'], report['domains'])
