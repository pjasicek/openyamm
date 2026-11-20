"""Run2 for the MM7 Chicken (7m504, zchicken a-c, two-legged hen), gait rollout package q4 (2026-10-31).

The hen wanders at 0.98 and chases at 1.95 model units/s (both rulesets; MAW leaves it unchanged). Its run was bound to
Walking (0.40 m in 0.4333 s, 0.92), so it chased on the walk at x2.12, held at the 2x ceiling with sliding feet.
gait_gate.py: run 1.30-2.60.

  Run2   0.552 m in 0.30 s (18 keys at 60 fps), authored 1.84, duty 0.40: a hen's run with short flights (Froude
         number 1.7), body leaning forward 12 deg and lowest at mid-stance, neck stretched forward and the head held
         level and steadier than in the walk (a smaller thrust), wings held a little out from the body and beating
         lightly for balance, tail lowered, feet lifted higher and the toes curled in the swing.

It keeps Walking's stance sweep (0.22 m, the legs' reach) and its phase: the left foot touches down at 0. The
footholds sit `back` (4 cm) behind Walking's and the hips 3 cm lower: centred like Walking's, the ankle missed its
target by 42 mm at touchdown. The leg, body,
wing, tail and floor machinery is ../../mm7_7m504_claude/scripts/anim_chicken.py's, executed unchanged up to its clip
table (that script keys every clip when run). Reads ../../mm7_7m504_claude/work/anim_v2u.blend (read only), saves
work/m504_gaits.blend and writes only the new clip to the GLB given, for ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P scripts/gait_m504.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
from mathutils import Vector

Q4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.normpath(os.path.join(Q4, '..', '..', 'mm7_7m504_claude'))
ANIM = os.path.join(PROJECT, 'scripts', 'anim_chicken.py')
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
sys.argv = [sys.argv[0], '--', os.path.join(PROJECT, 'work', 'anim_v2u.blend'), '-']   # anim_chicken.py's arguments
source = open(ANIM).read()
A = {'__file__': ANIM, '__name__': 'anim_chicken'}
exec(compile(source[:source.index('\nCLIPS = {')], ANIM, 'exec'), A)
P, rig, MESH = A['P'], A['rig'], A['MESH']
body, wings, tail, place_leg, ss, ANKLE = (A[k] for k in ('body', 'wings', 'tail', 'place_leg', 'ss', 'ANKLE'))
FPS = 60
CLIPS = {
    'Run2': dict(frames=18, speed=1.84, duty=0.40, lift=0.065, toe=-40, bob=0.007, base=-0.03, pitch=-12, neck=-6,
                 head=14, thrust=5, wing=9, flap=5, tail_lift=-4, sway=3, roll=3, yaw=2, back=0.04),
}
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):          # tuning: "Clip:key=value,..."
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = float(_v)
MISS = []


def run_pose(p, c, stride):
    P.reset(rig)
    duty = c['duty']; s = stride * duty
    step = 4 * math.pi * (p - duty / 2)              # two steps a loop; 0 at the left foot's mid-stance
    q2 = (2 * p) % 1.0                               # the head thrusts forward once a step, smaller than the walk's
    thrust = c['thrust'] * (ss(q2 / 0.35) if q2 < 0.35 else 1 - ss((q2 - 0.35) / 0.65))
    body(hips_d=Vector((0, 0, c['base'] - c['bob'] * math.cos(step))),
         hips_pitch=c['pitch'] + 1.5 * math.cos(step), hips_roll=c['roll'] * math.sin(2 * math.pi * p),
         hips_yaw=c['yaw'] * math.sin(2 * math.pi * p), neck_pitch=c['neck'], head_pitch=c['head'],
         head_thrust=thrust - 6)
    wings(c['wing'] + c['flap'] * math.cos(step + math.pi))
    tail(c['sway'], p, lift=c['tail_lift'])
    for side, ph in (('L', 0.0), ('R', 0.5)):
        q = (p + ph) % 1.0
        if q < duty:
            dy = s / 2 - s * (q / duty); dz = 0.0; pitch = 0.0          # planted: slides back (body moves -Y)
        else:
            u = (q - duty) / (1 - duty)
            dy = -s / 2 + s * ss(u); dz = c['lift'] * math.sin(math.pi * u) ** 0.8; pitch = c['toe'] * math.sin(math.pi * u)
        target = ANKLE[side] + Vector((0, -dy + c['back'], dz))
        place_leg(side, target, pitch)
        miss = ((rig.matrix_world @ rig.pose.bones[f'Foot_{side}'].head) - target).length
        if q < duty:
            MISS.append((miss, side, round(q, 2)))


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = None
    poses, lows = [], []
    for f in range(n + 1):
        fn((f % n) / n)
        lows.append(float(A['mesh_co']()[:, 2].min()))
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
            prev[b.name] = q; b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return lows


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
info = {}
for name, c in CLIPS.items():
    n = int(c['frames']); T = n / FPS; stride = c['speed'] * T
    MISS.clear()
    lows = key_action(name, n, lambda p: run_pose(p, c, stride))
    info[name] = dict(c, seconds=T, stride=round(stride, 4), sweep=stride * c['duty'], lowest=[min(lows), max(lows)],
                      planted_miss_mm=max(MISS)[0] * 1000)
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f}, sweep {stride * c["duty"]:.3f}, lowest '
          f'{min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} cm, worst planted ankle miss {max(MISS)[0] * 1000:.1f} mm '
          f'({max(MISS)[1]} at stance {max(MISS)[2]}), over 5 mm: {sorted(m for m in MISS if m[0] > .005)[-6:]}',
          flush=True)
json.dump(info, open(os.path.join(Q4, 'work', 'm504_gaits_info.json'), 'w'), indent=1)
P.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Q4, 'work', 'm504_gaits.blend'))
for a in list(bpy.data.actions):
    if a.name not in CLIPS:
        bpy.data.actions.remove(a)
for o in bpy.data.objects:
    o.select_set(o in (MESH, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
