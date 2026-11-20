"""Death and Dead, authored from the native keys (cledyi a-f): work/rig_v3.blend in place.

Meshy's library forward falls did not fit (184 starts from a raised-arm stance, swings the staff overhead, sinks up to
28 cm through the floor and ends curled on its side). Keys, in the rest-floor frame (character faces -Y):
 a f4  sways back;  b f8 slumps, knees giving, heels lifting;  c f11 on the knees (toes tucked), torso forward;
 d f15 toppling forward, hands reaching for the floor;  e f19 face down, legs straight behind, arms out, the staff on
 the floor beside the outstretched left hand (native corpse cledyif0), its heading the least wrist cost within 15
 deg of his axis.
Per frame: the Hips world position and forward pitch are interpolated (Catmull-Rom), the spine and head bend, both
legs are solved with two-bone IK onto ankle targets with an interpolated foot pitch (planted, then plantar-flexed
behind; an ankle rises when its toes would dip below the floor), the staff tilts so its foot drags on the floor as the hand drops, the staff arm is solved with
staff_rig.Side.solve and the right arm with the straight-wrist IK. A final pass lifts the
hips wherever the lowest body (not cloak) or staff vertex dips below the floor. 'Dead' is the last frame held.
The cloak is simulated afterwards (cloak_sim.py lays it on the floor)."""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
import staff_rig as sr
from author_lib import V, catmull, free_arm, staff_on_floor

arm = sr.arm; scene = sr.scene; AW = sr.AW
LEFT, RIGHT = sr.Side('Left'), sr.Side('Right')
CARRY = json.loads(scene['cle_carry'])
UP = V(0, 0, 1)
REST_HIPS = (AW @ sr.D('Hips').head_local).copy()
FLOOR_MIN = 0.0
TOE_THICK = 0.025
N = 20
ANK = {'Left': (AW @ sr.D('LeftFoot').head_local).copy(), 'Right': (AW @ sr.D('RightFoot').head_local).copy()}

