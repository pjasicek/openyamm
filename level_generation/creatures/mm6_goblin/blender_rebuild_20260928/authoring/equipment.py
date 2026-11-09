"""Separate fitted equipment; only silhouette and construction detail consume geometry."""
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from mesh_tools import Mesh, ROOT, material, mix, ring


def materials():
    return {'iron': material('Worn iron blockout', (.075, .088, .095), .56, .8),
            'edge': material('Steel edges', (.17, .18, .16), .43, .8),
            'leather': material('Leather blockout', (.16, .073, .027), .74),
            'brass': material('Muted brass', (.40, .27, .085), .42, .8),
            'horn': material('Claws', (.27, .23, .12), .53)}


def shell(mesh, grid, weights, thickness, inward):
    outer = [[mesh.vertex(p, weights) for p in row] for row in grid]
    inner = [[mesh.vertex(p + inward(p) * thickness, weights) for p in row] for row in grid]
    for surface in [outer, inner]:
        for a, b in zip(surface, surface[1:]):
            for j in range(len(a) - 1):
                mesh.face((a[j], a[j + 1], b[j + 1], b[j]))
    outline = outer[0] + [r[-1] for r in outer[1:]] + list(reversed(outer[-1][:-1])) + \
        [r[0] for r in reversed(outer[1:-1])]
    inner_outline = inner[0] + [r[-1] for r in inner[1:]] + list(reversed(inner[-1][:-1])) + \
        [r[0] for r in reversed(inner[1:-1])]
    mesh.bridge(outline, inner_outline)


def spike(mesh, start, direction, radius, length, weights):
    direction = Vector(direction).normalized()
    u = direction.cross(Vector((0, 1, 0))).normalized()
    if u.length < .1:
        u = direction.cross(Vector((1, 0, 0))).normalized()
    v = direction.cross(u).normalized()
    a = ring(mesh, start, u, v, radius, radius, 6, weights)
    b = ring(mesh, Vector(start) + direction * length * .3, u, v, radius * .64, radius * .64, 6, weights)
    mesh.bridge(a, b)
    tip = mesh.vertex(Vector(start) + direction * length, weights)
    for p, q in zip(b, b[1:] + b[:1]):
        mesh.face((p, q, tip))
    mesh.cap(a, weights)


def plate_patch(name, outline, center, mat, weight, back=False):
    mesh = Mesh(name, mat)
    rows = []
    for factor in [1, .89, .65, .35, .06]:
        row = []
        for x, z in outline:
            x, z = mix(center[0], x, factor), mix(center[1], z, factor)
            y = .16 - .6 * x * x if back else .044 - .138 * math.sqrt(max(.05, 1 - (x / .203) ** 2))
            if not back:
                hit = bpy.gb15_skin_bvh.ray_cast(Vector((x, -.4, z)), Vector((0, 1, 0)), .6)
                if hit[0] is not None:
                    y = hit[0].y - .013
            if factor == .89:
                y += -.002 if not back else .002
            row.append(mesh.vertex((x, y, z), weight))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        mesh.bridge(a, b)
    mesh.cap(rows[-1], weight)
    if not back:
        p = mesh.vertices[-1]
        hit = bpy.gb15_skin_bvh.ray_cast(Vector((p.x, -.4, p.z)), Vector((0, 1, 0)), .6)
        if hit[0] is not None:
            p.y = hit[0].y - .013
    inner = [mesh.vertex(mesh.vertices[i] + Vector((0, -.004 if back else .004, 0)), weight) for i in rows[0]]
    mesh.bridge(rows[0], inner)
    mesh.cap(inner, weight)
    return mesh.object()


