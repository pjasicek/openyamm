"""Gait pass (2026-10-21): two new locomotion clips on the clip master, for the game's speeds.

The engine plays a walk or run one loop per stride of travel, and moves the walker at 2.03-2.75 model units/s
wandering and 4.06-5.51 chasing (tiers C-A). The installed Walking (0.70 m per 1.0 s) and Running (1.00 m per
0.75 s) therefore played at 1.5-2.1x and 3.0-4.1x. The new clips are authored for those speeds (gait_gate.py
targets: walk 2.36, run 4.72 model units per second):

  Walk2  0.75 s loop, 1.74 m per cycle (2.32 /s): a long, low stalking stride. Duty 0.52 (always a foot down),
         the body drops at double support so the straight leg reaches 0.45 m ahead and behind the hip, rises over
         the planted leg (inverted pendulum, 8 cm), pelvis yaw into the reaching leg, chest counter-turns, head
         steady, arms swing opposite the legs.
  Run2   0.625 s loop, 2.95 m per cycle (4.72 /s): a run with a flight phase. Duty 0.28, the body lowest at
         mid-stance and highest in flight, trunk leaned 14 deg forward with the head pulled up to look ahead,
         heels kick up behind in swing, elbows flexed and arms pumping.

Both: soles planted flat and sliding back at exactly the body speed (two-bone IK, knee forward), a slightly
narrower track than at rest so the extended leg reaches. Existing clips are untouched. Writes
work/anim_gait2.blend and the donor GLB (every action, the project's export settings) for add_clips.py.
Usage: blender -b -P anim_gait2.py -- [work/anim_v2.blend work/anim_gait2.blend work/gait2_donor.glb]"""
import json, math, os, sys, bpy
from mathutils import Matrix, Vector, Euler
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src, dst, glb = (a + ['work/anim_v2.blend', 'work/anim_gait2.blend', 'work/gait2_donor.glb'][len(a):])[:3]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 48
GAITS = {
    'Walk2': dict(dur=.75, stride=1.74, duty=.52, lift=.12, pitch=14, low=.15, high=.07, k0=.30, k1=.10,
                  track=.05, hip_yaw=7, chest_yaw=4, roll=2.5, lean=(2, 1, 1, -3, -1), arm=18, fore=10,
                  fore_pump=8),
    'Run2': dict(dur=.625, stride=2.95, duty=.28, lift=.30, pitch=22, k0=.55, k1=.15, track=.06, hip_yaw=5,
                 chest_yaw=6, roll=1.5, lean=(5, 4, 5, -8, -6), arm=26, fore=30, fore_pump=10,
                 mid=.17, flight=.085),
}

bpy.ops.wm.open_mainfile(filepath=os.path.join(P, src))
scene = bpy.context.scene; scene.render.fps = FPS
rig = bpy.data.objects['CrystalRig']; body = bpy.data.objects['CrystalWalker']
data = rig.data
REST = {b.name: b.matrix_local.copy() for b in data.bones}
HEAD = {b.name: b.head_local.copy() for b in data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in data.bones}
ORDER = [b.name for b in data.bones]
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
REACH = {}


def leg_ik(deltas, s, ank_n, pitch=0.0):
    """two-bone IK of one leg from the posed hip to a world ankle target (knee forward), foot level plus pitch;
    returns how far the ankle falls short of the target (0 when reachable)"""
    hip, knee, ank = HEAD[s + 'Thigh'], HEAD[s + 'Shin'], HEAD[s + 'Foot']
    hip_n = deltas['Hips'] @ hip
    ax = ank_n - hip_n; want = ax.length; ax.normalize()
    la = (knee - hip).length; lb = (ank - knee).length
    dist = min(want, (la + lb) * .995)
    along = (la * la - lb * lb + dist * dist) / (2 * dist)
    pole = Vector((0, -1, 0)); pole = (pole - ax * pole.dot(ax)).normalized()
    knee_n = hip_n + ax * along + pole * math.sqrt(max(0, la * la - along * along))
    end = hip_n + ax * dist
    for n, s0, e0, s1, e1 in ((s + 'Thigh', hip, knee, hip_n, knee_n), (s + 'Shin', knee, ank, knee_n, end)):
        turn = (e0 - s0).rotation_difference(e1 - s1).to_matrix().to_4x4()
        deltas[n] = Matrix.Translation(s1) @ turn @ Matrix.Translation(-s0)
    deltas[s + 'Foot'] = (Matrix.Translation(end) @ Euler((math.radians(pitch), 0, 0)).to_matrix().to_4x4()
                          @ Matrix.Translation(-ank))
    return want - dist


def height(g, ph):
    """pelvis drop (negative z) over the cycle"""
    if 'mid' in g:   # run: lowest at mid-stance (q = duty/2), highest in mid-flight
        flight = (g['duty'] + .5) / 2
        c = (g['mid'] + g['flight']) / 2; b = (g['mid'] - g['flight']) / 2
        return -c + b * math.cos(4 * math.pi * (ph - flight))
    # walk: highest over the planted leg (mid-stance), lowest at double support
    c = (g['low'] + g['high']) / 2; b = (g['low'] - g['high']) / 2
    return -c + b * math.cos(4 * math.pi * (ph - g['duty'] / 2))


