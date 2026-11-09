"""New connected torso/limb topology, with explicit branching hand and foot surfaces."""
import math
import json
from pathlib import Path

import bpy
from mathutils import Vector

from mesh_tools import Mesh, ROOT, blend_weights, curve, front_surface, material, mix, ring

LANDMARKS = {}


def torso_weights(z):
    if z < 1.00:
        return {'pelvis': 1}
    if z < 1.15:
        return blend_weights({'pelvis': 1}, {'spine': 1}, (z - 1.00) / .15)
    if z < 1.29:
        return blend_weights({'spine': 1}, {'chest': 1}, (z - 1.15) / .14)
    return blend_weights({'chest': 1}, {'neck': 1}, max(0, min(1, (z - 1.34) / .08)))


def body():
    skin = material('Skin blockout', (.205, .245, .078), .62)
    mesh = Mesh('GB15 Skin body', skin)
    specs = [(.80, .146, .100), (.85, .150, .109), (.91, .151, .111), (.97, .143, .100),
             (1.02, .124, .085), (1.045, .124, .086), (1.07, .126, .087), (1.095, .134, .090),
             (1.12, .143, .094), (1.145, .155, .101), (1.17, .166, .111), (1.195, .178, .115),
             (1.21, .184, .114), (1.235, .190, .115), (1.25, .193, .116), (1.27, .193, .115),
             (1.29, .190, .111), (1.33, .174, .100),
             (1.37, .125, .083), (1.405, .055, .054), (1.425, .049, .050)]
    rows = []
    for z, rx, ry in specs:
        row = []
        for j in range(32):
            angle = j * math.tau / 32
            point = Vector((rx * math.sin(angle), .046 - ry * math.cos(angle), z))
            if z > 1.37:
                point.y -= .039 * min(1, (z - 1.37) / .055)
            if 1.015 <= z <= 1.215:
                direction = Vector((math.sin(angle), -math.cos(angle), 0))
                hit = bpy.gb15_guide_bvh.ray_cast(Vector((0, .046, z)) + direction * .29, -direction, .27)
                if hit[0] is not None and abs(hit[0].x) < .21:
                    point = point.lerp(hit[0], .88)
            if 1.22 <= z <= 1.33 and math.cos(angle) > 0:
                point.y -= .023 * math.exp(-((abs(point.x) - .098) / .062) ** 2 -
                                          ((z - 1.264) / .047) ** 2) * math.cos(angle)
            weights = torso_weights(z)
            if 1.21 <= z <= 1.37 and abs(point.x) > .13:
                blend = min(.4, (abs(point.x) - .13) / .12)
                weights = blend_weights(weights, {'upper_arm.L' if point.x > 0 else 'upper_arm.R': 1}, blend)
            row.append(mesh.vertex(point, weights))
        rows.append(row)
    holes = {1: [], -1: []}
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(32):
            quad = (a[j], a[(j + 1) % 32], b[(j + 1) % 32], b[j])
            side = 1 if 6 <= j < 10 else -1 if 22 <= j < 26 else 0
            if side and 1.209 <= specs[i][0] < 1.37:
                holes[side].append(quad)
            else:
                mesh.face(quad)
    LANDMARKS.update({'pelvis': [0, .05, .92], 'spine': [0, .045, 1.10],
                      'chest': [0, .047, 1.27], 'neck': [0, .042, 1.39], 'head': [0, .035, 1.49]})
    for side in [1, -1]:
        arm(mesh, side, mesh.hole_loop(holes[side]))
    # Shared crotch seam branches the pelvic surface into two actual leg openings.
    seam = [mesh.vertex((0, y, .765), {'pelvis': 1}) for y in [.095, .045, -.005]]
    pelvic = rows[0]
    for side in [1, -1]:
        opening = pelvic[:17] + seam if side == 1 else pelvic[16:] + pelvic[:1] + list(reversed(seam))
        leg(mesh, side, opening)
    obj = mesh.object()
    obj['gb_neck_ring'] = json.dumps(rows[-1])
    (ROOT / 'authoring/landmarks.json').write_text(json.dumps(LANDMARKS, indent=2) + '\n')
    return obj


