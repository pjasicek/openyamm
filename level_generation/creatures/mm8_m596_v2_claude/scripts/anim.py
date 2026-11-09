"""Author the Crystal Walker v2 clips on the fitted rig (work/rig_v1.blend), keyed at 48 fps.
Poses are rotations about each joint in world rest axes (degrees, XYZ), as in the installed walker's build.py, so the
native intent carries over; every curve is a monotone cubic through its keys (continuous speed, no stop at inner
keys), legs in Walking/Running by two-bone IK to planted soles, a mesh floor pass in Hit/Death/Dead.
Clips and the actors.yml contract: Standing 2.0 loop, Walking 1.0 loop, Running 0.75 loop, Attack 1.5 and Cast 1.5
(impact 0.8333), Hit 0.7917, Fidget 0.625, Death 1.0, Dead 1.0.
Usage: blender -b -P anim.py -- <rig.blend> <out.blend> <out_lod0.glb>"""
import json, math, os, sys, bpy
from mathutils import Matrix, Vector, Euler
a = sys.argv[sys.argv.index('--') + 1:]; src, dst, glb = a
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 48
CLIPS = {'Standing': 2.0, 'Walking': 1.0, 'Running': .75, 'Attack': 1.5, 'Cast': 1.5, 'Hit': 19 / 24,
         'Fidget': .625, 'Death': 1.0, 'Dead': 1.0}
WALK = dict(stride=.70, duty=.60, lift=.10, sink=.065)
RUN = dict(stride=1.00, duty=.45, lift=.16, sink=.085)


