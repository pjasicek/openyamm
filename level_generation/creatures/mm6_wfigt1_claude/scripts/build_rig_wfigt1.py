"""Rigged master from Meshy's API auto-rig (meshy/rig_v1, 1.578 m, armature at 0.01 scale) and our UV mesh
(work/step1_uv.blend, same surface). Saves work/rig_v1.blend. Adapted from the titan's build_rig_ttn.py.
 1. The armature scale is applied (location keys rescaled), Meshy's walking/running clips are merged in as
    'Walking'/'Running' (+ any Meshy library clips given as arguments, named after the argument).
 2. Our mesh takes Meshy's skin weights from the nearest surface point of Meshy's mesh (face-interpolated).
 3. Rigid parts: hands below the wrist 100 % on their Hand bone (Meshy gives no finger chains; the claws are open and
    fixed); head skin above the neck, teeth and tongue 100 % on Head. Every mane card, fur tuft and the pendant take
    one weight set per connected piece (the mean final weight of the body skin under it), so a card moves rigidly instead of bending.
    Upper-arm and clavicle weight is ramped out of the chest toward the midline (titan lesson), and upper-arm weight
    on the torso skin fades out below the armpit (lats; user review 5). At most 4 influences.
 4. Jaw: a 'Jaw' bone (child of Head, hinge behind the mouth corners) carries the lower jaw below the measured mouth
    line, the lower teeth and the tongue, faded in over 5 cm in front of the hinge; the attack opens the mouth.
 5. Feet/wrists/shoulders of the Meshy locomotion clips as in the titan (sole flat on the ground, wrist flex 50 %,
    clavicles within 3 deg of rest).
Usage: blender --background --python build_rig_wfigt1.py -- [anim.glb:Name ...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

EXTRA = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
RIG = os.path.join(common.PROJECT, 'meshy', 'rig_v1')


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


def import_glb(path):
    before = set(bpy.data.objects)
    acts = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before], [a for a in bpy.data.actions if a not in acts]


objs, acts = import_glb(os.path.join(RIG, 'result_rigged_character_glb_url.glb'))
arm = next(o for o in objs if o.type == 'ARMATURE')
arm.name = 'Werewolf_Rig'
src = next(o for o in objs if o.type == 'MESH' and o.name.startswith('char'))
src.name = 'MeshyWerewolf'
for o in objs:
    if o not in (arm, src):
        bpy.data.objects.remove(o, do_unlink=True)
for a in acts:
    bpy.data.actions.remove(a)
clips = [(os.path.join(RIG, 'result_basic_animations_walking_glb_url.glb'), 'Walking'),
         (os.path.join(RIG, 'result_basic_animations_running_glb_url.glb'), 'Running')]
for e in EXTRA:
    p, n = e.rsplit(':', 1)
    clips.append((os.path.join(common.PROJECT, p), n))
for path, name in clips:
    o2, a2 = import_glb(path)
    for o in o2:
        bpy.data.objects.remove(o, do_unlink=True)
    keep = max(a2, key=lambda a: a.frame_range[1] - a.frame_range[0])
    for a in a2:
        if a is not keep:
            bpy.data.actions.remove(a)
    keep.name = name
    keep.use_fake_user = True
    print('CLIP', name, tuple(round(x, 2) for x in keep.frame_range))

# 1. apply the 0.01 armature scale; location keys are in the old (cm) bone space
k = arm.scale[0]
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.context.view_layer.objects.active = arm
arm.animation_data_create()
arm.animation_data.action = None
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
for a in bpy.data.actions:
    for fc in fcurves(a):
        if fc.data_path.endswith('location'):
            for kp in fc.keyframe_points:
                kp.co[1] *= k
                kp.handle_left[1] *= k
                kp.handle_right[1] *= k
            fc.update()
print('ARMATURE scale applied', k, 'world', tuple(arm.matrix_world.to_scale()))


def resample(act):
    """Meshy keys sit on fractional frames (30 fps keys at 24 fps). Re-key every bone on integer frames 0..N
    spanning the same time (N = rounded length; the last frame repeats the first pose of cyclic clips)."""
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    a0, a1 = act.frame_range
    n = max(1, int(round(a1 - a0)))
    poses = []
    for f in range(n + 1):
        t = a0 + (a1 - a0) * f / n
        scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
        poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones})
    new = bpy.data.actions.new(act.name)
    name = act.name
    bpy.data.actions.remove(act)
    new.name = name
    new.use_fake_user = True
    arm.animation_data.action = new
    for f, pose in enumerate(poses):
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            pb.location, pb.rotation_quaternion = pose[pb.name]
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('RESAMPLE', name, 'frames 0 ..', n)


for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
for a in list(bpy.data.actions):
    resample(a)

with bpy.data.libraries.load(os.path.join(common.WORK, 'step1_uv.blend')) as (df, dt):
    dt.objects = ['Werewolf']
    dt.scenes = df.scenes[:1]
mesh = dt.objects[0]
scene.collection.objects.link(mesh)
lib = dt.scenes[0]
for key in ('wfigt1_parts', 'wfigt1_uv_regions'):
    scene[key] = lib[key]
bpy.data.scenes.remove(lib)
PARTS = json.loads(scene['wfigt1_parts'])
me = mesh.data

# 2. weights from the nearest point on Meshy's surface (barycentric over the hit triangle)
dg = bpy.context.evaluated_depsgraph_get()
sme = src.data
sco = [src.matrix_world @ v.co for v in sme.vertices]
sme.calc_loop_triangles()
tris = [tuple(t.vertices) for t in sme.loop_triangles]
tree = BVHTree.FromPolygons(sco, tris)
gname = {g.index: g.name for g in src.vertex_groups}
W = np.zeros((len(sco), len(gname)))
for v in sme.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
for g in src.vertex_groups:
    mesh.vertex_groups.new(name=g.name)
dmax = 0.0
OW = np.zeros((len(me.vertices), len(gname)))
for v in me.vertices:
    p = mesh.matrix_world @ v.co
    loc, nrm, ti, d = tree.find_nearest(p)
    dmax = max(dmax, d)
    a, b, c = (sco[i] for i in tris[ti])
    from mathutils.geometry import barycentric_transform
    bc = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    OW[v.index] = sum(max(bc[j], 0.0) * W[tris[ti][j]] for j in range(3))
print('WEIGHT_COPY max distance', round(dmax * 1000, 3), 'mm')
OW0 = OW.copy()                          # Meshy's weights, for matching cards to the skin they belonged to

# 3. rigid parts
part = np.zeros(len(me.polygons), dtype=np.int32)
me.attributes['part'].data.foreach_get('value', part)
gidx = {n: i for i, n in gname.items()}
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
vpart = {}
for p in me.polygons:
    for vi in p.vertices:
        vpart.setdefault(vi, set()).add(PARTS[part[p.index]])
rigid = {'LeftHand': 0, 'RightHand': 0, 'Head': 0}
HEAD_RIGID = {'Teeth', 'Tongue'}
for vi, ps in vpart.items():
    target = None
    if 'Body' in ps and co[vi, 2] < 0.79 and abs(co[vi, 0]) > 0.33:
        target = 'LeftHand' if co[vi, 0] > 0 else 'RightHand'
    elif ps & HEAD_RIGID or ('Body' in ps and (co[vi, 2] > 1.37 or (co[vi, 2] > 1.29 and co[vi, 1] < -0.2))):
        target = 'Head'
    if target:
        OW[vi] = 0.0
        OW[vi, gidx[target]] = 1.0
        rigid[target] += 1
# arm bleed (user review 106: the right pec stretched with the arm overhead in the hook): Meshy gave the chest up to
# 55 % upper-arm and 97 % clavicle weight up to the sternum. On the torso skin (Body, z 0.85-1.30) the allowed arm
# weight ramps from 0 at |x| ARM_X0 to full at ARM_X1 and the clavicle's from 0 at CLAV_X0 to full at CLAV_X1; the
# removed weight goes to the vertex's spine bones (Spine if it has none), so the cuirass moves with the chest.
ARM_X0, ARM_X1, CLAV_X0, CLAV_X1 = 0.12, 0.21, 0.05, 0.17
SPINE_B = [gidx[n] for n in ('Spine', 'Spine01', 'Spine02') if n in gidx]
bleed = 0
for vi, ps in vpart.items():
    if ps != {'Body'} or not (0.85 < co[vi, 2] < 1.30) or OW[vi, gidx['Head']] >= 0.999:
        continue
    ax = abs(co[vi, 0])
    allow_arm = min(1.0, max(0.0, (ax - ARM_X0) / (ARM_X1 - ARM_X0)))
    allow_clav = min(1.0, max(0.0, (ax - CLAV_X0) / (CLAV_X1 - CLAV_X0)))
    moved = 0.0
    for n, allow in (('LeftArm', allow_arm), ('RightArm', allow_arm), ('LeftShoulder', allow_clav),
                     ('RightShoulder', allow_clav)):
        j = gidx[n]
        extra = OW[vi, j] * (1 - allow)
        OW[vi, j] -= extra; moved += extra
    if moved > 1e-4:
        sw = OW[vi, SPINE_B]
        if sw.sum() > 1e-4:
            OW[vi, SPINE_B] += moved * sw / sw.sum()
        else:
            OW[vi, gidx['Spine']] += moved
        bleed += 1
rigid['chest bleed fixed'] = bleed
# upper-arm skin (user review 6: the biceps thinned and sheared with the claws raised; scripts/arm_volume.py measured
# one side of the upper arm at 34 % of its rest thickness): Meshy weighted the upper arm 20-30 % to the clavicle and
# up to 15 % to the spine all the way to the elbow, so that share stays behind when the arm rises. Along the
# shoulder->elbow segment the allowed clavicle/spine/hip/leg weight fades from full at t UA_T0 to 0 at UA_T1 and goes
# to the upper-arm bone; skin on the torso side further than UA_LAT from the bone axis (the lat) is left alone.
UA_T0, UA_T1, UA_R, UA_LAT, UA_SMOOTH = 0.12, 0.35, 0.17, 0.07, 12
TORSO_B = [gidx[n] for n in ('LeftShoulder', 'RightShoulder', 'Spine', 'Spine01', 'Spine02', 'Hips', 'LeftUpLeg',
                             'RightUpLeg', 'neck') if n in gidx]
def upper_arm_pass():
    """Armness field (1 = upper-arm skin far enough down the arm, 0 = torso), smoothed over the mesh so neighbouring
    vertices never differ abruptly (user review 7: per-vertex cut-offs left armpit vertices 100 % on the arm next to
    torso-weighted ones; they spiked 7 cm out of the shoulder junction); torso-bone weight x armness moves to the
    upper-arm bone of the vertex's side."""
    arm_ness = np.zeros(len(me.vertices))
    side_of = {}
    for vi, ps in vpart.items():
        if 'Body' not in ps or OW[vi, RIGID_B].max() >= 0.999:
            continue
        side = 'Left' if co[vi, 0] > 0 else 'Right'
        A_ = np.array(arm.matrix_world @ arm.data.bones[side + 'Arm'].head_local)
        B_ = np.array(arm.matrix_world @ arm.data.bones[side + 'ForeArm'].head_local)
        L_ = np.linalg.norm(B_ - A_); u_ = (B_ - A_) / L_
        t = float((co[vi] - A_) @ u_ / L_)
        r = co[vi] - A_ - t * L_ * u_; d = float(np.linalg.norm(r))
        inward = np.array([-A_[0], 0.0, 0.0]); inward /= np.linalg.norm(inward)
        reach = min(1.0, max(0.0, (UA_R - d) / 0.04))
        if r @ inward > 0.5 * d:
            reach *= min(1.0, max(0.0, (UA_LAT + 0.04 - d) / 0.04))
        tr = min(1.0, max(0.0, (t - UA_T0) / (UA_T1 - UA_T0))) if t <= 1.05 else 1.0
        arm_ness[vi] = reach * tr
        side_of[vi] = side
    ids = np.array(sorted(side_of))
    for _ in range(UA_SMOOTH):
        avg = np.array([arm_ness[nbr[vi]].mean() if len(nbr[vi]) else arm_ness[vi] for vi in ids])
        arm_ness[ids] = 0.5 * arm_ness[ids] + 0.5 * avg
    ua = 0
    for vi in ids:
        k = arm_ness[vi]
        if k < 1e-3:
            continue
        side = side_of[vi]
        moved = 0.0
        for j in TORSO_B:
            extra = OW[vi, j] * k
            OW[vi, j] -= extra; moved += extra
        OW[vi, gidx[side + 'Arm']] += moved
        ua += 1
    return ua


