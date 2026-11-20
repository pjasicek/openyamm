"""Author a clip set on the Nobles' rig (work/rig.blend -> work/clips_<set>.blend), clips_lib.author per clip:
library trunk and arms (anim_library/humanoid_set, chosen in G1: review/g1/) over the flying demon's native wings, legs
and pelvis (the Overseer clips), eased from and back to the set's carry pose; fist poses from work/grips.json; the
left fist put on a two-handed weapon's second grip by IK (clips_lib.support_grip, scripts/weapons.json `support`).
Sets (clip prefix = the set name capitalised):
- noble (10040-10042, the fang): Flight (ArmedIdle carry over the native flight), AttackMelee (SwordAttackR1, the
  fang's cross-body cut), AttackRanged (ArmedCastLAttackHand2, a left-palm bolt), Cast (ArmedCastLAOE1, the left hand
  raised), Hit (ArmedGetHitF1 over the native hit), Death / Dead (native burn-away poses, the carry arms).
- ssekh (10113, twin fangs): as noble with both fists closed; AttackMelee ArmedAttackDual1, AttackRanged
  ArmedCastRAttack1 (a fang flick, released at the right fang's tip), Cast ArmedCastLAOE1, Dive (script clip `dive`,
  ArmedAttackDual2 in 0.8 s).
- mraal (10114, grounded, the phase cleaver two-handed): the 2Hand Axe set full body (pelvis path scaled to our legs,
  the lowest toe kept on the floor), the wings at rest with a third of the flight's motion: Standing (2HandAxeIdle),
  Walking (2HandAxeWalk), Running (2HandAxeRunForward), AttackMelee (2HandAxeAttack2), AttackRanged (2HandAxeAttack3,
  the sweep that throws the wave), Cast (2HandAxeActivate), Cleave (script clip `cleave`, 2HandAxeAttack1 in 1.2 s),
  Hit (2HandAxeGetHitF1), Death (2HandAxeDeath1), Dead (its last frame).
- xith (10115, the storm caster) / gate (10112, the Lancer carbine): 2Hand Shooting arms over the flight: Flight
  (2HandShootingIdle), AttackRanged (2HandShootingFireRifle1), AttackMelee (2HandShootingAttack1, a bash), Cast
  (2HandShootingFireRifle2, a charged shot), Hit (2HandShootingGetHitF1), Death / Dead; Xith's ChargedShot (script clip
  `charged_shot`, FireRifle2 slowed to 1 s).
Args: -- <set>"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Quaternion, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]
SET = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rig.blend'))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
GR = json.loads((P / 'work' / 'grips.json').read_text())
MOUNTS = json.loads((P / 'scripts' / 'weapons.json').read_text())
A = bpy.data.actions
UP = cl.TRUNK[1:]
ARMS = cl.CLAV + cl.ARM['L'] + cl.ARM['R']
WINGS = [b.name for b in rig.data.bones if b.name.startswith('B_Wing_')]
REST = Quaternion()
PFX = SET.capitalize()
misses = []


BODY = bpy.data.objects['Body']
_gi = {g.index: g.name for g in BODY.vertex_groups}
_dom = [_gi[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in BODY.data.vertices]
TORSO_FACES = [tuple(p.vertices) for p in BODY.data.polygons      # the clearance body: no wing membranes (double-sided:
               if not any(_dom[i].startswith('B_Wing_') for i in p.vertices)]   # their normals flip the inside test)


def body_tree():
    dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh()
    co = [tuple(BODY.matrix_world @ v.co) for v in m.vertices]; e.to_mesh_clear()
    return BVHTree.FromPolygons(co, TORSO_FACES)


CLEAR_SKIP = ('B_Wing_', 'B_L_UpperArm', 'B_L_Fore', 'B_L_Hand', 'B_L_Finger', 'B_R_Fore', 'B_R_Hand', 'B_R_Finger')
CLEAR_FACES = [tuple(p.vertices) for p in BODY.data.polygons    # what a held gun must clear: the torso, legs, head and
               if not any(_dom[i].startswith(CLEAR_SKIP) for i in p.vertices)]   # right upper arm (not the arms holding it)
LIFT_MARGIN = 0.035     # the carapace stands 2.6 cm off the skin (make_carapace: off 1.8 cm + 0.8 cm thick), plus air
LIFT_MAX = 0.15
LIFT_STEP = 0.005      # m per 48 Hz frame (0.24 m/s): the lift never jerks the arms


def lift_need(mount, pts, sup_pt):
    """the push (armature space) that brings the gun's deepest point LIFT_MARGIN out of the skin, along that point's
    surface normal; points within 7 cm of the gun hand or of the support grip are the grips"""
    from mathutils import Vector
    dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh()
    tree = BVHTree.FromPolygons([tuple(BODY.matrix_world @ v.co) for v in m.vertices], CLEAR_FACES); e.to_mesh_clear()
    G = rig.pose.bones['Grip_R'].matrix @ mount
    hands = [rig.pose.bones['B_R_Hand'].head, G @ Vector(sup_pt)]
    worst = None
    for p in pts:
        q = G @ Vector(p)
        if min((q - h).length for h in hands) < 0.07:
            continue
        loc, n, i, d = tree.find_nearest(q, 0.15)
        if loc is not None and (q - loc).dot(n) < LIFT_MARGIN:
            k = LIFT_MARGIN - (q - loc).dot(n)
            if worst is None or k > worst[0]: worst = (k, n)
    return worst[1] * worst[0] if worst else Vector()


def lift_arm(off):
    """move the gun hand (and the rigidly held gun) by `off`, the hand's world rotation kept (two-bone IK)"""
    hd = rig.pose.bones['B_R_Hand']; q = hd.matrix.to_quaternion()
    cl.two_bone_ik(rig, 'R', hd.head + off, q)


