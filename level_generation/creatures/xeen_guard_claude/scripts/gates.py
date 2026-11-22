"""Clip gates on work/anim_v1.blend (rigid plates: posed vertex = bone pose matrix x rest^-1 x rest vertex).
Per clip:
- contacts (G6 / arm and hand gate 1, 4): deepest point of a hand, forearm or upper arm inside a closed plate of the
  trunk, the thighs, the calves or the dome, and of one leg inside the other (cm; nearest-face normal test on the
  plate as posed); a pauldron and its own upper arm, the elbow and wrist neighbours are adjacent, not contacts;
- wrist swing (gate 5): the hand's rotation against the forearm from the bind relation (deg); forearm twist: the
  forearm's rotation about its own axis against the upper arm (deg), and its largest frame-to-frame change;
- soles (feet): the lowest sole point per frame (cm), min and max over the clip, and frames with no foot on the floor;
- motion: largest per-frame vertex step (cm) and second difference (cm/frame^2); loops: the seam (cm);
- floor: lowest point of the body (cm).
Writes work/gates.json. Args: -- [clip ...]"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']; me = mesh.data
sc = bpy.context.scene
gi = {g.index: g.name for g in mesh.vertex_groups}
VB = np.array([gi[v.groups[0].group] for v in me.vertices])
V0 = np.array([v.co[:] for v in me.vertices])
part = np.zeros(len(me.vertices), int)
for p in me.polygons:
    for i in p.vertices:
        part[i] = me.attributes['part'].data[p.index].value
polys = {}
for p in me.polygons:
    polys.setdefault(VB[p.vertices[0]], []).append(list(p.vertices))
BONES = sorted(set(VB))
RINV = {b: np.array(rig.data.bones[b].matrix_local.inverted()) for b in BONES}
TRUNK = ['B_Spine2', 'B_Spine', 'B_Pelvis', 'B_Head']
LOOPS = {'Standing', 'Walking', 'Running'}


def posed():
    P = np.empty_like(V0)
    for b in BONES:
        m = np.array(rig.pose.bones[b].matrix) @ RINV[b]
        idx = VB == b
        P[idx] = V0[idx] @ m[:3, :3].T + m[:3, 3]
    return P


def hits(tree, o, d):
    n = 0; o = Vector(o)
    for _ in range(64):
        loc, nor, idx, dist = tree.ray_cast(o, d)
        if loc is None:
            break
        n += 1; o = loc + d * 1e-4
    return n


def depth_inside(P, target, pts):
    """Deepest of pts inside the closed plate `target` (posed), cm: ray parity in two directions (both odd), depth =
    distance to the plate's surface. Joint spheres are not plates."""
    ids = np.where((VB == target) & (part != 2))[0]
    if not len(ids):
        return 0.0
    T = P[ids]; lo = T.min(0); hi = T.max(0)
    inb = pts[np.all((pts > lo) & (pts < hi), axis=1)]
    if not len(inb):
        return 0.0
    remap = {int(i): k for k, i in enumerate(ids)}
    faces = [[remap[i] for i in f] for f in polys[target] if all(i in remap for i in f)]
    tree = BVHTree.FromPolygons([Vector(p) for p in T], faces)
    best = 0.0
    d1 = Vector((0.31, 0.27, 0.91)).normalized(); d2 = Vector((-0.4, 0.83, -0.39)).normalized()
    for p in inb:
        if hits(tree, p, d1) % 2 == 1 and hits(tree, p, d2) % 2 == 1:
            best = max(best, tree.find_nearest(Vector(p))[3])
    return best * 100


def local_rot(child, parent):
    pc = rig.pose.bones[child]; pp = rig.pose.bones[parent]
    rest = rig.data.bones[parent].matrix_local.inverted() @ rig.data.bones[child].matrix_local
    cur = pp.matrix.inverted() @ pc.matrix
    return (rest.inverted() @ cur).to_quaternion()


def twist_deg(q, axis):
    """Twist of q about axis (swing-twist decomposition), degrees."""
    v = Vector((q.x, q.y, q.z)); p = axis * v.dot(axis)
    t = Vector((q.w, p.x, p.y, p.z)); n = t.length
    if n < 1e-9:
        return 0.0
    w = t[0] / n
    ang = 2 * math.degrees(math.acos(max(-1, min(1, abs(w)))))
    return ang if (p.dot(axis) * (1 if w >= 0 else -1)) >= 0 else -ang