def pchip(keys):
    """monotone cubic (Fritsch-Carlson) through (t, v) keys; flat at the ends"""
    t = [k[0] for k in keys]; v = [k[1] for k in keys]; n = len(t)
    d = [(v[i + 1] - v[i]) / (t[i + 1] - t[i]) for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * (t[i + 1] - t[i]) + (t[i] - t[i - 1]); w2 = (t[i + 1] - t[i]) + 2 * (t[i] - t[i - 1])
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def f(x):
        if x <= t[0]:
            return v[0]
        if x >= t[-1]:
            return v[-1]
        i = max(j for j in range(n - 1) if t[j] <= x)
        h = t[i + 1] - t[i]; s = (x - t[i]) / h
        h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
        return h00 * v[i] + h10 * h * m[i] + h01 * v[i + 1] + h11 * h * m[i + 1]
    return f


bpy.ops.wm.open_mainfile(filepath=os.path.join(P, src))
scene = bpy.context.scene; scene.render.fps = FPS
rig = bpy.data.objects['CrystalRig']; body = bpy.data.objects['CrystalWalker']
data = rig.data


def crystal_material():
    """one opaque crystal material: facet base colour, per-facet roughness (orm G), nonmetal; engine extras"""
    mat = bpy.data.materials.new('AmethystCrystal'); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
    base = nt.nodes.new('ShaderNodeTexImage'); base.image = bpy.data.images.load(os.path.join(P, 'textures/basecolor.png'))
    orm = nt.nodes.new('ShaderNodeTexImage'); orm.image = bpy.data.images.load(os.path.join(P, 'textures/orm.png'))
    orm.image.colorspace_settings.name = 'Non-Color'
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(orm.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    mat['openyamm_specular'] = .8; mat['openyamm_edge_darkening'] = .12
    return mat


if os.path.exists(os.path.join(P, 'textures/basecolor.png')):
    body.data.materials.clear(); body.data.materials.append(crystal_material())
REST = {b.name: b.matrix_local.copy() for b in data.bones}
HEAD = {b.name: b.head_local.copy() for b in data.bones}
DIR = {b.name: (b.tail_local - b.head_local).normalized() for b in data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in data.bones}
ORDER = [b.name for b in data.bones]  # parents before children
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# --- clip curves -------------------------------------------------------------------------------------------------
def pos(x, e=.1):
    """smooth positive part (0 at 0): max(x, 0) has a kink where the speed jumps"""
    return .5 * (x + math.sqrt(x * x + e * e)) - e / 2


def vpchip(keys):
    """monotone cubic per component through (t, vector) keys, renormalised: a smooth direction path"""
    fs = [pchip([(t, v[i]) for t, v in keys]) for i in range(3)]
    return lambda t: Vector(tuple(f(t) for f in fs)).normalized()


# Attack (review 2): the right claw rises high on its right, then swipes diagonally down across the front to the
# front-left, passing in front of the body centre at chest height at the impact (0.8333). Arm and forearm are aimed
# by minimal swing (no roll, so the shoulder does not twist); the clavicle shares the raise.
R_UP, R_FORE = DIR['RightArm'], DIR['RightForeArm']
ATK = {
    'up': vpchip([(0, R_UP), (.40, (-.55, .22, .80)), (.60, (-.58, .30, .76)), (.70, (-.40, -.12, .90)),
                  (.8333, (.45, -.86, -.12)), (.97, (.74, -.44, -.50)), (1.18, (.30, -.25, -.92)), (1.5, R_UP)]),
    'fore': vpchip([(0, R_FORE), (.40, (-.32, .36, .88)), (.60, (-.28, .45, .85)), (.70, (-.10, -.05, .99)),
                    (.8333, (.70, -.62, -.36)), (.97, (.72, -.20, -.66)), (1.18, (.10, -.30, -.95)), (1.5, R_FORE)]),
    'coil': pchip([(0, 0), (.40, 1.0), (.60, 1.1), (.70, .8), (.8333, -.35), (.97, -1.0), (1.2, -.45), (1.5, 0)]),
    'lift': pchip([(0, 0), (.40, 1.0), (.62, 1.0), (.8333, .3), (.97, 0), (1.5, 0)]),
    'reach': pchip([(0, 0), (.62, 0), (.8333, .8), (.97, 1.0), (1.2, .4), (1.5, 0)]),
}
PELVIS = [pchip([(0, 0), (.40, a), (.60, b), (.70, c), (.8333, d), (.97, e), (1.20, f), (1.5, 0)])
          for a, b, c, d, e, f in zip((-.06, .035, -.025), (-.065, .045, -.03), (-.03, 0, -.035), (.03, -.13, -.075),
                                      (.04, -.15, -.085), (.01, -.05, -.035))]
STEP, HOME = .30, (.50, .80, 1.05, 1.40)   # left foot: lift-off, landing, lift-off back, landing home (s)


def LSTEP(t):
    """left foot forward travel, lift and toe pitch: planted, eased swing forward, planted, eased swing home"""
    a, b, c, d = HOME
    if t < a or t >= d:
        return 0.0, 0.0, 0.0
    if t < b:
        u = (t - a) / (b - a); e = u * u * (3 - 2 * u)
        return STEP * e, .10 * math.sin(math.pi * u) ** 2, -10 * math.sin(math.pi * u) ** 2
    if t < c:
        return STEP, 0.0, 0.0
    u = (t - c) / (d - c); e = u * u * (3 - 2 * u)
    return STEP * (1 - e), .07 * math.sin(math.pi * u) ** 2, -8 * math.sin(math.pi * u) ** 2


L_UP, L_FORE = DIR['LeftArm'], DIR['LeftForeArm']
CST = {   # both claws rise forward-up, then push toward the target through the release (0.8333)
    'r_up': vpchip([(0, R_UP), (.55, (-.30, -.50, .81)), (.72, (-.28, -.42, .86)), (.8333, (-.18, -.97, .15)),
                    (.98, (-.20, -.95, .05)), (1.25, (-.25, -.45, -.85)), (1.5, R_UP)]),
    'r_fore': vpchip([(0, R_FORE), (.55, (-.10, -.75, .65)), (.72, (-.08, -.65, .75)), (.8333, (-.10, -.99, .05)),
                      (.98, (-.10, -.98, -.10)), (1.25, (-.15, -.55, -.80)), (1.5, R_FORE)]),
    'lean': pchip([(0, 0), (.55, -1), (.72, -1.1), (.8333, .8), (1.0, .7), (1.5, 0)]),
}


def mirror(v):
    return Vector((-v.x, v.y, v.z))


HIT = pchip([(0, 0), (.12, 1.0), (.32, .7), (.55, .25), (19 / 24, 0)])
FALL = pchip([(0, 0), (.15, .06), (.30, .32), (.50, .78), (.68, 1.0), (1.0, 1.0)])
LEGS = pchip([(0, 0), (.30, .04), (.50, .45), (.70, .92), (.85, 1.0), (1.0, 1.0)])   # legs follow the fall late
KNEE = pchip([(0, 0), (.22, .8), (.45, 1.0), (.70, .45), (.85, .25), (1.0, .25)])    # knees buckle, then relax
FID = pchip([(0, 0), (.22, 1.0), (.40, .85), (.625, 0)])


def leg_ik(deltas, s, ank_n, pitch=0.0):
    """two-bone IK of one leg from the posed hip to a world ankle target (knee forward), foot level plus pitch"""
    hip, knee, ank = HEAD[s + 'Thigh'], HEAD[s + 'Shin'], HEAD[s + 'Foot']
    hip_n = deltas['Hips'] @ hip
    ax = ank_n - hip_n; dist = ax.length; ax.normalize()
    la = (knee - hip).length; lb = (ank - knee).length
    dist = min(dist, (la + lb) * .995)
    along = (la * la - lb * lb + dist * dist) / (2 * dist)
    pole = Vector((0, -1, 0)); pole = (pole - ax * pole.dot(ax)).normalized()
    knee_n = hip_n + ax * along + pole * math.sqrt(max(0, la * la - along * along))
    ank_n = hip_n + ax * dist
    for n, s0, e0, s1, e1 in ((s + 'Thigh', hip, knee, hip_n, knee_n), (s + 'Shin', knee, ank, knee_n, ank_n)):
        turn = (e0 - s0).rotation_difference(e1 - s1).to_matrix().to_4x4()
        deltas[n] = Matrix.Translation(s1) @ turn @ Matrix.Translation(-s0)
    deltas[s + 'Foot'] = (Matrix.Translation(ank_n) @ Euler((math.radians(pitch), 0, 0)).to_matrix().to_4x4()
                          @ Matrix.Translation(-ank))


def posing(clip, t, lift=0.0):
    ang = {}; trans = Vector((0, 0, lift)); aim = {}
    def rot(n, x=0, y=0, z=0):
        ox, oy, oz = ang.get(n, (0, 0, 0)); ang[n] = (ox + x, oy + y, oz + z)
    dur = CLIPS[clip]
    if clip in ('Standing', 'Fidget', 'Hit', 'Attack', 'Cast'):
        ph = t / dur * math.tau if clip == 'Standing' else 0
        b = math.sin(ph); c = math.cos(ph)
        if clip == 'Standing':   # breathing and a slow weight shift; claws flex
            rot('Chest', -1.6 * b, .8 * c, 1.2 * c); rot('Neck', .8 * b); rot('Head', .6 * b, 0, -2.5 * c)
            for s, g in (('Left', 1), ('Right', -1)):
                rot(s + 'Arm', 2.0 * b, g * 1.5 * (1 - c) * .5, 0); rot(s + 'ForeArm', -2.5 * b)
                rot(s + 'Hand', -4 * b)
    if clip == 'Fidget':
        f = FID(t)
        rot('Head', -4 * f, 0, 20 * f); rot('Neck', -2 * f, 0, 6 * f); rot('Chest', 0, 0, 4 * f)
        rot('LeftHand', -14 * f, 0, 6 * f); rot('LeftForeArm', -10 * f)
    if clip == 'Attack':
        k, lf, rc = ATK['coil'](t), ATK['lift'](t), ATK['reach'](t)
        aim['RightArm'] = ATK['up'](t); aim['RightForeArm'] = ATK['fore'](t)
        trans += Vector(tuple(f(t) for f in PELVIS))
        rot('Hips', 4 * pos(-k), 0, -8 * k); rot('Neck', 0, 0, 5 * k); rot('Head', 0, 0, 3 * k)
        rot('RightShoulder', 0, 16 * lf, 10 * rc)
        rot('RightHand', -10 * lf + 12 * rc)
        # trunk: wind turns the right shoulder back and leans back, the swipe turns it through and leans in;
        # neck and head counter-turn so the head keeps facing forward
        rot('Chest', -5 * pos(k) + 10 * pos(-k), 0, -13 * k)
        rot('Waist', -2 * pos(k) + 5 * pos(-k), 0, -6 * k)
        rot('Neck', 3 * pos(k) - 6 * pos(-k), 0, 11 * k)
        rot('Head', 2 * pos(k) - 4 * pos(-k), 0, 8 * k)
        rot('LeftArm', 12 * pos(-k) - 6 * pos(k), 0, -6 * lf)
        rot('LeftForeArm', -12 * lf - 10 * pos(-k))
    if clip == 'Cast':
        ln = CST['lean'](t)
        aim['RightArm'] = CST['r_up'](t); aim['RightForeArm'] = CST['r_fore'](t)
        aim['LeftArm'] = mirror(CST['r_up'](t)); aim['LeftForeArm'] = mirror(CST['r_fore'](t))
        up = pos(-ln)
        for s_, g in (('Left', -1), ('Right', 1)):
            rot(s_ + 'Shoulder', 0, g * 12 * up, 0); rot(s_ + 'Hand', 18 * pos(ln) - 8 * up)
        rot('Chest', 7 * ln, 0, 0); rot('Waist', 3 * ln); rot('Neck', -4 * ln); rot('Head', -3 * ln)
    if clip == 'Hit':
        h = HIT(t)
        rot('Chest', -15 * h, 0, -8 * h); rot('Waist', -5 * h); rot('Head', -12 * h, 0, 6 * h)
        rot('LeftArm', -22 * h, 0, -10 * h); rot('RightArm', -26 * h, 0, 12 * h)
        rot('LeftForeArm', -18 * h); rot('RightForeArm', -14 * h)
    if clip in ('Death', 'Dead'):
        tt = 1.0 if clip == 'Dead' else t
        f, fl, kb = FALL(tt), LEGS(tt), KNEE(tt)
        # the trunk tips back about the hips while the legs stay near upright, buckle at the knees, and only
        # follow the trunk down at the end (no feet swinging up mid-fall)
        rot('Hips', -88 * f); rot('Chest', 8 * f); rot('Neck', 10 * f); rot('Head', 8 * f)
        for s, g in (('Left', 1), ('Right', -1)):
            rot(s + 'Arm', 30 * f, g * 50 * f, 0); rot(s + 'ForeArm', -12 * f); rot(s + 'Hand', -10 * f)
            rot(s + 'Thigh', 88 * (f - fl) - 38 * kb, g * 6 * f, 0); rot(s + 'Shin', 62 * kb); rot(s + 'Foot', -24 * kb * (1 - fl))
        trans.y = .30 * f; trans.z += -.80 * f
    deltas = {}; world = {}
    for n in ORDER:
        h = HEAD[n]; pd = deltas.get(PARENT[n], Matrix.Identity(4))
        r = Euler(tuple(math.radians(x) for x in ang.get(n, (0, 0, 0))), 'XYZ').to_matrix().to_4x4()
        if n in aim:   # swing (no roll) from the rest direction (after the parent) to the world target
            local = pd.to_3x3().inverted() @ aim[n]
            if n.endswith('Arm') and not n.endswith('ForeArm'):
                # upper arms go via a neutral out-and-forward direction: a direct swing from hanging down to raised
                # overhead is near 180 deg, where the swing axis is undefined and the arm flipped (review 2: the
                # right shoulder twisted at frame 29)
                nd = Vector((.949 if n.startswith('Left') else -.949, -.316, 0))
                q = nd.rotation_difference(local) @ DIR[n].rotation_difference(nd)
            else:
                q = DIR[n].rotation_difference(local)
            r = q.to_matrix().to_4x4() @ r
        deltas[n] = Matrix.Translation(trans) if n == 'Root' else pd @ Matrix.Translation(h) @ r @ Matrix.Translation(-h)
    if clip in ('Walking', 'Running'):
        cfg = WALK if clip == 'Walking' else RUN
        ph = t / dur
        bob = -cfg['sink'] + .012 * (1 - math.cos(4 * math.pi * ph))
        deltas['Root'] = Matrix.Translation((0, 0, bob))
        sw = math.sin(2 * math.pi * ph)
        # upper body: chest counter-twist, arms swing opposite the legs, head steady
        extra = {'Hips': (0, 2 * sw, -3 * sw), 'Chest': (-3 if clip == 'Running' else -1, 0, 4 * sw),
                 'Head': (0, 0, -3 * sw), 'LeftArm': (-14 * sw if clip == 'Walking' else -24 * sw, 0, 0),
                 'RightArm': (14 * sw if clip == 'Walking' else 24 * sw, 0, 0),
                 'LeftForeArm': (-8 - 6 * max(0, -sw), 0, 0), 'RightForeArm': (-8 - 6 * max(0, sw), 0, 0)}
        for n in ORDER:
            if n in ('Root',) or n.endswith(('Thigh', 'Shin', 'Foot')):
                continue
            h = HEAD[n]; pd = deltas[PARENT[n]]
            r = Euler(tuple(math.radians(x) for x in extra.get(n, (0, 0, 0))), 'XYZ').to_matrix().to_4x4()
            deltas[n] = pd @ Matrix.Translation(h) @ r @ Matrix.Translation(-h)
        for s, shift in (('Left', 0), ('Right', .5)):
            q = (ph + shift) % 1; duty, stride, lift = cfg['duty'], cfg['stride'], cfg['lift']
            hip, knee, ank = HEAD[s + 'Thigh'], HEAD[s + 'Shin'], HEAD[s + 'Foot']
            hip_n = deltas['Hips'] @ hip
            if q < duty:
                travel = (duty / 2 - q) * stride; height = 0.0   # planted: the sole slides back under the body
            else:
                u = (q - duty) / (1 - duty)
                h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h01 = -2 * u ** 3 + 3 * u ** 2
                h10 = u ** 3 - 2 * u ** 2 + u; h11 = u ** 3 - u ** 2
                v_plant = -stride  # planted speed, per unit phase
                travel = h00 * (-duty / 2 * stride) + h01 * (duty / 2 * stride) + (h10 + h11) * (-v_plant) * (1 - duty) * .5
                height = math.sin(u * math.pi) ** 2 * lift
            pitch = -12 * math.sin(math.pi * max(0, (q - duty) / (1 - duty))) if q >= duty else 0
            leg_ik(deltas, s, ank + Vector((0, -travel, height)), pitch)
    if clip == 'Attack':
        # whole-body swipe (review 3: "use legs also"): the right foot stays planted, the left foot steps forward
        # into the swipe and back; the pelvis shifts onto the right leg in the raise, lunges forward and down
        # through the cut and returns; knees bend by IK to the locked soles
        for s_, step in (('Right', None), ('Left', LSTEP)):
            ank = HEAD[s_ + 'Foot']
            if step is None:
                leg_ik(deltas, s_, ank.copy(), 0)
            else:
                fwd, lift, pitch = step(t)
                leg_ik(deltas, s_, ank + Vector((0, -fwd, lift)), pitch)
    for n in ORDER:
        world[n] = deltas[n] @ REST[n]
    for n in ORDER:
        p = PARENT[n]
        rr = REST[p].inverted() @ REST[n] if p else REST[n]
        pr = world[p].inverted() @ world[n] if p else world[n]
        rig.pose.bones[n].matrix_basis = rr.inverted() @ pr


def floor_min():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear(); return z


rig.animation_data_create(); report = {}
for clip, dur in CLIPS.items():
    act = bpy.data.actions.new(clip); act.use_fake_user = True; rig.animation_data.action = act
    frames = round(dur * FPS); prev = {}; lows = []
    for fr in range(frames + 1):
        t = min(fr / FPS, dur); scene.frame_set(fr + 1); posing(clip, t); bpy.context.view_layer.update()
        if clip in ('Hit', 'Death', 'Dead', 'Attack', 'Cast'):
            low = floor_min()
            lift = -low if (low < 0 or (clip in ('Death', 'Dead') and FALL(1.0 if clip == 'Dead' else t) > .6)) else 0
            if abs(lift) > 1e-5:
                posing(clip, t, lift); bpy.context.view_layer.update()
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
    report[clip] = {'duration': frames / FPS, 'keys': frames + 1, 'floor_min': min(lows), 'floor_max': max(lows)}
    print('CLIP', clip, report[clip], flush=True)
rig.animation_data.action = bpy.data.actions['Standing']; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, dst))
for o in bpy.data.objects:
    o.select_set(o in (rig, body))
bpy.ops.export_scene.gltf(filepath=os.path.join(P, glb), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_skins=True, export_all_influences=False, export_attributes=False, export_extras=True,
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(os.path.join(P, 'work', 'anim_report.json'), 'w'), indent=1)
