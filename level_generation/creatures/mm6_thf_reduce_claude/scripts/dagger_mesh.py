"""Rebuilt thief daggers (user review 2026-10-14: "the daggers could look more sharp and overall better, with the tris
count in mind"), replacing the reduced originals of ../mm6_thf_claude/scripts/seat_daggers.py on the same seat (grip
centre, blade axis, width axis from scene['thf_daggers']) and bones (100 % DaggerL / DaggerR).

Per dagger, about 126 triangles (the reduced originals had 82, the unreduced 150):
- blade 16 cm: eight-sided section (cutting edge, edge bevel, flat, central ridge on both faces), a slight leaf
  profile and a long taper into a needle point; flat-shaded so the bevels read as sharp lines;
- cross guard 6.2 cm with quillons thinning and curving slightly toward the blade;
- hexagonal wrapped grip 8.5 cm with a slight swell, smooth-shaded; faceted pommel.
Face attribute `dagger_piece`: 1 blade, 2 grip, 3 guard, 4 pommel (0 = not a dagger). UVs: map_uvs() lays every
piece into its rectangle of the dagger column of the body image (painted by compose_tex.py)."""
import json
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

GRIP_L, GRIP_R = 0.085, 0.0105
GUARD_Y0, GUARD_Y1, GUARD_W = GRIP_L / 2, GRIP_L / 2 + 0.012, 0.062
BLADE, HALF_W, HALF_T = 0.16, 0.013, 0.00275
PROFILE = ((0.0, 0.95, 1.0), (0.3, 1.0, 0.95), (0.62, 0.86, 0.8), (0.84, 0.5, 0.55))   # t, width, thickness
POMMEL = (-GRIP_L / 2 - 0.0075, 0.0145, -GRIP_L / 2 - 0.016)                         # ring y, ring radius, point y
BLADE_PIECE, GRIP_PIECE, GUARD_PIECE, POMMEL_PIECE = 1, 2, 3, 4


