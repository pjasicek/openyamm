"""Walk2 and Run2 for the MM7 spider (2026-10-21 creature post-process), after mm6_spi1_claude/scripts/gait2_spi1.py.

The engine plays one loop per stride of travel, so the look depends only on the stride; the clips are authored at the
speeds the game moves the spider (gait_gate.py targets: walk 1.99-3.45, run 3.98-6.91 model units/s, fit middles 2.62
and 5.24), with strides the legs can actually cover. Same rig and tetrapod as anim_spider.py (L1 R2 L3 R4 / R1 L2 R3 L4),
but:
  - each leg's foothold is planned for its sweep (stride x duty): pulled in or shifted along the body so hip-to-ankle
    stays between FOLD and REACH of the femur + tibia over the whole stance (the front legs rest almost straight);
  - the planted tarsus tip is the contact point and sits on the floor (each tarsus piece's lowest vertex at +2 mm);
    the tarsus turns about its tip with the leg's azimuth, so long sweeps roll over the foot instead of skating;
  - a small metachronal lead from the back legs to the front ones;
  - Run2 lowers and levels the body, reaches longer and lifts the feet higher.
Keys at 60 fps. Reads work/anim_v2u.blend (unchanged), saves work/gait2.blend and writes the two clips (only) to the GLB
given as argument, to be grafted onto the installed export with ../../claude_shared/graft_clips.py.
Args: -- <out clips.glb>"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v2u.blend'))
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']
FPS = 60
SIZE = 1.2                                   # half the leg span (m): scales poles, lifts and bobs
FLOOR_CLEAR = 0.002                          # planted tarsus piece's lowest vertex above the floor
BODY_CLEAR = 0.005                           # the body (thorax, abdomen, fangs) stays this high: it is raised to it
REACH, FOLD = 0.96, 0.08                     # hip-to-ankle over femur + tibia: at most REACH, at least the leg's
#                                              folded limit |femur - tibia| / (femur + tibia) + FOLD
CLIPS = {
    # name: speed (model units/s), frames at 60 fps, duty, swing lift, body lift/crouch, bob, yaw, roll, pitch, lead
    'Walk2': dict(speed=2.62, frames=25, duty=0.55, lift=0.17, base=0.012, bob=0.012, yaw=2.0, roll=1.5, pitch=0.0,
                  lead=0.03, abdomen=3.0, pair_duty={'1': 0.8}),
    'Run2': dict(speed=5.24, frames=18, duty=0.45, lift=0.22, base=-0.02, bob=0.02, yaw=2.5, roll=2.0, pitch=0.0,
                 lead=0.02, abdomen=5.0, abdomen_lift=3.0, pair_duty={'1': 0.8}),
}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = [f'{s}{i}' for s in 'LR' for i in range(1, 5)]
GROUP_A = ('L1', 'R2', 'L3', 'R4')
P.reset(rig)
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
W = rig.matrix_world
REST_FOOT = {leg: (W @ rig.pose.bones[f'Tarsus_{leg}'].tail).copy() for leg in LEGS}
REST_ANKLE = {leg: (W @ rig.pose.bones[f'Tarsus_{leg}'].head).copy() for leg in LEGS}
REST_KNEE = {leg: (W @ rig.pose.bones[f'Tibia_{leg}'].head).copy() for leg in LEGS}
REST_HIP = {leg: (W @ rig.pose.bones[f'Femur_{leg}'].head).copy() for leg in LEGS}
REST_TARSUS = {leg: rig.pose.bones[f'Tarsus_{leg}'].matrix.to_quaternion() for leg in LEGS}
CHAIN = {leg: rig.pose.bones[f'Femur_{leg}'].length + rig.pose.bones[f'Tibia_{leg}'].length for leg in LEGS}
TARSUS_VEC = {leg: REST_FOOT[leg] - REST_ANKLE[leg] for leg in LEGS}
# at least 0.6: a more folded leg lays its tibia low, and the fringe card under it (rigged to the leg in the reduced
# export, mm7_m402_reduce_claude) cut the floor by 4 cm
MIN_RATIO = {leg: max(0.6, abs(rig.pose.bones[f'Femur_{leg}'].length - rig.pose.bones[f'Tibia_{leg}'].length)
                      / CHAIN[leg] + FOLD) for leg in LEGS}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- mesh and floor
_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


REST_CO = mesh_co()
# planted tip height: the tarsus bone tail sits so its piece's lowest vertex is FLOOR_CLEAR above the floor
TIP_Z = {leg: REST_FOOT[leg].z - REST_CO[_dom == f'Tarsus_{leg}', 2].min() + FLOOR_CLEAR for leg in LEGS}
NOT_TARSUS = ~np.char.startswith(_dom.astype(str), 'Tarsus')
BODY = np.isin(_dom, ('Thorax', 'Abdomen', 'Fang_L', 'Fang_R'))


# ---------------------------------------------------------------- footholds
def plan(leg, sweep, lift):
    """Foothold centre (x, y) for a stance sweep along Y: rest foot pulled in radially (r) and shifted along the body
    (dy) so the hip-to-ankle distance stays in [FOLD, REACH] x chain over the sweep; least change from rest wins."""
    hip = REST_HIP[leg] + Vector((0, 0, lift))
    foot = REST_FOOT[leg]
    best = None
    for r in np.linspace(0.86, 1.05, 20):  # pulled in at most 14 %
        for dy in np.linspace(-0.6, 0.6, 61) * SIZE:
            cx, cy = hip.x + (foot.x - hip.x) * r, hip.y + (foot.y - hip.y) * r + dy
            ratios = []
            for k in np.linspace(-0.5, 0.5, 11):
                tip = Vector((cx, cy + k * sweep, TIP_Z[leg]))
                ankle = tip - TARSUS_VEC[leg]
                ratios.append((ankle - hip).length / CHAIN[leg])
            cost = 100 * max(0.0, max(ratios) - REACH) + 100 * max(0.0, MIN_RATIO[leg] - min(ratios)) + abs(r - 1) + abs(dy) / SIZE
            if best is None or cost < best[0]:
                best = (cost, cx, cy, min(ratios), max(ratios), r, dy)
    return best


# ---------------------------------------------------------------- posing
def body(lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, abdomen=0.0):
    root = rig.pose.bones['Thorax']
    root.matrix = Matrix.Translation(Vector((0, 0, lift))) @ root.matrix
    bpy.context.view_layer.update()
    if roll:
        P.rotate_world(rig, 'Thorax', Y, roll)
    if pitch:
        P.rotate_world(rig, 'Thorax', X, -pitch)
    if yaw:
        P.rotate_world(rig, 'Thorax', Z, yaw)
    if abdomen:
        P.rotate_world(rig, 'Abdomen', X, abdomen)


def azimuth(v):
    return math.atan2(v.y, v.x)


def place_tip(leg, tip, curl=0.0):
    """IK the leg so the tarsus tip reaches `tip`; the tarsus turns about the vertical with the leg's azimuth (it
    rolls over its planted tip) and pitches its tip down by `curl` degrees in swing."""
    hip = W @ rig.pose.bones[f'Femur_{leg}'].head
    turn = Quaternion(Z, 0.0)
    for _ in range(3):                                     # the ankle depends on the turn, the turn on the ankle
        rot = turn
        if curl:
            side = Vector((tip.x - hip.x, tip.y - hip.y, 0)).normalized().cross(Z)
            rot = Quaternion(side, -math.radians(curl)) @ turn   # tip folds down and in
        ankle = tip - rot @ TARSUS_VEC[leg]
        turn = Quaternion(Z, azimuth(ankle - hip) - azimuth(REST_ANKLE[leg] - REST_HIP[leg]))
    knee = REST_KNEE[leg]
    out = Vector((knee.x, knee.y, 0)).normalized()
    pole = W @ rig.pose.bones[f'Femur_{leg}'].head + (knee - REST_HIP[leg]) + out * 0.3 * SIZE + Z * 0.7 * SIZE
    P.two_bone_ik(rig, f'Femur_{leg}', f'Tibia_{leg}', ankle, pole)
    tarsus = rig.pose.bones[f'Tarsus_{leg}']
    tarsus.matrix = Matrix.LocRotScale(tarsus.head.copy(), rot @ REST_TARSUS[leg], Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    return ((W @ tarsus.tail) - tip).length


# Leg vertices that hang to the floor at rest (fringe cards under the tibiae): their positions in the reduced export,
# rigid on their dominant bone. A planted foot whose tibia would push one through the floor is raised instead (the card
# hangs from the tibia's far end, so any tibia pitch from rest lowers it).
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared', 'floor'))
import glb_pose
_g = glb_pose.Glb(os.path.join(HERE, '..', 'mm7_m402_reduce_claude', 'export', 'mm7_m402.glb'))
_m = glb_pose.Model(_g)
_prim = _m.primitives[0]
_gnames = [n.get('name') for n in _g.json['nodes']]
HANGING = {}
for _i in np.where(_prim['positions'][:, 1] < 0.06)[0]:
    _bone = _gnames[_m.joints[_prim['joints'][_i][np.argmax(_prim['weights'][_i])]]]
    if _bone.startswith(('Femur_', 'Tibia_')):
        _x, _y, _z = (float(v) for v in _prim['positions'][_i])
        local = rig.data.bones[_bone].matrix_local.inverted() @ Vector((_x, -_z, _y))
        HANGING.setdefault(_bone[-2:], []).append((_bone, local))
print('HANGING', {k: len(v) for k, v in HANGING.items()}, flush=True)


def hanging_low(leg):
    return min(((W @ rig.pose.bones[b].matrix @ local).z for b, local in HANGING.get(leg, [])), default=1.0)


def leg_duty(c, leg):
    """Stance share of a leg: the clip's duty, times the clip's per-pair factor (a pair with a shorter stance sweeps
    less ground: sweep = stride x duty)."""
    return c['duty'] * c.get('pair_duty', {}).get(leg[1], 1.0)


def gait(p, c, centres, stride):
    P.reset(rig)
    body(lift=c['base'] + c['bob'] * math.cos(4 * math.pi * p) - c['bob'], pitch=c['pitch'],
         roll=c['roll'] * math.sin(2 * math.pi * p), yaw=c['yaw'] * math.sin(2 * math.pi * p),
         abdomen=c.get('abdomen_lift', 0.0) + c['abdomen'] * (0.5 + 0.5 * math.sin(4 * math.pi * p + 0.6)))  # tip up only
    miss = 0.0
    for leg in LEGS:
        duty = leg_duty(c, leg)
        s = stride * duty
        q = (p + (0.0 if leg in GROUP_A else 0.5) + c['lead'] * (int(leg[1]) - 1)) % 1.0
        cx, cy = centres[leg]
        if q < duty:
            y = cy - s / 2 + s * (q / duty); z = 0.0; curl = 0.0
        else:
            u = (q - duty) / (1 - duty)
            y = cy + s / 2 - s * ss(u); z = c['lift'] * math.sin(math.pi * u) ** 0.8; curl = 25 * math.sin(math.pi * u)
        m = place_tip(leg, Vector((cx, y, TIP_Z[leg] + z)), curl)
        for _ in range(4):
            low = hanging_low(leg)
            if low >= HANG_CLEAR:
                break
            z += HANG_CLEAR - low
            FLOATS[leg] = max(FLOATS.get(leg, 0.0), z if q < duty else 0.0)
            m = place_tip(leg, Vector((cx, y, TIP_Z[leg] + z)), curl)
        if m > 0.005:
            MISSES.setdefault(leg, []).append((round(p, 2), round(q, 2), round(m * 1000, 1)))
        miss = max(miss, m)
    return miss


MISSES = {}
FLOATS = {}
HANG_CLEAR = -0.005


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, body_lows, miss = [], [], [], 0.0
    for f in range(n + 1):
        miss = max(miss, fn((f % n) / n))
        co = mesh_co()
        lows.append(float(co[:, 2].min())); body_lows.append(float(co[BODY, 2].min()))
        if os.environ.get('GAIT_DEBUG') and lows[-1] < -0.002:
            i = np.where(NOT_TARSUS)[0][np.argmin(co[NOT_TARSUS, 2])]
            print(f'LOW {name} f{f}: {_dom[i]} {co[i].round(3)} rest {REST_CO[i].round(3)}', flush=True)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act, min(lows), max(lows), miss, min(body_lows)


info = {}
for name, c in CLIPS.items():
    T = c['frames'] / FPS
    stride = c['speed'] * T
    centres = {}
    for leg in LEGS:
        cost, cx, cy, lo, hi, r, dy = plan(leg, stride * leg_duty(c, leg), c['base'])
        centres[leg] = (cx, cy)
        print(f'PLAN {name} {leg}: r {r:.2f} dy {dy:+.3f} hip-ankle {lo:.2f}-{hi:.2f} of chain', flush=True)
    for attempt in range(4):                                   # raise the body until it clears the floor
        act, low, high, miss, body_low = key_action(name, c['frames'], lambda p: gait(p, c, centres, stride))
        if body_low >= BODY_CLEAR - 1e-4:
            break
        c['base'] += BODY_CLEAR - body_low
        print(f'RAISE {name}: body lowest {body_low * 100:+.2f} cm, base now {c["base"]:+.4f}', flush=True)
    info[name] = {'seconds': T, 'stride': round(stride, 4), 'authored_speed': c['speed'], 'sweep': stride * c['duty'],
                  'lowest': [low, high], 'tip_miss': miss, 'base': c['base'], 'body_lowest': body_low}
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f} m, sweep {stride * c["duty"]:.3f} m, lowest vertex '
          f'{low * 100:+.2f}..{high * 100:+.2f} cm, body {body_low * 100:+.2f} cm, worst tip miss {miss * 1000:.1f} mm',
          flush=True)
    for leg, rows in MISSES.items():
        print(f'MISS {name} {leg}: {rows[:6]}', flush=True)
    MISSES.clear()
    print(f'FLOAT {name}: planted feet raised for hanging cards (max cm) ' +
          ', '.join(f'{k} {v * 100:.1f}' for k, v in sorted(FLOATS.items())), flush=True)
    info[name]['planted_raise_cm'] = {k: round(v * 100, 2) for k, v in FLOATS.items()}
    FLOATS.clear()
json.dump(info, open(os.path.join(HERE, 'work', 'gait2_info.json'), 'w'), indent=1)
P.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'gait2.blend'))
for a in list(bpy.data.actions):
    if a.name not in CLIPS:
        bpy.data.actions.remove(a)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