adj = {}
for e in me.edges:
    a, b = e.vertices
    adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
# shoulder smoothing (user review 5: the lat and armpit stretched with the claws raised; review/heat_v1.png): Meshy's
# arm-to-torso weight transition on this broad torso is a few centimetres wide, so a raised arm stretches a narrow
# band of skin a lot (cutting the arm weight off the lats only moved the tear onto the triceps, heat_v3.png). The
# weights of the body skin between the shorts' top and the neck (z SM_Z0..SM_Z1, no neck/head weight, not hands)
# are smoothed
# over the mesh (SM_ITER Laplacian passes, rate SM_RATE) so the transition spreads over a wide area.
SM_Z0, SM_Z1, SM_ITER, SM_RATE = float(os.environ.get('SM_Z0', 0.98)), 1.28, int(os.environ.get('SM_ITER', 20)), 0.5
NECK = [gidx[n] for n in ('neck', 'Head') if n in gidx]
RIGID_B = [gidx[n] for n in ('LeftHand', 'RightHand', 'Head', 'Jaw') if n in gidx]
# (only the rigid hand/head vertices are fixed; armpit vertices left 100 % on the upper arm by the upper-arm pass
# must blend with their neighbours, user review 7: they spiked 7 cm out of the shoulder junction)
free = np.array([('Body' in vpart.get(vi, ())) and SM_Z0 < co[vi, 2] < SM_Z1 and OW[vi, RIGID_B].max() < 0.999
                 and OW[vi, NECK].sum() < 1e-4 for vi in range(len(me.vertices))])
