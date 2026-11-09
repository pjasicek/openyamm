"""Arm and hand gate for an Attack clip of a centaur master (humanoid playbook "Arm and hand gate", numbers on every
frame): wrist swing (forearm vs hand axis) per side, forearm twist about the forearm against the rest pose and its
frame-to-frame change, forearm/hand/finger vertices inside the torso (nearest torso face, signed by its normal),
draw-hand to nock distance while drawing, lowest body point, and the largest per-frame bone rotation step (pops).
Usage: blender -b -P attack_gate.py -- <master.blend> <out.json> [action=Attack]"""
import bpy, bmesh, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]; action = args[2] if len(args) > 2 else 'Attack'
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = bpy.data.actions[action]; rig.animation_data.action_slot = rig.animation_data.action.slots[0]
pb = rig.pose.bones; rest = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}
names = [g.name for g in body.vertex_groups]
dom = []
for v in body.data.vertices:
    g = max(v.groups, key=lambda x: x.weight, default=None); dom.append(names[g.group] if g else '')
ARM = lambda n: n[:1] in 'LR' and any(k in n for k in ('ForeArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))
TORSO = {'Spine', 'Spine1', 'Chest', 'Neck', 'Head', 'HorseChest', 'HorseSpine'}
arm_v = [i for i, n in enumerate(dom) if ARM(n)]
torso_f = [p.index for p in body.data.polygons if all(dom[i] in TORSO for i in p.vertices)]
f0, f1 = (int(x) for x in rig.animation_data.action.frame_range)
rows = []; prev = {}; worst_step = (0, '', 0)


def twist(side):
    fa = pb[side + 'ForeArm'].matrix.to_3x3().normalized(); h = pb[side + 'Hand'].matrix.to_3x3().normalized()
    # hand X expressed against the forearm's X after removing the swing (rest offset subtracted)
    rel = fa.inverted() @ h; rrel = rest[side + 'ForeArm'].inverted() @ rest[side + 'Hand']
    q = (rrel.inverted() @ rel).to_quaternion(); axis = Vector((0, 1, 0))
    tw = math.degrees(2 * math.atan2(Vector(q[1:]).dot(axis), q[0]))
    return (tw + 180) % 360 - 180


def twist2(parent, child):
    rel = pb[parent].matrix.to_3x3().normalized().inverted() @ pb[child].matrix.to_3x3().normalized()
    q = ((rest[parent].inverted() @ rest[child]).inverted() @ rel).to_quaternion()
    return (math.degrees(2 * math.atan2(q[2], q[0])) + 180) % 360 - 180


wrap = lambda x: abs((x + 180) % 360 - 180)
for f in range(f0, f1 + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    co = [body.matrix_world @ v.co for v in me.vertices]
    bm = bmesh.new(); bm.verts.ensure_lookup_table()
    verts = [bm.verts.new(co[i]) for i in range(len(co))]; bm.verts.ensure_lookup_table()
    for fi in torso_f:
        try:
            bm.faces.new([verts[i] for i in me.polygons[fi].vertices])
        except ValueError:
            pass
    tree = BVHTree.FromBMesh(bm); deep = 0.; count = 0
    for i in arm_v:
        hit = tree.find_nearest(co[i], .08)
        if hit[0] is not None:
            s = (co[i] - hit[0]).dot(hit[1])
            if s < -.004:
                count += 1; deep = max(deep, -s)
    bm.free(); ev.to_mesh_clear()
    row = {'f': f, 'arm_in_torso_vertices': count, 'arm_in_torso_depth_mm': round(deep * 1000, 1),
           'lowest_z_mm': round(min(c.z for c in co) * 1000, 1)}
    for s in 'LR':
        fa = pb[s + 'ForeArm'].tail - pb[s + 'ForeArm'].head; h = pb[s + 'Hand'].tail - pb[s + 'Hand'].head
        row['wrist_' + s] = round(math.degrees(fa.angle(h)), 1); row['twist_' + s] = round(twist(s), 1)
        row['elbow_twist_' + s] = round(twist2(s + 'Arm', s + 'ForeArm'), 1)
    row['nock_to_finger_mm'] = round((pb['StringNock'].head - pb['RIndex3'].tail).length * 1000, 1)
    # bow plane (Bow bone: limbs along +Y, string at local -Z, plane normal local X) against the shot line, from the
    # grip to the drawn nock while the string is off its rest, else to the base of the neck (the chest side)
    Bm = pb['Bow'].matrix.to_3x3().normalized(); grip = pb['Bow'].head
    rest_nock = pb['Bow'].matrix @ (rig.data.bones['Bow'].matrix_local.inverted() @ rig.data.bones['StringNock'].head_local)
    drawn = (pb['StringNock'].head - rest_nock).length > .02
    shot = ((pb['StringNock'].head if drawn else pb['Neck'].head) - grip).normalized()
    row['bow_normal_to_shot_deg'] = round(math.degrees(Bm.col[0].angle(shot)), 1)
    row['bow_string_side'] = round((-Bm.col[2]).dot(shot), 2)      # +1: string toward the archer, -1: away
    row['bow_drawn'] = drawn
    frame_step = ('', 0.)
    for b in pb:
        if b.name in ('Arrow', 'StringNock', 'StringTop', 'StringBottom'):
            continue
        q = b.matrix.to_quaternion()
        if b.name in prev:
            step = math.degrees(prev[b.name].rotation_difference(q).angle); step = min(step, 360 - step)
            if step > worst_step[2]:
                worst_step = (f, b.name, round(step, 1))
            if step > frame_step[1]:
                frame_step = (b.name, round(step, 1))
        prev[b.name] = q
    row['largest_step'] = frame_step
    rows.append(row)
summary = {'action': action, 'frames': [f0, f1],
           'max_wrist_L': max(r['wrist_L'] for r in rows), 'max_wrist_R': max(r['wrist_R'] for r in rows),
           'frames_wrist_over_60': [r['f'] for r in rows if max(r['wrist_L'], r['wrist_R']) > 60],
           'max_abs_twist_L': max(abs(r['twist_L']) for r in rows), 'max_abs_twist_R': max(abs(r['twist_R']) for r in rows),
           'max_abs_elbow_twist_L': max(abs(r['elbow_twist_L']) for r in rows), 'max_abs_elbow_twist_R': max(abs(r['elbow_twist_R']) for r in rows),
           'max_twist_step': max(max(wrap(rows[i][k + s] - rows[i - 1][k + s]) for s in 'LR' for k in ('twist_', 'elbow_twist_')) for i in range(1, len(rows))),
           'max_arm_in_torso_depth_mm': max(r['arm_in_torso_depth_mm'] for r in rows),
           'frames_arm_in_torso_over_10mm': [r['f'] for r in rows if r['arm_in_torso_depth_mm'] > 10],
           'lowest_z_mm': min(r['lowest_z_mm'] for r in rows), 'largest_bone_step': worst_step,
           'bow_plane_off_deg_max': max(abs(90 - r['bow_normal_to_shot_deg']) for r in rows),
           'bow_string_side_min': min(r['bow_string_side'] for r in rows)}
json.dump({'summary': summary, 'rows': rows}, open(out, 'w'), indent=1)
print('GATE', json.dumps(summary))
