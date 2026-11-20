"""hkr copy of rifle_clear.py with the torso plates (Arm_* on B_Spine2 / B_Pelvis) as obstacles and the right arm plates as movers.
Keep the rifle and the right fist out of the armoured torso (gate G6: the source mannequin's chest is slimmer than
the guard's chest plate, so the aim pressed the stock and the fist up to 8 cm into it). Per frame of the listed clips:
the evaluated torso, plates, head and legs (not the arms, not the skirt) as a BVH; the deepest point of the rifle and
of the right fist inside it (nearest-surface test, as gates.py) plus MARGIN; the right hand moves by that depth along
the chest's horizontal forward axis (smoothed over time, kept at least the depth on the frames that need it), the
right arm re-solved with armik (hand rotation kept). The left hand is re-seated afterwards by support_hand.py.
PASSES rounds. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, cfg
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
MARGIN, PASSES, SIG = float(os.environ.get('MARGIN', '0.012')), int(os.environ.get('PASSES', '2')), 1.5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; gun = bpy.data.objects['Rifle']; sc = bpy.context.scene; AW = rig.matrix_world
me = body.data; nv = len(me.vertices)
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]; W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
arm = W[:, [i for i, n in enumerate(names) if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]].sum(1) > 0.2
P0 = np.array([v.co[:] for v in me.vertices]); JB = lambda n: np.array(rig.data.bones[n].head_local)
rhand = cfg.hand_mask(P0, pv, 'R', JB('B_R_Hand'), JB('B_R_Forearm'), 0.0)
tail = W[:, [i for i, n in enumerate(names) if n.startswith('Bone_0') and n not in ('Bone_024', 'Bone_023', 'Bone_025')]].sum(1) > 0.5
solid = ~arm & ~tail                                       # hkr: the whole body but the arms and the tail
faces = [tuple(f.vertices) for f in me.polygons if all(solid[i] for i in f.vertices)]


def evaluated(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


# v2 armour: the whole cuirass (chest, back, abdomen lames, belt, tasset) and the leg plates are obstacles
OBST_BONES = ('B_Spine2', 'B_Spine1', 'B_Spine', 'B_Pelvis', 'B_Groin', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf')
OBST = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in OBST_BONES]
MOVERS = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_R_Forearm', 'B_R_UpperArm')]


DIRS = [Vector((0.0123, 0.0217, 1.0)).normalized(), Vector((0.71, -0.33, -0.62)).normalized(), Vector((-0.55, 0.81, 0.2)).normalized()]


def parity(tree, p, maxd=1.0):
    votes = 0
    for d in DIRS:
        o = Vector(p); n = 0; tr = 0.0
        while tr < maxd:
            loc, nrm, fi, dist = tree.ray_cast(o, d, maxd - tr)
            if loc is None: break
            n += 1; tr += dist + 1e-5; o = loc + d * 1e-5
        votes += n % 2
    return votes >= 2


HANDV = W[:, [i for i, n in enumerate(names) if any(t in n for t in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]].sum(1) > 0.5
FULL = [tuple(f.vertices) for f in me.polygons if not all(HANDV[k] for k in f.vertices)]   # the arms hold the gun (G5, support_hand)
ALLF = [tuple(f.vertices) for f in me.polygons]
RARM = np.nonzero(W[:, [i for i, n in enumerate(names) if n.startswith('B_R_') and any(t in n for t in ('Forearm', 'Hand', 'Finger'))]].sum(1) > 0.5)[0]
_RS = set(RARM.tolist())
RARMF = [all(k in _RS for k in f) for f in ALLF]
# LEFT=1: the supporting left forearm and hand (skin, guard plate) as movers too (a hit drove them through the belt
# and the thigh); the left hand then moves with the carbine (same offset, rotation kept) so the support stays seated
LEFT = bool(os.environ.get('LEFT'))
LARM = np.nonzero(W[:, [i for i, n in enumerate(names) if n.startswith('B_L_') and any(t in n for t in ('Forearm', 'Hand', 'Finger'))]].sum(1) > 0.5)[0]
_LS = set(LARM.tolist())
LARMF = [all(k in _LS for k in f) for f in ALLF]
# armour pass: the upper arms (skin past the shoulder ring) against the cuirass too: the supporting left arm crossed
# the v2 chest plate's front in Running (1.8 cm); pushing the gun forward swings the arm off it
P0_ = np.array([v.co[:] for v in me.vertices])
UARM = np.nonzero((W[:, [i for i, n in enumerate(names) if 'UpperArm' in n]].sum(1) > 0.6) &
                  (np.minimum(np.linalg.norm(P0_ - JB('B_L_UpperArm'), axis=1), np.linalg.norm(P0_ - JB('B_R_UpperArm'), axis=1)) > 0.06))[0]
_US = set(UARM.tolist())
UARMF = [sum(k in _US for k in f) * 2 > len(f) for f in ALLF]
if LEFT:
    MOVERS += [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_L_Forearm', 'B_L_UpperArm', 'B_L_Buckler')]
    RARM = np.concatenate([RARM, LARM]); RARMF = [x or y for x, y in zip(RARMF, LARMF)]
    LMOV = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_L_Forearm', 'B_L_Buckler')]


def depth():
    """deepest point of the carbine inside the body (closed skin, parity) or a torso plate, and of the right arm's
    plates inside a torso plate (nearest distance of the inside points)"""
    bc = evaluated(body); best = 0.0
    trees = [BVHTree.FromPolygons(bc.tolist(), FULL)]
    for o in OBST:
        e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
        trees.append(BVHTree.FromPolygons([tuple(o.matrix_world @ v.co) for v in m.vertices], [tuple(p.vertices) for p in m.polygons if p.material_index == 0])); e.to_mesh_clear()
    G = evaluated(gun)
    if LEFT:                                               # the left forearm guard inside the body (thighs, hips)
        for p in np.vstack([evaluated(o) for o in LMOV]):
            loc, n, fi, d = trees[0].find_nearest(Vector(p), 0.15)
            if loc is None or d <= best: continue
            if (Vector(p) - loc).dot(n) < 0 and parity(trees[0], p, 0.6): best = d
    for k, tree in enumerate(trees):
        pts = G if k == 0 else np.vstack([G, bc[RARM], bc[UARM]] + [evaluated(o) for o in MOVERS])
        for p in pts:
            loc, n, fi, d = tree.find_nearest(Vector(p), 0.15)
            if loc is None or d <= best: continue
            if (Vector(p) - loc).dot(n) < 0 and parity(tree, p, 0.6): best = d
    # the torso plates' vertices inside the right forearm / hand (the aim pressed the forearm onto the chest plate)
    full = BVHTree.FromPolygons(bc.tolist(), ALLF)
    # the hand's own faces too: a plate vertex inside the body counts against the arm when the arm's surface is about
    # as near as the nearest skin (a fist resting over the belly is nearer the belly than its own knuckles)
    armt = BVHTree.FromPolygons(bc.tolist(), [f for f, r, u in zip(ALLF, RARMF, UARMF) if r or u])
    for o in OBST:
        for p in evaluated(o):
            loc, n, fi, d = full.find_nearest(Vector(p), 0.08)
            if loc is None or (Vector(p) - loc).dot(n) >= 0: continue
            la, na, fa, da = armt.find_nearest(Vector(p), 0.08)
            if la is None or da <= best or da > d + 0.01: continue
            if parity(full, p, 1.2): best = da          # 1.2 m rays as armour_gate.py: 0.6 m ones can end in the torso
    return best


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    first = None
    for it in range(PASSES):
        need = []
        for f in fr:
            sc.frame_set(f); need.append(depth())
        need = np.array(need)
        if first is None:
            first = float(need.max())
        push = np.where(need > 0, need + MARGIN, 0.0)
        k = np.exp(-0.5 * (np.arange(-5, 6) / SIG) ** 2); k /= k.sum()
        push = np.maximum(np.convolve(np.pad(push, 5, mode='edge'), k, mode='valid'), push)
        if push.max() <= 0:
            break
        keys = {}
        for f, d in zip(fr, push):
            sc.frame_set(f)
            if d <= 0:
                continue
            C = AW @ rig.pose.bones['B_Spine2'].matrix
            fwd = C.to_3x3() @ Vector((0, 0, -1)) if False else None
            sp = AW @ rig.pose.bones['B_Spine2'].matrix; pe = AW @ rig.pose.bones['B_Pelvis'].matrix
            # the chest's forward: perpendicular to the shoulder line, horizontal, toward the rifle's muzzle side
            sh = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation - (AW @ rig.pose.bones['B_R_UpperArm'].matrix).translation
            fwd = Vector((0, 0, 1)).cross(sh); fwd.z = 0; fwd.normalize()
            if fwd.dot(Vector((0, -1, 0))) < 0:
                fwd = -fwd
            H = AW @ rig.pose.bones['B_R_Hand'].matrix; HL = AW @ rig.pose.bones['B_L_Hand'].matrix
            armik.solve(rig, 'R', H.translation + fwd * float(d), hand_rot=H.to_3x3().normalized())
            if LEFT:
                armik.solve(rig, 'L', HL.translation + fwd * float(d), hand_rot=HL.to_3x3().normalized())
            sides = 'RL' if LEFT else 'R'
            keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for sd in sides for n in (f'B_{sd}_UpperArm', f'B_{sd}_Forearm', f'B_{sd}_Hand')}
        prev = {}
        for f in fr:
            if f not in keys:
                continue
            for n, q in keys[f].items():
                pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
                if n in prev and q.dot(prev[n]) < 0: q = -q
                prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    last = []
    for f in fr:
        sc.frame_set(f); last.append(depth())
    rep[name] = {'before_cm': round(first * 100, 1), 'after_cm': round(float(max(last)) * 100, 1)}
    print('RIFLECLEAR', name, json.dumps(rep[name]))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