def arm(mesh, side, opening):
    suffix = '.L' if side == 1 else '.R'
    shoulder = Vector((side * .210, .048, 1.315))
    elbow = Vector((side * .330, .026, 1.115))
    wrist = Vector((side * .441, -.023, .932))
    hand_end = wrist + Vector((side * .028, -.003, -.076))
    for key, point in [('shoulder', shoulder), ('elbow', elbow), ('wrist', wrist), ('hand_end', hand_end)]:
        LANDMARKS[key + suffix] = list(point)
    path = [(shoulder, .077, .069, {'upper_arm' + suffix: .65, 'chest': .35}),
            (shoulder.lerp(elbow, .16), .073, .068, {'upper_arm' + suffix: 1}),
            (shoulder.lerp(elbow, .37), .064, .064, {'upper_arm' + suffix: 1}),
            (shoulder.lerp(elbow, .67), .052, .051, {'upper_arm' + suffix: 1}),
            (shoulder.lerp(elbow, .90), .042, .044, {'upper_arm' + suffix: .8, 'forearm' + suffix: .2}),
            (elbow, .044, .042, {'upper_arm' + suffix: .5, 'forearm' + suffix: .5}),
            (elbow.lerp(wrist, .12), .046, .044, {'upper_arm' + suffix: .2, 'forearm' + suffix: .8}),
            (elbow.lerp(wrist, .34), .046, .043, {'forearm' + suffix: 1}),
            (elbow.lerp(wrist, .61), .036, .037, {'forearm' + suffix: 1}),
            (elbow.lerp(wrist, .86), .025, .027, {'forearm' + suffix: .7, 'hand' + suffix: .3}),
            (wrist, .024, .023, {'hand' + suffix: 1})]
    direction = (wrist - shoulder).normalized()
    u = Vector((side * -direction.z, 0, abs(direction.x))).normalized()
    v = Vector((0, -1, 0))
    previous = opening
    for index, (center, ru, rv, weights) in enumerate(path):
        row = ring(mesh, center, u, v, ru, rv, 16, weights)
        if index in [2, 3]:
            for idx in row:
                point = mesh.vertices[idx]
                radial = (point - center).normalized()
                hit = bpy.gb15_guide_bvh.ray_cast(center + radial * .14, -radial, .16)
                if hit[0] is not None:
                    mesh.vertices[idx] = point.lerp(hit[0], .65)
        previous = mesh.bridge(previous, row, align=index == 0)
    hand(mesh, side, previous, wrist, (hand_end - wrist).normalized(), u, v)


def branch_digits(mesh, row, center, u, v, direction, widths, lengths, prefix, weights, nails=False):
    top = row[:9]
    bottom = list(reversed(row[9:]))
    for digit in range(4):
        root = top[digit * 2:digit * 2 + 3] + list(reversed(bottom[digit * 2:digit * 2 + 3]))
        c = sum((mesh.vertices[i] for i in root), Vector()) / 6
        length = lengths[digit]
        axis = (direction + u * ((digit - 1.5) * .06)).normalized()
        points = [c, c + axis * (length * .43), c + axis * (length * .76) + v * .004,
                  c + axis * length + v * .010]
        name = prefix + str(digit)
        LANDMARKS[name] = [list(p) for p in points]
        previous = root
        stations = [(0.10, 1.0), (.34, .96), (.43, 1.00), (.52, .9), (.70, .79),
                    (.76, .82), (.84, .69), (1.0, .36)]
        for t, radius_factor in stations:
            z = c + axis * (length * t) + v * (.01 * t * t)
            if nails:
                weight = weights
            else:
                a = name + '.01'
                b = name + '.02'
                c_name = name + '.03'
                if t < .34:
                    weight = {a: 1}
                elif t < .52:
                    weight = blend_weights({a: 1}, {b: 1}, (t - .34) / .18)
                elif t < .69:
                    weight = {b: 1}
                elif t < .84:
                    weight = blend_weights({b: 1}, {c_name: 1}, (t - .69) / .15)
                else:
                    weight = {c_name: 1}
            row = ring(mesh, z, u, v, widths[digit] * radius_factor,
                       widths[digit] * .8 * radius_factor, 6, weight, phase=math.pi / 6)
            previous = mesh.bridge(previous, row, align=t == .10)
        mesh.cap(previous, weight)


def hand(mesh, side, wrist_ring, wrist, direction, u, v):
    suffix = '.L' if side == 1 else '.R'
    rows, thumb_faces = [], []
    for t, width, depth in [(0, .025, .022), (.025, .035, .019), (.052, .039, .018), (.076, .039, .015)]:
        c = wrist + direction * t
        weights = {'hand' + suffix: 1}
        row = []
        for face_side in [1, -1]:
            sequence = range(9) if face_side == 1 else reversed(range(9))
            for j in sequence:
                x = (j - 4) / 4
                fullness = .58 + .42 * math.sqrt(max(0, 1 - x * x))
                point = c + u * (x * width) + v * (face_side * depth * fullness)
                row.append(mesh.vertex(point, weights))
        rows.append(row)
    mesh.bridge(wrist_ring, rows[0], align=True)
    # The thumb grows out of a real side opening across the thenar pad.
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(18):
            face = (a[j], a[(j + 1) % 18], b[(j + 1) % 18], b[j])
            if i < 2 and j in [16, 17, 0]:
                thumb_faces.append(face)
            else:
                mesh.face(face)
    branch_digits(mesh, rows[-1], wrist + direction * .076, u, v, direction,
                  [.010, .0105, .010, .0085], [.082, .096, .089, .073], 'digit' + suffix + '.',
                  {'hand' + suffix: 1})
    root = mesh.hole_loop(thumb_faces)
    c = wrist + direction * .031 - u * .028
    path = [c, c - u * .039 + direction * .020 + v * .007,
            c - u * .044 + direction * .051 + v * .012,
            c - u * .034 + direction * .071 + v * .024]
    LANDMARKS['thumb' + suffix] = [list(p) for p in path]
    prev = root
    for segment in range(3):
        a, b = path[segment:segment + 2]
        axis = (b - a).normalized()
        cross = axis.cross(v).normalized()
        for step in ([.35, .75, 1.] if segment == 0 else [.35, .75, 1.]):
            radius = mix(.016, .007, (segment + step) / 3)
            w = {'thumb' + suffix + '.' + str(segment + 1).zfill(2): 1}
            if segment == 0 and step < 1:
                blend = min(1, step / .85)
                w = {'hand' + suffix: 1 - blend, 'thumb' + suffix + '.01': blend}
            if step > .75 and segment < 2:
                w = blend_weights(w, {'thumb' + suffix + '.' + str(segment + 2).zfill(2): 1}, .25)
            row = ring(mesh, a.lerp(b, step), cross, v, radius, radius * .85, 8, w)
            prev = mesh.bridge(prev, row, align=True)
    mesh.cap(prev, w)


