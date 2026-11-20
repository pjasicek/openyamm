"""Bow, string and arrow bones and tracks for m154 (after the gated chain: rebuild.sh -> rig_v5), the m214 rules
(mm7_m214_claude/scripts/bow_rig.py, author_bow.py) mirrored: the bow is in the RIGHT fist, the LEFT hand draws.
- Bow (child of B_R_Hand, deforming: the bow mesh and the string ends), rest frame = the solved fist handle
  (grip_pose.json): +Y along the grip axis, signed so it points UP at full draw; +X toward the string, chosen so the
  full-draw pinch (left thumb and index tips) lies in the bow plane; origin at the handle centre.
- StringNock (child of Bow) at the nocking point (string line, NOCK_Y above the grip centre).
- Socket_Arrow_Release (child of Bow, no deformation): the arrow rest just in front of the grip (the release socket).
- Arrow (child of B_Pelvis, deforming the arrow prop; keyed in world terms; scale 0 = hidden).
Attack frames (the joined Draw+Recoil after clip_timing.py's lead): GRAB = lead + 10 (the left pinch takes an arrow
from the quiver over the left shoulder), NOCK = lead + 17, RELEASE = lead + the Draw length (Recoil frame 1).
GRAB..NOCK the arrow's nock end sits at the pinch, turning from the quiver direction to the nocked direction;
NOCK..RELEASE it is nocked (nock at the string, pointing at the arrow rest); hidden from RELEASE. The string follows
the pinch NOCK..RELEASE (never in front of the braced string), then snaps back with a 1 cm overshoot. Every other
clip: arrow hidden, string at rest.
BONES_ONLY=1 adds the bones from work/bow_rig.json (no keys; for rig_v6 before sync_actions.py).
Writes work/bow_rig.json and work/attack_timing.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work')
NOCK_Y = 0.03
REST = Vector((-0.015, 0.05, 0.0))                               # arrow rest: front of the grip (string at +X)
GRAB_S, NOCK_S = 10, 17                                          # Draw frames (m214's probe of the same Mixamo clip)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; body = bpy.data.objects['Body']
GEO = json.load(open(os.path.join(HERE, 'textures', 'props', 'bow_geometry.json')))
FJ = json.load(open(os.path.join(W, 'finger_joints.json')))['L']
smooth = lambda x: x * x * (3 - 2 * x)


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def tip(n):
    pb = rig.pose.bones[n]
    return rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ Vector(FJ[n + '_tip'])


pinch = lambda: (tip('B_L_Finger02') + tip('B_L_Finger12')) / 2
H = rig.data.bones['B_R_Hand'].matrix_local
if os.environ.get('BONES_ONLY'):
    BR = json.load(open(os.path.join(W, 'bow_rig.json')))
    B_hand = Matrix(BR['bow_hand'])
else:
    G = json.load(open(os.path.join(W, 'grip_pose.json')))
    AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
    lead = int(round(json.load(open(os.path.join(W, 'clip_timing.json')))['lead_s'] * 30))
    nd = json.loads(scene.get('concat', '{}')).get('Attack', [32])[0]
    F_REL = lead + nd; F_GRAB, F_NOCK = lead + GRAB_S, lead + NOCK_S
    att = bpy.data.actions['Attack']; set_act(att); scene.frame_set(F_REL - 1)
    Mh = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    p_loc = Mh.inverted() @ pinch()
    if (Mh.to_3x3() @ AX).z < 0:
        AX = -AX
    v = p_loc - GC; bx = (v - AX * v.dot(AX)).normalized(); bz = bx.cross(AX)
    B_hand = Matrix((bx, AX, bz)).transposed().to_4x4(); B_hand.translation = GC
    print('BOWFRAME full-draw pinch from the grip cm', round(100 * v.length, 1), 'out of the grip axis cm',
          round(100 * (v - AX * v.dot(AX)).length, 1))
    set_act(None)
B_rest = H @ B_hand
NOCK = Vector((GEO['string_x'], NOCK_Y, 0.0))
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones


def add(name, parent, M, length, deform=True):
    b = eb.get(name) or eb.new(name)
    b.head = M.translation; b.tail = M.translation + M.col[1].xyz * length; b.align_roll(M.col[2].xyz)
    b.parent = eb[parent]; b.use_deform = deform


add('Bow', 'B_R_Hand', B_rest, 0.2)
Mn = B_rest.copy(); Mn.translation = B_rest @ NOCK; add('StringNock', 'Bow', Mn, 0.05)
Mr = B_rest.copy(); Mr.translation = B_rest @ REST; add('Socket_Arrow_Release', 'Bow', Mr, 0.05, deform=False)
d = ((B_rest @ REST) - (B_rest @ NOCK)).normalized(); up = B_rest.col[1].xyz; x = d.cross(up).normalized()
Ma = Matrix((x, d, x.cross(d))).transposed().to_4x4(); Ma.translation = B_rest @ NOCK
add('Arrow', 'B_Pelvis', Ma, 0.3)
bpy.ops.object.mode_set(mode='OBJECT')
for n in ('Bow', 'StringNock', 'Arrow'):
    if n not in body.vertex_groups:
        body.vertex_groups.new(name=n)
if os.environ.get('BONES_ONLY'):
    print('BOWRIG bones only (from bow_rig.json)')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out)); raise SystemExit
json.dump({'bow_hand': [list(r) for r in B_hand], 'nock_bow': list(NOCK), 'rest_bow': list(REST)},
          open(os.path.join(W, 'bow_rig.json'), 'w'), indent=1)
# quiver axis (into the quiver, downward) in the B_Spine2 rest frame: PCA of the quiver shells P05/P16
co = np.array([tuple(v.co) for v in body.data.vertices]); pv = np.zeros(len(co), np.int32)
body.data.attributes['piece'].data.foreach_get('value', pv)
q = co[np.isin(pv, (5, 16))]; c = q.mean(0); qa = np.linalg.svd(q - c)[2][0]; qa = qa if qa[2] < 0 else -qa
QUIVER_DIR = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector(qa)
an, sn = rig.pose.bones['Arrow'], rig.pose.bones['StringNock']
for pb in (an, sn):
    pb.rotation_mode = 'QUATERNION'
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    set_act(act); f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    if act.name != 'Attack':
        for f in (f0, f1):
            an.matrix_basis = Matrix.Diagonal((0, 0, 0, 1)); sn.matrix_basis = Matrix()
            an.keyframe_insert('scale', frame=f); an.keyframe_insert('location', frame=f)
            an.keyframe_insert('rotation_quaternion', frame=f); sn.keyframe_insert('location', frame=f)
        continue
    log = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        Bw = rig.matrix_world @ rig.pose.bones['Bow'].matrix
        rest_w = Bw @ REST; pw = pinch(); pb_bow = Bw.inverted() @ pw
        nock_bow = NOCK.copy()
        if F_NOCK <= f < F_REL:
            nb = pb_bow.copy(); nb.x = max(nb.x, NOCK.x)
            nock_bow = nock_bow.lerp(nb, smooth(min(1.0, (f - F_NOCK) / 2.0)))      # the string is caught over two frames
        elif F_REL <= f < F_REL + 3:
            nock_bow = nock_bow - Vector((0.01 * (1, -0.4, 0.1)[f - F_REL], 0, 0))
        nw = Bw @ nock_bow
        Mn = rig.pose.bones['Bow'].matrix.copy(); Mn.translation = rig.matrix_world.inverted() @ nw
        sn.matrix = Mn; bpy.context.view_layer.update(); sn.keyframe_insert('location', frame=f)
        if F_GRAB <= f < F_REL:
            nocked = (rest_w - nw).normalized()
            if f < F_NOCK:
                C = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3().normalized()
                dq = (C @ QUIVER_DIR).normalized(); t = smooth((f - F_GRAB) / (F_NOCK - F_GRAB))
                dvec = Quaternion().slerp(dq.rotation_difference(nocked), t) @ dq; base = pw
            else:
                dvec = nocked; base = nw
            up = Bw.col[1].xyz.normalized()
            xx = dvec.cross(up).normalized(); M = Matrix((xx, dvec, xx.cross(dvec))).transposed().to_4x4(); M.translation = base
            an.matrix = rig.matrix_world.inverted() @ M
        else:
            an.matrix_basis = Matrix.Diagonal((0, 0, 0, 1))
        bpy.context.view_layer.update()
        an.keyframe_insert('location', frame=f); an.keyframe_insert('rotation_quaternion', frame=f)
        an.keyframe_insert('scale', frame=f)
        log.append({'f': f, 'pinch_bow': [round(v_, 3) for v_ in pb_bow], 'nock_bow': [round(v_, 3) for v_ in nock_bow]})
    draw = max(e['nock_bow'][0] - NOCK.x for e in log)
    print('TRACKS Attack: arrow visible frames', F_GRAB, '..', F_REL - 1, 'nocked from', F_NOCK, 'release', F_REL,
          f'({F_REL / 30:.3f} s)', 'max draw beyond brace cm', round(100 * draw, 1),
          'full-draw pinch in the bow frame', log[F_REL - 1]['pinch_bow'])
    json.dump({'fps': 30, 'grab': F_GRAB, 'nock': F_NOCK, 'release_frame': F_REL, 'release_s': F_REL / 30},
              open(os.path.join(W, 'attack_timing.json'), 'w'), indent=1)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
