"""Elf warrior statue `dec01` (Murmurwoods out07; directional sprite dec01a0-a4) -> work/elfstatue_export.glb.

The project's MM6 fighter (assets_source/worlds/mm6/models/mm6_fgt.glb, read only: a slim male in leather armour
with shoulder pads and high boots) posed with world-space bone operations (MM6 props corpse_pose.py) and two-bone IK
as all five sprite views show it: feet apart, knees a little bent, both hands on a long two-handed sword at the
right hip, the blade raised past the head to his right and a little forward, head level. The pose is baked static;
the hair is pressed onto the skull (the statue is bald) and pointed elf ears are added. The sword is procedural:
a diamond-section blade, a straight guard, a wrapped grip and a round pommel. Texture: elfstone (the fighter's atlas
turned to weathered grey-green stone, its armour detail kept in the blended normal map) and elfsword (mossy stone).
Usage: blender --background --python build_elfstatue.py -- [--preview]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl, cp = ml.pl, ml.cp
SOURCE = os.path.join(ml.REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_fgt.glb')
BONES = {'Spine': 'B_Spine', 'Spine2': 'B_Spine2', 'Neck': 'B_Neck', 'Head': 'B_Head',
         'LeftUpLeg': 'B_L_Thigh', 'LeftLeg': 'B_L_Calf', 'LeftFoot': 'B_L_Foot',
         'RightUpLeg': 'B_R_Thigh', 'RightLeg': 'B_R_Calf', 'RightFoot': 'B_R_Foot',
         'LeftArm': 'B_L_UpperArm', 'LeftForeArm': 'B_L_Forearm', 'LeftHand': 'B_L_Hand',
         'RightArm': 'B_R_UpperArm', 'RightForeArm': 'B_R_Forearm', 'RightHand': 'B_R_Hand'}


def B(name):
    return BONES[name]


V = Vector
SWORD_DIR = V((-0.42, -0.12, 1.0)).normalized()      # blade direction: up, to his right (-x), a little forward
GRIP = V((-0.15, -0.23, 0.98))                       # lower hand on the grip, at his right hip in front
BLADE = 1.05                                         # blade length (m) from the guard
POSE = [
    ('aim', B('Spine'), (0.0, -0.08, 1.0), 1.0),
    ('aim', B('Spine2'), (0.03, -0.05, 1.0), 1.0),
    ('aim', B('Neck'), (0.0, -0.05, 1.0), 1.0),
    ('aim', B('Head'), (0.0, -0.12, 1.0), 1.0),
    ('aim', B('LeftUpLeg'), (0.24, -0.15, -1.0), 1.0),
    ('aim', B('LeftLeg'), (0.12, 0.14, -1.0), 1.0),
    ('aim', B('LeftFoot'), (0.15, -1.0, -0.45), 1.0),
    ('aim', B('RightUpLeg'), (-0.24, -0.02, -1.0), 1.0),
    ('aim', B('RightLeg'), (-0.12, 0.18, -1.0), 1.0),
    ('aim', B('RightFoot'), (-0.15, -1.0, -0.45), 1.0),
]
# arms by two-bone IK: (upper, lower, hand, wrist target, elbow pole direction)
ARMS = [('RightArm', 'RightForeArm', 'RightHand', GRIP + V((0.02, 0.05, 0.0)), V((-1.0, 0.4, -0.4))),
        ('LeftArm', 'LeftForeArm', 'LeftHand', GRIP + SWORD_DIR * 0.1 + V((0.06, 0.05, 0.0)), V((1.0, 0.3, -0.5)))]
LEVELS = [(5700, 140), (2300, 70), (850, 30)]
SKULL = (0.095, 0.098)        # skull centre above the head joint, skull radius (m)         # body, sword triangles


def world(arm, name, end='head'):
    return arm.matrix_world @ getattr(arm.pose.bones[B(name)], end)


def solve_arms(arm):
    for upper, lower, hand, target, pole in ARMS:
        a = (world(arm, upper, 'tail') - world(arm, upper)).length
        b = (world(arm, hand) - world(arm, lower)).length
        start = world(arm, upper)
        d = target - start
        reach = min(d.length, (a + b) * 0.999)
        axis = d.normalized()
        x = (a * a - b * b + reach * reach) / (2 * reach)
        h = math.sqrt(max(a * a - x * x, 0.0))
        side = (pole - axis * pole.dot(axis)).normalized()
        cp.pose(arm, [('aim', B(upper), (start + axis * x + side * h) - start, 1.0)])
        cp.pose(arm, [('aim', B(lower), start + axis * reach - world(arm, lower), 1.0, B(hand))])
        cp.pose(arm, [('aim', B(hand), GRIP + SWORD_DIR * 0.05 - world(arm, hand) + V((0, -0.04, 0)), 1.0)])


def shave(obj, strongest, head, top):
    """Press the hair onto the skull: Head-bone vertices above the ears outside a skull sphere move onto it."""
    up = (top - head).normalized()
    centre = head + up * SKULL[0] + V((0, -0.012, 0))       # the head bone is a short stub at the neck's top
    radius = SKULL[1]
    for v, bone in zip(obj.data.vertices, strongest):
        if bone == 'B_Head' and (v.co - centre).dot(up) > -0.01:
            d = v.co - centre
            if d.length > radius:
                v.co = centre + d.normalized() * (radius + (d.length - radius) * 0.15)
    obj.data.update()
    return centre, radius


def fists(obj, strongest):
    """Both hands close round the grip: finger and thumb vertices are pulled toward the sword's axis (the T-pose
    fingers would splay out of the grip)."""
    g = GRIP + SWORD_DIR * 0.05
    for v, bone in zip(obj.data.vertices, strongest):
        if 'Finger' in bone:
            p = v.co
            t = (p - g).dot(SWORD_DIR)
            axis_point = g + SWORD_DIR * t
            d = p - axis_point
            if d.length > 0.03:
                v.co = axis_point + d.normalized() * (0.03 + (d.length - 0.03) * 0.25)
    obj.data.update()


def bulk(obj):
    """The sprite's armoured elf is broader than the slim fighter: the chest, shoulder pads and arms widen
    (x 1.2, y 1.1 about the body's axis), fading in from the hips to the chest; the legs widen a little (x 1.08)."""
    for v in obj.data.vertices:
        t = min(1.0, max(0.0, (v.co.z - 0.85) / 0.35))
        v.co.x *= 1.08 + 0.12 * t
        v.co.y = -0.02 + (v.co.y + 0.02) * (1.0 + 0.1 * t)
    obj.data.update()


def ears(centre, radius, mat):
    parts = []
    for side in (1, -1):
        base = centre + V((side * radius * 0.8, 0.0, -radius * 0.3))
        tip = base + V((side * 0.8, 0.3, 0.6)).normalized() * radius * 0.85
        parts.append(pl.tube(f'Ear{side}', base, tip, radius * 0.26, radius * 0.03, 6, mat, caps=True))
    for p in parts:
        p.data.transform(Matrix.Identity(4))
        for v in p.data.vertices:                     # flatten each ear front to back
            v.co.y = centre.y + 0.01 + (v.co.y - centre.y - 0.01) * 0.45
    return parts


def sword(mat, level):
    g = GRIP + SWORD_DIR * 0.05
    guard_at = g + SWORD_DIR * 0.16
    side = SWORD_DIR.cross(V((0, 1, 0))).normalized()          # the blade's flat faces the front
    flat = SWORD_DIR.cross(side).normalized()
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    steps = (6, 3, 2)[level]
    rows = []
    for i in range(steps + 1):
        t = i / steps
        w = 0.033 * (1 - 0.45 * t) if i < steps else 0.0
        c = guard_at + SWORD_DIR * BLADE * t
        rows.append([bm.verts.new(c + side * w), bm.verts.new(c + flat * 0.011 * (1 - t)),
                     bm.verts.new(c - side * w), bm.verts.new(c - flat * 0.011 * (1 - t))])
    for i in range(steps):
        for j in range(4):
            q = [rows[i][j], rows[i][(j + 1) % 4], rows[i + 1][(j + 1) % 4], rows[i + 1][j]]
            if i == steps - 1:
                q = q[:3]
            f = bm.faces.new(q)
            for loop in f.loops:
                p = loop.vert.co - guard_at
                loop[uv].uv = (0.5 + p.dot(side) * 2, p.dot(SWORD_DIR) * 0.8)
    bmesh.ops.contextual_create(bm, geom=rows[0])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    blade = pl.to_object('Blade', bm, mat, smooth=False)
    guard = pl.tube('Guard', guard_at - side * 0.14, guard_at + side * 0.14, 0.02, 0.02, (6, 4, 4)[level], mat)
    grip = pl.tube('Grip', g - SWORD_DIR * 0.13, guard_at, 0.018, 0.018, (6, 4, 4)[level], mat)
    parts = [blade, guard, grip]
    if level < 2:
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.03)
        bmesh.ops.translate(bm, verts=bm.verts, vec=g - SWORD_DIR * 0.16)
        parts.append(pl.to_object('Pommel', bm, mat))
    out = pl.join('Sword', parts)
    ml.box_uv(out, 0.4)
    return out