# Ankles: from the knees down the shins lie on the floor behind the knees (each key's ankle is the hip joint's floor
# knee point plus a shin length back), so the knees stay on the floor while the hips topple forward.
# per key: hips position, hips forward pitch (deg), spine/head pitch (deg, + forward), ankle offset (y, z) from the
# rest ankle for both feet, foot pitch (deg, + toes down), knee hint, staff grip/axis/pole, right wrist/pole
KEYS = [
    {'f': 0, 'hips': REST_HIPS, 'pitch': 0.0, 'spine': 0.0, 'head': 0.0, 'ank': V(0, 0, 0), 'foot': 0.0,
     'knee': V(0, -1, -0.2), 'G': V(*CARRY['stand_grip']), 'a': UP, 'pole': V(0.3, 0.7, -0.6),
     'rW': V(-0.29, 0.0, 0.86), 'rpole': V(-0.4, 0.6, -0.6)},
    {'f': 4, 'hips': REST_HIPS + V(0, 0.03, -0.01), 'pitch': -4.0, 'spine': -5.0, 'head': -10.0, 'ank': V(0, 0, 0),
     'foot': 0.0, 'knee': V(0, -1, -0.2), 'G': V(0.50, -0.04, 1.10), 'a': V(0.10, 0.15, 0.98), 'pole': V(0.3, 0.7, -0.6),
     'rW': V(-0.30, 0.03, 0.88), 'rpole': V(-0.4, 0.6, -0.6)},
    {'f': 8, 'hips': REST_HIPS + V(0, -0.04, -0.24), 'pitch': 10.0, 'spine': 10.0, 'head': 5.0, 'ank': V(0, 0.02, 0.03),
     'foot': 25.0, 'knee': V(0, -1, -0.4), 'G': V(0.46, -0.24, 0.92), 'a': V(0.30, -0.40, 0.86), 'pole': V(0.4, 0.6, -0.6),
     'rW': V(-0.30, -0.12, 0.66), 'rpole': V(-0.4, 0.6, -0.6)},
    {'f': 11, 'hips': V(0.014, -0.16, 0.53), 'pitch': 22.0, 'spine': 18.0, 'head': 0.0, 'ank': V(0, 0.30, 0.0),
     'foot': 120.0, 'knee': V(0, -1, -0.5), 'G': V(0.42, -0.40, 0.58), 'a': V(0.40, -0.25, 0.88), 'pole': V(0.5, 0.4, -0.6),
     'rW': V(-0.32, -0.38, 0.48), 'rpole': V(-0.6, 0.4, -0.5)},
    {'f': 15, 'hips': V(0.014, -0.42, 0.33), 'pitch': 55.0, 'spine': 18.0, 'head': -20.0, 'ank': V(0, 0.32, -0.02),
     'foot': 140.0, 'knee': V(0, -1, -0.5), 'G': V(0.40, -0.92, 0.28), 'a': V(0.0, -0.90, 0.45),
     'pole': V(0.6, 0.3, -0.5), 'rW': V(-0.36, -0.95, 0.26), 'rpole': V(-0.6, 0.3, 0.2)},
    {'f': 19, 'hips': V(0.014, -0.70, 0.19), 'pitch': 88.0, 'spine': 2.0, 'head': -10.0, 'ank': V(0, 0.16, -0.03),
     'foot': 165.0, 'knee': V(0, -1, -0.5), 'G': V(0.62, -1.12, 0.055), 'a': V(0.12, -1.0, 0.0),
     'pole': V(0.3, 0.2, 1.0), 'rW': V(-0.46, -1.02, 0.09), 'rpole': V(-0.2, 0.3, 1.0)},
    {'f': 20, 'hips': V(0.014, -0.70, 0.19), 'pitch': 88.0, 'spine': 2.0, 'head': -10.0, 'ank': V(0, 0.16, -0.03),
     'foot': 165.0, 'knee': V(0, -1, -0.5), 'G': V(0.62, -1.12, 0.055), 'a': V(0.12, -1.0, 0.0),
     'pole': V(0.3, 0.2, 1.0), 'rW': V(-0.46, -1.02, 0.09), 'rpole': V(-0.2, 0.3, 1.0)},
]
REST_HIPS_M = (AW @ sr.D('Hips').matrix_local).copy()
REST_FOOT_M = {s: (AW @ sr.D(s + 'Foot').matrix_local).copy() for s in ('Left', 'Right')}


