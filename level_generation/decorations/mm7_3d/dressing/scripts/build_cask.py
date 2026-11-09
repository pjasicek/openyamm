"""MM7 `7dec21` (1 placement, 7d29): a squat cask lying on its side, its head toward the viewer's right with a tap
(spigot and T handle), four riveted iron hoops (two close together at the head, one a third along, one at the far
end), wide orange-brown staves. Measured on the x2 sprite (248 x 187 px): the head ellipse is 59 x 75 units, so the
head faces about 38 degrees right of the view; the cask is 96 long, 75 across the heads and 90 at the bulge.

Built upright with build_barrel.py's builders (spec `7dec21` in barrel_spec.json, atlas from barrel_textures.py),
closed by a second head at the far end, then laid on its side (axis along the head direction (0.62, -0.79, 0)) and
grounded on its bulge. COLOR_0 = vertex occlusion with the floor. Writes work/7dec21.blend, work/7dec21_export.glb.
Usage: blender --background --python build_cask.py"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
import build_barrel as bb  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = '7dec21'
bb.configure(PROP)
HEAD_YAW = math.radians(-46.0)          # local +x (after laying, the head direction) turned 44 degrees right of the view
IRON_RECT = (0.31, 0.79, 0.49, 0.97)


def to_rect(obj, rect):
    """Squeeze an object's texture coordinates into rect (u0, v0, u1, v1) of the atlas."""
    uv = obj.data.uv_layers[0].data
    us = [d.uv[0] for d in uv]; vs = [d.uv[1] for d in uv]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    for d in uv:
        d.uv = (rect[0] + (d.uv[0] - u0) / max(u1 - u0, 1e-6) * (rect[2] - rect[0]),
                rect[1] + (d.uv[1] - v0) / max(v1 - v0, 1e-6) * (rect[3] - rect[1]))
    return obj


def far_head(level):
    """The far end's head: a flat disc at z = 0 inside the bottom hoop, facing down (outward)."""
    segments = (16, 12, 8, 6)[level]
    r = bb.radius(0.0)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    ring = [bm.verts.new((u(r) * math.sin(2 * math.pi * s / segments), -u(r) * math.cos(2 * math.pi * s / segments),
                          u(0.4))) for s in reversed(range(segments))]
    f = bm.faces.new(ring)
    for loop in f.loops:
        loop[uvl].uv = (bb.LID_C[0] + loop.vert.co.x / u(r) * bb.LID_R * 0.9,
                        bb.LID_C[1] + loop.vert.co.y / u(r) * bb.LID_R * 0.9)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    obj = pl.to_object('farhead', bm, bb.mats_cache['Barrel'], False)
    if obj.data.polygons[0].normal.z > 0:
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(obj.data); bm.free()
    return obj


def tap(level):
    """Spigot on the head, a little above the axis (local -x is up once laid): boss, spout bending down, T handle."""
    if level >= 3:
        return []
    zh = bb.H - bb.SPEC['lid_depth']
    sides = (8, 6, 4)[level]
    up = -5.0
    m = 1 / dlib.UNITS_PER_METRE
    parts = [
        pl.tube('boss', (up * m, 0, zh * m), (up * m, 0, (zh + 3) * m), u(3.4), u(3.0), sides,
                bb.mats_cache['Barrel']),
        pl.tube('spout', (up * m, 0, (zh + 3) * m), (up * m, 0, (zh + 9) * m), u(2.4), u(2.4), sides,
                bb.mats_cache['Barrel']),
        pl.tube('nozzle', (up * m, 0, (zh + 8.2) * m), ((up + 7) * m, 0, (zh + 10.5) * m), u(2.2), u(1.9), sides,
                bb.mats_cache['Barrel']),
    ]
    if level < 2:
        parts.append(pl.tube('stem', (up * m, 0, (zh + 6.5) * m), ((up - 6) * m, 0, (zh + 6.5) * m), u(1.0),
                             u(1.0), 4, bb.mats_cache['Barrel']))
        parts.append(pl.tube('bar', ((up - 6) * m, -u(5.5), (zh + 6.5) * m), ((up - 6) * m, u(5.5), (zh + 6.5) * m),
                             u(1.0), u(1.0), 4, bb.mats_cache['Barrel']))
    for p in parts:
        to_rect(p, IRON_RECT)
    return parts


if __name__ == '__main__':
    pl.reset()
    bb.mats_cache = {'Barrel': dlib.material('Barrel', PROP, extras={'openyamm_specular': 0.6,
                                                                       'openyamm_specular_mask': True})}
    lay = Matrix.Rotation(HEAD_YAW, 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'Y')
    lods = []
    for level in range(4):
        parts = bb.body(level, bb.mats_cache) + [far_head(level)] + tap(level)
        for obj in parts:
            dlib.apply(obj)
        name = 'Cask' if level == 0 else f'Cask_LOD{level}'
        solid = pl.join(name, parts)
        solid.data.transform(Matrix.Translation((0, 0, -u(bb.H / 2))))
        solid.data.transform(lay)
        lowest = min(v.co.z for v in solid.data.vertices)
        solid.data.transform(Matrix.Translation((0, 0, -lowest)))
        solid.data.update()
        bpy.context.view_layer.objects.active = solid
        solid.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        occ = pl.vertex_occlusion(solid, rays=(48, 32, 16, 12)[level], distance=u(20), strength=0.45, floor=True)
        print('LEVEL', level, name, 'tris', pl.triangles(solid), 'occlusion', round(occ, 3))
        lods.append(solid)
    dlib.save(PROP, lods)