# neck and head weights keep their values (the head texture split selects faces by them; its UVs must match the head
# retexture)
nbr = [np.array(adj.get(vi, []), dtype=np.int64) for vi in range(len(me.vertices))]
idx = np.where(free)[0]
for _ in range(SM_ITER):
    avg = np.array([OW[nbr[vi]].mean(0) if len(nbr[vi]) else OW[vi] for vi in idx])
    OW[idx] = OW[idx] * (1 - SM_RATE) + avg * SM_RATE
lat = len(idx)
rigid['upper-arm skin freed'] = upper_arm_pass()      # after the smoothing (it diffused torso weight into the arm)
rigid['shoulder smoothed'] = lat
# armour plates: one weight set per connected piece
PLATES = {'Mane', 'Fur', 'Pendant'}
from mathutils.kdtree import KDTree as _KD
skin_by_bone = {}
for vi, ps in vpart.items():
    if ps == {'Body'}:
        skin_by_bone.setdefault(int(np.argmax(OW0[vi])), []).append(vi)
skin_kd = {}
for bone_, ids in skin_by_bone.items():
    kd_ = _KD(len(ids))
    for i_, vi in enumerate(ids):
        kd_.insert(Vector(co[vi]), i_)
    kd_.balance()
    skin_kd[bone_] = (ids, kd_)
