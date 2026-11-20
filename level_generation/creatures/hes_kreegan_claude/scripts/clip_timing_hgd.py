"""Guard clip assembly and timing (playbook "Clip timing"; structure of caster_timing.py), after seat_rifle.py.
- Attack (attack_ranged): the set's FireRifle1 starts shouldered, so a LEAD ease (smoothstep, every B_* bone) raises
  the rifle from Standing frame 0 into its first pose, then the source at its own speed, out OUT s back to Standing.
  IMPACT (the shot) = the first frame of the recoil: the rifle's backward speed along its own barrel first exceeds
  half its peak (searched after the raise).
- AttackMelee (the set's rifle-butt Attack1): in 0.15 / out 0.25 s; IMPACT = when the stock's butt reaches 95 % of
  its forward travel (in the pelvis heading at frame 0), the blow lands at contact.
- Hit in 0.12 / out 0.20 s, Death in 0.25 s with its pelvis travel halved (the corpse lies near the actor).
- Fidget: the guard raises the rifle, sights along it and lowers it: a FID_IN ease from Standing into the set's aiming
  idle (IdleAlt, retargeted as 'Aim'), FID_HOLD loops of it, FID_OUT back (the set's reload sent the free left hand
  through the chest plate, 7 cm). Standing, Walking, Running loop as the source.
Writes work/clip_timing.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
FID_IN, FID_HOLD, FID_OUT = 0.45, 2, 0.45
LEAD = {'Attack': float(os.environ.get('ATTACK_LEAD', '0.30'))}
BLEND_IN = {'AttackMelee': 0.15, 'Hit': 0.12, 'Death': 0.25}
BLEND_OUT = {'Attack': 0.30, 'AttackMelee': 0.25, 'Hit': 0.20, 'Fidget': FID_OUT}
SOURCE = {'Attack': 'Fire', 'Fidget': 'Aim', 'AttackMelee': 'Melee'}
DEATH_TRAVEL = 0.5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; AW = rig.matrix_world
names = [b.name for b in rig.data.bones if b.name.startswith('B_')]
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
BUTT = Vector((0.0, -0.33, 0.095))                     # the stock's butt in the rifle frame (make_carbine.py)


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


def rifle_world():
    return AW @ rig.pose.bones['Rifle'].matrix


ST = sample(bpy.data.actions['Standing'], 0)
timing = {}
for name in [n for n in ('Attack', 'AttackMelee', 'Hit', 'Death', 'Fidget') if SOURCE.get(n, n) in bpy.data.actions]:
    act = bpy.data.actions[SOURCE.get(name, name)]; n_src = int(round(act.frame_range[1])) + 1
    poses = [sample(act, f) for f in range(int(act.frame_range[0]), n_src)]
    if name == 'Fidget':                               # the aiming idle loops: hold it FID_HOLD times
        poses = (poses[:-1] * FID_HOLD) + [poses[-1]]
        LEAD['Fidget'] = FID_IN
    lead = int(round(LEAD.get(name, 0) * FPS))
    frames = [blend(ST, poses[0], smooth(i / lead)) for i in range(lead)] + poses
    n = len(frames); fi, fo = BLEND_IN.get(name, 0) * FPS, BLEND_OUT.get(name, 0) * FPS
    res = []
    for i, p in enumerate(frames):
        w = 1.0
        if fi: w = min(w, smooth(i / fi))
        if fo: w = min(w, smooth((n - 1 - i) / fo))
        res.append(blend(ST, p, w) if w < 1 else p)
    if name == 'Death':                                # halve the travel (the corpse lies near the actor)
        p0 = res[0]['B_Pelvis'][1]
        for p in res:
            q, l = p['B_Pelvis']; d = l - p0; d.y *= DEATH_TRAVEL; d.x *= DEATH_TRAVEL; p['B_Pelvis'] = (q, p0 + d)
    write(name, res)
    info = {'frames': n, 'seconds': round((n - 1) / FPS, 3)}
    if name == 'Attack':
        R = []
        for i, p in enumerate(res):
            pose(p); R.append(rifle_world())
        speed = []
        for i in range(1, n):
            ax = R[i].to_3x3() @ Vector((0, 1, 0))
            speed.append(-((R[i].translation - R[i - 1].translation).dot(ax)) * FPS)     # backward along the barrel
        search = range(lead, n - 1)
        peak = max(speed[i - 1] for i in search)
        shot = next(i for i in search if speed[i - 1] >= 0.5 * peak)
        info.update({'impact': round(shot / FPS, 3), 'recoil_peak_mps': round(peak, 2), 'lead_frames': lead})
    if name == 'AttackMelee':
        pose(res[0]); P0 = AW @ rig.pose.bones['B_Pelvis'].matrix
        fwd = (P0.to_3x3() @ Vector((0, 0, 1)))
        fwd = Vector((0, -1, 0))                   # the character faces -Y in every clip start (planted source)
        ys = []
        for p in res:
            pose(p); ys.append((rifle_world() @ BUTT).dot(fwd))
        lo, hi = min(ys), max(ys); ipk = ys.index(hi)
        hit = next(i for i in range(ipk + 1) if ys[i] >= lo + 0.95 * (hi - lo))
        info.update({'impact': round(hit / FPS, 3), 'butt_travel_m': round(hi - lo, 3)})
    timing[name] = info
    print('TIMING', name, json.dumps(info))
for a in ('Fire', 'Aim', 'Melee'):
    if a in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[a])
json.dump(timing, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
