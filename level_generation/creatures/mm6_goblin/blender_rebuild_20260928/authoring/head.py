"""Authored face patch, true orbital/mouth openings, connected skull and ear surfaces."""
import math
import json

import bpy
from mathutils import Vector

from mesh_tools import Mesh, ROOT, curve, front_surface, material, mix, ring


def build_head():
    skin = bpy.data.materials['GB15 Skin blockout']
    mesh = Mesh('GB15 Head and ears', skin)
    levels = [1.443, 1.453, 1.467, 1.480, 1.490, 1.505, 1.520, 1.533, 1.546, 1.553,
              1.565, 1.579, 1.591, 1.603, 1.619, 1.637, 1.653, 1.669, 1.684, 1.695, 1.699]
    widths = [(1.443, .049), (1.467, .063), (1.49, .075), (1.52, .088), (1.553, .094),
              (1.59, .095), (1.619, .093), (1.637, .083), (1.653, .072), (1.669, .054),
              (1.684, .034), (1.695, .017), (1.699, .004)]
    depths = [(1.443, .073), (1.48, .066), (1.53, .079), (1.56, .107), (1.60, .157),
              (1.63, .111), (1.665, .064), (1.695, .013), (1.699, .004)]
    body = bpy.data.objects['GB15 Skin body']
    neck = json.loads(body['gb_neck_ring'])
    bottom = [mesh.vertex(body.data.vertices[i].co, {'neck': 1}) for i in neck]
    rows = []
    for z in levels:
        width = curve(widths, z)
        row = []
        for col in range(21):
            x = (col - 10) / 10 * width
            fallback = .012 - .13 * math.sqrt(max(0, 1 - (x / width) ** 2))
            y = front_surface(x, z, fallback)
            if abs(x) > width * .87:
                y = mix(y, .014, ((abs(x) / width - .87) / .13) ** 2)
            if 1.48 < z < 1.525:
                y = max(y, -.118)
            if 1.533 <= z <= 1.565 and abs(x) < .026:
                y -= .0035 * math.exp(-((z - 1.548) / .021) ** 2) * (1 - abs(x) / .026)
            # The brow and chin are silhouette-scale forms, not details deferred to a map.
            if abs(x) < .085:
                y -= .012 * math.exp(-((abs(x) - .039) / .033) ** 2 - ((z - 1.590) / .017) ** 2)
                y -= .013 * math.exp(-(x / .044) ** 2 - ((z - 1.471) / .017) ** 2)
            row.append(mesh.vertex((x, y, z), {'head': 1}))
        for j in range(1, 12):
            theta = j * math.pi / 12
            row.append(mesh.vertex((width * math.cos(theta), .014 + curve(depths, z) * math.sin(theta), z),
                                   {'head': 1}))
        rows.append(row)
    mesh.bridge(bottom, rows[0], align=True)
    holes = {name: [] for name in ['eye.L', 'eye.R', 'mouth', 'ear.L', 'ear.R', 'nostril.L', 'nostril.R']}
    for r, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(32):
            face = (a[j], a[(j + 1) % 32], b[(j + 1) % 32], b[j])
            region = None
            if 9 <= r < 11:
                if 12 <= j < 17:
                    region = 'eye.L'
                elif 3 <= j < 8:
                    region = 'eye.R'
            if 4 <= r < 6 and 5 <= j < 15:
                region = 'mouth'
            if r == 7 and j in [8, 11]:
                region = 'nostril.L' if j == 11 else 'nostril.R'
            if 9 <= r < 13:
                if 19 <= j < 22:
                    region = 'ear.L'
                elif j in [30, 31, 0]:
                    region = 'ear.R'
            if region:
                holes[region].append(face)
            else:
                mesh.face(face)
    mesh.cap(rows[-1], {'head': 1})
    eye_centers = []
    for side in [1, -1]:
        suffix = '.L' if side == 1 else '.R'
        outer = mesh.hole_loop(holes['eye' + suffix])
        center = Vector((side * .0425, -.089, 1.563))
        eye_centers.append(center)
        angles = []
        for idx in outer:
            p = mesh.vertices[idx]
            angle = math.atan2((p.z - center.z) / .017, (p.x - center.x) / .027)
            angles.append(angle)
            x, z = center.x + .027 * math.cos(angle), center.z + .018 * math.sin(angle)
            y = min(front_surface(x, z, -.104), -.108 + .015 * abs(math.cos(angle)) ** 2)
            mesh.vertices[idx] = Vector((x, y, z))
        previous = outer
        for hx, hz, projection in [(.0245, .013, True), (.0205, .0064, False), (.0198, .0059, False)]:
            row = []
            for angle in angles:
                x = center.x + hx * math.cos(angle)
                z = center.z + hz * math.sin(angle) + side * .0036 * math.cos(angle)
                y = min(front_surface(x, z, -.109), -.109 + .012 * abs(math.cos(angle)) ** 2) if projection else \
                    -.1105 + .008 * abs(math.cos(angle)) ** 2
                if math.sin(angle) > 0 and projection:
                    y -= .004
                row.append(mesh.vertex((x, y, z), {'head': 1}))
            mesh.bridge(previous, row)
            previous = row
        ear(mesh, side, mesh.hole_loop(holes['ear' + suffix]))
        nostril = mesh.hole_loop(holes['nostril' + suffix])
        cx, cz = side * .014, 1.539
        angles = [math.atan2((mesh.vertices[i].z - cz) / .005,
                            (mesh.vertices[i].x - cx) / .006) for i in nostril]
        for index, angle in zip(nostril, angles):
            x, z = cx + .0068 * math.cos(angle), cz + .005 * math.sin(angle)
            mesh.vertices[index] = Vector((x, front_surface(x, z, -.129) - .003, z))
        row = [mesh.vertex((cx + .0043 * math.cos(a), -.124, cz + .0027 * math.sin(a)), {'head': 1})
               for a in angles]
        mesh.bridge(nostril, row)
        mesh.cap(row, {'head': 1})
    outer = mesh.hole_loop(holes['mouth'])
    angles = []
    for idx in outer:
        p = mesh.vertices[idx]
        angle = math.atan2((p.z - 1.503) / .016, p.x / .041)
        angles.append(angle)
        x, z = .046 * math.cos(angle), 1.503 + .018 * math.sin(angle)
        mesh.vertices[idx] = Vector((x, max(-.116, front_surface(x, z, -.104)), z))
    previous = outer
    inner = None
    for width, height, y in [(.0435, .011, -.112), (.040, .0077, -.110), (.038, .007, -.091)]:
        row = []
        for angle in angles:
            x = width * math.cos(angle)
            z = 1.503 + height * math.sin(angle) - .003 * abs(math.cos(angle))
            row.append(mesh.vertex((x, y + .012 * abs(math.cos(angle)) ** 2, z), {'head': 1}))
        mesh.bridge(previous, row)
        previous = row
        inner = row
    obj = mesh.object()
    mouth = Mesh('GB15 Mouth cavity', material('Mouth', (.027, .013, .009), .9))
    loop = [mouth.vertex(mesh.vertices[i], {'head': 1}) for i in inner]
    deep = [mouth.vertex((p.x * .88, p.y + .016, p.z), {'head': 1}) for p in [mesh.vertices[i] for i in inner]]
    mouth.bridge(loop, deep)
    mouth.cap(deep, {'head': 1})
    mouth.object()
    eyes(eye_centers)
    teeth()
    return obj


