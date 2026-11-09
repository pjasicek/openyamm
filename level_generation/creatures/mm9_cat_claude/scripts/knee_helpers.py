"""Half-rotation helper bones on the cat's hind legs (Blender module used by build_export.py).

A sitting cat turns its hip, knee and hock by 100 degrees or more from the rest pose. A linear skin blends two matrices, so at
those angles the skin across the joint collapses: the fold becomes a sharp lip and a flap. Each helper sits on the joint and
turns half as far as the child bone, and the skin over the joint moves onto it, so it follows an arc instead of a chord.

  bone Xblegpiv_h  on the hip,  child of Xbackleg,  half of Xblegpiv
  bone Xbleg_h     on the knee, child of Xblegpiv,  half of Xbleg
  bone Xbankle_h   on the ankle, child of Xblegmid, half of Xbankle: the flat tarsus of a sitting cat opens this joint
  (and the same with 01). The hock has no helper: its point is anatomy, and a helper flattened it into a slab.

add() builds the bones and moves the weights: per vertex t = child / (parent + child), widened along the surface, then
parent (1 - 2t), helper (1 - |2t - 1|), child (2t - 1). Back-of-knee and groin skin that MM9's labels left between spine and
shin is sorted first, by two smooth ramps. key() writes the helpers' keys: a pure function of the child's curve, so it adds no motion.
Skin weights stay mirror-symmetric because every step is. MM9's own bones keep their names and keys."""
import bpy
import numpy as np
from mathutils import Quaternion

LEGS = (('Xbackleg', 'Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle'), ('Xbackleg', 'Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01'))
BODY = ('Xbackleg', 'XbackC', 'XbackB', 'XbackA', 'XCENTER')
WIDEN = {'hip': 10, 'knee': 30, 'ankle': 12}
CREASE_DEPTH = 0.006
ALIGN = 0.5


def helpers():
    for pel, hip, knee, hock, ankle in LEGS:
        yield hip + '_h', pel, hip
        yield knee + '_h', hip, knee
        yield ankle + '_h', hock, ankle


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def add_bones(rig):
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    for name, parent, child in helpers():
        c = eb[child]
        b = eb.new(name)
        b.head, b.tail, b.roll = c.head.copy(), c.tail.copy(), c.roll
        b.parent = eb[parent]
        b.use_connect = False
        b.use_deform = True
    bpy.ops.object.mode_set(mode='OBJECT')
    for name, _, _ in helpers():
        rig.pose.bones[name].rotation_mode = 'QUATERNION'


def weights(body):
    n = len(body.data.vertices)
    idx = {g.name: g.index for g in body.vertex_groups}
    W = np.zeros((n, len(idx)))
    for v in body.data.vertices:
        for ge in v.groups:
            W[v.index, ge.group] = ge.weight
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return W, idx


def diffuse(values, free, edges, iters):
    v = values.copy()
    n = len(v)
    for _ in range(iters):
        s = np.zeros(n)
        c = np.zeros(n)
        np.add.at(s, edges[:, 0], v[edges[:, 1]])
        np.add.at(s, edges[:, 1], v[edges[:, 0]])
        np.add.at(c, edges[:, 0], 1)
        np.add.at(c, edges[:, 1], 1)
        new = s / np.maximum(c, 1)
        v[free] = new[free]
    return v


def crease(t, P, joint, concave):
    """On the concave side of a fold a blended skin turns inside out; a sharp split lets each side stay rigid and press against
    the other, as a real crease does. The convex side keeps its smooth blend."""
    depth = (P - np.array(joint[:])) @ np.array(concave)
    s = ss(0.0, CREASE_DEPTH, depth)
    return t * (1 - s) + ss(0.35, 0.65, t) * s