def leg(mesh, side, opening):
    suffix = '.L' if side == 1 else '.R'
    hip = Vector((side * .088, .050, .850))
    knee = Vector((side * .115, .047, .505))
    ankle = Vector((side * .142, .089, .120))
    for key, point in [('hip', hip), ('knee', knee), ('ankle', ankle)]:
        LANDMARKS[key + suffix] = list(point)
    specs = [(.78, .078, .089), (.73, .080, .091), (.66, .074, .085), (.59, .065, .072),
             (.545, .056, .060), (.52, .051, .054), (.50, .050, .050), (.477, .048, .052),
             (.445, .055, .056), (.39, .059, .060), (.32, .053, .055), (.24, .043, .046),
             (.165, .037, .040), (.12, .037, .037)]
    previous = opening
    for index, (z, rx, ry) in enumerate(specs):
        center = hip.lerp(knee, (hip.z - z) / (hip.z - knee.z)) if z >= knee.z else \
            knee.lerp(ankle, (knee.z - z) / (knee.z - ankle.z))
        if z > .55:
            weights = {'thigh' + suffix: 1}
        elif z >= .46:
            weights = blend_weights({'thigh' + suffix: 1}, {'shin' + suffix: 1}, (.55 - z) / .09)
        elif z > .165:
            weights = {'shin' + suffix: 1}
        else:
            weights = blend_weights({'shin' + suffix: 1}, {'foot' + suffix: 1}, (.165 - z) / .045)
        row = ring(mesh, center, Vector((1, 0, 0)), Vector((0, -1, 0)), rx, ry, 20, weights)
        if .55 < z < .74:
            for idx in row:
                radial = (mesh.vertices[idx] - center).normalized()
                hit = bpy.gb15_guide_bvh.ray_cast(center + radial * .13, -radial, .14)
                if hit[0] is not None:
                    mesh.vertices[idx] = mesh.vertices[idx].lerp(hit[0], .7)
        previous = mesh.bridge(previous, row, align=index == 0)
    foot(mesh, side, previous, ankle)


def foot(mesh, side, ankle_ring, ankle):
    suffix = '.L' if side == 1 else '.R'
    u, v, direction = Vector((side, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))
    weights = {'foot' + suffix: 1}
    rows = []
    for y, width, height in [(.145, .030, .060), (.12, .042, .085), (.088, .047, .095),
                              (.052, .048, .080), (.01, .055, .064), (-.04, .062, .053),
                              (-.090, .064, .044)]:
        row = []
        for upper in [True, False]:
            sequence = range(9) if upper else reversed(range(9))
            for j in sequence:
                x = (j - 4) / 4
                z = .009 + (height - .009) * (.65 + .35 * math.sqrt(max(0, 1 - x * x))) if upper else .009
                row.append(mesh.vertex((ankle.x + side * x * width, y, z), weights))
        rows.append(row)
    removed = []
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(18):
            face = (a[j], a[(j + 1) % 18], b[(j + 1) % 18], b[j])
            if 1 <= i < 3 and 1 <= j < 7:
                removed.append(face)
            else:
                mesh.face(face)
    mesh.cap(rows[0], weights)
    hole = mesh.hole_loop(removed)
    mesh.bridge(ankle_ring, hole, align=True)
    branch_digits(mesh, rows[-1], Vector((ankle.x, -.09, .03)), u, v, direction,
                  [.018, .017, .015, .013], [.085, .082, .070, .052], 'toe' + suffix + '.', weights, nails=True)
    LANDMARKS['toe_end' + suffix] = [ankle.x, -.166, .027]


if __name__ == '__main__':
    body()
