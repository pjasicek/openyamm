"""Halberd carry: work/rig_v2.blend -> work/rig_v3.blend (after mm6_pmn2_claude/scripts/carry_staff.py).

Native guard (ANIMATION_STUDY.md, guastaa/guawal): one-handed low carry, right wrist at the thigh/low hip with the
elbow nearly straight, shaft near horizontal along the right side with the head forward and slightly low, blade flat
with the axe edge outward; the left arm hangs. Walking see-saws the shaft about the grip with the right arm swing:
hand ahead and up at the waist with the head raised 25-40 deg (walk a-c), hand back with the head down (d-f).

- Standing: new held clip (25 frames, static as the study asks) from the rest pose: left arm hung beside the thigh
  (free-arm IK), right arm solved onto the carry.
- Walking / Running: Meshy legs, spine, head and left arm; the right arm's own swing phase u in [-1, 1] drives grip
  forward offset, grip height and shaft pitch. The butt leans outward per frame just enough (smoothed) to keep the
  shaft 15 mm off the body.
The grip point is the least-wrist-strain grid point whose standing shaft clears the body by 2.5 cm; every solve adds
a blade cost so the blade stays flat with the axe outward. Per-frame numbers: work/carry_report.json."""
import bpy, sys, os, math, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
import gua_rig as gr

UP = Vector((0, 0, 1))
HIPS_REST_Z = (gr.AW @ gr.D('Hips').head_local).z
RIGHT, LEFT = gr.Side('Right'), gr.Side('Left')
MARGIN = 0.015
L, GRIP = gr.L, gr.GRIP_FROM_FOOT
CLIPS = {'Walking': {'pitch_amp': 28.0, 'fwd_amp': 0.10, 'lift': 0.06},
         'Running': {'pitch_amp': 22.0, 'fwd_amp': 0.12, 'lift': 0.08}}
PITCH0 = -8.0


def axis(F, R, pitch_deg, out):
    t = math.radians(pitch_deg)
    return (F * math.cos(t) + UP * math.sin(t) - R * out).normalized()      # head forward/in, butt back/out


def blade_cost(R, a):
    want = R.cross(a).normalized()
    def cost(Rh):
        shaft, n, axe = gr.halberd_frame(Rh)
        return 0.35 * math.degrees(n.angle(want))
    return cost


def target(lat, fwd, z, pitch, out):
    hips, F, R = gr.body_frame()
    G = Vector((hips.x, hips.y, 0)) + F * fwd + R * lat
    G.z = z + (hips.z - HIPS_REST_Z)
    a = axis(F, R, pitch, out)
    pole = UP * -0.6 - F * 0.6 + R * 0.4
    return G, a, pole, R


def clearance(P, G, a):
    return gr.shaft_clearance(P, G, a, below_grip=GRIP - 0.02, above_grip=L - GRIP - 0.30, radius=0.016)


# Standing: rest pose + hung left arm
arm = gr.arm
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
    pb.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
S = gr.AW @ gr.B('LeftArm').head
W = S + Vector((0.10, 0.01, -1)).normalized() * (LEFT.l1 + LEFT.l2) * 0.993
r = LEFT.free(W, Vector((0.3, 1.0, 0.0)))


def place(rr, side):
    for bn, R3, head in (('Arm', rr['Ra'], rr['S']), ('ForeArm', rr['Rf'], rr['E']), ('Hand', rr['Rh'], rr['W'])):
        pb = gr.B(side.s + bn)
        M = R3.to_4x4()
        M.translation = head
        pb.matrix = gr.AW.inverted() @ M
        bpy.context.view_layer.update()


place(r, LEFT)                                          # posed with no action attached, keyed below
P0 = gr.body_points()
grid = []
for lat in (0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30):
    for fwd in (-0.12, -0.08, -0.04, 0.0, 0.04, 0.08):
        for z in (0.74, 0.78, 0.82, 0.86):
            G, a, pole, R = target(lat, fwd, z, PITCH0, 0.06)
            rr = RIGHT.solve(G, a, pole, roll_cost=blade_cost(R, a))
            clr = clearance(P0, G, a)
            if clr >= 0.025 and rr['miss'] < 0.004:
                # native: upper arm by the ribs, wrist at the thigh -> prefer the hand close to the body
                grid.append((rr['cost'] + 0.3 * (clr * 1000 - 25), lat, fwd, z, round(rr['sw'], 1), round(rr['tw'], 1), round(clr * 1000)))
