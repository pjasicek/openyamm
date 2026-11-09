"""Death and Dead from Meshy's Dying Backwards (DyingSrc, library 189): work/rig_v5.blend -> work/rig_v6.blend.

Native guadtha..e + guadthf0 (ANIMATION_STUDY.md): left palm to the face, back sway, balance failure, backward drop,
curled on the side/back; the right hand keeps the halberd out to the right and it ends on the floor outside the body.
Meshy's clip (hunch with a hand at the face, buckle, fall onto the back, arms out) matches; source frames 4..44 play
at source speed (1.67 s, frames 0..40; 2026-10-10: the engine finishes a longer death, it was 1.67x in 1.0 s). Its right arm would pull the halberd through the body, so the right arm is solved
per frame onto chest-relative keys: carry -> shaft upright at the side -> arm out and forward -> arm out with the shaft
toward the head end -> lying beside the body. Over the last 40 % the grip sinks to 4 cm above the floor, the shaft
levels and the blade rolls flat (Halberd bone). A constant Hips offset per frame keeps every body vertex >= 0.
Dead holds the last frame. Per-frame numbers: work/death_report.json."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v5.blend'))
import gua_rig as gr

arm, AW = gr.arm, gr.AW
UP = Vector((0, 0, 1))
F0, R0 = Vector((0, -1, 0)), Vector((-1, 0, 0))
RIGHT = gr.Side('Right')
SRC0, SRC1, N = 4, 44, 40
CARRY = json.loads(gr.scene['gua_carry'])

act, (s0, s1) = gr.set_action('DyingSrc')
src = []
for k in range(N + 1):
    t = SRC0 + (SRC1 - SRC0) * k / N
    gr.scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    src.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones})
arm.animation_data.action = None
CH = 'Spine'
rest_ch = gr.rest3(CH)
Fl, Rl, Ul = rest_ch.inverted() @ F0, rest_ch.inverted() @ R0, rest_ch.inverted() @ UP


def chest():
    M = AW @ gr.B(CH).matrix
    R3 = M.to_3x3().normalized()
    return M.translation.copy(), (R3 @ Fl).normalized(), (R3 @ Rl).normalized(), (R3 @ Ul).normalized()


# carry grip/axis in the rest chest frame
c0 = AW @ gr.D(CH).head_local
hips0 = AW @ gr.D('Hips').head_local
cg = Vector((hips0.x, hips0.y, 0)) + R0 * CARRY['lat'] + F0 * CARRY['fwd'] + UP * CARRY['z']
tp = math.radians(CARRY['pitch'])
ca = (F0 * math.cos(tp) + UP * math.sin(tp) - R0 * 0.06).normalized()
carry_off = (cg - c0)
KEYS = [  # t, hand offset (f, r, u) from the chest, axis (f, r, u), pole (f, r, u)
    (0.00, (carry_off.dot(F0), carry_off.dot(R0), carry_off.dot(UP)), (ca.dot(F0), ca.dot(R0), ca.dot(UP)), (-0.6, 0.4, -0.6)),
    (0.15, (0.12, 0.32, -0.15), (0.0, 0.15, 1.0), (-0.3, 1.0, -0.5)),
    (0.40, (0.22, 0.45, -0.12), (0.2, 0.5, 0.8), (-0.3, 1.0, -0.4)),
    (0.70, (0.12, 0.55, -0.05), (0.0, 0.4, 0.9), (-0.2, 1.0, -0.2)),
    (1.00, (0.05, 0.55, 0.05), (0.0, 0.3, 0.95), (-0.2, 1.0, 0.0)),
]


def at(t):
    i = max(j for j in range(len(KEYS)) if KEYS[j][0] <= t) if t < 1 else len(KEYS) - 2
    u = (t - KEYS[i][0]) / (KEYS[i + 1][0] - KEYS[i][0])
    u = u * u * (3 - 2 * u)
    return [tuple(a + (b - a) * u for a, b in zip(KEYS[i][j], KEYS[i + 1][j])) for j in (1, 2, 3)]


mesh = gr.mesh
hal = bpy.data.objects['Halberd']


def lowest(obj, point=False):
    dg = bpy.context.evaluated_depsgraph_get()
    em = obj.evaluated_get(dg).to_mesh()
    p = min((obj.matrix_world @ v.co for v in em.vertices), key=lambda q: q.z)
    obj.evaluated_get(dg).to_mesh_clear()
    return (p.z, p) if point else p.z


poses, rows = [], []
phi = None
prev = (None, None)
for k in range(N + 1):
    t = k / N
    gr.set_pose(src[k])
    low = lowest(mesh)                                  # body never below the floor
    if low < 0.0:
        hips = gr.B('Hips')
        M = AW @ hips.matrix
        M.translation.z -= low
        hips.matrix = AW.inverted() @ M
        bpy.context.view_layer.update()
    c, Fc, Rc, Uc = chest()
    ho, ax, po = at(t)
    G = c + Fc * ho[0] + Rc * ho[1] + Uc * ho[2]
    a = (Fc * ax[0] + Rc * ax[1] + Uc * ax[2]).normalized()
    pole = (Fc * po[0] + Rc * po[1] + Uc * po[2]).normalized()
    w = max(0.0, (t - 0.6) / 0.4)
    w = w * w * (3 - 2 * w)
    if w > 0:
        G.z = G.z + (0.04 - G.z) * w if G.z > 0.04 else G.z
        flat = Vector((a.x, a.y, 0)).normalized() if Vector((a.x, a.y)).length > 1e-3 else a
        a = a.lerp(flat, w).normalized()
    lift = 0
    while True:
        rr = RIGHT.search([(G, a, 'k')], pole, phi, steps=72, angles=(-60, -30, 0, 30, 60), share=0.8,
                          prev_ft=prev[0], prev_E=prev[1], torso=gr.torso_penalty())
        for bn, R3, head in (('Arm', rr['Ra'], rr['S']), ('ForeArm', rr['Rf'], rr['E']), ('Hand', rr['Rh'], rr['W'])):
            pb = gr.B('Right' + bn)
            M = R3.to_4x4()
            M.translation = head
            pb.matrix = AW.inverted() @ M
            bpy.context.view_layer.update()
        shaft, n, axe = gr.halberd_frame(rr['Rh'])
        if n.z < 0:
            n = -n
        roll = math.atan2(n.cross(UP).dot(shaft), n.dot(UP)) * w if w > 0 else 0.0
        hb = gr.B('Halberd')
        hb.rotation_mode = 'QUATERNION'
        hb.rotation_quaternion = Quaternion((0, 1, 0), roll)
        bpy.context.view_layer.update()
        hz = lowest(hal)
        if hz >= 0.008 or lift >= 12:
            break
        side = a.cross(UP)                              # tilt the low end up about the grip
        lo_end = 1 if (lowest(hal, True)[1] - G).dot(a) > 0 else -1     # +1: the low point is on the gem side
        if side.length < 1e-3:
            break
        a = Quaternion(side.normalized(), math.radians(6 * lo_end)) @ a
        if hz < -0.0 and G.z < 0.03:
            G.z += 0.01
        lift += 1
    phi, prev = rr['phi'], (rr['ft'], rr['E'] - rr['S'])
    low = lowest(mesh)
    if low < 0.0:
        hips = gr.B('Hips')
        M = AW @ hips.matrix
        M.translation.z -= low
        hips.matrix = AW.inverted() @ M
        bpy.context.view_layer.update()
        hz = lowest(hal)
    rows.append({'f': k, 'lift_steps': lift, 'sw': round(rr['sw'], 1), 'tw': round(rr['tw'], 1), 'ft': round(rr['ft'], 1),
                 'miss_mm': round(rr['miss'] * 1000, 1), 'halberd_low_z': round(hz, 3), 'body_low_z': round(lowest(mesh), 3)})
    poses.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones})
for name, frames in (('Death', range(N + 1)), ('Dead', (N, N))):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for i, k in enumerate(frames):
        gr.set_pose(poses[k])
        gr.key_all(i)
    print(name, 'quaternion flips fixed', gr.fix_quaternion_signs(act))
for r in rows:
    print('DTH', r)
json.dump(rows, open(os.path.join(common.WORK, 'death_report.json'), 'w'), indent=0)
gr.set_action('Death')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v6.blend'))
