"""Halberd prop for the MM6 guard, from the native sprites (see trace_halberd.py).

Native measurements (body height H = 251 px, guastaa0): shaft gem-to-butt 0.83 H (genuine side view guastaa2),
grip 56 % from the butt in the carry, shaft ~0.02 H thick with a thicker butt cap, blue gem cap on top. Head traced
broadside from guawinc0: crescent axe blade (0.24 H tall, 0.12 H out) and an opposite three-point star spike
(0.17 H out). Blades are flat 7 mm plates (edges come from the texture).

Built along +Z (butt at z = 0, gem on top), axe toward -X, spike toward +X, blade plane XZ.
Usage: blender --background --python make_halberd.py -- <body height m>
Saves work/halberd_v1.blend (object 'Halberd', custom props grip_from_butt, length)."""
import bpy, bmesh, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

H = float(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else 1.75
L = 0.83 * H
R = 0.0085 * H                  # shaft radius (native shaft 2.5-3.1 cm)
outline = json.load(open(os.path.join(common.WORK, 'halberd_outline.json')))

bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()


def ring(z, r, n=8, rot=0.0):
    return [bm.verts.new((r * math.cos(2 * math.pi * k / n + rot), r * math.sin(2 * math.pi * k / n + rot), z))
            for k in range(n)]


def bridge(a, b):
    n = len(a)
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))


def cap(rg, z, up):
    c = bm.verts.new((0, 0, z))
    n = len(rg)
    for k in range(n):
        bm.faces.new((rg[k], rg[(k + 1) % n], c) if up else (rg[(k + 1) % n], rg[k], c))


# shaft: butt knob, wrapped grip band, plain shaft, socket under the head
prof = [(0.000, 0.85), (0.012, 1.35), (0.035, 1.40), (0.050, 1.05), (0.25, 1.0), (0.45, 1.0), (0.62, 1.0),
        (0.70, 1.0), (0.735, 1.25), (0.95, 1.25), (0.985, 1.05), (1.0, 0.95)]
rings = [ring(f * L, s * R) for f, s in prof]
for a, b in zip(rings, rings[1:]):
    bridge(a, b)
cap(rings[0], -0.004, False)
top = rings[-1]
# gem: a small faceted dome on the top ring
gr = ring(L + 0.010 * H, 1.25 * R, 8, math.pi / 8)
bridge(top, gr)
cap(gr, L + 0.024 * H, True)


def plate(points, thick):
    """Closed outline (u from gem down, v across, in H units) -> flat plate in XZ, thickness along Y.
    The concave outline is tessellated once and used for both faces; a rim joins them."""
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon
    pts = [(v * H, L - u * H) for u, v in points]
    front = [bm.verts.new((x, -thick / 2, z)) for x, z in pts]
    back = [bm.verts.new((x, thick / 2, z)) for x, z in pts]
    n = len(pts)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((front[k], back[k], back[j], front[j]))
    for tri in tessellate_polygon([[Vector((x, z, 0)) for x, z in pts]]):
        bm.faces.new([front[i] for i in tri])
        bm.faces.new([back[i] for i in tri[::-1]])


plate(outline['axe'], 0.007)
plate(outline['spike'], 0.007)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Halberd')
bm.to_mesh(me)
bm.free()
for p in me.polygons:                       # smooth shaft, flat blades
    p.use_smooth = abs(p.normal.y) < 0.5 and (p.center.x ** 2 + p.center.y ** 2) ** 0.5 < 2.0 * R
o = bpy.data.objects.new('Halberd', me)
bpy.context.scene.collection.objects.link(o)
# per-face part: 0 wood, 1 iron, 2 gem, 3 grip band
part = me.attributes.new('part', 'INT', 'FACE')
for p in me.polygons:
    rr = (p.center.x ** 2 + p.center.y ** 2) ** 0.5
    if p.center.z > L + 0.002 * H and rr < 1.5 * R:
        k = 2
    elif rr > 1.6 * R or (0.73 * L < p.center.z < 0.99 * L and rr > 1.15 * R):
        k = 1
    elif p.center.z < 0.06 * L:
        k = 1
    else:
        k = 0
    part.data[p.index].value = k
o['grip_from_butt'] = 0.56 * L
o['length'] = L
o['body_height'] = H
print('HALBERD tris', len(me.polygons), 'length', round(L, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'halberd_v1.blend'))
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, 'halberd_v1'), L / 2, L * 1.1, views=('front', 'left'),
                    resolution=(400, 900))
common.render_views(os.path.join(common.REVIEW, 'halberd_v1_head'), L - 0.10 * H, 0.36 * H, views=('front', 'left'),
                    resolution=(500, 500))
