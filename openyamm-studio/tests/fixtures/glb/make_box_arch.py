# Writes box_arch.glb beside this file: the GLB import's test model (tests/OdmV2Tests.cpp, examples/glb_gate), made
# the way a landmark is made: in Blender, in map units (1 unit = 1 map unit), exported with Blender's defaults (+Y up,
# triangles). Two meshes:
#   Gate: a wall 1024 wide, 768 high, 128 thick with a round-headed opening 512 wide (sides to 256, the crown at
#         512), its faces in quads round the arch; walls t14a01, the top t06b01.
#   Box:  a 512 cube beside it, material `t14a01.001` (Blender's numbered copy of a material) and its top a
#         collision-only slab material `blocker`.
# UVs: each face's corners projected on its plane's main axes at 128 units a picture, so faces of one plane carry one
# continuous picture. Run: blender --background --factory-startup --python make_box_arch.py
import math
import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_PER_PICTURE = 128.0


def material(name):
    found = bpy.data.materials.get(name)
    return found if found is not None else bpy.data.materials.new(name)


def planar_uvs(mesh_data):
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    uv = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        for loop in face.loops:
            p = loop.vert.co
            if axis == 2:      # level: east and south
                u, v = p.x, -p.y
            elif axis == 1:    # facing north or south: along x, down
                u, v = (p.x if n.y < 0 else -p.x), -p.z
            else:              # facing east or west
                u, v = (p.y if n.x > 0 else -p.y), -p.z
            loop[uv].uv = (u / UNITS_PER_PICTURE, -v / UNITS_PER_PICTURE)
    bm.to_mesh(mesh_data)
    bm.free()


def add_object(name, verts, faces, face_materials, materials):
    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(verts, [], faces)
    for m in materials:
        mesh_data.materials.append(material(m))
    for poly, index in zip(mesh_data.polygons, face_materials):
        poly.material_index = index
    mesh_data.update()
    planar_uvs(mesh_data)
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def gate():
    half, thick, height, spring, radius, segments = 512.0, 128.0, 768.0, 256.0, 256.0, 8
    t = thick / 2
    verts, faces, mats = [], [], []

    def v(x, y, z):
        verts.append((x, y, z))
        return len(verts) - 1

    def face(ids, m, want):
        # Wound so that its normal (Newell's) points the way `want` does: outward.
        n = [0.0, 0.0, 0.0]
        for i, a in enumerate(ids):
            p, q = verts[a], verts[ids[(i + 1) % len(ids)]]
            n[0] += (p[1] - q[1]) * (p[2] + q[2])
            n[1] += (p[2] - q[2]) * (p[0] + q[0])
            n[2] += (p[0] - q[0]) * (p[1] + q[1])
        faces.append(ids if sum(a * b for a, b in zip(n, want)) > 0 else list(reversed(ids)))
        mats.append(m)

    # Arc points (inner) and the matching points on the outer rectangle (rays from the arch's centre).
    def outer(angle):
        dx, dz = math.cos(angle), math.sin(angle)
        k = min((half / abs(dx)) if abs(dx) > 1e-9 else 1e9, (height - spring) / dz if dz > 1e-9 else 1e9)
        return dx * k, spring + dz * k

    for y in (-t, t):
        want = (0.0, -1.0 if y < 0 else 1.0, 0.0)
        arc = [v(radius * math.cos(math.pi * i / segments), y, spring + radius * math.sin(math.pi * i / segments))
               for i in range(segments + 1)]
        rim = [v(outer(math.pi * i / segments)[0], y, outer(math.pi * i / segments)[1]) for i in range(segments + 1)]
        for i in range(segments):
            ids = [arc[i], arc[i + 1], rim[i + 1], rim[i]]
            a, b = verts[rim[i]], verts[rim[i + 1]]
            # A rim stretch that turns a corner of the rectangle gets the corner too.
            if (a[2] < height - 1e-6) != (b[2] < height - 1e-6):
                ids = [arc[i], arc[i + 1], rim[i + 1], v(half if a[0] > 0 else -half, y, height), rim[i]]
            face(ids, 0, want)
        # The pillars under the spring.
        for x0, x1 in ((-half, -radius), (radius, half)):
            face([v(x0, y, 0.0), v(x1, y, 0.0), v(x1, y, spring), v(x0, y, spring)], 0, want)
    # Top, ends, jambs and the soffit (facing into the opening).
    face([v(-half, -t, height), v(half, -t, height), v(half, t, height), v(-half, t, height)], 1, (0, 0, 1))
    for x0, out in ((half, 1.0), (-half, -1.0)):
        face([v(x0, -t, 0), v(x0, t, 0), v(x0, t, height), v(x0, -t, height)], 0, (out, 0, 0))
    for x0, inward in ((-radius, 1.0), (radius, -1.0)):
        face([v(x0, -t, 0), v(x0, t, 0), v(x0, t, spring), v(x0, -t, spring)], 0, (inward, 0, 0))
    for i in range(segments):
        a0, a1 = math.pi * i / segments, math.pi * (i + 1) / segments
        middle = (a0 + a1) / 2
        p0 = (radius * math.cos(a0), spring + radius * math.sin(a0))
        p1 = (radius * math.cos(a1), spring + radius * math.sin(a1))
        face([v(p0[0], -t, p0[1]), v(p0[0], t, p0[1]), v(p1[0], t, p1[1]), v(p1[0], -t, p1[1])], 0,
             (-math.cos(middle), 0, -math.sin(middle)))
    return add_object('Gate', verts, faces, mats, ['t14a01', 't06b01'])


def box():
    s = 256.0
    x0, y0 = 1024.0, 0.0
    verts = [(x0 - s, y0 - s, 0), (x0 + s, y0 - s, 0), (x0 + s, y0 + s, 0), (x0 - s, y0 + s, 0),
             (x0 - s, y0 - s, 2 * s), (x0 + s, y0 - s, 2 * s), (x0 + s, y0 + s, 2 * s), (x0 - s, y0 + s, 2 * s)]
    faces = [(4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return add_object('Box', verts, faces, [1, 0, 0, 0, 0], ['t14a01.001', 'blocker'])


bpy.ops.wm.read_factory_settings(use_empty=True)
gate()
box()
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'box_arch.glb'), export_format='GLB', use_selection=False,
                          export_apply=True)
print('wrote', os.path.join(HERE, 'box_arch.glb'))
