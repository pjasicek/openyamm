"""Elbow clearance (user review 2026-10-20: in the thrust the right elbow went through the chest to the left side and
the upper arm sank into it, frames 22-40 up to 11.6 cm; arm_torso_probe.py). Per frame of each listed action and arm,
the elbow turns about the shoulder -> wrist line (the wrist stays where it is and the hand keeps its world orientation,
so a held prop does not move) by the angle theta of least cost over the whole clip (Viterbi): the depth of the
skinned upper-arm and forearm vertices (weighted > 0.5; upper arm beyond 8 cm from the shoulder joint) inside the
skinned torso (faces of the spine/pelvis/neck/head vertices; the G6 test of arm_torso_probe.py: behind the closest
face within a 45 deg cone of its normal, up to 12 cm), PEN per cm, + K_THETA per degree of theta + K_STEP per degree
and K_STEP2 per degree squared between frames; a one-shot clip's first and last frames keep theta 0 (they meet the idle). The mesh is evaluated for every candidate theta (a rigid turn of the arm vertices missed the skin
blend at the shoulder and promised clearance the skinned arm did not have) on the frames with contact and NEAR frames
around them; elsewhere theta stays 0. Run it on the final weights, then rebake the twist bones.
Args: -- <in blend> <out blend> <Action>:<sides LR> ...   (env PEN=40 K_THETA=0.2 K_STEP=0.4 K_STEP2=0.05 MAXDEG=120 STEP=10 NEAR=4)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
PEN = float(os.environ.get('PEN', '40')); K_THETA = float(os.environ.get('K_THETA', '0.2'))
K_STEP = float(os.environ.get('K_STEP', '0.4')); K_STEP2 = float(os.environ.get('K_STEP2', '0.05')); MAXDEG = int(os.environ.get('MAXDEG', '120'))
THETAS = np.arange(-MAXDEG, MAXDEG + 1, int(os.environ.get('STEP', '10'))); NEAR = int(os.environ.get('NEAR', '4'))
LOOPS = ('Standing', 'Walking', 'Running', 'Fidget')
names = [g.name for g in body.vertex_groups]
AXIAL = ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head')
nv = len(me.vertices); ax = np.zeros(nv); wt = {}
for v in me.vertices:
    for e in v.groups:
        n = names[e.group]
        if n in AXIAL:
            ax[v.index] += e.weight
        wt.setdefault(n, np.zeros(nv))[v.index] += e.weight
tris = [tuple(p.vertices) for p in me.polygons if all(ax[i] > 0.6 for i in p.vertices)]


def part(prefix):                                                # the bone and its twist bone
    return sum((w for n, w in wt.items() if n.startswith(prefix)), np.zeros(nv))


ARMV = {s: np.where((part(f'B_{s}_UpperArm') > 0.5) | (part(f'B_{s}_Forearm') > 0.5))[0]
        for s in 'LR'}


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def pen(bvh, P):
    worst = 0.0
    for p in P:
        p = Vector(p); hit = bvh.find_nearest(p, 0.12)
        if hit[0] is None:
            continue
        d = p - hit[0]; L = d.length
        if L > 1e-6 and d.dot(hit[1]) < -0.7 * L:
            worst = max(worst, L)
    return worst


def pose(snap, s, th):
    """The frame's pose with the upper arm turned by th about the shoulder -> wrist line, the hand's world turn kept."""
    for pb in rig.pose.bones:
        pb.matrix_basis = snap[pb.name]
    bpy.context.view_layer.update()
    if th == 0:
        return
    H = armik.W(rig, f'B_{s}_Hand').copy(); U = armik.W(rig, f'B_{s}_UpperArm')
    u = (H.translation - U.translation).normalized(); R = Quaternion(u, math.radians(float(th))).to_matrix()
    M = (R @ U.to_3x3().normalized()).to_4x4(); M.translation = U.translation; armik.set_world(rig, f'B_{s}_UpperArm', M)
    armik.set_world(rig, f'B_{s}_Hand', H)


def depth(s):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear(); co = co.reshape(-1, 3)
    bvh = BVHTree.FromPolygons([Vector(c) for c in co], tris)
    S = np.array(rig.pose.bones[f'B_{s}_UpperArm'].head)
    A = co[ARMV[s]]; A = A[np.linalg.norm(A - S, axis=1) > 0.08]
    return pen(bvh, A)


for item in items:
    an, sides = item.split(':'); act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    frames = list(range(f0, f1 + 1))
    for s in sides:
        set_act(act); snaps = []
        for f in frames:
            sc.frame_set(f); snaps.append({pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones})
        set_act(None)
        d0 = []
        for sn in snaps:
            pose(sn, s, 0); d0.append(depth(s))
        hit = [i for i, d in enumerate(d0) if d > 0.005]
        active = sorted({j for i in hit for j in range(i - NEAR, i + NEAR + 1) if 0 <= j < len(frames)})
        costs = []
        for i, sn in enumerate(snaps):
            row = np.full(len(THETAS), 1e6); row[THETAS == 0] = d0[i] * 100 * PEN
            if i in active:
                for k, th in enumerate(THETAS):
                    if th != 0:
                        pose(sn, s, th); row[k] = depth(s) * 100 * PEN + K_THETA * abs(th)
            costs.append(row)
        if an not in LOOPS:                                          # a one-shot clip starts and ends at the idle's arm
            for i in (0, len(snaps) - 1):
                costs[i][THETAS != 0] = 1e6
        C = np.array(costs); n = len(THETAS)
        dth = np.abs(np.subtract.outer(THETAS, THETAS)).astype(float)
        step = K_STEP * dth + K_STEP2 * dth * dth                    # the square term spreads a turn over frames
        acc = C[0].copy(); back = []
        for i in range(1, len(frames)):
            tot = acc[None, :] + step                               # [new, old]
            back.append(np.argmin(tot, axis=1)); acc = tot.min(axis=1) + C[i]
        k = int(np.argmin(acc)); path = [k]
        for b in reversed(back):
            k = int(b[k]); path.append(k)
        path.reverse()
        th_deg = THETAS[path]
        before = d0
        after = [(C[i][path[i]] - K_THETA * abs(th_deg[i])) / (100 * PEN) for i in range(len(frames))]
        # apply: the upper arm turns about the shoulder -> wrist line, the hand keeps its world orientation
        keys = []
        for i, sn in enumerate(snaps):
            pose(sn, s, th_deg[i])
            keys.append({nm: rig.pose.bones[nm].matrix_basis.to_quaternion() for nm in (f'B_{s}_UpperArm', f'B_{s}_Hand')})
        set_act(act)
        prev = {}
        for i, f in enumerate(frames):
            for nm, q in keys[i].items():
                pb = rig.pose.bones[nm]; pb.rotation_mode = 'QUATERNION'
                if nm in prev and q.dot(prev[nm]) < 0:
                    q = -q
                prev[nm] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        set_act(None)
        moved = [int(f) for f, t in zip(frames, th_deg) if t != 0]
        print(f'ELBOWDEPTH {an} {s}: ' + ' '.join(f'{f}:{d0[i] * 100:.1f}/{after[i] * 100:.1f}' for i, f in enumerate(frames) if d0[i] > 0.005 or after[i] > 0.005))
        print(f'ELBOWPATH {an} {s}: ' + ' '.join(f'{f}:{int(t)}' for f, t in zip(frames, th_deg) if t != 0))
        print(f'ELBOWCLEAR {an} {s}: arm depth before max {max(before) * 100:.1f} cm, after max {max(after) * 100:.1f} cm; '
              f'theta {int(th_deg.min())}..{int(th_deg.max())} deg on {len(moved)} frames {moved[:3]}..{moved[-3:]}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