def main():
    pl.reset()
    stone = ml.material('Stone', 'elfstone', extras={'openyamm_specular': 0.3})
    blade_mat = ml.material('Blade', 'elfsword', extras={'openyamm_specular': 0.3})
    arm, body = cp.load(SOURCE)
    cp.pose(arm, POSE)
    solve_arms(arm)
    head, top = world(arm, 'Head'), world(arm, 'Head', 'tail')
    static = cp.bake(arm, body, 'Body')
    strongest = cp.strongest_bone(static)
    for o in (arm, body):
        bpy.data.objects.remove(o)
    static.vertex_groups.clear()
    centre, radius = shave(static, strongest, head, top)
    fists(static, strongest)
    bulk(static)
    static.data.materials.clear(); static.data.materials.append(stone)
    ear_parts = ears(centre, radius, stone)
    for e in ear_parts:
        ml.box_uv(e, 0.3)                              # (the stone atlas's median texels: any patch reads as stone)
        for loop in e.data.uv_layers[0].data:
            loop.uv = (0.25 + loop.uv[0] * 0.02, 0.5 + loop.uv[1] * 0.02)
    body = pl.join('Body', [static] + ear_parts)
    lo, hi = pl.bounds([body])
    print('POSED body tris', pl.triangles(body), 'size', [round(v, 3) for v in hi - lo])
    if '--preview' in sys.argv:
        sw = sword(blade_mat, 0)
        pl.setup_render((512, 768))
        out = os.path.join(ml.HERE, 'review', 'elfstatue')
        for tag, view in (('front', (0, 5)), ('tq', (40, 5)), ('side', (90, 5)), ('back', (180, 5))):
            pl.render_views([body, sw], out, 'pose_' + tag, views=(view,))
        return
    body.name = 'BodySrc'
    levels = []
    for k, (nb, ns) in enumerate(LEVELS):
        name = 'Elfstatue' if k == 0 else f'Elfstatue_LOD{k}'
        b = ml.duplicate(body, name + 'B'); pl.decimate_to(b, nb)
        sw = sword(blade_mat, k)
        lod = pl.join(name, [b, sw])
        ml.smooth(lod)
        ml.colour(lod, distance=0.15, strength=0.95, power=1.7)
        levels.append(lod)
    bpy.data.objects.remove(body)
    # origin under the feet (the base centre on the ground), not under the bounds with the sword
    feet = np.array([v.co[:] for v in levels[0].data.vertices])
    low = feet[feet[:, 2] < feet[:, 2].min() + 0.05]
    offset = V((-low[:, 0].mean(), -low[:, 1].mean(), -feet[:, 2].min()))
    for o in levels:
        o.data.transform(Matrix.Translation(offset))
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'elfstatue')


main()