def smooth_lift(raw, r=6):
    """per-frame lifts (chest frame): dilated (the largest in +-r frames) then averaged over +-r: lifts ahead, no jitter"""
    from mathutils import Vector
    ks = sorted(raw); dil = {k: max((raw[j] for j in ks if abs(j - k) <= r), key=lambda v: v.length) for k in ks}
    return {k: sum((dil[j] for j in ks if abs(j - k) <= r), Vector()) / len([j for j in ks if abs(j - k) <= r]) for k in ks}


def weapon_points(name, count=160):
    """a subsample of the weapon's vertices (weapon coords) for the clearance test"""
    with bpy.data.libraries.load(str(P / 'work' / 'weapons' / f"{MOUNTS[name].get('mesh', name)}.blend"), link=False) as (src, dst):
        dst.meshes = [n for n in src.meshes if n.startswith('W_')]
    me = dst.meshes[0]; step = max(1, len(me.vertices) // count)
    return [tuple(v.co) for v in list(me.vertices)[::step]]


def post_fn(right, left, support=None, wings_rest=0.0, floor=None, weapon_floor=0.06, clear=False, body_floor=False,
            lift=False):
    """fists (0 rest .. 1 the fist), the support grip of a two-handed weapon, wings eased toward rest, a floor pass
    (grounded sets: the lowest toe ball kept at its rest height)"""
    mount = cl.mount_matrix(MOUNTS[support]) if support else None
    sup = MOUNTS[support]['support'] if support else None
    pts = weapon_points(support) if (support and clear) else None
    gun_pts = weapon_points(support, 60) if support else None
    from mathutils.bvhtree import BVHTree
    def post(t):
        for side, k in (('R', right), ('L', left)):
            for n, q in GR[side].items():
                pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = REST.slerp(Quaternion(q), k)
        if wings_rest:
            for n in WINGS:
                pb = rig.pose.bones[n]; loc, q, sc = pb.matrix_basis.decompose()
                pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q.slerp(REST, wings_rest)
        bpy.context.view_layer.update()
        if floor is not None and floor(t):
            low = min(rig.pose.bones[f'B_{s}_Toe0'].head.z for s in 'LR')
            ref = rig.data.bones['B_L_Toe0'].head_local.z
            pb = rig.pose.bones['B_Pelvis']; M = pb.matrix.copy(); M.translation.z -= low - ref; pb.matrix = M
            bpy.context.view_layer.update()
        if body_floor:                                          # a fall: the posed mesh's lowest point on the floor
            dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh()
            low = min((BODY.matrix_world @ v.co).z for v in m.vertices); e.to_mesh_clear()
            if low < 0.005:
                pb = rig.pose.bones['B_Pelvis']; M = pb.matrix.copy(); M.translation.z += 0.005 - low; pb.matrix = M
                bpy.context.view_layer.update()
        if pts:                                                 # the long prop out of the body
            tree = body_tree()
            post.depth = max(getattr(post, 'depth', 0.0), cl.swing_clear(rig, mount, pts, tree))
        if support and MOUNTS[support].get('ends'):            # both weapon ends above the floor: swing the right arm
            from mathutils import Vector
            for _ in range(3):
                W = rig.pose.bones['Grip_R'].matrix @ mount
                low = min((W @ Vector(e) for e in MOUNTS[support]['ends']), key=lambda v: v.z)
                if low.z >= weapon_floor: break
                ua = rig.pose.bones['B_R_UpperArm']; S = ua.head; v = low - S
                hz = math.sqrt(max(v.length ** 2 - (weapon_floor - S.z) ** 2, 1e-6)); h = v.copy(); h.z = 0
                v2 = h.normalized() * hz; v2.z = weapon_floor - S.z
                q = v.rotation_difference(v2)
                M = Matrix.Translation(S) @ q.to_matrix().to_4x4() @ Matrix.Translation(-S)
                ua.matrix = M @ ua.matrix; bpy.context.view_layer.update()
        if lift:                                                # the held gun off the carapace (lift_need)
            from mathutils import Vector
            ch = rig.pose.bones['B_Spine2'].matrix.to_quaternion(); fr = round(t * cl.FPS)
            if 'lift_s' in post.state:                          # the real pass: the dry pass's lifts, smoothed and
                want = post.state['lift_s'].get(fr, Vector())   # changed by at most LIFT_STEP a frame
                prev = post.state.get('lift_prev', want); d = want - prev
                cur = prev + d * min(1.0, LIFT_STEP / d.length) if d.length > 1e-9 else want
                post.state['lift_prev'] = cur
                lift_arm(ch @ cur)
            else:                                               # the dry pass: solve and record
                tot = Vector()
                for _ in range(4):
                    d = lift_need(mount, gun_pts, sup['point'])
                    if d.length < 0.003 or (tot + d).length > LIFT_MAX: break
                    lift_arm(d); tot += d
                post.state.setdefault('lift_raw', {})[fr] = ch.inverted() @ tot
        if support:
            src_q = rig.pose.bones['B_L_Hand'].matrix.to_quaternion()
            misses.append(cl.support_grip(rig, mount, sup['point'], sup['axis'], src_q, state=post.state, pts=gun_pts))
            if 'trial' not in post.state:                       # the support fist turns at most MAX_STEP a frame too
                hd = rig.pose.bones['B_L_Hand']; cur = hd.matrix.to_quaternion(); prev = post.state.get('hand_prev')
                if prev is not None:
                    if cur.dot(prev) < 0: cur.negate()
                    ang = prev.rotation_difference(cur).angle
                    if ang > cl.MAX_STEP:
                        cl.set_world_rot(rig, 'B_L_Hand', prev.slerp(cur, cl.MAX_STEP / ang))
                        bpy.context.view_layer.update()
                post.state['hand_prev'] = hd.matrix.to_quaternion()
            for n, q in GR['L'].items():
                pb = rig.pose.bones[n]; pb.rotation_quaternion = Quaternion(q)
            bpy.context.view_layer.update()
    post.state = {}; post.support = bool(support)
    return post


def carry(src, scale=1.0, trunk=False, pelvis=None):
    dur = srcs[src][0]
    L = [{'bones': ARMS, 'src': src, 't': lambda t: (t * scale) % dur, 'w': lambda t: 1.0, 'rel': 'B_Spine2'}]
    if trunk:
        bones = UP + (['B_Pelvis'] + cl.LEGS if pelvis else [])
        L.insert(0, {'bones': bones, 'src': src, 't': lambda t: (t * scale) % dur, 'w': lambda t: 1.0})
        if pelvis:
            L.insert(1, {'bones': [], 'src': src, 't': lambda t: (t * scale) % dur, 'w': lambda t: 1.0, 'pelvis_loc': pelvis})
    return L


def action(src, lead, speed, seconds, tail=0.35, legs=None, legs_w=1.0):
    """the source action from `lead` at `speed`, eased in over `lead` and out over `tail` before the end; legs: the
    grounded sets also take the source's pelvis, legs and pelvis path (scale)"""
    dur = srcs[src][0]
    w = cl.envelope(0.0, lead, seconds - tail, seconds)
    tm = lambda t: max(0.0, min((t - lead) * speed, dur))
    L = [{'bones': UP, 'src': src, 't': tm, 'w': w},
         {'bones': ARMS, 'src': src, 't': tm, 'w': w, 'rel': 'B_Spine2'}]
    if legs:
        wl = lambda t: legs_w * w(t)
        L.insert(1, {'bones': ['B_Pelvis'] + cl.LEGS, 'src': src, 't': tm, 'w': wl})
        L.append({'bones': [], 'src': src, 't': tm, 'w': wl, 'pelvis_loc': legs})
    return L


fl, hit, death, dead = A['Overseer_Flight'], A['Overseer_Hit'], A['Overseer_Death'], A['Overseer_Dead']
now = lambda t: t
if SET == 'noble':
    srcs = cl.load_sources(ROOT, {'Armed.glb': ['ArmedIdle', 'ArmedCastLAttackHand2', 'ArmedCastLAOE1', 'ArmedGetHitF1'],
                                  '1Hand.glb': ['SwordAttackR1']}, scene)
    c = carry('ArmedIdle', 2.0 / 3.0); post = post_fn(1.0, 0.3)
    clips = [('Flight', fl, 3.0, None, c),
             ('AttackMelee', fl, 1.70, None, c + action('SwordAttackR1', 0.30, 0.75, 1.70, 0.40)),
             ('AttackRanged', fl, 1.40, None, c + action('ArmedCastLAttackHand2', 0.15, 1.0, 1.40, 0.30)),
             ('Cast', fl, 1.60, None, c + action('ArmedCastLAOE1', 0.15, 1.0, 1.60, 0.30)),
             ('Hit', hit, 0.75, now, c + action('ArmedGetHitF1', 0.05, 1.0, 0.75, 0.20)),
             ('Death', death, 1.25, now, c), ('Dead', dead, 1.0, now, c)]
elif SET == 'ssekh':
    srcs = cl.load_sources(ROOT, {'Armed.glb': ['ArmedIdle', 'ArmedAttackDual1', 'ArmedAttackDual2', 'ArmedCastRAttack1',
                                                'ArmedCastLAOE1', 'ArmedGetHitF1']}, scene)
    c = carry('ArmedIdle', 2.0 / 3.0); post = post_fn(1.0, 1.0)
    clips = [('Flight', fl, 3.0, None, c),
             ('AttackMelee', fl, 1.45, None, c + action('ArmedAttackDual1', 0.20, 0.9, 1.45, 0.30)),
             ('AttackRanged', fl, 1.30, None, c + action('ArmedCastRAttack1', 0.15, 1.0, 1.30, 0.30)),
             ('Cast', fl, 1.60, None, c + action('ArmedCastLAOE1', 0.15, 1.0, 1.60, 0.30)),
             ('Dive', fl, 0.80, None, c + action('ArmedAttackDual2', 0.08, 1.4, 0.80, 0.12)),
             ('Hit', hit, 0.75, now, c + action('ArmedGetHitF1', 0.05, 1.0, 0.75, 0.20)),
             ('Death', death, 1.25, now, c), ('Dead', dead, 1.0, now, c)]
elif SET == 'mraal':
    srcs = cl.load_sources(ROOT, {'2Hand Axe.glb': ['2HandAxeIdle', '2HandAxeWalk', '2HandAxeRunForward', '2HandAxeAttack1',
                                                    '2HandAxeAttack2', '2HandAxeAttack3', '2HandAxeActivate',
                                                    '2HandAxeGetHitF1', '2HandAxeDeath1']}, scene)
    k = rig.data.bones['B_Pelvis'].head_local.z / srcs['_rest_pelvis'].z
    always, alive = (lambda t: True), None
    post = post_fn(1.0, 1.0, support='phase_cleaver', wings_rest=0.66, floor=always)
    post_death = post_fn(1.0, 0.4, wings_rest=0.66, body_floor=True)   # the left hand lets go of the haft as he falls
    idle = carry('2HandAxeIdle', 1.0, trunk=True, pelvis=k)
    clips = [('Standing', fl, 2.0, None, idle),
             ('Walking', fl, 0.8, None, carry('2HandAxeWalk', 1.0, trunk=True, pelvis=k)),
             ('Running', fl, 0.8, None, carry('2HandAxeRunForward', 1.0, trunk=True, pelvis=k)),
             ('AttackMelee', fl, 1.80, None, idle + action('2HandAxeAttack2', 0.15, 1.0, 1.80, 0.25, legs=k, legs_w=0.6)),
             ('AttackRanged', fl, 1.80, None, idle + action('2HandAxeAttack3', 0.15, 1.0, 1.80, 0.25, legs=k, legs_w=0.5)),
             ('Cast', fl, 1.80, None, idle + action('2HandAxeActivate', 0.10, 1.0, 1.80, 0.20, legs=k)),
             ('Cleave', fl, 1.20, None, idle + action('2HandAxeAttack1', 0.06, 1.45, 1.20, 0.10, legs=k, legs_w=0.5)),
             ('Hit', fl, 0.75, None, idle + action('2HandAxeGetHitF1', 0.05, 1.0, 0.75, 0.20, legs=k))]
    dl = srcs['2HandAxeDeath1'][0]
    death_layers = idle + action('2HandAxeDeath1', 0.05, 1.0, dl + 0.05, 0.0001, legs=k)
    for L in death_layers[-4:]: L['w'] = cl.envelope(0, 0.05, 99, 100)
    clips += [('Death', fl, dl + 0.05, None, death_layers, post_death),
              ('Dead', fl, 1.0, None, [dict(L, t=(lambda t: dl), w=(lambda t: 1.0)) for L in death_layers], post_death)]
elif SET in ('xith', 'gate'):
    srcs = cl.load_sources(ROOT, {'2Hand Shooting.glb': ['2HandShootingIdle', '2HandShootingFireRifle1',
                                  '2HandShootingFireRifle2', '2HandShootingAttack1',
                                  '2HandShootingGetHitF1']}, scene)
    gun = 'storm_rifle' if SET == 'xith' else 'lancer_carbine'
    c = carry('2HandShootingIdle', 1.0, trunk=False); post = post_fn(1.0, 1.0, support=gun, lift=True)
    bash = post_fn(1.0, 1.0, support=gun)                     # the bash swings at the rate limit: no lift on top
    clips = [('Flight', fl, 3.0, None, c),
             ('AttackRanged', fl, 1.35, None, c + action('2HandShootingFireRifle1', 0.25, 1.0, 1.35, 0.30)),
             ('AttackMelee', fl, 1.40, None, c + action('2HandShootingAttack1', 0.15, 1.0, 1.40, 0.25), bash),
             ('Cast', fl, 1.40, None, c + action('2HandShootingFireRifle2', 0.20, 0.85, 1.40, 0.30)),   # a charged shot:
             #                         the spell leaves the muzzle (2HandShootingActivate spun the support hand 168 deg)
             ('Hit', hit, 0.75, now, c + action('2HandShootingGetHitF1', 0.05, 1.0, 0.75, 0.20)),
             ('Death', death, 1.25, now, c), ('Dead', dead, 1.0, now, c)]
    if SET == 'xith':
        clips.append(('ChargedShot', fl, 1.0, None, c + action('2HandShootingFireRifle2', 0.10, 0.8, 1.0, 0.15)))
else:
    raise SystemExit('unknown set ' + SET)
report = {}
for spec in clips:
    name, base, seconds, bt, layers = spec[:5]
    p = spec[5] if len(spec) > 5 else post
    choice = None
    if p.support:                                               # dry pass: score the 24 rigid support grips
        misses.clear(); p.state.clear(); p.state['trial'] = None; p.depth = 0.0
        trial = cl.author(rig, scene, srcs, f'_trial_{PFX}_{name}', base, seconds, layers, base_time=bt, post=p)
        costs, cands = p.state['costs'], p.state['trial']; k = min(range(len(costs)), key=costs.__getitem__)
        choice = {'grip': k, 'cost': round(costs[k], 1), 'first_cost': round(costs[0], 1)}
        bpy.data.actions.remove(trial)
        raw = p.state.get('lift_raw')
        p.state.clear(); p.state['rel'] = cands[k]               # (w_prev cleared: the real pass starts fresh)
        if raw:
            p.state['lift_s'] = smooth_lift(raw)
            choice['lift_max_m'] = round(max(v.length for v in raw.values()), 4)
    else:
        p.state.clear()
    misses.clear(); p.depth = 0.0
    cl.author(rig, scene, srcs, f'{PFX}_{name}', base, seconds, layers, base_time=bt, post=p)
    report[f'{PFX}_{name}'] = {'seconds': round(seconds * cl.FPS) / cl.FPS, 'base': base.name,
                               'sources': sorted({L['src'] for L in layers}),
                               'support_miss_max_m': round(max(misses), 4) if misses else None,
                               'prop_depth_before_clear_m': round(p.depth, 4), 'support_grip': choice}
    print('CLIP', f'{PFX}_{name}', report[f'{PFX}_{name}']['support_miss_max_m'], flush=True)
for a in [a for a in bpy.data.actions if not a.name.startswith(PFX + '_')]:
    a.use_fake_user = False
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
scene.render.fps = cl.FPS
(P / 'work' / f'clips_{SET}.json').write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / f'clips_{SET}.blend'))
print('CLIPS_DONE', SET); sys.stdout.flush(); os._exit(0)
