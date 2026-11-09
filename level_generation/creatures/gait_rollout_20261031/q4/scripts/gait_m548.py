"""Walk2 and Run2 for the MM8 Crystal Dragon (m548, wingless crystal quadruped), gait rollout package q4 (2026-10-31),
authored for the game's speeds (gait_gate.py targets; MAW leaves them unchanged): it wanders at 0.71-0.84 and chases
at 1.43-1.67 model units/s. The installed Walking (0.32 m in 1.0 s, 0.32) and Running (0.43 m in 0.75 s, 0.57) are
both trots: wandering played Running x1.25-1.47 and chasing x2.48-2.92 (held at the 2x ceiling, sliding).

  Walk2  trot as Walking and Running (front L + hind R at 0), duty 0.52: the wander. Sweep 0.26 m (Running 0.24).
  Run2   transverse gallop (front L 0, front R .1, hind L .55, hind R .65; front L at 0 as the walk), duty 0.32, a
         gathered flight after the fore legs and a short extended one after the hinds, the back flexing (arched as the
         hinds swing under, stretched as the fores reach), the body pitching nose-down as the fores land and the
         head steadied against it.

The leg machinery is ../../mm8_m548_codex/scripts/motion.py's, imported unchanged: front legs two-bone IK to the paw,
hind legs two-bone IK to the hock with the tarsus held at the paw's pitch, the paw keeping its rest orientation (only
pitched in the swing), footholds about the rest paws. Additions: the swing paw is raised by its toe's drop (q3's
Gorgon), harmonics for bob, pitch, flex and head nod, and motion.py's floor rule (the body lifted when a vertex dips
under -3 mm).

Reads the project's editable master (read only), saves <package>/work/m548_gaits.blend and writes only the new clips
to the GLB given, to be grafted onto the installed source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P gait_m548.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q4 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm8_m548_codex', 'export', 'mm8_m548.blend'))
sys.path.insert(0, os.path.join(CREATURES, 'mm8_m548_codex', 'scripts'))
_rig = bpy.data.objects['CrystalDragonRig']
if _rig.animation_data:
    _rig.animation_data.action = None                                        # the master's rest, not a clip
import motion as M  # noqa: E402  (binds the open file's rig and mesh)

rig, mesh = M.rig, M.mesh
FPS = 48
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
TROT = {('front', 'L'): 0.0, ('hind', 'R'): 0.0, ('front', 'R'): 0.5, ('hind', 'L'): 0.5}
GALLOP = {('front', 'L'): 0.0, ('front', 'R'): 0.1, ('hind', 'L'): 0.55, ('hind', 'R'): 0.65}
# speed (model units/s), frames at 48 fps, footfalls, duty, paw lift front/hind (sin^lift_pow), swing pitch (deg,
# + = toes down), front reach / hind trail in the swing (m), body drop and bob (bob_harm a loop, lowest at bob_phase),
# pitch rocking (deg, + = nose down, rock_harm a loop, most nose-down at rock_phase), back flex (deg, + = arched, most
# at flex_phase), head nod (deg, + = down, nod_harm a loop, most at nod_phase), neck steadying share, spine and tail
# sway (deg)
COMMON = dict(lift_pow=1.0, reach=0.0, trail=0.0, bob_harm=2, rock=0.0, rock_harm=2, rock_phase=0.0, flex=0.0,
              flex_phase=0.0, nod=0.0, nod_harm=2, nod_phase=0.0, sway=2.0, tail=5.0)
CLIPS = {
    # Walking: 1.0 s, 0.32 m, duty 0.62, lift 0.045, pitch 12, drop -0.028 +- 0.008 twice a loop (lowest at 0.25).
    'Walk2': dict(COMMON, speed=0.74, frames=32, feet=TROT, duty=0.52, lift_f=0.05, lift_h=0.045, pitch=18.0,
                  drop=-0.034, bob=0.007, bob_phase=0.25, rock=0.8, rock_phase=0.0, nod=1.5, nod_phase=0.3,
                  sway=2.5, tail=6.0),
    'Run2': dict(COMMON, speed=1.46, frames=27, feet=GALLOP, duty=0.32, lift_f=0.075, lift_h=0.065, lift_pow=0.8,
                 pitch=35.0, reach=0.02, trail=0.03, drop=-0.035, bob=0.012, bob_harm=1, bob_phase=0.2, rock=3.0,
                 rock_harm=1, rock_phase=0.15, flex=8.0, flex_phase=0.5, nod=-2.0, nod_harm=1, nod_phase=0.15,
                 sway=1.0, tail=4.0),
}
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):          # tuning: "Clip:key=value,..."
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = float(_v)

PAW = {(k, s): rig.pose.bones[('FrontPaw_' if k == 'front' else 'HindPaw_') + s].length
       for k in ('front', 'hind') for s in 'LR'}
MISS = []


def smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def gait(phase, c, stride):
    M.posing.reset(rig)
    w = lambda harm, ph: math.cos(2 * math.pi * harm * (phase - ph))          # noqa: E731
    M.root((0, 0, c['drop'] - c['bob'] * w(c['bob_harm'], c['bob_phase'])))
    pitch = c['rock'] * w(c['rock_harm'], c['rock_phase'])
    flex = c['flex'] * w(1, c['flex_phase'])
    M.rot('Spine1', X, pitch)
    M.rot('Spine2', X, flex * 0.5); M.rot('Spine3', X, flex * 0.5)
    M.rot('Spine2', Z, c['sway'] * math.sin(2 * math.pi * phase))
    # the neck takes back the pitch and the flex (the head stays steady), then nods
    nod = c['nod'] * w(c['nod_harm'], c['nod_phase'])
    M.rot('Neck1', X, -0.7 * (pitch + flex) + 0.5 * nod); M.rot('Head', X, 0.5 * nod)
    M.rot('Neck1', Z, -c['sway'] * math.sin(2 * math.pi * phase))
    duty = c['duty']; distance = stride * duty
    for key, touch in c['feet'].items():
        q = (phase - touch) % 1
        kind, side = key
        if q < duty:
            dy = -distance / 2 + stride * q
            dz = p = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = distance / 2 - distance * smooth(u)
            dz = (c['lift_f'] if kind == 'front' else c['lift_h']) * math.sin(math.pi * u) ** c['lift_pow']
            p = c['pitch'] * math.sin(math.pi * u)
            dz += PAW[key] * math.sin(math.radians(p)) * 0.6                 # the toe-down paw's tip clears
            if kind == 'front':
                dy -= c['reach'] * math.sin(math.pi * min(1.0, max(0.0, (u - 0.4) / 0.6)))
            else:
                dy += c['trail'] * math.sin(math.pi * min(1.0, u / 0.45))
        M.leg(kind, side, (0, dy, dz), p)
        if q < duty:
            name = ('FrontPaw_' if kind == 'front' else 'HindPaw_') + side
            MISS.append(((rig.pose.bones[name].head - (M.REST[name].translation + Vector((0, dy, dz)))).length,
                         name, round(q, 2)))
    M.rot('Tail1', Z, c['tail'] * math.sin(2 * math.pi * phase)); M.rot('Tail2', Z, c['tail'] * 0.6 *
                                                                       math.sin(2 * math.pi * phase - .5))
    low = float(M.co()[:, 2].min())
    if low < -.003:                                                           # motion.py's floor rule
        M.root((0, 0, -low))
    return low


info = {}
for name, c in CLIPS.items():
    n = int(c['frames']); T = n / FPS; stride = c['speed'] * T
    rig.animation_data_create(); rig.animation_data.action = None
    frames, lows = [], []
    MISS.clear()
    for f in range(n + 1):
        gait((f % n) / n, c, stride)
        lows.append(float(M.co()[:, 2].min()))
        frames.append({b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in rig.pose.bones})
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    previous = {}
    for f, frame in enumerate(frames):
        for b in rig.pose.bones:
            loc, q = frame[b.name]
            if b.name in previous and q.dot(previous[b.name]) < 0:
                q = -q
            previous[b.name] = q
            b.location, b.rotation_quaternion = loc, q
            b.keyframe_insert('location', frame=f); b.keyframe_insert('rotation_quaternion', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    worst = max(MISS)
    info[name] = dict({k: v for k, v in c.items() if k != 'feet'}, seconds=T, stride=stride,
                      sweep=stride * c['duty'], lowest=[min(lows), max(lows)], planted_miss=worst[0])
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f}, sweep {stride * c["duty"]:.3f}, lowest vertex '
          f'{min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} cm, worst planted paw miss {worst[0] * 1000:.1f} mm '
          f'({worst[1]} at stance {worst[2]}); over 5 mm: {len([m for m in MISS if m[0] > .005])}', flush=True)
json.dump(info, open(os.path.join(HERE, 'work', 'm548_gaits_info.json'), 'w'), indent=1)
M.posing.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'm548_gaits.blend'))
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
