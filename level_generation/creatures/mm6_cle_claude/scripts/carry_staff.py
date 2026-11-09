"""Standing clip and the staff carry on the locomotion clips: work/rig_v2.blend -> work/rig_v3.blend; adapted from
mm6_pmn2_claude/scripts/carry_staff.py (staff in the LEFT hand).

Standing pose (keyed by author_clips.py): the left arm is solved onto the native standing staff (clesta0-2): upright
beside the left foot, foot on the floor, the arm reaching out to the side (grip STAND_GRIP). The staff mesh is rolled
about its own axis so the ring faces forward in this pose (flat in the native front view, edge-on in the profile).
Walking/Running (Meshy; the run as a jog, legs at RUN_LEG, hips re-levelled): per frame the staff is placed in the body's heading frame: upright at the left side, grip
CARRY_Z above the rest floor moving with the hips, tilted forward per clip, swept with the right arm's swing (its foot
trails the stepping left leg) and its foot leaned outward per frame just enough (smoothed) to keep the shaft MARGIN
off the legs, skirt and cloak. The grip position is the least-wrist-strain grid point whose first-frame shaft clears
the body by 3 cm. Legs, spine, head and the right arm stay Meshy's. Per-frame numbers: work/carry_report.json."""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
import staff_rig as sr

STAND_GRIP = Vector((0.50, -0.12, sr.GRIP_FROM_FOOT))
STAND_FRAMES = 48
CLIPS = {'Walking': {'tilt': 4, 'sweep': 0.35}, 'Running': {'tilt': 12, 'sweep': 0.25}}
CARRY_Z, FOOT_CLEAR, MARGIN = sr.GRIP_FROM_FOOT + 0.05, 0.02, 0.015
HIPS_REST_Z = (sr.AW @ sr.D('Hips').head_local).z
LEFT = sr.Side('Left')
arm = sr.arm; scene = sr.scene


def clear_pose():
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()


# the native standing staff (Standing itself is keyed by author_clips.py), solved detached for the ring roll
clear_pose()
UP = Vector((0, 0, 1))
POLE_STAND = Vector((0.3, 0.7, -0.6))
r = LEFT.solve(STAND_GRIP, UP, POLE_STAND, None)
LEFT.apply(r)
print('STANDING wrist swing %.1f twist %.1f reach miss %.1f mm' % (r['sw'], r['tw'], r['miss'] * 1000))
stand_rows = [{'wrist_swing': round(r['sw'], 1), 'wrist_twist': round(r['tw'], 1)}]

# roll the staff mesh about its axis so the ring plane faces forward in Standing (ring normal ~ -Y)
staff = bpy.data.objects['Staff']
Ms = sr.AW @ sr.B('Staff').matrix                          # posed bone, world
Mr = sr.AW @ sr.D('Staff').matrix_local                     # rest bone, world
ring_n_rest = Vector((0, 1, 0))                            # make_staff: ring in local X-Z, seen open from local -Y
rot_rest = Vector((0, 0, 1)).rotation_difference(Vector(sr.ST['axis'])).to_matrix()
n_rest = rot_rest @ ring_n_rest                            # ring normal at seating (world rest)
n_pose = (Ms.to_3x3() @ Mr.to_3x3().inverted()) @ n_rest
axis_pose = (Ms.to_3x3() @ Vector((0, 1, 0))).normalized()
want = Vector((0, -1, 0)); want = (want - axis_pose * want.dot(axis_pose)).normalized()
have = (n_pose - axis_pose * n_pose.dot(axis_pose)).normalized()
ang = math.atan2(have.cross(want).dot(axis_pose), have.dot(want))
axis_rest = Vector(sr.ST['axis']); grip_rest = Vector(sr.ST['grip'])
R = Matrix.Translation(grip_rest) @ Matrix.Rotation(ang, 4, axis_rest) @ Matrix.Translation(-grip_rest)
for v in staff.data.vertices:
    v.co = R @ v.co
staff.data.update()
print('STAFF ROLL %.1f deg' % math.degrees(ang))


def staff_axis(F, Rt, tilt_deg, out):
    t = math.radians(tilt_deg)
    return (UP * math.cos(t) + F * math.sin(t) + Rt * out).normalized()        # head in, foot out to his left


def carry_target(tilt, out, lat, fwd):
    hips, F, Rt = sr.body_frame()
    a = staff_axis(F, Rt, tilt, out)
    G = Vector((hips.x, hips.y, 0)) + F * fwd - Rt * lat
    G.z = max(CARRY_Z + (hips.z - HIPS_REST_Z), FOOT_CLEAR + a.z * sr.GRIP_FROM_FOOT)
    pole = Vector((0, 0, -1)) * 0.6 - F * 0.6 - Rt * 0.4
    return G, a, pole


RUN_LEG = 0.65
LEGS = [s + b for s in ('Left', 'Right') for b in ('UpLeg', 'Leg')]


