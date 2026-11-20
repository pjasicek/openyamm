"""Two daggers for the thief, modelled from the Crude Dagger icon (assets_dev/engine/icons_x2/item021.png) at the
size of the native attack frames (plain silver blade about 1/9 of body height): straight diamond-section blade
16 cm x 2.6 cm, short cross guard, wrapped grip 8.5 cm, round pommel; about 150 triangles each.
Seated on the grip axis solved by fist_solve.py (the fist closes on it in the attack; in the rest pose the hand is
open and the dagger is hidden by its bone scale), hammer grip: the blade leaves the thumb/index side at GRIP_DEG to the forearm (the handle
diagonal across the palm), so a forward thrust points it forward. Bones DaggerL / DaggerR (children of the hands, grip -> point) carry the daggers (100 % weight); the
daggers join the mesh as part 'Dagger'. Saves work/rig_v1.blend in place."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
BLADE, BLADE_W, BLADE_T = 0.16, 0.026, 0.0055
GRIP_R, GRIP_L, GUARD_W = 0.0105, 0.085, 0.062
GRIP_DEG = 55.0           # blade angle to the forearm in the closed fist (90 = crosswise)


def dagger_mesh(name):
    """Dagger along +Y (grip centre at the origin, point at +Y), blade width along X, flats facing +-Z."""
    bm = bmesh.new()

    def ring(y, r, n=8, sx=1.0, sz=1.0):
        return [bm.verts.new((r * sx * math.cos(2 * math.pi * k / n), y, r * sz * math.sin(2 * math.pi * k / n)))
                for k in range(n)]

    def bridge(a, b):
        for k in range(len(a)):
            bm.faces.new((a[k], a[(k + 1) % len(a)], b[(k + 1) % len(a)], b[k]))

    def cap(r, y, up):
        c = bm.verts.new((0, y, 0))
        for k in range(len(r)):
            bm.faces.new((r[k], r[(k + 1) % len(r)], c) if not up else (r[(k + 1) % len(r)], r[k], c))

    # pommel and grip
    g0 = ring(-GRIP_L / 2 - 0.012, 0.006); p1 = ring(-GRIP_L / 2 - 0.006, 0.014); g1 = ring(-GRIP_L / 2, GRIP_R)
    g2 = ring(GRIP_L / 2, GRIP_R)
    cap(g0, -GRIP_L / 2 - 0.016, False); bridge(g0, p1); bridge(p1, g1); bridge(g1, g2)
    # guard (flattened ring, wide along X)
    q0 = ring(GRIP_L / 2, 1.0, 8, GUARD_W / 2, 0.008); q1 = ring(GRIP_L / 2 + 0.012, 1.0, 8, GUARD_W / 2, 0.008)
    bridge(q0, q1); cap(q0, GRIP_L / 2, False); cap(q1, GRIP_L / 2 + 0.012, True)
    # blade: diamond sections (edge, spine, edge, spine), tapering to the point
    y0 = GRIP_L / 2 + 0.012
    secs = []
    for t, wf in ((0.0, 1.0), (0.35, 0.95), (0.7, 0.75), (0.9, 0.4)):
        y = y0 + BLADE * t; w = BLADE_W / 2 * wf; th = BLADE_T / 2 * (0.4 + 0.6 * wf)
        secs.append([bm.verts.new(c) for c in ((w, y, 0), (0, y, th), (-w, y, 0), (0, y, -th))])
    for a, b in zip(secs, secs[1:]):
        bridge(a, b)
    tip = bm.verts.new((0, y0 + BLADE, 0))
    for k in range(4):
        bm.faces.new((secs[-1][k], secs[-1][(k + 1) % 4], tip))
    cap(secs[0], y0, False)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(name, m); scene.collection.objects.link(o)
    return o


FIST = json.loads(scene['thf_fist'])
seat = {}
for side, sd in (('Left', 'L'), ('Right', 'R')):
    f = FIST[sd]
    k = Vector(f['axis']).normalized()                  # fist axis (knuckle line); thumb/index side = +k
    a = Vector(f['width_axis']); a = (a - k * a.dot(k)).normalized()      # wrist -> fingertips of the open hand
    # hammer grip: the handle runs diagonally across the palm, so the blade leaves the thumb side GRIP_DEG from the
    # forearm, leaning toward the fingertips (exactly crosswise, every downswing led with the butt and a thrust
    # pointed the blade up: user review, "he only shows off his knives")
    d = (k * math.sin(math.radians(GRIP_DEG)) + a * math.cos(math.radians(GRIP_DEG))).normalized()
    p = Vector(f['grip']) - d * (GRIP_L / 2 - 0.02)     # the fist (~4 cm wide) holds the upper part of the grip
    xw = (a - d * a.dot(d)).normalized()                # edges in the plane of fist axis and fingers
    flat = d.cross(xw).normalized()
    o = dagger_mesh('Dagger' + sd)
    R = Matrix((xw, d, flat)).transposed().to_4x4()
    M = Matrix.Translation(p) @ R
    for v in o.data.vertices:
        v.co = M @ v.co
    seat[sd] = {'axis': list(d), 'grip': list(p), 'width_axis': list(xw)}
    print('SEAT', side, {k_: [round(x, 3) for x in v] for k_, v in seat[sd].items()})
bpy.context.view_layer.objects.active = arm
for x in bpy.data.objects:
    x.select_set(x == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
for side, sd in (('Left', 'L'), ('Right', 'R')):
    s = seat[sd]; d = Vector(s['axis']); p = Vector(s['grip'])
    b = eb.new('Dagger' + sd); b.head = inv @ p; b.tail = inv @ (p + d * (GRIP_L / 2 + 0.012 + BLADE))
    b.parent = eb[side + 'Hand']; b.align_roll(inv.to_3x3() @ Vector(s['width_axis'])); b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
# join into the body mesh, 100 % on the dagger bones, part 'Dagger'
if 'Dagger' not in PARTS:
    PARTS.append('Dagger'); scene['thf_parts'] = json.dumps(PARTS)
di = PARTS.index('Dagger')
for sd in ('L', 'R'):
    o = bpy.data.objects['Dagger' + sd]
    g = o.vertex_groups.new(name='Dagger' + sd); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    a = o.data.attributes.new('part', 'INT', 'FACE'); a.data.foreach_set('value', [di] * len(o.data.polygons))
    if 'Dagger' + sd not in mesh.vertex_groups:
        mesh.vertex_groups.new(name='Dagger' + sd)
for x in bpy.data.objects:
    x.select_set(x.name in ('Thief', 'DaggerL', 'DaggerR'))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
scene['thf_daggers'] = json.dumps(seat)
print('JOINED tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
from mathutils import Euler, Quaternion
for sd, f in FIST.items():
    for j, ang in enumerate(f['fing']):
        arm.pose.bones[f'Fing{sd}{j + 1}'].rotation_mode = 'QUATERNION'
        arm.pose.bones[f'Fing{sd}{j + 1}'].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(ang))
    arm.pose.bones[f'Thumb{sd}1'].rotation_mode = 'QUATERNION'; arm.pose.bones[f'Thumb{sd}2'].rotation_mode = 'QUATERNION'
    arm.pose.bones[f'Thumb{sd}1'].rotation_quaternion = Euler(tuple(math.radians(x) for x in f['thumb'][:3])).to_quaternion()
    arm.pose.bones[f'Thumb{sd}2'].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(f['thumb'][3]))
bpy.context.view_layer.update()
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
for sd in ('L', 'R'):
    h = Vector(seat[sd]['grip'])
    for v in ('front', 'right' if sd == 'R' else 'left', 'three_quarter'):
        common.render_views(os.path.join(common.REVIEW, 'dagger_seat_' + sd), float(h.z), 0.3, views=(v,),
                            resolution=(400, 400), target=(float(h.x), float(h.y)))
