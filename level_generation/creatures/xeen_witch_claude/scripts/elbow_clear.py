"""Arm and staff clearance (witch G6 repair, 2026-11-20 session 2): where the left forearm/elbow fold presses into the
closed torso skin (Running, Cast start, Fidget, the lying corpse) or the staff's fork end enters the body (the death's
first frames), move the wrist out along the outward face normal at the deepest point by depth + margin, with the elbow
plane pushed the same way (armik.solve with a pole for the joint positions; the upper arm and forearm are then set as
pure swings of their own rotations, since armik's plane roll flips on a near-straight arm), the hand's world
orientation kept. Offsets are a smooth envelope
over time (raised cosine, +-EASE frames; cyclic for loops) and the pass repeats until the measured depth is under TOL.

Measured on the FINAL skinned body (the reduced, weight-fixed Body of a reference blend, normally work/rig_v5.blend of
the previous build) driven by this file's rig: the chain's own Body still has Meshy's base weights at this stage.
The inside test is g6_contacts.py's (closest closed-skin face, behind it within a 45 deg cone; robe skirt and open
shells excluded). Runs right after arm_push.py, before wrist_ease/forearm_hinge/twist, so those see the cleared arm.

Args: -- <in blend> <out blend> <reference blend> <Action>:<L|R>:<forearm|staff|both>[:loop] ...
Env: MARGIN (m, default 0.012), EASE (frames, default 4), TOL (m, default 0.003), ITER (default 4)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common

a = sys.argv[sys.argv.index('--') + 1:]
src, out, ref, items = a[0], a[1], a[2], a[3:]
MARGIN = float(os.environ.get('MARGIN', '0.012')); EASE = int(os.environ.get('EASE', '4'))
TOL = float(os.environ.get('TOL', '0.003')); ITER = int(os.environ.get('ITER', '4'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
# the reference body (final weights), parented to this file's rig
with bpy.data.libraries.load(os.path.abspath(ref), link=False) as (src_data, dst):
    dst.objects = ['Body']
mb = dst.objects[0]; mb.name = 'MeasureBody'; sc.collection.objects.link(mb)
for m in mb.modifiers:
    if m.type == 'ARMATURE':
        m.object = rig
mb.parent = rig
me = mb.data
names = [g.name for g in mb.vertex_groups]; col = {n: i for i, n in enumerate(names)}
nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight


def part(side, keys):
    return Wt[:, [col[n] for n in names if n.startswith(f'B_{side}_') and any(k in n for k in keys)]].sum(1)


PIECE = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', PIECE)
PC = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PC)
REST = np.array([tuple(mb.matrix_world @ v.co) for v in me.vertices])
SHEET = (PC == 0) & (REST[:, 2] < 1.08)
faces = [tuple(p.vertices) for p in me.polygons]
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
SPEAR_T = np.linspace(-0.82, 0.47, 52)


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def measure(side, what):
    """(depth, outward direction) of the deepest arm/staff sample inside the closed skin at the current pose."""
    deps = bpy.context.evaluated_depsgraph_get(); ev = mb.evaluated_get(deps); m = ev.to_mesh()
    P = np.array([tuple(mb.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    keep = ~(part(side, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2)
    fl = [fc for fc in faces if all(keep[i] for i in fc) and PIECE[fc[0]] == 0 and not SHEET[fc[0]]]
    tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
    pts = []
    if what in ('forearm', 'both'):
        pts += [Vector(p) for p in P[part(side, ('Forearm',)) > 0.5]]
    if what in ('staff', 'both'):
        hm = rig.matrix_world @ rig.pose.bones[f'B_{side}_Hand'].matrix
        c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
        pts += [c + ax * t for t in SPEAR_T]
    best, nrm_best = 0.0, None
    for p in pts:
        loc, nrm, idx, dist = tree.find_nearest(p, 0.15)
        if loc is not None and dist > best and (p - loc).dot(nrm) < -0.7 * dist:
            best, nrm_best = dist, nrm.normalized()
    return best, nrm_best


def snapshot(f):
    sc.frame_set(f)
    return {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


def envelope(req, loop):
    """Per-frame offset vectors: each frame's need spread over +-EASE frames with a raised cosine; max by magnitude."""
    n = len(req); outv = [Vector() for _ in range(n)]
    for i, r in enumerate(req):
        if r.length < 1e-6:
            continue
        for k in range(-EASE, EASE + 1):
            j = i + k
            if loop:
                j %= (n - 1)       # last frame duplicates the first
            elif not 0 <= j < n:
                continue
            w = 0.5 * (1 + math.cos(math.pi * k / (EASE + 1)))
            v = r * w
            if v.length > outv[j].length:
                outv[j] = v
    if loop:
        outv[n - 1] = outv[0].copy()
    return outv


