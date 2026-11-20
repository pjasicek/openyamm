"""MM8 m452 actions from native timing, using the MM6 Rat IK gait, bite and lagging tail methods.
The native m452 hit rears upward and its corpse settles belly-down with spread paws.
"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work/rig_uv.blend'))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']; sc = bpy.context.scene
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
WRIST = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
ANKLE = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


def place_leg(kind, side, target, pitch=0.0, free=None):
    """kind 'front'/'hind'; target = wrist/ankle world point; pitch tilts the paw (+ = toes down)."""
    if free is not None:                                      # FK: (upper deg, lower deg, splay deg)
        up, lo, splay = free
        u, l = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'front' else (f'Thigh_{side}', f'Shin_{side}')
        rot(u, Y, splay * SIDE[side]); rot(u, X, up); rot(l, X, lo)
        return
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.05, 0.25, 0.05))
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.04, -0.25, 0.10))
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    q = Quaternion(X, math.radians(pitch)) @ rest.to_quaternion()
    set_world_rot(paw, q)


def tail_wave(amp_yaw, amp_pitch, phase, lift=0.0, base_pitch=0.0):
    for i in range(1, 7):
        k = i / 6.0
        rot(f'Tail{i}', Z, amp_yaw * k * math.sin(2 * math.pi * (phase - 0.09 * i)))
        rot(f'Tail{i}', X, (lift if i == 1 else lift * 0.15) + amp_pitch * math.sin(2 * math.pi * (phase - 0.09 * i))
            + (base_pitch if i == 1 else 0))


def body(hips_d=Vector(), hips_pitch=0.0, hips_roll=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0,
         head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, hips_roll); rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)


# ---------------------------------------------------------------- floor rules
import numpy as np
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Jaw')) for n in _dom])
_dg = bpy.context.evaluated_depsgraph_get()
FLOOR = 0.004


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def clamp_tail():
    """Raise any tail segment whose end dips under the floor (bone by bone, base to tip)."""
    for i in range(1, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        if t.z < 0.012:
            h = rig.matrix_world @ b.head
            d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized()
            dz = 0.012 - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, b.name, target)


def floor_fit(lift_core=True):
    """Keep the body out of the floor: lift the whole rat if core (body/head/upper legs) sinks, then the tail."""
    if lift_core:
        co = mesh_co()
        low = co[CORE, 2].min()
        if low < -FLOOR:
            root = rig.pose.bones['Spine1']
            root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix; bpy.context.view_layer.update()
    clamp_tail()


# ---------------------------------------------------------------- clips
def gait(t, T, stride, duty, lift_f, lift_h, flex):
    p = (t / T) % 1.0
    P.reset(rig)
    body(hips_d=Vector((0, 0, -0.006 * math.cos(4 * math.pi * p) - 0.004)), spine_pitch=flex * math.sin(4 * math.pi * p),
         spine_yaw=3 * math.sin(2 * math.pi * p), head_pitch=-2 * math.cos(4 * math.pi * p), head_yaw=-2 * math.sin(2 * math.pi * p))
    tail_wave(14, 4, p, lift=6)
    s = stride * duty
    for kind, side, ph in (('front', 'L', 0.0), ('hind', 'R', 0.0), ('front', 'R', 0.5), ('hind', 'L', 0.5)):
        q = (p + ph) % 1.0
        if q < duty:
            dy = -s / 2 + s * (q / duty); dz = 0.0; pitch = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = s / 2 - s * ss(u); dz = (lift_f if kind == 'front' else lift_h) * math.sin(math.pi * u)
            pitch = 30 * math.sin(math.pi * u)
        base = WRIST[side] if kind == 'front' else ANKLE[side]
        place_leg(kind, side, base + Vector((0, dy, dz)), pitch)


def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 2.0)
    body(spine_pitch=-1.2 * b, head_pitch=1.5 * b, head_yaw=4 * math.sin(2 * math.pi * t / 2.0))
    tail_wave(5, 2, t / 2.0)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


def fidget(t):
    P.reset(rig)
    u = t / 0.625
    sniff = 3 * math.sin(2 * math.pi * 6 * u) * math.sin(math.pi * u)
    body(head_pitch=-12 * math.sin(math.pi * u) + sniff, head_yaw=10 * math.sin(2 * math.pi * u), spine_pitch=-3 * math.sin(math.pi * u))
    tail_wave(18 * math.sin(math.pi * u), 3, u * 2)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


def keyed(keys, t):
    """keys: list of (time, params dict); smoothstep interpolation per segment."""
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            out = {}
            for k in set(a) | set(b):
                va, vb = a.get(k, 0.0), b.get(k, 0.0)
                out[k] = va + (vb - va) * u if not isinstance(va, Vector) and not isinstance(vb, Vector) else \
                    (va if isinstance(va, Vector) else Vector()).lerp(vb if isinstance(vb, Vector) else Vector(), u)
            return out
    return keys[-1][1]


def generic(params, legs_free=False):
    P.reset(rig)
    body(hips_d=params.get('hips', Vector()), hips_pitch=params.get('hips_pitch', 0.0), hips_roll=params.get('roll', 0.0),
         spine_pitch=params.get('spine', 0.0), spine_yaw=params.get('yaw', 0.0),
         head_pitch=params.get('head', 0.0), head_yaw=params.get('head_yaw', 0.0))
    tail_wave(params.get('tail_sway', 0.0), 0, params.get('tail_phase', 0.0), lift=params.get('tail_lift', 0.0))
    rot('Jaw', X, params.get('jaw',0.0))
    for side in 'LR':
        if legs_free:
            place_leg('front', side, None, free=(params.get('fu', 0.0), params.get('fl', 0.0), params.get('fs', 0.0)))
            place_leg('hind', side, None, free=(params.get('hu', 0.0), params.get('hl', 0.0), params.get('hs', 0.0)))
        else:
            off = params.get('front_' + side, Vector())
            place_leg('front', side, WRIST[side] + off, params.get('paw', 0.0))
            place_leg('hind', side, ANKLE[side] + params.get('hind_' + side, Vector()))


    if params.get('ground',0)>0:
        for _ in range(3):
            low=mesh_co()[CORE,2].min()
            root=rig.pose.bones['Spine1']
            root.matrix=Matrix.Translation(Vector((0,0,(.004-low)*params['ground'])))@root.matrix
            bpy.context.view_layer.update()
            for kind,base in [('front',WRIST),('hind',ANKLE)]:
                for side in 'LR':place_leg(kind,side,base[side]+params.get(kind+'_'+side,Vector()))

V = Vector
ATTACK=[
 (0.0,{}),
 (.30,{'hips':V((0,.025,.01)),'hips_pitch':-22,'spine':-17,'head':10,'jaw':22,'tail_lift':18,
       'front_L':V((.025,.015,.20)),'front_R':V((-.025,.015,.20)),'paw':-25}),
 (.50,{'hips':V((0,-.045,.035)),'hips_pitch':-2,'spine':-8,'head':8,'jaw':30,'tail_lift':30,
       'front_L':V((.015,-.09,.065)),'front_R':V((-.015,-.09,.065)),
       'hind_L':V((0,.02,.025)),'hind_R':V((0,.02,.025)),'paw':8}),
 (.65,{'hips':V((0,-.065,-.006)),'hips_pitch':4,'spine':5,'head':12,'jaw':2,'tail_lift':40,
       'front_L':V((.025,-.09,0)),'front_R':V((-.025,-.09,0))}),
 (.78,{'hips':V((0,-.04,-.005)),'spine':4,'head':6,'tail_lift':20,
       'front_L':V((.02,-.06,0)),'front_R':V((-.02,-.06,0))}),
 (1.0,{})]
HIT=[
 (0.0,{}),
 (.125,{'hips':V((0,.025,.015)),'hips_pitch':-18,'spine':-20,'head':-10,'jaw':12,'tail_lift':25,
        'front_L':V((.03,.025,.17)),'front_R':V((-.03,.025,.17)),'paw':-30}),
 (.28,{'hips':V((0,.02,.005)),'hips_pitch':-13,'spine':-12,'head':-6,'jaw':6,'tail_lift':35,
       'front_L':V((.02,.02,.12)),'front_R':V((-.02,.02,.12)),'paw':-20}),
 (.50,{'spine':5,'head':5,'tail_lift':10}),
 (.625,{})]
SPLAT={'hips':V((0,-.045,-.07)),'hips_pitch':8,'spine':5,'head':8,'head_yaw':8,'jaw':6,
       'front_L':V((.07,-.07,0)),'front_R':V((-.07,-.07,0)),
       'hind_L':V((.055,.015,0)),'hind_R':V((-.055,.015,0)),
       'tail_sway':10,'tail_phase':.2,'ground':1.0}
DEATH=[
 (0.0,{}),
 (.22,{'hips':V((0,.025,.015)),'hips_pitch':-25,'spine':-20,'head':-12,'jaw':18,'tail_lift':22,
       'front_L':V((.035,.02,.23)),'front_R':V((-.035,.02,.23)),'paw':-30}),
 (.40,{'hips':V((0,-.035,.015)),'hips_pitch':2,'spine':-5,'head':4,'jaw':12,'tail_lift':38,
       'front_L':V((.06,-.04,.12)),'front_R':V((-.06,-.04,.12)),
       'hind_L':V((.035,.015,.015)),'hind_R':V((-.035,.015,.015))}),
 (.625,dict(SPLAT,ground=.95,head=12)),(.75,SPLAT)]
CLIPS={
 'Standing':(2.0,True,standing),
 'Walking':(1.0,True,lambda t:gait(t,1.0,.30,.58,.045,.035,2)),
 'Running':(.625,True,lambda t:gait(t,.625,.43,.48,.060,.043,4)),
 'Attack':(1.0,False,lambda t:generic(keyed(ATTACK,t))),
 'Hit':(.625,False,lambda t:generic(keyed(HIT,t))),
 'Death':(.75,False,lambda t:generic(keyed(DEATH,t))),
 'Fidget':(.625,False,fidget),
 'Dead':(1.0,False,lambda t:generic(SPLAT))}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; act['loop']=loop
    if rig.animation_data is None:
        rig.animation_data_create()
    n = int(round(seconds * FPS))
    poses = []
    rig.animation_data.action = None
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        fn(t)
        floor_fit(lift_core=name in ('Attack', 'Hit', 'Death', 'Dead'))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    if loop:
        assert all(abs(abs(poses[0][n][0].dot(poses[-1][n][0]))-1)<1e-5 and
                   (poses[0][n][1]-poses[-1][n][1]).length<1e-5 for n in poses[0])
    rig.animation_data.action = None
    return act


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
info={'fps':FPS,'walk_stride_m':.30,'run_stride_m':.43,'attack_contact_seconds':.65,
      'clips':{n:{'seconds':v[0],'loop':v[1]} for n,v in CLIPS.items()}}
json.dump(info,open(os.path.join(HERE,'work/anim_info.json'),'w'),indent=2)
sc.render.fps=FPS
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work/anim_v1.blend'))
print('SAVED anim_v1.blend')
