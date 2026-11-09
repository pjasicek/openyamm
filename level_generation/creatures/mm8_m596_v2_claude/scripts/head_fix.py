"""Head fixes on the prepared mesh (review 2026-10-19): (1) the Meshy head is yawed about 32 deg to the creature's left
(the three-quarter master's head faces its camera): turn it back to face forward about a vertical axis through the
head joint, fading the turn in over the neck; (2) inset faceted gem eyes (bright amber, painted by texture.py) in
dark sockets on both sides of the face, at the brow line above the beak, found by ray casts from the front.
Faces get the int attribute 'part' (0 body, 1 eye gem, 2 eye socket) for texture.py.
Usage: blender -b -P head_fix.py -- <in.blend> <out.blend> <yaw deg> <eye aim y> <eye z> <eye angle deg from front>"""
import math, os, sys, bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, dst, yaw, ey, ez, eang = a[0], a[1], float(a[2]), float(a[3]), float(a[4]), float(a[5])
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, src))
body = bpy.data.objects['CrystalWalker']; me = body.data
PIV = Vector((0, -.17, 1.60))
def smooth(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
for v in me.vertices:
    c = v.co
    # the face and snout are turned, the crown top much less (measured forward-most points per 10 cm slab)
    w = smooth((c.z - 1.44) / .10) * (1 - .85 * smooth((c.z - 1.70) / .12))
    if c.z < 1.62 and abs(c.x) > .17:      # shoulder tops and arms stay
        w *= smooth((.24 - abs(c.x)) / .07)
    if w <= 0:
        continue
    r = Matrix.Rotation(math.radians(-yaw * w), 3, 'Z')
    d = c - PIV; d2 = r @ Vector((d.x, d.y, 0)); v.co = Vector((PIV.x + d2.x, PIV.y + d2.y, c.z))
me.update()
bm = bmesh.new(); bm.from_mesh(me)
part = bm.faces.layers.int.new('part')
tree = BVHTree.FromBMesh(bm)
eyes = []
for sx in (1, -1):
    # a horizontal ray toward the head's centre line from the front-side, eang degrees off straight ahead
    t = math.radians(eang); d = Vector((-sx * math.sin(t), math.cos(t), 0))
    hit, nrm, idx, dist = tree.ray_cast(Vector((0, ey, ez)) - d * .8, d)
    assert hit is not None, 'eye ray missed'
    eyes.append((hit, nrm.normalized()))
    print('EYE', [round(x, 3) for x in hit], 'normal', [round(x, 2) for x in nrm])
# sockets: faces near the eye, painted dark
for f in bm.faces:
    cen = f.calc_center_median()
    if any((cen - h).length < .030 for h, _ in eyes):
        f[part] = 2
# gem: a flattened faceted bipyramid (6 sides), 2.6 cm across, set half into the surface along its normal
for h, n in eyes:
    up = Vector((0, 0, 1)); side = n.cross(up).normalized(); up2 = side.cross(n).normalized()
    ctr = h + n * .002; rx, ry, depth = .021, .014, .011
    ring = [bm.verts.new(ctr + side * (math.cos(t) * rx) + up2 * (math.sin(t) * ry)) for t in
            [i * math.tau / 6 + .3 for i in range(6)]]
    tip = bm.verts.new(ctr + n * depth); back = bm.verts.new(ctr - n * depth)
    for i in range(6):
        a_, b_ = ring[i], ring[(i + 1) % 6]
        f1 = bm.faces.new((a_, b_, tip)); f1[part] = 1
        f2 = bm.faces.new((b_, a_, back)); f2[part] = 1
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[part] == 1])
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = False
print('HEADFIX yaw', yaw, 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, dst))
bpy.ops.export_scene.gltf(filepath=os.path.join(P, dst.replace('.blend', '.glb')), export_format='GLB', export_materials='NONE')
