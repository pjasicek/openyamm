"""Seat the halberd in the right fist of work/rig_v1.blend (rest pose) -> work/rig_v2.blend (adapted from
mm6_pmn2_claude/scripts/seat_staff.py).
The fist tunnel is the line through the fist with the most clearance from fist vertices among lines the fist wraps
around (>= 12 of 16 angular sectors occupied within 2.5 cm of the clearance radius). The halberd's grip point (56 %
from the butt, native carry) sits on that line at its closest approach to the fist centre; the head points to the
thumb side (forward in the rest pose) and the blade lies flat with the axe edge outward (character right, -X), as in
the native standing carry. The left fist's tunnel is stored for two-handed poses.
A 'Halberd' bone (child of RightHand, grip -> gem) carries the halberd (100 % weight), 'HalberdTip' marks the gem."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(scene['gua_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)


def tunnel(hand_part, cone=35.0):
    """The fist's see-through hole: among lines within `cone` deg of forward/back (a palm-in fist's hole runs along
    the knuckle line) through a grid around the fist centre, keep those that cross the fist without hitting a face and
    that the fist encloses (8 perpendicular rays from the line's closest point to the centre all hit within 3 cm);
    return the one with the most clearance (nearest-face distance sampled along the line)."""
    from mathutils.bvhtree import BVHTree
    fis = [p for p in me.polygons if PARTS[part[p.index]] == hand_part
           and all(abs((mesh.matrix_world @ me.vertices[i].co).x) > 0.50 for i in p.vertices)]
    vid = sorted({i for p in fis for i in p.vertices})
    remap = {v: k for k, v in enumerate(vid)}
    W = [mesh.matrix_world @ me.vertices[i].co for i in vid]
    tree = BVHTree.FromPolygons(W, [[remap[i] for i in p.vertices] for p in fis])
    c = sum(W, Vector()) / len(W)
    n = 3000; ga = math.pi * (3 - math.sqrt(5))
    dirs = []
    for k in range(n):
        z = 1 - (k + 0.5) / n
        d = Vector((math.cos(ga * k) * math.sqrt(1 - z * z), math.sin(ga * k) * math.sqrt(1 - z * z), z))
        if d.y < -math.cos(math.radians(cone)):
            dirs.append(d)
    best = (0.0, None)
    offs = [x * 0.002 for x in range(-15, 16)]
    for d in dirs:
        u = d.cross(Vector((0, 0, 1))).normalized(); w = d.cross(u)
        for a in offs:
            for b in offs:
                o = c + u * a + w * b
                if tree.ray_cast(o - d * 0.12, d, 0.24)[0] is not None:
                    continue                            # blocked: not a see-through line
                ok = True
                for k in range(8):
                    ang = 2 * math.pi * k / 8
                    r = u * math.cos(ang) + w * math.sin(ang)
                    if tree.ray_cast(o, r, 0.03)[0] is None:
                        ok = False
                        break
                if not ok:
                    continue
                clr = min(tree.find_nearest(o + d * t)[3] for t in (-0.03, -0.015, 0.0, 0.015, 0.03))
                if clr > best[0]:
                    best = (clr, (d.copy(), o.copy()))
    clr, (d, p) = best
    return clr, d, p, vid


def widen(vid, d, p, radius, half_len=0.06):
    """Push fist vertices closer than `radius` to the tunnel line radially out to it (rigid fist, rest pose)."""
    inv = mesh.matrix_world.inverted(); n = 0
    for i in vid:
        w = mesh.matrix_world @ me.vertices[i].co
        r = w - p; t = r.dot(d)
        if abs(t) > half_len:
            continue
        radial = r - d * t
        if radial.length < radius:
            w = p + d * t + radial.normalized() * radius
            me.vertices[i].co = inv @ w; n += 1
    me.update()
    return n


with bpy.data.libraries.load(os.path.join(common.WORK, 'halberd_v1.blend')) as (df, dt):
    dt.objects = ['Halberd']
hal = dt.objects[0]; scene.collection.objects.link(hal)
SHAFT_R = max(math.hypot(v.co.x, v.co.y) for v in hal.data.vertices if 0.3 < v.co.z / hal['length'] < 0.65)
clr, d, p, rvid = tunnel('ArmRight')
lclr, ld, lp, lvid = tunnel('ArmLeft')
print('WIDEN right', widen(rvid, d, p, SHAFT_R + 0.002), 'left', widen(lvid, ld, lp, SHAFT_R + 0.002), 'verts; shaft r',
      round(SHAFT_R * 1000, 1), 'mm')
LH = (arm.matrix_world @ arm.data.bones['LeftHand'].matrix_local)
scene['gua_left_tunnel'] = json.dumps({'clearance_mm': round(lclr * 1000, 1), 'axis_hand': list(LH.to_3x3().inverted() @ ld),
                                        'centre_hand': list(LH.inverted() @ lp)})
print('LEFT TUNNEL clearance %.1f mm' % (lclr * 1000), 'axis', [round(x, 3) for x in ld])
print('TUNNEL clearance %.1f mm' % (clr * 1000), 'axis', [round(x, 3) for x in d], 'grip', [round(x, 3) for x in p])
# halberd object, butt at z=0 along +Z, axe toward -X -> world: +Z to the tunnel axis, axe outward (-X)
L = hal['length']; grip = hal['grip_from_butt']
zx = d.normalized(); out = Vector((-1, 0, 0)); out = (out - zx * out.dot(zx)).normalized()
xl = -out                                               # local +X (spike side) points inward
yl = zx.cross(xl)
rot = Matrix((xl, yl, zx)).transposed().to_4x4()
hal.matrix_world = Matrix.Translation(p) @ rot @ Matrix.Translation((0, 0, -grip))
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
sb = eb.new('Halberd'); sb.head = inv @ p; sb.tail = inv @ (p + d * (L - grip)); sb.parent = eb['RightHand']
sb.align_roll(inv.to_3x3() @ yl); sb.use_deform = True
tb = eb.new('HalberdTip'); tb.head = inv @ (p + d * (L - grip)); tb.tail = inv @ (p + d * (L - grip + 0.05)); tb.parent = sb
tb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
me_s = hal.data
hw = hal.matrix_world.copy()
for v in me_s.vertices:
    v.co = hw @ v.co
hal.matrix_world = Matrix.Identity(4)
hal.parent = arm; hal.matrix_parent_inverse = arm.matrix_world.inverted()
g = hal.vertex_groups.new(name='Halberd'); g.add(list(range(len(me_s.vertices))), 1.0, 'REPLACE')
mod = hal.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
scene['gua_halberd'] = json.dumps({'clearance_mm': round(clr * 1000, 1), 'axis': list(d), 'grip': list(p), 'length': L,
                                   'grip_from_butt': grip})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
h = p
for v in ('front', 'right', 'back', 'three_quarter'):
    common.render_views(os.path.join(common.REVIEW, 'seat'), float(h.z), 0.18, views=(v,), resolution=(350, 350), target=(float(h.x), float(h.y)))
common.render_views(os.path.join(common.REVIEW, 'seat_full'), 0.9, 2.0, views=('front', 'left'), resolution=(400, 500))