def foot(g, q):
    """(forward travel of the ankle from its rest foothold, lift, pitch) at foot phase q (0 = touchdown in front)"""
    duty, stride = g['duty'], g['stride']
    if q < duty:
        return (duty / 2 - q) * stride, 0.0, 0.0
    u = (q - duty) / (1 - duty)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h01 = -2 * u ** 3 + 3 * u ** 2
    h10 = u ** 3 - 2 * u ** 2 + u; h11 = u ** 3 - u ** 2
    v = stride * (1 - duty)                      # ground speed in swing-phase units
    travel = h00 * (-duty / 2 * stride) + h01 * (duty / 2 * stride) - h10 * g['k0'] * v - h11 * g['k1'] * v
    s = math.sin(math.pi * u)
    pitch = -g['pitch'] * s * s                  # toe up through the swing
    lift = g['lift'] * s * s + .07 * math.sin(math.radians(-pitch))   # heel kept clear of the floor while pitched
    return travel, lift, pitch


def pose(clip, t):
    g = GAITS[clip]; ph = t / g['dur']
    c = math.cos(2 * math.pi * ph); sw = math.sin(2 * math.pi * ph)
    hips_l, waist_l, chest_l, neck_l, head_l = g['lean']
    hy, cy = g['hip_yaw'], g['chest_yaw']
    # left foot touches down in front at ph 0: the left hip turns forward (negative z), arms swing opposite the legs
    ang = {
        'Hips': (hips_l, g['roll'] * sw, -hy * c),
        'Waist': (waist_l, 0, .5 * (hy + cy) * c),
        'Chest': (chest_l, -.5 * g['roll'] * sw, .5 * (hy + cy) * c),
        'Neck': (neck_l, 0, -.5 * cy * c),
        'Head': (head_l, 0, -.5 * cy * c),
        'LeftArm': (g['arm'] * c, 0, 0), 'RightArm': (-g['arm'] * c, 0, 0),
        # elbows: a constant flex plus a pump on the forward swing
        'LeftForeArm': (-g['fore'] - g['fore_pump'] * max(0.0, -c), 0, 0),
        'RightForeArm': (-g['fore'] - g['fore_pump'] * max(0.0, c), 0, 0),
        'LeftHand': (-.25 * g['fore'], 0, 0), 'RightHand': (-.25 * g['fore'], 0, 0),
        'LeftShoulder': (0, 0, 3 * c), 'RightShoulder': (0, 0, 3 * c),
    }
    deltas = {}
    for n in ORDER:
        if n == 'Root':
            deltas[n] = Matrix.Translation((0, 0, height(g, ph)))
            continue
        h = HEAD[n]; pd = deltas[PARENT[n]]
        r = Euler(tuple(math.radians(x) for x in ang.get(n, (0, 0, 0))), 'XYZ').to_matrix().to_4x4()
        deltas[n] = pd @ Matrix.Translation(h) @ r @ Matrix.Translation(-h)
    for s, shift, side in (('Left', 0.0, 1), ('Right', .5, -1)):
        travel, lift, pitch = foot(g, (ph + shift) % 1)
        target = HEAD[s + 'Foot'] + Vector((-side * g['track'], -travel, lift))
        short = leg_ik(deltas, s, target, pitch)
        if lift == 0.0:
            REACH[clip] = max(REACH.get(clip, 0.0), short)
    world = {n: deltas[n] @ REST[n] for n in ORDER}
    for n in ORDER:
        p = PARENT[n]
        rr = REST[p].inverted() @ REST[n] if p else REST[n]
        pr = world[p].inverted() @ world[n] if p else world[n]
        rig.pose.bones[n].matrix_basis = rr.inverted() @ pr


def floor_min():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear(); return z


report = {}
for clip, g in GAITS.items():
    old = bpy.data.actions.get(clip)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(clip); act.use_fake_user = True; rig.animation_data.action = act
    frames = round(g['dur'] * FPS); prev = {}; lows = []
    for fr in range(frames + 1):
        scene.frame_set(fr + 1); pose(clip, fr / FPS); bpy.context.view_layer.update()
        lows.append(round(floor_min(), 4))
        for pb in rig.pose.bones:
            if pb.name in prev and prev[pb.name].dot(pb.rotation_quaternion) < 0:
                pb.rotation_quaternion.negate()
            prev[pb.name] = pb.rotation_quaternion.copy()
            for path in ('location', 'rotation_quaternion', 'scale'):
                pb.keyframe_insert(path, frame=fr + 1, group=pb.name)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
    report[clip] = {'duration': frames / FPS, 'stride': g['stride'], 'speed': round(g['stride'] / g['dur'], 3),
                    'floor_min': min(lows), 'floor_max': max(lows), 'reach_short_mm': round(REACH.get(clip, 0) * 1000, 2)}
    print('CLIP', clip, report[clip], flush=True)
rig.animation_data.action = bpy.data.actions['Standing']; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, dst))
for o in bpy.data.objects:
    o.select_set(o in (rig, body))
bpy.ops.export_scene.gltf(filepath=os.path.join(P, glb), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_skins=True, export_all_influences=False, export_attributes=False, export_extras=True,
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(os.path.join(P, 'work', 'gait2_report.json'), 'w'), indent=1)
