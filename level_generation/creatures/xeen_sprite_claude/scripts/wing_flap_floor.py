"""Wing flutter, floor pass, Dead and event times for the Killer Sprite.
Wings: each wing turns about the spine's up axis through its own root (bone head): sweep angle behind the back plane
= BASE + AMP sin(2 pi f t + phase), the lower wings PHASE_LOW of a cycle behind the upper ones (a figure-of-eight
beat), the right wings mirrored. Loops get a whole number of beats (f near F_STAND / F_WALK / F_RUN Hz); one-shot
clips beat at F_ACT. Death: the beat dies out between DEATH_STOP0 and DEATH_STOP1 s and the wings fold shut behind
the back (FOLD deg).
Floor (flyer rule, no hover lift, no z_offset): every living loop is shifted so its lowest point over the clip (wing
tips included) meets the floor; one-shot actions keep Standing's shift and are raised only on frames that would cut
the floor (a constant per-clip shift popped the attack 10 cm up at its start); Death keeps the lowest point on the floor on every frame once it falls (blended from
the Standing shift over the first 0.3 s), so the corpse rests on the floor; Dead = Death's last pose held 1 s.
Events: Attack impact = peak speed of the right fingertips; Cast release = the frame where both palms are furthest
forward (-Y). Source actions (Src*) are deleted. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
FPS = 30
BASE, AMP, PHASE_LOW = E('BASE', 20), E('AMP', 18), E('PHASE_LOW', 0.15)
F_STAND, F_WALK, F_RUN, F_ACT = E('F_STAND', 6.0), E('F_WALK', 6.5), E('F_RUN', 7.5), E('F_ACT', 6.0)
FOLD, DEATH_STOP0, DEATH_STOP1 = E('FOLD', 78), E('DEATH_STOP0', 0.35), E('DEATH_STOP1', 1.0)
SWEEP = E('SWEEP', 22)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; wings = bpy.data.objects['Wings']
for a in [a for a in bpy.data.actions if a.name.startswith('Src')]:
    bpy.data.actions.remove(a)
WINGS = {'Wing_L_Up': (1, 0.0), 'Wing_L_Low': (1, PHASE_LOW), 'Wing_R_Up': (-1, 0.0), 'Wing_R_Low': (-1, PHASE_LOW)}
SP = rig.data.bones['B_Spine2']
PEL = 'B_Pelvis'
RPEL = rig.data.bones[PEL].matrix_local.to_3x3().normalized()
LOOPS = {'Standing': F_STAND, 'Walking': F_WALK, 'Running': F_RUN}
CLIPS = ['Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Fidget', 'Death']


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def nframes(act):
    return int(round(act.frame_range[1] - act.frame_range[0])) + 1


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lowest():
    deps = bpy.context.evaluated_depsgraph_get(); z = 1e9
    for o in (body, wings):
        ev = o.evaluated_get(deps); me = ev.to_mesh()
        c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c)
        z = min(z, float((np.array(o.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(len(me.vertices))].T)[2].min()))
        ev.to_mesh_clear()
    return z


report = {}
for name in CLIPS:
    act = bpy.data.actions[name]; set_act(act); n = nframes(act)
    dur = (n - 1) / FPS
    if name in LOOPS:
        f = max(1, round(LOOPS[name] * dur)) / dur
    else:
        f = F_ACT
    for i in range(n):
        t = i / FPS
        scene.frame_set(i)
        sp = rig.pose.bones['B_Spine2'].matrix @ SP.matrix_local.inverted()      # spine motion since rest
        for wb, (sg, ph) in WINGS.items():
            ang = BASE + AMP * math.sin(2 * math.pi * (f * t - ph))
            if name == 'Death':
                k = smooth((t - DEATH_STOP0) / (DEATH_STOP1 - DEATH_STOP0))
                ang = (1 - k) * ang + k * FOLD
            rest = rig.data.bones[wb].matrix_local
            h = rest.translation
            R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(ang - SWEEP) * sg, 4, 'Z') @ Matrix.Translation(-h)
            pb = rig.pose.bones[wb]; pb.rotation_mode = 'QUATERNION'
            pb.matrix = sp @ R @ rest
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
            pb.keyframe_insert('location', frame=i)
    report[name] = {'frames': n, 'beat_hz': round(f, 3)}
# floor pass
pel_loc = {}
def pelvis_keys(act):
    fc = [c for c in (act.fcurves if hasattr(act, 'fcurves') and len(act.fcurves) else
          [c for l in act.layers for s in l.strips for cb in s.channelbags for c in cb.fcurves])
          if c.data_path == f'pose.bones["{PEL}"].location']
    return sorted(fc, key=lambda c: c.array_index)


stand_shift = None
for name in CLIPS:
    act = bpy.data.actions[name]; set_act(act); n = nframes(act)
    lows = []
    for i in range(n):
        scene.frame_set(i); lows.append(lowest())
    lows = np.array(lows)
    if name in LOOPS:
        sh = np.full(n, -lows.min())
        if name == 'Standing':
            stand_shift = float(sh[0])
    elif name != 'Death':                     # one-shot actions keep Standing's height, raised only where they would cut
        sh = np.maximum(stand_shift, -lows)
    else:
        sh = np.empty(n)
        for i in range(n):
            k = smooth((i / FPS) / 0.3)
            sh[i] = max((1 - k) * stand_shift + k * (-lows[i]), -lows[i])
    fcs = pelvis_keys(act)
    for i in range(n):
        d = RPEL.inverted() @ Vector((0, 0, float(sh[i])))
        for c in fcs:
            for kp in c.keyframe_points:
                if abs(kp.co[0] - i) < 1e-3:
                    kp.co[1] += d[c.array_index]; kp.handle_left[1] += d[c.array_index]; kp.handle_right[1] += d[c.array_index]
    for c in fcs:
        c.update()
    after = []
    for i in range(n):
        scene.frame_set(i); after.append(lowest())
    report[name].update({'shift_cm': round(float(sh.mean()) * 100, 1), 'lowest_cm_min': round(min(after) * 100, 2),
                         'lowest_cm_max': round(max(after) * 100, 2), 'lowest_cm_last': round(after[-1] * 100, 2)})
    print('FLOOR', name, json.dumps(report[name]))
# Dead = Death's last pose, 1 s
dact = bpy.data.actions['Death']; set_act(dact); last = nframes(dact) - 1; scene.frame_set(last)
pose = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
old = bpy.data.actions.get('Dead')
if old:
    bpy.data.actions.remove(old)
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True; set_act(dead)
for i in (0, 30):
    for nm, (q, l) in pose.items():
        pb = rig.pose.bones[nm]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=i); pb.keyframe_insert('location', frame=i)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
scene.frame_set(0); print('FLOOR Dead lowest cm', round(lowest() * 100, 2))
# events
def bone_track(act, bn, tip=False):
    set_act(act); P = []
    for i in range(nframes(act)):
        scene.frame_set(i); pb = rig.pose.bones[bn]
        P.append(np.array(rig.matrix_world @ (pb.tail if tip else pb.head)))
    return np.array(P)
att = bpy.data.actions['Attack']
tipR = bone_track(att, 'B_R_Finger22', tip=True) if 'B_R_Finger22' in rig.pose.bones else bone_track(att, 'B_R_Hand', True)
sp = np.linalg.norm(np.diff(tipR, axis=0), axis=1) * FPS
ia = int(np.argmax(sp)) + 1
cast = bpy.data.actions['Cast']
pl = bone_track(cast, 'B_L_Hand'); pr = bone_track(cast, 'B_R_Hand')
fwd = -(pl[:, 1] + pr[:, 1]) / 2
ic = int(np.argmax(fwd))
report['events'] = {'attack_impact_s': round(ia / FPS, 3), 'attack_peak_tip_speed_mps': round(float(sp.max()), 2),
                    'cast_release_s': round(ic / FPS, 3), 'cast_palms_forward_m': round(float(fwd[ic] - fwd[0]), 3)}
print('EVENTS', json.dumps(report['events']))
scene['flap_floor_report'] = json.dumps(report)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
