"""Cleric's staff from the native standing sprite (clesta0, x2 restored: 495 px body = 1.578 m, 3.19 mm/px).
Measured: total length 501 px = 1.60 m; ring finial 38 x 31 px outer (12.0 x 9.9 cm, tube ~2.5 cm); two crossbars
36 px wide (11.5 cm) at 45-50 and 55-62 px below the top; collar knob 15 px (4.8 cm) at 62-75 px; shaft ~3 cm;
grip centre 163 px below the top (1.08 m above the foot).
Built along +Z (foot at z=0). The ring lies in the local X-Z plane (seen open from local -Y), the crossbars run
along X. Saves work/staff_v1.blend (object 'Staff', custom props length, grip_from_foot, head_centre)."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

L = 1.60
GRIP = 1.08
RING_W, RING_H, TUBE = 0.120, 0.099, 0.0125
RING_C = L - RING_H / 2
BARS = [(L - 0.123, 0.115, 0.020), (L - 0.158, 0.108, 0.026)]     # (z centre, width, height)
KNOB = (L - 0.190, 0.024, 0.040)                                   # (z centre, radius, height)
SHAFT_R0, SHAFT_R1 = 0.0145, 0.0160                                # foot, top
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()


def tube_ring(verts_ring, n):
    return [verts_ring[k] for k in range(n)]


def lathe(profile, sides, z_axis_offset=0.0):
    """Closed surface of revolution about Z: profile [(z, r)], capped at both ends."""
    rings = []
    for z, r in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z))
                      for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    for ring, top in ((rings[0], False), (rings[-1], True)):
        c = bm.verts.new((0, 0, profile[-1 if top else 0][0] + (0.002 if top else -0.002)))
        for k in range(sides):
            f = (ring[k], ring[(k + 1) % sides], c) if top else (ring[(k + 1) % sides], ring[k], c)
            bm.faces.new(f)


# shaft with the collar knob merged into its profile
kz, kr, kh = KNOB
shaft_top = L - RING_H + 1.5 * TUBE                               # up through both bars into the ring
profile = [(0.0, SHAFT_R0 * 0.85), (0.012, SHAFT_R0)]
for z in (0.40, 0.80, GRIP - 0.06, GRIP + 0.06, kz - kh / 2 - 0.02):
    profile.append((z, SHAFT_R0 + (SHAFT_R1 - SHAFT_R0) * z / L))
profile += [(kz - kh / 2, kr * 0.7), (kz - kh / 2 + 0.006, kr), (kz + kh / 2 - 0.006, kr), (kz + kh / 2, kr * 0.8),
            (kz + kh / 2 + 0.004, 0.011), (shaft_top, 0.011)]
lathe(profile, 8)

# crossbars: rounded boxes (8-sided extrusions along X)
for zc, w, h in BARS:
    sides = 8
    rings = []
    for x in (-w / 2, -w / 2 + 0.006, w / 2 - 0.006, w / 2):
        s = 1.0 if abs(x) < w / 2 - 0.001 else 0.6
        rings.append([bm.verts.new((x, s * 0.013 * math.cos(2 * math.pi * k / sides),
                                    zc + s * h / 2 * math.sin(2 * math.pi * k / sides))) for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    for ring, end in ((rings[0], -1), (rings[-1], 1)):
        c = bm.verts.new((end * (w / 2 + 0.002), 0, zc))
        for k in range(sides):
            bm.faces.new((ring[k], ring[(k + 1) % sides], c) if end < 0 else (ring[(k + 1) % sides], ring[k], c))

# ring finial: elliptical torus in the X-Z plane on top of the shaft
seg, tube_sides = 18, 6
ra, rb = RING_W / 2 - TUBE, RING_H / 2 - TUBE
rings = []
for i in range(seg):
    t = 2 * math.pi * i / seg
    c = Vector((ra * math.sin(t), 0.0, RING_C + rb * math.cos(t)))
    tangent = Vector((ra * math.cos(t), 0.0, -rb * math.sin(t))).normalized()
    nrm = Vector((0, 1, 0)).cross(tangent).normalized()
    ring = []
    for k in range(tube_sides):
        a = 2 * math.pi * k / tube_sides
        ring.append(bm.verts.new(c + (nrm * math.cos(a) + Vector((0, 1, 0)) * math.sin(a) * 0.9) * TUBE))
    rings.append(ring)
for i in range(seg):
    a, b = rings[i], rings[(i + 1) % seg]
    for k in range(tube_sides):
        bm.faces.new((a[k], a[(k + 1) % tube_sides], b[(k + 1) % tube_sides], b[k]))

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces)
me = bpy.data.meshes.new('Staff'); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
o = bpy.data.objects.new('Staff', me); bpy.context.scene.collection.objects.link(o)
o['grip_from_foot'] = GRIP; o['length'] = L; o['head_centre'] = RING_C
print('STAFF tris', len(me.polygons), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'staff_v1.blend'))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, 'staff_v1'), 0.8, 1.7, views=('front', 'left'), resolution=(300, 900))
common.render_views(os.path.join(common.REVIEW, 'staff_v1_head'), 1.50, 0.30, views=('front', 'left'), resolution=(400, 400))
