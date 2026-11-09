"""Pose the MM6 bones batch's Meshy skeleton (read only: ../../../mm6_dungeons_3d/bones/work/skeleton_tex.blend,
skull_tex.blend, skeleton/skeleton_joints.json; its skelpose.py and blib.py are imported) for the MM7 dressing
batch. A copy of that batch's pose_skeleton.py with this batch's poses and output (work/skeleton_<pose>.blend).
Original notes:
Pose the Meshy skeleton for the cages and write its LODs for the hanging batch's build_cage.py.
Rest mesh: work/skeleton_tex.blend (object 'skeleton' with UVs and the Bone material) when present, else
work/skeleton_uv.blend. Rest joints: skeleton/skeleton_joints.json (metres, front -y, own left +x).
The skeleton is scaled to HEIGHT map units standing, each connected piece (a bone) is bound rigidly to the rig bone
whose capsule is nearest on average (skelpose.py), the trunk is aimed at target points and the limbs are solved with
two-bone IK to the wrist/ankle targets (poles give the elbow/knee side). Targets are in cage map units (cage axis at
x = y = 0, floor of the cage interior about z = 22, front toward -y).
Writes work/skeleton_<pose>.blend (objects Skel_<pose>_L0..L3, material Bone) and work/skeleton_<pose>.json (posed
wrists for the shackles). Usage: blender --background --python pose_skeleton.py -- <hanging|sitting> [--preview]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
sys.path.insert(0, os.path.join(dlib.MM6_BONES, 'scripts'))
import blib  # noqa: E402
import skelpose as sp  # noqa: E402

OUT = dlib.WORK

UNIT = 1 / blib.dl.UNITS_PER_METRE
HEIGHT = 185.0                      # standing height in map units (ribcage about 33 wide, as the sprites paint it)
LOD_TRIS = (2400, 1000, 360, 150)   # LOD0..3 targets for the skeleton with its skull

POSES = {
    # dec19: lying on its back along x, head at +x, seen from the side (-y). The near arm (its left, -y) lies along
    # the side with the hand on the ground by the thigh, the far hand rests on the pelvis, legs straight, toes up.
    # Lying length (heel to crown) about 124 map units, as the sprite (126 x 37 units).
    'lying': {
        'height': 124.0, 'lod_tris': (3900, 1600, 600, 220), 'thicken': 1.4, 'chest_scale': (1.3, 1.5), 'skull_scale': 1.4,
        'skull_tris': (900, 380, 120, 50),
        'hips': (5, 0, 9), 'chest': (21, 0, 11), 'neck': (40, 0, 10),
        'skull': (48, 0, 10), 'head_top': (61, -3, 14), 'head_twist': 70, 'pelvis_twist': -90,
        'wrist_l': (2, -15, 3), 'elbow_pole_l': (0.0, -1.0, 0.2), 'finger_l': (-7, -16, 2),
        'wrist_r': (-1, 6, 18), 'elbow_pole_r': (0.0, 1.0, 0.4), 'finger_r': (-10, 1, 17),
        'ankle_l': (-59, -7, 5), 'knee_pole_l': (0.0, 0.0, 1.0), 'toe_l': (-63, -9, 14),
        'ankle_r': (-58, 7, 5), 'knee_pole_r': (0.0, 0.2, 1.0), 'toe_r': (-62, 9, 13),
    },
}


def load_rest(height):
    source = os.path.join(blib.WORK, 'skeleton_tex.blend')
    if not os.path.exists(source):
        source = os.path.join(blib.WORK, 'skeleton_uv.blend')
    bpy.ops.wm.open_mainfile(filepath=source)
    obj = bpy.data.objects['skeleton']
    meta = json.load(open(os.path.join(blib.HERE, 'skeleton', 'skeleton_joints.json')))
    scale = height * UNIT / meta['height']
    joints = {k: np.array(v) * scale for k, v in meta['joints'].items()}
    for v in obj.data.vertices:
        v.co *= scale
    obj.data.update()
    return obj, joints


def pieces(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    label = np.full(len(bm.verts), -1)
    count = 0
    for v in bm.verts:
        if label[v.index] >= 0:
            continue
        stack = [v]; label[v.index] = count
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                o = e.other_vert(w)
                if label[o.index] < 0:
                    label[o.index] = count; stack.append(o)
        count += 1
    bm.free()
    return label, count


def rigid_weights(points, joints, label, count, height):
    """Per-vertex capsule weights, then each piece wholly to its majority bone (bones are rigid)."""
    w = sp.weights(points, joints, height * UNIT)
    best = np.argmax(w, axis=1)
    out = np.zeros_like(w)
    for piece in range(count):
        mask = label == piece
        votes = np.bincount(best[mask], minlength=w.shape[1])
        out[mask, np.argmax(votes)] = 1.0
    return out


def ik(start, target, a, b, pole):
    """Two-bone IK: elbow/knee position for upper length a and lower length b from start toward target, bending
    toward pole (a direction)."""
    start, target, pole = Vector(start), Vector(target), Vector(pole).normalized()
    d = target - start
    reach = min(d.length, (a + b) * 0.999)
    axis = d.normalized()
    x = (a * a - b * b + reach * reach) / (2 * reach)
    h = math.sqrt(max(a * a - x * x, 0.0))
    side = (pole - axis * pole.dot(axis)).normalized()
    return start + axis * x + side * h, start + axis * reach


def solve(joints, spec):
    """Full target joints (metres) for skelpose.pose from a pose spec (map units)."""
    m = {k: Vector(v) * UNIT for k, v in spec.items() if isinstance(v, tuple) and 'pole' not in k}
    targets = {k: m[k] for k in ('hips', 'chest', 'neck', 'skull', 'head_top')}
    twists = {'head': spec.get('head_twist', 0.0), 'pelvis': spec.get('pelvis_twist', 0.0)}
    transforms, posed = sp.pose(joints, targets, twists=twists)
    rest = {k: Vector(v) for k, v in joints.items()}
    for s in ('l', 'r'):
        for upper, mid, low, end, pole in (('shoulder', 'elbow', 'wrist', 'finger', 'elbow_pole'),
                                           ('hip', 'knee', 'ankle', 'toe', 'knee_pole')):
            start = posed[f'{upper}_{s}']
            a = (rest[f'{mid}_{s}'] - rest[f'{upper}_{s}']).length
            b = (rest[f'{low}_{s}'] - rest[f'{mid}_{s}']).length
            middle, reached = ik(start, m[f'{low}_{s}'], a, b, spec[f'{pole}_{s}'])
            targets[f'{upper}_{s}'] = start
            targets[f'{mid}_{s}'] = middle
            targets[f'{low}_{s}'] = reached
            targets[f'{end}_{s}'] = reached + (m[f'{end}_{s}'] - m[f'{low}_{s}'])
    return sp.pose(joints, targets, twists=twists)


def decimate_pieces(obj, target, minimum):
    """Decimate every loose piece on its own toward a shared ratio, no piece below `minimum` triangles (small bones
    keep a shape instead of collapsing into shards), so the whole lands near `target`."""
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = list(bpy.context.selected_objects)
    counts = np.array([blib.pl.triangles(p) for p in parts], float)
    ratio = 1.0
    for _ in range(40):
        total = np.minimum(counts, np.maximum(minimum, counts * ratio)).sum()
        ratio *= target / max(total, 1)
    for part, n in zip(parts, counts):
        goal = int(min(n, max(minimum, n * ratio)))
        if goal < n:
            for o in bpy.data.objects:
                o.select_set(o is part)
            bpy.context.view_layer.objects.active = part
            mod = part.modifiers.new('D', 'DECIMATE'); mod.ratio = goal / n; mod.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return blib.pl.join(obj.name, parts)


def drop_small(obj, min_vertices):
    label, count = pieces(obj)
    sizes = np.bincount(label, minlength=count)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if sizes[label[v.index]] < min_vertices], context='VERTS')
    bm.to_mesh(obj.data); bm.free()


SKULL_TRIS = (520, 240, 90, 44)
PIECE_MIN = (10, 6, 4, 4)
DROP_BELOW = (0, 0, 60, 110)          # far levels lose finger and toe bones and small vertebrae


def lod(obj, skull, level, name, budget):
    body = blib.duplicate(obj, name)
    if DROP_BELOW[level]:
        drop_small(body, DROP_BELOW[level])
    body = decimate_pieces(body, budget[level] - SKULL_TRIS[level], PIECE_MIN[level])
    parts = [body]
    if skull is not None:
        head = blib.duplicate(skull, name + 'Skull')
        if level >= 2:
            drop_small(head, 200)          # the far skull keeps cranium and jaw, not the separate teeth
        head = decimate_pieces(head, SKULL_TRIS[level], PIECE_MIN[level])
        parts.append(head)
    out = blib.pl.join(name, parts)
    for p in out.data.polygons:
        p.use_smooth = True
    return out


def graft_skull(obj, w, transforms, height):
    """Replace the skeleton's own skull and jaw (the pieces on the head bone) by the Meshy skull asset
    (work/skull_tex.blend), fitted to their rest bounds and moved with the head bone. Returns the posed skull
    object, or None when the asset is missing."""
    path = os.path.join(blib.WORK, 'skull_tex.blend')
    if not os.path.exists(path):
        return None
    head = sp.ORDER.index('head')
    on_head = w[:, head] > 0.5
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = co[on_head].min(0), co[on_head].max(0)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if on_head[v.index]], context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = ['skull']
    skull = dst.objects[0]
    bpy.context.scene.collection.objects.link(skull)
    sc = np.array([v.co[:] for v in skull.data.vertices])
    s_lo, s_hi = sc.min(0), sc.max(0)
    scale = (hi[2] - lo[2]) / (s_hi[2] - s_lo[2])           # match the height (the asset's jaw is closed too)
    scale *= SKULL_SCALE                                     # (added) the MM7 sprites paint bigger skulls
    centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    s_centre = np.array([(s_lo[0] + s_hi[0]) / 2, (s_lo[1] + s_hi[1]) / 2, s_lo[2]])
    rest = (sc - s_centre) * scale + centre
    posed = sp.skin(rest, np.eye(len(sp.ORDER))[[head] * len(rest)], transforms)
    for v, p in zip(skull.data.vertices, posed):
        v.co = p
    skull.data.update()
    return skull, on_head


def proportions(points, w, label, count, joints, spec):
    """Stouter bones for the painted MM7 skeletons (added here): every piece but the skull's is scaled across its
    bone's axis by spec['thicken'] about its own centre line; the ribcage pieces (chest bone) are scaled about the
    spine line by spec['chest_scale'] (lateral, front-back)."""
    thick = spec.get('thicken', 1.0)
    chest = spec.get('chest_scale')
    if thick == 1.0 and not chest:
        return points
    out = points.copy()
    best = np.argmax(w, axis=1)
    for piece in range(count):
        mask = label == piece
        bone = sp.ORDER[best[mask][0]]
        if bone in ('head', 'neck'):
            continue
        head, tail = (np.array(joints[j]) for j in sp.BONES[bone][:2])
        axis = (tail - head) / np.linalg.norm(tail - head)
        P = points[mask]
        if bone == 'chest' and chest:
            q = P - head
            along = q @ axis
            perp = q - along[:, None] * axis
            perp[:, 0] *= chest[0]
            perp[:, 1] *= chest[1]
            out[mask] = head + along[:, None] * axis + perp
            continue
        c = P.mean(0)
        rel = P - c
        along = rel @ axis
        out[mask] = c + along[:, None] * axis + (rel - along[:, None] * axis) * thick
    return out


SKULL_SCALE = 1.0


def main():
    global SKULL_SCALE, SKULL_TRIS
    args = sys.argv[sys.argv.index('--') + 1:]
    name = args[0]
    spec = POSES[name]
    SKULL_SCALE = spec.get('skull_scale', 1.0)
    SKULL_TRIS = spec.get('skull_tris', SKULL_TRIS)
    height = spec.get('height', HEIGHT)
    obj, joints = load_rest(height)
    points = np.array([v.co[:] for v in obj.data.vertices])
    label, count = pieces(obj)
    w = rigid_weights(points, joints, label, count, height)
    points = proportions(points, w, label, count, joints, spec)
    for v, p in zip(obj.data.vertices, points):
        v.co = p
    transforms, posed = solve(joints, spec)
    new = sp.skin(points, w, transforms)
    for v, p in zip(obj.data.vertices, new):
        v.co = p
    obj.data.update()
    report = {k: [round(c / UNIT, 1) for c in v] for k, v in posed.items()}
    lo = new.min(0) / UNIT; hi = new.max(0) / UNIT
    print('POSED', name, 'pieces', count, 'bounds', np.round(lo, 1).tolist(), np.round(hi, 1).tolist())
    for key in ('shoulder_r', 'elbow_r', 'knee_l', 'knee_r', 'wrist_l', 'wrist_r', 'ankle_l', 'ankle_r', 'skull',
                'head_top', 'hips'):
        print('  ', key, report[key], 'target', spec.get(key))
    # The graft needs rest positions: undo the pose on a copy of the points for the head bounds.
    for v, p in zip(obj.data.vertices, points):
        v.co = p
    grafted = graft_skull(obj, w, transforms, height)
    keep = ~grafted[1] if grafted else np.ones(len(points), bool)
    for v, p in zip(obj.data.vertices, new[keep]):
        v.co = p
    obj.data.update()
    skull = grafted[0] if grafted else None
    levels = [lod(obj, skull, k, f'Skel_{name}_L{k}', spec.get('lod_tris', LOD_TRIS)) for k in range(4)]
    print('LODS', [blib.pl.triangles(o) for o in levels], 'skull asset', skull is not None)
    for o in list(bpy.data.objects):
        if o not in levels:
            bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'skeleton_{name}.blend'))
    json.dump(report, open(os.path.join(OUT, f'skeleton_{name}.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