def armor(mats, landmarks):
    plate_patch('GB15 Gorget', [(-.166, 1.355), (-.113, 1.371), (-.057, 1.352), (0, 1.339),
                               (.057, 1.352), (.113, 1.371), (.166, 1.355), (.133, 1.302),
                               (.073, 1.257), (0, 1.230), (-.073, 1.257), (-.133, 1.302)],
                (0, 1.310), mats['iron'], {'chest': 1})
    for side in [1, -1]:
        suffix = '.L' if side == 1 else '.R'
        mesh = Mesh('GB15 Shoulder' + suffix, mats['iron'])
        weight = {'pauldron' + suffix: 1}
        rows = []
        for radius in [.12, .45, .78, 1]:
            row = []
            for i in range(16):
                angle = i * math.tau / 16
                x = .218 + .084 * radius * math.cos(angle)
                y = .047 + .101 * radius * math.sin(angle)
                z = 1.393 - .027 * radius * radius - .42 * .084 * radius * math.cos(angle) - \
                    .061 * radius ** 1.5 * abs(math.sin(angle))
                hit = bpy.gb15_skin_bvh.ray_cast(Vector((side * x, y, 1.6)), Vector((0, 0, -1)), .45)
                if hit[0] is not None:
                    z = max(z, hit[0].z + .005)
                row.append(mesh.vertex((side * x, y, z), weight))
            rows.append(row)
        mesh.cap(rows[0], weight)
        for a, b in zip(rows, rows[1:]):
            mesh.bridge(a, b)
        inner = [mesh.vertex(mesh.vertices[i] - Vector((0, 0, .004)), weight) for i in rows[-1]]
        mesh.bridge(rows[-1], inner)
        mesh.cap(inner, weight)
        for x, y, z, direction in [(.260, -.002, 1.352, (side * .6, -.35, .68)),
                                    (.292, .040, 1.330, (side * .9, 0, .4)),
                                    (.275, .106, 1.344, (side * .60, .5, .55))]:
            radius = math.sqrt(((x - .218) / .084) ** 2 + ((y - .047) / .101) ** 2)
            angle = math.atan2((y - .047) / .101, (x - .218) / .084)
            z = 1.393 - .027 * radius ** 2 - .42 * .084 * radius * math.cos(angle) - \
                .061 * radius ** 1.5 * abs(math.sin(angle))
            spike(mesh, (side * x, y, z - .001), direction, .012, .045, weight)
        mesh.object().data.set_sharp_from_angle(angle=.75)
        plate_patch('GB15 Back plate' + suffix,
                    [(side * x, z) for x, z in [(.019, 1.349), (.101, 1.354), (.128, 1.320),
                                                (.105, 1.267), (.022, 1.278)]],
                    (side * .070, 1.31), mats['iron'], {'chest': 1}, back=True)
        for kind in ['Bracer', 'Shin guard']:
            if kind == 'Bracer':
                start, end = Vector(landmarks['elbow' + suffix]), Vector(landmarks['wrist' + suffix])
                widths = [.050, .051, .044, .034, .029]
                depths = [.048, .048, .040, .035, .027]
                weight = {'forearm' + suffix: 1}
            else:
                start, end = Vector(landmarks['knee' + suffix]), Vector(landmarks['ankle' + suffix])
                widths = [.058, .067, .060, .048, .046]
                depths = [.058, .065, .060, .047, .046]
                weight = {'shin' + suffix: 1}
            direction = (end - start).normalized()
            u = Vector((side * -direction.z, 0, abs(direction.x))).normalized()
            v = Vector((0, -1, 0))
            grid = []
            for j in range(5):
                row = []
                for i in range(11):
                    angle = mix(-1.85, 1.85, i / 10)
                    t = mix(.18 - .13 * math.cos(angle), .99, j / 4)
                    row.append(start.lerp(end, t) + u * (widths[j] * math.sin(angle)) +
                               v * (depths[j] * math.cos(angle)))
                grid.append(row)
            mesh = Mesh('GB15 ' + kind + suffix, mats['iron'])
            shell(mesh, grid, weight, .0035, lambda p: -v)
            for j in [1, 2, 3]:
                center = start.lerp(end, j / 4)
                radial = (u * .73 + v * .60).normalized()
                spike(mesh, center + radial * widths[j], radial, .0068, .024 if kind == 'Bracer' else .021,
                      weight)
            mesh.object()
            straps = Mesh('GB15 ' + kind + ' straps' + suffix, mats['leather'])
            for t in [.23, .83]:
                radius = mix(widths[1], widths[-1], t) - .001
                a = ring(straps, start.lerp(end, t - .02), u, v, radius, radius, 12, weight)
                b = ring(straps, start.lerp(end, t + .02), u, v, radius, radius, 12, weight)
                if kind == 'Bracer':
                    for row, station in [(a, t - .02), (b, t + .02)]:
                        center = start.lerp(end, station)
                        for index in row[:7]:
                            straps.vertices[index] = center + (straps.vertices[index] - center) * .80
                straps.bridge(a, b)
            straps.object()