for it in items:
    parts = it.split(':'); name, side, what = parts[0], parts[1], parts[2]; loop = 'loop' in parts[3:]
    act = bpy.data.actions[name]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    ARM = [f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand']
    total = [Vector() for _ in range(f0, f1 + 1)]
    for itn in range(ITER):
        set_act(act)
        req, worst = [], (0.0, None)
        for f in range(f0, f1 + 1):
            sc.frame_set(f); d, n = measure(side, what)
            if d > worst[0]:
                worst = (d, f)
            req.append(n * (d + MARGIN) if d > TOL and n is not None else Vector())
        print(f'ELBOWCLEAR {name} {side} {what} pass {itn}: worst {worst[0] * 100:.1f} cm at frame {worst[1]}')
        if worst[0] <= TOL:
            break
        off = envelope(req, loop)
        keys = {}
        for i, f in enumerate(range(f0, f1 + 1)):
            if off[i].length < 1e-5:
                continue
            set_act(act); snap = snapshot(f)
            rig.animation_data.action = None
            for bn, mtx in snap.items():
                rig.pose.bones[bn].matrix_basis = mtx
            bpy.context.view_layer.update()
            old = {bn: rig.pose.bones[bn].rotation_quaternion.copy() for bn in ARM}
            E0 = armik.W(rig, f'B_{side}_Forearm').translation.copy()
            W0 = armik.W(rig, f'B_{side}_Hand').translation.copy()
            ua, fa, hd = ARM
            Ru, Rf, Rh = (armik.W(rig, bn).to_3x3().normalized() for bn in ARM)
            armik.solve(rig, side, W0 + off[i], pole=E0 + off[i] * 2.0)
            # keep only armik's joint positions: rebuild the upper arm and forearm as pure swings of their own
            # rotations (no roll about the bone: armik's elbow-plane roll flips on a near-straight arm), hand kept
            S = armik.W(rig, ua).translation.copy(); E = armik.W(rig, fa).translation.copy()
            T = armik.W(rig, hd).translation.copy()
            armik.set_world(rig, ua, armik.rot_world(armik.W(rig, ua), ((E0 - S).normalized().rotation_difference(
                (E - S).normalized())).to_matrix() @ Ru))
            E1 = armik.W(rig, fa).translation.copy()
            fdir0 = Ru.inverted() @ Rf                                                   # forearm in upper-arm frame
            Rf1 = armik.W(rig, ua).to_3x3().normalized() @ fdir0
            armik.set_world(rig, fa, armik.rot_world(armik.W(rig, fa), Rf1))
            cur = (armik.W(rig, hd).translation - E1).normalized()                      # joint heads, not bone tails
            armik.set_world(rig, fa, armik.rot_world(armik.W(rig, fa), cur.rotation_difference((T - E1).normalized())
                                                     .to_matrix() @ Rf1))
            armik.set_world(rig, hd, armik.rot_world(armik.W(rig, hd), Rh))
            keys[f] = {}
            for bn in ARM:
                q = rig.pose.bones[bn].rotation_quaternion.copy()
                keys[f][bn] = -q if q.dot(old[bn]) < 0 else q      # sign-continuous with the existing keys
            total[i] = total[i] + off[i]
        set_act(act)
        for f, ks in keys.items():
            for bn, q in ks.items():
                pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
                pb.keyframe_insert('rotation_quaternion', frame=f)
    mx = max(total, key=lambda v: v.length)
    print(f'ELBOWCLEAR {name} {side} {what} done: largest wrist offset {mx.length * 100:.1f} cm')
rig.animation_data.action = None
bpy.data.objects.remove(mb, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
