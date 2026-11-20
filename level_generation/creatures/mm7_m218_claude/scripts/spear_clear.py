"""Spear clearance for clips that keep their source arms (fidget, death, cast, hit): per frame, if the spear shaft
(grip axis from work/grip_pose.json, or grip_pose_L.json with SIDE=L; BUTT..TIP m from the grip, default -0.70 .. +1.19) passes inside the skin (garment 0, the right arm
excluded; inside = behind the nearest face within a 45 deg cone, 8 cm search), the hand is turned about the wrist by
the smallest rotation (directions every 30 deg around the shaft, 3..36 deg) that clears it with a 1.5 cm margin.
The per-frame angles are dilated by 2 frames and smoothed (Gaussian, sigma 1.5 frames) so the hand eases in and out.
Runs before twist_bones.py (the forearm twist is baked from the final hand). Args: -- <in blend> <out blend> <Action> ..."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
S = os.environ.get('SIDE', 'R')                            # m218: the spear rides in the LEFT fist
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json' if S == 'R' else f'grip_pose_{S}.json')))
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
gv = np.zeros(len(me.vertices), np.int32)
if 'garment' in me.attributes:
    me.attributes['garment'].data.foreach_get('value', gv)
else:                                                           # before weights_fix.py: the skin shells by piece
    _p = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', _p)
    gv = np.where(np.isin(_p, [int(x) for x in os.environ.get('SKIN_PIECES', '0,1,2').split(',')]), 0, 1).astype(np.int32)
names = [g.name for g in body.vertex_groups]
armw = np.zeros(len(me.vertices))
for v in me.vertices:
    armw[v.index] = sum(e.weight for e in v.groups if any(names[e.group].startswith(f'B_{x}_') for x in os.environ.get('EXCL_SIDES', S)) and any(k in names[e.group] for k in ('UpperArm', 'Forearm', 'Hand', 'Finger')))
keep = (gv == 0) & (armw < 0.2)
if 'piece' in me.attributes:                                    # props (1000+) are not body
    _pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', _pc); keep &= _pc < 1000
faces = [tuple(p.vertices) for p in me.polygons if all(keep[i] for i in p.vertices)]
T = np.linspace(float(os.environ.get('BUTT', '-0.70')), float(os.environ.get('TIP', '1.19')), 64); MARGIN = 0.025


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots): rig.animation_data.action_slot = x.slots[0]


def depth(tree, H):
    g = H @ GC; d = (H.to_3x3() @ AX).normalized(); worst = 0.0
    for t in T:
        p = g + d * t
        loc, nrm, idx, dist = tree.find_nearest(p, 0.08)
        if loc is None: continue
        if (p - loc).dot(nrm) < -0.7 * dist: worst = max(worst, dist + MARGIN)
        elif dist < MARGIN: worst = max(worst, MARGIN - dist)
    return worst


for an in acts:
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    rots = []
    for f in range(f0, f1 + 1):
        set_act(act); sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
        tree = BVHTree.FromPolygons(P, faces)
        H = armik.W(rig, f'B_{S}_Hand'); d0 = depth(tree, H)
        best = (0.0, Quaternion())
        if d0 > 0:
            dax = (H.to_3x3() @ AX).normalized(); u = dax.orthogonal().normalized(); w = dax.cross(u)
            found = None
            for ang in range(3, 37, 3):
                for k in range(12):
                    th = 2 * math.pi * k / 12; axis = (u * math.cos(th) + w * math.sin(th))
                    q = Quaternion(axis, math.radians(ang))
                    R = q.to_matrix() @ H.to_3x3(); H2 = R.to_4x4(); H2.translation = H.translation
                    if depth(tree, H2) == 0.0:
                        found = (ang, q); break
                if found: break
            best = found if found else (36.0, Quaternion())
        rots.append((d0, best))
    # dilate + smooth the rotation (as axis-angle vectors)
    vec = np.array([np.array(q.axis) * math.radians(ang) if ang else np.zeros(3) for d0, (ang, q) in rots])
    mag = np.linalg.norm(vec, axis=1)
    n = len(vec); vd = vec.copy()
    for i in range(n):
        j = max(range(max(0, i - 3), min(n, i + 4)), key=lambda k: mag[k]); vd[i] = vec[j] if mag[j] > mag[i] else vec[i]
    gk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); gk /= gk.sum()
    pad = np.concatenate([np.repeat(vd[:1], 4, 0), vd, np.repeat(vd[-1:], 4, 0)])
    vs = np.array([sum(gk[k] * pad[i + k] for k in range(9)) for i in range(n)])
    for i, f in enumerate(range(f0, f1 + 1)):
        set_act(act); sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        set_act(None)
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        bpy.context.view_layer.update()
        ang = np.linalg.norm(vs[i])
        if ang > 1e-4:
            q = Quaternion(Vector(vs[i] / ang), ang); H = armik.W(rig, f'B_{S}_Hand')
            armik.set_world(rig, f'B_{S}_Hand', armik.rot_world(H, q.to_matrix() @ H.to_3x3().normalized()))
        pb = rig.pose.bones[f'B_{S}_Hand']; qq = pb.rotation_quaternion.copy()
        set_act(act); pb.rotation_quaternion = qq; pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    hit = [i for i, (d0, _) in enumerate(rots) if d0 > 0]
    print(f'SPEARCLEAR {an}: frames with contact {len(hit)} of {n}, worst {max([d0 for d0, _ in rots] + [0]) * 100:.1f} cm, '
          f'max turn {math.degrees(float(np.linalg.norm(vs, axis=1).max())):.0f} deg, unresolved {sum(1 for d0, (ang, q) in rots if d0 > 0 and ang >= 36)}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