def split(W, parents, child, helper, edges, iters, X=None, pivot=None, concave=None):
    """Moves the skin between parents and child onto the helper. parents: column list, child and helper: columns."""
    P = W[:, parents].sum(1)
    C = W[:, child]
    M = P + C
    joint = (P > 0.02) & (C > 0.02)
    t = np.where(M > 1e-6, C / np.maximum(M, 1e-6), 0.0)
    near = diffuse(joint.astype(float), np.ones(len(t), bool), edges, 3) > 0.02
    free = near & (M > 0.5)
    t = diffuse(t, free, edges, iters)
    if pivot is not None:
        t = crease(t, X, pivot, concave)
    h = M * (1 - np.abs(2 * t - 1))
    p = M * np.maximum(1 - 2 * t, 0)
    c = M * np.maximum(2 * t - 1, 0)
    scale = np.where(P > 1e-9, p / np.maximum(P, 1e-9), 0.0)
    for k in parents:
        W[:, k] *= scale
    # a vertex with no parent weight left in P but a share of p keeps it on the first parent
    W[:, parents[0]] += np.where(P <= 1e-9, p, 0.0)
    W[:, child] = c
    W[:, helper] = h


def add(rig, body):
    add_bones(rig)
    for name, _, _ in helpers():
        if name not in body.vertex_groups:
            body.vertex_groups.new(name=name)
    W, idx = weights(body)
    edges = np.array([e.vertices[:] for e in body.data.edges])
    P = np.array([v.co[:] for v in body.data.vertices])
    # back of the knee and groin, both as smooth ramps: skin off the midline follows the leg instead of the pelvis, which
    # pitches away from it when the cat sits; skin at the midline follows the body instead of the shin
    kn = rig.data.bones['Xbleg'].head_local
    ax = np.abs(P[:, 0])
    leg_side = ss(0.012, 0.024, ax)
    below = 1 - ss(kn.z - 0.005, kn.z + 0.03, P[:, 2])
    behind = ss(kn.y - 0.02, kn.y, P[:, 1])
    to_leg = leg_side * below * behind
    to_body = (1 - leg_side) * ss(kn.z - 0.012, kn.z, P[:, 2]) * ss(kn.y - 0.012, kn.y, P[:, 1])
    spine = idx['XbackB']
    body_cols_ = [idx[b] for b in BODY if b in idx]
    for _, hip, knee, hock, _ankle in LEGS:
        side = (P[:, 0] > 0) if rig.data.bones[hip].head_local.x > 0 else (P[:, 0] <= 0)
        for c in body_cols_:
            m = W[:, c] * to_leg * side
            W[:, c] -= m
            W[:, idx[hip]] += m
        for b in (knee, hock):
            m = W[:, idx[b]] * to_body * side
            W[:, idx[b]] -= m
            W[:, spine] += m
    moved = int(((to_leg > 0.01) | (to_body > 0.01)).sum())
    body_cols = [idx[b] for b in BODY if b in idx]
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    for pel, hip, knee, hock, ankle in LEGS:
        split(W, body_cols, idx[hip], idx[hip + '_h'], edges, WIDEN['hip'])
        split(W, [idx[hip]], idx[knee], idx[knee + '_h'], edges, WIDEN['knee'], P, rig.data.bones[knee].head_local, (0, 1, 0))
        # the hock keeps its point, no helper: only the concave side of the fold is sharpened
        M = W[:, idx[knee]] + W[:, idx[hock]]
        t = np.where(M > 1e-6, W[:, idx[hock]] / np.maximum(M, 1e-6), 0.0)
        t = crease(t, P, rig.data.bones[hock].head_local, (0, -1, 0))
        W[:, idx[hock]] = M * t
        W[:, idx[knee]] = M * (1 - t)
        split(W, [idx[hock]], idx[ankle], idx[ankle + '_h'], edges, WIDEN['ankle'])
    for g in body.vertex_groups:
        col = W[:, g.index]
        g.remove(list(range(len(col))))
        for i in np.nonzero(col > 1e-3)[0]:
            g.add([int(i)], float(col[i]), 'REPLACE')
    return {'groin_vertices': moved, 'helpers': [h for h, _, _ in helpers()]}


def key(rig, actions):
    sc = bpy.context.scene
    for act in actions:
        rig.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        rows = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            row = []
            for name, _, child in helpers():
                c = rig.pose.bones[child]
                row.append((name, Quaternion().slerp(c.rotation_quaternion.normalized(), ALIGN), c.location.copy()))
            rows.append((f, row))
        for f, row in rows:
            for name, q, l in row:
                pb = rig.pose.bones[name]
                pb.rotation_quaternion, pb.location = q, l
                pb.keyframe_insert('rotation_quaternion', frame=f)
                pb.keyframe_insert('location', frame=f)
