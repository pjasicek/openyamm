"""v2 clips from the native-fitted pose tables (Blender, 24 fps, in place).

work/v2/clip_tables.json (scripts/clip_tables.py) gives every frame's pose parameters; `dragon_pose.ops` turns them
into bone rotations exactly as the fitter's numpy skinning does. The native body bob is added to the Root height.
Floor rule: one constant lift for the flight loops so no vertex of any sampled frame goes below z = 2 mm; the
actions keep that height, lift a hanging tail by a smoothed extra tail pitch and take a smoothed extra lift where
needed; a half-frame pass raises the Root at both keys around any remaining dip. Death follows the native keys to
the fitted side-lying corpse and is lowered onto the floor during the fall (from the native frame da on). Dead holds
the last Death frame.
Usage: animate_v2.py -- <rig.blend> <out.blend>. Writes work/v2/clips.json."""
import bpy, json, math, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts'))
import dragon_pose as DP
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; o = bpy.data.objects['Body']; sc = bpy.context.scene; sc.render.fps = 24
for act in list(bpy.data.actions): bpy.data.actions.remove(act)
axes = {n: b.matrix_local.to_3x3().inverted() for n, b in rig.data.bones.items()}
rest = np.array([v.co[:] for v in o.data.vertices])
wing = np.array([v.value for v in o.data.attributes['wing'].data], bool)
head_m = np.array([v.value for v in o.data.attributes['head'].data], bool)
T = json.loads((P / 'work/v2/clip_tables.json').read_text())['clips']
TAILMASK = (rest[:, 1] > .02) & ~wing


def surface():
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); em = ev.to_mesh(); arr = np.empty(len(em.vertices) * 3)
    em.vertices.foreach_get('co', arr); ev.to_mesh_clear(); return arr.reshape(-1, 3)


def apply(p, lift):
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    ops, shift = DP.ops(p)
    for n, axis, ang in ops:
        if ang == 0 or n not in rig.pose.bones: continue
        pb = rig.pose.bones[n]; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(axes[n] @ Vector(axis), ang)
    shift = Vector(shift) + Vector((0, 0, p.get('bob', 0.) + lift))
    rig.pose.bones['Root'].location = axes['Root'] @ shift
    bpy.context.view_layer.update()


def turn(pb, axis, angle):
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Quaternion(axis, angle).to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()


def solve(pb, axis, mask, target, lo, hi):
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
    """The fitted corpse (scripts/fit_native.py refit_corpse) already lies consistently on its trunk, so the fall only
    brings the lowest vertex down to the floor (blended in with the fall)."""
    if fall <= 0: return
    low = float(surface()[:, 2].min())
    rig.pose.bones['Root'].location += axes['Root'] @ Vector((0, 0, (.003 - low) * fall)); bpy.context.view_layer.update()


def tail_floor():
    """Aim each tail segment whose end dips under its own radius above the floor back up to it (v1 floor rule for
    tails; lifting the whole body for a hanging tail would float the actions)."""
    for i in range(1, 11):
        seg = rig.pose.bones[f"Tail{i}"]; h = seg.head.copy(); d = seg.tail - h; radius = .045 - .0012 * i   # margin for the half frames
        if seg.tail.z >= radius: continue
        dz = radius - h.z
        if abs(dz) >= d.length: continue
        horiz = Vector((d.x, d.y, 0))
        if horiz.length < 1e-6: horiz = Vector((0, 1, 0))
        flat = horiz.normalized() * math.sqrt(d.length_squared - dz * dz); goal_dir = Vector((flat.x, flat.y, dz))
        q = d.rotation_difference(goal_dir)
        seg.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ seg.matrix; bpy.context.view_layer.update()


def fall_of(name, f):
    if name == 'Dead': return 1.
    if name != 'Death': return 0.
    t = f / 24; x = min(1., max(0., (t - .5) / (.9375 - .5))); return x * x * (3 - 2 * x)


family = {'Standing': 'flight', 'Walking': 'flight', 'Running': 'flight', 'Fidget': 'flight', 'Attack': 'act', 'Cast': 'act', 'Hit': 'act'}
lifts = {}
for name, frames in T.items():
    if family.get(name) != 'flight': continue
    low = 1.
    for f, p in enumerate(frames):
        apply(p, 0.); low = min(low, float(surface()[:, 2].min()))
    lifts['flight'] = max(lifts.get('flight', 0.), .002 - low)