def build(bm):
    """One dagger in local coordinates (X width, +Y toward the point, grip centre at the origin, Z the blade flats).
    Returns {face: piece}."""
    pieces = {}

    def face(vs, piece):
        f = bm.faces.new(vs)
        pieces[f] = piece

    def bridge(a, b, piece):
        n = len(a)
        for k in range(n):
            face((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]), piece)

    # blade
    y0 = GUARD_Y1
    secs = []
    for t, wf, tf in PROFILE:
        w, th, y = HALF_W * wf, HALF_T * tf, y0 + BLADE * t
        pts = ((w, 0), (0.55 * w, 0.7 * th), (0, th), (-0.55 * w, 0.7 * th),
               (-w, 0), (-0.55 * w, -0.7 * th), (0, -th), (0.55 * w, -0.7 * th))
        secs.append([bm.verts.new((x, y, z)) for x, z in pts])
    for a, b in zip(secs, secs[1:]):
        bridge(a, b, BLADE_PIECE)
    tip = bm.verts.new((0, y0 + BLADE, 0))
    for k in range(8):
        face((secs[-1][k], secs[-1][(k + 1) % 8], tip), BLADE_PIECE)
    # cross guard: four rectangular sections along X; the quillons thin and curve toward the blade
    rings = []
    for x, dy, hy, hz in ((-GUARD_W / 2, 0.004, 0.0035, 0.0045), (-0.012, 0.0, 0.006, 0.008),
                          (0.012, 0.0, 0.006, 0.008), (GUARD_W / 2, 0.004, 0.0035, 0.0045)):
        yc = (GUARD_Y0 + GUARD_Y1) / 2 + dy
        rings.append([bm.verts.new((x, yc + sy * hy, sz * hz)) for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rings, rings[1:]):
        bridge(a, b, GUARD_PIECE)
    face(tuple(reversed(rings[0])), GUARD_PIECE)
    face(tuple(rings[-1]), GUARD_PIECE)
    # grip (hexagonal, swelling slightly in the middle) and pommel
    hexes = [[bm.verts.new((r * math.cos(2 * math.pi * k / 6 + math.pi / 6), y, r * math.sin(2 * math.pi * k / 6 + math.pi / 6)))
              for k in range(6)] for y, r in ((-GRIP_L / 2, GRIP_R), (0.0, GRIP_R * 1.1), (GRIP_L / 2, GRIP_R))]
    bridge(hexes[1], hexes[0], GRIP_PIECE)
    bridge(hexes[2], hexes[1], GRIP_PIECE)
    py, pr, pt = POMMEL
    ring = [bm.verts.new((pr * math.cos(2 * math.pi * k / 6), py, pr * math.sin(2 * math.pi * k / 6))) for k in range(6)]
    bridge(hexes[0], ring, POMMEL_PIECE)
    point = bm.verts.new((0, pt, 0))
    for k in range(6):
        face((ring[k], ring[(k + 1) % 6], point), POMMEL_PIECE)
    bmesh.ops.recalc_face_normals(bm, faces=list(pieces))
    return pieces


def seat_frame(seat):
    d = Vector(seat['axis']).normalized()
    xw = Vector(seat['width_axis'])
    xw = (xw - d * xw.dot(d)).normalized()
    flat = d.cross(xw).normalized()
    return Vector(seat['grip']), xw, d, flat


def replace(mesh, rig, scene, part):
    """Delete the mesh's dagger faces and join the rebuilt daggers (rest pose, mesh space = rig space)."""
    parts = json.loads(scene['thf_parts'])
    seats = json.loads(scene['thf_daggers'])
    di = parts.index('Dagger')
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.faces.ensure_lookup_table()
    old = [f for f in bm.faces if part[f.index] == di]
    bmesh.ops.delete(bm, geom=old, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(mesh.data)
    bm.free()
    new_objects = []
    for sd in ('L', 'R'):
        bm = bmesh.new()
        pieces = build(bm)
        grip, xw, d, flat = seat_frame(seats[sd])
        M = Matrix.Translation(grip) @ Matrix((xw, d, flat)).transposed().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
        tri = bmesh.ops.triangulate(bm, faces=bm.faces[:])
        origin = tri['face_map']                                        # new triangle -> the face it came from
        me = bpy.data.meshes.new('Dagger' + sd)
        bm.faces.ensure_lookup_table()
        piece_of = [pieces[origin.get(f, f)] for f in bm.faces]
        bm.to_mesh(me)
        bm.free()
        for p, pc in zip(me.polygons, piece_of):
            p.use_smooth = pc == GRIP_PIECE
        n = len(me.polygons)
        me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', [di] * n)
        me.attributes.new('uv_region', 'INT', 'FACE').data.foreach_set('value', [0] * n)
        me.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [0] * n)
        me.attributes.new('dagger_piece', 'INT', 'FACE').data.foreach_set('value', piece_of)
        me.uv_layers.new(name=mesh.data.uv_layers.active.name)
        o = bpy.data.objects.new('Dagger' + sd, me)
        scene.collection.objects.link(o)
        o.vertex_groups.new(name='Dagger' + sd).add(list(range(len(me.vertices))), 1.0, 'REPLACE')
        new_objects.append(o)
    for o in bpy.data.objects:
        o.select_set(o in new_objects or o == mesh)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    print('DAGGERS replaced: old faces', len(old), 'new tris', sum(len(o_.vertices) - 2 for o_ in mesh.data.polygons
                                                               if mesh.data.attributes['dagger_piece'].data[o_.index].value))


def map_uvs(bm, uvl, col, rects):
    """Dagger faces into the dagger column: blade by (across, along), grip and pommel by (angle, along), guard planar."""
    seats = json.loads(bpy.context.scene['thf_daggers'])
    frames = {sd: seat_frame(seats[sd]) for sd in ('L', 'R')}
    piece = bm.faces.layers.int['dagger_piece']
    u0, u1 = col

    def local(co):
        best = min(frames.values(), key=lambda fr: (co - fr[0]).length)
        grip, xw, d, flat = best
        c = co - grip
        return c.dot(xw), c.dot(d), c.dot(flat)

    for f in bm.faces:
        pc = f[piece]
        if not pc:
            continue
        coords = [local(l.vert.co) for l in f.loops]
        if pc == BLADE_PIECE:
            r0, r1 = rects['blade']
            uvs = [(u0 + (x / (HALF_W * 1.05) * 0.5 + 0.5) * (u1 - u0), r0 + (y - GUARD_Y1) / BLADE * (r1 - r0))
                   for x, y, z in coords]
        elif pc in (GRIP_PIECE, POMMEL_PIECE):
            r0, r1 = rects['grip'] if pc == GRIP_PIECE else rects['iron']
            if pc == POMMEL_PIECE:
                r0 = (r0 + r1) / 2                                     # upper half of the iron rect
            ys = (-GRIP_L / 2, GRIP_L / 2) if pc == GRIP_PIECE else (POMMEL[2], -GRIP_L / 2)
            angles = [math.atan2(z, x) % (2 * math.pi) / (2 * math.pi) for x, y, z in coords]
            if max(angles) - min(angles) > 0.5:                        # face across the wrap: continuous angles
                angles = [a + 1.0 if a < 0.5 else a for a in angles]
            uvs = [(u0 + a / 1.2 * (u1 - u0), r0 + (y - ys[0]) / (ys[1] - ys[0]) * (r1 - r0))
                   for a, (x, y, z) in zip(angles, coords)]
        else:                                                           # guard: planar, lower half of the iron rect
            r0, r1 = rects['iron']
            uvs = [(u0 + (x / GUARD_W + 0.5) * (u1 - u0), r0 + ((y - GUARD_Y0) / 0.02 + 0.2) * ((r1 - r0) / 2))
                   for x, y, z in coords]
        for l, uv in zip(f.loops, uvs):
            l[uvl].uv = uv
