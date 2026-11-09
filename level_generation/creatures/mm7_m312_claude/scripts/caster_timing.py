"""Clip timing for the robed casters (m312: also the peasant set without Attack/Cast; Fidget eases 0.3 s in/out) (playbook "Clip timing"), adapted from mm6_natm_claude/scripts/clip_timing.py.
- Every one-shot eases from (and back to) Standing frame 0 with a smoothstep on every B_* bone:
  Attack/Cast: a LEAD ready ease into the clip's first pose (the set's casts start in their own guard), the source at
  its own speed, out OUT s; Hit in 0.12 / out 0.20 s; Death in 0.25 s (the engine does not crossfade into a death),
  its pelvis travel halved (the corpse lies near the actor). Fidget is authored with its own ease.
- Release (impact) times, written to work/clip_timing.json: Attack = peak speed of the casting hand (ATTACK_HAND);
  Cast = the frame the two hands' mean reaches its farthest forward point in the chest-yaw frame (release near full
  reach, as the accepted MM8 Cleric).
- Floor (death only): per frame the lowest point of the body without the robe skirt, rope ends and banners (the robe
  is simulated later with its own floor) is brought to z >= FLOOR by moving the pelvis, smoothed.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = {'Attack': float(os.environ.get('ATTACK_LEAD', '0.25')), 'Cast': float(os.environ.get('CAST_LEAD', '0.30'))}
BLEND_IN = {'Hit': 0.12, 'Death': 0.25, 'Fidget': 0.3}
BLEND_OUT = {'Hit': 0.20, 'Fidget': 0.3, 'Attack': float(os.environ.get('ATTACK_OUT', '0.30')), 'Cast': float(os.environ.get('CAST_OUT', '0.30'))}
ATTACK_HAND = os.environ.get('ATTACK_HAND', 'L')
DEATH_TRAVEL, FLOOR = 0.5, 0.0
NOFLOOR = tuple(int(x) for x in os.environ.get('NOFLOOR_GARMENTS', '2,8,10').split(','))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; AW = rig.matrix_world
names = [b.name for b in rig.data.bones if b.name.startswith('B_')]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pose(p):
    set_act(None)
    for n, (q, l) in p.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act); prev = {}
    for i, p in enumerate(frames):
        for n, (q, l) in p.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis': pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None); return act


def blend(a, b, w):
    return {k: ((a[k][0] if a[k][0].dot(b[k][0]) >= 0 else -a[k][0]).slerp(b[k][0], w), a[k][1].lerp(b[k][1], w)) for k in a}


ST = sample(bpy.data.actions['Standing'], 0)
out = {}
for name in ('Attack', 'Cast', 'Hit', 'Death', 'Fidget'):
    act = bpy.data.actions.get(name)
    if act is None:
        continue
    n_src = int(round(act.frame_range[1])) + 1
    poses = [sample(act, f) for f in range(n_src)]
    lead = int(round(LEAD.get(name, 0) * FPS))
    frames = [blend(ST, poses[0], smooth(i / lead)) for i in range(lead)] + poses
    n = len(frames); fi, fo = BLEND_IN.get(name, 0) * FPS, BLEND_OUT.get(name, 0) * FPS
    res = []
    for i, p in enumerate(frames):
        w = 1.0
        if fi: w = min(w, smooth(i / fi))
        if fo: w = min(w, smooth((n - 1 - i) / fo))
        res.append(blend(ST, p, w))
    if name == 'Death':
        W0 = None
        for k, p in enumerate(res):
            pose(p)
            M = AW @ rig.pose.bones['B_Pelvis'].matrix
            if W0 is None: W0 = M.translation.copy()
            t = M.translation.copy(); t.x = W0.x + (t.x - W0.x) * DEATH_TRAVEL; t.y = W0.y + (t.y - W0.y) * DEATH_TRAVEL
            M.translation = t; rig.pose.bones['B_Pelvis'].matrix = AW.inverted() @ M; bpy.context.view_layer.update()
            res[k] = dict(p); res[k]['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
    write(name, res)
    out[f'{name.lower()}_lead_s'] = round(lead / FPS, 4)
    out[f'{name.lower()}_seconds'] = round((len(res) - 1) / FPS, 4)
body = bpy.data.objects['Body']; me = body.data
gv = np.array([a.value for a in me.attributes['garment'].data])
vg = [g.name for g in body.vertex_groups]
robe = np.array([any(vg[e.group].startswith('Robe_') and e.weight > 0.3 for e in v.groups) for v in me.vertices])
FLOORV = ~np.isin(gv, NOFLOOR) & ~robe
gk = np.exp(-0.5 * (np.arange(-4, 5) / 0.8) ** 2); gk /= gk.sum()
act = bpy.data.actions['Death']; n = int(act.frame_range[1]) + 1; lows = []
for f in range(n):
    set_act(act); scene.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
    lows.append(z[FLOORV].min())
lows = np.array(lows)
need = np.maximum(0.0, FLOOR - lows)                     # lift each frame needs; dilated (max over +-4) before the
pad = np.concatenate([np.repeat(need[:1], 4), need, np.repeat(need[-1:], 4)])   # smoothing so no frame stays under
dil = np.array([pad[i:i + 9].max() for i in range(len(need))])
pad = np.concatenate([np.repeat(dil[:1], 4), dil, np.repeat(dil[-1:], 4)])
dz = np.convolve(pad, gk, 'valid')
poses = [sample(act, f) for f in range(n)]
for f, p_ in enumerate(poses):
    pose(p_)
    M = AW @ rig.pose.bones['B_Pelvis'].matrix; M.translation.z += float(dz[f])
    rig.pose.bones['B_Pelvis'].matrix = AW.inverted() @ M; bpy.context.view_layer.update()
    p_['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
write('Death', poses)
print(f'TIMING floor Death: lowest body point {lows.min() * 100:.1f}..{lows.max() * 100:.1f} cm, pelvis lift max {dz.max() * 100:.1f} cm')


def chest_fwd(act):
    set_act(act); scene.frame_set(0)
    R = (AW @ rig.pose.bones['B_Spine2'].matrix).to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
    f = R @ Vector((0, -1, 0)); f.z = 0
    return f.normalized()


fwd = chest_fwd(bpy.data.actions['Standing'])
act = bpy.data.actions.get('Attack')
if act is not None:
    set_act(act); P = []
    for f in range(int(act.frame_range[1]) + 1):
        scene.frame_set(f); P.append(np.array((AW @ rig.pose.bones[f'B_{ATTACK_HAND}_Hand'].matrix).translation))
    sp = np.linalg.norm(np.diff(np.array(P), axis=0), axis=1); k = int(np.argmax(sp))
    out['attack_impact_s'] = round((k + 0.5) / FPS, 4); out['attack_peak_hand_speed_mps'] = round(float(sp[k] * FPS), 2)
act = bpy.data.actions.get('Cast')
if act is not None:
    set_act(act); D = []
    lead = out['cast_lead_s'] * FPS
    for f in range(int(act.frame_range[1]) + 1):
        scene.frame_set(f)
        m = (np.array((AW @ rig.pose.bones['B_L_Hand'].matrix).translation) + np.array((AW @ rig.pose.bones['B_R_Hand'].matrix).translation)) / 2
        D.append(float(m @ np.array(fwd)))
    D = np.array(D); k = int(np.argmax(D[int(lead):])) + int(lead)
    out['cast_impact_s'] = round(k / FPS, 4); out['cast_reach_m'] = round(float(D[k] - D[0]), 3)
set_act(None)
json.dump(out, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'), indent=1)
print('TIMING', json.dumps(out))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
