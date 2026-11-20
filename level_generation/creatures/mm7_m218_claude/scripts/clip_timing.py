"""m218 clip timing for the engine's action events (playbook "Clip timing"), adapted from mm7_m214_claude / natm: <in> -> <out blend>.
- Stance blends from/to Standing frame 0 (smoothstep on every bone): Hit in 0.12 / out 0.20 s, Death in 0.25 s (the
  engine does not crossfade into the death); the Mixamo fall's pelvis travel is halved (corpse near the actor).
- Floor pass: per frame the lowest sole (the whole body for the death) is brought to the floor (pelvis z, smoothed);
  the walk too (one foot is always planted).
- Attack (author_spear.py) is eased from/to Standing and Fidget starts/ends at the carry; IMPACT = the spear tip at
  95 % of its forward travel (author_spear.py, after retime_attack.py).
- The spear (world-keyed bone) is re-keyed from the left fist in every clip but the attack; in the death the fist opens
  at DEATH_RELEASE and the spear drops to lie flat on the floor beside the body (native m218da..dd).
Writes work/clip_timing.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30; CAST_LEAD = 0.30; DEATH_TRAVEL = 0.5
BLEND_IN = {'Hit': 0.12, 'Death': 0.25}
BLEND_OUT = {'Hit': 0.20}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act); prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n in ('B_Pelvis', 'Spear'): pb.keyframe_insert('location', frame=i)   # Spear: world-keyed prop bone
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None); return act


def blend(a, b, w):
    return {k: ((a[k][0] if a[k][0].dot(b[k][0]) >= 0 else -a[k][0]).slerp(b[k][0], w), a[k][1].lerp(b[k][1], w)) for k in a}


ST = sample(bpy.data.actions['Standing'], 0)
out = {}
for name in ('Hit', 'Death'):
    poses = [sample(bpy.data.actions[name], f) for f in range(int(bpy.data.actions[name].frame_range[1]) + 1)]
    n = len(poses); fi, fo = BLEND_IN.get(name, 0) * FPS, BLEND_OUT.get(name, 0) * FPS
    res = []
    for i, p in enumerate(poses):
        w = 1.0
        if fi: w = min(w, smooth(i / fi))
        if fo: w = min(w, smooth((n - 1 - i) / fo))
        res.append(blend(ST, p, w))
    if name == 'Death':
        # the Mixamo fall travels ~1 m back; the corpse should lie near the actor's position (native falls in place)
        set_act(None); W0 = None
        for k, p in enumerate(res):
            for b_, (q, l) in p.items():
                pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
            bpy.context.view_layer.update()
            M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
            if W0 is None: W0 = M.translation.copy()
            t = M.translation.copy(); t.x = W0.x + (t.x - W0.x) * DEATH_TRAVEL; t.y = W0.y + (t.y - W0.y) * DEATH_TRAVEL
            M.translation = t; rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
            res[k] = dict(p); res[k]['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
    write(name, res)
# floor pass (review 1: the hit floated up to 17 cm, the cast sank 6 cm): per frame the lowest sole (the lowest point of
# the whole body for the death) is brought to the floor by moving the pelvis vertically, smoothed over 1.5 frames
# toes back to their rest relation to the foot in every clip (review 1: the Mixamo/set toe channels curled the toes up
# 4-7 cm - "feet weirdly warped"); the attack's heel-peeling foot is keyed flat by author_attack.py and kept
for act in bpy.data.actions:
    if act.name in ('Attack', 'GripRef', 'Thrust', 'Walking', 'Standing', 'Hit', 'Fidget', 'Death', 'Running'):
        continue                        # foot_level.py / run_fit.py / author_attack.py own the toes now
    for fc in [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]:
        if 'Toe0' in fc.data_path and fc.data_path.endswith('rotation_quaternion'):
            for kp in fc.keyframe_points:
                kp.co[1] = 1.0 if fc.array_index == 0 else 0.0; kp.handle_left[1] = kp.co[1]; kp.handle_right[1] = kp.co[1]
            fc.update()
body = bpy.data.objects['Body']; me = body.data; vg = [g.name for g in body.vertex_groups]
# walk toe-off: the rest toes push into the floor when the heel lifts; per frame and foot the toe bends up (about the
# foot's lateral axis) by the least angle that keeps every toe vertex on the floor
TOEV = {sd: np.array([sum(e.weight for e in v.groups if vg[e.group] == f'B_{sd}_Toe0') > 0.3 for v in me.vertices]) for sd in 'LR'}
def lowest(mask):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear(); return float(z[mask].min())
for name in ('Walking',) if os.environ.get('TOE_OFF') else ():
    act = bpy.data.actions[name]; n = int(act.frame_range[1]) + 1; poses = [sample(act, f) for f in range(n)]; worst = 0.0
    for f, p_ in enumerate(poses):
        set_act(None)
        for b_, (q, l) in p_.items():
            pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        bpy.context.view_layer.update()
        for sd in 'LR':
            if lowest(TOEV[sd]) > -0.002:
                continue
            tb = rig.pose.bones[f'B_{sd}_Toe0']; base = tb.rotation_quaternion.copy()
            lat = (rig.matrix_world @ rig.pose.bones[f'B_{sd}_Foot'].matrix).to_3x3() @ Vector((1, 0, 0))
            def bend(a):
                tb.rotation_quaternion = base; bpy.context.view_layer.update()
                M = rig.matrix_world @ tb.matrix; t = M.translation.copy()
                for sign in (1,):
                    R = Matrix.Rotation(math.radians(a), 4, lat.normalized())
                M = R @ M; M.translation = t; tb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
                return lowest(TOEV[sd])
            sgn = 1 if bend(10) > bend(-10) else -1
            lo_, hi_ = 0.0, 70.0
            for _ in range(7):
                mid = (lo_ + hi_) / 2
                if bend(sgn * mid) > -0.002: hi_ = mid
                else: lo_ = mid
            bend(sgn * hi_); worst = max(worst, hi_)
            p_[f'B_{sd}_Toe0'] = (tb.rotation_quaternion.copy(), tb.location.copy())
    write(name, poses)
    print(f'TIMING toe-off {name}: max toe bend {worst:.0f} deg')
_pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', _pc)
BODYV = _pc < 1000                                              # the body without the props (the dropped spear)
FEETV = np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')) > 0.5 for v in me.vertices])
gk = np.exp(-0.5 * (np.arange(-4, 5) / 0.8) ** 2); gk /= gk.sum()
for name in ('Hit', 'Fidget', 'Death', 'Walking', 'Attack'):
    act = bpy.data.actions[name]; n = int(act.frame_range[1]) + 1; lows = []
    for f in range(n):
        set_act(act); scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
        lows.append(z[BODYV].min() if name == 'Death' else z[FEETV].min())
    lows = np.array(lows); pad = np.concatenate([np.repeat(lows[:1], 4), lows, np.repeat(lows[-1:], 4)])
    if name == 'Walking':                                     # a loop: wrap (its last frame repeats the first)
        pad = np.concatenate([lows[-5:-1], lows, lows[1:5]])
    dz = -np.convolve(pad, gk, 'valid')
    poses = [sample(act, f) for f in range(n)]
    for f, p_ in enumerate(poses):
        set_act(None)
        for b_, (q, l) in p_.items():
            pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        bpy.context.view_layer.update()
        M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix; M.translation.z += float(dz[f])
        rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
        p_['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
    write(name, poses)
    print(f'TIMING floor {name}: lowest point before {lows.min() * 100:.1f}..{lows.max() * 100:.1f} cm, pelvis shift {dz.min() * 100:.1f}..{dz.max() * 100:.1f} cm')
AT = json.load(open(os.path.join(HERE, 'work', 'attack_timing.json')))
out['attack_impact_s'] = AT['impact_s'] if 'impact_s' in AT else round(AT['release_frame'] / FPS, 4)
# the spear rides in the left fist in every clip but the attack (write() keys rotations and the pelvis only)
S_HAND_L = Matrix(json.load(open(os.path.join(HERE, 'work', 'spear_rig.json')))['spear_hand_L'])
DEATH_RELEASE, DROP_FRAMES, DROP_SIDE = int(os.environ.get('DEATH_RELEASE', '15')), 12, 0.2   # native m218da..dd: the spear falls free
for act in [a for a in bpy.data.actions if a.use_fake_user and a.name not in ('Attack', 'GripRef', 'Thrust')]:
    set_act(act); f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    pb = rig.pose.bones['Spear']; pb.rotation_mode = 'QUATERNION'
    rel = DEATH_RELEASE if act.name in ('Death', 'Dead') else None
    M_rel = M_end = None
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        if rel is not None and f >= rel:
            if M_rel is None:                                   # the fist opens: the spear drops and lies flat
                M_rel = (rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix @ S_HAND_L).copy()
                yv = Vector((0.25, -1.0, 0.0)).normalized()     # lies along his left side, tip forward
                zv = Vector((0, 0, 1)); xv = yv.cross(zv)
                M_end = Matrix((xv, yv, zv)).transposed().to_4x4()
                M_end.translation = Vector((M_rel.translation.x + DROP_SIDE, M_rel.translation.y, 0.018))
            t = min(1.0, (f - rel) / DROP_FRAMES); t = t * t                    # falling: accelerating
            qa, qb = M_rel.to_quaternion(), M_end.to_quaternion()
            if qa.dot(qb) < 0:
                qb = -qb
            M = qa.slerp(qb, t).to_matrix().to_4x4(); M.translation = M_rel.translation.lerp(M_end.translation, t)
            ay = M.col[1].xyz.z                                  # never below the floor while it turns flat
            low = M.translation.z + min(ay * 1.15, -ay * 0.85) - 0.016
            if low < 0:
                M.translation.z -= low
        else:
            M = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix @ S_HAND_L
        pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
        if f > f0 and pb.rotation_quaternion.dot(q_prev) < 0:   # sign-continuous keys (half frames interpolate)
            pb.rotation_quaternion = -pb.rotation_quaternion
        q_prev = pb.rotation_quaternion.copy()
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
set_act(None)
json.dump(out, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'), indent=1)
print(f'TIMING blends in {BLEND_IN} out {BLEND_OUT}; IMPACT (release) {out["attack_impact_s"]} s')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