def ear(mesh, side, opening):
    previous = opening
    for index, (x, y, z, half_width) in enumerate([(.092, .016, 1.584, .034),
                                                  (.113, .030, 1.611, .041),
                                                  (.134, .041, 1.644, .026),
                                                  (.153, .051, 1.670, .010),
                                                  (.165, .058, 1.683, .001)]):
        row = []
        for front in [True, False]:
            for j in (range(7) if front else reversed(range(7))):
                t = (j - 3) / 3
                cup = .006 - .017 * abs(t) ** 1.5 if front else .014
                if index >= 3:
                    cup *= .45
                row.append(mesh.vertex((side * (x - .008 * t), y + cup, z + t * half_width), {'head': 1}))
        mesh.bridge(previous, row, align=index == 0)
        previous = row
    mesh.cap(previous, {'head': 1})


def ellipsoid(mesh, center, scale, segments=16, bands=8):
    rows = []
    for j in range(1, bands):
        theta = math.pi * j / bands
        rows.append([mesh.vertex(Vector(center) + Vector((scale[0] * math.sin(theta) * math.cos(i * math.tau / segments),
                                                         scale[1] * math.sin(theta) * math.sin(i * math.tau / segments),
                                                         scale[2] * math.cos(theta))), {'head': 1})
                     for i in range(segments)])
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    for row, z in [(rows[0], center.z + scale[2]), (rows[-1], center.z - scale[2])]:
        idx = mesh.vertex((center.x, center.y, z), {'head': 1})
        for a, b in zip(row, row[1:] + row[:1]):
            mesh.face((a, b, idx))


def eyes(centers):
    sclera = Mesh('GB15 Eyes', material('Eyes', (.040, .051, .016), .48))
    iris = Mesh('GB15 Irises', material('Amber irises', (.32, .20, .008), .4))
    pupil = Mesh('GB15 Pupils', material('Pupils', (.003, .006, .001), .3))
    for center in centers:
        ellipsoid(sclera, center, (.023, .019, .014), 16, 6)
        for mesh, radius, y in [(iris, .0056, -.1081), (pupil, .0023, -.1085)]:
            row = ring(mesh, (center.x, y, center.z), Vector((1, 0, 0)), Vector((0, 0, 1)),
                       radius, radius, 14, {'head': 1})
            mesh.cap(row, {'head': 1})
    sclera.object()
    iris.object()
    pupil.object()


def teeth():
    mesh = Mesh('GB15 Teeth', material('Ivory', (.31, .26, .15), .60))
    for upper in [True, False]:
        positions = [-.027, -.017, -.006, .0065, .0175, .028] if upper else [-.029, -.016, -.004, .009, .020, .031]
        for index, x in enumerate(positions):
            root_z = 1.513 if upper else 1.493
            length = [.009, .011, .008, .010, .009, .008][index] if upper else \
                [.017, .007, .0055, .0065, .006, .016][index]
            direction = -1 if upper else 1
            width = .0037 if upper else .0034
            base_y = -.111 + .006 * abs(x / .03)
            a = ring(mesh, (x, base_y, root_z), Vector((1, 0, 0)), Vector((0, 1, 0)),
                     width, .0036, 5, {'head': 1})
            b = ring(mesh, (x, base_y - .002, root_z + direction * length * .64),
                     Vector((1, 0, 0)), Vector((0, 1, 0)), width * .63, .0024, 5, {'head': 1})
            mesh.bridge(a, b)
            tip = mesh.vertex((x + .001 * math.sin(index * 2), base_y - .0025, root_z + direction * length),
                              {'head': 1})
            for p, q in zip(b, b[1:] + b[:1]):
                mesh.face((p, q, tip))
            mesh.cap(a, {'head': 1})
    mesh.object()


if __name__ == '__main__':
    build_head()
