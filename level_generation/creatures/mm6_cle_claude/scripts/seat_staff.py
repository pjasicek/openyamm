"""Seat the staff in the LEFT fist of work/rig_v1.blend (rest pose) -> work/rig_v2.blend; adapted from
mm6_pmn2_claude/scripts/seat_staff.py. The fist vertices are those 100 % on a Hand bone (build_rig_cle.py).
The fist tunnel is the line through the fist with the most clearance from fist vertices among lines the fist wraps
around (>= 12 of 16 angular sectors occupied within 2.5 cm of the clearance radius), among directions within
~20 deg of perpendicular to the forearm and within ~30 deg of front-to-back, where both fists' finger rings open
(unrestricted, the left fist's best line ran diagonally past it, then sideways under the knuckles). The staff's grip point
(1.08 m from the foot) sits on that line at its closest approach to the fist centre; the head points to the thumb
side (forward in the rest pose). The right fist's tunnel is stored too (scene['cle_right_tunnel']).
A 'Staff' bone (child of LeftHand, grip -> head) carries the staff (100 % weight); 'StaffTip' sits at the ring
centre (missile and spell origin)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def fist_verts(bone):
    g = mesh.vertex_groups[bone].index
    return [v.index for v in me.vertices if any(x.group == g and x.weight > 0.999 for x in v.groups)]


def tunnel(bone):
    """Largest-clearance line through a fist that its fingers wrap around (>= 12 of 16 sectors)."""
    V = np.array([tuple(mesh.matrix_world @ me.vertices[i].co) for i in fist_verts(bone)])
    c = V.mean(0)
    fore = arm.data.bones[bone].head_local - arm.data.bones[bone.replace('Hand', 'ForeArm')].head_local
    fore = np.array((arm.matrix_world.to_3x3() @ fore).normalized())
    n = 1800; ga = math.pi * (3 - math.sqrt(5))
    dirs = np.array([[math.cos(ga * k) * math.sqrt(1 - z * z), math.sin(ga * k) * math.sqrt(1 - z * z), z]
                     for k in range(n) for z in [1 - (k + 0.5) / n]])
    dirs = dirs[(np.abs(dirs @ fore) < 0.34) & (np.abs(dirs[:, 1]) > 0.85)]   # the fists' holes run front to back
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
    if d.y > 0:                                         # rest pose: thumb forward (-Y)
        d = -d
    return clr, d, Vector(p), len(V)


clr, d, p, nl = tunnel('LeftHand')
rclr, rd, rp, nr = tunnel('RightHand')
RH = (arm.matrix_world @ arm.data.bones['RightHand'].matrix_local)
scene['cle_right_tunnel'] = json.dumps({'clearance_mm': round(rclr * 1000, 1), 'axis_hand': list(RH.to_3x3().inverted() @ rd),
                                        'centre_hand': list(RH.inverted() @ rp)})
print('RIGHT TUNNEL clearance %.1f mm' % (rclr * 1000), 'axis', [round(x, 3) for x in rd], 'fist verts', nr)
print('TUNNEL clearance %.1f mm' % (clr * 1000), 'axis', [round(x, 3) for x in d], 'grip', [round(x, 3) for x in p],
      'fist verts', nl)
with bpy.data.libraries.load(os.path.join(common.WORK, 'staff_v1.blend')) as (df, dt):
    dt.objects = ['Staff']
staff = dt.objects[0]; scene.collection.objects.link(staff)
L = staff['length']; grip = staff['grip_from_foot']; head_c = staff['head_centre']
rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
staff.matrix_world = Matrix.Translation(p) @ rot @ Matrix.Translation((0, 0, -grip))
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
sb = eb.new('Staff'); sb.head = inv @ p; sb.tail = inv @ (p + d * (L - grip)); sb.parent = eb['LeftHand']
sb.roll = 0; sb.use_deform = True
tb = eb.new('StaffTip'); tb.head = inv @ (p + d * (head_c - grip)); tb.tail = inv @ (p + d * (head_c - grip + 0.05))
tb.parent = sb; tb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
me_s = staff.data
staff_world = staff.matrix_world.copy()
for v in me_s.vertices:
    v.co = staff_world @ v.co
staff.matrix_world = Matrix.Identity(4)
staff.parent = arm; staff.matrix_parent_inverse = arm.matrix_world.inverted()
g = staff.vertex_groups.new(name='Staff'); g.add(list(range(len(me_s.vertices))), 1.0, 'REPLACE')
mod = staff.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
scene['cle_staff'] = json.dumps({'clearance_mm': round(clr * 1000, 1), 'axis': list(d), 'grip': list(p), 'length': L,
                                 'grip_from_foot': grip, 'head_centre': head_c})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
for v in ('front', 'left', 'back', 'three_quarter'):
    common.render_views(os.path.join(common.REVIEW, 'seat'), float(p.z), 0.18, views=(v,), resolution=(350, 350),
                        target=(float(p.x), float(p.y)))
common.render_views(os.path.join(common.REVIEW, 'seat_full'), 0.9, 2.2, views=('front', 'left'), resolution=(400, 500))
