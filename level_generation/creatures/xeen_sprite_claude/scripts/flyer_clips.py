"""Flyer clips for the Killer Sprite (hovering humanoid, playbook "Flyers" + "Winged humanoids").
Input: the retargeted source actions (rebuild.sh): Standing (Mixamo Floating), SrcSwipe (Mutant Swiping, turned),
SrcCast (Standing 2H Magic Attack 01, turned), SrcHit (set Unarmed GetHit F1), SrcFidget (Taunt Gesture, turned),
SrcDeath (Standing Death Forward 01, turned). Output actions (30 fps keys, local quaternions + pelvis location):
- Standing: Floating, its loop seam closed (the seam difference spread over the clip), pelvis drift removed.
- Walking / Running: Standing with a forward lean (LEAN_WALK / LEAN_RUN deg about the pelvis), neck and head turned
  back by part of it (gaze level), thighs trailing back. One hover loop serves standing, walking and running.
- Attack / Cast / Hit / Fidget: the source's upper body (spine, arms, neck, head) on the hovering legs of Standing
  (same time), pelvis rotation half way between Standing and the source, pelvis travel K_XY of the source's
  horizontal and K_Z of its vertical motion (no lunge steps or crouches: she hovers); eased from Standing frame 0
  over BLEND_IN and back to it over BLEND_OUT.
- Death: the source fall (staggers, knees, falls face down) with the legs eased from the hovering legs over
  0.2-0.7 s, travel x DEATH_XY; the floor pass (wing_flap_floor.py) keeps the lowest point on the floor.
Windows (source frames at 30 fps) were chosen from review/cand2_sheet.png: the swipe raises the right arm (22-37) and
slashes down across the body (~44), the cast lifts both hands overhead and pushes them forward (~41).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
from mathutils import Quaternion, Vector, Matrix
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
FPS = 30
LEAN_WALK, LEAN_RUN = E('LEAN_WALK', 14), E('LEAN_RUN', 26)
K_XY, K_Z, DEATH_XY = E('K_XY', 0.35), E('K_Z', 0.25), E('DEATH_XY', 0.4)
BLEND_IN, BLEND_OUT = E('BLEND_IN', 0.2), E('BLEND_OUT', 0.3)
ACTIONS = {   # name: (source action, first frame, last frame or None, kind)
    'Attack': ('SrcSwipe', 15, 64, 'act'),
    'Cast': ('SrcCast', 20, 68, 'act'),
    'Hit': ('SrcHit', 0, None, 'act'),
    'Fidget': ('SrcFidget', 0, None, 'act'),
    'Death': ('SrcDeath', 0, None, 'death'),
}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
RREST = {n: rig.data.bones[n].matrix_local.to_3x3().normalized() for n in names}
PEL = 'B_Pelvis'


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def nframes(act):
    f0, f1 = act.frame_range
    return int(round(f1 - f0)) + 1


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def pel_pos(loc):                     # armature-space pelvis position from its local location (root bone)
    return rig.data.bones[PEL].head_local + RREST[PEL] @ loc


def pel_loc(pos):
    return RREST[PEL].inverted() @ (pos - rig.data.bones[PEL].head_local)


def turn_local(n, q, axis, deg):      # rotate a bone about an armature axis (expressed in its rest frame)
    R = RREST[n]
    d = (R.inverted() @ Matrix.Rotation(math.radians(deg), 3, axis) @ R).to_quaternion()
    return d @ q


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def blend(a, b, t):
    return {n: (a[n][0].slerp(b[n][0], t) if a[n][0].dot(b[n][0]) >= 0 else a[n][0].slerp(-b[n][0], t),
                a[n][1].lerp(b[n][1], t)) for n in names}


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q
            pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == PEL:
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None)
    print('CLIP', name, len(frames), 'frames', round((len(frames) - 1) / FPS, 3), 's')


# ---------------------------------------------------------------- Standing: loop seam closed, drift removed
sact = bpy.data.actions['Standing']
NS = nframes(sact)
stand = [sample(sact, i) for i in range(NS)]
seam = {n: stand[0][n][0].rotation_difference(stand[-1][n][0]) for n in names}   # q0 = seam @ q_last ... per bone
pos = [pel_pos(p[PEL][1]) for p in stand]
mean_xy = Vector((sum(p.x for p in pos) / NS, sum(p.y for p in pos) / NS, 0))
dz = pos[0].z - pos[-1].z
for i, p in enumerate(stand):
    t = i / (NS - 1)
    for n in names:
        q, l = p[n]
        q = Quaternion().slerp(seam[n], t) @ q
        p[n] = (q, l)
    pp = pos[i].copy(); pp.x, pp.y = mean_xy.x + 0.3 * (pp.x - mean_xy.x), mean_xy.y + 0.3 * (pp.y - mean_xy.y)
    pp.z += dz * t
    p[PEL] = (p[PEL][0], pel_loc(pp))
# the Floating legs pedal (knee up to the waist): keep LEG_K of their motion round the clip's mean leg pose
LEG_K = E('LEG_K', 0.4)
for b in LEGS:
    acc = Quaternion((0, 0, 0, 0))
    for p in stand:
        q = p[b][0]; acc = Quaternion([x + (y if acc.dot(q) >= 0 else -y) for x, y in zip(acc, q)])
    mean = acc.normalized()
    for p in stand:
        q = p[b][0]
        p[b] = (mean.slerp(q if q.dot(mean) >= 0 else -q, LEG_K), p[b][1])
# a dangling hover pose like the native frames: knees bent (her right more), thighs a little forward, toes pointed
DANGLE = {'B_R_Thigh': -E('THIGH_R', 14), 'B_L_Thigh': -E('THIGH_L', 6), 'B_R_Calf': E('KNEE_R', 38),
          'B_L_Calf': E('KNEE_L', 22), 'B_R_Foot': E('FOOT_PT', 35), 'B_L_Foot': E('FOOT_PT', 35)}
for p in stand:
    for b, deg in DANGLE.items():
        p[b] = (turn_local(b, p[b][0], 'X', deg), p[b][1])
print('SEAM max deg before', round(max(math.degrees(seam[n].angle) for n in names), 1), 'pelvis drift xy kept 30 %')
write('Standing', stand)
S0 = stand[0]

# ---------------------------------------------------------------- Walking / Running: leaned hover
for name, lean in (('Walking', LEAN_WALK), ('Running', LEAN_RUN)):
    fr = []
    for p in stand:
        q = dict(p)
        q[PEL] = (turn_local(PEL, p[PEL][0], 'X', lean), p[PEL][1])
        q['B_Neck'] = (turn_local('B_Neck', p['B_Neck'][0], 'X', -0.25 * lean), p['B_Neck'][1])
        q['B_Head'] = (turn_local('B_Head', p['B_Head'][0], 'X', -0.35 * lean), p['B_Head'][1])
        for s in 'LR':
            n = f'B_{s}_Thigh'
            q[n] = (turn_local(n, p[n][0], 'X', 0.6 * lean), p[n][1])
            n = f'B_{s}_Foot'
            q[n] = (turn_local(n, p[n][0], 'X', 0.3 * lean), p[n][1])
            n = f'B_{s}_UpperArm'                                           # arms drawn back a little with the speed
            q[n] = (turn_local(n, p[n][0], 'X', 0.4 * lean), p[n][1])
        fr.append(q)
    write(name, fr)

# ---------------------------------------------------------------- actions over the hovering legs
report = {}
for name, (sname, w0, w1, kind) in ACTIONS.items():
    a = bpy.data.actions[sname]
    n_src = nframes(a)
    w1 = n_src - 1 if w1 is None else min(w1, n_src - 1)
    src0 = sample(a, w0); p0 = pel_pos(src0[PEL][1])
    n = w1 - w0 + 1; fr = []
    for i in range(n):
        s = sample(a, w0 + i); st = stand[i % NS]
        q = dict(s)
        t = i / FPS
        dp = pel_pos(s[PEL][1]) - p0
        if kind == 'act':
            for b in LEGS:
                q[b] = st[b]
            q[PEL] = (st[PEL][0].slerp(s[PEL][0] if s[PEL][0].dot(st[PEL][0]) >= 0 else -s[PEL][0], 0.5),
                      pel_loc(pel_pos(st[PEL][1]) + Vector((dp.x * K_XY, dp.y * K_XY, dp.z * K_Z))))
        else:
            k = smooth((t - 0.2) / 0.5)                                    # legs leave the hover pose
            for b in LEGS:
                q[b] = (st[b][0].slerp(s[b][0] if s[b][0].dot(st[b][0]) >= 0 else -s[b][0], k), s[b][1])
            q[PEL] = (s[PEL][0], pel_loc(pel_pos(S0[PEL][1]) + Vector((dp.x * DEATH_XY, dp.y * DEATH_XY, dp.z))))
        fr.append(q)
    # ease from Standing frame 0 and (living actions) back to it
    nb_in = max(1, int(round(BLEND_IN * FPS)))
    for i in range(min(nb_in, n)):
        fr[i] = blend(S0, fr[i], smooth(i / nb_in))
    if kind == 'act':
        nb_out = max(1, int(round(BLEND_OUT * FPS)))
        for k in range(nb_out):
            i = n - 1 - k
            fr[i] = blend(S0, fr[i], smooth(k / nb_out))
    write(name, fr)
    report[name] = {'source': sname, 'window': [w0, w1]}
write('Dead', [dict(fr[-1]) for _ in range(31)])    # Death's last pose held 1 s (the floor pass rewrites it)
scene['flyer_report'] = json.dumps(report)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