def clothing(mats):
    belt = Mesh('GB15 Belt', mats['leather'])
    rows = []
    for z, rx, ry in [(.956, .160, .130), (.965, .160, .135), (.997, .153, .133), (1.005, .150, .130)]:
        rows.append(ring(belt, (0, .045, z), Vector((1, 0, 0)), Vector((0, 1, 0)), rx, ry, 32, {'pelvis': 1}))
    for a, b in zip(rows, rows[1:]):
        belt.bridge(a, b)
    inside = []
    for row in [rows[0], rows[-1]]:
        inner = [belt.vertex(Vector((belt.vertices[i].x * .97, .045 + (belt.vertices[i].y - .045) * .97,
                                     belt.vertices[i].z)), {'pelvis': 1}) for i in row]
        belt.bridge(row, inner)
        inside.append(inner)
    belt.bridge(*inside)
    belt.object()
    buckle = Mesh('GB15 Belt buckle', mats['brass'])
    loops = []
    for index in range(12):
        angle = index * math.tau / 12
        x = .025 * math.copysign(abs(math.cos(angle)) ** .5, math.cos(angle))
        z = .980 + .018 * math.copysign(abs(math.sin(angle)) ** .5, math.sin(angle))
        loops.append(ring(buckle, (x, -.094, z), Vector((math.cos(angle), 0, math.sin(angle))),
                          Vector((0, 1, 0)), .003, .003, 4, {'pelvis': 1}))
    for a, b in zip(loops, loops[1:] + loops[:1]):
        buckle.bridge(a, b)
    buckle.object()
    panels = Mesh('GB15 Leather skirt strips', mats['leather'])
    controls = {}
    for strip in range(17):
        angle = strip * math.tau / 17
        top = Vector((.151 * math.sin(angle), .045 - .110 * math.cos(angle), .967))
        name = 'skirt.' + str(strip).zfill(2)
        bottom_z = .747 + .026 * math.cos(angle * 3 + .4) + .013 * math.sin(angle * 5)
        controls[name] = [list(top), list(top - Vector((0, 0, .18)))]
        rows = []
        for t in [0, .25, .58, .84, 1]:
            row = []
            for j in [-1, 0, 1]:
                spread = (1 if t < .8 else mix(.90, .025, (t - .8) / .2)) * .197
                a = angle + j * spread
                rx, ry = mix(.154, .188, t), mix(.113, .148, t)
                z = mix(.960, bottom_z, t)
                radius_detail = .002 * (1 - abs(j)) * math.sin(t * math.pi)
                point = Vector(((rx + radius_detail) * math.sin(a), .045 - (ry + radius_detail) * math.cos(a), z))
                row.append(point)
            rows.append(row)
        outer, inner = [], []
        for index, row in enumerate(rows):
            blend = min(1, index * .65)
            weights = {'pelvis': 1 - blend, name: blend}
            outer.append([panels.vertex(p, weights) for p in row])
            inner.append([panels.vertex(p - Vector((math.sin(angle), -math.cos(angle), 0)) * .003, weights)
                          for p in row])
        for surface in [outer, inner]:
            for a, b in zip(surface, surface[1:]):
                for j in range(2):
                    panels.face((a[j], a[j + 1], b[j + 1], b[j]))
        outlines = [grid[0] + [r[-1] for r in grid[1:]] + list(reversed(grid[-1][:-1])) +
                    [r[0] for r in reversed(grid[1:-1])] for grid in [outer, inner]]
        panels.bridge(*outlines)
    panels.object()
    (ROOT / 'authoring/skirt_controls.json').write_text(json.dumps(controls, indent=2) + '\n')
    pouch = Mesh('GB15 Right hip pouch', mats['leather'])
    outline = [(-1, -.65), (-.65, -1), (.65, -1), (1, -.65), (1, .65), (.65, 1), (-.65, 1), (-1, .65)]
    rows = []
    for z, size in [(.843, .80), (.85, 1), (.929, 1), (.955, .8)]:
        rows.append([pouch.vertex((-.172 + x * .034 * size, -.010 + y * .025 * size, z), {'pelvis': 1})
                     for x, y in outline])
    for a, b in zip(rows, rows[1:]):
        pouch.bridge(a, b)
    pouch.cap(rows[0], {'pelvis': 1})
    pouch.cap(rows[-1], {'pelvis': 1})
    shell(pouch, [[Vector((-.204, -.038, .945)), Vector((-.172, -.042, .949)), Vector((-.141, -.038, .945))],
                  [Vector((-.20, -.042, .917)), Vector((-.172, -.046, .906)), Vector((-.145, -.042, .917))]],
          {'pelvis': 1}, .003, lambda p: Vector((0, 1, 0)))
    pouch.object()


