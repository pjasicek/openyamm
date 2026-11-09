"""Staff prop from the native pmn2 standing sprite (pmn2sta0, x2 restored): length 0.943 x body height (1.60 m at
1.7 m), club head 26 cm long / ~9 cm wide, shaft 5.0 cm under the head tapering to 4.2 cm at the foot, held 29 % from
the top. Built along +Z (foot at z=0), gnarled by small seeded offsets. Saves work/staff_v1.blend (object 'Staff')."""
import bpy, bmesh, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
L, HEAD = 1.60, 0.26
random.seed(6)
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()
rings = []
# (z, radius, sides, lump): shaft rings then the club head; lump = per-vertex radius noise fraction
prof = [(0.0, 0.0195, 8, 0.0)]
for i in range(1, 12):
    z = i * (L - HEAD) / 11
    prof.append((z, 0.0210 + 0.0040 * z / (L - HEAD), 8, 0.06))
head = [(0.03, 0.028), (0.07, 0.036), (0.11, 0.043), (0.15, 0.046), (0.19, 0.044), (0.225, 0.036), (0.25, 0.022)]
for dz, r in head:
    prof.append((L - HEAD + dz, r, 10, 0.16))
bend = 0.0
for z, r, n, lump in prof:
    bend_x = 0.006 * math.sin(z * 4.1) + random.uniform(-0.002, 0.002)
    bend_y = 0.005 * math.sin(z * 3.3 + 1.0) + random.uniform(-0.002, 0.002)
    ring = []
    for k in range(n):
        a = 2 * math.pi * k / n + (0.3 if n == 10 else 0)
        rr = r * (1 + random.uniform(-lump, lump))
        ring.append(bm.verts.new((bend_x + rr * math.cos(a), bend_y + rr * math.sin(a), z)))
    rings.append(ring)


def bridge(a, b):
    if len(a) == len(b):
        n = len(a)
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    else:                                               # 8 -> 10 transition
        bmesh.ops.bridge_loops(bm, edges=[bm.edges.get((a[k], a[(k + 1) % len(a)])) or bm.edges.new((a[k], a[(k + 1) % len(a)])) for k in range(len(a))]
                               + [bm.edges.get((b[k], b[(k + 1) % len(b)])) or bm.edges.new((b[k], b[(k + 1) % len(b)])) for k in range(len(b))])


for a, b in zip(rings, rings[1:]):
    bridge(a, b)
bot = bm.verts.new((0, 0, -0.004)); top = bm.verts.new((0.004, -0.003, L))
for ring, cap in ((rings[0], bot), (rings[-1], top)):
    n = len(ring)
    for k in range(n):
        bm.faces.new((ring[(k + 1) % n], ring[k], cap) if cap is bot else (ring[k], ring[(k + 1) % n], cap))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces)
me = bpy.data.meshes.new('Staff'); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
o = bpy.data.objects.new('Staff', me); bpy.context.scene.collection.objects.link(o)
o['grip_from_foot'] = L * 0.71; o['length'] = L
print('STAFF tris', len(me.polygons), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'staff_v1.blend'))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, 'staff_v1'), 0.8, 1.7, views=('front', 'left'), resolution=(300, 900))
common.render_views(os.path.join(common.REVIEW, 'staff_v1_head'), 1.45, 0.4, views=('front', 'left'), resolution=(400, 400))