def pose_frame(f, lift=0.0, phi=None):
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    hips = catmull(KEYS, 'hips', f, None) + V(0, 0, lift)
    pitch = catmull(KEYS, 'pitch', f, None)
    R = Matrix.Rotation(math.radians(pitch), 4, 'X')
    M = Matrix.Translation(hips) @ R @ Matrix.Translation(-REST_HIPS) @ REST_HIPS_M
    sr.B('Hips').matrix = AW.inverted() @ M
    bpy.context.view_layer.update()
    sp = catmull(KEYS, 'spine', f, None)
    for bone in ('Spine01', 'Spine'):
        sr.rotate_bone_world(bone, V(1, 0, 0), sp / 2)
    sr.rotate_bone_world('Head', V(1, 0, 0), catmull(KEYS, 'head', f, None))
    ank = catmull(KEYS, 'ank', f, None); fp = catmull(KEYS, 'foot', f, None); kn = catmull(KEYS, 'knee', f, None)
    for side in ('Left', 'Right'):
        A = ANK[side] + ank + V(0, 0, lift * 0.5)
        Fm = Matrix.Translation(A) @ Matrix.Rotation(math.radians(fp), 4, 'X') @ Matrix.Translation(-ANK[side]) \
            @ REST_FOOT_M[side]
        Fm.translation = A
        sr.leg_ik(side, Fm, kn, None)
        # curling toes: raise the ankle, not the hips. Toe tip estimated along ankle -> toe joint (Meshy's bone tails
        # are guesses and lifted the knees to 0.5 m)
        ank_w = AW @ sr.B(side + 'Foot').head; toe_w = AW @ sr.B(side + 'ToeBase').head
        tz = min(toe_w.z, (toe_w + (toe_w - ank_w) * 0.6).z) - TOE_THICK
        if tz < 0:
            Fm.translation = A + V(0, 0, -tz)
            sr.leg_ik(side, Fm, kn, None)
    G = catmull(KEYS, 'G', f, None) + V(0, 0, lift); a = catmull(KEYS, 'a', f, None).normalized()
    a = staff_on_floor(G, a)
    r = LEFT.solve(G, a, catmull(KEYS, 'pole', f, None), phi, steps=72)
    for bn, R3, head in (('Arm', r['Ra'], r['S']), ('ForeArm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
        pb = sr.B('Left' + bn); Mb = R3.to_4x4(); Mb.translation = head; pb.matrix = AW.inverted() @ Mb
        bpy.context.view_layer.update()
    free_arm(RIGHT, catmull(KEYS, 'rW', f, None) + V(0, 0, lift), catmull(KEYS, 'rpole', f, None), None)
    return r


_PARTS = json.loads(scene['cle_parts'])
_part = [0] * len(sr.me.polygons)
sr.me.attributes['part'].data.foreach_get('value', _part)
_REG = json.loads(scene['cle_uv_regions'])
_ureg = [0] * len(sr.me.polygons)
sr.me.attributes['uv_region'].data.foreach_get('value', _ureg)
# the tunic skirt follows the thighs into the floor while kneeling; it is cloth under the ground, not a floor contact
BODY_V = sorted({v for p in sr.me.polygons if _PARTS[_part[p.index]] != 'Cloak'
                 and _REG[_ureg[p.index]] not in ('SkirtF', 'SkirtB', 'Hidden') for v in p.vertices})


def lowest():
    """Lowest body (not cloak, kept above the floor by cloak_sim.py; not the tunic skirt) or staff vertex."""
    dg = bpy.context.evaluated_depsgraph_get()
    e = sr.mesh.evaluated_get(dg); m = e.to_mesh()
    low = min((sr.mesh.matrix_world @ m.vertices[i].co).z for i in BODY_V); e.to_mesh_clear()
    st = bpy.data.objects['Staff']; e = st.evaluated_get(dg); m = e.to_mesh()
    low = min(low, min((st.matrix_world @ v.co).z for v in m.vertices)); e.to_mesh_clear()
    return low


# the lying staff's heading on the floor: least wrist cost among forward headings within 15 deg of the body's axis,
# the arm
# out to the side on the floor (a fixed forward heading twisted the wrist 77 deg; free headings put the ring under
# his shoulder)
best = None
for deg in range(0, 360, 10):
    a = V(math.sin(math.radians(deg)), -math.cos(math.radians(deg)), 0.0)
    if abs(a.x) > math.sin(math.radians(15)) or a.y > 0:      # ring forward, as it falls (no 150 deg sweep)
        continue
    for k in KEYS[-2:]:
        k['a'] = a
    r = pose_frame(19)
    if best is None or r['cost'] < best[0]:
        best = (r['cost'], deg, a, round(r['sw'], 1), round(r['tw'], 1))
for k in KEYS[-2:]:
    k['a'] = best[2]
print('LYING staff heading', best[1], 'deg; wrist swing', best[3], 'twist', best[4])
for name in ('Death', 'Dead'):
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
act = bpy.data.actions.new('Death'); act.use_fake_user = True
phi = None; rows = []
for f in range(N + 1):
    r = pose_frame(f, 0.0, phi)
    low = lowest(); lift = max(0.0, FLOOR_MIN - low)
    if lift > 0:
        r = pose_frame(f, lift, phi)
    phi = r['phi']
    sr.key_pose(act, f)
    rows.append({'f': f, 'lift_mm': round(lift * 1000, 1), 'lowest_after': round(lowest(), 3),
                 'wrist_swing': round(r['sw'], 1), 'wrist_twist': round(r['tw'], 1), 'miss_mm': round(r['miss'] * 1000, 1)})
flips = sr.fix_quaternion_signs(act)
final = sr.sample_pose('Death', N); sr.detach()
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True
sr.set_pose(final)
for f in (0, 1):
    sr.key_pose(dead, f)
print('DEATH', json.dumps(rows), 'flips', flips)
json.dump(rows, open(os.path.join(common.WORK, 'death_report.json'), 'w'), indent=0)
sr.set_action('Standing')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