# actions keep the flight height (the native frames float at the same height); a hanging tail is lifted by an extra
# tail pitch (solved per frame, then smoothed over the clip so the half frames stay above the floor too), and any
# remaining dip is a smooth extra lift per frame
def tail_need(p, lift):
    def low(dl):
        q = dict(p); q['tail_pitch1'] = q.get('tail_pitch1', 0.) + dl; q['tail_pitch2'] = q.get('tail_pitch2', 0.) + dl * .6
        apply(q, lift); return float(surface()[TAILMASK, 2].min())
    if low(0.) >= .006: return 0.
    lo, hi = 0., .5
    if low(hi) < .006: return hi
    for _ in range(12):
        mid = (lo + hi) / 2
        if low(mid) < .006: lo = mid
        else: hi = mid
    return hi
def smooth(v, w=2):
    v = np.array(v); m = np.maximum.reduce([np.roll(np.pad(v, w, mode='edge'), k)[w:-w] for k in range(-w, w + 1)])
    kern = np.ones(2 * w + 1) / (2 * w + 1); return np.maximum(np.convolve(np.pad(m, w, mode='edge'), kern, mode='valid'), v)
extra = {}
for name in ('Attack', 'Hit', 'Death'):
    tl = [tail_need(p, lifts['flight']) if fall_of(name, f) == 0 else 0. for f, p in enumerate(T[name])]
    tl = smooth(tl)
    for f, p in enumerate(T[name]):
        if fall_of(name, f) < 1:
            k = 1 - fall_of(name, f); p['tail_pitch1'] = p.get('tail_pitch1', 0.) + tl[f] * k; p['tail_pitch2'] = p.get('tail_pitch2', 0.) + tl[f] * .6 * k
    need = []
    for f, p in enumerate(T[name]):
        if fall_of(name, f) > 0: need.append(0.); continue
        apply(p, lifts['flight']); need.append(max(0., .004 - float(surface()[:, 2].min())))
    extra[name] = smooth(need).tolist()
extra['Cast'] = extra['Attack']; T['Cast'] = T['Attack']; T['Dead'] = [dict(T['Death'][-1]) for _ in T['Dead']]
lifts['act'] = lifts['flight']
report = {'lift': lifts, 'extra_lift_max': {k: max(v) for k, v in extra.items()}}
order = ['Standing', 'Walking', 'Running', 'Fidget', 'Attack', 'Cast', 'Hit', 'Death', 'Dead']
for name in order:
    frames = T[name]; act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data_create(); rig.animation_data.action = act
    lift = lifts.get(family.get(name, 'flight'), lifts['flight']); bounds = []; prevq = {}
    for f, p in enumerate(frames):
        fall = fall_of(name, f)
        apply(p, (lift + (extra[name][f] if name in extra else 0.)) * (1 - fall))
        if fall > 0: settle_floor(fall)
        low = float(surface()[:, 2].min())
        if low < .002:                                  # residual dip (tail flesh below its aimed end)
            rig.pose.bones['Root'].location += axes['Root'] @ Vector((0, 0, .002 - low)); bpy.context.view_layer.update()
        for pb in rig.pose.bones:
            q = pb.rotation_quaternion                      # keep each bone's quaternion on one hemisphere so the
            if pb.name in prevq and q.dot(prevq[pb.name]) < 0: pb.rotation_quaternion = -q   # linear keys do not flip
            prevq[pb.name] = pb.rotation_quaternion.copy()
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
        s = surface(); assert np.isfinite(s).all(); bounds.append([s.min(0).tolist(), s.max(0).tolist()])
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    # half-frame floor pass: a dip between two keys (fast turns) raises the Root at both keys by the deficit
    last = len(frames) - 1; loop = name in ('Standing', 'Walking', 'Running', 'Fidget')
    for _ in range(6):
        raised = False
        for f in range(last):
            sc.frame_set(f, subframe=.5); low = float(surface()[:, 2].min())
            if low >= .0015: continue
            for k in {f, f + 1} | ({0, last} if loop and (f == 0 or f + 1 == last) else set()):
                sc.frame_set(k); pb = rig.pose.bones['Root']; pb.location += axes['Root'] @ Vector((0, 0, .002 - low))
                pb.keyframe_insert('location', frame=k)
            raised = True
        if not raised: break
    if name == 'Death': death_end_root = None
    report[name] = {'frames': len(frames) - 1, 'duration': (len(frames) - 1) / 24, 'impact': .5 if name in ('Attack', 'Cast') else None,
                    'min_z': min(b[0][2] for b in bounds), 'max_z': max(b[1][2] for b in bounds)}
    print('CLIP', name, report[name]['frames'], round(report[name]['min_z'], 4), round(report[name]['max_z'], 4), flush=True)
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
(P / 'work/v2/clips.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=a[1]); print('ANIMATED', lifts)