out = {}
for act in bpy.data.actions:
    if a and act.name not in a:
        continue
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = []; contacts = {}; wrist = 0.0; twist = []; soles = []; airborne = 0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        P = posed(); frames.append(P)
        for s in ('L', 'R'):
            o = 'R' if s == 'L' else 'L'
            for src_b in (f'B_{s}_Hand', f'B_{s}_Forearm', f'B_{s}_UpperArm'):
                pts = P[(VB == src_b) & (part != 2)][::2]
                tg = TRUNK + [f'B_L_Thigh', f'B_R_Thigh'] + ([f'B_L_Calf', f'B_R_Calf'] if 'UpperArm' not in src_b else [])
                for t in tg:
                    d = depth_inside(P, t, pts)
                    if d > contacts.get(f'{src_b}>{t}', 0):
                        contacts[f'{src_b}>{t}'] = round(d, 2)
            for leg in (f'B_{s}_Calf', f'B_{s}_Foot'):
                pts = P[(VB == leg) & (part != 2)][::2]
                for t in (f'B_{o}_Calf', f'B_{o}_Foot', f'B_{o}_Thigh'):
                    d = depth_inside(P, t, pts)
                    if d > contacts.get(f'{leg}>{t}', 0):
                        contacts[f'{leg}>{t}'] = round(d, 2)
            qh = local_rot(f'B_{s}_Hand', f'B_{s}_Forearm')
            wrist = max(wrist, math.degrees(qh.angle) if qh.angle <= math.pi else 360 - math.degrees(qh.angle))
            qf = local_rot(f'B_{s}_Forearm', f'B_{s}_UpperArm')
            twist.append((s, twist_deg(qf, Vector((0, 1, 0)))))
        fl = [P[(VB == f'B_{s}_Foot')][:, 2].min() for s in ('L', 'R')]
        soles.append(fl)
        if min(fl) > 0.01:
            airborne += 1
    F = np.stack(frames)
    step = np.linalg.norm(np.diff(F, axis=0), axis=-1).max() * 100 if len(F) > 1 else 0
    if len(F) > 1:
        dd = np.linalg.norm(np.diff(F, axis=0), axis=-1)
        fi, vi = np.unravel_index(dd.argmax(), dd.shape)
        print('STEPAT', act.name, 'frame', int(fi), '->', int(fi) + 1, 'bone', VB[vi], 'cm', round(float(dd.max() * 100), 1),
              'per bone', {b: round(float(dd[fi][VB == b].max() * 100), 1) for b in BONES if dd[fi][VB == b].max() > 0.08})
    if len(F) > 2:
        aa = np.linalg.norm(np.diff(F, 2, axis=0), axis=-1)
        fi, vi = np.unravel_index(aa.argmax(), aa.shape)
        print('ACCAT', act.name, 'frame', int(fi) + 1, 'bone', VB[vi], 'cm', round(float(aa.max() * 100), 1),
              {b: round(float(aa[fi][VB == b].max() * 100), 1) for b in BONES if aa[fi][VB == b].max() > 0.06})
    acc = np.linalg.norm(np.diff(F, 2, axis=0), axis=-1).max() * 100 if len(F) > 2 else 0
    seam = np.linalg.norm(F[-1] - F[0], axis=-1).max() * 100
    tw = {s: [t for ss, t in twist if ss == s] for s in ('L', 'R')}
    twmax = max(abs(t) for t in tw['L'] + tw['R'])
    twstep = max(max((abs(x - y) for x, y in zip(v[1:], v[:-1])), default=0) for v in tw.values())
    S = np.array(soles) * 100
    worst = sorted(contacts.items(), key=lambda kv: -kv[1])[:4]
    out[act.name] = {'frames': len(F), 'contacts_cm_worst': worst, 'wrist_deg': round(wrist, 1),
                     'forearm_twist_deg': round(twmax, 1), 'forearm_twist_step_deg': round(twstep, 1),
                     'sole_cm': [round(float(S.min()), 2), round(float(S.min(1).max()), 2)],
                     'frames_no_foot_down': airborne, 'step_cm': round(float(step), 2), 'accel_cm': round(float(acc), 2),
                     'seam_cm': round(float(seam), 2) if act.name in LOOPS else None,
                     'lowest_cm': round(float(F[..., 2].min() * 100), 2)}
    print('GATE', act.name, json.dumps(out[act.name]))
json.dump(out, open(os.path.join(HERE, 'work', 'gates.json'), 'w'), indent=1)
