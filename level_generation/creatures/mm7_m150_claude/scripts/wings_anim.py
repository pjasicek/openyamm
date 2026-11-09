"""Wing motion per clip (wings_rig.py chains Wing_<s>_1..3 on B_Spine2), matched against the native m150 frames.
Each bone's pose is a rotation relative to its rest, composed from angles about the REST armature axes (they move with
the parent): elev (tip up, about the body's forward axis), sweep (tip forward, about the vertical axis) and twist
(about the lateral axis, leading edge down). Signs per side so +elev raises both wings and +sweep brings both forward.
- Standing (native sa: wings spread high): the rest spread lowered REST_ELEV deg, a slow breath (+-3 deg, one cycle).
- Walking (native wa..wh, 1.0 s: top at wa, bottom at wc/wd, rising we..wh): elev = mid + amp cos(2 pi t), the outer
  bones lag a quarter beat (they trail on the downstroke and fold slightly back on the upstroke); the beat is biased
  down (FLAP_MID) so the upstroke stays low (playbook: flyers' ceilings).
- Attack (native aa..ah): wings rise with the sword (to +ATT_UP at the top of the wind-up), beat down through the blow
  (to ATT_DOWN at the impact), back to the stance by the end.
- Hit (native na..nf: wings thrown up and out): +HIT_UP at 0.12 s, back by the end.
- Fidget (native fa..fd: wings spread wide with the sword raised): a slow full spread and forward sweep at mid-clip.
- Death (native da..dd, xa: wings fold up, the body falls back, the corpse lies on its back with the wings spread flat
  at both sides): wings rise with the arms, then ease into a corpse pose found by search on the last frame (sweep
  forward on the root = up when lying on the back, outer bones bent back down onto the floor) so every wing vertex is
  >= FLOOR above the floor with the least mean height; per frame of the fall the blend toward it is raised until the
  wings clear the floor. Dead is not an action here (export_runtime holds the Death end).
All one-shot clips blend from and to the Standing wing pose at their ends. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
REST_ELEV, FLAP_MID, FLAP_AMP = E('REST_ELEV', -8), E('FLAP_MID', -10), E('FLAP_AMP', 42)
ATT_UP, ATT_DOWN, HIT_UP, FLOOR = E('ATT_UP', 30), E('ATT_DOWN', -22), E('HIT_UP', 25), E('FLOOR', 0.01)
IMPACT = E('IMPACT', 1.217)
FPS = 30
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; wings = bpy.data.objects['Wings']
BONES = {s: [f'Wing_{s}_{i}' for i in (1, 2, 3)] for s in 'LR'}
SG = {'L': 1.0, 'R': -1.0}
AX = {s: {'elev': Vector((0, -SG[s], 0)), 'sweep': Vector((0, 0, -SG[s])), 'twist': Vector((SG[s], 0, 0))} for s in 'LR'}
REST = {n: rig.data.bones[n].matrix_local.to_3x3() for s in 'LR' for n in BONES[s]}


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def q_of(name, side, elev=0.0, sweep=0.0, twist=0.0):
    R = (Matrix.Rotation(math.radians(sweep), 3, AX[side]['sweep']) @ Matrix.Rotation(math.radians(elev), 3, AX[side]['elev'])
         @ Matrix.Rotation(math.radians(twist), 3, AX[side]['twist']))
    Rr = REST[name]
    return (Rr.inverted() @ R @ Rr).to_quaternion()


def apply(pose, frame=None):
    """pose: {side: [(elev, sweep, twist) x 3]}"""
    for s in 'LR':
        for name, ang in zip(BONES[s], pose[s]):
            pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = q_of(name, s, *ang)
            if frame is not None:
                pb.keyframe_insert('rotation_quaternion', frame=frame)


def sym(b1, b2=(0, 0, 0), b3=(0, 0, 0)):
    return {s: [tuple(b1), tuple(b2), tuple(b3)] for s in 'LR'}


def lerp(a, b, t):
    return {s: [tuple(x + (y - x) * t for x, y in zip(pa, pb)) for pa, pb in zip(a[s], b[s])] for s in 'LR'}


def ss(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


STAND = sym((REST_ELEV, -4, 0), (-4, 0, 0), (-4, 0, 0))


def stand(t, T=3.0):
    b = 3 * math.sin(2 * math.pi * t / T)
    return sym((REST_ELEV + b, -4, 0), (-4 + 0.5 * b, 0, 0), (-4 + 0.5 * b, 0, 0))


def flap(t, T=1.0):
    ph = 2 * math.pi * t / T
    e = FLAP_MID + FLAP_AMP * math.cos(ph)
    lag = math.cos(ph - math.pi / 2)                       # +1 at the middle of the downstroke
    sw = 12 * math.sin(ph)                                 # forward on the downstroke, back on the upstroke
    return sym((e, sw, -6 * math.sin(ph)), (14 * lag, -0.5 * sw, 0), (18 * lag - 6, -0.6 * sw, 4 * lag))


def oneshot(keys, t, T, blend=0.2):
    """keys: [(time, pose)] inside the clip; outside the first/last key the Standing breath, eased"""
    if t <= keys[0][0]:
        return lerp(stand(t), keys[0][1], ss(t / max(keys[0][0], 1e-3)))
    if t >= keys[-1][0]:
        return lerp(keys[-1][1], stand(t), ss((t - keys[-1][0]) / max(T - keys[-1][0], 1e-3)))
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return lerp(pa, pb, ss((t - ta) / (tb - ta)))


def key_clip(name, fn):
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    for f in range(f0, f1 + 1):
        apply(fn((f - f0) / FPS, (f1 - f0) / FPS), frame=f)
    set_act(None)
    print('WINGS', name, 'frames', f1 - f0 + 1)


key_clip('Standing', lambda t, T: stand(t, T))
key_clip('Walking', lambda t, T: flap(t, T))
UP = sym((ATT_UP, -12, -6), (10, -4, 0), (8, 0, 0))   # swept back: the raised blade cleared the coverts by < 1.2 cm
DOWN = sym((ATT_DOWN, -4, 4), (-8, -6, 0), (-10, -8, 0))
key_clip('Attack', lambda t, T: oneshot([(max(IMPACT - 0.55, 0.15), UP), (IMPACT - 0.2, UP), (IMPACT + 0.03, DOWN)], t, T))
HIT = sym((HIT_UP, -14, 0), (12, 0, 0), (10, 0, 0))
key_clip('Hit', lambda t, T: oneshot([(0.12, HIT), (0.2, HIT)], t, T))
SPREAD = sym((20, -12, 0), (6, -4, 0), (4, 0, 0))
key_clip('Fidget', lambda t, T: oneshot([(0.35 * T, SPREAD), (0.65 * T, SPREAD)], t, T))
if 'Running' in bpy.data.actions:
    key_clip('Running', lambda t, T: flap(t, T))
for n in ('GripRef', 'Walking_mixamo'):
    if n in bpy.data.actions:
        key_clip(n, lambda t, T: STAND)

# ---------------------------------------------------------------- death: rise, then the searched corpse pose
deps = bpy.context.evaluated_depsgraph_get()
# the floor rule checks the wing beyond OUTER_X (the root region sits behind the back plate, under the lying body)
OUTER_X = E('OUTER_X', 0.25)
WV = {s: np.where(np.array([(wings.matrix_world @ v.co).x for v in wings.data.vertices]) * SG[s] > OUTER_X)[0] for s in 'LR'}


def wing_z(side):
    bpy.context.view_layer.update(); deps.update()
    ev = wings.evaluated_get(deps); m = ev.to_mesh()
    z = np.array([(wings.matrix_world @ m.vertices[i].co).z for i in WV[side]])
    ev.to_mesh_clear()
    return z


death = bpy.data.actions['Death']; set_act(death)
d0, d1 = int(death.frame_range[0]), int(death.frame_range[1])
scene.frame_set(d1)
best = {}
for s in 'LR':
    cand = None
    for a1 in range(0, 65, 5):
        for a2 in range(-50, 5, 10):
            for a3 in (-30, -15, 0):
                pose = {k: [(0, 0, 0)] * 3 for k in 'LR'}
                pose[s] = [(0, a1, 0), (0, a2, 0), (0, a3, 0)]
                apply(pose)
                z = wing_z(s)
                if z.min() >= FLOOR and (cand is None or z.mean() < cand[0]):
                    cand = (float(z.mean()), (a1, a2, a3), float(z.min()))
    if os.environ.get('WDBG'):
        for a1 in (0, 30, 60):
            pose = {k: [(0, 0, 0)] * 3 for k in 'LR'}; pose[s] = [(0, a1, 0), (0, 0, 0), (0, 0, 0)]; apply(pose)
            z = wing_z(s); print('WDBG', s, a1, round(float(z.min()), 3), round(float(z.mean()), 3), round(float(z.max()), 3))
    best[s] = cand
    print('DEATHWINGS', s, 'sweep root/mid/outer', cand[1] if cand else None, 'mean height cm',
          round(cand[0] * 100, 1) if cand else None)
CORPSE = {s: [(0, best[s][1][0], 0), (0, best[s][1][1], 0), (0, best[s][1][2], 0)] for s in 'LR'}
RISE = sym((28, -6, 0), (10, 0, 0), (8, 0, 0))
T = (d1 - d0) / FPS
# the fall: from the first frame the pelvis has dropped 15 cm below its start to the end
pz = []
for f in range(d0, d1 + 1):
    scene.frame_set(f); pz.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z)
pz = np.array(pz); fall0 = int(np.argmax(pz < pz[0] - 0.15)) if (pz < pz[0] - 0.15).any() else int(len(pz) * 0.5)
lifted = 0
for f in range(d0, d1 + 1):
    t = (f - d0) / FPS; i = f - d0
    scene.frame_set(f)
    if i < fall0:
        base = lerp(stand(t), RISE, ss(t / max(fall0 / FPS, 1e-3)))
        w = 0.0
    else:
        base = RISE
        w = ss((i - fall0) / max(d1 - d0 - fall0 - 6, 1))
    pose = lerp(base, CORPSE, w)
    apply(pose)
    for s in 'LR':                                         # floor rule: more of the corpse pose until clear
        k = w
        while wing_z(s).min() < FLOOR and k < 1.0:
            k = min(1.0, k + 0.1)
            pose[s] = lerp(base, CORPSE, k)[s]; apply(pose); lifted += 1
    apply(pose, frame=f)
set_act(None)
print('WINGS Death frames', d1 - d0 + 1, 'fall from frame', fall0, 'floor-rule steps', lifted)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
