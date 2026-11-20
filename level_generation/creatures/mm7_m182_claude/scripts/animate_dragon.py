"""Native-informed MM7 Dragon clips, 24 fps, in place (adapted from mm8_m492_claude/scripts/animate_dragon.py).

Native MM7 timing (mm7_m182/manifest.json): flight loop m183w 0.9375 s (6 frames + standing), attack m183a
0.875 s with the bite/breath at frame ad (~0.5 s), hit m183n 0.875 s, death m183d 1.25 s ending flat on the floor.
Standing/Walking/Running/Fidget are flight loops (MM7 dragons always fly). Floor rule: one constant lift per clip
family so no vertex goes below z = 0; Death settles body, limbs, tail and wings on the floor.
Writes work/anim_v1.blend, work/clips.json and review/anim/*.png."""
import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
P = Path(__file__).resolve().parents[1]
SOURCE = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else str(P / 'work/rig_v1.blend')
OUTPUT = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv else str(P / 'work/anim_v1.blend')
bpy.ops.wm.open_mainfile(filepath=SOURCE)
rig = bpy.data.objects['Rig']; o = bpy.data.objects['Body']; sc = bpy.context.scene; sc.render.fps = 24
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
axes = {n: b.matrix_local.to_3x3().inverted() for n, b in rig.data.bones.items()}
rest = np.array([v.co[:] for v in o.data.vertices]); wing = np.array([v.value for v in o.data.attributes['wing'].data], bool)
wing_normals = {}
for side, sg in [('L', 1), ('R', -1)]:
    cloud = rest[wing & (rest[:, 0] * sg > .20)]
    normal = np.linalg.eigh(np.cov(cloud.T))[1][:, 0]
    if normal[1] > 0: normal = -normal
    wing_normals[side] = Vector(normal)
REST_EL = {}
for side in 'LR':
    h = rig.data.bones[side + 'Wing0'].head_local; t = rig.data.bones[side + 'Wing3'].tail_local
    REST_EL[side] = math.atan2(t.z - h.z, abs(t.x - h.x))
core = (rest[:, 1] > -.27) & (rest[:, 1] < -.08) & (rest[:, 2] > .13) & (rest[:, 2] < .26) & (~wing)

def ss(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def rot(n, axis, a):
    pb = rig.pose.bones[n]; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(axes[n] @ Vector(axis), a)
def surface():
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); em = ev.to_mesh(); a = np.empty(len(em.vertices) * 3)
    em.vertices.foreach_get('co', a); ev.to_mesh_clear(); return a.reshape(-1, 3)