def jog_legs():
    """A jog, not a sprint: Meshy's run kicks the back heel up through the cloak (viewer, rear, frame 4); knee and
    thigh swing kept at RUN_LEG about the bind pose (as the thief's run, mm6_thf_claude/scripts/build_clips_thf.py)."""
    for n in LEGS:
        pb = sr.B(n); q = pb.rotation_quaternion.copy()
        if q.w < 0:
            q = -q
        pb.rotation_quaternion = Quaternion().slerp(q, RUN_LEG)
    bpy.context.view_layer.update()


def relevel(act, f0, f1):
    """Hips offset so the lowest sole of the clip is on the floor again (shorter strides change it)."""
    sr.set_action(act.name)
    low = 1e9
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for side in ('Left', 'Right'):
            low = min(low, (sr.AW @ sr.B(side + 'ToeBase').head).z, (sr.AW @ sr.B(side + 'Foot').head).z - 0.07)
    sole0 = min((sr.AW @ sr.D(s_ + 'ToeBase').head_local).z for s_ in ('Left', 'Right'))
    dz = sole0 - low
    for f in range(f0, f1 + 1):
        sr.sample_detached(act.name, f)
        hips = sr.B('Hips'); M = sr.AW @ hips.matrix; M = Matrix.Translation((0, 0, dz)) @ M
        hips.matrix = sr.AW.inverted() @ M; bpy.context.view_layer.update()
        sr.key_pose(act, f)
    print('RUN relevel hips %+.3f m' % dz)


sr.set_action('Walking'); scene.frame_set(0)
P0 = sr.body_points(); grid = []
for lat in (0.32, 0.36, 0.40):                       # native walk: staff ~0.38 m out
    for fwd in (0.04, 0.10, 0.16, 0.22):
        G, a, pole = carry_target(CLIPS['Walking']['tilt'], 0.02, lat, fwd)
        r = LEFT.solve(G, a, pole)
        clr = sr.shaft_clearance(P0, G, a)
        if clr >= 0.03:
            grid.append((r['cost'], lat, fwd, round(r['sw'], 1), round(r['tw'], 1), round(clr * 1000)))
grid.sort()
print('GRID best', grid[:3])
LAT, FWD = grid[0][1], grid[0][2]
scene['cle_carry'] = json.dumps({'lat': LAT, 'fwd': FWD, 'grip_z': CARRY_Z, 'stand_grip': list(STAND_GRIP)})
report = {'Standing': stand_rows}
for name, cfg in CLIPS.items():
    act, (f0, f1) = sr.set_action(name)
    swing = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); hips, F, Rt = sr.body_frame()
        v = (sr.AW @ sr.B('RightForeArm').head) - (sr.AW @ sr.B('RightArm').head)
        swing.append(math.degrees(math.atan2(v.dot(F), -v.z)))
    mean = sum(swing) / len(swing)
    sweeps = [max(-10, min(10, cfg['sweep'] * (x - mean))) for x in swing]
    need = []
    for i, f in enumerate(range(f0, f1 + 1)):
        scene.frame_set(f); P = sr.body_points(); out = 0.02
        while out < 0.30:
            G, a, pole = carry_target(cfg['tilt'] + sweeps[i], out, LAT, FWD)
            if sr.shaft_clearance(P, G, a) >= MARGIN:
                break
            out += 0.01
        need.append(out)
    n = len(need)
    wide = [max(need[(i + k) % n] for k in range(-2, 3)) for i in range(n)]
    lean = [max(sum(wide[(i + k) % n] for k in range(-2, 3)) / 5, need[i]) for i in range(n)]
    phi = None; rows = []
    for i, f in enumerate(range(f0, f1 + 1)):
        sr.sample_detached(name, f)
        if name == 'Running':
            jog_legs()
        G, a, pole = carry_target(cfg['tilt'] + sweeps[i], lean[i], LAT, FWD)
        r = LEFT.solve(G, a, pole, phi); phi = r['phi']
        LEFT.apply(r)
        sr.key_pose(act, f)
        rows.append({'f': f, 'lean': round(lean[i], 2), 'wrist_swing': round(r['sw'], 1), 'wrist_twist': round(r['tw'], 1),
                     'reach_miss_mm': round(r['miss'] * 1000, 1), 'staff_foot_z': round((G - a * sr.GRIP_FROM_FOOT).z, 3)})
    if name == 'Running':
        relevel(act, f0, f1)
    report[name] = rows
    print('CARRY', name, 'wrist swing max %.1f twist max %.1f reach miss max %.1f mm staff foot z min %.3f' % (
        max(r['wrist_swing'] for r in rows), max(abs(r['wrist_twist']) for r in rows),
        max(r['reach_miss_mm'] for r in rows), min(r['staff_foot_z'] for r in rows)))
json.dump(report, open(os.path.join(common.WORK, 'carry_report.json'), 'w'), indent=0)
sr.set_action('Walking')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