def hoops_and_claws(mats, landmarks):
    hoops = Mesh('GB15 Right ear hoops', mats['brass'])
    for x, y, z, radius in [(-.113, .016, 1.594, .010), (-.118, .017, 1.574, .012),
                           (-.116, .012, 1.552, .014)]:
        rows = []
        for i in range(12):
            angle = math.tau * i / 12
            center = Vector((x + radius * math.cos(angle), y, z + radius * math.sin(angle)))
            rows.append(ring(hoops, center, Vector((math.cos(angle), 0, math.sin(angle))), Vector((0, 1, 0)),
                             .0019, .0019, 4, {'head': 1}))
        for a, b in zip(rows, rows[1:] + rows[:1]):
            hoops.bridge(a, b)
    hoops.object()
    claws = Mesh('GB15 Claws', mats['horn'])
    for name, points in landmarks.items():
        if not name.startswith(('digit', 'toe', 'thumb')) or name.startswith('toe_end'):
            continue
        points = list(map(Vector, points))
        direction = (points[-1] - points[-2]).normalized()
        toe = name.startswith('toe')
        offset = Vector((0, 0, .008)) if toe else Vector((0, .003, 0))
        center = points[-1] - direction * .009 + offset
        suffix = '.L' if '.L' in name else '.R'
        weight = {'foot' + suffix: 1} if toe else {name + '.03': 1}
        spike(claws, center, direction + Vector((0, 0, -1.0 if toe else -.18)), .010 if toe else .0033,
              .033 if toe else .012, weight)
    claws.object()


def build():
    obj = bpy.data.objects['GB15 Skin body']
    bpy.gb15_skin_bvh = BVHTree.FromPolygons([v.co.copy() for v in obj.data.vertices],
                                          [p.vertices[:] for p in obj.data.polygons])
    landmarks = json.loads((ROOT / 'authoring/landmarks.json').read_text())
    mats = materials()
    armor(mats, landmarks)
    clothing(mats)
    hoops_and_claws(mats, landmarks)
    for obj in bpy.data.collections['GB15 Character'].objects:
        if obj.type == 'MESH' and obj.name.startswith(('GB15 Gorget', 'GB15 Shoulder', 'GB15 Bracer',
                                                     'GB15 Shin', 'GB15 Belt', 'GB15 Leather', 'GB15 Back',
                                                     'GB15 Right hip')):
            obj.data.set_sharp_from_angle(angle=.75)


if __name__ == '__main__':
    build()