FLIGHT = .9375
def pose(name, t, duration, lift=0.):
    if name == 'Dead': t = 1.25
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    period = duration if name in ('Standing', 'Walking', 'Running') else FLIGHT
    if name == 'Fidget': period = duration / 2
    phase = 2 * math.pi * t / period
    travel = .06 if name == 'Walking' else .12 if name == 'Running' else 0.
    pitch = -.06 - .05 * math.cos(phase) + travel; bank = .015 * math.sin(phase); yaw = 0.
    shift = Vector((0, 0, .006 * math.sin(phase - .6) + lift))
    elevation = math.radians(14 + 40 * math.cos(phase)); jaw = .04; neck = -pitch * .8; head_yaw = 0.; head_pitch = 0.
    fall = 0.; fold = 0.; recoil = 0.; sweep = 0.
    if name == 'Fidget':
        head_yaw = .32 * math.sin(math.pi * t / duration) ** 2 * math.sin(2 * math.pi * t / duration)
        bank += .03 * math.sin(2 * math.pi * t / duration); jaw += .12 * ss((t - .9) / .2) * (1 - ss((t - 1.3) / .2))
    if name in ('Attack', 'Cast'):
        # native m182aa-af: wings rise, then sweep down and forward while the neck lunges with open jaws
        wind = ss(t / .30) * (1 - ss((t - .36) / .12)); strike = ss((t - .36) / .14) * (1 - ss((t - .62) / .22))
        pitch += -.10 * wind + .12 * strike; neck += -.30 * wind + .48 * strike; head_pitch = -.15 * wind + .10 * strike
        shift.y += .02 * wind - .035 * strike; jaw = .04 + .08 * wind + .40 * strike
        elevation = math.radians(14 + 40 * math.cos(phase)) * (1 - wind - strike) + math.radians(52) * wind - math.radians(24) * strike
        sweep = .35 * strike
    if name == 'Hit':
        hit = ss(t / .10) * (1 - ss((t - .18) / .6)); pitch -= .22 * hit; neck -= .32 * hit; bank += .12 * hit
        head_yaw = -.25 * hit; shift.y += .03 * hit; jaw += .3 * hit
        elevation = elevation * (1 - hit) + math.radians(50) * hit
    death = name in ('Death', 'Dead')
    if death:
        # native m182na-nc recoil, da twisted roll in the air, db-dc fall, xa flat on the belly, wings on the ground
        recoil = ss(t / .22) * (1 - ss((t - .40) / .35)); fall = ss((t - .30) / .75); fold = ss((t - .30) / .65)
        twist = .85 * math.sin(math.pi * min(1., max(0., (t - .18) / .75)))
        pitch = (1 - fall) * (-.06 - .25 * recoil) + .22 * fall
        bank = twist; yaw = .12 * fall; neck = -.35 * recoil + .95 * fall   # neck laid forward on the ground
        jaw = .04 + .4 * recoil + .15 * fall; shift = Vector((.015 * fall, .01 * recoil, lift * (1 - fall)))
        elevation = (1 - fold) * math.radians(14 + 40 * math.cos(phase)) + fold * math.radians(-6)
    rot('Root', (1, 0, 0), pitch); rot('Root', (0, 1, 0), bank); rot('Root', (0, 0, 1), yaw)
    rig.pose.bones['Root'].location = axes['Root'] @ shift
    for i in range(1, 4):
        rot(f'Neck{i}', (1, 0, 0), neck / 3); rot(f'Neck{i}', (0, 0, 1), head_yaw / 3 - (.3 if i == 1 else 0) * fall)
    rot('Head', (1, 0, 0), -.015 * math.sin(phase) * (1 - fall) + head_pitch - .2 * recoil); rot('Jaw', (1, 0, 0), jaw)
    for i in range(1, 11):
        counter = -pitch * ({1: .5, 2: .3, 3: .2}.get(i, 0)) * (1 - fall)
        rot(f'Tail{i}', (0, 0, 1), (.014 + .002 * i) * math.sin(phase - i * .45) * (1 - fall) + .03 * fall)
        rot(f'Tail{i}', (1, 0, 0), counter + .012 * math.sin(phase - i * .35) * (1 - fall) + .02 * fall)
    for side, sg in [('L', 1), ('R', -1)]:
        rot(side + 'Wing0', (1, 0, 0), -pitch * (1 - fall) - sweep)
        rot(side + 'Wing0', (0, 0, 1), sg * .25 * fold)   # corpse wings stay spread, slightly swept back
        rot(side + 'Wing0', (0, 1, 0), sg * (REST_EL[side] - elevation))
        rot(side + 'Wing1', (0, 1, 0), sg * .08 * math.sin(phase - .35) * (1 - fold))
        rot(side + 'Wing2', (0, 1, 0), sg * .12 * math.sin(phase - .65) * (1 - fold))
        rot(side + 'Wing3', (0, 1, 0), sg * .08 * math.sin(phase - .9) * (1 - fold))
        rot(side + 'Wing2', (0, 0, 1), sg * (.12 * (1 + math.sin(phase)) * (1 - fold) + .12 * fold))
        # feather the outer hand on the upstroke (native edge-on recovery); the inner membrane near the body stays flat
        feather = (.10 + .55 * ss((math.cos(phase) + .2) / 1.2)) * (1 - fold)
        pb = rig.pose.bones[side + 'Wing2']; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((0, 1, 0), sg * .25 * feather)
        pb = rig.pose.bones[side + 'Wing3']; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((0, 1, 0), sg * .75 * feather)
        for limb in ['Fore', 'Hind']:
            if limb == 'Fore':
                upper = -.10 - .08 * math.cos(phase - .5) - pitch * .5 - .25 * (recoil if death else 0)
                upper = upper * (1 - fold) - .25 * fold
                rot(side + 'ForeUpper', (0, 0, 1), sg * -.3 * fold)
            else:
                upper = .32 - pitch * .6 + .03 * math.sin(phase - .7)   # hind legs tucked back in flight
                upper = upper * (1 - fold) + .55 * fold
                rot(side + 'HindUpper', (0, 0, 1), sg * .45 * fold)
            rot(side + limb + 'Upper', (1, 0, 0), upper)
            rot(side + limb + 'Lower', (1, 0, 0), (.05 + .03 * math.sin(phase - 1)) * (1 - fold) - .2 * fold)
            rot(side + limb + 'Foot', (1, 0, 0), -.04 * (1 - fall) + .15 * fall)
    bpy.context.view_layer.update()
    if death:
        settle_floor(fall)

HEADMASK = np.array([v.value for v in o.data.attributes['head'].data], bool)
TAILMASK = (rest[:, 1] > .02) & ~wing

def turn(pb, axis, angle):
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Quaternion(axis, angle).to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()

def solve(pb, axis, mask, target, lo, hi):
    """Turn pb about axis (through its head) so the masked vertices' lowest point sits at target; returns the angle.
    The lowest point must rise monotonically from lo to hi."""
    base = pb.matrix.copy()
    def height(angle):
        pb.matrix = base; bpy.context.view_layer.update(); turn(pb, axis, angle); return float(surface()[mask, 2].min())
    if height(lo) > target: return lo
    if height(hi) < target: return hi
    for _ in range(14):
        mid = (lo + hi) / 2
        if height(mid) < target: lo = mid
        else: hi = mid
    pb.matrix = base; bpy.context.view_layer.update(); return hi