seen = set(); pieces = 0
for vi, ps in vpart.items():
    if vi in seen or not (ps & PLATES) or len(ps) > 1:
        continue
    comp = [vi]; seen.add(vi); st = [vi]
    while st:
        x = st.pop()
        for y in adj.get(x, []):
            if y not in seen and vpart.get(y) == ps:
                seen.add(y); comp.append(y); st.append(y)
    # each card follows the skin under it (user review 7: cards kept Meshy's clavicle weights after the shoulder skin
    # was moved to the upper arm and poked out of the shoulder as fins): mean final weight of the nearest body skin
    # (nearest skin that Meshy gave the same dominant bone: an elbow tuft hangs next to the torso at rest)
    dom = int(np.argmax(OW0[comp].mean(0)))
    if ps == {'Fur'} and dom in skin_kd:          # limb tufts only: mane and pendant keep their own mean (the head
                                                  # texture split selects faces by these weights)
        ids, kd_ = skin_kd[dom]
        OW[comp] = np.mean([OW[ids[kd_.find(Vector(co[c]))[1]]] for c in comp], 0)
    else:
        OW[comp] = OW[comp].mean(0)
    pieces += 1
rigid['rigid cards'] = pieces
print('RIGID', rigid)
for vi in range(len(me.vertices)):
    w = OW[vi]
    top = np.argsort(-w)[:4]
    s = w[top].sum()
    for j in top:
        if w[j] > 1e-4:
            mesh.vertex_groups[gname[j]].add([vi], float(w[j] / s), 'REPLACE')
# 4. jaw bone and weights (mouth line measured on the midline: z 1.342 at y -0.38 rising to 1.37 at y -0.25)
XC, HINGE = -0.024, Vector((-0.024, -0.19, 1.365))
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones.new('Jaw')
eb.head = arm.matrix_world.inverted() @ HINGE
eb.tail = arm.matrix_world.inverted() @ Vector((XC, -0.37, 1.335))
eb.parent = arm.data.edit_bones['Head']
eb.roll = 0.0
bpy.ops.object.mode_set(mode='OBJECT')
jaw_g = mesh.vertex_groups.new(name='Jaw')
head_g = mesh.vertex_groups['Head']


