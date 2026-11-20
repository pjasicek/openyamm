"""Wing and tail motion per clip for the gargoyle (wings_rig_bat.py: Wing_<s>_1/2 arm, Wing_<s>_F1..F4 fingers;
tail_rig.py: Tail_1..N), matched against the native m234 frames. Wing poses are rotations relative to the rest pose
about REST axes (they move with the parent): elev (tip up, about the body's forward axis), sweep (tip forward, about the
vertical) and fan (in the wing plane, turning a bone from 'out' toward 'down': folds the arm and closes the fingers).
- Standing / Dead-free clips start and end in FOLD (native sa: the arm raised beside the shoulder, the hooked wrists by
  the horns, the fingers hanging down beside the body like a cloak, membranes half closed); a slow breath.
- Walking (native wa..wh, upright hovering flight, 1.0 s): elev = FLAP_MID + FLAP_AMP cos(2 pi t) (top at wa); the
  fingers spread on the downstroke and half close on the upstroke; forward on the downstroke.
- Attack (native aa..ah: the wings spread wide behind the swipe): FOLD -> SPREAD for the wind-up, held through the
  blow, back to FOLD. Hit (native na..nf: wings flung up and out): SPREAD_UP at 0.12 s. Fidget: a slow spread and close.
- Death (native: falls back, the corpse lies on its back with the wings spread flat): spread with the fall, then ease
  into a corpse pose found by search on the last frame (root sweep forward = up when lying on the back, arm and
  fingers fanned) with every wing vertex beyond OUTER_X at least FLOOR above the floor; per frame the blend toward it is
  raised until the wings clear.
Tail: per clip a sway (yaw about the vertical with a phase lag along the chain, amplitude growing to the tip), a lash in
the attack, and a FLOOR RULE per frame (each segment from the root, whose end dips below TAIL_R, is turned up the least
about the horizontal axis across it). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
FLAP_MID, FLAP_AMP, FLOOR, OUTER_X, TAIL_R = E('FLAP_MID', 0), E('FLAP_AMP', 38), E('FLOOR', 0.01), E('OUTER_X', 0.3), E('TAIL_R', 0.025)
IMPACT = E('IMPACT', 0.95)
FPS = 30
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = json.load(open(os.path.join(HERE, 'work', 'wing_chains.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; wings = bpy.data.objects['Wings']
WB = {s: [f'Wing_{s}_1', f'Wing_{s}_2'] + [f'Wing_{s}_F{k}' for k in (1, 2, 3, 4)] for s in 'LR'}
TB = sorted([b.name for b in rig.data.bones if b.name.startswith('Tail_')], key=lambda n: int(n.split('_')[1]))
SG = {'L': 1.0, 'R': -1.0}
AX = {}
for s in 'LR':
    u, v = Vector(CH[s]['u']), Vector(CH[s]['v'])
    AX[s] = {'elev': Vector((0, -SG[s], 0)), 'sweep': Vector((0, 0, -SG[s])), 'fan': u.cross(v).normalized()}
REST = {n: rig.data.bones[n].matrix_local.to_3x3() for n in sum(WB.values(), []) + TB}


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def q_wing(name, side, elev=0.0, sweep=0.0, fan=0.0):
    R = (Matrix.Rotation(math.radians(sweep), 3, AX[side]['sweep']) @ Matrix.Rotation(math.radians(elev), 3, AX[side]['elev'])
         @ Matrix.Rotation(math.radians(fan), 3, AX[side]['fan']))
    Rr = REST[name]
    return (Rr.inverted() @ R @ Rr).to_quaternion()


def apply_wings(pose):
    for s in 'LR':
        for name, ang in zip(WB[s], pose[s]):
            pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q_wing(name, s, *ang)


def key_wings():
    for s in 'LR':
        for name in WB[s]:
            rig.pose.bones[name].keyframe_insert('rotation_quaternion', frame=scene.frame_current)


def sym(*bones):
    return {s: [tuple(b) for b in bones] for s in 'LR'}


def lerp(a, b, t):
    return {s: [tuple(x + (y - x) * t for x, y in zip(pa, pb)) for pa, pb in zip(a[s], b[s])] for s in 'LR'}


def ss(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


FOLD = sym((-12, -12, 0), (0, 0, 0), (0, 0, 33), (0, 0, 17), (0, 0, 0), (0, 0, -9))   # closed fan: fingers 115..150 deg (fold_probe.py)
SPREAD = sym((8, 6, 0), (0, 0, 0), (0, 0, -4), (0, 0, -4), (0, 0, -2), (0, 0, 0))
SPREAD_UP = sym((26, 0, 0), (0, 0, -6), (0, 0, -6), (0, 0, -4), (0, 0, -2), (0, 0, 0))


def fold(t, T=4.0):
    b = 2.5 * math.sin(2 * math.pi * t / T)
    return {s: [(FOLD[s][0][0] + b, FOLD[s][0][1], 0)] + FOLD[s][1:] for s in 'LR'}


def flap(t, T=1.0):
    ph = 2 * math.pi * t / T
    e = FLAP_MID + FLAP_AMP * math.cos(ph)
    close = 12 - 12 * math.sin(ph)                         # 0 on the downstroke, 24 on the upstroke
    sw = 10 * math.sin(ph)
    return sym((e, sw, 0), (0, 0, 0.5 * close), (0, 0, close), (0, 0, 0.8 * close), (0, 0, 0.6 * close), (0, 0, 0.3 * close))


def oneshot(keys, t, T):
    if t <= keys[0][0]:
        return lerp(fold(t), keys[0][1], ss(t / max(keys[0][0], 1e-3)))
    if t >= keys[-1][0]:
        return lerp(keys[-1][1], fold(t), ss((t - keys[-1][0]) / max(T - keys[-1][0], 1e-3)))
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return lerp(pa, pb, ss((t - ta) / (tb - ta)))


# ---------------------------------------------------------------- tail
def tail_pose(t, T, amp, period, lash=0.0):
    n = len(TB)
    for i, name in enumerate(TB):
        a = amp * (0.4 + 0.6 * i / max(n - 1, 1)) * math.sin(2 * math.pi * (t / period) - 0.6 * i) + lash * (1 - i / n)
        pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'
        Rr = REST[name]
        pb.rotation_quaternion = (Rr.inverted() @ Matrix.Rotation(math.radians(a), 3, Vector((0, 0, 1))) @ Rr).to_quaternion()


def tail_floor():
    lifted = 0
    for name in TB:
        bpy.context.view_layer.update()
        pb = rig.pose.bones[name]
        M = rig.matrix_world @ pb.matrix; h = M.translation.copy(); tl = rig.matrix_world @ pb.tail
        if tl.z >= TAIL_R:
            continue
        d = (tl - h); L = d.length
        axis = d.cross(Vector((0, 0, 1)))
        if axis.length < 1e-6:
            continue
        axis.normalize()
        need = TAIL_R - tl.z
        ang = math.asin(min(1.0, need / max(L, 1e-4)))
        for sgn in (1, -1):                                 # the sign that raises the end
            R = Matrix.Rotation(sgn * ang, 4, axis)
            if ((R @ (tl - h).to_4d()).to_3d() + h).z > tl.z:
                break
        pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)
        lifted += 1
    return lifted


def tail_settle(share):
    """death: lower every segment whose end stands more than 2 cm above TAIL_R toward the floor, by `share` of the
    turn that would put it there (the rest curl of the tail otherwise stands up off the lying corpse)"""
    for name in TB:
        bpy.context.view_layer.update()
        pb = rig.pose.bones[name]
        M = rig.matrix_world @ pb.matrix; h = M.translation.copy(); tl = rig.matrix_world @ pb.tail
        excess = tl.z - (TAIL_R + 0.02)
        if excess <= 0 or share <= 0:
            continue
        d = tl - h; L = d.length; axis = d.cross(Vector((0, 0, 1)))
        if axis.length < 1e-6:
            continue
        axis.normalize(); ang = share * math.asin(min(1.0, excess / max(L, 1e-4)))
        for sgn in (1, -1):
            R = Matrix.Rotation(sgn * ang, 4, axis)
            if ((R @ (tl - h).to_4d()).to_3d() + h).z < tl.z:
                break
        pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)


def key_tail():
    for name in TB:
        rig.pose.bones[name].keyframe_insert('rotation_quaternion', frame=scene.frame_current)


def key_clip(name, wing_fn, tail_fn):
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); lifts = 0
    for f in range(f0, f1 + 1):
        scene.frame_set(f); t = (f - f0) / FPS; T = (f1 - f0) / FPS
        apply_wings(wing_fn(t, T)); tail_fn(t, T); lifts += tail_floor()
        key_wings(); key_tail()
    set_act(None)
    print('APPEND', name, 'frames', f1 - f0 + 1, 'tail floor turns', lifts)


key_clip('Standing', lambda t, T: fold(t, T), lambda t, T: tail_pose(t, T, 6, T))
key_clip('Walking', lambda t, T: flap(t, T), lambda t, T: tail_pose(t, T, 10, T))
key_clip('Attack', lambda t, T: oneshot([(max(IMPACT - 0.5, 0.15), SPREAD), (IMPACT + 0.15, SPREAD)], t, T),
         lambda t, T: tail_pose(t, T, 8, T, lash=25 * math.sin(math.pi * ss(t / T))))
key_clip('Hit', lambda t, T: oneshot([(0.12, SPREAD_UP), (0.22, SPREAD_UP)], t, T), lambda t, T: tail_pose(t, T, 12, 0.5))
key_clip('Fidget', lambda t, T: oneshot([(0.3 * T, SPREAD), (0.7 * T, SPREAD)], t, T), lambda t, T: tail_pose(t, T, 8, T / 2))
for n in ('Running', 'GripRef', 'Walking_mixamo', 'AttackFull', 'FidgetFull'):
    if n in bpy.data.actions:
        key_clip(n, lambda t, T: fold(t), lambda t, T: tail_pose(t, T, 0, 1))

# ---------------------------------------------------------------- death
deps = bpy.context.evaluated_depsgraph_get()
WX = np.array([(wings.matrix_world @ v.co).x for v in wings.data.vertices])
WV = {s: np.where(WX * SG[s] > OUTER_X)[0] for s in 'LR'}


def wing_z(side):
    bpy.context.view_layer.update(); deps.update()
    ev = wings.evaluated_get(deps); m = ev.to_mesh()
    z = np.array([(wings.matrix_world @ m.vertices[i].co).z for i in WV[side]]); ev.to_mesh_clear()
    return z


death = bpy.data.actions['Death']; set_act(death)
d0, d1 = int(death.frame_range[0]), int(death.frame_range[1])
scene.frame_set(d1)
best = {}
for s in 'LR':
    cand = None
    for a1 in range(0, 75, 5):
        for a2 in (-20, -10, 0, 10, 20):
            for af in (-10, 0, 10, 20):
                pose = {k: [(0, 0, 0)] * 6 for k in 'LR'}
                pose[s] = [(0, a1, 0), (0, 0, a2), (0, 0, af), (0, 0, af), (0, 0, af), (0, 0, af)]
                apply_wings(pose); z = wing_z(s)
                if z.min() >= FLOOR and (cand is None or z.mean() < cand[0]):
                    cand = (float(z.mean()), (a1, a2, af))
    best[s] = cand
    print('DEATHWINGS', s, 'root sweep / arm fan / finger fan', cand[1] if cand else None,
          'mean height cm', round(cand[0] * 100, 1) if cand else None)
CORPSE = {s: ([(0, best[s][1][0], 0), (0, 0, best[s][1][1])] + [(0, 0, best[s][1][2])] * 4) if best[s] else SPREAD[s] for s in 'LR'}
pz = []
for f in range(d0, d1 + 1):
    scene.frame_set(f); pz.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z)
pz = np.array(pz); fall0 = int(np.argmax(pz < pz[0] - 0.15)) if (pz < pz[0] - 0.15).any() else len(pz) // 2
steps = 0
for f in range(d0, d1 + 1):
    t = (f - d0) / FPS; i = f - d0
    scene.frame_set(f)
    if i < fall0:
        base = lerp(fold(t), SPREAD, ss(t / max(fall0 / FPS, 1e-3))); w = 0.0
    else:
        base = SPREAD; w = ss((i - fall0) / max(d1 - d0 - fall0 - 6, 1))
    pose = lerp(base, CORPSE, w); apply_wings(pose)
    for s in 'LR':
        k = w
        while wing_z(s).min() < FLOOR and k < 1.0:
            k = min(1.0, k + 0.1); pose[s] = lerp(base, CORPSE, k)[s]; apply_wings(pose); steps += 1
    tail_pose(t, (d1 - d0) / FPS, 6 * (1 - ss(i / (d1 - d0))), 1.0); tail_settle(w); tail_floor()
    key_wings(); key_tail()
set_act(None)
print('APPEND Death frames', d1 - d0 + 1, 'fall from frame', fall0, 'wing floor steps', steps)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