grid.sort()
print('GRID best', grid[:3])
_, LAT, FWD, Z = grid[0][:4]
G, a, pole, R = target(LAT, FWD, Z, PITCH0, 0.06)
rr = RIGHT.solve(G, a, pole, roll_cost=blade_cost(R, a))
place(rr, RIGHT)
pose = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones}
act = bpy.data.actions.new('Standing')
act.use_fake_user = True
arm.animation_data.action = act
for f in (0, 24):
    gr.set_pose(pose)
    gr.key_all(f)
gr.scene['gua_carry'] = json.dumps({'lat': LAT, 'fwd': FWD, 'z': Z, 'pitch': PITCH0})
report = {'Standing': {'wrist_swing': round(rr['sw'], 1), 'wrist_twist': round(rr['tw'], 1),
                       'clearance_mm': grid[0][6], 'miss_mm': round(rr['miss'] * 1000, 1)}}
print('STANDING', report['Standing'])

for name, cfg in CLIPS.items():
    act, (f0, f1) = gr.set_action(name)
    swing = []
    for f in range(f0, f1 + 1):
        gr.scene.frame_set(f)
        hips, F, R = gr.body_frame()
        v = (gr.AW @ gr.B('RightForeArm').head) - (gr.AW @ gr.B('RightArm').head)
        swing.append(math.degrees(math.atan2(v.dot(F), -v.z)))
    lo, hi = min(swing), max(swing)
    mid, amp = (lo + hi) / 2, max((hi - lo) / 2, 1e-3)
    U = [(x - mid) / amp for x in swing]
    need = []
    for i, f in enumerate(range(f0, f1 + 1)):
        gr.scene.frame_set(f)
        P = gr.body_points()
        u = U[i]
        out = 0.06
        while out < 0.40:
            G, a, pole, R = target(LAT, FWD + cfg['fwd_amp'] * u, Z + cfg['lift'] * max(u, 0.0),
                                   PITCH0 + cfg['pitch_amp'] * u, out)
            if clearance(P, G, a) >= MARGIN:
                break
            out += 0.02
        need.append(out)
    n = len(need)
    wide = [max(need[(i + k) % n] for k in range(-2, 3)) for i in range(n)]
    lean = [max(sum(wide[(i + k) % n] for k in range(-2, 3)) / 5, need[i]) for i in range(n)]
    phi = None
    rows = []
    for i, f in enumerate(range(f0, f1 + 1)):
        gr.scene.frame_set(f)
        u = U[i]
        G, a, pole, R = target(LAT, FWD + cfg['fwd_amp'] * u, Z + cfg['lift'] * max(u, 0.0),
                               PITCH0 + cfg['pitch_amp'] * u, lean[i])
        rr = RIGHT.solve(G, a, pole, phi, roll_cost=blade_cost(R, a))
        phi = rr['phi']
        RIGHT.apply(rr, f)
        rows.append({'f': f, 'u': round(u, 2), 'lean': round(lean[i], 2), 'wrist_swing': round(rr['sw'], 1),
                     'wrist_twist': round(rr['tw'], 1), 'reach_miss_mm': round(rr['miss'] * 1000, 1),
                     'butt_z': round((G - a * GRIP).z, 3)})
    report[name] = rows
    print('CARRY', name, 'wrist swing max %.1f twist max %.1f reach miss max %.1f mm butt z min %.3f lean max %.2f' % (
        max(r['wrist_swing'] for r in rows), max(abs(r['wrist_twist']) for r in rows),
        max(r['reach_miss_mm'] for r in rows), min(r['butt_z'] for r in rows), max(r['lean'] for r in rows)))
json.dump(report, open(os.path.join(common.WORK, 'carry_report.json'), 'w'), indent=0)
gr.set_action('Standing')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