def mouth_z(y):
    return 1.342 + (1.37 - 1.342) * min(1.0, max(0.0, (y + 0.38) / 0.13))


njaw = 0
jaw_w = {}
for vi, ps in vpart.items():                     # lower-jaw skin, faded in over 5 cm in front of the hinge
    x, y, z = co[vi]
    if ps != {'Body'} or y > -0.19 or z < 1.24 or abs(x - XC) > 0.12 or z >= mouth_z(y) - 0.002:
        continue
    w = min(1.0, max(0.0, (-0.19 - y) / 0.05))
    try:
        hw = head_g.weight(vi)
    except RuntimeError:
        hw = 0.0
    if w <= 0 or hw <= 0:
        continue
    jaw_g.add([vi], hw * w, 'REPLACE')
    head_g.add([vi], hw * (1 - w), 'REPLACE')
    jaw_w[vi] = w
    njaw += 1
# teeth and tongue: each connected piece goes wholly to the jaw or the head, by the body vertex nearest its centre
# (a tooth split between the two stretched into a spike when the mouth opened)
body_ids = [vi for vi, ps in vpart.items() if ps == {'Body'} and co[vi, 2] > 1.24 and co[vi, 1] < -0.15]
from mathutils.kdtree import KDTree
kd = KDTree(len(body_ids))
for i, vi in enumerate(body_ids):
    kd.insert(Vector(co[vi]), i)
kd.balance()
seen = set(); pieces = {'jaw': 0, 'head': 0}
for vi, ps in vpart.items():
    if vi in seen or not (ps & {'Teeth', 'Tongue'}):
        continue
    comp = [vi]; seen.add(vi); st = [vi]
    while st:
        x_ = st.pop()
        for y_ in adj.get(x_, []):
            if y_ not in seen and vpart.get(y_, set()) & {'Teeth', 'Tongue'}:
                seen.add(y_); comp.append(y_); st.append(y_)
    c = Vector(co[comp].mean(0))
    _p, i, _d = kd.find(c)
    to_jaw = 'Tongue' in ps or jaw_w.get(body_ids[i], 0.0) > 0.5
    for v in comp:
        head_g.add([v], 0.0 if to_jaw else 1.0, 'REPLACE')
        jaw_g.add([v], 1.0 if to_jaw else 0.0, 'REPLACE')
    pieces['jaw' if to_jaw else 'head'] += 1
    njaw += len(comp) if to_jaw else 0
print('JAW teeth/tongue pieces', pieces)
print('JAW vertices', njaw)
mesh.parent = arm
mesh.matrix_parent_inverse = arm.matrix_world.inverted()
mod = mesh.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
bpy.data.objects.remove(src, do_unlink=True)


def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


# 4. feet
sole = {}
for s, side in ((1, 'Left'), (-1, 'Right')):
    sole[side] = np.where((co[:, 2] < 0.035) & (co[:, 0] * s > 0.05))[0]


def smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return 1 - t * t * (3 - 2 * t)


def sole_state(side):
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ m.vertices[i].co) for i in sole[side]])
    ev.to_mesh_clear()
    c = P.mean(0)
    n = np.linalg.svd(P - c)[2][2]
    n = n * np.sign(n[2])
    return Vector(n), float(P[:, 2].min())


