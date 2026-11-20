"""Bat-wing bone chains for the gargoyle ('Wings' object from split_parts.py: the arm and finger struts of P00 plus the
membranes P01/P02). Skeleton from work/wing_skeleton.json (wing_probe.py), mirrored for symmetry (x = +-mean|x|, y/z
averaged): Wing_<s>_1 root (shoulder blade) -> elbow, Wing_<s>_2 elbow -> wrist (the hooked claw), Wing_<s>_F1..F4 wrist
-> the four strut tips (F1 the leading finger, F4 the innermost). Parent B_Spine2; roll: local Z = the wing normal.
Weights: every wing vertex takes the two nearest bone segments, w ~ 1 / (d + 2 cm)^3, normalised; within ROOT_R of the
root the share fades into B_Spine2 (fully at the root). The object is parented to the rig with an armature modifier.
Writes work/wing_chains.json (bone heads/tails and the per-side wing-plane axes u (out), v (down), n). Args: -- <in> <out>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
ROOT_R = float(os.environ.get('ROOT_R', '0.14'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = json.load(open(os.path.join(HERE, 'work', 'wing_skeleton.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; wings = bpy.data.objects['Wings']; me = wings.data


def mir(key, i=None):
    a = np.array(SK['L'][key] if i is None else SK['L'][key][i]); b = np.array(SK['R'][key] if i is None else SK['R'][key][i])
    x = (abs(a[0]) + abs(b[0])) / 2; yz = (a[1:] + b[1:]) / 2
    return {'L': np.array([x, *yz]), 'R': np.array([-x, *yz])}


P = {k: mir(k) for k in ('root', 'elbow', 'wrist')}
TIPS = [mir('tips', i) for i in range(4)]
chains, segs = {}, {}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s in 'LR':
    root, el, wr = P['root'][s], P['elbow'][s], P['wrist'][s]
    tips = [t[s] for t in TIPS]
    u = wr - root; u /= np.linalg.norm(u)
    n = np.cross(u, tips[1] - wr); n /= np.linalg.norm(n)
    if n[1] < 0:
        n = -n
    v = np.cross(n, u)
    if v[2] > 0:
        v = -v
    defs = [(f'Wing_{s}_1', root, el, 'B_Spine2'), (f'Wing_{s}_2', el, wr, f'Wing_{s}_1')]
    defs += [(f'Wing_{s}_F{k + 1}', wr, tips[k], f'Wing_{s}_2') for k in range(4)]
    for name, h, t, par in defs:
        b = eb.new(name); b.head = Vector(h); b.tail = Vector(t); b.align_roll(Vector(n))
        b.parent = eb[par]; b.use_connect = name.endswith('_2'); b.use_deform = True
        segs[name] = (h, t)
    chains[s] = {'bones': {nm: [list(map(float, h)), list(map(float, t))] for nm, h, t, _ in defs},
                 'u': u.tolist(), 'v': v.tolist(), 'n': n.tolist()}
bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(wings.matrix_world @ vv.co) for vv in me.vertices])


def seg_d(p, a, b):
    t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * (b - a)), axis=1)


wings.vertex_groups.clear()
names = ['B_Spine2'] + list(segs)
G = {nm: wings.vertex_groups.new(name=nm) for nm in names}
for s, sg in (('L', 1.0), ('R', -1.0)):
    ids = np.where(co[:, 0] * sg >= 0)[0]; p = co[ids]
    own = [nm for nm in segs if nm.startswith(f'Wing_{s}_')]
    D = np.stack([seg_d(p, *map(np.array, segs[nm])) for nm in own], 1)
    o = np.argsort(D, 1)[:, :2]
    d2 = np.take_along_axis(D, o, 1); w = 1.0 / (d2 + 0.02) ** 3; w /= w.sum(1, keepdims=True)
    spine = np.clip(1 - np.linalg.norm(p - P['root'][s], axis=1) / ROOT_R, 0, 1)
    for j, vi in enumerate(ids):
        for k in range(2):
            G[own[o[j, k]]].add([int(vi)], float(w[j, k] * (1 - spine[j])), 'REPLACE')
        if spine[j] > 0:
            G['B_Spine2'].add([int(vi)], float(spine[j]), 'REPLACE')
wings.parent = rig
for md in [m for m in wings.modifiers if m.type == 'ARMATURE']:
    wings.modifiers.remove(md)
md = wings.modifiers.new('Armature', 'ARMATURE'); md.object = rig
json.dump(chains, open(os.path.join(HERE, 'work', 'wing_chains.json'), 'w'), indent=1)
print('WINGRIG bones', len(segs), 'vertices', len(co), {s: {k: np.round(P[k][s], 3).tolist() for k in P} for s in 'L'})
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
