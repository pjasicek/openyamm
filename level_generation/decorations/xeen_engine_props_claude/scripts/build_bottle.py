"""`7dec41` "bottle" (MM7 engine decoration; Crodo's bottle in Xeen): a tall olive-green glass bottle with a cork and
a yellow label, traced from the x2 sprite (123 x2 pixels tall, 37 wide: straight body to 68 % of the height, a short
rounded shoulder, a narrow neck, a pale lip ring, the cork). Glass as the MM7/MM8 goblet (mm8_3d/props
build_goblet.py): opaque and glossy, no blending. Three smooth lathes that meet at hard steps (glass body with shoulder
and neck, lip ring, cork), so each step is a real vertex split; one material on the `bottle` unwrap (u around, v =
height / 123, the label on the front half; the bottom cap and the cork top map into plain glass and cork).
COLOR_0 = light vertex occlusion x the outdoor grade.
Usage: blender --background --python build_bottle.py -- [grade_r grade_g grade_b]"""
import math
import os
import sys

import bmesh
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlib  # noqa: E402

pl = xlib.pl
PROP = '7dec41'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
GRADE = [float(a) for a in args[:3]] if len(args) >= 3 else [1.0, 1.0, 1.0]

HEIGHT_PX = 123.0               # sprite x2 pixels (make_textures.BOTTLE_HEIGHT)
SCALE = 0.01                    # metres per sprite pixel in Blender (the binding sets the world height)
# (radius, z) in sprite x2 pixels, bottom to top, per part and level
GLASS = [
    [(0.0, 0.0), (16.0, 0.0), (17.6, 1.2), (18.0, 3.0), (18.0, 84.0), (17.4, 87.0), (15.4, 90.0), (11.8, 93.0),
     (8.0, 95.6), (5.6, 97.8), (5.0, 100.0), (5.0, 104.0)],
    [(0.0, 0.0), (17.0, 0.0), (18.0, 2.0), (18.0, 84.0), (16.4, 89.0), (11.0, 93.5), (5.6, 97.6), (5.0, 104.0)],
    [(0.0, 0.0), (18.0, 0.0), (18.0, 85.0), (11.0, 93.5), (5.0, 98.0), (5.0, 104.0)],
]
LIP = [(5.0, 104.0), (6.2, 104.0), (6.2, 110.0), (4.7, 110.0)]
CORK = [(4.7, 110.0), (4.9, 121.0), (4.4, 123.0), (0.0, 123.0)]
SEGMENTS = [(16, 12), (10, 8), (6, 0)]          # glass, lip and cork (0: merged into the glass's top)
LOW_TOP = [(5.0, 104.0), (5.0, 123.0), (0.0, 123.0)]


def lathe(bm, uv, profile, segments, cap_uv):
    """Rings of profile [(r, z) px]; a profile point with r = 0 closes the end with an n-gon cap mapped to cap_uv
    (u0, v0, u1, v1). Side u = angle / 2pi, v = z / HEIGHT_PX."""
    rings = []
    for r, z in profile:
        if r <= 0.0:
            rings.append(None)
            continue
        rings.append([bm.verts.new((r * SCALE * math.cos(2 * math.pi * s / segments),
                                    r * SCALE * math.sin(2 * math.pi * s / segments), z * SCALE))
                      for s in range(segments)])
    side_faces = []
    for i in range(len(profile) - 1):
        a, b = rings[i], rings[i + 1]
        if a is None or b is None:
            continue
        za, zb = profile[i][1] / HEIGHT_PX, profile[i + 1][1] / HEIGHT_PX
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((a[s], a[s2], b[s2], b[s]))
            side_faces.append(f)
            for loop, (uu, vv) in zip(f.loops, ((s, za), (s + 1, za), (s + 1, zb), (s, zb))):
                loop[uv].uv = (uu / segments, vv)
    for i, ring in enumerate(rings):
        if ring is not None:
            continue
        neighbour = rings[i + 1] if i == 0 else rings[i - 1]
        f = bm.faces.new(list(reversed(neighbour)) if i == 0 else neighbour)
        u0, v0, u1, v1 = cap_uv
        r = max(abs(v.co.x) for v in neighbour) or 1.0
        for loop in f.loops:
            loop[uv].uv = (u0 + (u1 - u0) * (0.5 + loop.vert.co.x / r * 0.5),
                           v0 + (v1 - v0) * (0.5 + loop.vert.co.y / r * 0.5))
    return side_faces


GLASS_CAP = (0.05, 0.40, 0.25, 0.60)            # plain glass in the unwrap
CORK_CAP = (0.30, 0.91, 0.70, 0.99)             # the cork band


def build(level):
    glass_seg, top_seg = SEGMENTS[level]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    if top_seg:
        lathe(bm, uv, GLASS[level] + [(0.0, 104.0)], glass_seg, GLASS_CAP)
        lathe(bm, uv, LIP + [(0.0, 110.0)], top_seg, CORK_CAP)
        lathe(bm, uv, CORK, top_seg, CORK_CAP)
    else:
        lathe(bm, uv, GLASS[level][:-1] + LOW_TOP, glass_seg, GLASS_CAP)
    # the lip and cork bottoms are open rings resting on the part below; close them for a clean winding check
    filled = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    for f in filled['faces']:
        for loop in f.loops:
            loop[uv].uv = (0.15, 0.5)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE', ngon_method='BEAUTY')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object('Base' if level == 0 else f'Base_LOD{level}', bm, None, True)


pl.reset()
glass = xlib.material('Glass', 'bottle', extras={'openyamm_specular': 0.5})
lods = []
for level in range(3):
    obj = build(level)
    obj.data.materials.append(glass)
    # sharp ring edges where the profile turns by more than 40 degrees (bottom rim, lip steps, cork top); edges along
    # the profile stay smooth, so the low levels' few sides still shade round
    bm = bmesh.new(); bm.from_mesh(obj.data)
    for e in bm.edges:
        ring = abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6
        if ring and len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40):
            e.smooth = False
    bm.to_mesh(obj.data); bm.free()
    pl.vertex_occlusion(obj, rays=(32, 16, 8)[level], distance=0.1, strength=0.35, floor=True)
    me = obj.data
    c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', c)
    c = c.reshape(-1, 4); c[:, :3] = np.clip(c[:, :3] * np.array(GRADE, np.float32), 0, 1)
    me.color_attributes['Color'].data.foreach_set('color', c.ravel())
    lods.append(obj)
xlib.save(PROP, lods)