LOCO = [a for a in bpy.data.actions if a.name in ('Walking', 'Running')]
report = {}
for act in LOCO:
    keep = act.copy()
    keep.name = act.name + '_src'
    keep.use_fake_user = True
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    plan = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        row = {}
        for side in ('Left', 'Right'):
            pb = arm.pose.bones[side + 'Foot']
            n, h = sole_state(side)
            if n.z < math.cos(math.radians(40)):
                continue
            toe = arm.matrix_world @ arm.pose.bones[side + 'ToeBase'].tail
            ank = arm.matrix_world @ pb.head
            fwd = Vector((toe.x - ank.x, toe.y - ank.y, 0)).normalized()
            lat = fwd.cross(Vector((0, 0, 1)))
            wr, wp = smooth(h, 0.04, 0.12), smooth(h, 0.015, 0.05)
            nt = (n - fwd * (n.dot(fwd) * wp) - lat * (n.dot(lat) * wr)).normalized()
            R = n.rotation_difference(nt).to_matrix().to_4x4()
            M = arm.matrix_world @ pb.matrix
            Mn = Matrix.Translation(ank) @ R @ Matrix.Translation(-ank) @ M
            row[side] = (arm.matrix_world.inverted() @ Mn, round(math.degrees(n.angle(Vector((0, 0, 1)))), 1),
                         round(math.degrees(nt.angle(Vector((0, 0, 1)))), 1), round(h, 3))
        plan.append((f, row))
    for f, row in plan:
        scene.frame_set(f)
        for side, (Mloc, *_r) in row.items():
            pb = arm.pose.bones[side + 'Foot']
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = Mloc
            pb.keyframe_insert('rotation_quaternion', frame=f)
    report[act.name] = {f: {s: r[1:] for s, r in row.items()} for f, row in plan}
    low = 1.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        low = min(low, min(sole_state(side)[1] for side in ('Left', 'Right')))
    if abs(low) > 0.005:
        hips = arm.pose.bones['Hips']
        mats = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            mats.append((f, Matrix.Translation((0, 0, -low)) @ (arm.matrix_world @ hips.matrix)))
        for f, Mw in mats:
            scene.frame_set(f)
            hips.matrix = arm.matrix_world.inverted() @ Mw
            hips.keyframe_insert('location', frame=f)
    print('FLOOR', act.name, 'lowest sole before', round(low, 3))
json.dump(report, open(os.path.join(common.WORK, 'rig_v1_feet.json'), 'w'), indent=0)

# 5. wrists
WRIST_KEEP, WRIST_MAX = 0.5, math.radians(35)
for act in LOCO:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    for side in ('Left', 'Right'):
        pb = arm.pose.bones[side + 'Hand']
        pb.rotation_mode = 'QUATERNION'
        keys = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            q = Quaternion().slerp(pb.rotation_quaternion.normalized(), WRIST_KEEP)
            if q.angle > WRIST_MAX:
                q = Quaternion().slerp(q, WRIST_MAX / q.angle)
            keys.append((f, q))
        for f, q in keys:
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
for name, frames in report.items():
    worst = {s: max((v[s][1] for v in frames.values() if s in v and v[s][2] < 0.03), default=None)
             for s in ('Left', 'Right')}
    print('FEET', name, 'max tilt on ground after fix', worst)

# 6. shoulders
SHOULDER_TOL = 3.0      # deg; Meshy's walk dropped the clavicles (user review: slumped shoulders)
REST_ELEV = {}
for side in ('Left', 'Right'):
    sh = arm.matrix_world @ arm.data.bones[side + 'Shoulder'].head_local
    ah = arm.matrix_world @ arm.data.bones[side + 'Arm'].head_local
    REST_ELEV[side] = math.atan2(ah.z - sh.z, Vector((ah.x - sh.x, ah.y - sh.y)).length)
for act in LOCO:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = lowest = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for side in ('Left', 'Right'):
            pb = arm.pose.bones[side + 'Shoulder']
            pb.rotation_mode = 'QUATERNION'
            sh = arm.matrix_world @ pb.head
            ah = arm.matrix_world @ arm.pose.bones[side + 'Arm'].head
            v = ah - sh
            elev = math.atan2(v.z, Vector((v.x, v.y)).length)
            delta = elev - REST_ELEV[side]
            tol = math.radians(SHOULDER_TOL)
            excess = delta - tol if delta > tol else (delta + tol if delta < -tol else 0.0)
            upper = arm.pose.bones[side + 'Arm']
            upper.rotation_mode = 'QUATERNION'
            if excess != 0:
                worst = max(worst, abs(excess)) if excess > 0 else worst
                lowest = min(lowest, excess)
                axis = Vector((0, 0, 1)).cross(v).normalized()
                keepm = (arm.matrix_world @ upper.matrix).to_3x3().normalized()
                M = arm.matrix_world @ pb.matrix
                M = Matrix.Translation(sh) @ Matrix.Rotation(excess, 4, axis) @ Matrix.Translation(-sh) @ M
                pb.matrix = arm.matrix_world.inverted() @ M
                bpy.context.view_layer.update()
                U = keepm.to_4x4()
                U.translation = arm.matrix_world @ upper.head
                upper.matrix = arm.matrix_world.inverted() @ U
                bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
            upper.keyframe_insert('rotation_quaternion', frame=f)
    print('SHOULDERS', act.name, 'lowered by up to %.1f deg, raised by up to %.1f deg'
          % (math.degrees(worst), -math.degrees(lowest)))
set_action(bpy.data.actions['Walking'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