def settle_floor(fall):
    """Belly on the floor, then wings, head and tail lowered onto it (or lifted out of it) as the fall completes."""
    if fall <= 0: return
    low = float(surface()[~wing & ~TAILMASK & ~HEADMASK, 2].min())
    rig.pose.bones['Root'].location += axes['Root'] @ Vector((0, 0, (.003 - low) * fall)); bpy.context.view_layer.update()
    for side, sg in [('L', 1), ('R', -1)]:
        pb = rig.pose.bones[side + 'Wing0']; mask = wing & (rest[:, 0] * sg > .09)
        axis = Vector((0, -sg, 0))                       # positive angle raises this wing
        now = float(surface()[mask, 2].min()); goal = solve(pb, axis, mask, .004, -1.4, 1.4)
        base = pb.matrix.copy(); turn(pb, axis, goal if now < .004 else goal * fall)
    pb = rig.pose.bones['Neck1']; now = float(surface()[HEADMASK, 2].min())
    goal = solve(pb, Vector((-1, 0, 0)), HEADMASK, .008, -.9, .9)    # positive angle lifts the head
    turn(pb, Vector((-1, 0, 0)), goal if now < .008 else goal * fall)
    pb = rig.pose.bones['Tail1']; now = float(surface()[TAILMASK, 2].min())
    goal = solve(pb, Vector((1, 0, 0)), TAILMASK, .006, -1.0, 1.0)   # +X turn lifts the tail behind the hips
    turn(pb, Vector((1, 0, 0)), goal if now < .006 else goal * fall)
    # each further tail segment aims its end at its own radius above the floor (no arch, no dip)
    for i in range(2, 11):
        seg = rig.pose.bones[f'Tail{i}']; h = seg.head.copy(); d = seg.tail - h
        radius = .016 - .001 * i; dz = radius - h.z
        if abs(dz) >= d.length: continue
        flat = Vector((d.x, d.y, 0)).normalized() * math.sqrt(d.length_squared - dz * dz); goal_dir = Vector((flat.x, flat.y, dz))
        q = Quaternion((1, 0, 0, 0)).slerp(d.rotation_difference(goal_dir), fall)
        seg.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ seg.matrix
        bpy.context.view_layer.update()
    low = float(surface()[:, 2].min())
    if low < .0005:
        rig.pose.bones['Root'].location += axes['Root'] @ Vector((0, 0, .0005 - low)); bpy.context.view_layer.update()

clips = {'Standing': 22, 'Walking': 22, 'Running': 18, 'Fidget': 44, 'Attack': 21, 'Cast': 21, 'Hit': 21, 'Death': 30, 'Dead': 24}
family = {'Standing': 'flight', 'Walking': 'flight', 'Running': 'flight', 'Fidget': 'flight', 'Attack': 'act', 'Cast': 'act', 'Hit': 'act'}
# constant floor lift per family: the lowest vertex of every sampled frame stays at or above z = 0.002
lifts = {}
for name, frames in clips.items():
    if name not in family: continue
    low = 1.
    for f in np.arange(0, frames + .01, .5):
        pose(name, f / 24, frames / 24); low = min(low, float(surface()[:, 2].min()))
    lifts[family[name]] = max(lifts.get(family[name], 0.), .002 - low)
lifts['act'] = max(lifts['act'], lifts['flight']); lifts['flight'] = max(lifts['flight'], 0.)
report = {'lift': lifts}
for name, frames in clips.items():
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data_create(); rig.animation_data.action = act
    bounds = []; core_low = []
    lift = lifts.get(family.get(name, 'flight'), lifts['flight'])
    for f in range(frames + 1):
        pose(name, f / 24, frames / 24, lift)
        for pb in rig.pose.bones:
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
        a = surface(); assert np.isfinite(a).all(); bounds.append([a.min(0).tolist(), a.max(0).tolist()]); core_low.append(float(a[core, 2].min()))
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    report[name] = {'frames': frames, 'duration': frames / 24, 'impact': .5 if name in ('Attack', 'Cast') else None,
                    'min_z': min(b[0][2] for b in bounds), 'max_z': max(b[1][2] for b in bounds), 'bounds': bounds, 'core_floor': core_low}
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
(P / 'work/clips.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_cavity = True
sc.render.resolution_x = 900; sc.render.resolution_y = 750; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('AnimCam', bpy.data.cameras.new('AnimCam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
out = P / 'review/anim'; out.mkdir(parents=True, exist_ok=True)
shots = [(c, f, v) for c, fr in [('Standing', (0, 6, 11, 16)), ('Attack', (0, 7, 12, 16)), ('Hit', (3, 8)), ('Death', (6, 14, 22, 30))] for f in fr for v in ('front', 'side')]
for clip, frame, view in shots:
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(frame)
    target = Vector((0, -.05, .3)); d = Vector((0, -1, .08) if view == 'front' else (1, -.25, .12)).normalized()
    cam.location = target + d * 3; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = 1.45
    sc.render.filepath = str(out / f'{clip}_{frame:02d}_{view}.png'); bpy.ops.render.render(write_still=True)
print('CLIPS', {k: (v['min_z'], v['max_z']) for k, v in report.items() if k != 'lift'}, 'LIFT', lifts)
