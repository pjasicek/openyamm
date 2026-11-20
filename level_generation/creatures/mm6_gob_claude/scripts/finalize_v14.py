"""Goblin revision 14: final clip set on the Meshy auto-rig with fixed hands (no per-frame grip solving).

  - one fixed right fist around the sword (solved once at rest) and one relaxed left hand, used in every frame,
  - Meshy motion copied as world bone rotations (same joints as the rig), hips position included,
  - forearm twist beyond 90 deg clamped (the rest is spread by the twist bones), wrist swing limited to 70 deg,
  - arm/body contact: distal arm skin found inside the torso pushes the wrist outward until it clears,
  - Walking/Running torso lean pulled back to the Standing lean (Meshy's walk slumps),
  - Attack = Meshy 219 (frames 2-33, x1.5), Hit = Meshy 179 (x1.4), Death = Meshy 184 (frames 0-44, x1.5),
    Dead = Meshy 184 last frame held; Standing/Fidget/Cast_FireBolt are our clips re-posed with the fixed fist.
Run on work/final_v1.blend (Meshy rig); writes work/final_v14.blend.

Clip timing (2026-10-10, engine action events): with GOB_ONLY=Attack,Death only those clips are rebuilt, in place
in work/final_v1.blend (the later head split stays). Attack = LEAD s ready pause (ease from Standing into the slash's
first pose) + the slash at source speed; Death at source speed (the engine plays a long death to its end). Prints the
blow (peak Sword tip speed) for actors.yml `events: attack_melee: {impact}`.
"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']; me = mesh.data
scene = bpy.context.scene
import author_clips as A
import posing as P

MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b
BODY = ['mixamorig:' + v for v in MAP.values()]
ORDER = [b.name for b in rig.data.bones if b.name in BODY]
inv = rig.matrix_world.inverted()
RQ = rig.matrix_world.to_quaternion().inverted()


def fingers(side):
    return [b for b in rig.pose.bones if b.name.startswith(f'mixamorig:{side}Hand') and b.name != f'mixamorig:{side}Hand']


# ---------------------------------------------------------------- fixed hand poses
rig.animation_data.action = None
P.reset(rig)
P.curl_hand(rig, 'Right', 80, thumb=35)
A.wrap_grip('Right'); A.wrap_thumb('Right')
FIST = {b.name: b.rotation_quaternion.copy() for b in fingers('Right')}
P.reset(rig)
P.curl_hand(rig, 'Left', 25, thumb=10)
RELAX = {b.name: b.rotation_quaternion.copy() for b in fingers('Left')}
P.reset(rig)

# ---------------------------------------------------------------- contact data (from pose_audit)
PARTS = json.loads(scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
gnames = [g.name for g in mesh.vertex_groups]
dom = np.full(len(me.vertices), -1); best = np.zeros(len(me.vertices))
for v in me.vertices:
    for g in v.groups:
        if g.weight > best[v.index]:
            best[v.index] = g.weight; dom[v.index] = g.group
dn = np.array([gnames[d] if d >= 0 else '' for d in dom])
TORSO = np.array([any(k in n for k in ('Hips', 'Spine', 'Neck', 'Head', 'UpLeg', 'Shoulder')) for n in dn])
BODYP = part == PARTS.index('Body')
POLYS = [tuple(p.vertices) for p in me.polygons]
TPOLYS = [POLYS[i] for i in range(len(POLYS)) if BODYP[i] and all(TORSO[j] for j in POLYS[i])]
LIMB = {s: np.array([(s + 'ForeArm' in n) or (s + 'Hand' in n) for n in dn]) for s in ('Left', 'Right')}
UPPER = {s: dn == f'mixamorig:{s}Arm' for s in ('Left', 'Right')}
RAYS = [Vector(d).normalized() for d in ((1, 0.1, 0.05), (-1, 0.05, 0.1), (0.1, 1, 0.05), (0.05, -1, 0.1),
                                          (0.1, 0.05, 1), (0.05, 0.1, -1))]
dg = bpy.context.evaluated_depsgraph_get()


def inside(tree, v):
    odd = 0
    for d in RAYS:
        n, o = 0, v
        while n < 12:
            h = tree.ray_cast(o, d, 2.0)
            if h[0] is None:
                break
            n += 1; o = h[0] + d * 1e-4
        odd += n % 2
    return odd >= 4


def contact(side):
    ev = mesh.evaluated_get(dg); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ev.to_mesh_clear()
    tree = BVHTree.FromPolygons([Vector(c) for c in co], TPOLYS)
    sh = np.array(rig.matrix_world @ P.pb(rig, side + 'Arm').head)
    sel = LIMB[side] | (UPPER[side] & (np.linalg.norm(co - sh, axis=1) > 0.12))
    depth, count = 0.0, 0
    for i in np.nonzero(sel)[0]:
        v = Vector(co[i]); near = tree.find_nearest(v, 0.10)
        if near[0] is not None and inside(tree, v):
            depth = max(depth, near[3]); count += 1
    return depth, count


# ---------------------------------------------------------------- posing
def clamp_twist(side, limit=math.radians(90)):
    fa = P.pb(rig, side + 'ForeArm'); hand = P.pb(rig, side + 'Hand')
    rest_rel = fa.bone.matrix_local.to_quaternion().inverted() @ hand.bone.matrix_local.to_quaternion()
    fq = fa.matrix.to_quaternion()
    d = rest_rel.inverted() @ (fq.inverted() @ hand.matrix.to_quaternion())
    swing, tw = d.to_swing_twist('Y')
    if abs(tw) <= limit:
        return
    q = fq @ rest_rel @ swing @ Quaternion((0, 1, 0), math.copysign(limit, tw))
    hand.matrix = Matrix.LocRotScale(hand.head.copy(), q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def push_out(side, max_iter=5):
    """Swing the whole arm outward about the shoulder (forward axis) until the arm clears the torso."""
    total = 0.0
    for _ in range(max_iter):
        depth, count = contact(side)
        if depth < 0.012 or count < 3:
            break
        origin, x, y, z = A.shoulder_frame(side)
        hand0 = P.bone_world(rig, side + 'Hand')
        deg = min(12.0, 3.0 + math.degrees(depth / 0.45))
        P.rotate_world(rig, side + 'Arm', z, deg)
        if (P.bone_world(rig, side + 'Hand') - hand0).dot(x) < 0:
            P.rotate_world(rig, side + 'Arm', z, -2 * deg)
        total += deg
    return total


HEADV = np.array(['Head' in n or 'Neck' in n for n in dn])


def head_contact(side):
    ev = mesh.evaluated_get(dg); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ev.to_mesh_clear()
    hp = [POLYS[i] for i in range(len(POLYS)) if BODYP[i] and all(HEADV[j] for j in POLYS[i])]
    tree = BVHTree.FromPolygons([Vector(c) for c in co], hp)
    depth = 0.0
    for i in np.nonzero(LIMB[side] | UPPER[side])[0]:
        v = Vector(co[i]); near = tree.find_nearest(v, 0.08)
        if near[0] is not None and (v - near[0]).dot(near[1]) < 0:
            depth = max(depth, near[3])
    return depth


def dodge_head(side, max_iter=4):
    """A raised arm passing the head: tilt the head (and neck) away from that arm."""
    for _ in range(max_iter):
        if head_contact(side) < 0.01:
            return
        origin, x, y, z = A.shoulder_frame(side)
        for n, deg in (('Neck', 4.0), ('Head', 6.0)):
            P.rotate_world(rig, n, z, -deg if side == 'Right' else deg)   # away from that arm
        if head_contact(side) >= 0.01:
            pass


def lean(a, b):
    d = P.bone_world(rig, b) - P.bone_world(rig, a)
    return math.degrees(math.atan2(-d.y, d.z))


def straighten(target):
    for _ in range(3):
        excess = lean('Hips', 'Neck') - target
        lat = P.bone_world(rig, 'LeftUpLeg') - P.bone_world(rig, 'RightUpLeg'); lat.z = 0; lat.normalize()
        for n, share in (('Spine', 0.3), ('Spine1', 0.35), ('Spine2', 0.35)):
            P.rotate_world(rig, n, lat, -excess * share)


def head_pitch():
    d = (P.bone_world(rig, 'Head', tail=True) - P.bone_world(rig, 'Head')).normalized()
    return math.degrees(math.atan2(-d.y, d.z))


STAND = {}


def match_standing_upper(world):
    """Locomotion: clavicles as in Standing (no dropped shoulders), arms keep the source directions, head pitch
    back to the Standing pitch (straightening the torso tips the head up)."""
    for side in ('Left', 'Right'):
        rig.pose.bones[f'mixamorig:{side}Shoulder'].rotation_quaternion = STAND['clav_' + side]
    bpy.context.view_layer.update()
    for n in ('Arm', 'ForeArm', 'Hand'):
        for side in ('Left', 'Right'):
            b = f'mixamorig:{side}{n}'; pb = rig.pose.bones[b]
            pb.matrix = Matrix.LocRotScale(pb.head.copy(), RQ @ world[b].to_quaternion(), Vector((1, 1, 1)))
            bpy.context.view_layer.update()
    for _ in range(3):
        err = STAND['head_pitch'] - head_pitch()
        lat = P.bone_world(rig, 'LeftUpLeg') - P.bone_world(rig, 'RightUpLeg'); lat.z = 0; lat.normalize()
        P.rotate_world(rig, 'Neck', lat, err * 0.4); P.rotate_world(rig, 'Head', lat, err * 0.6)


def pose_frame(world, left_fingers=None, lean_target=None):
    """world: {our body bone: world matrix}. Fingers are fixed; returns the captured pose."""
    rig.animation_data.action = None
    P.reset(rig)
    for n in ORDER:
        if n not in world:
            continue
        pb = rig.pose.bones[n]; loc, rot, _ = world[n].decompose()
        head = inv @ loc if n == 'mixamorig:Hips' else pb.head.copy()
        pb.matrix = Matrix.LocRotScale(head, RQ @ rot, Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    if lean_target is not None:
        straighten(lean_target)
        match_standing_upper(world)
    for side in ('Left', 'Right'):
        A.limit_wrist(side); clamp_twist(side)
    for side in ('Left', 'Right'):
        push_out(side)
    for side in ('Left', 'Right'):
        dodge_head(side)
    for b in fingers('Right'):
        b.rotation_quaternion = FIST[b.name]
    for b in fingers('Left'):
        b.rotation_quaternion = (left_fingers or RELAX)[b.name]
    bpy.context.view_layer.update()
    return A.capture()


# ---------------------------------------------------------------- sources
def sample_meshy(glb, substring):
    before = set(bpy.data.objects); before_act = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    objs = [o for o in bpy.data.objects if o not in before]
    marm = next(o for o in objs if o.type == 'ARMATURE')
    acts = [a for a in bpy.data.actions if a not in before_act]
    src = next(a for a in acts if substring.lower() in a.name.lower())
    marm.animation_data.action = src
    f0, f1 = (int(round(x)) for x in src.frame_range)
    frames = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        frames.append({'mixamorig:' + v: (marm.matrix_world @ marm.pose.bones[k].matrix).copy() for k, v in MAP.items()})
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in acts:
        bpy.data.actions.remove(a)
    return frames


def sample_ours(action_name):
    act = bpy.data.actions[action_name]; rig.animation_data.action = act
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames, lefts = [], []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        frames.append({n: (rig.matrix_world @ rig.pose.bones[n].matrix).copy() for n in BODY})
        lefts.append({b.name: b.rotation_quaternion.copy() for b in fingers('Left')})
    rig.animation_data.action = None
    return frames, lefts


def resample(frames, first, last, speed, drift=True):
    """Frames first..last played `speed` times faster, as 24 fps samples (slerp/lerp between source frames)."""
    seg = frames[first:last + 1]
    n = max(2, int(round((len(seg) - 1) / speed)) + 1)
    out = []
    for k in range(n):
        t = k * (len(seg) - 1) / (n - 1); i = min(int(t), len(seg) - 2); u = t - i
        fr = {}
        for b in seg[i]:
            l0, r0, _ = seg[i][b].decompose(); l1, r1, _ = seg[i + 1][b].decompose()
            fr[b] = Matrix.LocRotScale(l0.lerp(l1, u), r0.slerp(r1, u), Vector((1, 1, 1)))
        out.append(fr)
    if drift:                                       # remove net horizontal hips travel over the clip
        h0 = out[0]['mixamorig:Hips'].translation.copy(); h1 = out[-1]['mixamorig:Hips'].translation.copy()
        for k, fr in enumerate(out):
            d = (h1 - h0) * (k / (len(out) - 1)); d.z = 0
            loc, rot, _ = fr['mixamorig:Hips'].decompose()
            fr['mixamorig:Hips'] = Matrix.LocRotScale(loc - d, rot, Vector((1, 1, 1)))
    return out


def build(name, frames, loop=False, lefts=None, lean_target=None):
    out = []
    for k, fr in enumerate(frames):
        out.append((k + 1, pose_frame(fr, lefts[k] if lefts else None, lean_target)))
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    A.write_action(name, out, loop=loop)
    print('BUILT', name, len(frames), 'frames', round((len(frames) - 1) / 24, 3), 's', flush=True)


ours = {n: sample_ours(n) for n in ('Standing', 'Fidget', 'Cast_FireBolt')}
scene.frame_set(1)
stand_frames = ours['Standing'][0]
pose_frame(stand_frames[0])
STAND_LEAN = lean('Hips', 'Neck')
STAND['head_pitch'] = head_pitch()
for side in ('Left', 'Right'):
    STAND['clav_' + side] = rig.pose.bones[f'mixamorig:{side}Shoulder'].rotation_quaternion.copy()
print('STAND LEAN', round(STAND_LEAN, 1))
lib = 'meshy/anim_lib_v1/result_animation_glb_url.glb'
slash = sample_meshy(lib, 'Right_Hand_Sword_Slash')
hit = sample_meshy(lib, 'Hit_Reaction_1')
death = sample_meshy(lib, 'Shot_and_Fall_Forward')
walk = sample_meshy('meshy/rig_v1/result_basic_animations_walking_glb_url.glb', 'walk')
run = sample_meshy('meshy/rig_v1/result_basic_animations_running_glb_url.glb', 'run')

ONLY = [n for n in os.environ.get('GOB_ONLY', '').split(',') if n]
LEAD = 0.3


def ease_into(a, b, n):
    """n frames easing from world pose a toward world pose b (b itself not included)."""
    out = []
    for k in range(n):
        u = k / n; u = u * u * (3 - 2 * u); fr = {}
        for bn in a:
            l0, r0, _ = a[bn].decompose(); l1, r1, _ = b[bn].decompose()
            fr[bn] = Matrix.LocRotScale(l0.lerp(l1, u), r0.slerp(r1, u), Vector((1, 1, 1)))
        out.append(fr)
    return out


if ONLY:
    slash_src = resample(slash, 2, 33, 1.0)
    clips = {'Attack': (ease_into(stand_frames[0], slash_src[0], int(round(LEAD * 24))) + slash_src, {}),
             'Death': (resample(death, 0, 44, 1.0, drift=False), {'loop': False})}
    for name in ONLY:
        frames, kw = clips[name]
        build(name, frames, **kw)
    if 'Attack' in ONLY:
        act = bpy.data.actions['Attack']; rig.animation_data.action = act
        tips = []
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            scene.frame_set(f); tips.append(np.array(rig.matrix_world @ rig.pose.bones['Sword'].tail))
        sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1); k = int(np.argmax(sp))
        impact = (k + 0.5) / 24
        print(f'ATTACK {(len(tips) - 1) / 24:.3f} s, blow at {impact:.3f} s -> wind-up stretch {0.75 / impact:.2f}x; '
              f'IMPACT {impact:.3f}', flush=True)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'final_v1.blend'))
    print('SAVED final_v1.blend', flush=True)
    raise SystemExit(0)

for name in [a.name for a in bpy.data.actions]:
    if name not in ('Standing', 'Fidget', 'Cast_FireBolt'):
        bpy.data.actions.remove(bpy.data.actions[name])
build('Standing', stand_frames, loop=True)
build('Fidget', ours['Fidget'][0])
build('Cast_FireBolt', ours['Cast_FireBolt'][0], lefts=ours['Cast_FireBolt'][1])
build('Walking', resample(walk, 0, len(walk) - 1, 1.0, drift=False), loop=True, lean_target=STAND_LEAN)
build('Running', resample(run, 0, len(run) - 1, 1.0, drift=False), loop=True, lean_target=STAND_LEAN + 4.5)
build('Attack', resample(slash, 2, 33, 1.5))
build('Hit', resample(hit, 0, len(hit) - 1, 1.4))
build('Death', resample(death, 0, 44, 1.5, drift=False))
build('Dead', [death[-1], death[-1]] + [death[-1]] * 23, loop=False)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'final_v14.blend'))
print('SAVED final_v14.blend')
