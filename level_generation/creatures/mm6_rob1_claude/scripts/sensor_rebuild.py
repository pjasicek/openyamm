"""Replace Meshy's sensor head with clean hard-surface geometry (user review 2026-10-08: the nozzle was an open tube
and the box and vents soft blobs; scaled up 1.4x it read as sloppy). Runs once on the reduced work/anim_v1.blend
(backup work/anim_v1_pre_sensor.blend); the clips are unchanged because they key bones.

Proportions from the native frames (1 px = 0.0063 m at the sphere's 134 px): head about 0.29 m long, 0.16 m wide,
0.075 m tall, its centre about 0.19 m above the sphere top on a thin post bent forward.
  post    square bar along a bent path (pale tan)
  block   rear box with three vent ridges on its back face (pale blue-grey steel)
  nozzle  tapered front box (grey steel) closed by a round lens (dark glass)
Face attribute 'part' 41 post, 42 block, 43 nozzle, 44 lens, 45 vents (40 + sub-part; compose paints them
procedurally). UVs go into the free strip at the top of the atlas (v 0.952..0.998), long side along u.
All new vertices are bound 100 % to the Sensor bone; Socket_Lens moves to the new lens front."""
import bpy, bmesh, os, shutil, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
if not os.path.exists(os.path.join(WORK, 'anim_v1_pre_sensor.blend')):
    shutil.copy2(bpy.data.filepath, os.path.join(WORK, 'anim_v1_pre_sensor.blend'))
robot = bpy.data.objects['Robot']; rig = bpy.data.objects['Robot_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()

# Remove the old sensor (part 4, or a previous rebuild 41..45).
bm = bmesh.new(); bm.from_mesh(robot.data)
layer = bm.faces.layers.int['part']
old = [f for f in bm.faces if f[layer] == 4 or 41 <= f[layer] <= 45]
bmesh.ops.delete(bm, geom=old, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(robot.data); bm.free()

HEAD_Z = 1.040
new = bmesh.new()
part = new.faces.layers.int.new('part')


def box(corners, label):
    """corners: 8 points, bottom ring (-x-y, +x-y, +x+y, -x+y) then top ring in the same order."""
    v = [new.verts.new(c) for c in corners]
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        new.faces.new([v[i] for i in idx])[part] = label


def section(y0, y1, w0, h0, w1, h1, zc, label):
    """Box along Y from y0 (half width w0, half height h0) to y1 (w1, h1), centred at height zc."""
    box([(-w0, y0, zc - h0), (w0, y0, zc - h0), (w1, y1, zc - h1), (-w1, y1, zc - h1),
         (-w0, y0, zc + h0), (w0, y0, zc + h0), (w1, y1, zc + h1), (-w1, y1, zc + h1)], label)


# Post: square bar along a bent path, capped at both ends.
path = [Vector((0, 0.005, 0.835)), Vector((0, 0.005, 0.950)), Vector((0, -0.022, 1.008))]
half = 0.017
rings = []
for i, p in enumerate(path):
    d = (path[min(i + 1, 2)] - path[max(i - 1, 0)]).normalized()
    side = Vector((1, 0, 0)); up = d.cross(side).normalized()
    rings.append([new.verts.new(p + side * sx * half + up * sy * half) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
for a, b in zip(rings[:-1], rings[1:]):
    for k in range(4):
        new.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))[part] = 41
new.faces.new(list(reversed(rings[0])))[part] = 41
new.faces.new(rings[-1])[part] = 41

section(0.130, 0.0, 0.080, 0.037, 0.080, 0.037, HEAD_Z, 42)            # rear block
section(0.0, -0.160, 0.068, 0.032, 0.050, 0.023, HEAD_Z, 43)           # tapered nozzle
for dz in (-0.020, 0.0, 0.020):                                        # vent ridges on the back face
    section(0.138, 0.130, 0.064, 0.004, 0.064, 0.004, HEAD_Z + dz, 45)
# Lens: short cylinder along -Y in front of the nozzle, closed at the front.
SEG, R, Y0, Y1 = 12, 0.017, -0.158, -0.168
back_ring = [new.verts.new((R * math.cos(2 * math.pi * k / SEG), Y0, HEAD_Z + R * math.sin(2 * math.pi * k / SEG)))
             for k in range(SEG)]
front_ring = [new.verts.new((v.co.x * 0.9, Y1, HEAD_Z + (v.co.z - HEAD_Z) * 0.9)) for v in back_ring]
for k in range(SEG):
    new.faces.new((back_ring[k], back_ring[(k + 1) % SEG], front_ring[(k + 1) % SEG], front_ring[k]))[part] = 44
new.faces.new(list(reversed(front_ring)))[part] = 44
bmesh.ops.recalc_face_normals(new, faces=new.faces)

# UVs: planar projection of each face on its dominant plane, long side along u, shelf-packed into the top strip.
uv = new.loops.layers.uv.new('UVMap')
V0, V1, U0, U1, GAP = 0.952, 0.998, 0.004, 0.996, 0.003
items = []
for f in new.faces:
    n = f.normal
    axis = max(range(3), key=lambda i: abs(n[i]))
    a, b = [i for i in range(3) if i != axis]
    pts = [(l.vert.co[a], l.vert.co[b]) for l in f.loops]
    mu, mv = min(p[0] for p in pts), min(p[1] for p in pts)
    pts = [(p[0] - mu, p[1] - mv) for p in pts]
    w, h = max(p[0] for p in pts), max(p[1] for p in pts)
    if h > w:
        pts = [(p[1], p[0]) for p in pts]; w, h = h, w
    items.append((f, pts, w, h))
items.sort(key=lambda it: -it[3])
for density in (0.30, 0.26, 0.22, 0.18, 0.15, 0.12):
    x, y, shelf, placed, ok = U0, V0, 0.0, [], True
    for f, pts, w, h in items:
        if x + w * density > U1:
            x, y, shelf = U0, y + shelf + GAP, 0.0
        if y + h * density > V1:
            ok = False; break
        placed.append((f, pts, x, y)); x += w * density + GAP; shelf = max(shelf, h * density)
    if ok:
        break
for f, pts, x, y in placed:
    for l, p in zip(f.loops, pts):
        l[uv].uv = (x + p[0] * density, y + p[1] * density)
me = bpy.data.meshes.new('SensorNew'); new.to_mesh(me); new.free()
obj = bpy.data.objects.new('SensorNew', me); bpy.context.scene.collection.objects.link(obj)
group = obj.vertex_groups.new(name='Sensor'); group.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o in (robot, obj))
bpy.context.view_layer.objects.active = robot
bpy.ops.object.join()
sock = bpy.data.objects['Socket_Lens']
sock.matrix_world = Matrix.Translation(Vector((0, Y1 - 0.004, HEAD_Z)))
robot.data.calc_loop_triangles()
print('SENSOR rebuilt: density', density, 'tris', sum(len(p.vertices) - 2 for p in robot.data.polygons
                                                   if robot.data.attributes['part'].data[p.index].value >= 41),
      'total', len(robot.data.loop_triangles), 'unweighted', sum(1 for v in robot.data.vertices if not v.groups))
bpy.ops.wm.save_mainfile()
