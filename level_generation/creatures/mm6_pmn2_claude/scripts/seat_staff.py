"""Seat the staff in the right fist of work/rig_v1.blend (rest pose) -> work/rig_v2.blend.
The fist tunnel is the line through the fist with the most clearance from fist vertices among lines the fist wraps
around (>= 12 of 16 angular sectors occupied within 2.5 cm of the clearance radius). The staff's grip point (29 %
from the top) sits on that line at its closest approach to the fist centre; the top end points to the thumb side
(forward in the rest pose).
A 'Staff' bone (child of RightHand, grip -> top) carries the staff (100 % weight), 'StaffTip' marks the head."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Mage_Rig']; mesh = bpy.data.objects['Mage']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(scene['pmn2_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
def tunnel(hand_part):
    """Largest-clearance line through a fist that its fingers wrap around (>= 12 of 16 sectors)."""
    vid = sorted({v for p in me.polygons if PARTS[part[p.index]] == hand_part for v in p.vertices})
    V = np.array([tuple(mesh.matrix_world @ me.vertices[i].co) for i in vid])
    c = V.mean(0)
    n = 900; ga = math.pi * (3 - math.sqrt(5))
    dirs = np.array([[math.cos(ga * k) * math.sqrt(1 - z * z), math.sin(ga * k) * math.sqrt(1 - z * z), z]
                     for k in range(n) for z in [1 - (k + 0.5) / n]])
    best = (0, None)
    offs = np.linspace(-0.025, 0.025, 21)
    for d in dirs:
        u = np.cross(d, [0, 0, 1] if abs(d[2]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u); w = np.cross(d, u)
        R = V - c; P2 = np.stack([R @ u, R @ w], 1)
        for a in offs:
            for b in offs:
                q = P2 - [a, b]; r = np.hypot(q[:, 0], q[:, 1])
                clr = r.min()
                if clr <= best[0]:
                    continue
                ring = r < clr + 0.025
                sect = np.unique(((np.arctan2(q[ring, 1], q[ring, 0]) + math.pi) / (2 * math.pi) * 16).astype(int) % 16)
                if len(sect) >= 12:
                    best = (clr, (d.copy(), c + a * u + b * w))
    clr, (d, p) = best
    d = Vector(d)
    if d.y > 0:                                         # rest pose: palm toward the thigh, thumb forward (-Y);
        d = -d                                          # Meshy's thumb bones lie along the knuckles on a fist
    return clr, d, Vector(p)


clr, d, p = tunnel('HandRight')
lclr, ld, lp = tunnel('HandLeft')
LH = (arm.matrix_world @ arm.data.bones['mixamorig:LeftHand'].matrix_local)
scene['pmn2_left_tunnel'] = json.dumps({'clearance_mm': round(lclr * 1000, 1), 'axis_hand': list(LH.to_3x3().inverted() @ ld),
                                        'centre_hand': list(LH.inverted() @ lp)})
print('LEFT TUNNEL clearance %.1f mm' % (lclr * 1000), 'axis', [round(x, 3) for x in ld])
print('TUNNEL clearance %.1f mm' % (clr * 1000), 'axis', [round(x, 3) for x in d], 'grip', [round(x, 3) for x in p])
# staff object, foot at z=0 along +Z -> world
with bpy.data.libraries.load(os.path.join(common.WORK, 'staff_v1.blend')) as (df, dt):
    dt.objects = ['Staff']
staff = dt.objects[0]; scene.collection.objects.link(staff)
L = staff['length']; grip = staff['grip_from_foot']
rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
staff.matrix_world = Matrix.Translation(p) @ rot @ Matrix.Translation((0, 0, -grip))
bpy.context.view_layer.update()
# bones
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
sb = eb.new('Staff'); sb.head = inv @ p; sb.tail = inv @ (p + d * (L - grip)); sb.parent = eb['mixamorig:RightHand']
sb.roll = 0; sb.use_deform = True
tb = eb.new('StaffTip'); tb.head = inv @ (p + d * (L - grip)); tb.tail = inv @ (p + d * (L - grip + 0.05)); tb.parent = sb
tb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
me_s = staff.data
staff_world = staff.matrix_world.copy()
for v in me_s.vertices:
    v.co = staff_world @ v.co
staff.matrix_world = Matrix.Identity(4)
staff.parent = arm; staff.matrix_parent_inverse = arm.matrix_world.inverted()
g = staff.vertex_groups.new(name='Staff'); g.add(list(range(len(me_s.vertices))), 1.0, 'REPLACE')
mod = staff.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
scene['pmn2_staff'] = json.dumps({'clearance_mm': round(clr * 1000, 1), 'axis': list(d), 'grip': list(p), 'length': L})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
h = p
for v in ('front', 'right', 'back', 'three_quarter'):
    common.render_views(os.path.join(common.REVIEW, 'seat'), float(h.z), 0.18, views=(v,), resolution=(350, 350), target=(float(h.x), float(h.y)))
common.render_views(os.path.join(common.REVIEW, 'seat_full'), 0.9, 2.0, views=('front', 'left'), resolution=(400, 500))
