"""Run2 and Sprint for the MM6 Cockatrice (gait rollout q1, 2026-10-31): a two-legged bird run and a wing-assisted
sprint for the chases the walk could not cover.

The Cockatrice chases at 1.12-1.31 (Standard) and 1.96-2.06 (MAW) model units/s on its only gait, Walking (0.503 m in
0.75 s, 0.67): x1.67-1.95 and held at the 2x ceiling with sliding feet. gait_gate.py: run 0.87-1.50, sprint 1.37-2.62.

  Run2    0.665 m in 0.5833 s (28 keys at 48 fps), authored 1.14, duty 0.45: a bird run with short flights;
          body pitched 11 deg, lower, neck stretched, one wing beat per step
  Sprint  0.945 m in 0.5 s (24 keys at 48 fps), authored 1.89, duty 0.32: long bounding strides, the extra stride from
          the body's travel in flight; body pitched 17 deg, tail held out and steadier, full wing beats (wing-assisted
          running), head forward

Both keep Walking's stance sweep (0.30 m about the rest ankle, the most the legs reach) and its phase: the left foot
touches down at 0. Body lowest at mid-stance, highest in flight. The leg, wing, head, tail and floor machinery is
../../mm6_ckt_claude/scripts/anim_ckt.py's, executed unchanged up to its clip table (that script keys every clip when
run). Reads ../../mm6_ckt_claude/work/anim_v1.blend (read only), saves work/ckt_gaits.blend and writes the two clips
(only) to the GLB given as argument, for ../../claude_shared/graft_clips.py.
Run: blender -b --factory-startup ../../mm6_ckt_claude/work/anim_v1.blend -P scripts/gait_ckt.py -- <out clips.glb>"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector

Q1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIM = os.path.normpath(os.path.join(Q1, '..', '..', 'mm6_ckt_claude', 'scripts', 'anim_ckt.py'))
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
source = open(ANIM).read()
A = {'__file__': ANIM, '__name__': 'anim_ckt'}
exec(compile(source[:source.index('\nCLIPS = {')], ANIM, 'exec'), A)
P, rig, mesh = A['P'], A['rig'], A['mesh']
body, head, tail, wing, place_leg, rest_ankle = (A[k] for k in ('body', 'head', 'tail', 'wing', 'place_leg',
                                                              'rest_ankle'))
ss, W = A['ss'], A['W']
FPS = 48
SWEEP = 0.30                                    # Walking's stance sweep (anim_ckt STRIDE)
CLIPS = {
    'Run2': dict(frames=28, speed=1.14, duty=0.45, base=-0.018, bob=0.010, pitch=11, chest=-2, roll=2.5, side=0.004,
                 yaw=2, lift=0.085, toe=30, hpitch=6, reach=7, tlift=-1.2, sway=4, up=10, flap=30, elbow=8, fan=8),
    'Sprint': dict(frames=24, speed=1.89, duty=0.32, base=-0.022, bob=0.016, pitch=17, chest=-3, roll=2.0, side=0.003,
                   yaw=1.5, lift=0.10, toe=35, hpitch=10, reach=12, tlift=-1.0, sway=3, up=14, flap=38, elbow=10, fan=10),
}
MISS = []


def leg_phase(q, c):
    """Ankle offset along travel (+ forward), lift and toe pitch for leg phase q: stance sweeps SWEEP back under the
    body at the body's speed (stride x duty = SWEEP); the swing lifts the foot and brings it forward."""
    duty = c['duty']
    if q < duty:
        return SWEEP * (0.5 - q / duty), 0.0, 0.0
    u = (q - duty) / (1 - duty)
    return SWEEP * (-0.5 + ss(u)), c['lift'] * math.sin(math.pi * u), c['toe'] * math.sin(math.pi * u)


def run_pose(p, c):
    P.reset(rig)
    w = 2 * math.pi * p
    step = 4 * math.pi * (p - c['duty'] / 2)        # two steps per loop; 0 at the left foot's mid-stance
    body(lift=c['base'] - c['bob'] * math.cos(step), pitch=c['pitch'] + 1.5 * math.cos(step), chest=c['chest'],
         roll=c['roll'] * math.sin(w), side=c['side'] * math.sin(w), yaw=c['yaw'] * math.sin(w))
    head(pitch=c['hpitch'] + 3 * math.cos(step + 0.8), reach=c['reach'] + 3 * math.cos(step + 0.4),
         yaw=-2 * math.sin(w))
    tail(p * c['frames'] / FPS, sway=c['sway'], freq=FPS / c['frames'], lift=c['tlift'] - 1.2 * math.cos(step + 0.6))
    flap = math.cos(step + math.pi)                 # wings up in flight, the downstroke through each stance
    for s in 'LR':
        wing(s, up=c['up'] + c['flap'] * flap, elbow=c['elbow'] + 0.5 * c['flap'] * math.cos(step + math.pi - 0.5),
             fan=-4 + c['fan'] * max(0.0, -flap), curl=8 * math.sin(step - 0.8))
        dy, dz, toe = leg_phase((p + (0.0 if s == 'L' else 0.5)) % 1.0, c)
        target = rest_ankle(s, dy=-dy, dz=dz)
        place_leg(s, target, tarsus_pitch=dz * 120, toe_pitch=toe)
        miss = (W(f'Foot_{s}') - target).length
        if miss > 0.002:
            MISS.append((s, round(p, 3), round(miss * 1000, 1)))
    A['tail_floor']()


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, feet = [], [], []
    for f in range(n + 1):
        fn((f % n) / n)
        co = A['mesh_co']()
        lows.append(float(co[:, 2].min()))
        feet.append(float(co[A['LEGS'], 2].min()))
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
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return lows, feet


info = {}
for name, c in CLIPS.items():
    MISS.clear()
    lows, feet = key_action(name, c['frames'], lambda p: run_pose(p, c))
    T = c['frames'] / FPS
    info[name] = {'seconds': T, 'stride': round(c['speed'] * T, 4), 'authored_speed': c['speed'],
                  'duty': c['duty'], 'sweep': SWEEP, 'lowest': [min(lows), max(lows)],
                  'feet_lowest': [min(feet), max(feet)], 'ankle_miss_mm': max([m for _, _, m in MISS], default=0.0)}
    print(f'CLIP {name}: {T:.4f} s, stride {c["speed"] * T:.4f}, lowest {min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} '
          f'cm, feet {min(feet) * 100:+.2f}..{max(feet) * 100:+.2f} cm, ankle misses {MISS[:8]}', flush=True)
    assert c['frames'] / FPS * c['speed'] * c['duty'] - SWEEP < 0.01, name
json.dump(info, open(os.path.join(Q1, 'work', 'ckt_gaits_info.json'), 'w'), indent=1)
P.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Q1, 'work', 'ckt_gaits.blend'))
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
